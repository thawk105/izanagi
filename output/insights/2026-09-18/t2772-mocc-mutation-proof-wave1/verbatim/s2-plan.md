## 判定と参照の読み方

**P2 の balanced 形を採用し、P1・P3・P5・P6 を修正する案です。** とくに、cycle の発生を理由に別 integrity 異常を許容する P3 は採用しません。

以下の略記を使います。

- `V/` = `/home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/verbatim/`
- `T:n` = `V/mocc-transaction-e9e477ca.cc:n`。e9e477ca の元ソース行。
- `I:n` = 計装 patch だけを適用した後の物理行。今回、patch の context を元ソースと照合し、メモリ上で算出。
- repo 内の行番号は現在のファイル。新規ファイルには実在する行番号がないため、関数名と移植元の行を示します。

指定資料を静的に読解しました。ファイル変更、build、pytest、benchmark は実行していません。

## 1. 新負例 patch の逐語案

対象は `patches/broken-mocc-hot-update-unlock.patch`、touch set は `["cc/mocc/transaction.cc"]` のみです。preimage は e9e477ca に旧計装 patch を適用したものです。

挿入位置は次のとおりです。物理行は**新負例をまだ適用していない I** を基準にします。

| hunk | 計装後の位置 | 元の論理行 | 復元値 |
|---|---|---:|---:|
| file scope | I:18 `#line 17` の直後、I:19 の空行の前 | 17 | `#line 17` |
| update | I:461 の一行を置換 | 459 | `#line 460` |
| abort | I:1095 `unlockCLL();` の直前 | 1069 | `#line 1069` |
| publish | I:1259 `#line 1195` の直後、I:1260 の store 前 | 1195 | `#line 1195` |

file scope の挿入本文：

```cpp
#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK
[[maybe_unused]] static constexpr bool izanagi_break_mocc_hot_update_unlock = TRACE != 0;
[[maybe_unused]] static thread_local Tuple* izanagi_hot_update_pending = nullptr;
#else
[[maybe_unused]] static constexpr bool izanagi_break_mocc_hot_update_unlock = false;
[[maybe_unused]] static thread_local Tuple* izanagi_hot_update_pending = nullptr;
#endif
#line 17
```

P2 への小修正は、ON 側の bool を `TRACE != 0` とすることです。診断動作を TRACE=1 に限定します。裸 directive は引き続き `#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK` の一回だけです。condition gate は TRACE=1 configure で実施します。

`Tuple` は T:11 の include 後なので宣言済みです。pointer は両腕で宣言し、`nullptr` で定数初期化します。非 template 関数内の discarded statement も名前解決されるため、OFF 側の宣言を省きません。`[[maybe_unused]]` は両宣言に付け、macro=0 の未使用診断を避けます。実際の警告・symbol 消失は DW-G01 で確認します。

update の置換本文：

```cpp
  if (loadepot.temp >= FLAGS_temp_threshold) {
    lock(tuple, true);
    if constexpr (izanagi_break_mocc_hot_update_unlock) {
      if (this->status_ != TransactionStatus::aborted &&
          izanagi_hot_update_pending == nullptr) {
        tuple->rwlock_.w_unlock();
        izanagi_hot_update_pending = tuple;
      }
    }
  }
#line 460
```

T:460〜464 のコメントと `status_` 判定は元のまま続けます。macro=0 では、元の温度条件で同じ `lock(tuple, true)` を一回呼び、その後の abort 判定も同位置で実行します。新しいローカル変数を導入しないため、T:430 の `goto FINISH_WRITE` による初期化跨ぎも増やしません。

abort の挿入本文：

```cpp
  if constexpr (izanagi_break_mocc_hot_update_unlock) {
    if (izanagi_hot_update_pending != nullptr) {
      izanagi_hot_update_pending->rwlock_.w_lock();
      izanagi_hot_update_pending = nullptr;
    }
  }
#line 1069
```

T:1068 のコメントの後、T:1069 の `unlockCLL()` 前です。`construct_RLL()` は元の T:1071 のままです。

publish の挿入本文：

```cpp
    if constexpr (izanagi_break_mocc_hot_update_unlock) {
      if (izanagi_hot_update_pending == (*itr).rcdptr_) {
        izanagi_hot_update_pending->rwlock_.w_lock();
        izanagi_hot_update_pending = nullptr;
      }
    }
#line 1195
```

位置は、`"lock-lost-before-publish"` を含む TRACE block の終了と既存 `#line 1195` **より後**、T:1195 の `__atomic_store_n` **より前**です。既存計装 patch:106〜115 と整合します。

