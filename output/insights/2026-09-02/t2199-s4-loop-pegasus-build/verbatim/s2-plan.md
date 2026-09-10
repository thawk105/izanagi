## 総括

最有力原因は、condition gate が CMake configure 直後に owner TU を preprocess する一方、Masstree の `config.h` は build-time custom target が生成するため、fresh offline source では未生成なことです。確信度は 0.85 です。
この preprocess 問題単独なら、job-private hydrate、Masstree 事前 build、CMake wrapper による pinned `FETCHCONTENT_SOURCE_DIR_*` 注入で `tools/pegasus/` 内から解けます。
ただし preprocess 通過後、Pegasus compute は `linux-baremetal` authorization を明示拒否します。`p3_s4_loop.py` の site-aware contract 化が必要で、編集面の外です。
したがって、現行 scope の job script だけで「Pegasus 上で build 到達」は達成不能です。実装へ進まず親へ返すべきです。
実行場所として直ちに安いのは `linux-baremetal`、つまり cygnus です。同じ loop の 4 iteration certified 実績があり、Pegasus は 6 投入で未到達です。これは Pegasus 既定を覆す実測根拠になります。
以下は静的検査結果です。pytest、configure、preprocess、build は実走していません。

## Q1 preprocess 失敗の code path

### 呼出し連鎖

1. `run_one_iteration()` は patch 適用と diff quarantine 後、build より前に `_require_condition_gate()` を呼びます。[p3_s4_loop.py:1414-1428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1414)
2. `_require_condition_gate()` は実 site から compiler を選び、source root を capture し、`BACKOFF_FIXED` request を作って supply arm を評価します。[p3_s4_loop.py:130-153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:130)
3. `BACKOFF_FIXED` は `cmake-cache-option` route、owner TU は `cc/silo/transaction.cc`、target は `ycsb_silo.exe` です。[condition_meaning_gate.py:68-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:68)
4. supply evaluator は一時 root 内に requested/control build tree を作り、両方を CMake configure します。[condition_meaning_gate.py:1608-1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1608)
5. `compile_commands.json` を読み、owner TU と target marker が一致する entry を一意に選びます。[condition_meaning_gate.py:1459-1503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1459) [condition_meaning_gate.py:1543-1573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1543)
6. compile argv を preprocess argv に変換し、requested、control の順に `_collect_preprocess()` を実行します。[condition_meaning_gate.py:1789-1842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1789) [condition_meaning_gate.py:2088-2152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:2088)
7. `ConditionMeaningGateError` は supply の red record に変換され、`p3_s4_loop` が reason code だけを例外文へ出します。[condition_meaning_gate.py:2205-2223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:2205) [p3_s4_loop.py:151-158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:151)

### `preprocess-failed` の全送出条件

literal の出現は3箇所だけです。[condition_meaning_gate.py:1995-2012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1995)

| 発火元 | 送出条件 | 効く環境入力 |
|---|---|---|
| compiler `--version`、1995-1997行 | `_run_process()` が process を起動できない | compiler 実体、PATHからの解決、実行権限、dynamic loader、資源不足 |
| 同 | return code が非0 | compiler 実体と version 動作 |
| 同 | rc=0でも stderr が1 byte以上 | compiler/version の出力仕様 |
| owner TU preprocess、1998-2001行 | process 起動失敗 | compiler 実体、entry の cwd、消えた build tree |
| 同 | return code が非0 | compile entry、include path、generated header、`-D`、source/build tree、cwd |
| 同 | rc=0でも stderr が1 byte以上 | compile flags、警告、header/toolchain の組合せ |
| version stdout 検査、2011-2012行 | UTF-8 decode後、先頭行が無いか空 | compiler `--version` の stdout |

共通の process 判定は、timeout、起動例外、非0、stderr 非空を別々に扱います。[condition_meaning_gate.py:1370-1399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1370)

環境で解けるものは、PATH上の正しい compiler/CMake、実在 cwd、完全な source/build tree、必要な include/generated header、offline dependency、警告を生まない実効 argv です。timeout値の変更、stderrを許す変更、allowed define集合の変更、空のversion出力を別媒体で補う変更は code 側であり、gate の編集または緩和になるため本 wave では不可です。

