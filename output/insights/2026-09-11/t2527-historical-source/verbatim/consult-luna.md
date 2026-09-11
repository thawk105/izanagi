## 総括

**最小実装方針は条件付き採用を推奨します。修正すべき所見は2件で、いずれも変異検査の帰属・到達性です。** 新機構の追加やconsumer本体の一律変更は不要です。編集・pytest・commitは行っていません。

**C1 / severity: medium / F28：旧source識別子の改竄試験は、除外処理の弱体化を単独で検出できない。**

- **file:line:** [plan.md:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2527-historical-source/artifacts/t2527/plan.md:98)、[s1_known_axes_freeze.py:874](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_known_axes_freeze.py:874)。
- **real疑い根拠:** 旧source SHAを変更すると固定root識別を失い、厳格経路のgenerator不一致で先に拒否されます。source比較を無条件除外する変異を入れても、この拒否は残ります。plan:106の注意書きは正しいものの、:98の「弱体化を検出」という帰属とは両立しません。
- **成果物影響:** 改竄拒否自体は確認できますが、source除外範囲の健全性を過大評価します。
- **最小対処:** 旧6種SHA改竄は「歴史識別を失った文書の拒否」として記録してください。入力束縛は認証済み旧文書＋resolver先の単一改竄、SHA以外を保持する比較は再構成側のkey等の単一変更で、それぞれ独立に帰属させます。既存拒否は緩めません。

**C2 / severity: medium / F28・F29：oracleの変異試験は、既存receipt経路では対象呼出しに到達しない。**

- **file:line:** [plan.md:103](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2527-historical-source/artifacts/t2527/plan.md:103)、[s8b_oracle_driver.py:467](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s8b_oracle_driver.py:467)、[同:509](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s8b_oracle_driver.py:509)。
- **real疑い根拠:** adapterが発火すると、成功して拒否リストが空でも `adapter_refusals is not None` となり、:518のknown-axes `verify` は呼ばれません。既存receipt fixtureの成功や他理由の拒否では、当該呼出しを歴史閲覧へ変更する変異を評価できません。
- **成果物影響:** 現行consumerの検証経路を固定したという受入証拠が成立しない可能性があります。
- **最小対処:** adapter非発火の正常対照で:518への到達を確認し、known-axesの意味不一致だけによる拒否を検査してください。receipt経路は既存検査を維持します。校正も[validated_target:235](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_verify_extime_calibration.py:235)を対象に含め、後段のread-heavy対象照合にmaskされない別構成の不一致を使うと帰属できます。

静的検算では、実物rootは `354f4b…11f516` と一致し、記録sourceとの差は指定のコード6ファイルだけでした。記録generator SHAも `e5dfa84c6` のblobと一致しました。

そのgenerator版との比較では、[build_document:734](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_known_axes_freeze.py:734)の出力構造・文言に変更はありません。呼出し先の `_BASE`、`SWEEP_US`、両sweepの `_genome`、`SILO_SPACE`、`subset_name`、`variant_id`、Genomeの正準化もAST一致でした。追加された述語・comparator・pairing検査は拒否条件を変えますが、成功時の出力値を書き換えません。**記録metadataを指定して再構成する場合、source SHA以外の出力差を生む変更は今回の静的照合では見つかりませんでした。** 実再構成の一致は親の実測で確定すべきで、`e5dfa84c6`を全sourceの凍結HEADとは扱えません。

共有fixtureは[real_known_axes_doc:44](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/tests/test_s1_measurement_freeze.py:44)の実生成→独立golden→実検証を維持すればよく、planのmeta登録方針も既存のreader分類・共有fixture閉包と整合します。measurement・校正・oracle非adapter経路は現行利用です。CLIの歴史閲覧だけなら現行再構成は不要ですが、旧measurement自身の[generator／implementation検査:400](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_measurement_freeze.py:400)まで通るとは一般化できません。

受理する正例は、固定rootに一致し入力束縛が正常な旧実物の歴史閲覧、その旧実物がSHA限定補正後の再構成と一致する現行利用、および現行 `build_document()` が生成した自己整合文書です。
拒否する負例は、旧識別子・内容・入力の改竄、旧実物の現行利用時の意味不一致、新規文書のgenerator/source不一致・非ancestor・再構成不一致です。

**推奨裁定:** C1・C2を検査計画へ反映してauthorへ進める。F27は固定root認証後の限定補正なら恒真化に当たりませんが、入力自身のhashを期待rootに差し込む実装は不可です。F28は上記のmaskを除去して評価し、F29は旧実物・新規実生成・注入した再構成変異を別々の証拠として報告してください。golden・hold・既存拒否の変更は不要です。