この逐語案なら追加量は file scope 8 行、update 差分 +10 行、abort 7 行、publish 7 行です。新 patch 適用後の各変更先頭は物理行 19、469、1113、1285 になります。unified diff の context を増減する場合も、上表の preimage anchor を正本にしてください。

確認事項：

- 裸 directive 一回、`if constexpr` 三回。D1686:17〜18 の exactly-one 契約を維持。
- commit/abort の再取得は直接 `rwlock_.w_lock()`。`TxExecutor::lock()` は T:744〜746 の stale CLL 判定で戻るため不可。
- 既存計装の七つの `#line` は変更しない。
- **計装の TRACE=0 論理行一致**と、**新負例 OFF の最適化後 binary 一致**は別命題。新負例には constexpr 宣言や block が残るため、macro=0 の前処理本文が無 patch と一致するとは主張しません。D1687 の正本比較は無 patch ↔ 計装のみです。

## 2. U に限定した balanced・待ちの論証

前提は設計:174〜181 の U、既存 record への blind UPDATE 一操作、RWLOCK です。YCSB の生成と初期温度の根拠は設計:60〜61、親 brief:30〜32 にあり、射影には `ycsb.hh`・初期化実装そのものがありません。その部分は親の確認結果を前提とし、直接再検算済みとは区別します。

`update()` 自体は T:434 で read set を検索しますが、新しい read 要素を追加せず、T:477 で write set に追加します。

| regime / thread | 新負例の遷移 | 待ち |
|---|---|---|
| hot / t1 | update で `0→-1→0`、validation は stale CLL で戻る、publish 前に `0→-1`、末尾で `-1→0` | 他 worker なし |
| hot / t4 | 各 thread が上記を行う。他 thread の所有期間が `0` の間へ挟まる | 初回取得・再取得とも一つの lock だけ |
| cold / t1 | update では取得なし、validation で `0→-1`、末尾 `-1→0` | 他 worker なし |
| cold / t4 | 同上。pending は常に null | 一つの lock だけ |
| default / t1 | 温度 0 が維持され、cold と同じ | 他 worker なし |
| default / t4 | 同上 | 一つの lock だけ |

根拠は T:459、477、744〜746、884〜888、993〜1000、1195、1207。counter の意味は `external/ccbench/cc/mocc/include/lock.hh:137〜156`、unlock が加算である点は D1686:15〜16 です。`include/rwlock.hh:54〜80` は類似実装ですが、クラス名が `ReaderWriteLock` であり、mocc の `ReaderWriterLock` 実装そのものとは扱いません。

hot/t4 の競合順序例：

1. A が x を取得し、故意に解放。A の CLL と pending は x を保持。
2. B が x を取得。A の再取得は待つが、A は実 lock を一つも保持していない。
3. B が故意に解放すれば A/B の再取得が競合する。
4. 勝者は publish、`unlockCLL()` を終え、敗者が取得できる。
5. 勝者は再取得後に別 lock を待たない。

従って、この workload では wait-for cycle を構成できません。**spin lock の公平性、starvation 不在、120 秒以内の終了までは証明していません。**

RLL が空であることは帰納的に説明できます。

- 初期 RLL 空を前提とする。
- U の最初の lock は CLL 空なので `vioctr=0`。T:770 の abort 可能な枝には入らない。
- hot の validation lock は同じ writer CLL により T:746 で戻る。cold/default は一つの writer lock を取得する。
- DELETE がないため T:995 の absent 条件は偽。
- read set が空なので T:1008〜1039 の検査は実行されない。
- scan がないため node map は空という前提で、T:1042〜1048 も実行されない。
- validation は T:1050 で成功。commit は T:1208 で RLL を消去する。

abort 側の再取得は構造上必要ですが、この U 実走で動的被覆されたとは報告しません。

反例・限定：

- 多操作へ拡張すると、次の `lock()` が T:834〜857 で stale CLL を再解放し、counter を壊し得ます。pending が一つだから一般に balanced、とは言えません。
- この論証を旧 early-unlock/W の t4 に転用できません。旧 patch は複数 write の lock を解放・順次再取得します。36 走全体の無 hang は compute で確認します。
- 故意に lock を外した負例について、C++ の未同期 payload アクセスまで含む一般的な実行保証はできません。ここで示すのは lock 制御フロー上の限定的な論証です。

## 3. driver の構成と再利用

新規 `s3_mocc_mutation_proof.py` は旧 module を `legacy` として import し、旧ファイルを変更しません。

