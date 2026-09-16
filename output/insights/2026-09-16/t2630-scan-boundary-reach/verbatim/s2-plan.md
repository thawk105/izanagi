## probe test の設計 (file:line)

**M3a/M3b を主候補、M6 を TRACE 漏れ候補とする。M4 は前処理差の候補として残すが、現物ではコンパイル不能になるため「実行可能な別挙動への到達例」には数えない。** この段では読み取りと静的検査だけを行った。pytest・configure・前処理・コンパイルは未実走。

新設先は `orchestrator/tests/test_t2630_scan_boundary_reach.py`。probe branch のみに commit し、その tip の clean な別 worktree を harness に渡す。以下の新規行番号は**実装時の配置案**であり、既存行番号ではない。

| 新規配置案 | 内容 |
|---|---|
| `:20` | pin、carrier path、2 genome、証拠出力先 |
| `:40` | 固定 HEAD の template bytes と現在の carrier bytes の独立取得 |
| `:65` | 独立 local clone と `patchharness.checkout` |
| `:95` | 実 `resolve`、preimage、TRACE 検査結果の採取 |
| `:130` | 実 configure → owner compile command → 前処理 |
| `:190` | reference/current の観測を保存する helper |
| `:230` | N1a `test_stock_identity` |
| `:240` | N1b `test_variant_identity` |
| `:250` | N2a `test_stock_owner_tu` |
| `:260` | N2b `test_variant_owner_tu` |

**木と比較基準**

- pin は `p3_s4_loop.py:112` の `511c9538e4e8efa54b45cda62e72389ed3b706ec`。
- reference patch は **superproject の固定 HEAD** に対する `git show <HEAD>:patches/silo-backoff-fixed.patch` の bytes。current patch は working tree の同 file の bytes。両者を同じ読み出し元にしない。
- 共有 submodule は object の読み取り元に限る。job scratch に `git clone --no-hardlinks --no-checkout <external/ccbench> <clone>` を作り、pin の存在と tree OID を確認する。共有 submodule に checkout/apply/worktree-add しない。
- `patchharness.checkout(PIN, base_dir=clone)` が返す **同一 path** 内で、reference を `applied()` →観測→復元、current を `applied()` →観測→復元する。reference/current で root を変えると、`__FILE__` 展開などが偽の差になるためである。
- configure/build directory は source tree 外の scratch。reference/current の対応する genome では directory path も揃え、再 configure する。

[patchharness.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2630-scan-boundary-reach/orchestrator/campaign/patchharness.py:315) の guard は common-dir の canonical path **または** inode が実共有 checkout と同じ場合に登録を要求する。独立 clone なら両方異なる。`checkout:346` はこの判定後に clone 側へ worktree を登録し、`applied:247` は pinned-clean、apply、finally で復元する。

`conftest.py:532,659,2137,2223` の writer 登録を広げる案は、共有 submodule を書く権限・ロック対象を増やしてしまう。この probe はそれを必要としないため、**登録変更なしの local clone 案を採る**。guard の monkeypatch や pytest context の解除はしない。

**genome と compiler**

```python
stock = model.Genome("silo", {"BACKOFF_FIXED": -1})
variant = model.Genome("silo", {"BACKOFF_FIXED": 1})
```

`model.py:125,136,147` の実 `Genome` を使う。`1` は synthetic 枝を確実に live にし、M1 の `+1.0` と区別できる。`TRACE` は genome に入れない。

`buildcache.compilers_for_current_site():1861` を compute 上で呼び、返された `gcc/g++` を実 path に解決して CMake と digest の双方へ渡す。version と executable hash も保存する。**login ではこの helper は `gcc-13/g++-13` を返す**ので、親の「helper を使えば g++ 11」という前提は compute 限定である。

**4 node の契約**

