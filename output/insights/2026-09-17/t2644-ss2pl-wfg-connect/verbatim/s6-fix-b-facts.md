# 親の実測 — probe 1 走目の blocker (2026-09-17 01:24〜01:40 JST)

## 計算ノード 1 走目 (request 0:2301.nqsv、bnode015、所要 13 秒)

`probe-result-1.json`: `status=error`, `stage=build_S`, `error.type=ContractError`,
`error.message` =
```
condition gate rejected SS2PL study: SS2PL_LOCK_IMPL=red/owner-tu-unresolved, SS2PL_LOCK_KIND=red/configure-failed,
SS2PL_DLR=red/owner-tu-unresolved, SS2PL_WFG_DIAG=red/owner-tu-unresolved,
SS2PL_LOCK_IMPL=unestablished/meaning-witness-undeclared, SS2PL_LOCK_KIND=unestablished/meaning-witness-undeclared,
SS2PL_DLR=unestablished/meaning-witness-undeclared, SS2PL_WFG_DIAG=unestablished/meaning-witness-undeclared
```
前段はすべて緑: required_commands (cmake=/usr/bin/cmake, c++=/usr/bin/c++, git, make, as, ld, ar, ranlib, nm, strings)、
thirdparty (3 pin 一致・clean)、canonical (511c9538、clean)、clone_stock 0.45 s、clone_patched 0.43 s、apply_patch 0.03 s、
abort_ownership 0.006 s。`pbs_jobid` は `compute-visible` 経由で `0:2301.nqsv` (env には無かった)。scratch は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/scratch-1/t2644-b96716762cb24b5a919f07217f062b88/` に残っている
(`ccbench` = patched clone、`condition-gate-stock` = stock clone、`builds/` は空)。

## login で gate CLI を当てた結果 (同じ scratch clone、同じ configure 引数)

### arm S、macro SS2PL_LOCK_KIND (requested 1 = default 1、--stock-comparison)

supply-effectuation = red / `configure-failed`:
```
successful process wrote stderr=b'CMake Warning:\n  Manually-specified variables were not used by the project:\n\n    CCBENCH_SS2PL_LOCK_IMPL\n\n\n';
argv=/usr/bin/cmake -S <scratch>/condition-gate-stock -B /tmp/izanagi_condition_supply_*/stock -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
-DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-11 -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF '-DCMAKE_PREFIX_PATH=...
```
→ gate は inert な要求 (requested == default) で **stock 木**を対照に configure し、companion define `CCBENCH_SS2PL_LOCK_IMPL`
(DefineSpec の依存) を stock に渡す。stock の ss2pl は同 option を持たず CMake が未使用警告を stderr へ出し、gate は
「stderr が非空 = configure-failed」と判定する。他 3 軸の `owner-tu-unresolved` は、stock の ss2pl に `ycsb_ss2pl.exe`
target が無い (patch が足す) ため owner TU (ycsb_ss2pl の TU) が stock の compile_commands に存在しないことによる。
**いずれも stock 対照に固有で、本 wave の変更とは無関係。T-2018 (2026-08-27、原 study の後) で gate が入って以来、
runner の `build_target` は一度も実走していない。**

### arm phase1、macro SS2PL_WFG_DIAG (requested 1、default 0、stock 対照なし)

supply-effectuation = red / `preprocess-failed`:
```
process returned rc=1; stderr=b'.../ccbench/cc/ss2pl/transaction.cc:10:
.../ccbench/cc/ss2pl/include/../../../include/masstree_wrapper.hh:20:10: fatal error: config.h: そのようなファイルやディレクトリはありません
   20 | #include <config.h>
compilation terminated.'
argv=/usr/bin/x86_64-linux-gnu-g++-11 -DADD_ANALYSIS=0 -DBACK_OFF=1 ... -DSS2PL_DLR=1 -DSS2PL_LOCK_IMPL=0 -DSS2PL_LOCK_KIND=1
-DSS2PL_WFG_DIAG=1 -DSS2PL_WORKLOAD_YCSB=1 -DTRACE=0 -DVAL_SIZE=8 -I<scratch>/ccbench/... (前処理 -E)
```
runtime-meaning = unestablished / `meaning-witness-undeclared` (raw-measurement では admitted を妨げない:
`require_condition_gate_family` は `supply_green and meaning_not_red`、unestablished は not red)。

→ **phase1 で唯一の赤は masstree の `config.h` 不在。** `external/ccbench/cmake/ThirdParty.cmake:57-78` の
`masstree_build` custom target が `./bootstrap.sh && ./configure && make && ar` を **masstree の source dir の中で**走らせ、
`config.h` と `libkohler_masstree_json.a` を source dir に生成する。hydrate 済みの pristine staging
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/thirdparty-src/masstree`) には `config.h` が無い
(`ls` で確認: bootstrap.sh / configure.ac はあるが config.h は無い)。永続 cache
`/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree/config.h` は実在する (過去の build 生成物、だから T-2213 の gate 実測は通った)。

## 是正の方向 (親の裁定)

- phase1 の gate を通すには、gate より前に `masstree_build` target を 1 回 build して `config.h` を生成する (warm-up)。
  `build_target` 自身は変えない。
- arm S の不在性は gate を通せない (stock 対照の既存不整合) ので、gate を省いた production 部品の組合せ (`_configure` →
  `cmake --build` → `_find_binary` / `_target_compile_entries` / `_validate_compile_definitions` → `_wfg_absence_evidence`)
  で取る。gate を省いたことは結果 JSON に明記する。
- 既存不整合 2 件 (stock 対照の owner TU 不在、pristine staging での config.h 不在) は親が別起票する。