| 旧 driver の要素 | 判定 | 根拠・新側の責務 |
|---|---|---|
| `PIN`、`SOURCE_REL`、`STOCK_G`、patch 定数 | 再利用 | :42〜69 |
| `SINGLE_FLAGS`、`HIGH_FLAGS` | コピーして再利用 | :52〜61。共有 dict を mutate しない |
| `_sha256_file`、`_run_checked` | 再利用 | :93〜117 |
| policy/toolchain/dependency helpers | 再利用 | :120〜253 |
| `_common_configure_args` | 再利用 | :257〜271 |
| `_apply_owned_patch` | 再利用 | :438〜445。transaction 単独制約が適合 |
| `_trace_counts` | 部分再利用 | :367〜388。R 行数を返さない |
| `_trace0_record` | 補助情報として再利用 | :453〜486。論理行列も `.text` section bytes も測っていない |
| `_require_condition_gate` | 新側に実装 | :274〜310 の形で新 driver ID を使用 |
| `_build_variant` | 新側に実装 | :313〜340。新 materializer 名を登録 |
| `_run_trace` | 新側に実装 | :343〜364 は timeout/非零 rc を例外化する |
| `_verify` | **新側に実装** | :391〜418 は timeout=300、raw integrity を捨て、異常終了も例外化 |
| `_variant_run`、`main` | 新側に実装 | :421〜435、:610〜。matrix と逐次保存が異なる |

新 `_verify` は旧 `_run_checked(..., timeout=900, allowed_returncodes={0,1,3})` を利用できます。verifier rc=1/3 は負例の判定結果になり得るため、benchmark rc=0 要件と混同しません。timeout・起動失敗・JSON 不正は run 内の verifier failure として残します。旧 module の timeout 定数を書き換える方式は採りません。

新側に必要な小さな追加処理：

- `_trace_counts` の結果に `read_rows` を加える処理。
- D1687 の論理行列比較。旧 test:117〜179 の方式を参考にし、production から test module は import しない。
- 同一 directory 内の一時ファイルから `os.replace` する JSON 保存。
- 全 check に必要な観測値を保存し、不完全な入力では false を返す処理。

実行順は **stock の12走 → lockskip の6走 → perm の6走 → early の6走 → hot-update の6走**。各 build の checkout が生きている間に、その binary の benchmark と verifier を一走ずつ直列実行します。verifier も直列でよく、source snapshot の寿命とメモリ使用を単純に保てます。旧 `patchharness.py:346〜378` の隔離 checkout を使用します。

## 4. 36 走 matrix

共通 flags は旧 driver:52〜61 の値です。

- W: `tuple_num=200, zipf_skew=0.9, rratio=0, rmw=true, max_ope=5, extime=1`
- U: W から `rmw=false, max_ope=1`
- 各行で `thread_num=t`、`temp_threshold=θ`、実 argv に `-clocks_per_us=2100`
- A = 受入必須、O = 観測のみ

build は S=計装 stock、L=lockskip、P=permutation-erase、E=early-unlock、H=hot-update-unlock。TRACE=1 の五本を共有します。

| build | run_name | flags | regime θ | thread | 区分 |
|---|---|---|---:|---:|---|
| S | `stock_hot_t1` | W | hot 0 | 1 | A |
| S | `stock_hot_t4` | W | hot 0 | 4 | A |
| S | `stock_cold_t1` | W | cold 21 | 1 | A |
| S | `stock_cold_t4` | W | cold 21 | 4 | A |
| S | `stock_default_t1` | W | default 10 | 1 | A |
| S | `stock_default_t4` | W | default 10 | 4 | A |
| S | `stock_u_hot_t1` | U | hot 0 | 1 | A |
| S | `stock_u_hot_t4` | U | hot 0 | 4 | A |
| S | `stock_u_cold_t1` | U | cold 21 | 1 | A |
| S | `stock_u_cold_t4` | U | cold 21 | 4 | A |
| S | `stock_u_default_t1` | U | default 10 | 1 | A |
| S | `stock_u_default_t4` | U | default 10 | 4 | A |
| L | `lockskip_hot_t1` | W | hot 0 | 1 | O |
| L | `lockskip_hot_t4` | W | hot 0 | 4 | O |
| L | `lockskip_cold_t1` | W | cold 21 | 1 | A |
| L | `lockskip_cold_t4` | W | cold 21 | 4 | A |
| L | `lockskip_default_t1` | W | default 10 | 1 | A |
| L | `lockskip_default_t4` | W | default 10 | 4 | A |
| P | `perm_hot_t1` | W | hot 0 | 1 | A |
| P | `perm_hot_t4` | W | hot 0 | 4 | O |
| P | `perm_cold_t1` | W | cold 21 | 1 | A |
| P | `perm_cold_t4` | W | cold 21 | 4 | O |
| P | `perm_default_t1` | W | default 10 | 1 | O |
| P | `perm_default_t4` | W | default 10 | 4 | O |
| E | `early_unlock_hot_t1` | W | hot 0 | 1 | A |
| E | `early_unlock_hot_t4` | W | hot 0 | 4 | O |
| E | `early_unlock_cold_t1` | W | cold 21 | 1 | A |
| E | `early_unlock_cold_t4` | W | cold 21 | 4 | O |
| E | `early_unlock_default_t1` | W | default 10 | 1 | O |
| E | `early_unlock_default_t4` | W | default 10 | 4 | O |
| H | `hot_update_unlock_hot_t1` | U | hot 0 | 1 | A |
| H | `hot_update_unlock_hot_t4` | U | hot 0 | 4 | O |
| H | `hot_update_unlock_cold_t1` | U | cold 21 | 1 | A |
| H | `hot_update_unlock_cold_t4` | U | cold 21 | 4 | A |
| H | `hot_update_unlock_default_t1` | U | default 10 | 1 | A |
| H | `hot_update_unlock_default_t4` | U | default 10 | 4 | A |

