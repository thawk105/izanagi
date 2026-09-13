## must-fix

成果物の誤値・誤受理・参照破損を具体的に示す must-fix は見つかりませんでした。ただし、裁定済みの公開経路テストと規範追補が未実装であり、段 5 の完了判定はできません。

以下、I＝`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`、TI＝対応する issuer テスト、R＝`orchestrator/campaign/p3_b4_material_report.py`、TR＝対応する material-report テストとします。

## 所見 (nit)

**所見1: 必須の公開発行から material report までの正例が存在しない。**

根拠: TI:1019 は `_compose_aggregate_authority` の直接試験、TI:1087 の公開発行 API 呼出しは不正 pin の拒否試験、TI:1152 は publisher 単体試験です。新規関数には、正常な v2 の発行・読込・resolver・report builder を通すものがありません。

成果物への影響: 最大床値・v2 の参照・全入力の非保証がレポートへ届くという契約は未検証です。現実装が誤値を返す反例までは示せないため、指定基準に従い nit とします。

推奨対応: 裁定済みの「3 spec・各 2 窓・許容内欠測」の公開経路正例と、報告に列挙された未作成の公開 API 負例を追加してください。今回の read-only レビューで実走を要求するものではありません。

**所見2: 規範追補は差分に含まれていない。**

根拠: 提示差分は現 worktree の差分と一致し、変更は I と TI の 2 ファイルだけです。裁定文書 `s4-adjudication.md` の「lens luna」項 6・7 が採用した追補はありません。

成果物への影響: コードの集約規則と人手の採用責任を結ぶ規範文書が未更新です。値セル・既存 pin 自体の変化はないため nit とします。

推奨対応: 裁定された位置・根拠で追補を完成させ、既存の凍結 pin を維持してください。

## CLI 受理集合の表

根拠: I:1528 の `ArgumentParser`、I:1530 の必須排他 group、I:1531 以降の登録・追加検査。`allow_abbrev` は指定されず、既定の **True** です。登録と guard だけを AST 抽出してメモリ上でも照合しました。issuer 本体や pytest は実行していません。

|入力（必要な `--repo-root` は付与）|変更前|変更後|
|---|---|---|
|`--summary PATH`|受理|旧 API へ渡す|
|`--s`、`--su`、`--sum`、`--summ`、`--summa`、`--summar`|受理|すべて維持。新オプションとの prefix 衝突なし|
|`--summary A --summary B`|B を採用|B を採用|
|旧モードに `--expected-spec PATH HASH` を混入|未知引数として拒否|専用 guard で拒否|
|旧モードに `--aggregate-output-dir DIR` を混入|未知引数として拒否|専用 guard で拒否|
|`--summary` と `--aggregate-summary` を併記|拒否|排他 group で拒否|
|モードなし|拒否|必須 group で拒否|
|集約 summary・期待 spec・出力先をすべて指定|拒否|新規受理。summary と spec は反復可|
|集約モードで期待 spec または出力先を省略|拒否|追加 guard で拒否|
|`--a`〜`--aggregate-`|未知引数|集約用 2 オプションに一致して曖昧、拒否|
|`--aggregate-s`、`--aggregate-o`、`--e` と必要引数|拒否|一意な新省略形として受理|

**縮小:** 既存 CLI の成功入力が拒否へ変わる箇所は見つかりませんでした。新専用引数の混入は、以前から拒否されていた入力です。

**拡大:** 完備した集約モードと、その一意な省略形が加わっています。集約経路では旧単一経路にない「期待 spec 閉包・ちょうど 2 窓・被覆」の制約がありますが、旧経路の受理集合は縮めていません。

## schema dispatch の表

根拠: I:1329 の v2 分岐、I:1332 の v1 exact 欄集合、I:1347 の版検査、I:1262 の aggregation 検査、I:1277 の全体再構成比較。

|入力（外側 hash・canonical JSON は有効とする）|結果|
|---|---|
|有効な v1|既存 v1 検査で受理。返却 `schema_version` は v1|
|有効な v2|全 source・期待 spec を再読込し、再構成全体との一致後に受理。返却版は v2|
|未知の版＋v1 欄集合|`artifact_schema_error`|
|未知の版＋v2 欄集合|v1 exact 欄検査で `schema_error`。v2 へ推測 dispatch しない|
|v1 本文の schema だけを v2 に変更|`aggregation` 欠落で `schema_error`|
|v2 本文の schema だけを v1 に変更|余剰 `aggregation` により `schema_error`|
|v1 の必須欄欠落・余剰欄|exact 欄検査で拒否|
|v2 の aggregation 欄不一致|aggregation の exact 検査で拒否|
|v2 のその他の欄欠落・余剰・改変|source 検査等で先に拒否されなければ、全体再構成比較で拒否|