`allowed_defines` は request macroとcompanionから固定生成されます。[condition_meaning_gate.py:1981-1992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1981) ただし `_preprocess_argv()` は allowed defineだけを実 argvへ残す実装ではありません。allowed defineを比較用 argvから除外し、それ以外も `kept` に残します。[condition_meaning_gate.py:1824-1842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1824) よって今回の失敗を「allowed set不足」と推定する根拠はありません。

### 隣接 reason との境界

- `preprocess-timeout`: 120秒を超え、`TimeoutExpired` になった場合だけです。前 wave の `preprocess-failed` はこれではありません。[condition_meaning_gate.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:225) [condition_meaning_gate.py:1385-1389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1385)
- `preprocess-unsupported-input`: process 起動前に response file、PCH、module optionを見つけた場合です。[condition_meaning_gate.py:1797-1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1797)
- `preprocess-output-empty`: preprocess が rc=0、stderr空で完了した後、stdoutが空の場合です。[condition_meaning_gate.py:2013-2017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:2013)
- `preprocess-nondeterministic-builtin`: preprocess成功後、dependency closure内の code-owned fileに `__DATE__`、`__TIME__`、`__TIMESTAMP__` を見つけた場合です。[condition_meaning_gate.py:1870-1911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1870)
- `dependency-closure-invalid`: dependency fileのdecode/parse失敗、dependency消失などです。[condition_meaning_gate.py:1845-1867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1845)
- `preprocess-root-dependent-builtin`: requested/control双方のpreprocess成功後、root依存builtinとroot pathの実出力混入が重なった場合です。[condition_meaning_gate.py:2242-2266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:2242)
- `preprocess-bytes-identical`: requested/default双方が成功したが、bytesが同じ場合です。[condition_meaning_gate.py:2267-2283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:2267)
- `branch-preprocess-*` と `compile-time-branch-preprocess-*` は meaning arm用の別 reason族です。前 wave は meaning=`declared-meaning-observed` なので該当しません。[run-record.md:68-78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/output/insights/2026-09-02_t2182-k2-arm-liveness/run-record.md:68)

### 最有力原因

最有力は `config.h` 未生成による owner TU preprocess の非0終了です。

- CMake configureはMasstree sourceをpopulateするだけです。[ThirdParty.cmake:49-55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cmake/ThirdParty.cmake:49)
- `config.h` とarchiveは `add_custom_command()` のbuild時に生成されます。[ThirdParty.cmake:57-78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cmake/ThirdParty.cmake:57)
- owner TU `transaction.cc` は `common.hh` を経由してMasstree wrapperを読みます。[common.hh:8-15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cc/silo/include/common.hh:8)
- Masstree wrapperは無条件で `<config.h>` をincludeします。[masstree_wrapper.hh:17-25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/include/masstree_wrapper.hh:17)
- condition gateはconfigure後に `cmake --build ... masstree_build` を行わず、直ちにpreprocessへ進みます。[condition_meaning_gate.py:1657-1672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1657) [condition_meaning_gate.py:1993-2001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:1993)

永続 cache のMasstreeには現在 `config.h` とarchiveがignored生成物として存在しましたが、hydrateはcacheからclean cloneを作り、hydrate先のignored生成物を拒否します。[fetch_third_party.py:605-679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/fetch_third_party.py:605) したがって、URL置換でfresh cloneしただけでは生成物は移りません。

確信度は0.85です。前 wave は詳細stderrを保存せずreason codeだけを記録しているため、直接証明ではありません。

安い切り分け順は次です。

1. job-private hydrate直後に `masstree/config.h` の不在を記録する。
2. condition gateが使ったowner compile entryとpreprocess argvをCMake wrapper側で保存する。
3. そのargvを一度だけ直接再生してrc/stdout/stderrを保存する。`config.h: No such file` なら確定。
4. rc=0かつstderr非空なら、次候補は `_run_process()` の「成功processのstderr拒否」です。
5. それでも違う場合だけcompiler `--version` のstdout/stderr/rcを検査する。

## Q2 編集面の外か

preprocess原因だけなら編集面の内です。job-private hydrate後にMasstreeを事前buildし、`cmake` wrapperが同じpinの `FETCHCONTENT_SOURCE_DIR_MASSTREE/MIMALLOC/GOOGLETEST` をconfigure時だけ追加すれば、condition gate自体を変える必要はありません。