必須25、観測11です。設計:189〜201 と一致します。

compute の TRACE=0 は無 patch と計装のみの二本。合計七本です。新負例 macro=0 の binary 比較は後述する login 生死確認で別途実施します。

## 5. JSON と run record

top-level は次を固定します。

| key | 内容 |
|---|---|
| `schema_version` | `"s3-mocc-mutation-proof/v1"` |
| `ccbench_commit` | e9e477ca の full SHA |
| `env_tag`, `site`, `genome`, `clocks_per_us` | 旧 driver と同じ由来 |
| `toolchain` | 実 compiler path と version-body sha |
| `patches` | 旧四本＋新一本の path、sha256 |
| `workloads` | W/U の共通 flags |
| `regimes` | hot=0、cold=21、default=10 |
| `trace0` | 比較対象、nm/strings、論理行列の一致・件数・digest、補助 binary 比較 |
| `legacy_proof` | 旧 JSON の repo-relative path、sha256、旧14 check の写し |
| `condition_gates` | 負例四本の `macro/supply/meaning/admission` |
| `diagnostic_build_admission` | 新 `_build_variant` の NON_ADMISSIBLE record |
| `hot_path_evidence` | 下記 method と保証名 |
| `touch_sets` | patch ごとの実 touch set |
| `runs` | 上表の run_name を key とする record |
| `checks`, `all_pass` | 保存観測値から導出 |

`n1_*` と `template` は入れません。

保証名は本依頼が名指す設計:160 の逐語を採ります。

```json
{
  "method": "negative-control",
  "guarantee": "stock 等価述語における hot-update 負例の到達と、既存 X 3 検査点の検出"
}
```

D2134 項4では「と」の後の読点がありません。意味は同じですが、文字列 exact test のため設計版へ統一することを段4で記録してください。

各 run は以下を持ちます。

```text
build, workload, regime, thread, acceptance, flags
argv, terminated, returncode, timed_out, error
verifier:
  argv, terminated, returncode, timed_out, error, record
verdict, certified, total_cycles, txns
lock_coverage_violations, permutation_violations
x_reasons, p_reasons, non_insert_writes, read_rows
integrity
```

成功時の要約値は `verifier.record` から抽出し、consumer が両者の一致を確認します。失敗時の未観測値は `null`、未観測の数値をゼロにしません。

`integrity` は raw record 全体を保存します。少なくとも旧 `_verify`:405〜411 の十項目に加え、X/P details、proof surfaces、expected/observed commits、notes を落としません。

`txns > 0 && non_insert_writes == txns` **だけでは R 行ゼロを証明できません**。U の確認には `read_rows == 0` を直接記録します。

JSON は初期状態、benchmark 終了後、verifier 終了後に atomic replacement します。benchmark 完了後・verifier timeout 前にも証拠を残せます。job kill 時に保証できるのは最後の保存地点までです。

## 6. check の述語と P3

新 `compute_checks` は旧 driver:493〜591 の入力由来方式を引き継ぎます。ただし evidence method の検査には対応する入力が必要です。

```python
compute_checks(
    runs, trace0, touch_sets, patch_relatives, toolchain, policy,
    *, hot_path_evidence,
)
```

method を関数内の固定値と比較するだけの恒真 check にしません。

