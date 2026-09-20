---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2344-closure-stage
seq: 2
---

## {{D:closure-stage-by-import-layer}}. enforcement source closure の段階実装は現行 tuple の直接 import 先 1 段ずつ進め、tuple を動かす変更単位に同 grammar の歴史収載を含める

**決定 (D1884 の段階実装の次段、実装 wave の裁定):** 収載 tuple を推移閉包へ向けて進める単位は、
**現行 tuple の各 member が直接 import する module とその package 初期化 (probe の 1 段目)** とする。
本段では 2026-09-20 の着手 commit で数えた 22 本を末尾に path の sorted 順で足し exact 63 → 85 にした。
既存の宣言順は動かさない (epoch preimage は宣言順)。tuple を動かす変更単位には、**直前の grammar を
歴史閲覧限定 decoder へ収載する変更 (独立 ordered literal・兄弟 validator・grammar 固有の scope 定数)** を
同じ commit に含める。収載条件は D1653 のとおり実在 corpus の確認で、exact-63 は記録済み lock 20 本の
wire key 列と記録 commit 9 件の宣言順を exact 照合して満たした。scope 文言は D2081 の形式で、
発見集合は「測定 commit の source 木で本版の tuple を起点に辿った集合」として日付・commit・数値を書き、
収載の内訳は書かない。

**理由:**
- 1 段目は probe (`ast.walk` + package 初期化、D1650 と同規則) で機械的に再現でき、判断の余地が無い。
  今回の 22 本は T-2344 一次資料が挙げた 1 段目の drift 2 本と、認証受理 API で関数本体まで実行された
  未収載 4 本のうち 2 本を含む。
- exact-62 のときは歴史収載が別 wave (8 日後) になり、その間 3 本の記録済み lock が両経路から読めなかった。
  同じ穴を tuple の前進ごとに再発させない。
- 発見集合は tuple が不変でも動く (09-09 の 140 → 09-16 の 162 → 09-20 の 163)。日付・commit 付きの
  数値だけが将来も偽にならない。「85 / 163 / 78 を着手 commit の実測」と書くと、着手時点の tuple は
  63 なので偽になる — 本版の tuple を起点に同じ source 木で再測した値であることを文言に書く。

**却下した選択肢:**
- 1 段目の drift 2 本だけ足す — 推移閉包へ「1 段」進んだとは言えない (T-733 の名乗りの回復に留まる)。
- 発行器 6 本 (+ 発行器起点にだけ居る 10 本) を先に足す — D1884 の目標内で、発行器自身の穴には
  より直接効くが、本段の規則 (tuple 起点の閉包を層ごとに閉じる) と混ぜると再現規則が二重になる。
  次段の順序は裁定パッケージへ返す。
- 一度に発行器起点を含む和 (173) へ広げる — D1884 が却下済み。
- 歴史収載を後続 wave に回す — exact-62 の再発になる。
- 通常 decoder を exact-63 との union にする — D1653 が禁じる (certified の受理集合を広げない)。

**保証しない範囲 (記録):** 「certified 経路が source-bound である」を推移閉包の意味では引き続き
名乗らない (tuple 起点の未収載 78、発行器起点との和で 88 が残る)。tuple の前進により、記録済み exact-63
campaign は tuple 前進後の checkout の certified consumer では decode 段で拒否され、歴史閲覧でだけ読める
(D1653 / D1770 の帰結)。最新 consumer での certified 再解析を続けるかは別途諮る。
