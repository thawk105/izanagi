---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-output-pruning
seq: 1
title: output/ の低価値 file の整理、第 1 段 — 参照閉包を全数走査し、保護条件を守って外せた 6 file を git rm して索引 output/PRUNED-INDEX.jsonl を置いた。file 数の大半は束縛された証拠で、次段候補 7,549 file を全部外した tree でも worktree add は同時刻対照の 0.85 倍、git status の短縮は言えなかった (insight + 索引 + README 1 行、branch dev-wave-output-pruning)
---

## 本文

- ユーザー依頼 (2026-09-29、並行 session の git が Lustre の metadata 待ちで詰まった件): 「output/ 配下にある価値の低すぎるファイルは削除した方が良いのでは。例えば『これやってみたけどこうだった』というようなもの、claude / codex から見てその知識はなくても自明と思えるもの、そういうのは掃除しても良い」。依頼 file の保護条件 (sha256 束縛・事前登録・凍結・テストが読む file は外さない) に従った。
- 方針は {{D:output-pruning-policy}}。一次資料は `output/insights/2026-09-29/output-pruning/README.md`。
- 段 3 の 2 レンズ: 「消してよい」側でも上位 40 root に高確信度の B は無く、C (dir 丸ごと) は README を残す規則と両立しないと結論した。「消すと困る」側は A 候補 131 件の確定に反対し、gz 化前の名前での参照 44・変異 spec と台帳 20・正例負例 6 などを示した。親の照合で配置移行前の旧 path による引用と、README が概念で指す証拠 (「本 wave の中心的な証拠」) も見つかり、最終的に 6 file だけを外した。
- セッション異常: `EnterWorktree(name)` が「Could not read the repository git config」で失敗 (既知) → 手動 `git worktree add` (1,070 秒、並行 add 約 20 本・load 47〜54)。走査器は 3 回走らせた (1 回目は merge 経由の root の履歴取得で停止、2 回目は総称 glob・在庫一覧・短い内容の hash で参照軸が飽和)。16:1x〜16:3x に land 調整役からユーザーの push のための git 書込み停止を受け、読み取りだけ続けた。
- 工数: Codex gpt-6-sol / medium 7 本 (author 1・fix 3・測定 harness 1・段 3 相談 2)、Explore (sonnet) 1 本。全量走査 3 回 (各 約 37 分)。

## 次の一手差分

### 新規

- {{T:output-pruning-stage2}} **P3・新規**: output/ 整理の次段。(1) 走査器の穴 (gz 化前の名前、2026-09-10 配置移行前の旧 path、`{a,b}`・`before/after/x` の束表記、保護語の root 名からの波及) を直して再走査する。(2) 一次資料 §4.2 の次段候補 7,549 file (自 root manifest だけの sha256 束縛 2,996・事前登録が dir ごと引く t361-t362 生ログ 3,179・別 insight の probe-ledger が列挙する生出力 1,374) は依頼の保護条件に当たるので、外すかはユーザーの判断による。効果の実測は同 §5 (全部外しても worktree add は 0.85 倍、git status は短縮を言えない。混雑時の短縮量は未測定)。
