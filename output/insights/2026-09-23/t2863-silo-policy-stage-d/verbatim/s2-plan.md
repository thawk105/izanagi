## 1. IR

**推奨は、式を純粋な型付き木、状態更新を hook ごとの同時代入として表す方式。** 受理契約は変えず、IR 側だけをその部分集合に閉じる。

以下、`C/` = `orchestrator/campaign/`、`Q/` = `orchestrator/tests/`。既存の行番号は静的に確認した。新設ファイルの関数名・配置は提案であり、行番号は付けない。ファイル変更・テスト実行はしていない。

新設 `C/silo_policy_ir.py` の定義案：

```python
ScalarType = Literal["u32", "u64", "bool"]
ExprType = Literal["u32", "u64", "bool", "reason", "action"]

# 各構成子は frozen=True の dataclass
Const(type, value)
Reason()                      # abort hook のみ
Attempt()                     # lock hook のみ、U32
StateRef(index)               # 宣言した scalar field
Compare(op, left, right)
Select(condition, yes, no)
Min(left, right)
Max(left, right)
SatAdd(left, right)
SatSub(left, right)
Shift(direction, value, amount)  # amount は式ではなく固定整数

StateField(type, initial_literal)
AbortHook(wait, next_state)
LockHook(action, wait, next_state)
CommitHook(next_state)
PolicyIR(fields, after_abort, on_lock_conflict, on_commit)
```

- `next_state` は field 順の式 tuple。省略時は全 field を保持する。
- 出力と次状態はすべて **hook 入口の状態**から計算し、計算後に状態へ代入する。
- 出力待機量は U32、action は `retry`／`abort` の列挙値。状態は U32／U64／bool、最大 4 field。
- reason と attempt は対応 hook だけで参照可能。`rand` は今回の IR には入れない。
- 数値二項演算は同じ型同士に限定する。v1 が許す暗黙の U32/U64 混在より狭い。
- 任意識別子・任意 C++・補助関数呼出しを IR に持たせない。

構成子と v1 の対応は次のとおり。

| IR 構成子 | 描画先の v1 規則 | 構成的な保証 |
|---|---|---|
| `Const` | `u`／`ul`、bool literal、完全修飾列挙子 | 型の値域外を IR 検証で拒否 |
| `Reason` | `AbortContext.reason` のメンバ読出し | abort hook のみで使用 |
| `Attempt` | `LockContext.attempt` のメンバ読出し | lock hook のみで使用 |
| `StateRef` | 宣言済み `PolicyState` メンバ読出し | field index と型を検証 |
| `Compare` | 数値比較、同型 bool／列挙型の等値比較 | 結果は bool、bool の算術昇格なし |
| `Select` | bool 条件と同型両枝の `?:` | 部分式に状態変更なし |
| `Min` | 同型 unsigned の `std::min(a,b)` | template 引数等を生成しない |
| `Max` | 同型 unsigned の `std::max(a,b)` | 同上 |
| `SatAdd` | 比較・減算・条件式・加算 | 上限超過する加算を評価しない |
| `SatSub` | 比較・条件式・減算 | 下限未満になる減算を評価しない |
| `Shift` | unsigned 左辺、幅未満の literal 右辺 | 負値・過大 shift なし |
| `StateField` | literal 初期化つき `PolicyState` | 未初期化読出しなし |
| `next_state` | 初期化つき局所宣言 → 独立した代入文 | 自己初期化・順序未定義の書込みなし |
| hook 出力 | 末尾 `return`、`LockResponse{action, wait}` | 必須署名・全経路 return |
| `PolicyIR` | 有限個の宣言・直線的な文 | loop・再帰・任意 call がなく停止 |

v1 実装の対応点は `C/silo_policy_grammar.py:202`、`:252`、`:313`、`:433`、`:471`、`:563`。

飽和演算は、先に同型の純粋な子式を局所値 `a`、`b` に評価し、次の形にする。

```cpp
uint32_t t = a > 4294967295u - b ? 4294967295u : a + b;
uint32_t u = a < b ? 0u : a - b;
```

U64 は `18446744073709551615ul` と `0ul` を用いる。`MAX-b` は常に値域内。加算・減算の危険側は条件式で選択されない。

有界 shift は、例えば `a << 3u`／`a >> 3u`。右辺を変数や括弧つき式にせず literal とする。左 shift は **unsigned の剰余意味論**であり、飽和ではない。待機上限への制限は `Min` で表現する。

