---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-prov-incremental-audit
seq: 1
---

## 新規

### {{F:acceptance-untracked-churn-flips-state-assertions}}. 受入全走が自分の作業ツリーへ作る未 tracked scratch が、repo 状態の不変を assert するテストを落とす [テスト代表性] [計測汚染]

- 事象: provenance 差分監査 wave の受入全走で 2 回続けて非帰属赤が出た。1 回目は 3 件
  (`test_p3_b4_producer_auth_experiment.py::test_case_failure_records_aborted_and_remaining_cases_continue`、
  同 `::test_disposable_tree_mutation_does_not_change_main_worktree`、
  `test_run_tests_preflight.py::test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch`)、
  2 回目は 1 件 (`test_check_ai_provenance.py::test_provenance_headroom_short_queue_unavailable_cap_oom_stops`)。
  **落ちる node が回ごとに違い、同じ 2 file の単独走は 266 passed で緑**である (競走であって決定的赤ではない)。
- 根本原因: 受入全走は 1 つの wave worktree で shard を並行に走らせる。`t316` 系のテストは repo 直下へ
  `.t316-live-<8 文字>/` という **`.gitignore` の対象外**の scratch directory を作る。一方で、
  `git status --porcelain -z --untracked-files=all` の出力 bytes が走行前後で変わらないことを要求する
  テストが複数ある。前者が後者の観測窓に入ると後者が落ちる。
  - `cap_oom` 族 (`_run_bounded_scope` を monkeypatch して `cap_oom` を返させる 2 つの双子テスト) は、
    その後 **production が実 repository の指紋を before/after で取り、変化していれば fallback を拒否する**
    分岐へ入る。期待した「ログインの余裕もキューも無いため、いまは実行できません」ではなく
    「local 試行の前後で tree / submodule 状態が変化しました」が出る。実測は
    `各状態出力 bytes (0, 0, 313, 0, 0) -> (51, 0, 313, 0, 0)` で、未 tracked が 1 件増えている。
  - `ScratchTree` 族は `assert_repository_unchanged` が同じ理由で落ちる。
- 帰属の判定: 同 wave の差分は `tools/check_ai_provenance.py` と
  `orchestrator/tests/test_check_ai_provenance.py` だけで、**作業ツリーへ未 tracked path を作らない**
  (受領証は共通 git-dir 配下で `git status` に現れない)。`output/pegasus-dispatch/` は `.gitignore`
  対象なので dispatch 成果物も原因ではない。したがって非帰属である。
- 恒久対応: **部分的。** 同 wave は `cap_oom` 族の双子テスト 2 件 —
  `test_check_ai_provenance.py::test_provenance_headroom_short_queue_unavailable_cap_oom_stops` と
  `test_run_tests_preflight.py::test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch`
  — を、production の指紋採取を monkeypatch して周囲の churn から隔離した。前者を直した 3 回目の
  受入で後者だけが落ち、族であることが確定したので同じ隔離を入れている。
  **`ScratchTree` 族の 2 node (`test_p3_b4_producer_auth_experiment`) は手を付けていない**
  (1 回目の受入でしか観測しておらず、2・3 回目では落ちていない)。本質的な是正は
  「`t316` 系の scratch を repo 外へ出す」か「repo 状態の不変を要求するテストを一律に隔離する」の
  どちらかで、main 全体のテスト隔離に当たるため別 wave の scope である。
- 再発検知: 受入全走でこの 4 node のいずれかが落ち、かつ同じ file の単独走が緑であること。
  落ちる node が回ごとに変わることが競走の署名である。**「N 走完全一致」は flake の証拠にならない**
  (`DW-O18`) が、本件は逆に **node が回ごとに変わる**ので決定的赤ではないと言える。
