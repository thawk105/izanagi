## 実装

- [p3_b4_material_report.py:211](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/campaign/p3_b4_material_report.py:211)
  - 固定 preregistration §5 を実 resolver で先に解決。
  - resolver 例外は `authoritative_floor_rejected` として fail-closed。
  - evaluator call は同じ `_load_and_evaluate()` 内の 1 回だけを維持し、present 時は `Fraction`、sentinel 時は `None` を渡す。
- [p3_b4_material_report.py:844](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/campaign/p3_b4_material_report.py:844) の既存 absent composer は維持し、[present 射影:963](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/campaign/p3_b4_material_report.py:963) だけを後段で適用。
- [射影 assertion:1040](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/campaign/p3_b4_material_report.py:1040) と [present Markdown:1201](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/campaign/p3_b4_material_report.py:1201) を追加。
- `SCHEMA_VERSION`、`GENERATOR_IDENTITY`、public 関数・CLI の引数は変更なし。

|権威|assembly|availability|analysis.status|floor_argument|
|---|---|---|---|---|
|なし|成功|`absent`|`evaluated`|`null`|
|なし|拒否|`absent`|`not_evaluated`|`null`|
|あり|成功|`present`|`evaluated`|`[num, den]`|
|あり|拒否|`present`|`not_evaluated`|`null`|

4 状態は [test:847](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/tests/test_p3_b4_material_report.py:847)、fail-closed は [test:955](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/tests/test_p3_b4_material_report.py:955) で固定しました。実 resolver を使用しており、stub していません。

## 実走した検査

pytest はすべて runner が child を起動する前に停止したため未実走です。

- 新設 3 node 指定: `rc=16`, `child_started=false`
  - `test_m8_absent_authority_public_bytes_match_pre_change_golden`
  - `test_m9_four_authority_and_assembly_states_project_exactly`
  - `test_m7_non_sentinel_resolver_failure_never_falls_back_or_calls_evaluator`
- `orchestrator/tests/test_p3_b4_material_report.py` 全体: 未実走、`rc=16`
- node 集合 meta-test 2 件: 未実走、`rc=16`
  - `test_real_repo_group_collection_exactly_matches_canonical_nodes`
  - `test_shard_assignment_preserves_live_xdist_group_components_and_split_control`

非-pytest 検査:

- `python3 tools/check_docs.py`: `rc=0`
- `git diff --check`（所有 3 file）: `rc=0`
- 3 file の構文 compile diagnostic: `rc=0`
- node golden と実関数 30 node の AST 比較: `rc=0`
- resolver-before-single-evaluator AST 検査: `rc=0`
- 実 resolver present/fail-closed、M7/M8 test-body、present 射影 diagnostic: `rc=0`

## 独立 golden

変更前コードの public `build_material_report_document()` から一度だけ採取し、[test:727](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/tests/test_p3_b4_material_report.py:727) に固定しました。

- JSON: `7b73826656dc301565713cca8a74f3ccc523ce5659ccae6c7c0247be07864e74`
- Markdown: `46c130753462da2ff825f152ce36ff3c85f3bc04ba3c6d4388d5ba33651ead6b`

期待値は `_build_report_value()` / `_render_markdown()` から導出していません。固定 relative payload を使い、worktree path、`/tmp`、時刻を含まないことを検査しています。CWD を `/tmp` に変えた再実行でも同 digest でした。

## 受理集合

変更前:

- §5 の内容を読まず、assembly 成功時は常に `floor=None`。
- assembly 拒否時は evaluator を呼ばない。
- malformed pin、missing artifact、hash/schema 不一致も材料レポートからは観測されなかった。

変更後:

- 逐語 `未記入` は従来どおり `None` かつ同一 bytes。
- exact grammar と検証済み authority は `Fraction` として受理。
- malformed、missing、hash/schema/conversion 不一致は `None` へ落とさず拒否。
- assembly・ledger・publication の既存受理／拒否条件と public surface は不変。
- test authority の値は推定値ではなく、契約の下端境界 control `0` のみです。

## 波及可能性

- 所有外 production caller は射影資料上なし。`build_material_report_document`、`write_material_report`、CLI は同じ内部経路を通ります。
- `test_p3_b4_producer_auth_experiment.py` は `_load_and_evaluate` の AST callsite を参照。evaluator は移動せず、複数化もしていません。
- 共有 fixture は `immutable_publication`、`_INPUT_CACHE`、`_DOCUMENT_CACHE`、`test_p3_b4_raw_record_producer` の publication support。
- node 集合 consumer は `test_real_repo_serialization.py` の上記 meta-test 2 件。golden は [282行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-b/orchestrator/tests/test_real_repo_serialization.py:282) に更新済み。
- 単位 A の production-file scan 候補である `test_official_perf_closure.py`、`test_s8b_floor_campaign.py`、`test_campaign.py`、`test_p3_exploration_namespace.py` にも波及余地があります。

## 総括

単位 B の resolver 配線、4 状態射影、fail-closed、独立 golden を実装しました。  
不在時 bytes と public/CLI surface は維持しています。  
編集差分は指定された 3 file だけで、commit/add はしていません。  
docs・静的・軽量 diagnostic は `rc=0` です。  
pytest は dispatch infrastructure `rc=16` のため未実走で、完了・closed とは申告しません。