---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2374-a1-pilot-next-attempt
seq: 3
---

## 再発

### F428

- **再発: 2026-09-14** — 基本型 (別 ID・別 wave の成果が carry の実体を満たす) と同型だが、
  **実体を満たした wave は自分の ID を正しく完了にしており、閉じ損ねたのは同じ作業を指す別 ID の
  carry である**点が新しい。[T-2374] の carry (エントリ 1304、2026-09-07) は「A-1 pilot の
  attempt-0002 を fresh wave で投入する」と書き、以後 bare pointer のまま 7 世代運ばれた。実体は
  [T-2397] が 2026-09-11 に attempt-0004 として実施し、3 workload とも valid で完走して sizing 入力を
  生成し、T-2397 自身は完了として閉じられている。2026-09-14 に carry 本文を写した依頼で P1 の wave が
  起動した。着手前実測 (`DW-S01` の裁定前提実測) が段 1 で覆し、実害は実装子を 1 本も起動しないまま
  docs-only の終端記録へ切り替えたことで止まった。**2026-09-09 の再発が「最も安く効く」と挙げた
  lint — 同一 fragment 内で、本文が閉じたと書いている作業の ID が同じ fragment の 完了 節に無いことを
  見る検査 — は本件を検出しない。** T-2397 の fragment は自分の ID を完了にしており、fragment 内に
  食い違いが無いからである。同じ作業が 2 つの ID に分かれている形は、ID 単位の closing commit 対応では
  なく、carry 本文どうしの重複か、carry が名指す成果物 path の実在で見るしかない。局所修復として、
  本 wave が [T-2374] を 完了 にした。
