---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2409-wal-verdict-bind
seq: 3
---

## 再発

### F39

- **再発: 2026-09-08** — [T-2409] wave の段 6 で、production へ 10 行足したことにより
  `test_ccbench_spawn_sites.py` の deferred-gate 登録簿が pin する build sink の行番号が
  4051 から 4061 へずれ、既存 3 node が赤になった。**F39 が既に「production の行数を変える wave では、
  位置を台帳に持つ test も pin 閉包と焦点走の対象に入れる」と恒久対応を書いていたにもかかわらず、
  段 1 の pin 閉包で同じ誤りを繰り返した** — whole-file sha256 pin は path 検索で探したが、
  行番号 pin を探していない。
- **この再発が足す事実は「恒久対応の置き場所」である。** F39 の運用ルールは failures 台帳にしか
  書かれておらず、段 1 の pin 閉包で実際に読まれる節 (`docs/dev-wave/operations.md` の `DW-O09`) は
  行番号 pin に一言も触れていない。**読まれない場所にある恒久対応は守られない。**
- **統合を試みたが単節予算に入らず、差し戻した。** `DW-O09` は 992 bytes で単節予算 1000 bytes に
  対し残り 8 bytes しかなく、1 文 (約 220 bytes) を足すと 1205 bytes で `tools/check_docs.py` が
  赤になる。既存文を 205 bytes 削れば入るが、それは安全義務の削除・弱化に当たるため行わなかった。
  予算の変更は段 8 が実装せず裁定パッケージへ送る事項なので、{{T:pin-closure-lineno-budget}} として返す。
- 検出は着地前で実害ゼロ。拾ったのは `DW-O26` の consumer 拡張焦点走 (参照関係で引いた 6 file) で、
  段 6 の敵対レビューも独立に同じものを検出した。**変更 file だけの焦点走なら取り逃していた。**
  挿入点より上にあるもう 1 つの pin (`_build_binary`) は動かず、赤にも出ていない。
