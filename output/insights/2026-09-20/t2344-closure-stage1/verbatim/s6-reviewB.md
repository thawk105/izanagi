## 所見 RB-1: 焦点走の赤3件は、85本化に伴うtimeout期待値の追随漏れ

**主張:** 親の原因分類と「630 → 850を5か所」の修正範囲は正しい。ただし、本差分に帰属するテスト追随漏れであり、無関係な既存失敗ではない。

**根拠 (file:line):** `orchestrator/tests/test_t671_source_binding.py:1638,1717,1723,1801,1807` が630を固定している。productionの `orchestrator/campaign/contract_loader_binding.py:391,453` は問い合わせ件数×10秒で、85本なら850秒。`focus-f1.log:116,213,308` の失敗はこの引数比較であり、直前の欠損拒否・全disk読取・digest不一致拒否の検査ではない。同ログ`:319` は3112 passed / 3 failed。

**real / refuted:** real。productionの拒否ロジック欠陥という疑いはrefuted。

**must-fix か nit か:** nit。指定された成果物影響基準では、期待値修正によるcertified選択・材料レポート・成果物台帳の変更は示せない。ただし焦点走の完了には修正・再確認が必要。

**成果物影響:** 科学成果物の値・受理集合は変わらず、テスト期待値が現行85本の問い合わせを正しく記述する。

## 所見 RB-2: 他ファイルに同型の件数依存literalの追随漏れは見つからない

**主張:** `orchestrator/tests/` 全体を検索した範囲で、現行closureを旧件数で検査する残存はRB-1の5か所だけ。

**根拠 (file:line):** `test_t671_source_binding.py:1469` の62は任意件数のスケーリング試験の入力であり、現行tupleの件数ではない。同`:1591,1643` と `acceptance_duration_ledger.json:23037,23039` の`sixty_two`は既存node名。`test_layer3_report.py:1917,1935,1946,2023` の63は新設した歴史grammarを指す。その他の63にはdigest長不正例や数値演算があり、closure件数への追随対象ではない。

**real / refuted:** 他ファイルの同型漏れはrefuted。古いnode名の残存はreal。

**must-fix か nit か:** nit。node名の改名は不要。

**成果物影響:** 改名しなければ既存duration ledgerのnode参照を維持でき、受理集合には影響しない。

## 所見 RB-3: 新旧scopeとtuple順序は独立照合で一致した

**主張:** 名乗りの拡大、旧scopeの改変、既存63本の並べ替えはない。

**根拠 (file:line):** `artifact_admission.py:76,82` の2定数は `s4-ruling.md:29` 以下の確定コードブロックとUTF-8 bytesで一致。指定された旧commitを自分で`git show`し、旧2定数と新設定数 `artifact_admission.py:111,116` もbytes一致した。`campaign_lock.py:49` の先頭63行は旧commitと行単位で一致し、`:113` からの22本は `layer1-edges.json:3` の`layer1_unenrolled`キーのsorted順と一致。`:234` の歴史tupleも旧63と同順・同内容。追加文言に推移閉包完成や、その意味でのsource-bound保証はない。

**real / refuted:** 違反の疑いはrefuted。

**must-fix か nit か:** nit相当の確認事項。修正不要。

**成果物影響:** 現行材料レポートは確定した85／163／78のscopeを表示し、歴史63のscopeと記録epochの導出順序を保存する。

## 所見 RB-4: production差分に裁定外の一般化・互換unionはない

**主張:** 裁定§2のproduction項目は実装され、削除すべき新機構は認めない。兄弟validatorの複製は裁定どおり。

**根拠 (file:line):** `campaign_lock.py:629` は62版`:584` の関数名・tuple名置換と本文一致。既存の通常・24・62 validatorは変更前と文字列一致した。`:815` の歴史decoderは85／63／62／24へ分岐する。`artifact_admission.py:265,320,1074,1148` に所定の歴史63対応があり、`:1128` のepoch hash式にscopeは追加されていない。`contract_loader_binding.py:2,58,61` はdocstring変更のみ。差分は指定8ファイルで、新module・共通production helper・registry・実行時閉包計算・通常decoderの互換unionはない。

**real / refuted:** 過剰実装・production実装漏れの疑いはrefuted。

**must-fix か nit か:** nit相当の確認事項。共通化や削除は不要。

**成果物影響:** 新規v2 lockの束縛対象が85本となり、歴史63は専用経路だけで読める。既存24／62の検証順・例外文面・返却処理は保存される。

## 所見 RB-5: テスト追加は指定構成で、既存期待値の反転・緩和はない

**主張:** 新設はcodec4関数＋admission5関数＋22本driftの1関数で一致する。「9本＋22本」は関数数とparam展開数を区別する必要がある。

**根拠 (file:line):** `test_campaign_lock_codec.py:755,776,790,830` の4関数は8ケース。`test_artifact_admission.py:3465,3511,3529,3570,3591` の5関数は70ケース、`:3660` からのdrift試験は22ケースで、新設10関数は合計100ケース。`test_layer3_report.py:1917,1946,2023` には既存関数の歴史63ケースも追加される。既存関数の削除はなく、変更はtuple・固定epoch・scope・件数・grammarラベルの追随。4固定値は独立再計算でも一致し、`FROZEN_E0_EPOCH` は不変。

**real / refuted:** 構成不一致・既存検査緩和の疑いはrefuted。追随不足はRB-1。

**must-fix か nit か:** nit相当の確認事項。修正不要。

**成果物影響:** 歴史63の記録blob照合、certified隔離、新22本の未commit drift拒否を検査する範囲が増え、既存の拒否条件は維持される。

## 所見 RB-6: 旧63のcertified再解析喪失は実装どおりで、Cの実測は代表4件

**主張:** 裁定§6の開示は実装と一致する。ただしCを「20件すべてのcertified consumer実走」と説明してはならない。

**根拠 (file:line):** `artifact_admission.py:1037` はHISTORICAL_RAWだけを歴史decoderへ送る。通常validator `campaign_lock.py:485` は現行85を要求するため、exact-63はcertifiedのdecode段で拒否される。`real-locks-probe.json:4` のAは20件、`:146` のBと`:192` のCは各4件。Cは必須代表3件にrr50を加え、通常decoderとcertified epoch APIのcodec拒否を記録する。`:226` はbytes不変。

**real / refuted:** 受理集合縮小はrealで裁定済み。20件すべてでCを実走したという解釈はrefuted。

**must-fix か nit か:** nit相当の開示事項。decoderやpurposeの緩和は求めない。

**成果物影響:** 記録済みexact-63の20件は最新checkoutのcertified選択対象から外れる一方、歴史閲覧では旧scope・記録E1を保持する。全20件への拒否の一般化はgrammar検査からの静的結論である。

## 総括

最も影響が大きいのはRB-6の旧63成果物のcertified再解析喪失だが、裁定済みの挙動で開示とも一致する。
採否判定は **NO-GO（現commitの完了採用）**：焦点走の赤3件が残っている。
production差分の裁定違反は検出せず、次の修正はRB-1の5 literalへの局所追随で足りる。
本レビューは静的検査のみ。pytest・変異検査は実走しておらず、受入全走の完了も認定しない。