返却版は I:1284 と I:1467 で各経路の定数に固定され、検証版との不一致はありません。v2 拒否後の v1 fallback もありません。

なお、v2 から `aggregation` を削除し、schema も v1 に変えて外側 pin を更新すると、残りが v1 契約を満たす場合は受理され得ます。これは既存 v1 の自己整合検査の境界です。v2 の検証済み成果物として返ることはなく、新しい downgrade 防止 gate は提案しません。

## 波及の取りこぼし

**所見3: 報告の波及列挙には、具体的な呼出し経路と duration 未登録時の挙動が不足している。〔nit〕**

根拠と参照関係は次のとおりです。

|対象|現物で確認した参照関係|
|---|---|
|private 契約|TI:552 の既存 test → TI:569 `_authority_value`。新集約経路も I:1172 で同関数を呼ぶ|
|report 評価|R:215 resolver → I:1520 loader → R:267 evaluator。床値は `Fraction` のまま渡す|
|report 出所・非保証|R:952 は返却された版・artifact path/hash を転記。R:963 は床値と非保証を射影|
|JSON・Markdown の両公開経路|R:1238 と R:1567 が同じ射影を使用。Markdown は R:1195|
|既存 report テスト|TR:257 `_document` → builder。TR:515・590・1043 等もこの経路を使う。TR:633 は `_load_and_evaluate`、TR:958 は resolver と射影を直接試験|
|raw-record producer|`test_p3_b4_raw_record_producer.py:1013`・`:1228` → `material_report.build_material_report_document`|
|producer-auth experiment|`test_p3_b4_producer_auth_experiment.py:352` の `_route_probe` が subprocess 本文で R を import（:366）。同 :806・:830 は R のソース参照・改変対象|
|新規合成 helper|TI:794 → `test_floor_pair_driver.py:157` `_write_inputs`、TI:795 → 同 :208 `_valid_document`。既存 helper 自体は無変更|
|duration 未登録|`conftest.py:1657`・`:1722` は未登録 node を未知 duration として処理。登録欠落による収集拒否ではない|

成果物への影響: report 経路の回帰は床値・出所・非保証に波及し得ますが、今回その誤りは確認できていません。duration 欠落は実行順の見積りに影響し、成果物の値は変えません。

推奨対応: 親の受入対象に上記の具体的経路を記録し、duration は実測後に登録してください。

新規 test の登録漏れについては、次を確認しました。

- TI に `xdist_group` の追加はなく、新規関数は TR の `immutable_publication` fixture を利用していません。
- TR:41 の module group と、`test_real_repo_serialization.py:356` の名前集合は無変更です。同 :1324 の group 消費者集合検査にも TI の追加は入りません。
- `conftest.py:2128` の resource node に基づく group 付与にも、新規 TI 関数の登録はありません。
- 差分と `git status --short --untracked-files=all` に、新規 test file はありません。

## 実装子の報告への反証

**既存テスト無変更の主張は確認できました。** 提示差分と現差分は同一です。TI は既存テスト末尾までの bytes が一致し、既存関数・fixture・decorator を含むソース比較にも変更・削除・改名はありません。TR はファイル全体が byte 単位で同一です。既存の「v1 本文を v2 と名乗らせる」負例も維持されています。

**追加 15 関数・48 ケースも静的に一致しました。** ただし pytest collection の実走結果ではありません。

**実走 nodeid の架空報告や、未実走を緑とする記載はありません。** 報告は実走 nodeid を 0 件と明記しています。記載された issuer テストファイルは実在します。runner の rc=16・hook 拒否という過去の実行結果は、今回許可された資料だけでは独立検証できません。

公開経路正例・公開 API 負例・規範追補の未完了は現物とも一致します。「実装済み・未実走」に加えて「未作成」を区別した報告は適切です。

## 総括

旧 CLI・v1 互換性、schema 分岐、既存テスト無変更について具体的な破損は見つかりませんでした。  
必須の公開経路テストと規範追補が残るため、段 5 完了としての受入は未成立です。  
静的照合とメモリ上の parser 検算のみ実施し、編集・commit・pytest 実走はしていません。