`validate_ir()` を `render_policy()` の最初に必ず呼ぶ：

- 葉の深さを 1 として、全出力・次状態式の最大深さ ≤ 4。
- 全 hook の式木の node 出現数の合計 ≤ 64。同じ Python object の再使用も出現ごとに数える。
- field ≤ 4、literal の型・値域、演算子の型、hook ごとの入力範囲を検証。
- field 名は `f0`〜`f3` に固定。名前や整数幅が有限なので、表現空間も有限。
- Python 側の循環参照を拒否し、深さ・node 上限到達時点で探索を打ち切る。

深さ・node 数の数え方は設計 §5 に明記されていないため、上記を段 4 で固定する。

## 2. 描画器

新設 `render_policy(ir) -> str` は、`PolicyState`、abort、lock、commit の固定順で生成する。署名の正本は `C/silo_function_policy_api.hh:11`。

- 型名・列挙子を完全修飾する。`namespace` 外枠・include・macro・コメントは出さない。
- state field は index 順。式は固定の子順で描画し、局所変数を `t0`、`t1`…と採番する。
- 複合式を局所変数に下ろし、飽和演算で子式が重複展開されないようにする。
- 出力・次状態を計算してから field を更新し、最後に return する。
- 使わない state/context 引数は名前を省略する。読み出しだけでなく代入先としての使用も数える。
- 空状態・定数出力では不要な局所変数を作らず、手書き方策と同じ直接 return にする。
- 空白・改行・末尾 newline を固定し、同じ IR から同じ bytes を得る。

例えば無状態の静的 5 µs は `C/silo_function_policy_hand/static5.cpp:1` と同じ形になる。仮引数名省略は D2226 項 1 に従う。

描画結果は必ず既存 `prepare_policy()` に渡す。`C/silo_policy_coverage.py:278` は quarantine／effect gate → grammar／TU compile を実行し、`:295` で検査本文と材料化本文の一致を確かめている。この入口を迂回しない。

IR の深さ 4 と、描画後 C++ の式・文の深さは別物である。描画後の 4096 token 等の制約は既存検査のまま維持し、境界 IR の test で renderer の展開量も確認する。

## 3. 偵察の列挙

**P2 の完全要因 16 点を採用する。ただし「全 IR の列挙」ではなく、次のテンプレート部分空間の全列挙と記す。**

| 因子 | 0 | 1 | IR との対応 |
|---|---|---|---|
| L：lock 応答 | 即 abort | attempt < 4 の間 retry | `Attempt`・`Compare`・`Select(action)` |
| S：状態依存 | 静的待機 | 連続 abort で待機を加算、commit で reset | `StateRef`・`SatAdd`・`Min`・次状態 |
| R：要因依存 | 全 abort に待機 | lock_conflict だけ待機 | `Reason`・等値比較・`Select` |
| M：加算幅 | 5 µs | 10 µs | U32 定数 |

定数の根拠：

- 5／10 µs は段階 C の `static5.cpp:3`／`static10.cpp:3` と設計 §5 の seed。
- retry の閾値 4 は **`retry.cpp` ではなく** `focus.cpp:11` の `attempt < 4u`。`retry.cpp` は常時 retry、最終上限は骨格の 32。
- 状態待機の cap は `C/axis_silo_function_policy.py:11` の 1000 µs。
- lock 待機は 0 µs とする。retry の有無と abort 待機幅を分離し、`retry.cpp` の値を踏襲する。骨格の 50 µs／32 周回は変更しない。

以下の略記で各点を定義する。

- `b = 5u` または `10u`。
- 静的：`X=b`、空状態。
- 状態あり：`f0=0u`、`X=min(1000u, SatAdd(f0,b))`。abort 時 `f0'=X`、commit 時 `f0'=0u`、lock 時保持。
- `G(X) = reason == lock_conflict ? X : 0u`。
- `A`：`{abort,0u}`。
- `T`：`{attempt < 4u ? retry : abort,0u}`。

