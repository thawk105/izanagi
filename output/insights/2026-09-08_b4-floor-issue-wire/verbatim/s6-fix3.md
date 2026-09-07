## 適合

- T-1: [p3_b4_floor_artifact_issuer.py:38](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:38)  
  summary pin を単一文字列 `floor-pair-summary/v3` へ更新。v3 の `statistics` top-level field と dropped record の `side_id` にも適合した。v2 負例は [test_p3_b4_floor_artifact_issuer.py:409](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:409)。

- T-2: [p3_b4_floor_artifact_issuer.py:531](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:531)  
  `session_medians` を side 別 `{candidate, reference}` に変更し、producer と同じ順序で `candidate_1/reference_1-1.0`、`candidate_2/reference_2-1.0`、`abs(gain_1-gain_2)` を再導出。符号込み一致、`-0.0`・bool 拒否、層別/final upper、`candidate_floor == upper` は維持した。

- T-3: [p3_b4_floor_artifact_issuer.py:847](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:847)、[test_p3_b4_floor_artifact_issuer.py:52](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:52)  
  producer の `load_frozen_spec()` を使う閉 schema 検証を維持し、fixture を v3 spec/summary と4測定値へ適合。実 `finalize_floor()` 正例では side ごとに異なる reference を使うよう更新した。

- T-4: [test_real_repo_serialization.py:294](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/tests/test_real_repo_serialization.py:294)  
  不足していた `test_present_floor_projects_required_verbatim_non_guarantees` だけを material-report golden に追加した。

## fixture の適合と期待値変更の区別

v3 適合は、side 別 median、4引数の producer API、summary の `statistics`、shared `_pair_measurement_values()` 形式への変更。

期待値変更は以下だけ。

- schema pin の期待値を v2 から v3へ変更し、schema 負例を v3からv2へ変更。T-1で必須の受理版切替で、緩和ではない。
- serialization golden に実在 node を1件追加。T-4で指定された canonical collection の更新。

既存の拒否条件、数値期待、skip、例外期待は緩和していない。

## D1699 適合の非保証をどうしたか

逐語3件はすべて残した。`D1699_VERSION_LIMITATION` も削除していない。

producer v3 の現物は [floor_pair_driver.py:71](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/campaign/floor_pair_driver.py:71) と [floor_pair_driver.py:1464](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix3/orchestrator/campaign/floor_pair_driver.py:1464) で、各 side 固有の reference を分母にする4引数式を実装している。この点では依頼に記載された D1699 の D 意味を満たしたと判断できるが、非保証の削除判断は親へ残した。

v3 spec にも `protocol` は存在せず、通常の build receipt からも導出できないため、発行拒否の現状は変わらない。

## 実走した検査

以下はすべて runner 自体が `rc=16`（`qstat -Q` preflight failure）となり、子 pytest は開始されていない。したがって全 node を「未実走」とする。

- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` 全体
- `test_p3_b4_material_report.py::test_present_floor_projects_required_verbatim_non_guarantees`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact`
- `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact`
- 最終変更後の実 producer 正例 nodeも再試行したが `rc=16`、未実走。

静的検査は AST parse `rc=0`、`git diff --check` `rc=0`。テスト緑または `closed` は申告しない。

## 受理集合

- 変更前: `floor-pair-summary/v2` のみ受理。v3を拒否。
- 変更後: `floor-pair-summary/v3` のみ受理。v2および未知版を fail-closed で拒否。

## 波及可能性

- v2 summary を渡す所有外 caller/CLI は今後拒否される。
- `p3_b4_material_report.py` は authority artifact を消費するため、authority schema・public signatureを変えておらず直接影響なし。
- shared `test_floor_pair_driver.py` は未変更。その v3 fixture/APIへ issuer testを追従させた。
- `test_p3_b4_material_report.py` は未変更。追加済み test nodeだけ serialization goldenへ登録した。
- 射影外 caller の全 inventory は、指定された読み取り境界に従って走査していない。

## 総括

v2受理を廃止し、producer v3 の side固有 reference による D 再導出へ適合した。  
実 producer `finalize_floor()` を使う正例も v3入力へ更新した。  
非保証3件と material-report schema/identityは維持した。  
変更は許可された3ファイルのみで、commitは作成していない。  
pytestはdispatch障害で未実走のため、実装済み・未検証であり `closed` ではない。