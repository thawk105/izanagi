## 総括

**GO（静的検査）**。A-1〜A-3、B-1〜B-4 はすべて `closed` と判定する。  
親による amendment 訂正は一次資料と整合し、新しい採番・数値誤りもない。  
復元した空配列負例は production の拒否条件を拘束しており、恒真な assertion ではない。  
fix の変更はテスト 2 case の追加だけで、production や裁定 §5 の scope 外には接触していない。  
pytest・変異試験は実走しておらず、緑とは報告しない。

## 所見の対応表

| ID | 判定 | 根拠 |
|---|---|---|
| A-1 | closed | canonical node は型タグ、`join`、field 名と文字列値、多重度、入れ子を tuple に保存する。並べ替えるのは root/group の子だけで、順序以外を同一視する経路は見つからない。 |
| A-2 | closed | 非対称は残るが、契約 §3 が重複 member 拒否を要求する対象は「応答」である。現行 catalog は生成器出力と byte 一致して重複がなく、現在の成果物に影響しないため、不採用裁定は妥当。 |
| A-3 | closed | root の `filter_rows=[]` と group の `filters=[]` が負例表へ追加され、いずれも `evaluate_page()` から production matcher を通る。既存 case の期待値変更ではなく純粋な 2 case 追加である。 |
| B-1 | closed | 旧実行記録 U11 の「頁境界で同一 work ID が重複する場合」が §1・§8 の双方で未決として復元された。anti-replay は U13 へ移され、ID 再利用は解消した。 |
| B-2 | closed | U7 は「併記は解決ではない」と明記され、§1・§8 とも未決。旧 amendment §10.3・§13、旧実行記録 §4・§8 と一致する。 |
| B-3 | closed | U15 は追加分 `2,130 file / 99,925,266 bytes` と、既存分を含む総量 `2,258 file / 102,738,024 bytes` を分離した。加算も一致する。 |
| B-4 | closed | 実装中の整列キーは canonical tuple を固定形式の JSON 配列へ直列化したもの。canonical domain は tuple と文字列だけで、JSON decode により元の木を一意に復元できるため、異なる canonical node 同士の衝突対は作れない。引用符・カンマ・括弧は JSON escaping され、空文字列も別値になる。29 通りの実測は補助証拠であり、根拠の本体はこの単射性である。したがって実衝突 fixture を要求した旧所見は成立せず、変異で退行を拘束する裁定は妥当。 |

## 親の訂正の検査

訂正後 §1 の継承表と §8 の台帳は相互に一致し、一次資料とも次のとおり整合する。

- 未決の U7・U9・U11 はすべて残っている。
  - U7 は旧 amendment §13 と旧実行記録 §8 の双方で未決。
  - U9 も両資料で未決。
  - U11 は旧実行記録 §8 が追加した条件 5 の問いであり、その意味のまま継承された。
- U8 は README 導線の項目で、claim-survey README に旧成果物が載り、本差分で再改訂と新 catalog も追加されるため「解決」は妥当。
- U10 は D1432 の裁定を受け、amendment §3 と production の canonical 比較で実装されているため「解決」は妥当。
- 新規 U12〜U15 は、既存の最大番号 U11 の後から採番され、衝突していない。
- U15 の file/byte 数は追加分・既存分・拡張後総量の区別も算術も正しい。

## fix の検査

追加された 2 case は `_openalex_condition1()` → `evaluate_page()` → `_openalex_oqo_matches()` を通る。

- root 空配列は `_canonicalize_openalex_oqo()` の `filter_rows` 非空条件で拒否される。
- group 空配列は root の子を再帰処理し、`_canonicalize_openalex_filter()` の `filters` 非空条件で拒否される。

両 case は expected/actual に同じ不正構造を置いている。左辺 expected の canonical 化で先に例外になるため actual 側はその実行では評価されないが、同じ canonicalizer を双方へ使っている。非空条件を除去すると両側が同じ canonical 値になって条件 1 が通り、assertion が失敗するため恒真ではない。

fix 前から存在した test case の期待値は変更されていない。wave 全体では裁定どおり production を変更しているが、fix 自身の追加は対象テストファイルの 2 case だけである。

## 残る所見

なし。