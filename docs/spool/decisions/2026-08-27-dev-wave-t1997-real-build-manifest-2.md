---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1997-real-build-manifest
seq: 2
---

## {{D:empty-cache-entry-is-unset}}. FetchContent の空値 cache entry は未設定として読む

**決定:** `CMakeCache.txt` の `FETCHCONTENT_SOURCE_DIR_MASSTREE` について、
**値が exact 空文字の行は「未設定」と同一視**し、`<FETCHCONTENT_BASE_DIR>/masstree-src` へ
落とす。空でない値は従来どおり NUL なし絶対 path を要求し、D786 の
A (cache 入力) = B (`DependInfo.cmake` の実効解決) = expected (呼び手の staged base) の
三者一致も 1 つも弱めない。緩和は次の連言にちょうど限る。

```
SOURCE_DIR がちょうど 1 行
AND その値が exact 空文字
AND BASE_DIR がちょうど 1 行の NUL なし絶対 path
AND 既存の全形式検査と A = B = expected を通る
```

`.strip()` や引用符の除去はしない。空白だけの値、引用符付きの空文字、相対 path、NUL 入り、
重複行はすべて従来どおり拒否する。実装は `matches` から空値行を削除せず、
選択の瞬間だけ未設定と同一視する — 重複行検査を空値行にも効かせ続けるためである。

判定を条件付き (宣言記述子の有無で有効化する opt-in) にはしない。

**理由:**

- CMake は `FetchContent_Declare` の時点で `FETCHCONTENT_SOURCE_DIR_<UPPER>` を
  **空値の cache PATH entry として必ず作る**。CCBench (pin
  `511c9538e4e8efa54b45cda62e72389ed3b706ec`) の `cmake/ThirdParty.cmake` は
  `FetchContent_Declare(masstree ...)` を使うため、実 `CMakeCache.txt` には当該行が常に 1 行在る。
  計算ノード (CMake 3.25.0) とログインノード (CMake 3.22.1) の実 build で同じ形を実測した。
- 旧実装は当該**行の存在**だけを「指定あり」の条件にしていたため、値が空でも SOURCE_DIR 分岐へ入り、
  直後の絶対 path 検査で必ず落ちた。`<FETCHCONTENT_BASE_DIR>/masstree-src` を使う分岐は
  「行が無い」ときだけ到達するので、実物では**構造的に到達不能**だった。
  依存受け渡しの既定 regime (base-only) の全 cell が build 段で拒否される。
- D786 の本文は A を「`FETCHCONTENT_SOURCE_DIR_MASSTREE`、**無ければ**
  `<FETCHCONTENT_BASE_DIR>/masstree-src`」と定めている。空値を「無い」と読むのが規範に忠実である。
  旧実装が固定していたのは D786 ではなく実装の読み違いだった。
- 条件付き opt-in を採らないのは、否定側の枝に**実在する呼び手が無い**からである。
  当該 helper は依存 receipt がある呼び出しでだけ発火し、その production 呼び手は
  floor campaign の 1 箇所だけで、同じ呼び出しが宣言記述子を全 cell へ無条件に渡している。
  負の枝が production で一度も通らない分岐は機構ではなく装飾であり、しかもその唯一の存在理由は
  「実物について事実として誤っているテストを緑のまま残すこと」になる。
- D1134 の「宣言記述子が渡らなければ変更前と厳密に同じ挙動を保つ」は、D1134 が新設する
  関門の発火条件を述べた文である。`build_v2` 内部の無関係な parser の是正まで永久に凍結する
  条項として読むと、当該関数の一切の bugfix が禁じられる。D1134 の理由節はその読みを支持しない。

**却下した選択肢:**

- **宣言記述子ありの経路だけで空値 fallback を有効化する** — 上記のとおり負の枝に呼び手が無い。
  既存テストを無編集で残せるという利点は、そのテストの期待が実物について誤っている以上、利点でない。
- **`.strip()` で空白も空とみなす** — 受理集合を実測していない形へ広げる。実 CMake は
  exact 空文字しか書かない。
- **BASE_DIR と B だけから root を導く** — A の独立性が消え、D786 が閉じた通常変数 shadow の
  検出が効かなくなる。
- **cache の空値行を読み取り前に削除する** — 生成された証跡を後処理で改変することになる。
- **configure に SOURCE_DIR を強制して非空化する** — base-only を source-dir regime へ変え、
  argv・transport mode・cache identity の意味を変える。是正 1 点より変更面が大きい。

## {{D:mock-shape-must-come-from-the-tool}}. 生成物を parse する述語の正例は、道具の実出力から作る

**決定:** 外部の道具 (CMake、compiler、scheduler 等) が生成した file を parse する述語について、
**正例 fixture は実行した道具の出力から作る**。実装がどう読むかという理解から書いてはならない。
実出力を採れない場合は、fixture の作成根拠 (どの版のどの道具のどの実行から取ったか) を
テストの近傍へ書き、採れていない事実を明記する。

この規律は既存の `DW-O13` (field の実在では足りない。実環境で取りうる**値**を実測する) の
正例側の対称義務であり、負例だけでなく**正例も実出力から作る**ことを求める。

**理由:**

- 実測で、同一の述語が 2 度続けて実物と食い違った。1 度目は実 CMake が書かない key を要求し、
  2 度目はその是正で導入した分岐が、実 CMake が必ず書く空値行のせいで到達不能になっていた。
  どちらも fixture が実出力ではなく実装の読みから書かれていたため、テストは食い違いを検出できなかった。
- 2 度目の事故では、fixture が実物と**逆向きに**固まっていた。実 CMake が必ず出す形を
  「拒否せよ」と固定した負例が在り、実 CMake が決して出さない形を正例に据えていた。
  この向きの誤りは、負例だけを実測しても見つからない。
- 実出力から作った fixture は、道具の版が上がって形が変わったときに CI で落ちる。
  実装の読みから作った fixture は、その場合も緑のまま本走だけが落ちる。

**却下した選択肢:**

- **静的レビューで代替する** — 敵対レビュー 2 本と 4 本が、2 度の事故のいずれも指摘しなかった。
  レビューは実装と fixture の両方を同じ理解の下で読むため、共通の誤解を検出できない。
- **実出力の逐語をテストへ丸ごと貼る** — 逐語が長い場合に可読性を失い、
  揮発する診断 payload を焼き込む risk がある。必要なのは形の再現であって全文の複製ではない。
