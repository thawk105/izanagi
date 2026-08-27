## 新設した file

`orchestrator/campaign/p3_b4_protocol.py` を新設しました。

## F1

[p3_b4_launcher.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:232) で production seal、issuer、binding、sidecar writer、activation を closure 内へ封印しました。issuer は [p3_b4_launcher.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:321) で実 `verify_b4_admission_record` を必ず呼びます。closure builder 自体も module 属性から削除しています。

固定検査:

- `test_p3_b4_launcher.py::test_g9_bootstrap_uses_real_verifier_before_driver`
- `test_p3_b4_launcher.py::test_production_issuer_and_activation_are_not_module_attributes`

前者は verifier を差し替えず、実在する不正 admission JSON からの発行失敗と driver 未到達を確認します。架空の `VerifiedB4AdmissionRecord` による production context 作成は対象検査から全て除去しました。

## F2

[wal.py:465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/wal.py:465) が decode 済み lock から driver kind を導出し、[p3_b4_launcher.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:421) の G4 validator へ渡します。context 自身を期待値にする比較は廃止しました。

固定検査:

- `test_p3_b4_launcher.py::test_g4_uses_decoded_lock_expectations`

## F3

中央 validator は [p3_b4_launcher.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:289) で driver、campaign id、arm を exact 比較します。

各 driver の G2/G3 は cfg 由来値を渡します。

- Base: [p3_s4_loop.py:1104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop.py:1104)、[p3_s4_loop.py:1481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop.py:1481)
- Sort: [p3_s4_loop_sort.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_sort.py:328)、[p3_s4_loop_sort.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_sort.py:476)
- Trigger: [p3_s4_loop_trigger_gating.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_trigger_gating.py:721)、[p3_s4_loop_trigger_gating.py:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_trigger_gating.py:836)、[p3_s4_loop_trigger_gating.py:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_s4_loop_trigger_gating.py:1002)
- Factory: [p3_b4_closed_critic.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_closed_critic.py:1189)

固定検査:

- `test_p3_b4_launcher.py::test_production_validator_requires_exact_campaign_and_arm`
- `test_p3_b4_launcher.py::test_g4_uses_decoded_lock_expectations`

## F4

[p3_b4_protocol.py:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_protocol.py:6) を識別語の唯一の定義元にしました。値は変更していません。

[wal.py:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/wal.py:416) は lock 不在だけを非 B-4 とし、実在する lock の `OSError`、UTF-8 decode 失敗、codec 失敗を拒否します。

固定検査:

- `test_p3_b4_launcher.py::test_existing_unclassifiable_lock_rejects_commit`
- `test_p3_b4_launcher.py::test_existing_unreadable_lock_rejects_commit`
- `test_p3_b4_launcher.py::test_all_drivers_and_wal_import_the_protocol_constants`

## F5

[test_p3_s4_loop.py:3082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_s4_loop.py:3082) の期待値を `L.B4ProtocolError / "fixture run_one_iteration"` へ復元しました。

固定検査:

- `test_p3_s4_loop.py::test_b4_fixture_main_rejects_run_one_iteration_bypass_m13`

受理済みの旧 CLI 置換 3 件は以下を固定します。

- `test_r7_a10_thin_cli_drives_factory_both_arms_pair_gate_and_failure_rc`: 旧 CLI が launcher を案内して factory 到達前に hard-fail。
- `test_closed_critic_cli_has_fixed_marked_configs_for_all_drivers`: 3 driver の固定 marker、arm、campaign identity。
- `test_closed_critic_cli_constructs_only_fixed_marked_base_configs`: CLI 引数の迂回でも injected factory へ到達しないこと。

## F6

M08からM10は権威 layout resolver を同じ tmp layout へ揃え、実 iteration 関数を包む spy で `iteration == 1` の引渡し点を観測できる形にしました。永続 state file 不在の assertion は除去しました。

- [test_p3_s4_loop.py:2565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_s4_loop.py:2565)  
  `test_p3_s4_loop.py::test_m08_b4_drive_iteration_rejects_before_layout_and_state_progress`
- [test_p3_s4_loop_sort.py:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_s4_loop_sort.py:960)  
  `test_p3_s4_loop_sort.py::test_m09_b4_sort_drive_rejects_before_layout_and_state_progress`
