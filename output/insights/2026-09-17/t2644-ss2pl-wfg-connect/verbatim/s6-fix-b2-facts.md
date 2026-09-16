# 親の実測 — probe 2 走目の結果 (request 0:2325.nqsv、bnode040、2026-09-17 01:39、所要 42 秒)

`probe-result-2.json`: `status=error`, `stage=build_phase1`。段階所要: warm_masstree 13.7 s (config.h・archive とも生成、`config_h_exists_after=true`)、
absence_S (plain) 12.2 s、build_phase1 8.6 s (gate で停止)。

## 1. absence_S (plain) の `_wfg_absence_evidence` は path 文字列の偽陽性で赤

`symbol_hits=[]`、preprocessed の `identifiers=[]`、`binary_label_count=1`、`population_ok=True` — 計器の識別子・symbol は性能 build に無い。
赤の原因はすべて `generic-wfg-identifier` が **path 文字列** に当たったもの:
`source_hits` の 3 TU、`string_hits` の 8 行、`preprocessed_hits` の `literals` はいずれも
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/scratch-2/.../ccbench/cc/ss2pl/...` と
`.../dev-wave-t2644-ss2pl-wfg-connect/thirdparty-src/masstree` という **job dir 名に含まれる `wfg`**。
`_wfg_text_hits` (runner:238-246) は `(?i)(?:wfg|wait[_ -]?for[_ -]?graph)` の部分文字列検査で、前処理出力の行マーカ
(`# 1 "/path/..."`) と binary 内の `__FILE__` 文字列を path ごと拾う。

→ 是正: scratch と thirdparty root を `wfg` を含まない path に置く。親が hydrate 済み:
`--thirdparty-root /work/1/SFC/tanab/dev-wave-jobs/t2644-deps/thirdparty-src` (pristine、config.h 無し)、
`--scratch-root /work/1/SFC/tanab/dev-wave-jobs/t2644-deps/scratch-3`。probe 側の変更は不要 (引数で解決)。

## 2. build_phase1 の condition gate は patch の設計と構造的に合わない

```
condition gate rejected SS2PL study: SS2PL_LOCK_IMPL=red/dependency-closure-drift, SS2PL_LOCK_KIND=green/requested-default-preprocess-different,
SS2PL_DLR=red/compile-command-drift, SS2PL_WFG_DIAG=red/dependency-closure-drift, (meaning 4 軸 = unestablished/meaning-witness-undeclared)
```
`orchestrator/campaign/condition_meaning_gate.py:2647-2651` は要求値と既定値の前処理の **依存閉包 (header 集合) が同一** であることを、
`:2619-2624` は **comparable argv が同一** であることを要求する。この patch は `SS2PL_LOCK_IMPL=1` で `ss2pl_study_lock.hh` を、
`SS2PL_WFG_DIAG=1` で `ss2pl_wfg.hh` を include し (閉包が変わる)、`SS2PL_DLR` は CMake が `DLR0/DLR1/DLR2` marker define を切り替える
(argv が変わる)。KIND だけは header を変えないので green。**warm-up は効いた** (前処理は通り、drift 判定まで進んだ)。
これは T-2018 (2026-08-27) の gate 導入以来 SS2PL runner の `build_target` が実走していなかった既存不整合であり、本 wave では直さない (親が別起票)。

→ 是正: phase1 も absence_S (plain) と同じ「gate を通さない production 部品の build」で record を組み、`_run_phase_trial` へ渡す。
`_admit_output` が要求する `build` の key は `requested_cache` / `observed_cache` / `compile_definitions` / `binary_sha256` / `binary`
(runner:2519-2530) で、plain record はこれを満たす。gate を省いたことと 2 走目の拒否文を record に残す。

## 段階所要の実測 (bnode040)

clone 0.5+0.4 s、warm-up 13.7 s、S build (configure + `cmake --build --target ycsb_ss2pl.exe -j48`) 12.2 s。phase1 build も同程度と見込む。
60 秒の走行を足しても walltime 00:30:00 で足りる。