しかし、依頼全体の「Pegasusでbuild到達」には編集面の外への変更が必要です。

- `p3_s4_loop.py` は `ENV_TAG="linux-baremetal"`、`CLK=1800`、`NUMA=["numactl","--interleave=all"]` を固定しています。[p3_s4_loop.py:107-113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:107)
- config、iteration、mainがこの固定contractを繰り返しbindします。[p3_s4_loop.py:1010-1021](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1010) [p3_s4_loop.py:1347-1349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1347) [p3_s4_loop.py:1965-1968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1965)
- `run_campaign()` に `env_contract=` を渡していません。[p3_s4_loop.py:1428-1433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1428)
- Pegasus computeでは、activation state内の一意なrequired contract、つまりPegasus contract以外を拒否します。[execution_guard.py:107-159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/execution_guard.py:107)
- さらに `env_contract` を渡さない経路はlegacy `buildcache.build()` へ進みます。[pipeline.py:1200-1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/pipeline.py:1200) legacy buildの既定compilerは `gcc-13/g++-13` です。[buildcache.py:621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/buildcache.py:621)

必要な変更箇所は `p3_s4_loop.py:111-113` と、contractをbind/authorize/run_campaignへ渡す `1019-1021`、`1347-1349`、`1428-1433`、`1965-1968` です。**すべて `orchestrator/campaign/**` であり、編集面の外です。**

`execution_guard.py` の受理集合を広げる変更、siteを偽装する変更、compiler alias、pin差替えは行ってはいけません。

## Q3 環境の棚卸し

### 起動口

正式な機械E2E入口はmodule CLIの `main()` です。[p3_s4_loop.py:1843-1853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1843)

fixture 1 iterationなら想定argvは次です。`--no-build` は付けません。

```bash
python3.10 -B -m orchestrator.campaign.p3_s4_loop \
  --allow-coder-derived-build \
  --value 20 \
  --reflux on \
  --isolate-worktree
```

- `--allow-coder-derived-build` はbuild時に必須です。[p3_s4_loop.py:1943-1948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1943)
- `p3_s4_loop.main` は既にregistered coder entrypointです。[materializer_admission.py:122-127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/materializer_admission.py:122)
- `--isolate-worktree` は使い捨てCCBench worktreeを作り、build cacheだけをbase側へ置きます。[p3_s4_loop.py:1976-1985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1976)
- 計算ノードではPython 3.10以上をjob内で検査します。[pegasus-runbook.md:725-729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/docs/pegasus-runbook.md:725)

### 出力 root

jobは `IZANAGI_EXPLORATION_OUTPUT_ROOT` をprocess起動前に1度だけ、repo外のjob専用絶対pathへ設定する必要があります。[pegasus-runbook.md:1550-1554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/docs/pegasus-runbook.md:1550)

resolverは次を拒否します。

- 相対path、`..`、symlink/non-directory component。[layout.py:286-350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/layout.py:286)
- 自身または祖先に `.git` があるpath。[layout.py:307-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/layout.py:307)
- 他uid所有の既存base。[layout.py:357-367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/layout.py:357)
- 同一process中の値変更。[layout.py:370-409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/layout.py:370)

前 wave の実在例は `/work/1/SFC/tanab/izanagi-exploration-t2182` です。[run-record.md:21-24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/output/insights/2026-09-02_t2182-k2-arm-liveness/run-record.md:21)

### third-party

永続cacheは `/work/1/SFC/tanab/izanagi-thirdparty-cache` です。[pegasus-runbook.md:309-320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/docs/pegasus-runbook.md:309)

`fetch_third_party.py` はpolicyとCMake pinを同期検査し、次の4操作を持ちます。[fetch_third_party.py:67-90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/fetch_third_party.py:67) [fetch_third_party.py:697-763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/fetch_third_party.py:697)

- `fetch`: network側取得
- `verify`: cache検査
- `hydrate`: job-private stagingへのoffline clone
- `verify-deps`: gflags/glog検査

pinは `policy.json:40-61` のMasstree、mimalloc、googletestです。[policy.json:40-61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/policy.json:40)