- [test_p3_s4_loop_trigger_gating.py:2820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2820)  
  `test_p3_s4_loop_trigger_gating.py::test_m10_b4_trigger_drive_rejects_before_layout_and_state_progress`

## F7

[test_p3_b4_closed_critic.py:2348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:2348) の正例 docstring に全差し替え対象と証明範囲を記載しました。

固定検査:

- `test_p3_b4_closed_critic.py::test_launcher_positive_uses_real_factory_and_real_base_main_for_commit`

この正例が示すのは routing です。科学処理本体の実体を示すものではありません。

## 受理集合の変化

- marker 不在の通常 campaign の cfg、identity、valid-lock COMMIT 経路は変更していません。
- 不正または読取不能な既存 lock の COMMIT だけが、F4 指示どおり fail-open から拒否へ変わります。
- marker 付き formal 経路は、実 admission verifier と cfgまたはlock由来の driver、campaign id、arm の一致を新たに要求します。
- A1の test-only context による G1 marker 作成は維持しました。
- A2の COMMIT 後の lock 再分類は変更していません。
- sidecar の上書き可能性、receipt 一回消費、既存6拒否は変更していません。
- context は `search_config` と `CampaignConfig` に保存していません。

read-only identity probe では次を確認しました。

- Base通常: `2cd75697`、`9f43a5b8`
- Sort通常: `081dd46f`
- Marker付き6件: `ad0444da`、`8700ee8e`、`2c241821`、`df423528`、`2adb6cf7`、`6328b84a`
- Trigger通常8件の期待値は変更していません。

## 書き換えた既存検査

全て実 commit 済み admission fixtureと実 verifierを通る helperへ移しました。

- `test_p3_b4_launcher.py`: M12、M13、M15、sidecar overwrite。
- `test_p3_s4_loop.py`: production context 下の6拒否、bound decision、一回消費、bootstrap、no-build、receipt-first。
- `test_p3_s4_loop_sort.py`: certified shared gate、gate-first、no-build。
- `test_p3_s4_loop_trigger_gating.py`: certified shared gate、resolved gate-first、no-build。
- `test_p3_b4_closed_critic.py`: certified factory、admission keyword/binding、repository-checked pair、projection/prompt/model rejection、driver projection closure、fixed executable、receipt v3、public receipt positiveと各 binding/layout/marker negative。
- F7正例: config 作成に使っていた架空の production context を test-only config contextへ変更し、production context 自体は launcher内部で発行。

到達しなくなる負例は削除していません。M12、M13、M15は実 admission fixtureを経由する形へ再構成しました。

## 正例の差し替え一覧

正例で差し替えている対象は以下の全18件です。

- `C.REPOSITORY_ROOT`
- `C.ROLE_FILE`
- `C.shutil.which`
- `C.B4ClosedCriticController.__init__`
- controller内部のprovider runner
- `C.exploration_campaign_layout`
- `C._load_stable_snapshot`
- `C.require_admitted_campaign`
- `C.make_critic_digest`
- `C.make_critic_identity_projection`
- `B4L.exploration_campaign_layout`
- `L.exploration_campaign_layout`
- `L.ident.ensure_resumable_attempts`
- `patchharness.assert_pinned_clean`
- `p2_2._assert_single_tenant`
- `L.run_one_iteration`
- `L.require_admitted_campaign`
- `L.make_critic_identity_projection`
- `L.make_critic_digest`

`create_b4_closed_critic_pair`、driver `main`、`wal.append` は差し替えていません。

## 実走した検査

指定 commandを3回試しました。

1. `wal.py` 差分あり。
2. `wal.py` だけ一時的にHEAD bytesへ戻し、他の修正を残した状態。
3. F4差分を再適用した最終状態。

全て `rc=16` で、出力は以下でした。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

したがってpytest nodeidは全件未実走です。test childが起動していないため、実装差分の赤もcontract-loader-driftの赤も観測されていません。両者を緑とは報告しません。

補助確認として、12 fileのAST parse、焦点test module 5本のimport、`git diff --check`、identity probeは成功しました。これらはpytest実走ではありません。

## 総括

F1からF7の実装と検査更新は完了しています。  
新設 file は `orchestrator/campaign/p3_b4_protocol.py` です。  
許可外のtracked file、docs、hooks、agent設定は変更していません。  
`git add`、`git commit`、merge、rebase、push、qsubは実行していません。  
唯一の未完了事項は、Pegasus dispatcher障害によるpytest未実走です。