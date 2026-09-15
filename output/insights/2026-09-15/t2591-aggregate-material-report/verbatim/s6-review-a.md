## 両層の実体性

**実装の must-fix は見つからない。実 issuer → resolver → builder の経路は成立している（静的読解）。**

以下、`T`＝`orchestrator/tests/test_p3_b4_material_report.py`、`R`＝`orchestrator/campaign/p3_b4_material_report.py`、`I`＝`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`。行番号は変更後。

- `T:969–988`：3 spec・summary の実 bytes から期待値を構成。
- `T:991` → `I:1244–1249`：実集約・canonical bytes 生成・create-only 発行。
- `T:1008` → `I:1513` → `I:1315–1325`：pin の実 bytes/hash を検査。v2 は `I:1266–1272` で source を読み直し、集約を再構成する。
- `T:1026` → `R:1230` → `R:215`：builder が resolver を再度実行する。先に得た `resolved` を builder に注入していない。
- `R:267` → `T:1021–1023`：観測 wrapper は実 evaluator へ委譲する。
- `T:1033`：assert 対象は `document.json_bytes` の decode 結果。

`_INPUT_CACHE` / `_DOCUMENT_CACHE` は `T:248,257` の helper 内だけで使われ、新正例から呼ばれない。共有 fixture は publication を提供するが、解析結果・report の使い回しではない。

Git・calibration・fsync と publication fixture 内部の環境 seam は残る。裁定の許可範囲内であり、集約・解決・投影の代替 stub は確認されなかった。

## 恒真な assert

**所見 1：集約固有でない検査はあるが、新正例全体は恒真ではない。**

- **根拠（file:line）：**
  - `T:972,973,978,987,988`：入力 fixture の性質確認。issuer/builder が何もしなくても、この部分自体は成立する。
  - `T:1000,1012–1014`：発行 bytes の hash と解決結果の一致。v1 でも成立し得る。
  - `T:1015,1031,1043,1056`：最大値との一致。単独 artifact に同じ最大値を入れても、これらの条件単独では識別できない。
  - `T:1029–1030`：呼出し回数・型。v1 の evaluator 呼出しでも成立する。
  - `T:1034` の `availability/reason/path/hash/generator_identity`：集約専用の性質ではない。
  - `T:1049–1051`：非保証の転記は必要だが、値だけを模倣する stub の不使用を単独では証明しない。`1050–1051` は入力側の名指し確認と `1049` からも導ける。
  - `T:1054–1055`：path/hash の転記は v1 にもある性質。
- **real か推測か：** real、静的読解。これらを「常に真」と断じるのは不正確。集約固有性・実呼出しの証拠として単独では不足するという意味。
- **must-fix か nit か：** nit。
- **放置時の成果物影響：** 現行実装の値・受理集合・参照は変わらない。
- **推奨：** 各 assert を独立した集約証明として水増ししない。実経路、literal v2、入力由来の最大値・全非保証を合わせて評価する。

裁定 §3 **(a)〜(f) の未充足は見つからない**。それぞれ `T:1029–1031`、`1033–1051`、`972–978`、`1034–1044`、`981–988/1049–1051`、`1054–1056` が対応する。床値・非保証は発行結果から逆算していない。

## 変異 5 件の kill 判定

以下は**静的予測であり、変異実走結果ではない**。旧走は当該 test file から新 node を除いた集合として判定する。

| 変異 | 新走 | 最初の検出位置 | 旧走 |
|---|---|---|---|
| M1：schema を v1 | KILLED 予測 | `T:1034`、literal v2 は `1040`。内部検査も同じ source helper を使うため、そこで識別されない | SURVIVED 予測。既存 present は v1 |
| M2：非保証を基底のみ | KILLED 予測 | `T:1049`。3 source の項目と集約非保証が欠落 | SURVIVED 予測。既存 present は基底非保証のみ |
| M3：floor 引数全体をゼロ | KILLED 予測 | `T:1031` | **KILLED 予測**。既存 m9 の absent/success が `T:907` で `[None]` を要求 |
| M4：投影 ratio をゼロ | KILLED 予測 | **新 assert には届かない**。`T:1026` 内で `R:1052–1053` が拒否 | SURVIVED 予測。既存 present の床値はゼロ |
| M5：Markdown path を固定 | KILLED 予測 | `T:1054`。発行先は `out/b4-floor-aggregate__…` | SURVIVED 予測。既存 path は指定 literal と同じ |

