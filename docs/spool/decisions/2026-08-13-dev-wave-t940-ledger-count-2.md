---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t940-ledger-count
seq: 2
---

## {{D:ledger-count-dynamic}}. 台帳件数の pin は絶対値でなく期待表の長さで書く

**決定:** 既知違反台帳 (`KNOWN_PROVENANCE_VIOLATIONS`) の件数を検査する assert は、絶対値の
literal ではなく、同じテスト内の期待表または台帳自身から導いた長さで書く。具体的には
`len(台帳) == len(expected)`、`len({row[0] for row in expected}) == len(expected)`、
`len(registry) == len(台帳)` の 3 形とする。承認済み entry の追加で更新が要るのは期待表だけになり、
検出力は絶対値 literal と入力ごとに同一に保たれる。

**理由:**
- 絶対値 literal は「承認された違反が台帳へ入る」という正常な運用のたびに受入を赤にする。
  検出力の本体は entry 内容の完全一致であり、件数の絶対値ではない。
- **件数の検査そのものを削除してはならない。** 内容完全一致 (`observed == expected`) は
  期待表と、台帳を**反復して**作った投影との比較である。この比較は長さの一致を含意するが、
  それは反復が容器の申告する件数と一致する場合に限る。`tuple` 派生型で `len()` は正直に返しつつ
  反復だけを呼び手によって変える容器を置くと、内容 oracle は欺けるが件数 assert は欺けない。
  実測 (in-memory probe) では、件数 assert を削除した形は未承認 entry を 1 件抱えたまま
  内容完全一致・SHA 一意性・registry の件数と値 tuple・実在 commit 検査のすべてを緑で通った。
- 動的な形はこの検出を保ったまま絶対値を消す。両立するので、どちらかを諦める必要はない。

**却下した選択肢:**
- 件数 assert の削除 — 上記のとおり検出力の純減であり、受理集合を承認済み entry の件数変化を
  超えて広げる。
- 容器・spec・全 field の exact type 固定 (`type(...) is tuple` 等) — 動的な件数検査が同じ攻撃を
  型検査なしで捕まえるため、本件では不要。型検査でしか捕まらない形 (件数が同じまま `str` 派生型で
  SHA をすり替える) は件数 literal を持つ形でも捕まっていない別の穴であり、別途起票する。
- 台帳の内容一致検査を「期待表の部分集合であること」へ緩める形 — 未承認 entry の混入を
  受理してしまう。正しさゲートの受理集合を広げてよいのは承認済み entry の件数変化だけである。
