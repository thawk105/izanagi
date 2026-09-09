---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2369-stale-carry
seq: 2
---

## 再発

### F428

- **再発: 2026-09-09** — 既存 3 例はいずれも**別 ID・別 wave**の成果が carry の実体を満たした型
  だったのに対し、本件は **carry を閉じ損ねたのが、その作業を実装した wave 自身**である点が新しい。
  [T-2369] (D1699、B-4 対照対 driver を候補と参照の 1 session 形へ直す) は 2026-09-08 のエントリ 1327
  (branch `worktree-dev-wave-b4-paired-session-driver`) が実装して land したが、同エントリの
  次の一手差分は [T-2369] を carry stub のまま残し 完了 にしなかった。以後の fold が保存則どおり
  毎回運び、1403〜1408 まで持ち越された結果、2026-09-09 に「残るのは driver の設計と実装である」
  という依頼で本 wave が起動した。着手前実測 (`DW-S01` の裁定前提実測) が段 1 で覆し、実害は
  実装子を 1 本も起動しないまま docs-only の終端記録へ切り替えたことで止まった。
  **本件は既存の恒久対応が挙げる「ID 単位で closing commit との対応を機械検査する lint」が
  最も安く効く型である** — エントリ 1327 の題と実装 commit `003ef6173` の件名は、どちらも
  carry 本文の逐語 (「対照対 driver を、candidate と reference を 1 つの低水準 session で測る形へ直し、
  reference の個数と D の式を実走前に凍結する」) とほぼ一致しており、別 ID を辿る必要がない。
  同一 fragment 内で「本文が閉じたと書いている作業の ID が、同じ fragment の 完了 節に無い」を
  見るだけで検出できる。lint は未実装のままなので、局所修復として本 wave が [T-2369] を 完了 にした。