| Node | 実呼び出しと比較 |
|---|---|
| N1a | reference/current 双方で `source_digest.resolve(stock, PIN, root, cxx)`。reference と current の token を UTF-8 bytes として `b"stock"` に比較 |
| N1b | reference/current 双方で `resolve(variant, …)`。reference token が非 stock であることを確認し、current token bytes と比較 |
| N2a | current の `resolve(stock, …)` が正常終了することを前提に、reference/current の stock 実 TU 前処理 bytes を完全比較 |
| N2b | current の `resolve(variant, …)` が正常終了することを前提に、reference/current の variant 実 TU 前処理 bytes を完全比較 |

N2 は token **一致**を前提にしない。これにより M1 は N1b と N2b の両方で赤になり、M2 は resolve 拒否によって全 node で赤になる。

`source_digest.py:2436` の実 `resolve` は allowlist、include 一致、macro coverage を通す。`compute:2117` のみを呼ぶ代用はしない。併せて `canonical_source_preimage_bytes:2100` を保存し、token 一致がどの bytes に由来したかを説明できるようにする。

観測は単一 process 内で共有してよいが、失敗を fixture setup の `ERROR` にしない。観測 helper は例外の種類・段階・詳細を保持し、各 node の call 内で失敗させる。これで harness の `FAILED` node 署名を得る。環境不足を skip して baseline 緑にしない。

## 別挙動証拠の取り方

`condition_meaning_gate.py:807,849,1683,1775,2056` の実関数を次の順で使う。

1. `capture_define_inputs(root, configure_args=…)`。
2. `make_define_request(driver_id="t2630-scan-boundary-reach", macro="BACKOFF_FIXED", requested_value=value, default_value=-1)`。
3. `_configure_compile_commands(..., value=str(value), companions=(), compiler=<実cxx>, cmake=<実cmake>)`。
4. `_select_owner_entry` で `cc/silo/transaction.cc`、target `ycsb_silo.exe` の唯一の entry を選ぶ。
5. `_entry_argv` → `_preprocess_argv`。`allowed_defines=frozenset()` とし、この同一 genome 比較では define の相違を比較対象から除かない。
6. entry の `directory` を cwd にして生成 argv を実行。stdout を **bytes のまま**保存する。

`_preprocess_argv:2056` は compile command の `-c`、出力・依存 file 指定を外し、`-E -P -MD -MF <scratch>` を加える。include path、実 compiler、警告・最適化・define は残す。digest 用の `-nostdinc` を実 TU 側へ持ち込まない。

configure 引数は `p3_s4_loop.py:346` の `_condition_gate_offline_configure_args` で生成する。

```text
-DCMAKE_PREFIX_PATH=/work/SFC/tanab/ss2pl-study-deps/gflags-install;/work/SFC/tanab/ss2pl-study-deps/glog-install
-DFETCHCONTENT_BASE_DIR=<job固有scratch>/fetchcontent
-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree
-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=/work/1/SFC/tanab/izanagi-thirdparty-cache/mimalloc
-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/work/1/SFC/tanab/izanagi-thirdparty-cache/googletest
```

さらに `-DCMAKE_BUILD_TYPE=Release`、`-DENABLE_SANITIZER=OFF`、実 `-DCMAKE_C_COMPILER=…`、`-DCCBENCH_TRACE=0` を渡す。prefix は CMake argv では **semicolon 区切りの1引数**。環境変数で渡す場合の colon 区切りと混同しない。

**cache を書かない根拠と限界**

- `external/ccbench/cmake/ThirdParty.cmake:66` の masstree 生成は build 用 custom command。configure だけでは `bootstrap/configure/make/ar` を実行しない。
- `:58,85` により、既存 cache の `config.h` が実 include path から読まれる。
- mimalloc の `CMakeLists.txt:735` の `configure_file` は binary directory に出力する。FetchContent base と build root を scratch に分ける。
- `buildcache.prepare_masstree_fetchcontent:2032` は **build を実行する関数**なので、この probe では呼ばない。
- configure も任意の CMake 処理を実行し得るため、「build しない」だけで cache 全体の不変を証明したとはしない。生死実験で cache の tracked/ignored を含む file inventory・内容 hash の前後差を確認する。これは当該実験の記録であり、新しい gate は設けない。

