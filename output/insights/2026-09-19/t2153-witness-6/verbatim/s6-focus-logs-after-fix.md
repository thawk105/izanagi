# fix 1 統合後の親の焦点走 (統合 commit 7cc76d98b)
- 焦点走 1 再走 (gate / rung1 driver / S1、22:42、Elapse 13 s、pytest 6.68 s): **374 passed** (赤ゼロ。fix 前の 2 failed は消え、新規 rung1 実 helper test を含む)。
- 閉包焦点走 (test_p3_b4_wiring_probe / test_ccbench_spawn_sites / test_silo_ladder_rung1 / test_silo_ladder_rung1_evidence / test_s8b_expected_materialization / test_s8b_oracle_n_pilot / test_build_site_gate / test_mocc_proof_surface / test_mocc_mutation_proof、22:47、pytest 80.49 s): **350 passed, 2 skipped**。
- 全史 provenance 監査 (統合 commit 後): 11,631 件、新規違反なし。
- official 同形 cell (最終 production 登録簿、certified-selection、env CMAKE_PREFIX_PATH + FETCHCONTENT_BASE_DIR + SOURCE_DIR ×3): login (pegasus02) と計算ノード (bnode055、10879.nqsv、Elapse 12 s) で SORT / REPORT とも supply green / meaning green (1,1)/(0,1) / admitted / unestablished []。前処理 digest・bytes・owner sha・compiler は login と計算ノードで完全一致 (SORT ff30961ccf8d/527b6edff128、4,471,878/4,471,661; REPORT a14dc4657a72/2775e7dc9e93、4,479,871/4,479,486)。
- 変異 matrix (m0〜m7、独立 clone、dispatch mode) は 22:52 に本走開始、結果は親が別途確定する。