現行 `p3_s4_loop` は `capture_define_inputs(source_root)` を追加引数なしで呼ぶため、condition gateのCMake argvへ `-D` を足せない、という前 wave の記録は正しいです。[p3_s4_loop.py:135-147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:135) generic condition-gate CLIには `--configure-arg` がありますが、p3経路はそれを使いません。[condition_meaning_gate.py:3520-3543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/condition_meaning_gate.py:3520)

job側の別経路は次です。

1. `$TMPDIR/thirdparty-src` へhydrateする。既存例は [mocc_trace_pilot.sh:1417-1444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/mocc_trace_pilot.sh:1417)。
2. private Masstree sourceで `bootstrap.sh`、`./configure --disable-assertions`、`make`、`ar`、`ranlib` を実行し、`config.h` とarchiveを生成する。正準のcommand列は [ThirdParty.cmake:66-78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cmake/ThirdParty.cmake:66)。
3. real CMakeの絶対pathを先に固定し、job-private `cmake` wrapperをPATH先頭に置く。
4. wrapperはconfigure invocationだけに、3本の `FETCHCONTENT_SOURCE_DIR_*` と `FETCHCONTENT_FULLY_DISCONNECTED=ON` を追加し、`cmake --build` 等は逐語透過する。既存の3 source-dir argv例は [mocc_trace_pilot.sh:1471-1499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/mocc_trace_pilot.sh:1471)。

### gflags / glog

正式B-10 jobはpolicyの絶対pathとpinを読み、pinned-cleanを確認後、fresh `/scr` build/installを行い、`CMAKE_PREFIX_PATH` をexportします。[b10_backoff_grid.sh:470-540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/b10_backoff_grid.sh:470)

実在pathとpinは次です。[policy.json:14-17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/policy.json:14)

- `/work/SFC/tanab/github/gflags` at `e171aa2d15ed9eb17054558e0b3a6a413bb01067`
- `/work/SFC/tanab/github/glog` at `8f9ccfe770add9e4c64e9b25c102658e3c763b73`

### compiler

`compilers_for_current_site()` は実siteが `PEGASUS_COMPUTE` の場合だけ `gcc/g++`、それ以外は `gcc-13/g++-13` を返します。[buildcache.py:1820-1842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/buildcache.py:1820)

site判定は `bnodeNNN` をcompute、`pegasus0N`とNQSV evidenceをloginとします。[site_policy.py:30-46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/site_policy.py:30)

Pegasus実測は次です。

- PATH上: `/bin/gcc`、`/bin/g++`
- realpath: `/usr/bin/x86_64-linux-gnu-gcc-11`、`/usr/bin/x86_64-linux-gnu-g++-11`
- version: Ubuntu GCC/G++ 11.4.0

根拠は [toolchain_versions.stdout:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/output/env/pegasus/smoke/0:867860.nqsv/toolchain_versions.stdout:1) と [toolchain_realpaths.stdout:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/output/env/pegasus/smoke/0:867860.nqsv/toolchain_realpaths.stdout:1) です。

### Pegasus contract使用時の追加環境

Pegasus contractは `single_process=True` なので、将来p3がPegasus contractへ正しく移植された場合、8個の `IZANAGI_RESERVATION_*`、`PBS_JOBID`、boot ID照合、および `<output>/env/pegasus/claims` の事前作成が必要です。[reservation.py:120-129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/reservation.py:120) [loop.py:198-229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/loop.py:198)

### submodule pin

- loopの歴史pinは `028f34d`。[p3_s4_loop.py:107-109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:107)
- 現行pinは `511c953`、直前pinとして `028f34d` が保存されています。[pin.py:26-33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/pin.py:26)
- mainは起動前に固定submoduleが `PIN` でpinned-cleanであることを要求します。[p3_s4_loop.py:1950-1956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1950)

pinは変えません。一時変異と復元は親が `DW-O19` の手順で行う操作です。

## Q4 登録義務

新しい `.sh`、`.py`、`.pbs` は1本ごとに次を満たす必要があります。