以下で X/P は総数、E/W/T は三 reason、C は total_cycles とします。

| check 名 | 述語 |
|---|---|
| `stock_{r}_{t}_certified_and_silent` ×6 | 対応 stock-W が certified、verdict=`serializable`、C=X=P=0、txns>0、non_insert_writes>0 |
| `stock_u_{r}_{t}_certified_and_silent` ×6 | 上記＋read_rows=0、non_insert_writes=txns |
| `{cold,default}_lockskip_t1_three_reasons_cycles_zero` ×2 | verdict=`indeterminate`、certified=false、C=P=0、X>0、E/W/T 各>0、txns/write>0 |
| `{cold,default}_lockskip_t4_x_positive` ×2 | X>0、P=0、txns/write>0、certified=false。C>0ならN、C=0ならI |
| `perm_{hot,cold}_t1_only_size_changed` ×2 | I、非 certified、C=X=0、P>0、`p_reasons == {"size-changed": P}`、txns/write>0 |
| `early_unlock_{hot,cold}_t1_retention_without_entry` ×2 | I、非 certified、C=P=0、E=0、W/T各>0、txns/write>0 |
| `hot_update_unlock_hot_t1_three_reasons_cycles_zero` | lockskip/t1型＋read_rows=0、non_insert_writes=txns |
| `hot_update_unlock_{cold,default}_{t1,t4}_silent` ×4 | stock-U型 |
| `matrix_runs_complete_and_terminated` | 下記の構造・終了要件 |
| `hot_path_evidence_method_is_negative_control` | 入力の method と保証名の文字列 exact |
| `trace0_nm_izanagi_zero` | nm count=0 |
| `trace0_strings_izanagi_trace_zero` | trace marker count=0、macro marker count=0 |
| `trace0_logical_rows_identical` | 実測した非空論理行列が一致し、件数>0 |
| `toolchain_matches_policy` | gcc/g++ の key exact、観測 digest と policy digest が一致 |
| `all_broken_patch_touch_sets_are_transaction_only` | 負例四本の集合 exact、各 touch set が `[SOURCE_REL]` |

X/P の総数と reason 集計、要約と raw record の一致は JSON consumer でも検査します。計装 patch の transaction 単独性は `_apply_owned_patch` と consumer で確認します。

matrix check は次です。

```text
set(runs) == expected_36_names
かつ全 run:
  metadata/flags が予定 cell と一致
  実 argv があり、その flags を含む
  terminated is True
  returncode == 0
  timed_out is False
  verifier.terminated is True
  verifier.timed_out is False
  verifier.returncode ∈ {0, 1, 3}
  verifier.record が存在し、必要な結果 field を持つ
```

ここには X/P の期待正数を入れません。

**P3 は棄却案です。** `V/s3_mocc_lock_coverage.summary.json:123〜136` の cycle=3,754 は DSG の異常です。`version_dups` や `dup_txids` の値はその要約に載っていません。`model.py:475〜480, 511〜520` は cycle と integrity を明確に区別しています。「cycle が出たので別 integrity clean は恒偽」は導けません。

一方、故意の lock 欠落が version 重複を起こす可能性はあります。しかし設計:203〜204 はその場合も赤としています。事前に例外化しません。

この要件を観測11走にも適用し、matrix check を終了確認に限定するため、**設計候補32 key に次の一つを追加する案**を段4へ出します。

```text
all_runs_other_integrity_clean
```

全36走について、旧 `_verify` が列挙する十項目が所定のゼロ／空値であることを raw integrity から検査します。X/P の期待違反は除外します。これは仮想リスク向けの新 gate ではなく、設計:203〜204 の明示要件の実装です。

この案の exact check 数は33。`all_pass` は exact key 集合を満たす全 check が true、かつ36走が揃う場合だけ true とします。

## 7. 新 test の node 一覧

新 `orchestrator/tests/test_mocc_mutation_proof.py` に以下を置きます。