| ID：LSRM | abort 出力 IR／本文要旨 | abort 後の状態 | lock 本文要旨 |
|---|---|---|---|
| 0000 | `5u` | なし | A |
| 0001 | `10u` | なし | A |
| 0010 | `G(5u)` | なし | A |
| 0011 | `G(10u)` | なし | A |
| 0100 | `min(1000,SatAdd(f0,5))` | 出力と同じ X | A |
| 0101 | `min(1000,SatAdd(f0,10))` | X | A |
| 0110 | `G(min(1000,SatAdd(f0,5)))` | 要因によらず X | A |
| 0111 | `G(min(1000,SatAdd(f0,10)))` | 要因によらず X | A |
| 1000 | `5u` | なし | T |
| 1001 | `10u` | なし | T |
| 1010 | `G(5u)` | なし | T |
| 1011 | `G(10u)` | なし | T |
| 1100 | `min(1000,SatAdd(f0,5))` | X | T |
| 1101 | `min(1000,SatAdd(f0,10))` | X | T |
| 1110 | `G(min(1000,SatAdd(f0,5)))` | 要因によらず X | T |
| 1111 | `G(min(1000,SatAdd(f0,10)))` | 要因によらず X | T |

要因因子は**待機の適用だけ**を変え、状態は全 abort で更新する。これで S は「連続 abort」、R は「待機対象」の意味を保つ。最大の待機式も、葉→飽和加算→min→条件式の深さ 4 に収まる。

攻撃すべき限定：

- 4 因子が全 IR の自然な唯一の分解とは言えない。U64、減算、shift、lock 状態更新等の地形は未探索。
- 16 点すべてが意味的に異なる保証と、当該 workload で異なる動作をする保証は別。後者を追加 probe で保証しない。
- 0000／0001 は C 段の静的 seed と重複する。これは固定 seed の再測として残し、C 段の throughput を転用しない。
- 待機 0・即 abort は 16 点外の `abort0` 対照として 1 回だけ数える。IR でも表し、同じ case に役割を付ける。
- P3 の軸 OFF 2 対照は flags が違う別候補。本文や `src_token` だけで重複排除しない。

## 4. login の機械検査

`Q/test_silo_policy_ir.py` に置くもの：

1. 16 点＋退化点の決定的描画、ID 順、本文 SHA の再現性。
2. 全点の `validate_policy()` と `compile_policy()`。後者は `C/silo_policy_compile.py:101`。
3. 深さ 4/5、node 64/65、field 4/5、型違い、入力の hook 違い、shift 幅境界の受理／拒否。
4. 飽和加減算の 0／MAX／境界値、unsigned shift、同時状態更新の意味を確かめる有限例。
5. 状態あり列挙点の abort 反復→1000 飽和→commit reset、要因による出力差、attempt 3/4/31/32 の action。
6. 未使用引数を省略した本文が実 TU compile を通ること。

login で正式に 1 回実走して記録するもの：

- renderer から専用の一時 `policy_dir` に 16 点＋abort0 の `.cpp` を書く。
- 全点を `check_policy_body()` に通す。
- **ディレクトリを** `run_ubsan_harness(policy_dir, compiler=..., scratch_dir=...)` に渡す。既存入口は `C/silo_policy_compile.py:158`。
- 本文 SHA、IR ID、compiler/version、grammar/TU 結果、UBSan JSON を保存する。
- 既存 harness の全 8 要因 × attempt 0〜33、1904 呼出し／方策、UB 負対照 3 種をそのまま利用する（同 `:120`、`:151`）。
- 結果集合が生成した方策集合と対応することを確認する。UBSan を通常 test のたびに全点実行する運用にはしない。

この有限 harness は算術安全の証明の代替ではない。停止・安全は IR 構成と描画規則で示し、harness は実装の裏取りに使う。

## 5. 偵察 driver

新設 `C/silo_policy_recon.py` に列挙選択・実行・集計を置き、低水準の build/run は増やさない。

**既存 helper の変更は二つに限定する。**

1. `C/silo_policy_coverage.py:546` の `_source()` に keyword `body: str | None = None` を追加する。
   `None` のときだけ従来の手書きファイル読出し（`:559`）。本文指定時も同じ `prepare_policy()` と書込み照合を通す。`stock` と本文の同時指定は拒否する。既存 call は変更しない。
2. `C/silo_policy_coverage.py:362` の `_build_variant()` に、軸 OFF 対照用の `stock_backoff=1` を追加する。
   `stock=True` の場合だけ 0／1 を許す。既定 1 は現在と同じ。軸 ON は現在の `GENOME` 固定を維持する。任意 Genome／任意 configure flags の入口にはしない。

`B0-L-W0` は `Genome("silo", {**locks._BASE, "BACK_OFF": 0})`。根拠は `C/s3_lock_coverage.py:59` と `output/s1-freeze/known_axes_freeze.json:318`。source evidence の算出にも実 build と同じ Genome を使う。

