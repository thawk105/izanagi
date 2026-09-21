---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2833-land-eintr-retry
seq: 1
title: [T-2833] land の登録 worktree path 解決を InterruptedError のときだけ最大 5 回呼び直した — F672 経路の局所修正、効果は未実測 (コード + テスト + insight、branch worktree-dev-wave-t2833-land-eintr-retry)
---

## 本文

- 依頼 (D2206 項 1、第 29 回 /rulings) を軽量版で処理した。段 1 brief → 段 4 裁定 (段 2・3 は省略、上限は 1 path あたり呼び出し最大 5 回・sleep なし、変異 M0〜M7 を事前登録) →
  段 5 Codex author 1 本 → 段 6 (焦点走・変異・敵対レビュー 2 本、fix なし) → 記録。詳細と受理集合の記述は `output/insights/2026-09-21/t2833-land-eintr-retry/README.md`。
- **段 6 の Codex review 子 2 本が Codex の利用上限 (`try again at Sep 26th, 2026 7:35 PM`、14:40:51 JST) で即死した。** D582 に従い自動再試行せずユーザーへ通知した。
  実装は Codex author commit で完了していたので、敵対レビューは独立 context の Claude 子 2 本 (Plan / opus、同じ prompt・同じ 2 レンズ、read-only) で代替した。
  DW-S06-A / DW-O01 の「codex」からの逸脱で、Codex の検査を受けたことにはならない。must-fix 0 のため fix は不要で、Codex 不可用は実装差分に影響していない。F818 の再発として追記した。
- レビュー: A (過剰・削除) GO、所見 6 (should 2 = 記録の文言: brief の「受入の取り直しまで遅れる」は F672 の是正済み復旧と矛盾する / 効果は未実測で、使い切れば同じ文言の rc=31 が残る)。
  B (正しさ・検出力) GO、所見 4 (nit)。採用はすべて記録の文言、不採用 (A4 / A5 / B1 / B4) は test の冗長と T5 の約 0.6 µs の実時間窓 (既存 test と同構造) で、Codex author が要るため insight に記録するだけにした。
- 親の懸念 (T3 が「他の OSError も再試行する」変異を呼び出し回数でしか見ない) はレビュー B が refuted とした — 回数 = 1 は 2 回目を呼ばないことの証明で、「1 回失敗→次は成功」の入力も拒否されることまで押さえる。
- 焦点走 (変更 test file + land tool の consumer 7 本 + inventory 4 群): 1,824 passed / 4 skipped、赤 0。変異 (事前登録 8 本、独立 clone・dispatch): final は KILLED 7 / SURVIVED 1 (等価対照 M0) で期待との一致 8 / 8、既存 test の赤 0。
- D2206 項 1 の「SIGALRM handler 下で 1 回注入して成功する test」は、handler 無しの成功 (T1[1]) と armed 下での期限超過 (T5) の組で満たした。期限前の handler は何もしないので armed か否かで分岐は変わらない (コードで確認)。
- **受入 final-1 (tested main `5be086476`、tip `49cda141c`、15:21〜15:47) は赤 3 件で rc=70、非帰属と判定して受入を取り直した。** 赤は 3 件とも
  `orchestrator/tests/test_mutation_harness.py` の局所 hang timeout を 1 秒にした試験 (`test_local_timeout_after_dispatch_submission_stops_without_terminal_record` と
  `test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable[malformed]` / `[missing]`、いずれも `assert 0 == 2`)。
  本 wave の差分 (`tools/dev_wave_land.py` と `orchestrator/tests/test_dev_wave_land.py`) はこの試験から import で到達せず、取り込んだ main 側の tools / orchestrator の差分は 0。
  同じ tip で同 file を単独再走すると 148 passed / 赤 0 だった。同じ試験群は同日の第 29 回 /rulings の受入 final-1 でも 1 件赤になっている (同日 2 wave 目)。
  揺れの機序は確かめていない。本項を含む tip で取り直した受入の緑は land の記録と受領証が持つ。
- 工数: Codex 子 = author 1 本 (4 分) + review 2 本 (上限で即死、出力 0)。Claude 子 = review 2 本 (各 10〜12 分)。親の計算ノード走行 = 焦点走 1 + 変異 probe 1 + 変異 final 1 + 全史 provenance 監査 1。

## 次の一手差分

### 完了

- [T-2833] `_registered_worktree_paths` の strict resolve を `InterruptedError` のときだけ 1 path あたり最大 5 回 (sleep なし) 呼び直す実装を land した (Codex author、commit `2a29a2381`)。
  他の経路・rc 分類・watchdog は不変。効果は未実測で、使い切れば同じ文言の rc=31 が残る (F672 の再発検知と復旧はそのまま)。
  remaining: none
  base: 5fa44273627ba0c5864e718b598fa13337cfae46968e9f8e6f98edb39becb5e9