| node | 検査内容 |
|---|---|
| `test_mocc_hot_unlock_is_balanced_on_commit_and_abort` | 実 patch 適用 source で三 site、guard、直接 relock、pending clear、publish/abort の順序、`#line` を検査 |
| `test_mocc_hot_unlock_has_unique_condition_witness` | owner/directive exact、production instrumenter が一回を受理し重複を拒否 |
| `test_mocc_mutation_matrix_is_exact` | 36 names、flags、必須25/観測11、U専用負例、build共有 |
| `test_mocc_mutation_check_keys_are_exact` | 独立に列挙した33 key と一致 |
| `test_mocc_mutation_checks_are_input_derived` | baseline全true、各keyに一field変異を与え当該keyだけfalse |
| `test_mocc_mutation_proof_json_is_complete_and_bound` | JSONの存在、schema/PIN、五patch sha、旧JSON sha/14check、36走、33key、再計算結果、all_pass |
| `test_mocc_mutation_run_records_failure_and_timeout` | benchmarkの非零rc・timeout・起動失敗を記録しmatrixを赤にする |
| `test_mocc_mutation_verify_binds_protocol_root_and_timeout` | `--protocol mocc`、渡されたroot、900秒、rc 0/1/3、raw integrity保持 |
| `test_mocc_mutation_condition_gate_uses_new_driver_id` | 四macro、1/0、新driver ID、supply/meaning/admission |
| `test_mocc_mutation_trace0_logical_rows_are_input_derived` | 計装前後の論理行比較。`#line ±1` で不一致 |
| `test_mocc_mutation_u_trace_counts_reads` | W数がtxn数と同じでもR行があればU条件を落とす |

patch の構造検査は旧 test:497〜592、入力由来検査は:798〜954、JSON consumer は:957〜985 が前例です。新 patch の検査は patch 文面だけでなく、適用後 source を対象にします。

一field変異の例：

- 各必須run check：対応する `certified`、C、reason、P など。
- matrix：観測run一件の `timed_out=True`。
- global integrity：観測run一件の `integrity.version_dups=1`。
- hot evidence：methodを変更。
- trace0：対応countまたは論理行一致を変更。
- toolchain：g++ digestを変更。
- touch set：一負例のtouch先を変更。

「当該keyだけfalse」はこのように選んだ独立変異で確認します。run丸ごと削除など、複数の要件を同時に壊す変異には複数赤を認めます。

**compute JSON がない間、consumer は赤です。skip・仮JSON・空の all_pass は使いません。** compute前の焦点走からconsumerを明示的に外すことはできますが、その状態を受入緑とは報告しません。

## 8. 登録簿閉包の逐語と焦点 node

`materializer_admission.py:87` 後：

```python
    "orchestrator.campaign.s3_mocc_mutation_proof._build_variant":
        MaterializerRegistration(
            NON_ADMISSIBLE,
            "trace-only mocc mutation proof controls; never source performance values",
        ),
```

`condition_meaning_gate.py:204` 後：

```python
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": DefineSpec(
        ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe",
        "patches/broken-mocc-hot-update-unlock.patch",
    ),
```

同 `:269` 後：

```python
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": (
        "cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK",
    ),
```

`screening_driver.py:80` 後：

```python
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": 0,
```

`test_condition_meaning_gate.py:40` と `:2685` の各直後：

```python
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK",
```

`test_ccbench_spawn_sites.py:27` 後：

```python
    s3_mocc_mutation_proof,
```

同 `:62` 後：

```python
    ("campaign/s3_mocc_mutation_proof.py", "<module>._run_trace"): 1,
```

同 `:4112` 後。新moduleでは U 定数名を `U_SINGLE_FLAGS/U_HIGH_FLAGS` とします。

```python
    for workload in (
        s3_mocc_mutation_proof.SINGLE_FLAGS,
        s3_mocc_mutation_proof.HIGH_FLAGS,
        s3_mocc_mutation_proof.U_SINGLE_FLAGS,
        s3_mocc_mutation_proof.U_HIGH_FLAGS,
    ):
        assert classify_minimal_holdout_signature(_flags(workload)) is None
```

`:208` 隣への追加は不要です。新 `_verify`・preprocess も旧 `_run_checked` を呼び、新たな直接 subprocess site は `_run_trace` 一つに限定する案です。

`test_p3_build_authority_cli.py:164` 後：

```python
    "s3_mocc_mutation_proof.py",
```

同 `:182` 後：

```python
    "orchestrator.campaign.s3_mocc_mutation_proof._build_variant",
```

`test_p3_s4_loop.py:7922` 後：

```python
        "patches/broken-mocc-hot-update-unlock.patch": frozenset({
            "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK",
        }),
```

対応する既存焦点 node：

| 面 | node |
|---|---|
| materializer／build authority | `test_python_ccbench_manual_materializers_are_explicitly_non_admissible`、`test_single_registry_has_typed_compatible_projections` |
| build launcher exact閉包 | `test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches` |
| DefineSpec／witness | `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`、`test_compile_time_branch_selection_accepts_each_registry_macro[IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK]`、`test_v1_domain_and_claim_boundaries_are_exact` |
| patch define inventory | `test_patch_define_inventory_matches_condition_gate_registry` |
| screening/build sink gate | `test_define_sink_cross_product_has_no_unreviewed_ungated_member` |
| process／holdout | `test_reviewed_process_launch_inventory_is_recursive_and_exact`、`test_direct_spawn_allowlist_constants_cannot_reach_protected_ratios` |
| B-3 | `test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted` |

