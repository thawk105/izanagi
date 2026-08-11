---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t756-fn2-trace-v2
seq: 2
---

## {{D:trace-v2-in-editable-surface}}. trace 形式 v2 は編集面内 (silo の transaction.cc) で完結させ、共有 helper を二重権威にしない

**決定:** committed txn の記録形式を v2 (C 行に read/write 件数、txn 終端に `E <txid>`) へ上げる
変更は、`external/ccbench/cc/silo/transaction.cc` の中だけで行う。`include/trace.hh` は変更しない。
その際、**helper `izanagi_trace::emit_commit` の呼び出しは残置せず置換する**。helper 自体は SI が
使い続けるので削除しない。終端マーカーは entry / retention の lock 被覆検査 (X 行) をすべて
出し切った後 (`clear_shadow()` の直後) に置く。

**理由:**
- `hooks/guard_write.py` の `EVOLVE_BLOCK_SOURCES` が CCBench の編集面を `include/backoff.hh` と
  `cc/silo/transaction.cc` に限定している。D41 で同じ壁に対する scratch copy + `git apply` の迂回が
  「hook のブロック回避」として却下され、transaction.cc 内で既存 `stream()` を直接呼ぶ設計へ
  変更した先例がある。同じ扱いを継承する。
- **helper を残したまま v2 行を追加すると、同一 txn に v1 と v2 の C が 2 本出る。** parser は
  同一 txid の 2 度目の C を `dup_txids` に積み、当該 variant の判定を indeterminate に倒す。
  C tag の schema 権威を 1 つに保つには置換しかない。
- 終端マーカーを R/W ループ直後に置くと、その後の X 行が末尾切断されても「完結」と誤認する。
  X をすべて出し切った後に置けば、write loop 途中の停止も終端欠落として捕まる。

**却下した選択肢:**
- **trace.hh の `emit_commit` を v2 化する** — 編集面外で hook が機械拒否する。迂回は D41 が却下済み。
- **版行 (`V 2`) をファイル先頭に置く** — thread ごとの stream 初期化点は trace.hh にあり編集面外。
  C 行の token 数 (5 か 7) で判別すれば版行は要らず、末尾切断で終端が失われても先頭の C だけで判別できる。
- **SI (`cc/si/transaction.cc`) も同時に v2 化する** — 編集面外。SI が v1 のまま残るため、
  後続の「v1 拒否」を protocol 無差別に適用してはならない (裁定へ返す)。

**この決定が閉じないもの (正直に):** 件数は R/W 行と同じコンテナから取るため**独立 witness ではない**。
write set から要素が消えれば件数も W 行も同時に減り、v2 では検出できない。そこは write-intent shadow
(独立 witness、別 pin として承認済み・未統合) の領分である。X 行の中間欠落、内容の置換、
実行の完了 (W 行は実データ更新より前に出る) も閉じない。

## {{D:trace0-preprocess-identity-gate}}. pin 前進時の規律 1 は「TRACE=0 正規化 preprocess 出力 + include 活性」の同一性で検査し、翻訳単位の同一性を名乗らない

**決定:** CCBench の pin を前進させるとき、旧 pin と新 pin の間で **TRACE=0 の正規化 preprocess 出力**と
**include 活性**が一致することを、独立の checker (`tools/check_trace0_preprocess_identity.py`) で
fail-closed に検査する。保証の名前は「翻訳単位の同一性」ではなく
「選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性」
とする。差分列挙は `git diff-tree --raw -r` で行い、header を含む差分は拒否する。

**理由:**
- 既存の `source_digest.assert_trace_diff_matches_head` は**同一 pin 内**の TRACE=1/TRACE=0 差を
  比べる。pin 自体が動くと baseline も一緒に動くので、**新 pin の trace-hook 変更そのものは
  検査されない**。pin 前進の場面ではこれが最後の防壁になる。
- **include 行の文字列比較だけでは条件付き include の偽緑を塞げない。** 必須 include を新側だけ
  `#if TRACE` の内側へ移すと、include 行集合は同一・include 除去後の preprocess 出力も同一なのに、
  実 TRACE=0 ビルドでは header が入らず翻訳単位が変わる。preprocess の前に各 include 行を一意な
  marker 識別子へ置換すれば、条件枝へ移した include は marker ごと消えて差分に現れる。
- **header の変更は保証範囲外である。** `-E -P` は `#define` 行を出力に残さないので header 内の
  マクロ定義変更が正規化出力から消え、header 単体の preprocess は consumer TU を代表しない。
  受理するより fail-closed で拒否する方が正直である。
- **比較 0 件の緑を作らない。** context 集合が空、または実際に積んだ件数が期待数と一致しない場合は
  拒否する。前者だけを塞いだ実装は、後者を無効化する変異が生存することで露見した。
- compiler builtin を保持したまま preprocess するため結果は compiler 依存である。したがって
  **複数の compiler で走らせ、admission toolchain と同一であるとは主張しない**。

**却下した選択肢:**
- **`compute()` / `assert_trace_diff_matches_head` を流用する** — working tree と固定の編集面集合を
  読むため 2 commit 比較に使えず、pin 前進の検査にならない。
- **nm の名前ベース検査 (`_has_trace_symbols`) に寄せる** — strip や無名データ構造の漏れを
  証明できない。実 perf build の補助防壁として残し、この checker には組み込まない。
- **差分 path を 1 ファイルに固定した専用 checker にする** — どの path もスキップしないという
  一般性の方が強い。呼び出し側が範囲を固定したい場合のために `--expect-paths` を任意引数で持たせる。
