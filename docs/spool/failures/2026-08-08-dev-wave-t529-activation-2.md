---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t529-activation
seq: 2
---

## 新規

### {{F:grep-r-misses-tracked-hit}}. pin 閉包の `grep -r` が tracked hit を黙って 1 件落とした [手順漏れ]

- 事象: 段 1 の pin 閉包で pegasus g1 の contract hash を repo root から
  `grep -rl "<hash>" --exclude-dir=.git --exclude-dir=archive --exclude-dir=insights
  --exclude-dir=external .` で検索し、tracked file 4 件を得て brief に書いた。
  段 3 レンズ A が 5 件目 (`output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/
  raw-bundle-attempt-1/gap-result-receipt.json`) を指摘した。
- 根本原因: 同じ hash・同じ除外 flag でも、検索起点を `.` にすると当該 file を落とし、
  起点を `output` / `output/env` にすると拾う。`git grep -l` も拾う。本 worktree で再現する
  (`grep` は GNU grep、file は 96560 bytes の通常 JSON、symlink でも権限差でもない)。
  原因は特定できていないが、**起点 `.` の再帰検索が silent に取りこぼす**ことは実測した。
  `DW-O09` は「path の hit 0 件を pin なしと結論しない」までしか定めておらず、
  検索コマンド自身の取りこぼしは射程外だった。
- 恒久対応: 未実施。`DW-O09` へ「tracked の閉包は `git grep` を authority とする」の 1 行を
  入れたいが、`docs/dev-wave/**` の合計予算に空きが 15 bytes しかなく入らない。
  {{T:dev-wave-budget-for-grep-authority}} としてユーザー裁定へ返す。
  それまでの暫定は memory の「着手前に main を確認する」等と同じ prompt 規律とする。
- 再発検知: pin 件数を 2 種類の検索 (`git grep -l` と部分木起点の `grep -rl`) で突き合わせ、
  食い違えば brief を書かない。

## 再発

### F112

- **再発: 2026-08-08** — [T-529] の fix 第 1 巡。親が scope 除外を「入口 gate を作らない」の
  つもりで書いたが、実際の文が「oracle driver へ receipt を配線しない」と file 単位で読め、
  必須引数を満たすための caller 配線まで禁じたことになっていた。子は矛盾を検出して
  1 行も書かずに fail-closed し、必要な配線の一覧だけを返した。親が境界を再裁定して再投入。
  F112 (未 land テストの範囲が曖昧) と同型で、**scope 記述の曖昧さが fix 1 巡を空振りさせる**
  独立 2 例目。`DW-S06-B` へ「scope 除外は file でなく禁じる挙動で書く」を入れたいが
  予算に空きがなく、{{T:dev-wave-budget-for-grep-authority}} と同じ裁定へ束ねる。