B-3 は node 単独で一回焦点走に入れます。旧 insight:106 の260秒/走を踏まえ、各変異の反復killerにはしません。焦点走・受入は `tools/run_tests.py` 経由です。

親が書く `patches/README.md:598` 隣の追記案：

> `broken-mocc-hot-update-unlock.patch` は e9e477ca + 計装 patch に適用する TRACE 診断用負例。hot な `update()` の writer lock を直後に解放し、publish 検査後と abort cleanup 前に直接再取得する。実証対象は blind UPDATE 一操作の U に限定する。保証は hot-update 負例の到達と既存 X 三検査点の検出であり、read 側 hot 経路、RLL 再試行、DELETE の動的被覆を含まない。旧 T-2294 の証拠は変更しない。

新JSONの結果文はcompute完了後に実測値で追加します。

## 9. DW-G01 の最小生死確認

親の一時 `liveness-run.sh` 相当で、以下を**buildのみ**行います。過去 script 本体は射影にないため、逐語再現ではなく `V/t2294-README.md:44〜53` の確認内容を再構成した手順です。

1. policy束縛toolchainと第三者cacheを解決する。
2. `checkout(PIN)` で隔離sourceを用意する。
3. 各sourceへ計装のみ、または計装＋負例一つを適用。
4. stock/L/P/E/H の五本を TRACE=1、負例macro=1、`-Wall -Wextra -Werror` を有効にして `ycsb_mocc.exe` までbuild。
5. 新負例macro=0・TRACE=0と、無patch・TRACE=0を、source/build path長を揃えてbuild。
6. 両binaryの `.text` section bytesを抽出してsha256とbytesを比較。新負例OFF binaryで `nm -C` の `izanagi`、`strings -a` の関連markerがゼロであることを確認。
7. 無patch↔計装のみのTRACE=0前処理論理行列を比較。
8. 四負例の実condition gateがgreenであることを確認。

build呼出しは親の現行 `tools/run_tests.py` による場所・メモリ判定経路を使います。直接pytest/buildを起動する手順にはしません。wrapperのCLIは射影対象外なので、未確認のoptionはここで固定しません。

CMakeの未使用変数警告を無視しないことが必要です。T-2294ではbuild成功後、`RULE_LAUNCH_COMPILE` の警告によりcondition gateが失敗しました（旧 insight:69〜74）。

## 10. compute 投入と時間予算

初回は指定どおり一jobです。

```text
tools/pegasus/dispatch_compute.py --task generic -- /usr/bin/python3 orchestrator/campaign/s3_mocc_mutation_proof.py --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
```

P6 の20〜25分は**可能な見積であり、検算済み上限ではありません**。

- 17.3秒/100万txnを線形に仮置きすると、300〜800万txnは約52〜138秒。
- t4/Uはstockと新負例の計6走なので、この六つだけで約311〜830秒。
- 残る30走、build七本、condition gate四組、trace集計とI/Oを加える必要があります。
- timeout上限の単純和は `36 × (120+900) = 36,720秒`。3600秒job内への完了保証にはなりません。
- 合成write-onlyの速度をWのDSG構築、cycle検出、X/P大量出力へそのまま転用できません。

したがってRUN=120、VERIFIER=900、gen_S=3600は初回設定として採用しますが、「足りる」と断定しません。各stageの実経過時間をrecordに残します。

初回で不足が判明した場合だけ、最小fixとして `--regime hot|cold|default` と別 `--out` を追加し、12走ずつの三jobへ分けます。統合時はPIN・五patch sha・toolchain・workloadsを一致確認し、36 namesを重複なく合成してcheckを再計算します。汎用schedulerやresume frameworkは作りません。分割しても一走の900秒不足は解決しないため、その場合は別途原因を判断します。

## 11. 変異事前登録候補

段4でkillerを確定する候補12件です。patch shaのconsumer拒否だけを意味検出力には数えません（旧 insight:107）。

