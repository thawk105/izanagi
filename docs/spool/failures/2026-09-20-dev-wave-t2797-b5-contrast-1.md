---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2797-b5-contrast
seq: 1
---

## 再発

### F28

- **再発: 2026-09-21** — [T-2797] wave で、変異の期待 node を `DW-M07` の probe 経路で**実測して**登録したが、
  probe を走らせた統合 commit 4 の後に fix3 (commit 5) が test 1 本 (`test_b5_string_preflight_rejection_uses_wal_and_rc0`) を足し、
  fix 最終 commit で期待 node を再検証せずに final を走らせたため、M10 / M11 の観測が期待の上位集合 (差は当該 test 1 本) になり
  **MISMATCH 2 件**を出した (変異は 2 件とも rc=1 で殺されており、無効なのは期待集合)。型は F28 の「事前登録を実測でなく設計から書いた」
  の新しい顕在化で、**実測はしたが fix 前の commit の実測で、fix 後には古くなっていた** (2026-08-16 の対応表転記、2026-08-25 の子の自己申告に続く
  第 3 の転記元 = 古い probe)。`DW-M07` の「本走前に fix 最終 commit で old 逐語 anchor・期待 node を再検証」を anchor だけ (`--plan-only`) で済ませ、
  期待 node の再検証を省いたのが直接原因。`DW-M08` に従い初回結果を消さず erratum を残し、final 走の観測を完全集合として再登録して
  final2 (2 件) を再走し KILLED (期待 = 観測) で閉じた。恒久対応は変更なし (`DW-M07` の再検証は anchor と期待 node の両方を対象にする、
  という既存文のとおり) — 手順として「fix commit が test を足したら、その test file を含む probe を fix 最終 commit で再走してから final」を
  親の memory へ置く。
