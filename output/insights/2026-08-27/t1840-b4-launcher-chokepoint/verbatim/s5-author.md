## 実装した関門

- G1: [base](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop.py:902)、[sort](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_sort.py:270)、[trigger](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_trigger_gating.py:565)。marker 作成時だけ sealed context を要求します。
- G2: [base](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop.py:1097)、[sort](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_sort.py:319)、[trigger resolved/public](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_trigger_gating.py:712)。exact marker の実 iteration に campaign-bound production context を要求します。
- G3: [base](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop.py:1469)、[sort](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_sort.py:462)、[trigger](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_trigger_gating.py:983)。`b4_mode` 分岐の先頭、`layout.ensure()` と state 前進前です。
- G4: [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/wal.py:411) で marker 付き lock の COMMIT だけを分類し、[実 sidecar/context 検証](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:360)を呼びます。
- G5: [create_b4_closed_critic_pair](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_closed_critic.py:1190) が production seal、campaign binding、expected driver、cfg driver、再検証 admission の一致を要求します。
- G6: [require_b4_production_context](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:197) が seal identity で test-only を拒否します。
- G7: [旧 main](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_closed_critic.py:1976) は専用 launcher を案内して即時拒否します。
- G8: [DRIVER_REGISTRY](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:411) は 3 本の実 `main` object を直接保持します。
- G9: [launcher admission 検証](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:469) は config/factory/driver より先です。bootstrap も同じ経路です。
- G10: [projection manifest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_closed_critic.py:613) の全 driver 共通 entry に launcher を追加し、独立算出 helper と exact-set test も更新しました。

## 負例と変異の対応

- M01: `test_p3_s4_loop.py::test_m01_b4_default_cfg_rejects_unsealed_marker_creation` — 実 base `default_cfg`、marker 未作成。
- M02: `test_p3_s4_loop_sort.py::test_m02_b4_sort_default_cfg_rejects_unsealed_marker_creation` — 実 sort `default_cfg`。
- M03: `test_p3_s4_loop_trigger_gating.py::test_m03_b4_trigger_default_cfg_rejects_unsealed_marker_creation` — 実 trigger `default_cfg`。
- M04: `test_p3_s4_loop.py::test_m04_b4_marked_run_one_iteration_direct_call_requires_launcher` — 実関数、root 不在、state 未変更。
- M05: `test_p3_s4_loop_sort.py::test_m05_b4_sort_run_one_iteration_direct_call_requires_launcher` — 実関数、root 不在、state 未変更。
- M06: `test_p3_s4_loop_trigger_gating.py::test_m06_b4_trigger_resolved_iteration_requires_launcher` — 実 resolved 関数、root 不在、state 未変更。
- M07: `test_p3_s4_loop_trigger_gating.py::test_m07_b4_trigger_public_iteration_requires_launcher` — 実公開関数、site resolution 未到達。
- M08: `test_p3_s4_loop.py::test_m08_b4_drive_iteration_rejects_before_layout_and_state_progress` — 実 drive。副作用不在で帰属し、root と loop state file がありません。
- M09: sort の同名 M09 test — M08 と同じ副作用不在を観測します。
- M10: trigger の同名 M10 test — M08 と同じ副作用不在を観測します。
- M11: `test_p3_b4_launcher.py::test_m11_real_wal_commit_requires_launch_sidecar` — 実 `wal.append`、WAL 未作成。
- M12: `::test_m12_real_wal_commit_rejects_sidecar_for_another_campaign` — cross-campaign sidecar、WAL 未作成。
- M13: `::test_m13_real_wal_commit_rejects_sidecar_for_other_live_context` — 正しい campaign id だが別 live context、WAL 未作成。
- M14: `::test_m14_real_production_pair_factory_requires_launch_context` — 実 factory、admission/artifact I/O 未到達。
- M15: `::test_m15_real_production_pair_factory_rejects_cross_driver_context` — exact driver kind 不一致、artifact 未作成。
- M16: `::test_m16_test_seal_cannot_be_promoted_by_evidence_class` — `evidence_class="production"` に偽装しても test seal identity で拒否します。
- M17: `::test_m17_real_legacy_cli_hard_fails_before_factory` — 実旧 CLI、factory spy 未到達。
- M18: `::test_m18_driver_registry_uses_real_main_object_identity` — 3 値すべてを `is` で検査します。