1. `tools/pegasus/admission_registry.json` にcanonical sorted entryを追加する。job bodyは `dispatch-required` とする。[admission_registry.json:1-15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/admission_registry.json:1)
2. loaderが要求するfield順は `class`, `reason`, `primary_gate`, `evidence` のexact 4 fieldです。classは3値、値は非空、JSON bytesもcanonicalでなければなりません。[pegasus_admission_registry.py:18-21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus_admission_registry.py:18) [pegasus_admission_registry.py:80-136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus_admission_registry.py:80)
3. consumerは `hooks/guard_bash.py` です。loader sourceを直接compile/execし、registryからsanctioned pathを導出します。[guard_bash.py:237-258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/hooks/guard_bash.py:237)
4. `orchestrator/tests/test_hooks.py` の `_PEGASUS_EXPECTED_CLASSES` と `_PEGASUS_EXPECTED_ENTRIES` へ同じentryを追加する。[test_hooks.py:2572-2641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_hooks.py:2572)
5. 同fileの `test_bash_pegasus_registry_schema_and_fixed_classes` がentry×4 fieldをliteral exact比較します。[test_hooks.py:3445-3456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_hooks.py:3445)
6. `test_bash_pegasus_execution_inventory_is_synchronized` は `tools/pegasus/` を再帰walkし、`.py/.sh/.pbs`、実行bit、shebangのいずれかを持つ全fileとregistry keyの集合完全一致を要求します。[test_hooks.py:3879-3905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_hooks.py:3879)
7. runbookの `(path,class,evidence)` 投影表を更新する必要があります。`tools/check_docs.py` が集合完全一致を検査します。[pegasus-runbook.md:484-487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/docs/pegasus-runbook.md:484) [check_docs.py:4805-4824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/check_docs.py:4805)
8. `tools/pegasus/README.md` で新scriptを手順として言及するなら、冒頭の実行site宣言表にも載せます。[README.md:20-26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/tools/pegasus/README.md:20)
9. 新規専用test fileには自走harnessを持たせるかpytest-only allowlistへ登録します。[test_plain_runner_coverage.py:35-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_plain_runner_coverage.py:35)

`test_reviewed_process_launch_inventory_is_recursive_and_exact` は、`orchestrator/calibrator/**/*.py` と `orchestrator/campaign/**/*.py` のprocess API呼出しを関数scopeと件数を含むCounterとしてexact比較します。[test_ccbench_spawn_sites.py:28-31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_ccbench_spawn_sites.py:28) [test_ccbench_spawn_sites.py:332-344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_ccbench_spawn_sites.py:332) [test_ccbench_spawn_sites.py:2555-2562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_ccbench_spawn_sites.py:2555)

したがって `tools/pegasus/*.sh` や同配下のPythonだけなら、このprocess inventory自体には入りません。shell materializerが別registryの対象外であることも明記されています。[materializer_admission.py:17-19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/materializer_admission.py:17)

先例は次です。

- A-5: `tools/pegasus/a5_second_boot_backoff_sweep.sh` と `submit_*` に対し、`orchestrator/tests/test_a5_second_boot_job_contract.py` を同時追加し、registry exact testも持ちます。[test_a5_second_boot_job_contract.py:352-370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_a5_second_boot_job_contract.py:352)
- Mocc trace: `mocc_trace_pilot.sh`、submitter、policyと同時に `orchestrator/tests/test_mocc_trace_job_contract.py` を追加しています。[test_mocc_trace_job_contract.py:23-30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/tests/test_mocc_trace_job_contract.py:23)

新script、registry、runbook投影、testは凍結成果物ではありません。外部exploration rootへ出力し、`output/s1-freeze`、`output/s8b-freeze` を一切編集しなければ凍結bytesは変わりません。凍結treeへ書く必要が生じたら停止です。

## Q5 実行場所の択一

### Pegasus entry

`pegasus` g1/g2はregistryに実在します。いずれも `clocks_per_us=2100`、`numactl=()`、required attestation、single processです。[env_contract.py:248-311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/env_contract.py:248)

ただしcurrent activationはg1です。g2は登録済みですが未activeです。[00000001.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/env_contract_activations/00000001.json:1)

authority snapshotはactive rowごとにcalibration path、SHA、qualityを検証します。[env_contract.py:601-631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/env_contract.py:601) [env_contract.py:634-687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/env_contract.py:634)

### 実際に落ちるgate

`p3_s4_loop` がPegasus compute上で `env_contract.authorize("linux-baremetal")` を発行し、`run_campaign()` に渡すと、`require_certified_writer_authorization()` のcompute専用検査がそれを拒否します。[p3_s4_loop.py:1428-1433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/p3_s4_loop.py:1428) [execution_guard.py:137-159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/execution_guard.py:137)

