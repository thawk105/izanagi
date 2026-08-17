---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1302-r2-nonattrib
seq: 1
---

## {{D:r2-flake-observation}}. flake を別集合で受理し、非帰属経路の runner を main へ束縛する

**決定:** ユーザー裁定 R2 (確率的なフレークで受入全走を何度も無駄にする構造を許さない) を
発効させるため、D371・D389・D393 を次の範囲で部分改訂する。既存 3 決定の本文はそのまま残し、
食い違う部分は本決定を正本とする。

1. **分類。** tested main の単独再走が rc=1 の node は `red_nodeids`、
   tested main と wave tip の単独再走がともに rc=0 の node は `flake_nodeids` へ分ける。
   `attributable` (main 緑・tip 赤) が 1 件でもあれば従来どおり checker rc=1 で停止する。
   verdict 名は `non-attributable-only` のままとし、**2 集合の和が非空**のときだけ成立する。
2. **exact な受理形。** 待ち手が受理する checker receipt の node は 2 形だけとする。
   非帰属は field 集合ちょうど `classification` / `nodeid` / `rerun_rc` で `rerun_rc == 1`、
   flake は field 集合ちょうど `classification` / `main_rerun_rc` / `nodeid` / `rerun_rc` /
   `wave_rerun_rc` で 3 個の rc がすべて 0 とする。2 集合は各々 sorted・unique で互いに素とする。
3. **schema.** outer acceptance receipt を `dev-wave-acceptance-receipt/v4` とし、
   `flake_nodeids` を必須 field にする。**D393 が定めた v3 の schema 値はここで後継する。**
   v3 fallback・互換受理・警告 mode は作らない。発行済み v3 receipt は変換せず、受入を撮り直す。
4. **runner 束縛。** `verdict == "non-attributable-only"` の受領証は、待ち手と land の双方で
   `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` の object type が `blob` で
   あることと blob SHA の等値を要求する。**`flake_nodeids` の値で条件分岐しない。**
   revision は当該走行の tested main / tested tip を使い、現在の `main` や `HEAD` を使わない。
   SHA を receipt field へ書かず、両者とも Git から再計算する。child-green の受理集合は変えない。
5. **checker は変更しない。** `tools/check_acceptance_reds.py` は既に単独再走 rc を `{0,1}` へ
   限定し、3 分類を出している。

**述語ごとの効き方 (恒真ゲートを「守っている」と書かないため):**

| 述語 | 現 producer に対する narrowing | crafted receipt / 将来 drift への防御深度 |
|---|---|---|
| flake node の exact 5 field と 3 rc == 0 | しない (producer が構造的に保証) | する |
| 非帰属 node の `rerun_rc == 1` | しない (同上) | する |
| 2 集合の sorted・unique・互いに素 | しない (producer が sort し 1 node 1 分類) | する |
| 和集合の非空 | しない (checker root が nodes 非空を要求) | する (land 側は外部 receipt に対して発火) |
| outer receipt の exact field 集合と v4 | する (v3 と field 欠落を拒否) | する |
| runner の main/tip blob 等値と object type | **する** (runner を変えた wave の非帰属受理を拒否) | する |

**保証の範囲 (盛らない):** runner の blob 等値が保証するのは「同一 bytes の
`tools/run_tests.py` が両側で使われたこと」だけである。import 閉包・cwd・環境変数・
pytest の選択と scheduler・`conftest.py`・plugin の同一性は保証しない。
初回全走と単独再走の argv・環境も同形ではない。

**明示的に受容する残余:** `flake` は原因の分類ではなく観測の分類である
(初回全走で赤、tested main 単独再走で緑、wave tip 単独再走でも緑)。
production code、`conftest.py`、共有 fixture、pytest plugin、test file 自身、選択・build 設定、
初回と再走の argv や環境の差、負荷や外部汚染に由来する「全走限定赤」を区別しない。
したがって**確率的でない決定的な赤も flake として通りうる**。差分到達可能性の完全な写像が
無い限りこの残余は閉じられない。R2 の発効と引き換えにこれを受容し、受理した nodeid は
`flake_nodeids` と land 結果 JSON へ耐久記録して追跡可能にする。
**検査を削除・弱化して緑を買う変更は引き続き絶対規律 2 により禁止する。**

**理由:**
- flake 1 件で受入全走 (1055〜1273 秒 + queue 待ち) を丸ごと捨てる構造が R2 を発効不能にしていた。
  待ち手の node exact 検査が 3 field 固定だったため、checker 側の分類は end-to-end で
  一度も発効していなかった。
- flake を `red_nodeids` へ混ぜると、実測証拠なしで通した残余がどの nodeid だったかを
  受領証・land 結果・台帳のどこからも追跡できない。
- field 集合が変わるのに schema 値を据え置くと、互換性の無い 2 形が同じ名前を持つ。
- 非帰属経路の証拠 (単独再走 rc) は `tools/run_tests.py` が生成する。既にユーザー裁定済みの
  「待ち手と runner も tested main 側 blob と照合する」方針を、この経路へ先に適用する。
  条件を `flake_nodeids` 非空に絞ると、flake を非帰属と偽った receipt が gate を素通りするため
  無条件とした。

**却下した選択肢:**
- flake を `red_nodeids` に含める / 記録しない — 残余の追跡可能性を失う。
- flake を従来どおり拒否する — R2 が発効せず、受入窓を捨て続ける。
- flake 専用の verdict を足す — 同じ安全条件に対して consumer と文書の分岐だけが増える。
- 同一 tip で全走を再走し、緑なら flake と確定する — 受入全走をもう 1 本消費する。
  窓を捨てないという R2 の目的と正面から矛盾する。
- runner blob SHA を receipt field へ書く — land が Git から再計算できる。自己申告 field を増やさない。
- 単独再走 rc=0 に「対象 node が実行され PASSED した」証明を要求する — 新機構であり本決定の scope 外。