## 不変条件の維持

手動実体 probe で以下を再計算しました。

- base ordinary: `2cd75697` / `9f43a5b8`
- sort ordinary: `081dd46f`
- marker 付き base/sort/trigger の on/off 6 件: `ad0444da` / `8700ee8e`、`2c241821` / `df423528`、`2adb6cf7` / `6328b84a`
- trigger ordinary identity testも直接実行して通過。
- `test_require_b4_iteration_authorization_keeps_all_six_direct_rejections` の6ケースと、production context 経由の同じ6ケースを直接呼び出し、全拒否を確認。
- receipt の `os.link` 消費経路は変更していません。
- `test_launcher_positive_uses_real_factory_and_real_base_main_for_commit` は実 launcher、実 verifier、実 factory、実 base `main`、実 `wal.append` を通り、`outcome=certified`、iteration 2、COMMIT 1件を確認しました。

## 受理集合の変化

変更前は marker 自作、marked iteration/drive の直呼び、production factory 直呼び、旧 CLI、marker 付き COMMIT の別 producer が受理され得ました。変更後は production context と sidecar に束縛された launcher 経路だけが formal B-4 として受理されます。

marker 不在では G1〜G6 を呼ばず、G4 も実行しません。`test_unmarked_commit_does_not_execute_b4_sink_gate` で G4 spy 未到達を確認しました。通常 campaign、verifier/anomaly、build/verify/bench 順序、WAL schema の受理集合は変更していません。

## 在庫検査への追随

- projection の独立算出 helper と exact-set test に launcher を追加しました。
- 17 file・22箇所を照合し、process、root creator、build/materializer、COMMIT producer、receipt issuer の allowlist 追加は不要と確認しました。
- 内容走査の実関数20件を手動実行し通過しました。
- `test_s1_known_axes_freeze.py` と `test_campaign_import_invariant.py` は growth-hold により手動 import を拒否されました。前者は verifier 配下のみの走査で本変更と無関係です。後者向けには launcher に canonical direct-CLI bootstrap を入れ、直接 `--help` import を確認しました。
- 編集不能 file への追随要求はありません。

## 所有外への波及

- `loop.run_campaign` と `pipeline.evaluate` の marker 付き COMMIT は、新しい WAL 支配点の対象になります。marker 不在は従来どおりです。
- `test_campaign_lock_wal_consumers.py` は WAL consumer として焦点走対象ですが、pytest 基盤障害で未実走です。
- 新しい projection hash により、将来の admission record は launcher bytes を含む期待値が必要です。生きた既存 record はありません。
- `output/insights/` は未変更です。runner が自動生成した3個の infra diagnostic directory は exact path を確認後に削除し、開始状態へ戻しました。

## 実走した検査

指定の単独走と6 file焦点走はいずれも runner が `qstat -Q preflight rc=1` で停止し、rc=16、`child_started=false` でした。こちらから `qsub` は実行していません。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_launcher.py -q
rc=16、pytest child 未開始

python3 tools/run_tests.py orchestrator/tests/test_p3_b4_launcher.py \
  orchestrator/tests/test_p3_b4_closed_critic.py \
  orchestrator/tests/test_p3_s4_loop.py \
  orchestrator/tests/test_p3_s4_loop_sort.py \
  orchestrator/tests/test_p3_s4_loop_trigger_gating.py \
  orchestrator/tests/test_campaign_lock_wal_consumers.py -q
rc=16、pytest child 未開始
```

したがって pytest nodeid を「緑」とは報告しません。代替として、M01〜M18、新規 test file 全関数、既存6拒否×2、production positive、golden、主要既存 B-4 regression、在庫 census を実関数として直接実行し通過しました。AST parse 11 file、結合文字走査、`git diff --check` も通過しています。

## 総括

G1〜G10とM01〜M18を指定11 file内で実装しました。  
formal B-4 は launcher、production seal、sidecar、certified sink の組合せに限定されています。  
通常 campaign identity と marker 付き6 identity、既存6拒否を保持しました。  
在庫追随で所有外編集は不要でした。  
pytest runner は queue 基盤障害のため未実走であり、手動実体 probe と明確に区別しています。  
`git add`、commit、merge、rebase、push、checkout、qsub は実行していません。