順序は次です。

1. condition gate
2. `run_campaign`
3. `_authorize_measurement`
4. `require_certified_writer_authorization`
5. ここで拒否
6. build未到達

[loop.py:161-182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/loop.py:161)

旧 `assert_machine_pin()` はp3経路では呼ばれず、floor/oracle専用です。[execution_guard.py:191-200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/execution_guard.py:191) p3で実効なのは上記authorization gateです。

これはjob script側では解けません。site偽装、authorization差替え、gate緩和はいずれも不正です。`p3_s4_loop.py` のsite-aware contract化が必要で、編集面の外です。

### 費用比較と推奨

Pegasus側の実測費用は、6投入、gflags/glog build、3 third-party offline配置を経て、なおbuild未到達です。[run-record.md:71-93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/output/insights/2026-09-02_t2182-k2-arm-liveness/run-record.md:71) さらに現行codeにはpreprocess後のhard authorization gateがあります。

一方、同じ段4 loopは `linux-baremetal` でiteration 1-4がすべてcertified/successまで実走済みです。[phase3-kickoff-stages1-5.md:115-118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/docs/archive/phase3-kickoff-stages1-5.md:115)

よって技術的に安い推奨は **`linux-baremetal`、つまりcygnus** です。Pegasus既定を覆す根拠は、同一loopのcygnus成功4 iteration対Pegasus失敗6投入という実測差と、Pegasus側hard gateの静的証明です。

ただしユーザー方針は「cygnusは使えるが使わず、新規evidenceはPegasus」です。[worklog.md:543-553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/docs/worklog.md:543) この方針を維持する場合は、現在のwaveを停止し、p3所有waveでPegasus contract移植を行う必要があります。

## Q6 規律 1

規律1は現行build経路で満たされています。

- CCBenchの既定performance buildは `CCBENCH_TRACE=0` です。[Options.cmake:13-19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cmake/Options.cmake:13)
- `TRACE=${CCBENCH_TRACE}` がtarget compile definitionへ入ります。[Options.cmake:58-68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cmake/Options.cmake:58)
- trace headerのinclude、buffer、I/O、stateは全体が `#if TRACE` 内です。[trace.hh:25-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/include/trace.hh:25)
- Siloのtrace呼出しも `#if TRACE` 内にあります。[transaction.cc:147-180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cc/silo/transaction.cc:147) [transaction.cc:538-578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/external/ccbench/cc/silo/transaction.cc:538)
- pipelineは `trace=True` と `trace=False` を別buildとして作ります。[pipeline.py:1197-1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/pipeline.py:1197)
- throughputへ渡すのは常に `pf.binary`、trace verifierへ渡すのは `tr.binary` です。[pipeline.py:1378-1382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/pipeline.py:1378) [pipeline.py:1553-1565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/pipeline.py:1553)
- perf binaryはcache hit/fresh buildの双方で `nm -C` により `izanagi_trace` symbol不在を検査します。[buildcache.py:3176-3186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/buildcache.py:3176) [buildcache.py:3432-3464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/buildcache.py:3432)

perf runにも `IZANAGI_TRACE_DIR` は設定されますが、これはverify/perfを環境変数の有無で識別させないためです。perf buildではtrace code自体がコンパイル除去されており、ランタイム `if(tracing)` ではありません。[pipeline.py:717-743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2199-s4-loop-pegasus-build/orchestrator/campaign/pipeline.py:717)

job scriptが独自に `ycsb_*.exe` を起動するとtrace binaryを誤測定する余地が生じます。scriptはp3 CLIだけを起動し、build tree内binaryを直接実行しない形に限定すべきです。

## 実装 plan

