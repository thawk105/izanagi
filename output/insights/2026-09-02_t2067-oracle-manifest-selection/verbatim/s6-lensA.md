## 所見 1 — 正例は gate 由来の `no-approved-spec` を識別できない

**所見:** genuine g1 正例は、現行実装では gate 通過後に spec loader へ到達する。しかし期待値が reason だけなので、「gate が正常に通った」ことを単独では証明しない。gate が選択検査を終えた後に `RatifiedFreezeError("no-approved-spec")` を送出する変異は、新規2本と既存4本をすべて通過できる。

**根拠 (file:line):** gate は `s8b_oracle_manifest.py:1206`、その例外の reason 素通しは `s8b_oracle_manifest.py:1207-1212`、spec loader は `s8b_oracle_manifest.py:1214-1217`。正例は `test_s8b_oracle_manifest.py:1482` の reason と `:1483` の出力不存在しか確認せず、`__cause__` が `ReviewedSpecError` であることを確認しない。負例は実 selection が `s8b_ratified_freeze.py:3639-3655` で先に mismatch を送出するため、上記の後置例外変異には到達しない。既存4本は public gate 自体を stub に置換する。

**成果物影響:** genuine g1 が受理集合から誤って除外され、oracle manifest candidate、以後のレポートおよび台帳参照が生成されないのに、テストは成功し得る。

**must-fix か nit か:** must-fix。正例で `captured.value.__cause__` が `oracle_spec.ReviewedSpecError` であることまで固定すれば識別できる。

## 所見 2 — 負例は実 eligibility 導出を置換している

**所見:** 新規負例は外側の selection helper、候補列挙、最小 run-id 判定、reason 翻訳を実行するが、earlier run の適格性を決める中核を stub にしている。したがって production の `_derive_floor_selection_eligibility` を常に `False` にする変異は殺せない。

**根拠 (file:line):** stub は `test_s8b_oracle_manifest.py:1507-1515`。earlier fixture は result だけを複製しており `:1496-1504`、実導出が要求する sibling manifest/journal は `s8b_holdout_freeze.py:1877-1888`、admission evidence の検査は `:1901-1909`。実戻り値は `:1925` で selection 集合へ反映されるのは `:1949-1959`。正例には earlier candidate がなく、この変異を発火させない。

**成果物影響:** 実導出が壊れて earlier eligible run を見落とすと、後発の floor_source を持つ g1 が受理され、その freeze SHA と参照を焼いた manifest、後続レポート、台帳が誤った certified 選択を引き継ぐ。

**must-fix か nit か:** must-fix。実 manifest、journal、admission evidence を持つ genuine earlier run を使う負例が必要。

## 所見 3 — 登録 M1〜M6 の KILL 対応

**所見:** 登録された M1〜M6 はすべて現行 suite で KILL できる。ただし M4 と M5 の事前登録に記された落ち方は現物と一致しない。

**根拠 (file:line):**

- M1: gate 削除で既存4本の `selection_calls` が空になり、`test_s8b_oracle_manifest.py:1353,1391,1426,1469` が失敗する。
- M2: `ratified.document` が記録され、同じ4 assert が失敗する。実 callee でも exact type 検査 `s8b_ratified_freeze.py:3567-3570` により、正例の `test_s8b_oracle_manifest.py:1482` が失敗する。
- M3: module `ROOT` は `s8b_oracle_manifest.py:42` の実 repository root なので、既存4本の期待する tmp `root` と異なり同じ4 assert が失敗する。
- M4: `root` 省略時は assert まで到達しない。stub の `lambda candidate, candidate_root` は `test_s8b_oracle_manifest.py:1342-1344,1374-1376,1417-1419,1459-1461` で第2引数必須のため、call site `s8b_oracle_manifest.py:1206` で `TypeError` となり4本が ERROR になる。KILL ではあるが「引数 assert が落ちる」という `ruling.md:92` の記述は不正確。
- M5: gate を spec loader 後へ移すと、pin 無し経路の `test_s8b_oracle_manifest.py:1353` が空、二回呼出し経路の `:1391` が一回となって失敗する。genuine 正例 `:1482` 自体は同じ `no-approved-spec` で成功するため、`ruling.md:93` の「genuine 正例も KILL」は成立しない。
- M6: manifest 側の reason 素通しだけを定数化すると `test_s8b_oracle_manifest.py:1521` が失敗する。元の `RatifiedFreezeError` は cause に残るため `:1525` は成功する。

**成果物影響:** 登録6変異による受理集合または manifest 参照の変化が、テストに検出されず残るケースはない。相違は KILL 根拠の記録精度だけである。

**must-fix か nit か:** nit。

## 所見 4 — 恒真 assert と探索順

**所見:** `eligibility_calls == [earlier_rel]` は恒真ではない。候補導出を省略すれば空になり、余分な earlier candidate を処理すれば要素が増える。ただし fixture 上は earlier candidate が一件だけなので、実 eligibility の正しさではなく探索 topology の確認に留まる。

**根拠 (file:line):** namespace 列挙は `s8b_holdout_freeze.py:1820-1827`、selected 以上の timestamp を除外するのは `:1834-1837`、eligibility 呼出しは `:1849-1853`、run-id sort は `:1862`。fixture の selected 時刻は固定値 `test_s8b_ratified_freeze.py:247-255` で、campaign へ `:1019` から渡される。`test_s8b_oracle_manifest.py:1526` はこの一件呼出しを確認するだけで、実導出は所見2の stub により消えている。`:1495` の非同一 assert は production 機構ではなく fixture 前提の guard である。

**成果物影響:** この assert 自体に成果物影響はない。実 eligibility の未被覆による成果物影響は所見2のとおり。

**must-fix か nit か:** nit。

## 所見 5 — 既存 assert、差分一致、揮発 payload

**所見:** 既存 assert の削除、緩和、反転、skip はない。`author.patch` と現物にも食い違いはない。新規期待値に working-tree hash、実時刻、絶対 tmp path は焼き込まれていない。

**根拠 (file:line):** `author.patch:1-182` は追加だけであり、reverse check も成功した。timestamp 文字列 `test_s8b_oracle_manifest.py:1492-1495` は wall clock ではなく `_FIXED_NOW` `test_s8b_ratified_freeze.py:247` に依存する。fixture 時刻や run-id 形式が変われば `:1495` が明示的に失敗するため、将来時刻による不定期破損ではない。

**成果物影響:** production の成果物値、受理集合、参照に影響しない。fixture 内部変更への保守上の結合だけである。

**must-fix か nit か:** nit。静的検査のみで、pytest は実行していない。

## 総括

must-fix は2件、登録 M1〜M6 に殺せない変異はない。ただし所見1と所見2の未登録変異は生存する。