実行順：

1. job 固有 scratch、toolchain、依存物 hydration。
2. `_prepare_build_dependencies()` を job ごとに 1 回。既存位置は `C/silo_policy_coverage.py:719`。
3. 各点の IR 描画→`_source()`→4 段検査→source evidence。
4. `_build_variant(trace=1)`。
5. `_run(..., trace=True)` で legacy／性能構成 verify。
6. 非 certified が出た点は即除外し、bench へ進めない。両 verify の記録は保持する。
7. 両方通過した点だけ `_build_variant(trace=0)`→compile-time の TRACE 除去確認。
8. `_run(..., trace=False, numa=True)` を明示的に 5 回呼ぶ。
9. 前後の source evidence を比較。既存 smoke の手本は `:677`〜`:694`。

`_run()` は `:498` のとおり 1 回実行であり、`PerfConfig.reps=5` だけでは 5 回にならない。`_verify()` は `_run()` 内から呼ばれるため driver から重ねて呼ばない。

workload は以下で固定する。

| 用途 | flags |
|---|---|
| legacy verify | 200 records、4 threads、skew 0.9、rratio 50、rmw true、max_ope 5、extime 1 |
| 性能構成 verify | 1M records、48 threads、skew 0.9、rratio 5、rmw false、max_ope 10、extime 3 |
| bench | 性能構成 verify と同じ、TRACE=0、5 回 |

legacy の正本は `C/pipeline.py:149`。write-heavy は `C/p2_2.py:77`。その workload の `rmw="0"` を `"false"` に正規化し、`max_ope="10"` を足した `PerfConfig` から `performance_correctness_workload()` を使う。この関数は workload の 4 key 完全一致を要求する（`C/pipeline.py:208`）。

`clocks_per_us` は既存 `_run()` の 2100 を維持し、NUMA は既存経路と同じにする。旧 `p2_2.CLK=1800` を転載しない。

TRACE=0 の既存確認（`C/silo_policy_coverage.py:619`）は主に probe/break の不在確認である。その述語だけを「全 trace の除去証拠」と呼ばず、実 owner compile command の TRACE=0 と前処理結果も結果に残す。

**case 部分集合と job 分割**

- `run --cases ID,... --out ...` と `aggregate INPUT... --out ...` を分ける。
- 初走は ID 順の偶数／奇数 index に 8 点ずつ割り付け、各 job に `abort0`・`flagopt`・`stock` を置く。因子 L だけで job が分かれる連番前半／後半分割を避ける。
- 順序は結果を見る前に固定し、JSON に記録する。
- 再測は初走で条件を満たした点の ID と `abort0` を指定できる。再測 job には stock を必須にしない。
- `_run()` が付ける `preliminary_same_job_stock_control=True`（`:541`）は再測には不正確なので、新 driver の結果では実際の対照リストに置き換える。

推奨 JSON の主要項目：

```text
schema_version, space_version, phase, job_id, site, hostname
repo_commit, ccbench_pin, toolchain, workloads, case_order
diagnostic_build_admission, dependency_preparation, complete
runs[case_id]:
  role, factors, ir, ir_id, body_sha256
  genome, src_token, source_evidence
  contract, builds, trace0_evidence
  verify: {legacy, performance}
  bench_reps: [{rep, throughput, commits, aborts, abort_rate, command}]
  median_tps, median_abort_rate, status
```

軸 OFF には policy 本文がないため `ir`／`body_sha256` は null。`src_token` 単独を候補 identity とせず、Genome・PIN・source evidence と一緒に扱う。すべて NON_ADMISSIBLE、verify の有限履歴だけを certified と表現する。

**P4 は同 module の純粋な集計関数で計算する。**

- rep ごとの abort 率は `aborts/(commits+aborts)`、比較値は 5 rep の中央値。
- throughput も 5 rep 中央値。欠測を除いて少ない rep で代用しない。
- high-abort は同 job の abort0 比で `> 2`。基準 abort 率が 0／欠測なら判定不能。先例は `C/s8a_trigger_sweep.py:831`。
- 初走で両 verify 通過・評価可能・`median_tps/base > 1.03` の点を再測対象とする。
- **推奨：初走で床を超えた全点＋基準を別 job で再測する。** 同じ点が再測でも全条件を満たせば「あり」。
- 「なし」は「この固定部分空間で、再現する床超点を観測しなかった」の意味に限定する。high-abort／anomaly／欠測件数は別掲する。
- job 未完了、基準失敗、必要な再測未実施、評価可能点がない場合は二値を null とする。欠測を false に変換しない。

