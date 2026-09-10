## 総括

**must-fix 1件。受入前に局所修正が必要です。** git diff・現物・必読資料を確認しました。作業差分は author.patch と完全一致し、旧artifactのSHAも既存rootと一致します。テスト・変異は実走していません。

**R1〔P2〕歴史的コードの存在が閲覧条件として残っている**

- **場所:** [s1_known_axes_freeze.py:908](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_known_axes_freeze.py:908)
- **根拠:** 既知旧文書かつ `historical=True` でも、6種のコードsourceに `resolver → is_file → _sha256` を実行します。SHAの値は不一致でも許すため、この読み取りは当時の入力bytesを束縛していません。親の「axis_trigger_gating.pyだけ不存在Pathに置換すると拒否」という観測と現物の制御フローは一致します。
- **影響:** 旧artifactと非コード凍結入力が不変でも、歴史的出所コードの解決先が存在しないだけで閲覧が拒否されます。これは不要なlive read依存です。なお、親観測は公開APIの入力置換であり、実コード削除後の動作を実証してはいません。
- **最小修正:** `known_historical and historical` の場合だけ、6種のコードsourceを存在確認・読み取りの前で除外する。897行の不要なgenerator SHA読み取りも比較が必要な分岐内へ移す。非コード入力のresolver・存在・SHA検査、現行利用の全文照合、新規文書の厳格検証は維持する。
- **裏取り:** 未改変旧実物＋コードsourceだけ不存在のresolverで歴史閲覧が通る正例を追加し、その存在拒否を戻す変異で検出する。既存の非コード入力改竄・不存在の負例は維持する。

その他の確認結果：

- measurement・calibration・oracle非adapter経路は既定の現行意味照合を維持。調査したconsumerに取り残しはありません。
- 共有fixtureの実生成→独立golden→実検証、既存hold・期待値は不変。meta差分は新規nodeの明示登録です。
- M2は旧文書識別、M3は非コード入力SHA検査を対象として分離されています。M4・M5は実builder後の単一差分で、期待値の同時導出による恒真化は見当たりません。
- **M6 oracleは診断感度だけの検査です。** 別refusalが残り、変異前後とも最終allowedは偽です。単独の受理反転killには数えられません。
- M1〜M6の検出成立は親の実走結果待ちです。authorの未実走を緑とは扱いません。
