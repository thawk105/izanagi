## 1. 残赤 1 の原因

判断は **(a) fixture の admission evidence 不足**です。

g1 は campaign と検証の双方で `root` を使います（[test_s8b_ratified_freeze.py:886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_freeze.py:886)、[同:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_freeze.py:928)）。

一方、g2 campaign は別の `scan_root` を `repo_root` に渡しています（[test_s8b_ratified_freeze.py:1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_freeze.py:1106)、[同:1134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_freeze.py:1134)）。`_holdout_repo_root` 未指定時はその `repo_root` が admission authority になります（[s8b_floor_campaign.py:4995](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4995)）。

しかし g2 の full validation は元の `root` を検査します（[test_s8b_ratified_verify.py:1325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_verify.py:1325)）。元 root には g1 台帳しかなく、g2 の `campaign_run_id` 行がありませんでした。live gate の位置は正しく、fixture 側の不足です。

## 2. 残赤 2 の root 依存値

原因は `measurement_head` です。

- 測定 authority の Git HEAD から生成されます（[s8b_holdout_admission.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:456)）。
- admit 行へ保存されます。
- 修正前は admit 行全体が `ledger_projection_sha256` の canonical 入力だったため、authority repo の HEAD 差が `result.json` の digest 差になっていました。

他候補は root 非依存でした。

- `campaign_run_id` は固定時刻と protocol digestから生成されます（[s8b_floor_campaign.py:5063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5063)）。
- `run_relpath` は env、mode、run ID の相対構造です（[同:5070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5070)）。
- `claim_identities` は freeze、holdout、configuration、CCBench pin、env、role の固定 key だけから hash されます（[s8b_holdout_admission.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:462)、[同:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:483)）。

## 3. 直した内容

- [s8b_holdout_admission.py:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1458)
  - exact live row から repository-local な `measurement_head` だけを除く portable projection を追加。
  - 入力 row の exact key 集合検査を維持。
- [s8b_holdout_admission.py:1972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1972)
  - `ledger_projection_sha256` を portable admission rows と完全な attempt rows から計算。
- [s8b_floor_evidence_fixture.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/s8b_floor_evidence_fixture.py:129)
  - production inspectorを呼ばない独立 canonical calculatorへ同じ portable 射影を実装。
- [test_s8b_ratified_freeze.py:1141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_freeze.py:1141)
  - g2 manifest・journalから元 root に完全な admission evidence を構築。
  - 独立 calculator の receipt を `result.json` に束縛してから generation hash を作成。
- [test_s8b_holdout_admission.py:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_holdout_admission.py:837)
  - 異なる `measurement_head` でも portable receipt が一致する正例を追加。
  - ledger だけの `measurement_head` 改変が claim exact 照合で拒否される負例も追加。

## 4. 検査を緩めていない根拠

`measurement_head` は portable artifact の identity ではなく、live authority repository の局所 identity なので、result digest の束縛対象からのみ除外しました。

field 自体の検査は残っています。

- 40桁 hex SHA-1 の形状検査（[s8b_holdout_admission.py:1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1725)）。
- exact ledger row 再構築との完全一致（[同:1735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1735)）。
- claim の exact key集合・全値一致（[同:1759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1759)）。
- 新規負例が ledger/claim 間の `measurement_head` 不一致を拒否します（[test_s8b_holdout_admission.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_holdout_admission.py:858)）。

fix2 の attempt coverage 導出は変更していません。actual/expected key 集合の双方向完全一致と各 row の全値一致も維持されています（[s8b_holdout_admission.py:1954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1954)）。

## 5. 緑だった 11 ファイルへの静的波及

- `test_s8b_sort_swo_receipt.py`: receipt identity・compiler hashは未変更。
- `test_s8b_binary_admission.py`: binary exact-key gateは未変更。
- `test_s8b_floor_contract.py`: receipt schema・key集合は不変更。digest値のみ新しいportable計算。
- `test_s8b_holdout_admission.py`:直接波及。新規正負例を追加し、既存helperの既定値は維持。
- `test_s8b_floor_stats.py`: live inspectorとartifact producerが同じ新digestを使う。公開署名は不変更。
- `test_s8b_materialization.py`: materialization・SWO receipt経路は未変更。
- `test_s8b_freeze_io.py`: freeze IO・generation契約は未変更。
- `test_s8b_ratified_freeze.py`: g2 fixtureだけ直接変更。g1構築経路は不変更。
- `test_s8b_holdout_freeze.py`: live inspector経由のdigest値が変わるが、consumer APIとfail-closed挙動は不変更。
- `test_s8b_oracle_driver.py`: oracle driver契約は未変更。
- `test_s8b_oracle_report.py`: downstream receipt schemaは不変更。

pytest・`tools/run_tests.py` は一度も実行していません。4変更ファイルの AST parse、NFC正規化、結合文字不在検査のみ成功しています。git操作、commit、docs、`freeze_verification_hold.py`、`output/`の編集は行っていません。

## 総括

残赤1は、g2 campaignが別authorityへ証拠を書き、検証rootにg2台帳が無かったfixture不足です。元rootへ独立calculatorで完全証拠を構築しました。

残赤2はrepository-localな`measurement_head`がportable digestへ混入したことが原因です。digestからのみ除外し、root非依存にしました。

緩めていない根拠は、`measurement_head`の形状・ledger完全一致・claim完全一致と、attempt coverageの双方向完全一致をすべて維持したことです。