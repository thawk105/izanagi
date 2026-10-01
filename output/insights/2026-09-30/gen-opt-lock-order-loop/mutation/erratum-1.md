# 変異の erratum 1 — probe2 の読みと登録の直し (2026-10-01 03:15 JST)

対象 commit `8631dee79ccaff96f84fcbb8854eea712b11dbb7` の独立 clone (D1009)、runner は新 test 4 file、dispatch probe (全件 SURVIVED 期待で赤 node を観測)。

## 初回の投入の失敗 (probe、40144.nqsv)
親が完全 SHA を手打ちで誤転記し、harness が「commit 解決に失敗 (git rc=128)」で 5 秒で止まった (計算の損失なし)。`git rev-parse` の値を渡して probe2 として投げ直した。

## probe2 (40151.nqsv、Elapse 328 s) の観測
基準走は緑 (38 passed)。M0 (等価) は SURVIVED。負の 15 本はすべて赤 node あり (`probe2-observed-nodes.json`)。

## 読みの直し
1. **drift による赤。** `test_pipeline_gate_witness.py::test_m2_explicit_requirement_passes_run_campaign` は `loop.run_campaign` を通り、
   起動時の contract-loader の照合 (閉包 file の disk bytes = HEAD blob) で `contract-loader-drift` になる。閉包には loop.py・pipeline.py・
   buildcache.py・判定器などが入るので、これらの file への変異では、内容と無関係に test_m2 が赤になる (M1・M2・M3・M4・M5・M13・M14 の観測に test_m2 が入った。
   M13 の本文で `contract-loader-drift: ... buildcache.py` を確かめた)。
   - 本走の期待 node は DW-M08 のとおり観測した完全集合で登録する (drift の node を含む)。**owner の証拠には drift を受けない test だけを数える。**
   - M1 = `test_m1_flag_forces_required_evaluate` (pipeline.evaluate を直接呼ぶ)、M3 = `test_m3_required_capability_rejects_absent_gate_file`、
     M4 = `test_m4_required_d5_uses_snapshot_not_disk`、M5 = `test_m5_unrequested_snapshot_legacy_bytes`、M14 = `test_required_repetition_reaches_capability` が owner。
   - **M2 (loop.py の evaluate への keyword の運搬) は owner の証拠が無い。** 観測は drift の test_m2 だけで、loop.py は閉包の中なので、注入方式では
     その運搬だけを赤にする test を置けない (先例: T-2253 の loop.py 変異も同じ)。flag 由来の強制 (M1) は pipeline 側で独立に効くので、
     gen-opt の genome (`SILO_ORDER_VARIANT≠0`) では loop の運搬が落ちても要求は外れない。M2 は「drift 込みの KILLED、owner なし」と記録する。
2. **M13 は狙いが外れていた。** 置換位置 (`buildcache.py` の `common["require_gate_witness"]`) は `build_v2` の中で、`test_m13_build_exit_rechecks_required_snapshot_for_fresh_and_hit`
   が通る `buildcache.build` の経路では使われない。観測は drift の test_m2 だけだった。build 出口の再照合 (`_recheck_source_evidence` の `resolve_evidence` 呼出し)
   へ狙い直した M13b を登録し、M13b だけの probe3 で観測してから本走に入れる。元の M13 は本走から外す。
   `build_v2` の経路で要求を落としても、出口の再照合が証拠束つき snapshot と食い違って fail-closed で止まる (受理は広がらない) が、その経路を要求つきで通す test は無い (限界)。
