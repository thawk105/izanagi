---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1472-provider-init-indeterminate
seq: 1
---

## {{D:c04-provider-init-indeterminate-implementation}}. C04 の crash 解釈へ provider-init/transport-admission 失敗を含める実装

**決定:** `orchestrator/campaign/p3_autonomous_workload_trial.py::_finish_trial()`のpre-loop部分
(`experiment_indeterminate = False`直後、per-workload loop開始前) へ、既存のmid-loop
supervisor-error分岐と対称な条件分岐を追加する。`_finish_trial()`呼出し前に既に`fatal_error`が
設定されている場合 (`_provider_set()`のprovider-init失敗、または`admit_claude_transport()`の
transport-admission失敗のいずれか — 両者は同じ`fatal_error`変数を共有する同一code pathであり
分離しない) かつregistered trial (`launch_admission.binding is not None`) のとき
`experiment_indeterminate = True`とし、C06 budget-tracked trial (`budget_ledger_path is not
None`) のときは同じ文言 (`"budget cell terminal is indeterminate after provider
initialization or transport admission error"`) で`AutonomousTrialError`をraiseする。
exploratory (unregistered) trialは現状維持 (indeterminate化しない)。

`_provider_set()`のexcept節・journal event (`_append_provider_init_error`) は変更しない。
pinned test `test_m26_manifest_binding_survives_provider_init_and_supervisor_failures`の
scenario1 (provider-init failure) を拡張し、report/attempt-registry/lifecycleの3点セット
(`lifecycle_terminal_status`, `terminal_status=="not-consumed"`, lifecycle rows
`["start","terminal"]`で`terminal_status=="indeterminate"`) を検証するようにした。新規test
3本を追加した: registered trialのtransport-admission failure、C06 budget-tracked trialの
raise到達と例外後のattempt/lifecycle永続化、exploratory trialではindeterminate化しない
ことの確認 (この3本目が変異事前登録MUT-1の唯一のkill test)。

**理由:**
- D657の要求 (実験全体をindeterminateとしてdurableに表現し、再走と成功を混同しない) を
  満たすには、provider-init/transport-admission失敗もmid-loop supervisor-error crashと
  同じ仕組みで扱う必要がある。`autonomous_trial_completeness.py`の
  `_check_terminal_projection`/`_check_workload_coverage`が既に`provider-init-error`/
  `transport-admission-error`を対称な終端event種別として扱っており (`cells==[]`の
  zero-cells経路を明示的に許可)、report側の`lifecycle_terminal_status`付与だけが
  欠けていた。段3敵対相談 (luna所見1) がproduction callerの実在 (CLI → `run_trial()` →
  `admit_registered_launch()`の経路) を独立に確認し、DW-G04の発火gate要件を満たすと
  判定した。
- 段3敵対相談 (sol所見1) は、`terminal_status=="not-consumed"`が`trial_registry.py`の
  `attempt_index>0`開始条件 (直前slotのterminal_statusが厳密に`retryable-failure`である
  こと) を満たさないため、provider-init/supervisor-error crash後に同一attempt_index系列で
  次slotを消費する再走が現状のattempt-registry状態機械では成立しないと指摘した。ただし
  これは本waveが新たに作る欠陥ではなく、既存のmid-loop supervisor-error crashにも既に
  存在するpre-existing gapであり、本waveのscope (brief記載の「8c supervisorのstate
  machine全体整合」除外) の外にある。D657の「再走と成功を混同しない」という要求
  (indeterminateがcompleteと誤認されない) は満たされるが、attempt-registry上の真の
  再走可能性は別waveの課題として残る。

**却下した選択肢:**
- provider-initとtransport-admissionを別々の分岐で扱う — 同一`fatal_error`共有code pathを
  人為的に分離するだけで実質的な安全性の向上が無く、`_check_terminal_projection`の既存の
  対称な扱いとも整合しない。
- `run_trial()`のprovider-init except節で直接lifecycle terminalizeする — `_finish_trial()`が
  reportを生成した後にattempt/lifecycle terminalizeする既存の一本化された経路と二重記録に
  なる (段3 luna所見3で確認)。
- C04が要求する「再走許可」の完全な意味論 (attempt-registry状態機械の再設計) まで本waveで
  実装する — 8c supervisorのstate machine全体整合という別の大きいgapであり、規律5
  (段階導入/盛らない) に照らし別waveへ送る。