**所見 2：M3 の旧走 SURVIVED は、引数全体の置換では成立しない。**

- **根拠（file:line）：** `R:268–272` は present/absent の条件式。`T:907` は absent 時の実引数 `None` を観測する。
- **real か推測か：** 旧 assert の存在は real。KILLED は静的予測。
- **must-fix か nit か：** nit。
- **放置時の成果物影響：** 成果物は変わらないが、旧走でも検出する変異を新正例の追加検出力として誤計上する。
- **推奨：** 引数全体を置換した場合は証拠から除外し erratum に残す。`authoritative_floor.floor` の present 枝だけをゼロにし `else None` を維持する変異なら、旧走 SURVIVED 予測となる。**親が測れ。**

**所見 3：M4 は既存 production 検査が先に殺す。**

- **根拠（file:line）：** `R:1243` → `R:1042–1053` は authority から独立に ratio を作り、投影値と比較する。
- **real か推測か：** real、静的読解。
- **must-fix か nit か：** nit。
- **放置時の成果物影響：** 誤ったゼロ床値の document は返らず、例外になる。新 assert の検出力という説明だけが誤る。
- **推奨：** 「新入力が既存検査を発火させる」と記録する。裁定 §4 の「内側にも拒否層が無い」という説明は訂正する。検査を外す必要はない。

M1/M2 は対象 module に定数・`floor_issuer` の import が現在ないため、変異作成時の **NameError を意味上の kill と数えないこと**。有効な参照で親が新旧両走を測れ。

## 規律 2 と禁止面

**差分検査で違反は見つからない。**

- 指定された変更前後の `T` を行単位で比較：**+101 / −0**。新関数を除去した AST も一致。
- `_ABSENT_LEGACY_*`、m9、手書き helper、既存 assert に変更なし。xfail/skip の追加なし。
- serialization golden は `test_real_repo_serialization.py:376` の新 node 1 件だけ追加。
- duration ledger は新 node `79.0` と件数 `23109 → 23110` のみ。これらを除いた JSON は変更前と一致。
- 禁止面の **1,604 ファイルを bytes 比較し差分ゼロ**（`__pycache__` を除外）。対象は `campaign/**`、`docs/**`、issuer test、floor-pair-driver test。基準 commit に対する禁止面の Git 差分も空。
- 新期待値に working-tree hash・現在日時・絶対 path・実行順の焼込みはない。artifact hash は当該実 bytes から算出する。

実装子報告の裏取り：

- `attempt-0001.events.jsonl:63,68` に **50 passed / 304.11秒 / rc=0**、**1 passed / 49 deselected / rc=0** の実行記録がある。
- `/tmp/t2591-aggregate-material-report.xml:1` の testcase 所要は **78.765秒**。79.0 の登録と整合。
- fixture consumer 増加、共有 helper 再利用、production 不変、meta-test の関連先は現物と整合する。
- 本レビュー自身はテスト未実走。子の成功記録を確認したのであって、独立再実測ではない。meta-test・変異の成功は確認していない。

## 総括

**実装は裁定 §3 を満たす。must-fix なし。証拠の説明に nit 2 件：M3 の変異範囲と、M4 の実際の拒否位置。**

新正例が殺せない指定変異は静的には見つからない。ただし **M3 を引数全体置換で実施すると旧走でも殺せる**ため、追加検出力の証拠にはならない。

親は有効な変異差分を固定し、新旧両走の失敗 node 完全集合と未実走 meta-test を測れ。実 Git 凍結・calibration 真正性・publish・certification 成立は、この正例の証明範囲に含まれない。