実 CCBench pin、実 template、実 CMake、実 dependency headers を使うため stub ではない。ただし既存 `config.h` の生成条件、compiler、依存 pin に限定された観測である。T-2650 の §5 は最小 project の実験なので、本 probe の実機成功を代替しない。

**保存する証拠**

patch SHA、genome、pin、compiler、configure/compile/preprocess argv、cwd、rc/stderr、前処理 bytes と SHA、dependency file、reference/current の `.diff.txt`、resolve token/preimage、TRACE 検査の成否を job 外部証拠 directory に保存する。harness stdout にその path と SHA、失敗段階を出す。

`_preprocess_evidence:2325` は既存 `_PreprocessResult` の記録器であり、比較実行器ではない。`_collect_preprocess:2210` を使う場合は、その実結果から `_preprocess_evidence` を生成できる。架空の結果 object を作って「既存 gate の証拠」としない。

**should：object 比較**

計算ノード上で元の compile command を使い、出力・依存 file の行先だけ scratch に変えて `-c` する。警告抑制は足さない。両方成功したら `objdump -drC` の該当関数、特に `TxExecutor::read` / `abort` の差を保存する。file banner や debug path の差と命令差を分ける。

`-E` 差は前処理されたプログラムの差、object 差は生成コード差であり、どちらも workload 上の実行結果差や link 成功を単独では保証しない。`cmake --build` は本設計では呼ばず、本走は compute dispatch とする。

## 変異 spec (各 replacement の old/new と仮説)

`tools/mutation_harness.py:481,532` の exact-key 契約は次のとおり。

```text
root:
  schema, estimated_run_seconds, timeout_seconds,
  hang_timeout_seconds, mutations

mutation:
  id, category, replacements, expected_nodes,
  expected_status, hang_risk

replacement:
  file, old, new
```

`schema="izanagi-dev-wave-mutation-spec/v1"`。category は `negative / positive / both-layers` のみ。全件 `hang_risk=false` とし、M0/M1/M2 は `positive`、M3a/M3b/M4/M6 は `negative` とする。これは登録上の分類であり、到達判定は署名と証拠で行う。

以下、全 replacement の `file` は `patches/silo-backoff-fixed.patch`。文字列は Python 表記で、`\n` は LF。記号による連結は spec 作成時に展開し、JSON に補助 key は入れない。

```python
H1 = "@@ -11,6 +11,15 @@\n"                 # patch:32
H2 = "@@ -91,9 +100,29 @@ public:\n"        # patch:48
TOP = ' #include "util.hh"\n \n'           # patch:34
BRANCH = "+#if BACKOFF_FIXED >= 0\n"       # patch:69
ELSE = "+#else\n     double now_backoff"   # patch:71
END = "     // static_cast<uint64_t>(static_cast<double>(clocks_per_us) * now_backoff));\n"
```

**M0：comment-only**

```python
old = "+# izanagi: static backoff magnitude (us) to bypass Cicada's adaptive hill-climb.\n"
new = "+# izanagi: static backoff magnitude (us) to bypass Cicada's adaptive hill-climb. T2630 comment-only.\n"
```

同じ行数なので hunk 更新なし。`expected_status="SURVIVED"`、`expected_nodes=[]`。

**M1：synthetic 枝の正例**

順序付き replacement：

```python
old = H2
new = "@@ -91,9 +100,30 @@ public:\n"

old = ELSE
new = "+    now_backoff += 1.0;\n+#else\n     double now_backoff"
```

追加1行。期待は `KILLED [N1b, N2b]`。stock 枝は不変。

**M2：include-match の正例**

```python
old = H1
new = "@@ -11,6 +11,16 @@\n"

old = H2
new = "@@ -91,9 +101,29 @@ public:\n"

old = TOP
new = TOP + "+#include <cstdint>\n"
```

第1 hunk が1行増えるので、第2 hunk の new start も `100→101`。期待は `KILLED [N1a,N1b,N2a,N2b]`。実 TU の差ではなく、`assert_includes_match_head` 拒否を正例として読む。

**M3a：synthetic 枝から macro が漏れる候補**

