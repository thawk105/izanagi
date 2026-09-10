単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg

必読事項の射影: 以下はすべて絶対パスである。**読めなければ即停止**し、読めなかったパスを出力に書け。

- **レビュー対象 (本体)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md`
- **レビュー対象 (地図の追記)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md`
- 親の段 4 裁定: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/adjudication.md`
- 段 3 レンズ A の所見: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/consult-a.md`
- 段 3 レンズ B の所見: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/consult-b.md`
- 段 2 プラン: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md`
- 親 brief: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/brief.md`
- 逐語 D1813: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1813.md`
- 第 1 段の一次資料: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/CLAUDE.md`
- 先例: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md`

repo path はすべて上記 worktree のものである。親側 repo は読まない。
本体 file は untracked である (まだ commit していない)。作業ツリー上の現物を読め。

## 依頼 — レンズ A「事前登録としての健全性」

[T-2500] の段 6 敵対レビューである。**親の裁定を守らず攻撃せよ。** 本 wave は docs-only で、
成果物は上記 2 file だけである。本走の投入は次 wave。

### 1. 段 3 所見の対応表を必ず作れ

段 3 の 2 レンズが出した所見それぞれについて、**本体文書が実際に閉じたかどうか**を
`closed` / `partial` / `regressed` / `not-addressed` で判定した表を出せ。**表なしで「閉じた」と判定しない。**
根拠は本体文書の節番号と逐語で示せ。親の裁定 (`adjudication.md` の R1〜R14) が
本文に本当に反映されているかを、裁定文ではなく**本文だけを読んで**確かめよ。

### 2. 新しい穴を探せ

とくに次を疑え。

- **恒真化。** 本体の各規則について、それが偽になる具体的な観測を書けるか。書けない条項は恒真である。
  「`indeterminate`」という新しい分類が、都合の悪い結果を吸い込む逃がし道になっていないか。
  「域内非飽和」と「`indeterminate`」の境界が、結果を見てから選べる曖昧さを残していないか。
- **前向き性の限定が正しいか。** §0 の「前向きではないもの」の列挙に漏れがないか。
  本文の他の箇所が、その限定と矛盾する強い言い方をしていないか。
- **規律 2 (正しさゲートを緩めない)。** 本体が本走へ要求する correctness・binary 相異・欠測の強さが、
  先例 (`t2266-tail` / `t2418-explore`) が実際に強制している強さより弱くなっていないか。
  実装の現物 (`orchestrator/campaign/backoff_extended_sweep.py`) を読んで確かめよ。
- **自己矛盾。** 散文 (§1〜§4、§6〜§9) と機械可読 spec (§5) の値・規則が食い違っていないか。
  食い違いは 1 件ずつ、どちらが正しいかの判断つきで挙げよ。
- **主張の過大。** §3 が「主張しない」と書いたことを、他の節が実質的に主張していないか。
- **信頼境界 (CLAUDE.md 規律 6)。** 本体が本走の成果物を受け取る側になったとき、
  汚染された入力が判定を緩められる経路が残っていないか。

### 3. 親の裁定そのものへの攻撃

親は段 3 の指摘を受けて**格子を変更した** (上限アンカーの半オクターブ、8944 の終端二分を廃止、
探索 abscissa の再利用を 9999 だけに縮小)。この変更が新しい欠陥を持ち込んでいないかを見よ。
とくに、探索 3 点のうち 2000 と 4000 が正式格子から外れたことで失われるものがあるか。

## 制約

- 所見は **real / refuted を自分で判定**し、根拠を path と節番号 (または行の逐語) で示せ。
- 成果物 (この事前登録が支配する将来の測定・レポート・台帳) の値・受理集合・参照がどう変わるかを
  1 行で書けない所見は must-fix にせず nit と明記せよ。
- **scope 外の real 所見も報告してよいが、実装を要求するな。**「裁定パッケージ候補」と明記せよ。
- 本 wave は docs-only である。コード・test・gate の新設を要求しない。
- sandbox は read-only である。**pytest 緑を要求しない。静的検査でよい。** 実走していないものを
  「確認済み」と書くな。
- 予算が尽きそうなら途中結論を下記の形式で書いて終われ。無出力が最悪である。
- 出力に結合文字 U+0300〜U+036F を使うな。

## 出力形式

## 段 3 所見の対応表
(所見 ID → closed / partial / regressed / not-addressed → 根拠の節と逐語)

## 所見
(1 件ずつ。`[real|refuted] [must-fix|nit|裁定パッケージ候補] 見出し` → 根拠 → 成果物影響 1 行 → 提案)

## 総括
(3〜8 行)