詳細は偵察 JSON／insight 内に留め、後段への投影は限定つき二値だけにする。

## 6. 既存登録簿・閉集合 test への波及

**段階 C は新 sink を増やしている。** `_build_variant()` に build 呼出し、`_run()` に直接 subprocess 呼出しが存在し、登録済みである。今回それらを再利用して追加を避ける。

| 既存箇所 | 今回の扱い |
|---|---|
| `Q/test_ccbench_spawn_sites.py:73` | `_run` の直接 run site 登録は不変 |
| 同 `:92` | TU／UBSan の subprocess 登録も不変 |
| 同 `:2933` | `_build_variant` の **382 行 pin** は編集後の実際の行へ追随 |
| 同 `:2939` | configure/build/preprocess/verify helper の呼出し完全一致は維持 |
| 同 `:2919` | condition gate と build sink の交差検査を再実行 |
| `C/materializer_admission.py:103` | 既存 NON_ADMISSIBLE 登録を再利用。必要なら説明を coverage/smoke/recon に更新 |
| `Q/test_p3_build_authority_cli.py:158` | 新 module に直接 build を置かないので `MANUAL_BUILD_FILES` は不変 |
| 同 `:178`、`:1226` | NON_ADMISSIBLE 集合は不変、閉集合 test を再実行 |
| `Q/test_p3_s4_loop.py:2204` | `render_hole` 入口は quarantine のみを維持。新 renderer から直接呼ばない |
| `Q/test_silo_policy_coverage.py:498` | 4 段検査と本文結合の既存 test は維持 |
| 同 `:538`、`:686` | gate 支配と依存物準備の既存 test は維持 |
| `Q/test_silo_policy_smoke_entry.py:82` | 従来 smoke の拒否順序・本文一致・timeout test はそのまま通す |

新しい build wrapper を材料化主体として導入する場合は、`MaterializerSiteKind.DELEGATING_MATERIALIZER`（`C/materializer_admission.py:35`）と期待集合への追随が必要になる。推奨構成では新 wrapper を作らず、既存 helper の receipt を保存する。

新 driver の test は `Q/test_silo_policy_recon.py` に置く：

- 指定本文が実 4 段検査を経る接続試験。
- stock／flagopt／IR の flags と source evidence の一致。
- verify 失敗時に bench が 0 回、成功時に 5 回。
- subset 実行、同 job 基準の参照、再測の別 job、3%／2 倍境界、欠測の集計。
- 既存 coverage/smoke の既定動作を変えず、新引数だけを検証する。

## 7. node 時間の見積りの材料

正常な 1 点の処理は次のとおり。

| 処理 | 回数 | 留意点 |
|---|---:|---|
| IR 描画・4 段検査 | 1 | TU compile を含む |
| source identity 導出 | 前後 | preprocess 等の費用あり |
| TRACE=1 build | 1 | configure・condition gate を含む |
| legacy trace＋verifier | 1 | 小規模 workload |
| 性能構成 trace＋verifier | 1 | write-heavy、1M／48 threads |
| TRACE=0 build | 1 | compile-time 除去の確認 |
| bench | 5 | 各 3 秒＋起動／初期化／終了処理 |

job ごとに dependency hydration/install と準備 stock build が別途ある（`C/silo_policy_coverage.py:719`、`C/s3_mocc_lock_coverage.py:224`）。

段階 C の実測は `output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md:91` の **793 秒／5 case**。これは方策ごとの測定単価ではなく、job 固有費も含む平均である。

算術的なシナリオ換算だけなら：

- 初走は 22 case 実行なので、`793 × 22/5 = 3489.2 秒 ≈ 0.97 node 時間`。
- bench 追加 4 rep の指定 extime は `22 × 4 × 3 = 264 秒`。
- ただし起動費、依存物の二重準備、write-heavy の trace／verifier 費用、IR build 差、再測、受入試験はこの加算で評価できない。

**これを上下限・確定単価として提示しない。** 特に C 段 smoke は balanced（`C/silo_policy_coverage.py:52`）であり、write-heavy verify の上乗せ量は未測定。

再測対象が k 点なら `k+1` case と job 固有費を追加する。初走 2 job を同時投入しても、node 時間は各 job の Elapse の和。段 4 では再測・焦点試験・受入も含めて用途別に積み上げ、投入前確認へ渡す。