```python
old = H2
new = "@@ -91,9 +100,31 @@ public:\n"

old = BRANCH
new = BRANCH + "+#undef SLEEP_READ_PHASE\n+#define SLEEP_READ_PHASE 1\n"
```

期待は `KILLED [N2b]`。backoff 単独の digest では指令が消費される一方、実 TU では `transaction.hh:9` から backoff を include した後、`transaction.cc:278` の `sleepTics(1)` が有効になる仮説。

「兄弟 variant 衝突」は **同じ genome、異なる patch の variant 同士**という意味に限る。異なる genome の identity 衝突ではない。

**M3b：top-level から stock identity を継承する候補**

```python
old = H1
new = "@@ -11,6 +11,17 @@\n"

old = H2
new = "@@ -91,9 +102,29 @@ public:\n"

old = TOP
new = TOP + "+#undef SLEEP_READ_PHASE\n+#define SLEEP_READ_PHASE 1\n"
```

期待は `KILLED [N2a,N2b]`。N1a 緑なら stock token 継承、N1b 緑なら同一 genome の reference variant token 継承である。

**M4：transaction.cc の include 挟み込み**

EOF の一意 anchor を置換して別 file の diff を追加する。

```python
old = END
new = END + (
    "diff --git a/cc/silo/transaction.cc b/cc/silo/transaction.cc\n"
    "--- a/cc/silo/transaction.cc\n"
    "+++ b/cc/silo/transaction.cc\n"
    "@@ -2,7 +2,9 @@\n"
    " #include <algorithm>\n"
    " #include <string>\n"
    " \n"
    "+#define desired expected\n"
    ' #include "include/atomic_tool.hh"\n'
    "+#undef desired\n"
    ' #include "include/log.hh"\n'
    ' #include "include/transaction.hh"\n'
    ' #include "include/scan_callback.hh"\n'
)
```

old 7行、新9行。include 行の列は同一で、`source_digest.py:96` の allowlist に transaction.cc は含まれる。期待署名は `KILLED [N2a,N2b]`。

ただし `cc/silo/include/atomic_tool.hh:10` が `uint64_t expected, expected;` に変わる。**これは C++ の再宣言エラーになるため、実行可能な到達例ではない。** `git apply` 成功とコンパイル成功を混同しない。後続の `-c` で拒否を記録する対照として残す。

**M6：TRACE 漏れ**

```python
old = H1
new = "@@ -11,6 +11,17 @@\n"

old = H2
new = "@@ -91,9 +102,29 @@ public:\n"

old = TOP
new = TOP + "+#undef TRACE\n+#define TRACE 1\n"
```

期待は `KILLED [N2a,N2b]`。`TRACE=0` の実 compile command でも、include 後の transaction 本体の trace 条件が有効になる仮説。

`assert_trace_diff_matches_head:2174` は別途**実行して成否を記録**する。N1 の失敗条件へ混ぜず、identity 到達と TRACE 防壁の通過を別に判定する。backoff 単独には対応する trace 本体がなく、transaction 単独では backoff の再定義を読まないため、静的には通過が予想される。link 成功・最終 binary の trace-symbol 検査通過は未証明。

M5/M7 は任意なので初回 matrix から外す。

**静的検査結果**

上記7件を元 patch bytes へ独立適用し、各 replacement の累積 anchor count がすべて **1** であることを確認した。`git apply --numstat -` は全件 rc=0。したがって hunk の構文・行数は整合している。**pin への `git apply --check` は未実施**であり、生死実験で確認する。

実 spec の node は省略名ではなく、例えば次の完全名に展開する。

```text
orchestrator/tests/test_t2630_scan_boundary_reach.py::test_variant_owner_tu
```

初回の集合を確定できない場合だけ、DW-M08 に従い exploratory spec を全件 `SURVIVED / []` として観測する。予想した赤は `MISMATCH` になり得る。初回台帳を残し、erratum と再登録で完全集合を確定する。

carrier を probe 内定数にすれば hunk 算術は減るが、製品 template を `applied()` する経路から離れる。今回は **template carrier を採る**。固定 HEAD の reference と working-tree carrier の分離が必須である。

