静的監査の結論は、must-fix 1件、nit 1件です。直接 caller 15件は全て確認済みです。

### 所見1 — real

根拠: `run_campaign` は必須引数化されています（[loop.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/campaign/loop.py:132)）。一方、[test_trigger_gate_binding.py:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_trigger_gate_binding.py:400) の kwargs（同:405）には `declared_use_class` がなく、同:420 の `signature.bind` で失敗します。

成果物影響: 共有 consumer test が受入前に止まり、wave の land と certified 成果物の確定を阻害する。

種別: must-fix

### 所見2 — real

根拠: 新テストが例外メッセージへ依存しています（[test_campaign.py:8439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_campaign.py:8439)、同:8522）。

成果物影響: 診断文だけの変更で偽赤となり、挙動と受理集合が不変でも受入が停止する。

種別: nit

### 所見3 — refuted

根拠: production の直接呼出しは `test_campaign.py:4727` の15件と一致し、raw AST 検査も全 call に `declared_use_class` を要求しています（同:4816、同:4830）。`campaign_namespace` は実装呼出しには残っていません。

成果物影響: 現行 production campaign の selector 欠落は確認されず、なし。

種別: nit（対応不要）

### 所見4 — refuted（8c）

根拠: 8c は `DECLARED_USE_CLASS` を宣言済みです（[p3_autonomous_workload_trial.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/campaign/p3_autonomous_workload_trial.py:123)）。`--no-build` の `CampaignLayout` 直構築は同:2834に残りますが、meta-test は `CampaignLayout` 経路も root producer として検出します（[test_p3_exploration_namespace.py:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_p3_exploration_namespace.py:63)、同:508）。

成果物影響: 8c の no-build 経路が新 selector 必須化で意図せず落ちる矛盾はない。

種別: nit（対応不要）

### 所見5 — refuted（fixture・partial・別 API）

根拠: `conftest.py` に wrapper はなく、`**kwargs` の trigger consumer は新名へ更新済みです（[test_p3_s4_loop_trigger_gating.py:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:415)）。partial は resolver 用文字列 fixture に過ぎません（[test_campaign.py:4330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_campaign.py:4330)）。`s8b_floor_campaign.run_campaign` は別 API です（[s8b_floor_campaign.py:5585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/campaign/s8b_floor_campaign.py:5585)）。

成果物影響: 変更対象 API の未更新共有 fixture は確認されず、なし。

種別: nit（対応不要）

### 所見6 — refuted（hooks・test file 集合・裁定逸脱）

根拠: guard は official / exploration の両 root を従来どおり保護しています（[guard_write.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/hooks/guard_write.py:244)、[guard_bash.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/hooks/guard_bash.py:80)）。差分は全て `M` で、新設・改名 test file はありません。`loop.py:142` で selector は一本化され、拒否は cid 計算（同:181）より前です。

成果物影響: hooks 防護、test 集合、cid/preimage 不変、裁定の1〜7への逸脱は静的にはなし。

種別: nit（対応不要）

## 総括

real は未更新の indirect consumer 1件です。  
直接15 caller、6 producer、8c の閉包は静的に整合しています。  
新設拒否テストの診断文字列依存は nit として残ります。  
pytest は reviewer も実装子も実走しておらず、緑とは扱いません。  
s5 報告では Pegasus dispatch が pytest 開始前に停止しています。  
まず stale consumer を修正し、下記 nodeid を `tools/run_tests.py` 経由で実走してください。

## 親が実走すべき nodeid（優先度順）

- P0 `orchestrator/tests/test_trigger_gate_binding.py::test_signature_stubs_keep_legacy_calls_valid_with_none_default`
- P1 `orchestrator/tests/test_campaign.py::test_run_campaign_requires_declared_use_class`
- P1 `orchestrator/tests/test_campaign.py::test_run_campaign_rejects_unsupported_declared_use_class_before_output_creation[qualification]`
- P1 `orchestrator/tests/test_campaign.py::test_run_campaign_rejects_unsupported_declared_use_class_before_output_creation[dry]`
- P1 `orchestrator/tests/test_campaign.py::test_run_campaign_rejects_unsupported_declared_use_class_before_output_creation[unknown]`
- P1 `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- P1 `orchestrator/tests/test_p3_exploration_namespace.py`
- P1 `orchestrator/tests/test_campaign.py::test_run_campaign_declared_use_class_does_not_change_campaign_id`
- P2 `orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_contract_sentinel_flows_to_run_campaign`
- P2 `orchestrator/tests/test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean`