---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-known-violation-audit
seq: 2
title: campaign advisory flock が exploration リダイレクトを無視するバグを修正した (コード+テスト、branch worktree-dev-wave-known-violation-audit、変異matrix = baseline PASSED・3/3 KILLED・SURVIVED0・MISMATCH0)
---

## 本文

- command 引数「known violationがあれば直す。リワードハック禁止。テストが間違っていれば
  テストを直し、テストされているものが間違っていればそれを治す」の一次資料を特定した:
  2026-08-17 `/rulings 全件 第4回` ユーザー裁定 (`docs/archive/worklog-phase3-0817-611.md`)。
  同裁定が直接対象にした既知漏れ4件は本日 [T-1222] 完了で全件決着済みと確認し (neither/
  test-side実装済み/target-side実装済み/恒久保留premise再確認)、新規対応なしと判断した。
- 調査の過程で、本日着地した [T-565] (campaign単位advisory flock、{{D:campaign-lock-honors-exploration-redirect}})
  に、exploration リダイレクトを無視する既存欠陥を発見した。target-side 修正を段2 codex plan・
  段3 敵対相談2レンズ (blocker/major なし)・段6 敵対レビュー2本 (blocker/major なし) を経て採用し、
  実装した。
- **near-miss の実測**: shared main checkout (隔離前) で探索目的の全テスト走行を行ったところ
  12 failed + 3 error が出たが、投入中に local main の commit 数が 62→71 進んでいたことと符合し、
  隔離 worktree での再走で 11+3 件 (`test_s8b_floor_campaign.py` 系・submodule real-repo 系) が
  全緑化することを確認した。並行 wave の land 活動との衝突による near-miss であり、実装差分とは
  無関係と判断した。真に決定的な赤は `test_exploration_external_root_keeps_wave_clean` 1件のみ
  だった。
- 段5 実装子は Pegasus dispatch preflight (`qstat -Q` rc=1) で pytest を実走できず、緑を申告
  しなかった (DW-S05-C 準拠の正直な報告)。親が commit 後に焦点走 (582 items) を実走し
  569 passed / 13 skipped / 0 failed を確認した。
- 段2 codex plan・段3 レンズA (sol) が独立に指摘: 新設 focused test は明示 `output_root` を
  official/exploration 双方に渡すため `declared_use_class` の取り違えを単独では検出できないが、
  既存の `test_exploration_external_root_keeps_wave_clean` (empty output_root、env var 経由の
  分岐) が独立に検出する。変異事前登録の初回 (M1) はこれを見落とし MISMATCH となり、DW-M08 に
  従い実測 failed_nodes で expected_nodes を補正して再登録・再走し baseline PASSED・3/3
  KILLED・SURVIVED0・MISMATCH0 を確定した。

## 次の一手差分

### 新規

- {{T:growth-test-holds-individual-review}} **P3・新規**: `orchestrator/tests/growth_test_holds.py`
  の既存恒久保留59件を、2026-08-17裁定と同じレンズ (test-side/target-side/neither 判定) で個別
  レビューする。ユーザー裁定原文「既存の恒久保留59件も同じ目で見直す射程に入る (一括解除の指示
  ではない — 個別に判断する)」が根拠。規模が大きく規律5 (段階導入・盛らない) に照らし本waveでは
  着手しなかった。
