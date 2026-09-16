## 総括

**must-fix は見つかりませんでした。** 追加受理集合は段 4 の最終仕様に一致し、対象外の行の受理条件も維持されています。M1〜M9 はすべて追加テストで検出できると静的に判断します。

指定の射影ファイルはすべて読了しました。現物の diff と射影 patch の一致も確認しました。**テスト・変異検査は実走していません。** 以下の期待赤は静的予測です。

参照略号：

- **A** = `orchestrator/campaign/p3_b4_admission_record.py`
- **T** = `orchestrator/tests/test_p3_b4_admission_record.py`
- **D** = `docs/phase3-b4-reflux-ablation-preregistration.md`
- **S4** = `/home/SFC/tanab/.claude/jobs/1c1ec45a/tmp/wave-t2464/s4-adjudication.md`
- **V** = `/home/SFC/tanab/.claude/jobs/1c1ec45a/tmp/wave-t2464/verbatim`

## must-fix

なし。

### 受理集合と対象外への影響

追加受理は、正規化後の対象 label に限り、次の全条件を満たす値です（A:658、A:668、A:670、A:674）。

```text
実行責任者 = <owner>、開始時刻 = 未記入
```

- 正規表現が値全体に一致する。
- owner は `、`・`=`・CR・LF を含まない。
- `owner.strip()` が非空。
- owner が既存 sentinel 正規表現に一致しない。
- owner の casefold 値が whole-value sentinel 集合に入らない。

生セルには先に外周の `strip()`、default-ignorable／format 文字の拒否、NFKC 正規化が適用されます。**内部空白を畳み込む処理はありません**（A:538、A:658）。

受理例は、他欄が有効であることを前提に、次のとおりです。

|対象行の値|結果・理由|
|---|---|
|`実行責任者 = thawk105、開始時刻 = 未記入`|追加受理|
|`実行責任者 =   thawk105  、開始時刻 = 未記入`|owner の外周空白を除去して判定|
|`実行責任者 ＝ ｔｈａｗｋ１０５、開始時刻 ＝ 未記入`|NFKC 後に指定構文へ一致|
|`実行責任者 = TBD123、開始時刻 = 未記入`|既存 sentinel の単語境界条件では `TBD` に一致しない|
|owner が説明文、NUL、BEL、`---`＋NUL|追加受理。段 4 で明示的に scope 外とされた意味検証の領域|

これらは最終仕様の正規化・既存 sentinel 規則から導かれる集合です。仕様外の拡張・縮小は見つかりませんでした。追加分岐に一致しない値も既存判定へ進むため、従来受理していた値は失われません（A:681）。

`values.values()` から `values.items()` への変更で走査順は変わりません。同じ辞書の挿入順を使い、走査中の変更もありません。正規化後の重複 label 拒否、キー集合一致検査も分岐より前に残っています（A:661、A:665）。対象外の 9 行は従来どおり A:681 の判定を受けます。expectation の raw／normalized 構文検査と binding も維持されています（A:687、A:691）。

### 負例の到達条件

以下の ID は変異表でも使用します。テスト名はすべて `test_section5_` に続く部分です。

|ID|テスト名・位置|実際に免除を阻止する条件|
|---|---|---|
|P|`accepts_unrecorded_start_time_with_named_owner` — T:483|正例。A:680 を通り、返却 projection も照合|
|N1|`rejects_whole_unrecorded_owner_start_cell` — T:497|A:670 の構文不一致 → A:683|
|N2|`rejects_unrecorded_owner_with_unrecorded_start` — T:512|A:677 の owner sentinel → A:683|
|N3|`rejects_whitespace_owner_with_unrecorded_start` — T:527|A:674 で owner が空 → A:676 → A:683|
|N4|`rejects_reserved_owner_with_unrecorded_start` — T:542|`TBD`・全角 `ＴＢＤ`・`N/A`・`要記入` は A:677、`x`・`---` は A:678 → A:683|
|N5|`rejects_other_start_sentinels` — T:565|A:670 の構文不一致 → A:683|
|N6|`rejects_unrecorded_start_suffix` — T:584|A:669 の fullmatch 不一致 → A:683|
|N7|`rejects_reordered_unrecorded_start_fields` — T:599|A:670 の構文不一致 → A:683|
|N8|`rejects_extra_owner_start_field` — T:614|A:670 の owner capture 不一致 → A:683|
|N9|`rejects_optional_start_syntax_in_other_label` — T:629|env_tag では A:668 不成立 → A:683|
|N10|`rejects_unrecorded_other_rows_with_optional_start` — T:646|対象外行で A:668 不成立 → A:683|

**N3 は非空条件を実際に検査しています。** T:529 の `=` 後の空白は 4 個あり、構文の固定空白が 1 個を消費しても capture に 3 個残ります。`+` に一致した後、`strip()` で空になります。M4 ではこの文書が受理され、テストが赤になります。