| # | 対象と変異 | 期待 | 主killer |
|---|---|---|---|
| 1 | 新patchのpublish側 `w_lock()` 削除 | KILLED | balanced構造node |
| 2 | 新patchのabort側再取得block削除 | KILLED | balanced構造node |
| 3 | 再取得を `lock(pending, true)` に変更 | KILLED | balanced構造node |
| 4 | publish側relockをX検査前へ移動 | KILLED | balanced構造node |
| 5 | 裸directiveを二箇所へ複製 | KILLED | unique witness node |
| 6 | `#line 460` を461へ変更 | KILLED | patchの行復元検査 |
| 7 | driverの主hot/t1 checkを定数Trueへ変更 | KILLED | input-derived node |
| 8 | timeout記録をfalseへ固定 | KILLED | failure/timeout node |
| 9 | `DefineSpec` の新entry削除 | KILLED | patch inventory／condition registry |
| 10 | 新materializer entry削除 | KILLED | build authority／floor registry |
| 11 | 新JSONの新patch sha一文字変更 | KILLED | JSON consumer |
| 12 | 新JSONを一時的に欠落させる | KILLED | JSON consumer、skip不可 |

B-3 entry削除は独立候補として有用ですが、反復費用を考え上の12件には含めません。SURVIVEDを期待する意味変更はこの候補集合にはありません。

## 12. 親 brief への異議

| 箇所 | 異議・修正 |
|---|---|
| brief:41 P1 | `_verify` はtimeout・raw integrity・終了recordの三点でそのまま使えない。旧driver:391〜418 |
| brief:41 P1 | `_trace_counts` はR行数を返さず、`_trace0_record` は論理行一致を測らない。旧driver:367〜388、453〜486 |
| brief:31 | `non_insert_writes == txns` はR行ゼロの証拠ではない。read_rowsを直接数える |
| brief:42 P2 | TRACE隔離を明文化する。macro ON側boolを `TRACE != 0` とする案 |
| brief:43 P3 | cycle=3,754から別integrity異常を推論できない。規律2・設計:203〜204を維持 |
| brief:43 P3 | 必須走の列挙からcold/default lockskip t4の二走が抜けている。設計:193〜194では必須 |
| brief:45 P5 | 終了確認には `timed_out=false` とverifier完了状態も必要 |
| brief:45 P5 | 観測走の別integrity要件を32候補keyだけでは表現していない。共通checkを一つ追加する案 |
| brief:46 P6 | 合成traceの単点実測から36走20〜25分を確定できない |
| brief:47 P7 | verifier前にも保存しなければ、その間のjob killで当該benchmark結果が失われる |
| brief:63〜69 | 「登録簿5箇所＋テスト側3箇所」は数え方が曖昧。実変更先はproduction三file、test四fileで、同一file内に複数entryがある |
| 射影のlock API説明 | `include/rwlock.hh` は別クラス。mocc headerはメソッド宣言が中心。実装の直接確認とD1686による根拠を区別 |
| 保証名 | 設計:160とD2134項4で読点が異なる。exact文字列の正本を固定する |
| 所有範囲 | READMEは親、新patch/driver/test/登録変更はauthor、新JSONはcompute生成。旧証拠・gitlink・wave2面には変更を入れない |

## 総括

**負例は、hot update直後のunlock、publish検査後とabort cleanup前の直接relock、thread-local `Tuple*` pendingによる三site構成で進められます。** 適用位置は I:461／1095／1260、復元値は460／1069／1195です。U限定で循環待ちを構成しない静的論証は成立しますが、実完走は未確認です。

| provisional | 判定 |
|---|---|
| P1 | 一部修正。helper再利用は妥当、`_verify`は新設、R行集計・論理行比較を補う |
| P2 | 条件付き採用。TRACE隔離、両腕宣言、三siteの行復元を上記で固定 |
| P3 | 棄却案。cycleと別integrity異常を混同せず、全走の別integrity異常を赤にする |
| P4 | 採用。compute七build、runtime閾値、stock binary共有 |
| P5 | 修正。32候補＋共通integrityの33check案、timeout/verifier完了を明示 |
| P6 | 初回設定として採用。20〜25分は不確実、3600秒内の保証なし |
| P7 | 採用。benchmark後・verifier後に保存し、部分証拠を保持 |
| P8 | 採用。hot/t4のX/P期待は観測だけで、reason正数を要求しない |

主要な異議は、旧verifierの再利用不能、P3の根拠不足、R行ゼロの証拠不足、TRACE=0比較の混同、時間見積の一般化です。

段5は**author一本で足ります**。patch・matrix・check・JSON consumerの契約を同じ担当で閉じる利点があります。見積は実装・静的整合で60〜120分、login build/gate/focusで追加15〜40分、computeは暫定20〜35分、変異・受入は別枠です。いずれも今回の実測値ではなく計画値です。