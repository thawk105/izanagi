---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-silo-intra-txn-fix
seq: 2
---

## 新規

### {{F:line-directive-cancels-later-line-shift}}. trace の整形を打ち消す `#line` の前に TRACE=0 の行数を変える修正を入れ、`#line` が修正の行数まで打ち消すことを見落として D297 補助比較の事前登録を外した [手順漏れ]

- 事象: CCBench の F `25898d00` (整形で行数が変わる `#if TRACE` 区間の直後に `#line` を置き、TRACE=0 の行番号を整形前に揃えた commit) の上に、Silo の修正 (update に +3 行) を `#line` を変えずに入れた。pin + 同じ修正 → 修正 tip の D297 比較を pass と事前登録したが、GCC 11・12 とも `header expanded 不一致` で拒否された。親の probe (Silo の 1 file・TRACE=0・1 文脈) で見た差は `ERR` の `__LINE__` 定数 (pin + 修正 693、修正 tip 690) の 1 行 (検査器は最初の不一致で止まるので他の entry は未確認)。段 3 の相談も親の段 4 裁定も「`#line` を変えなければ ERR の値が F と同じで安全」と読んでいた。
- 根本原因: `#line` は固定値で行番号を戻すので、後から入る TRACE=0 側の行数変化も打ち消す。その帰結を「trace 無し + 修正」との比較の側から検討しなかった。
- 恒久対応: memory `line-directive-cancels-later-trace0-changes` (izanagi branch の CCBench に TRACE=0 の行数を変える commit を入れるときは、後ろの `#line` を動かすかを段 1 で決め、比較の期待をその決定から導く。行番号の予測 probe の所在つき)。
- 再発検知: D297 の header 分岐 (include を展開した比較) が `ERR` の定数差で拒否する。本件もそれで検出した (`output/insights/2026-09-29/silo-intra-txn-fix/README.md` §3)。
