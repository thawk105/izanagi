---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-occupancy-repair-20260826
seq: 1
---

## 新規

### {{F:stubbed-dependency-hides-the-mechanism}}. 裁定が要求した機構の正例・負例を、実装子が両層とも依存先の stub で書き、機構を 1 度も通さないまま緑になった [恒真ゲート] [テスト代表性]

- 事象: 段 4 裁定は解除条件として「同じ pid が 1 回目の scan だけ issue を出し次で消える」正例と
  「3 回とも出る」負例を synthetic `/proc` で固定することを要求した。段 5 の実装子 2 本は
  どちらもその名前のテストを書き、親の実走も緑だった。しかし
  `orchestrator/tests/test_check_worktree_occupancy.py` の新設 4 node は
  `monkeypatch.setattr(checker, "scan_worktree_occupancy", scan)` で作り置きの `ScanReport` を返し、
  `orchestrator/tests/test_dev_wave_cleanup.py` の新設 node は `_occupancy_payload` を stub していた。
  **両方の層が依存先を差し替えたため、実際の走査が変化する `/proc` に対して
  一過性 issue を解消できるかを誰も検査していなかった。** 検査されていたのは再試行の制御フローだけである。
- 根本原因: 裁定文が「正例・負例を対で固定せよ」と**性質**で書き、
  **どの実体を通るか**を書かなかった。実装子は名前と観測可能な結論 (rc と retry 回数) を
  満たす最小の書き方を選び、それは stub だった。緑・テスト名・件数のどれもこの差を表さない。
- 恒久対応: `docs/dev-wave/workers.md` の `DW-S05-C` へ
  「機構の正例・負例を要求する裁定は、**その機構の実体を通ることを prompt で名指しする**
  (`X を差し替えてはならない。本物を呼べ`)」を足す。本 wave の fix prompt がこの形を実証し、
  `test_main_real_scan_accepts_pid_issue_that_disappears_after_first_scan` と
  `test_main_real_scan_rejects_same_pid_issue_on_all_three_scans` が実 scanner を
  連続で呼ぶ形へ置き換わった。
- 再発検知: 段 6 の敵対レビューのレンズに「新設 node が、裁定の名指しした機構の実体を通るか」を
  入れる。本件は 2 本のうち 1 本 (運用レンズ) だけが検出し、正しさレンズは見落とした。
  変異では検出できない — stub 版でも制御フローの変異は正しく KILLED になるためである。

## 再発

### F489

- **再発: 2026-08-26 (4 例目)** — 受入全走 2 走とも 1 node が
  `phase=occupancy reason=occupancy result is indeterminate or inconsistent` (rc=22) で落ち、
  **落ちる node は走ごとに移動した** (`test_forward_merged_landing_tip_is_used_for_cleanup[asserted]` と
  `test_reentry_states_run_only_remaining_cleanup[b]`)。原因は D705 / D793 のどちらの射程でもなく、
  **再試行の門そのもの**だった。`tools/dev_wave_cleanup.py` の `_assert_unoccupied` は最大 3 scan を
  持つが、2 回目へ進む条件が「全 issue が `error=="missing"` かつ
  `source ∈ {stat,cwd,cmdline}`」に限られ、48 worker の churn で出る他種別が 1 件混じると
  **再試行が 1 度も発火せずに拒否していた** (拒否本文の実測 `attempts=1 retry_count=0`)。
  実 `/proc` に到達する成功経路は 6 node で、各 node が preflight / recheck の 2 phase を持つため
  1 走あたり 12 判定、実測の判定あたり赤率は 8.3% (2 走 24 判定中 2 赤)、
  修理前に 1 走が緑になる確率は 35%。単独 file 走は 94 passed で緑のままだったため、
  **前回 (2026-08-24) の解除条件「明示 file 走が全緑」は満たされたまま再発した。**
  原因の特定が 3 例目まで 2 度誤ったのは、拒否本文が `payload["issues"]` を捨てていて
  **何が読めなかったかを一切残さなかった**ためである。恒久対応は {{D:occupancy-retry-by-persistence}}。

## supersede 追記

- F489 **supersede: 2026-08-26** — D705 と D793 はいずれも `_scan_pid` 内の個別経路 (zombie、削除済み cwd) を閉じたもので、再試行の門が種別で閉じているという上位の欠陥は 4 例目まで残っていた。現行の恒久対応は {{D:occupancy-retry-by-persistence}} であり、issue の種別に依存しない。
