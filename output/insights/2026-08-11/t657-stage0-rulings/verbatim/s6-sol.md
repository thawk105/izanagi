## 所見

### SOL6-01 / nit / 既存 node の受理方向が虚偽

- **破れる具体構成:** 既存 7 node の docstring は一律に「落ちる入力を増やす」と主張するが、実際は次のとおりである。
  - `unresolved_count` と blocker 診断の更新は、裁定後の正しい値への置換であり受理集合には中立。
  - gate 削除、owner 変更、Q3 の `not-applicable` は index 指定を同じ対象または等価な対象の ID 指定へ変えただけで中立。
  - `resolved_without_evidence` と enum 不在検査は、裁定により正例になった Q3 から、依然として負例の fixture-assignment/B へ再照準したもので中立。
- **根拠の file:line:** `orchestrator/tests/test_calibration_freeze_authority_contract.py:135-180,537-589,680-717`。裁定は各 node に方向を正確に書くよう要求する: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-rulings/s4-ruling.md:82-84`。
- **成果物影響:** certified 選択・台帳の受理集合は変わらないが、レポートへ「既存テストが受理集合を縮小した」という誤った監査結果を転記しうる。

## 段 3 所見の再発監査

- **SOL-01:** 裁定どおり未解決のまま温存。S/B は pin され、G の既存 applicability は不変、`require_stage0_complete` は S/B を数えて拒否する。`calibration_freeze_authority_contract.py:97-105,574-596,607-620,885-909`
- **SOL-02:** revocation は no-fallback literal だけ。namespace/schema/topology の実装追加なし。設計も裁定待ちを維持する。`docs/calibration-freeze-authority-bundle-design.md:815-821`
- **SOL-03:** 段集合が実体導出でないことは明記されたまま。実装は宣言と gate ID の drift だけを検査し、証拠とは主張していない。`docs/calibration-freeze-authority-bundle-design.md:643-647`; `calibration_freeze_authority_contract.py:338-354,745-759`
- **SOL-04:** manifest は 8 gate のままで段 6 新 gate はない。R3 も未解決のまま。`manifest.v1.json:1`; `docs/calibration-freeze-authority-bundle-design.md:829-832`
- **LUNA-01:** SOL-02 と同じ。失効 schema の越権再発なし。
- **LUNA-02:** manifest literal、実 entries の再計算値、module literal pin の三者比較になっており、自己再計算へ退化していない。`calibration_freeze_authority_contract.py:138-154,482-503`; `test_calibration_freeze_authority_contract.py:592-610`
- **LUNA-03:** 証拠欄のない段 6 gate は新設されていない。fixture-assignment gate は `pending` に pin され、宣言だけの `resolved` を拒否する。`calibration_freeze_authority_contract.py:138-151`; `test_calibration_freeze_authority_contract.py:573-589`
- **LUNA-04:** §8.1 の全 12 row を抽出し、selection literal 集合を enum と exact 比較する。`calibration_freeze_authority_contract.py:315-335,527-532`
- **LUNA-05:** 既存 §11.2 抽出器は未変更で、裁定どおり backlog のまま。`calibration_freeze_authority_contract.py:279-285`
- **LUNA-06:** production/resolver 変更は 0 件で、policy 実装を装っていない。
- **LUNA-07:** state regression、再計算済み gate 並べ替え、docs selection、段集合の各負例は、実際に synthetic repository を変更して `validate_repository` を呼ぶ。node 名だけの検査ではない。`test_calibration_freeze_authority_contract.py:124-132,400-505,592-677`
- **LUNA-08:** §10 の数値を gate ID に変換し、manifest 内の assignment gate と exact 比較する。`calibration_freeze_authority_contract.py:338-354,750-759`

## 受理集合監査

実装前なら拒否、実装後に受理される原子的な面は 9 点である。

- Q3 profile の裁定済み化 3 点。
- required gate の `resolved` 化 5 点。
- fixture-assignment gate ID の置換 1 点。
- U-A1 profile の `activation-window` は旧 enum でも既に受理されたため 0 点。

全 9 点は段 4 裁定 `s4-ruling.md:46-54` に逐語的根拠がある。これ以外の受理拡大は見つからない。`fixtures`、`row_coverage`、`pending_count=5`、top-level `status=incomplete` は不変で、production と case file の差分も 0 件だった。

## 総括

GO（blocker 0 / must-fix 0 / nit 1）。  
最大の破れは、既存 node の docstring が中立な再照準まで「受理集合縮小」と虚偽表示する点。  
先送り 3 件、applicability、段 0 の到達不能性、`require_stage0_complete` の fail-closed は維持されている。  
裁定根拠のない受理拡大、revocation schema、段 6 新 gate、production/case 変更は見つからない。