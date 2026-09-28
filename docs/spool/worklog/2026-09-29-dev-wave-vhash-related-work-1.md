---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-related-work
seq: 1
title: VHash 論文の文献調査と新規性の位置づけ — 出典メモの文献要約を原典で照合し、本案 4 点を既知と未確定に分けた (insight のみ、branch worktree-dev-wave-vhash-related-work)
---

## 本文

- 依頼: ユーザー依頼で親セッションが用意した投げ文 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_1.txt` と `common.txt`)。
  着手時、対象 item も `docs/paper-story-vhash/` も local main に未着地で、同じ中身の複製 (docs-snapshot) を読んだ。
  ユーザー就寝中のため判断は自分で行うよう、並行セッションの監督役から 2026-09-29 に連絡があった (ユーザーへの問い合わせは 0 件)。
- 成果物と結論: `output/insights/2026-09-29/vhash-related-work/README.md` (§0 が要約、§8 が 3 分類)。
- 検索の経緯: 事前登録した DBLP 12 本は全て HTTP 200 の bot 判定 HTML を返したため、結果を判定せず走行無効とし、
  OpenAlex の題名検索へ切り替えた ({{F:dblp-bot-challenge-http200}})。
- 段 6 の read-only レビュー (codex 1 本) は NO-GO で所見 5 件 (must-fix 1・should-fix 3・nit 1)。全件 real と裁定して親が直した。
  must-fix は Morty の「前進の結果を truncation 境界に使う」という誤読 (版順序は開始時に固定)。should-fix の 1 件で、
  起草時に「言われていないと主張できる」に置いた 1 項目を、検索式と主張の対応を結果を見てから選んでいたこと、および
  要裁定 1 件を題名だけで範囲外にしていたことを理由に未確定へ移した。
- 焦点再レビュー (codex 1 本) は前回 5 件を全て closed とし、新規 2 件 (未取得候補の数え方が行数か文献数か曖昧・
  Morty の読んだ節に §4.1 が抜けている) を出した。どちらも記録の修正で、親が直して grep で確かめて閉じた (3 巡目は起動していない)。
- 工数: 原典を読む子 5 本 (Claude sonnet、並行)、段 6 のレビュー 1 本と焦点再レビュー 1 本 (codex、各 5 分未満)。計算ノードは使っていない。

## 次の一手差分

### 新規

- {{T:vhash-related-work-open}} **P2・VHash 論文の文献調査と新規性の位置づけ (残件)**: 本 wave の insight
  (`output/insights/2026-09-29/vhash-related-work/README.md` §8.3) の未確定 U0〜U4 を確定させる。
  本文を取得できなかった候補 (§11.2 の 7 行、文献としては 8 本) を図書館経由で読み、検索式と主張の対応を先に固定した登録母集合検索
  (`docs/related-work/README.md` 7.7.4 の RW3) を行う。Lomet 2012 と本案の差を関連研究節の文に書き分けるのは次の版の wave の担当。