## 8. 所有 path の分割

| 単位 | 専有 path | 依存・成果物 |
|---|---|---|
| A | 新設 `C/silo_policy_ir.py`、新設 `Q/test_silo_policy_ir.py` | IR・validation・renderer・列挙・機械検査用 export |
| B | 新設 `C/silo_policy_recon.py`、新設 `Q/test_silo_policy_recon.py`、既存 `C/silo_policy_coverage.py`、`Q/test_ccbench_spawn_sites.py`、必要時 `C/materializer_admission.py`／`Q/test_p3_build_authority_cli.py` | A の固定 interface を利用、本文入口・flagopt 対応・実行・集計 |
| 親 | 結果 JSON、insight、逐語・裁定・統合記録 | 検査結果の凍結、投入見積りと人間判断 |

A→B の interface を先に固定する：

```python
enumerate_recon() -> tuple[ReconCase, ...]
degenerate_policy() -> PolicyIR
validate_ir(ir) -> None
render_policy(ir) -> str
canonical_ir(ir) -> dict
```

`ReconCase` は ID・因子・IR を持ち、性能結果を持たない。A は coverage を変更しない。B は IR を変更しない。既存 coverage/smoke test ファイルは変更せず、追加分は新 test に置く。

login 正式検査の出力は A が親へ返し、repo 内の凍結記録は親が所有する。B の単独作業で列挙点や定数を調整しない。

## 9. brief の誤り

1. **P1 は本文入口だけでは不足。** 現 `_build_variant()` は stock／軸 ON の二択で、flagopt の `BACK_OFF=0` を作れない（`C/silo_policy_coverage.py:372`）。狭い追加引数が必要。
2. **段階 C が sink を増やさなかったという仮説は誤り。** 新 run site は同 `:500` に明記され、build sink も登録済み。今回の目標は、その追加済み経路の再利用。
3. **P2 の「retry 上限」の出所が曖昧。** `retry.cpp` に方策側の閾値はない。4 を採るなら `focus.cpp:11`、32 は骨格定数と区別する。
4. **P3 の abort0 と B0-L-W0 の「同じ意味論」は限定が要る。** 待機 0・no-wait 方針は対応するが、軸 ON は hook・要因記録・32 周回上限等を持つ。差を純粋な骨格実行コストと断定しない。
5. **P4 の high-abort 規則は D46 の逐語そのままではない。** D46 は stock 比、trigger の先例は ident_all 比。今回の abort0 比は新軸での選択として固定する。基準率 0／欠測の扱いも必要。
6. **P4 は複数の初走床超点と再測失敗の扱いが未定義。** 1 点だけ再測して失敗しても、他点の再現可能性は否定できない。全該当点再測を推奨する。
7. **P5 は 19 unique case、22 case 実行。** 8 IR＋3 対照を 2 job で回すため、対照 3 本を重複計上する。
8. **P5 の分割だけでは各 job が 1 時間以内とは保証できない。** 再測が最大 17 case になる点も含め、段 4 の見積り次第では分割変更が必要。
9. **P6 の約160秒／方策は観測単価ではない。** 793 秒は balanced、bench 1 rep、依存物準備込みの job 実測。write-heavy への倍率は根拠がない。
10. **既存 TRACE=0 確認の射程が狭い。** probe/break 不在確認を trace 全体の消失証明と取り違えない。
11. **floor 3% は本軸で較正された値ではない。** `C/p2_2.py:59` の過去の between-run 指標を暫定流用する。再測成功でも軸全体の優劣・探索法の優劣は主張しない。

## 総括

- 純粋な型付き式木＋同時状態更新で、深さ4・node64・状態4 fieldを描画前に検証する。
- 16点は固定テンプレートの完全要因。abort0を別対照とし、計19 unique case。
- 既存の4段検査・build・run・verifyを再利用し、新しい低水準sinkを作らない。
- 必要な既存変更は本文入力と軸OFFのBACK_OFF指定、行番号pin等の追随。
- 初走は22 case実行。再測・job固有費・受入も合計見積りに含める。
- 未決：node/depthの計数法は本案、再測は初走床超点すべてを推奨。
- 欠測・基準失敗・未再測を「なし」にせず、二値未確定として残す。
- 最大の限定は部分空間の狭さ、floorの未較正、verify/perfの分岐一致を保証しない点。
- 後段へ渡すのは限定つき二値のみ。今回は静的検査のみで、実行結果はない。