「既存検査で落ちるだけ」の範囲は区別が必要です。

- N1・N5・N6・N7・N8 は owner 条件まで到達せず、構文不一致の後に既存 sentinel 検査で落ちます。**owner 条件の変異に対しては恒真**ですが、構文や対象行の免除範囲を広げる変異には有効です。
- N9・N10 は fixture 上、対象行より先に対象外行で落ちます。追加受理そのものの証拠にはなりません。N9 は M3 を検出し、N10 は既存の対象外行拒否を確認します。
- M1 に対しては負例すべてが拒否のままです。機構の存在を検出するのは P です。

### loop と既存テスト

late binding による未検査ケースはありません。`_raises` は渡された callable をその場で実行します（T:61、T:63）。N4・N5・N10 の各 lambda は、次の反復で `document` が更新される前に呼ばれます。

ただし変異で途中のケースが失敗すれば、その node 内の後続ケースは実行されません。たとえば M5 では N4 の先頭 `TBD`、M6 では `x`、M7 では N5 の `TODO` で停止する予測です。node の赤を、後続ケースまで観測した証拠にはできません。

差分はテスト 11 関数の追加のみです。既存テストの期待値変更・削除・改名・skip・xfail はありません。追加正例は従来の合成 `_PROJECTIONS` を使い（T:27、T:93、T:494）、現行 closure hash の差し込みはありません。T:667 以降の live projection 利用は既存コードです。

### M1〜M9 の期待赤 node 集合

対象は**追加された 11 node のみ**です。上表の ID はそれぞれ `orchestrator/tests/test_p3_b4_admission_record.py::test_section5_…` を表します。

|変異|期待赤 node 集合|静的判定|
|---|---|---|
|M1：追加分岐削除|{P}|検出|
|M2：対象 label を無条件 continue|{N1, N2, N3, N4, N5, N6, N7, N8}|検出|
|M3：label 条件削除|{N9}|検出|
|M4：owner 非空条件削除|{N3}|検出|
|M5：owner regex sentinel 条件削除|{N2, N4}|検出|
|M6：owner whole-value 条件削除|{N4}|検出|
|M7：開始時刻に TODO も許可|{N5}|検出|
|M8：fullmatch → match|{N6}|検出|
|M9：owner capture → `.+`|{N8}|検出|

**SURVIVE 予測はありません。** N10 はこの 9 変異のいずれも検出しません。

## nit

### 1. expectation 行の拒否順序について、段 4 の説明が逆

S4:79 は「expectation 行を `未記入` にすると構文検査が先に落ちる」としていますが、現物では sentinel 走査が先です。`未記入` は A:683 で拒否され、A:687 の構文検査には到達しません。

sentinel 判定を外せば後段の構文検査でも拒否されるため、「その負例だけでは sentinel 保持を証明できない」という結論は妥当です。ただし理由は修正すべきです。

**放置時の影響：成果物・受理集合・参照は変わりませんが、検証記録の拒否経路説明が誤ったまま残ります。**

### 2. 変更後 matrix の見出しが変更前を名乗っている

V/parent-probe-after-matrix.txt:1 は「現行（未変更）コード」と記載していますが、同ファイル:3 の `未記入 → ACCEPT` は変更後実装と整合します。また :12 は対象外セルの参考見出しだけで、結果行がありません。この出力単体を対象外行不変の実測証拠にはできません。

**放置時の影響：成果物・受理集合・参照は変わりませんが、probe の変更前後の帰属と証拠範囲を誤読できます。**

## 親 probe の現物照合

**実文書は変更後も拒否されます。** D:159、D:162、D:163、D:164、D:165、D:166 の計 6 欄に `未記入` が残っています。走査順では D:159 が A:683 に当たり、対象行の追加分岐へ到達する前に拒否されます。V/parent-probe-after.txt:1 と整合します。これは現物からの静的確認で、validator の再実走ではありません。

**§5.1.1 の bytes と sha は不変です。** 現物 D:420 から D:705 の直前までを HEAD と比較し、bytes 一致を確認しました。読み取り専用の hash 再計算結果も親 probe と一致しました。

|項目|確認値|
|---|---|
|節の長さ|21,833 bytes|
|raw SHA-256|`0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`|
|semantic SHA-256|`5d0b189bd68391b4a6876bd24400230e7186f6bc1fe374ea298d44edebcfd1a7`|
|変更後の文書全体 SHA-256|`f7db4e9a600babc1a13f1c9832340bda7844539680f84dd4659dc89356c356b8`|

両節 hash は `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47`、同:50 の pin と一致します。**節 hash 不変を文書全体やコード closure の参照不変へ一般化することはできません。**

## 別枠

owner の説明文・制御文字・識別子形式の検査は再提案しません。A:674 の処理は strip と既存 sentinel 検査に限られ、それらを受理する境界は S4:47 で明示的に scope 外とされています。今回の must-fix には含めません。