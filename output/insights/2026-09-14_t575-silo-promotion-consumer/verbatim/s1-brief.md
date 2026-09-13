# 親 brief — [T-575] silo 昇格を実行する consumer の同定

worktree (repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t575-silo-promotion-consumer`
基準 commit: `75bea8e5f` (branch `worktree-dev-wave-t575-silo-promotion-consumer`、tree clean、起動 gate rc=0)

## 研究前進

較正の再取得は D176 の bootstrap fuse で止まっており、その解除条件に「契約世代の活性化権限」がある
(D196)。活性化権限は「全入口が最初の書込み前に同じ活性化状態を検査する」要件で定義され、入口集合の
確定がその前提である。本 wave の最小差分は、その入口集合のうち **「silo 昇格」の実在判定を canonical
台帳へ確定し、以後の wave が ability probe を入口と誤認できないようにする**ことである。

## scope

1. 「silo 昇格 (promotion)」を実行する consumer が repo 内に実在するかを、file:line 粒度で確定する。
   列挙は module 名 grep で終えず、helper 経由の間接参照を 2 段辿る。
2. 実在しないと確定した場合に限り、「silo 昇格入口」という語およびそれと**意味的に同値な主張**
   (silo を活性化権限の入口として数える記述、`silo_ladder_rung1.py` を昇格経路と読める記述) を
   使う現行 (非凍結) の全箇所を訂正する。
3. 訂正の対象外: `docs/archive/**` と `output/insights/**` (凍結・append-only の記録)。
   これらでの同語の用法は「未実装と名乗る」という裁定そのものであり、誤りではない。

## 確定済み裁定 (逐語は refs/)

- T-529 択一 6 = 「後者。ability probe を結線して『昇格入口を守った』と報告してはならない」
  (`refs/02-t529-ruling-table.md`)。同 README は「silo は昇格入口として実在しない」とも書く。
- D162 決定 (7) = 「昇格権威として読む consumer は 0 件である」(`refs/06-d162-clause7.md`)。
  ただし対象は `patches/ledger.json` の 3 適格性 field であり、T-529 の 6 入口列挙では
  「適格性」と「silo 昇格」が**別項目**なので、同一命題ではない。両者の関係の確定も本 wave の仕事。
- D196 / D215 = 活性化権限の実装は保留 (`refs/07-d196.md`、`refs/08-d215.md`)。
  本 wave は活性化権限を実装しない。consumer の同定と語の訂正だけを行う。

## 不変条件

- 絶対規律 2 を緩めない。既存の正しさ gate・受理集合を 1 つも広げない。
- 凍結記録 (`docs/archive/**`、`output/insights/**`、`patches/ledger.json`、
  `output/env/pegasus/**`) の bytes を変えない。
- 「不在」は否定命題である。読解ではなく**実測 (検索 argv と rc、file:line)** で示す。
  1 経路でも見落とせば結論が反転するので、探索の閉包条件を明示する。

## 成果物の形

- 判定が「不在」: decisions への 1 D (入口集合からの silo 除外と、その根拠の閉包) と、
  現行 docs の訂正 (あれば)。worklog / spool fragment。
- 判定が「実在」: その file:line と、T-529 の裁定 6 を覆す実測。この場合は段 4 で再裁定する。

## (P1) 親の provisional 裁定 — 攻撃対象

`silo 昇格入口` という語は現行 (非 archive・非 insights) の docs・orchestrator・tools・hooks・src・
patches に 1 件も無い (親が `rg` で実測)。したがって scope 2 の訂正対象は**空**であり、
本 wave の成果物は「不在の canonical な確定」だけになる可能性が高い。これは親の暫定判定であって、
**意味的同値の記述を見落としている可能性**を子は積極的に攻撃せよ。

## DW-G05 成果物影響

放置すると、活性化権限の再開 wave が T-529 の brief と同じく `silo_ladder_rung1.py` を silo 入口と
名指しし、ability probe の writer を結線して「6 入口完了」と報告する。入口被覆率の過大報告が
台帳へ入り、活性化権限の保証が実態より広く読まれる。

## 分割方針

段 2 = plan 子 1 本 (read-only)。段 3 = 敵対 2 レンズ (read-only)。
実装面が出れば段 5 は Codex `role=author` (D95)。docs のみなら親が本文を書く。
