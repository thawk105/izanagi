---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t471-restore-bound
seq: 2
---

## 新規

### {{F:fix-prompt-existing-test-ambiguity}}. fix prompt の「既存テスト」が同 wave の未 land テストを含んで読め、fix 1 巡が編集ゼロで空振りした [手順漏れ] [コンテキスト浪費]

- 事象: [T-471] 段 6 の fix 子が、指示された 14 所見のうち 1 件も編集せずに停止した。
  停止理由は「凍結契約が要求する 5 arm を実装すると、既存テストの 4 arm 期待値が必ず赤になる。
  『既存テストの期待値を変更しない』『期待値が誤りなら実装を変えず報告して止める』に従う」。
  当該テストは同じ wave の段 5 が生成した untracked ファイルであった。
- 根本原因: 親の fix prompt が `DW-S06-B` の定型「既存テストの期待値を変更しない」をそのまま
  引き写し、**tracked な land 済みテストと、同 wave が段 5 で作った未 land のテストを
  区別しなかった**。後者は fix の編集対象そのものだが、prompt からは読み取れなかった。
  実装子の挙動自体は正しい fail-closed であり、欠陥は指示側にある。
- 恒久対応: memory `fix-prompt-scope-tracked-tests` — fix prompt では「既存」を tracked に限定し、
  同 wave の未 land テストは編集対象だと併記する。混在時は権威順序も書く。
  **同じ規則を `DW-S06-B` 本文へ入れる案は dev-wave docs の hard ceiling (25200 bytes) に
  収まらず、予算を上げないため裁定へ返した** (段 8 の予算契約どおり縮約でも収まらなかった)。
- 再発検知: 段 6 の fix 子が編集ゼロで停止したら、まず prompt の権限境界文を疑う。
  対応表が全件 `partial` かつ「実装した内容: 編集は行っていません」なら本型である。