## harness 投入形と所要見積り

probe tip の clean な別 worktree を `REPO`、checkout 外の job directory を `JOB` とする。次は親が実行する argv の形であり、この段では投入していない。

```bash
env \
  IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600 \
  IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600 \
  IZANAGI_DISPATCH_WALLTIME_OVERRIDE=01:00:00 \
  python3 "$REPO/tools/mutation_harness.py" \
    --repo "$REPO" \
    --spec "$JOB/mutation-spec.json" \
    --expected-spec-sha256 "$SPEC_SHA256" \
    --out "$JOB/mutation-out.json" \
    --attempt-out "$JOB/mutation-attempt-1.json" \
    --wrapper-attempt 1 \
    --runner-mode dispatch \
    --detached \
    -- python3 tools/run_tests.py -rf \
       orchestrator/tests/test_t2630_scan_boundary_reach.py \
       -n 0 --force-dispatch
```

- `-rf` は failed node 抽出に必須。`-n 0` で module 内観測の共有と逐次適用を保つ。
- `--detached` は自己申告 flag であり、自動的な detach ではない。親が外側時間制限のない既存起動経路を使う。
- `--attempt-out` / `--wrapper-attempt` は同時指定し、再投入では更新する。
- spec/out/attempt-out は checkout 外。harness 自体に `--scratch-root` はない。外側 dispatcher を使う場合、その scratch と out を同一 device に置く。
- harness と runner は同一 Python executable。runner・test・carrier は固定 HEAD に束縛される (`mutation_harness.py:775,882,1042`)。
- 親や子が編集中の木では実行しない。

暫定値：

```json
{
  "estimated_run_seconds": 240,
  "timeout_seconds": 8100,
  "hang_timeout_seconds": 3000
}
```

hydrate なし、local clone、4 configure、実 TU 前処理4回、identity 前処理群で **1 run 60〜240秒を仮置き**する。未実測なので生死確認で更新する。object 比較はこの見積りに含めず、候補ごとの追加観測に分ける。

7変異＋baseline で8 run、harness 表示上の見積りは **1,920秒**。collection と各 dispatch の待ち時間は別である。

`timeout_seconds` は test CPU 時間ではなく、dispatch runner の待機も含む。D612 の queue 3600秒＋walltime 3600秒＋grace 600秒＋余裕300秒で8100秒とする。collection の最低契約 `3600+600` も満たす (`mutation_harness.py:1454`)。全件 hang-risk false なので3000秒は未使用だが、job walltime より短くする。

参照先に注意がある。現行 `tools/pegasus/README.md` §7 は **P3 loop job body** の説明であり、mutation dispatch の envelope ではない。generic/dispatch 契約は `docs/pegasus-runbook.md` §7、実 timeout は `dispatch_compute.py:67` と harness/run_tests の D612 上書きを根拠にする。

## 生死実験

本走前は以下の順とする。

1. **login で patch 適用可能性を確認。** 独立 local clone の pin に対し、未変異 template と7変異すべてを `git apply --check`。`--recount` は使わない。構文・行数・context の問題をここで排除する。
2. **compute で依存供給を確認。** `dispatch_compute.py --task generic --walltime 00:15:00 -- <argv>` で既存 `python3 -m orchestrator.campaign.condition_meaning_gate` CLI を投入する。独立 clone に template を当て、`BACKOFF_FIXED=1/default=-1`、`--cxx g++`、前節の configure args を `--configure-arg=<1引数>` で渡す。`--meaning-case` は付けない。既存 CLI の supply 証拠で owner TU の非空前処理が得られたかを見る。最終 rc だけで判断しない。
3. **cache の前後不変を確認。** `config.h` と依存 tree の生成物を含めて比較する。欠落時に共有 cache 上で prebuild することは、この設計に含めない。
4. **baseline 4 node を1走。** `python3 tools/run_tests.py -rf <probe path> -n 0 --force-dispatch`。reference/current を実際に別々に前処理し、4 passed・0 skipped を本走の条件とする。
5. **M0→M1→M2 の対照。** M0 全緑、M1 `[N1b,N2b]`、M2 全4 node の include 拒否を確認してから主候補へ進む。