1. **現在のscopeでは実装を開始しない。** `p3_s4_loop.py:111-113,1019-1021,1347-1349,1428-1433,1965-1968` のPegasus contract配線がlandするまで停止する。これらは編集面の外である。
2. p3所有waveが、siteから一度だけcontractを解決し、その同じ値をconfig identity、`ENV_TAG/CLK/NUMA` 相当、authorization、`run_campaign(env_contract=...)` へ通したことを確認する。`execution_guard.py:137-159` は変更しない。
3. その前提がlandした後にのみ、新規 `tools/pegasus/p3_s4_loop_build.sh` を作る。別 `.pbs` は作らず、この `.sh` 自体に `#PBS -A SFC`、`-q gen_S`、`-b 1`、walltime、SIGTERM受理を置く。
4. script冒頭でPBS envelope、`bnodeNNN`、Python 3.10以上、repo HEAD、job script SHA、submodule `028f34d` pinned-clean、compiler/CMakeのrealpathとversionを検査し、receiptへ保存する。pinの一時変異は親のDW-O19に委ねる。
5. `/scr/${PBS_JOBID//:/_}-p3-s4-loop` をjob-private `TMPDIR` としてcreate-only作成し、trapで後片付けする。durable receipt rootと `IZANAGI_EXPLORATION_OUTPUT_ROOT` はgit common dirからrepo外へ導出し、既存attemptを再利用しない。
6. `policy.json:14-17` のgflags/glogをpinned-clean検査し、`b10_backoff_grid.sh:517-540` と同じfresh build/installを行う。実compilerはcomputeで選ばれる `gcc/g++` のままにする。
7. `fetch_third_party.py hydrate --staging-root "$TMPDIR/thirdparty-src"` を実行し、JSONの `.source_root` と3 pinを検査する。
8. hydrate直後のMasstreeに `config.h` が無いことを診断記録し、`ThirdParty.cmake:66-78` と同じcommand列でprivate sourceを事前buildする。生成後の `config.h` とarchiveのSHAをreceiptへ記録する。
9. real CMakeを固定後、`$TMPDIR/bin/cmake` wrapperを生成する。configure時だけ3本のexact source-dir、fully-disconnected、compiler launcher空を追加し、その他のsubcommandはreal CMakeへ逐語透過する。wrapper、real CMake、注入argvを保存する。
10. Pegasus contract用の8個のreservation環境変数をqstat、hostname、boot ID、script SHA、nonceから構築し、`<external-output>/env/pegasus/claims` を事前作成する。
11. `IZANAGI_EXPLORATION_OUTPUT_ROOT`、`CMAKE_PREFIX_PATH`、wrapper PATHを一度だけ設定し、前掲のp3 fixture CLIを1回起動する。stdout、stderr、rcをdurable attemptへ保存する。
12. `preprocess-failed` の場合は再投入せず、保存したcompile entry/preprocess argvを1回だけ再生して直接stderrを確定する。gate reasonやtimeoutを変更しない。
13. 完了時にsubmodule HEAD/status、superproject tracked status、凍結tree digestの前後一致、campaign WAL/checkpoint/condition recordの実在を確認する。terminal verdict未到達を成功扱いにしない。
14. `tools/pegasus/admission_registry.json` にjob bodyを `dispatch-required` で追加し、`test_hooks.py:2572` と `:2641` のliteral golden、runbook `:489` の投影表、`tools/pegasus/README.md:28` のsite表を同期する。
15. `orchestrator/tests/test_p3_s4_loop_pegasus_job_contract.py` を追加し、PBS/site gate、pin不変、compiler不変、private hydrate、Masstree prebuild、exact source-dir注入、外部output、p3 argv、trace/perf非直起動、registry exact entryを静的検査する。末尾に自走harnessを置く。
16. 親が焦点走として、新規test file、`test_plain_runner_coverage.py`、`test_hooks.py`、`test_ccbench_spawn_sites.py`、`tools/check_docs.py` を実走する。私はいずれも実走していない。

## 未確認・リスク

- 前 waveの実preprocessor stderrは成果物に残っていません。`config.h` 不在はcodeとcache状態からの推定で、確信度0.85です。
- job-private hydrate後のMasstree prebuildとcondition gate replayは実走していません。
- CMake wrapperによる追加argvがPegasus実機のCMake 3.25.0で両configureへ入ることは未実測です。
- gflags/glog、Masstree事前build、condition gate、trace/perf buildを含む必要walltimeは算出していません。
- current activationはPegasus g1です。g2登録済みをcurrentと誤読してはいけません。
- cygnusの現在の到達性、混雑、compiler状態は今回再確認していません。推奨根拠は既存の同loop 4 iteration実測です。
- pytest、shell syntax、check_docs、実buildは制約どおり未実走です。