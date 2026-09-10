## 対応表

| 所見 | 判定 | 種別 | 根拠 | 成果物影響 |
|---|---|---|---|---|
| F-P1 | closed | real | [fix1.patch:225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2327-s1-sort-contract-binding/codex/fix1.patch:225) で派生 pin を再計算値へ更新。`test_build_approved_valid_fixture_output_depends_only_on_spec_pin` と `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal` が検査する。 | production 成果物への影響なし。test golden の不整合を解消。 |
| F-P2 | closed | real | [fix1.patch:238](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2327-s1-sort-contract-binding/codex/fix1.patch:238) で旧 `resolve` を即失敗させ、`resolve_evidence` の契約 ID と oracle 前後順を `test_s1_sort_best_runs_same_oracle_before_source_materializer` が検査する。 | consumer test の偽陰性を解消。production 成果物への影響なし。 |
| F-P3 | closed | real | [s8b_oracle_driver.py:1731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_oracle_driver.py:1731) で ID を写し、[同:1788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_oracle_driver.py:1788) で条件付き転送。`test_success_wal_order_budget_and_evaluate_contract` の [sort assertion:3921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_oracle_driver.py:3921) と [非 sort assertion:3923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_oracle_driver.py:3923) が固定する。 | s8b oracle の sort_best が契約なし再解決で全件 abort する退行を解消。 |
| F-P4 | closed | real | [s8b_floor_campaign.py:4383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_floor_campaign.py:4383) で evidence、[同:4430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_floor_campaign.py:4430) で build kwargs へ同じ ID を転送。`test_build_cells_resolves_site_compilers_and_binding_once_before_cell_loop` の [2814](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_floor_campaign.py:2814) と [2818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_floor_campaign.py:2818) が両経路を検査する。 | floor の sort_best が build admission で全件失敗する退行を解消。 |

F-P4 の build 経路は閉じている。`build_kwargs` は `_invoke_build` の `**build_kwargs` から、[invoke_build:4700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_floor_campaign.py:4700) の `**kwargs`、`call_kwargs` を経て `build_fn` へ無加工で届く。`descriptor_aware=False` が除くのは descriptor だけで、契約 ID は除かない。

既定 `build_v2` は [buildcache.py:2984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/buildcache.py:2984) で ID を受け、`source_evidence`、束縛済み `src_token`、ID を `_build_v2_impl` へ渡す。入口では evidence と token の不一致を拒否し、出口の [_recheck_source_evidence:3370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/buildcache.py:3370) は同じ ID で evidence 全体を再解決して exact 照合する。共有 `_make_fake_build` は新 keyword を明示受理し、対象 test の局所 wrapper も `**kwargs` を持つ。提示された焦点走でも、既知の selector 赤以外に strict double の `TypeError` は出ていない。

F-P3 では manifest 作成と実行が同じ `prepare_fn` を通り、`_expected_binding` と `actual_binding` は [1698-1701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_oracle_driver.py:1698) で照合される。production の両側は s1 の契約付き materializer に由来する。

## must-fix

なし。

## nit

- real: `_prepare_factory` と `_fixture_source_evidence` は契約 ID を運ぶが、fixture token 自体には ID を反映しない。この入力では転送 assertion は通るため、binder preimage の正しさはこの二つの node 単独では検出しない。ただし s1 の `test_prepare_sort_best_binds_attested_oracle_contract_into_src_token` と D1630 側テストが別に担当しており、新たな成果物影響はない。

## refuted

- real input、must-fix 影響は refuted: sort_best が [4396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_floor_campaign.py:4396) の正規化へ入るのは、prepare 後の source drift、または不整合な注入 `prepare_fn` などで token が変わる場合。既定 `build_v2` は新 evidence と旧 `prepared.src_token` の不一致を拒否するため、[record 作成:4655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/campaign/s8b_floor_campaign.py:4655) へ到達せず、durable identity が別物になる production 経路はない。 permissive な注入 builder だけは異なる token を観測できるが、既存 test seam に限定された据え置き挙動。成果物影響: 既定 floor 成果物にはなし。
- real omission、意味影響は speculative かつ refuted: `prepared_for_eval` は `oracle_attempt` を写していない。ただし evaluate へ渡るのは genome、token、各 condition record、契約 ID で、`oracle_attempt` は evaluate kwargs でも binding 比較でも使用されない。この omission は fix 前から存在し、WAL・受理意味の退行を示さない。成果物影響: なし。
- real signature change、退行は refuted: `_fixture_source_evidence` と `_make_fake_build` は optional keyword の追加だけで既存 assertion を削っていない。`_prepare_factory` も sort_best だけに ID を設定し、非 sort の call shape は維持する。明示的な stock_common + sort_best の二セル選択後も、compiler と binding が loop 前に各一回という assertion は [2810-2812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_floor_campaign.py:2810) に残る。成果物影響: なし。

## 変異対応表

| 変異 | 殺す node と assertion | 冗長 gate |
|---|---|---|
| M7 | `test_success_wal_order_budget_and_evaluate_contract`: sort_best で `kwargs["sort_oracle_contract_id"] == ORACLE_CONTRACT_ID` ([3921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_oracle_driver.py:3921)) | なし |
| M8 | 同 node: 非 sort で key 不在 ([3923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_oracle_driver.py:3923)) | なし |
| M9 | `test_build_cells_resolves_site_compilers_and_binding_once_before_cell_loop`: evidence の sort_best 要素が契約 ID 付き ([2814-2817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_floor_campaign.py:2814)) | なし |
| M10 | 同 node: build の sort_best 要素が契約 ID 付き ([2818-2821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_floor_campaign.py:2818)) | なし |
| M11 | 同 node: evidence・build とも stock_common の要素が `{}` ([2815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_floor_campaign.py:2815)、[2819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2327-s1-sort-contract-binding/orchestrator/tests/test_s8b_floor_campaign.py:2819)) | なし |

## 総括

F-P1〜F-P4 はすべて root cause まで closed、partial / regressed はない。  
build と evaluate の契約 ID 転送、および非 sort の key 不在が固定された。  
正規化分岐は drift・注入 seam では入るが、既定 builder は不一致を拒否する。  
M7〜M11 はすべて明示 assertion で殺せ、冗長 gate はない。  
本レビューでは pytest を実走しておらず、判定は指定資料の静的検査による。