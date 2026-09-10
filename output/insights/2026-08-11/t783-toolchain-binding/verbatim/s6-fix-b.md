実装は完了しましたが、pytest は dispatch preflight で停止したため、各項目は `partial（実装済み・未実走）` です。docs 編集・commit は行っていません。

| 対象 | 状態 | 対応 |
|---|---|---|
| R1-1 | partial | wrapper が各 tool の `version` 全文を渡し、`build_v2` が期待値ありの場合だけ identity 用観測とは別に全文を再観測・比較 |
| R1-2 | partial | 実 wrapper を通る cc realpath、cxx version、cmake version の個別拒否テストを追加。対象 class は autouse fake の適用外 |
| 既知赤 1 | partial | golden caller に matching contract の `VerifiedCalibration` と toolchain fake を渡した。exact SHA は不変 |
| 既知赤 2 | partial | subprocess helper 内でも autouse fixture と同じ process-safe toolchain fake を明示配線 |
| 回帰 | 未検出 | 静的監査と `git diff --check` は成功。pytest は未実走 |

主な変更箇所:

- [_tool_version／_toolchain_manifest は不変、全文観測を分離](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:199)
- [期待値を identity 投影と全文投影へ分離](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:268)
- [全文比較後に従来どおり _v2_identity を呼ぶ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:710)
- [wrapper の期待 manifest に version 全文を追加](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1068)
- [wrapper 3 脚の拒否テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_s8b_floor_campaign.py:836)
- [下位行 drift の buildcache 拒否テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_buildcache_v2.py:420)
- [golden caller の追随](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_s8b_materialization.py:471)

検査は次の範囲を `tools/run_tests.py` に投入しましたが、`qstat -Q preflight rc=1` により runner が `rc=16` で終了し、pytest は起動していません。

- `test_buildcache_v2.py::{test_v2_expected_toolchain_manifest_exact_match_is_accepted,test_v2_expected_toolchain_manifest_mismatch_refuses_before_cache_claim,test_v2_expected_toolchain_version_lower_line_drift_refuses_before_cache_claim,test_v2_manifest_records_complete_identity}`
- `test_s8b_floor_campaign.py::TestFloorToolchainBinding`
- `test_s8b_floor_campaign.py::test_build_cells_resolves_site_compilers_and_binding_once_before_cell_loop`
- `test_s8b_floor_campaign.py::test_deterministic_artifacts_across_roots_and_subprocess_environments`
- `test_s8b_materialization.py::test_floor_manifest_golden_stable`

所有外への静的波及可能性:

- `pipeline.py`、site-gate、oracle 系の `build_v2` caller はすべて既定 `expected_toolchain_manifest=None` で、挙動は不変です。
- repo 内で非 `None` を渡す production caller は floor wrapper のみです。repo 外で旧 3-key 期待 manifest を直接渡す caller は、新しい全文 key がないため fail-closed になります。
- completion manifest の toolchain は従来の 3 key のままで、artifact consumer の形状は不変です。
- fix-A 所有の `silo_ladder_rung1.py` とその driver test に並行差分がありますが、触れていません。

## 総括

- R1-1 / R1-2 / 赤 2 件: すべて **partial（実装済み・未実走）**、regressed 申告なし。
- `_v2_identity` preimage は不変: [buildcache.py:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:295)、全文比較は呼出前の同ファイル 711–726 行。
- 実走 nodeid: **なし**。上記 targeted 範囲は `tools/run_tests.py` の dispatch preflight `rc=16` で未実走。
- `test_s8b_materialization.py` の exact SHA 書換え: **no**。
- 所有外への波及: 既定 `None` caller／artifact consumer は不変。旧形式の非 `None` 外部 caller のみ fail-closed。