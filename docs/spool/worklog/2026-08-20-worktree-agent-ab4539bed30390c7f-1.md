---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-agent-ab4539bed30390c7f
seq: 1
title: [/rulings 自己改善] 索引出力形式を表/ID主体から平易な段落形式へ是正
---

## 本文

- `.claude/commands/rulings.md` の出力節を是正した。「1 行索引 (通し番号・ID・題・出典・推奨順の印)」
  という記述が、ユーザーが本日拒否した表形式・ID 主体の出力を誘発しうる誤解を招く出力規則だったため、
  「索引 (通し番号・状況の短い説明。表にせず ID・出典は文末)」へ変更した。
- 根拠: 本日早い時間の別セッションの `/rulings all` 実行で、ユーザーが表形式・ID 主体の索引出力を
  「説明してよ。分からんって」と明確に拒否した (memory `plain-language-for-user-docs.md` に追補済み)。
- byte 予算 (`.claude/commands/rulings.md` は 5,000 bytes / 180 文字行) 捻出のため、作法節の
  「選択肢と推奨」bullet から重複表現「(そのまま流さない)」を削除した (直前の太字部分と同義)。
  是正後は 4,988 bytes・最長行 123 文字で予算内。
- `docs/skill-self-improvement.md` の rulings 節の発火条件 (誤解を招く出力規則を今回の実行で実測) に
  該当するため、同節の routing に従い rulings 本文を直接是正し軽量 commit にまとめた
  (dev-wave lease・受入全走の対象外)。

## 次の一手差分
