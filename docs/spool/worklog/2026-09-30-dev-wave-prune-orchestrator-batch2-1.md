---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-prune-orchestrator-batch2
seq: 1
title: 不要コードの整理 第 2 束 — 使われていない提出 gate と一回限りの分析の候補 9 群 (19 file) を D1989・D2179 で現物照合し、削除 0 と判定した (insight のみ、branch worktree-dev-wave-prune-orchestrator-batch2)
---

## 本文

- 依頼: 並行 wave 共通指示 speedup-2026-09-29 の md_4 (ユーザー依頼「不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいように」)。md_3 (prune-tools-batch1) の land 後に着手。候補別の判定と根拠は一次資料 `output/insights/2026-09-30/prune-orchestrator-batch2/README.md` §2。
- 結果: 削除 0。台帳・allowlist・spawn 表・地図・墓標・所要台帳は変更なし。依頼の「submission_gate 系 test 約 790 秒」は所要台帳で 222 node・788.8 worker 秒と一致したが縮まない。md の候補一覧 (「tests 以外から import 0」の機械集計) は 2026-09-20 の T-2800 の判定、事前登録の契約、live test の照合先、runbook 手順を反映していなかった。
- 棄却・訂正: 段 1 brief の件数「12 module」は段 2 の指摘で 9 群・19 file に訂正。記録レビュー (NO-GO) の must-fix 2 件を commit 前に直した — nonmonotonicity は D1989 上は歴史的言及しか持たず D2179 条件 1 の不成立で残す、sweep_report の根拠は `docs/orchestrator-design.md` §材料レポート (本 module を名指ししない) ではなく共有 test の import と `docs/phase2.md:184`。
- 段構成: 軽量版。段 2 Codex (read-only、「残しすぎ」「消しすぎ」の両方向) が親の見立て (削除 0) を支持。段 4 で「実装しない」と裁定し 4→7→8→9。段 3 は実装面ゼロ・受理集合不変で DW-C00 の必須条件が不成立のため省略。事実を再抽出した docs-only なので記録に独立 read-only レビュー 1 本。変異 matrix は実装差分ゼロで免除。受入は D2316 の縮小受入を予定したが、`tools/scoped_acceptance.py plan` (tested main 4f412c67b、記録 commit 7f51d0e91) が不適格と判定したので受入全走にした。不適格の理由は 8 件とも `production-reference:<insight の verbatim/ 配下の file>:orchestrator/campaign/condition_meaning_gate.py` で、同 file `:22` の docstring の英単語 "verbatim" が dir 名の鍵 `verbatim` と部分一致したもの。D2316 決定 3 の鍵は汎用名 README.md・index.md だけを除くので、`verbatim/` を持つ insight (tracked で 1,112 file) を書く wave は、production code にこの語がある限り縮小受入に入れない。安全側の過大除外で正しさの問題ではないが、縮小受入の効果が大きく減る。
- セッション異常: submodule 初期化 tool の 1 回目が `update-no-fetch` (既知の tool 内 30 秒上限型)、同じ引数の再走で rc=0。候補 hash の検索を needle ごとの `git grep` 76 回で始めて 1 回 30 秒前後かかり、`-e` を並べた 1 回走査へ切り替えた。記録レビューの待ち手を誤って 2 本張り、後の 1 本を止めた。
- 工数: Codex gpt-6-sol / medium 2 本 (段 2 plan 1・記録レビュー 1)。

## 次の一手差分

### 新規

- {{T:scoped-acceptance-verbatim-key}} **P2・新規**: 縮小受入 (D2316) の分類で、insight の `verbatim/` dir 名が production code の英単語 "verbatim" (`orchestrator/campaign/condition_meaning_gate.py:22` の docstring) と部分一致し、`verbatim/` を持つ insight を書く wave がすべて不適格になる (2026-09-30 prune-orchestrator-batch2 で実測、理由 8 件とも同型)。`verbatim` を README.md・index.md と同じ汎用名に加えるかを、D2316 決定 3 (受理集合の変更) として諮る。材料 = 本エントリと `output/insights/2026-09-30/prune-orchestrator-batch2/verbatim/scoped-plan.json` (`tools/scoped_acceptance.py plan` の出力)。
