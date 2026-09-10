## fix

- F-1 — [issuer.py:293](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:293): `math.copysign()` で対象 7 面の `-0.0` を拒否し、再導出比較にも符号一致を追加。既存 test 内に全 7 面の負例を追加。
- F-2 — [issuer.py:708](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:708): `floor_pair_driver.load_frozen_spec()` の型付き結果から identity を導出。.get() 読みを廃止し、producer 拒否 spec の負例を追加。
- F-3 — [issuer.py:1004](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1004): `expected_sha256` の既定値を削除し、必須引数化。署名と省略時 `TypeError` を検査。
- F-4 — [issuer.py:52](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:52)、[material_report.py:982](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/campaign/p3_b4_material_report.py:982): source summary 参照先の未照合を逐語追加し、upstream `proof_limitations.items` を順序どおり転記。汎用的な `authoritative_floor_artifact` checked 主張を削除。
- F-5 — [material_report.py:985](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/campaign/p3_b4_material_report.py:985): present 時の `expected_analysis_verdict` / `reason` を `null` 化。schema v1 と generator identity は不変。
- F-6 — [test_p3_b4_floor_artifact_issuer.py:252](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:252): expected ratio / hex を元 summary fixture 値から独立計算。
- F-7 — [issuer.py:959](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix1/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:959): 到達不能な `assert summary.identity is not None` を削除。

## 実走した検査

- `test_p3_b4_floor_artifact_issuer.py` 全範囲: `rc=16`、dispatch preflight 失敗、child 未起動。未実走。
- `test_p3_b4_material_report.py` 全範囲: `rc=16`、同上。未実走。
- `test_official_perf_surface_inventory_is_exact` / `test_outer_perf_file_and_added_guard_inventory_is_exact`: `rc=16`、同上。未実走。
- AST parse、import/契約 probe、`git diff --check`: `rc=0`。
- `tools/check_codex_agents.py`: `rc=0`。`tools/check_docs.py`: `rc=0`。
- 新しい test 関数 node は追加していないため、serialization golden は未変更。

## 受理集合

修正前は、対象 7 面の `-0.0`、producer の閉 schema が拒否する自己整合 spec、digest 省略 loader 呼出しを受理できました。

修正後はこれらを拒否します。`+0.0`、既存の有限値・canonical JSON、正しい digest の権威成果物は引き続き受理します。authority の非保証欄は、固定 prefix に summary の proof items を連結する形へ必要範囲だけ拡張しました。

D1696 の 9 項目や source summary 参照先の実在照合は追加していません。

## 波及可能性

- 所有外 production caller: `p3_b4_material_report.py` → preregistration resolver → 必須 digest loader。
- 所有外依存: `floor_pair_driver.load_frozen_spec()`、`FloorPairSpec`、既存 receipt/calibration binding。
- 共有 fixture: `test_floor_pair_driver.py` の `_write_inputs`、`_valid_document`、`_install_git`、`_verified_calibration`、`_run_production`。
- consumer test: `test_p3_b4_material_report.py`、`test_official_perf_closure.py` の指定 2 node、`test_real_repo_serialization.py` の material-report node golden。
- production receipt の `protocol` 欠落による発行拒否は既知どおり不変です。

## 総括

F-1〜F-7の実装と対応 test 更新は完了しました。  
tracked 変更は許可された 4 file のみで、commit は作成していません。  
静的検査と repository checker は通過しています。  
pytest は全試行が infrastructure `rc=16` で child 未起動でした。  
したがって現状は「実装済み・未実走」であり、closed とは申告しません。