login baseline は `-E` だけなので実行可能性はあるが、compiler helper の既定不一致がある。試すなら probe 専用の明示 compiler 指定で両側を同一 system compiler に揃え、必ず `run_tests.py` の admission に従う。site を偽装しない。今回の親指示を優先し、**標準手順は compute とする**。login で `cmake --build` を拒否された場合の迂回は設計しない。

## 恒真回避

- N2 reference は必ず固定 HEAD の template 適用木。現在の変異 carrier を両側に当てない。
- baseline でも current/reference をそれぞれ実前処理する。patch bytes が同じだから出力を流用する最適化はしない。
- stdout 非空、owner TU 一意、compile command の genome 値・TRACE 値・compiler 一致を確認する。失敗時に `b""` を返さない。
- 同一 root/cwd を使って位置差を抑える。残った `__LINE__` 等の差は raw diff に残し、意味差と分類する。
- M1 が赤にならなければ current carrier の未読・synthetic 枝 dead・比較流用を疑う。M2 が赤にならなければ `resolve` の未駆動を疑う。M0 が赤なら比較環境・位置依存・非決定入力を先に調べる。
- M3/M6 の N2 赤は、`sleepTics(1)` や trace 呼び出しという**対応する差**まで確認する。configure 失敗や単なる位置差を到達と数えない。

到達の記録には、少なくとも **実 resolve 成功、継承 token の特定、非位置的 TU 差、差の原因となる include/macro 経路**が必要である。実行可能な別挙動という主張には、さらに compile/link または対象実行の証拠が必要になる。

「未到達」は、注入実在と検出力を確認したその変異・genome・compiler・依存条件に限定する。拒否、等価化、コンパイル不能、観測不足を区別する。この有限 matrix が全緑でも、走査境界一般の不存在証明にはならない。

## 親 brief への反論

| 前提・仮説 | 現物に基づく評価 |
|---|---|
| P1 local clone | 支持。guard は common-dir path/inode 同一性による。独立 clone に限定すれば登録変更不要 |
| P2 cache 直指し | 条件付き支持。masstree の書き込み custom command は build 時。ただし configure 全体の非書き込みは自動では保証されず、依存 source と生成物の前後確認が必要 |
| P3 node 署名 | 支持。ただし同じ N2 赤でも、意味差・位置差・環境失敗を区別する必要がある |
| P4 template carrier | 支持。7件の anchor 一意性と hunk 構文を静的確認済み。pin への適用確認は未実施 |
| P5 probe 非 land | 支持。「repo に一度も入れない」ではなく「一時 probe branch に tracked commit、wave/main 非 land」という意味 |
| M3a 兄弟衝突 | 同一 genome・異なる payload の token 衝突という仮説なら妥当。stock 継承の例ではない |
| M4 挟み込み | include 一致・allowlist 通過の仮説は妥当。ただし `expected` の重複宣言を作るのでコンパイル可能な到達例にはならない |
| M6 TRACE 検査通過 | 非再帰な file 単独検査から通過を予想できる。ただし `resolve` 自体は TRACE diff 検査を呼ばないため、別途実関数を呼んだ証拠が必要 |
| compiler | `compilers_for_current_site()` が system compiler を返すのは compute のみ。login の g++-13 不在を解消する helper ではない |
| 「許された variant」 | この probe が示すのは名指した identity/TRACE 検査の受理。coder 編集契約、auditor、pipeline 全体の受理まで証明したとは扱えない |
| stock certified 結果の継承 | token 衝突だけでは実際の receipt/cache 消費まで実測したことにならない。今回の観測範囲を明記する |

## 総括

設計は実装可能で、**M3a/M3b が主候補、M6 が追加候補**。M4 はコンパイル不能の対照として扱う。

静的確認では全7変異の anchor は一意、patch hunk 構文は正常だった。次は親が独立 clone で `git apply --check`、compute の configure＋前処理、baseline と正負対照を実走する。現時点で到達・pytest 緑・cache 不変を実測済みとは報告しない。