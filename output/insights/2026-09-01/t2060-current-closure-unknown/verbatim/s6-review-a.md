## 受理集合への影響

結論: 実装前後の `CERTIFIED_ACCEPTANCE` の campaign 受理集合に差分はありません。

- production admission の差分は [artifact_admission.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:392) の historical property 追加だけです。
- purpose の exact 型検査、E0 拒否、current closure の capture/catch は [artifact_admission.py:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:939) と [artifact_admission.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:957) で不変です。
- 全 COMMIT の保存済み証拠検査は [artifact_admission.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1268)、token 付き view 発行は同 1282、exact 型境界は同 1315 で不変です。
- [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707) の field 除去は certified admission、decision 再照合、E1 検査の後にあり、拒否 campaign を受理へ変えません。

ただし、実装前から存在する通過反例が二つあります。

1. COMMIT が 0 件なら `for record in records` が空回りし、`require_persisted_certified_commit` は一度も呼ばれません。既存テスト自身が no-COMMIT campaign に exact `CertifiedCampaignView` を期待しています。[test_artifact_admission.py:1296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1296)、同 1351、1371。
2. module global の `_CERTIFIED_VIEW_TOKEN` は参照可能です。[artifact_admission.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:71)。dirty closure から得た E1 historical view の各 field を使い、この token を [CertifiedCampaignView の constructor](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:339) へ直接渡せば、current closure capture と persisted COMMIT 検査を通らず exact 型境界を通過できます。replay capability は別途失敗しますが、`require_certified_campaign_view` 自体は通ります。これは裁定 [s4-adjudication.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s4-adjudication.md:14) が認識済みの既存限界で、今回の受理集合拡大ではありません。

Layer 3 の non-certifying schema 受理集合は、新 optional key を受け入れる分だけ意図どおり広がります。certifying report には後述の条件で広がりません。

## 恒真性の検査 (実装を戻したときの赤の対応表)

新規 7 node を production 全体の旧状態へ戻した場合:

| 新規 node | 旧実装での結果 | 赤または通過理由 |
|---|---|---|
| historical structure | 通る | 旧来の historical early return を検査する回帰 pin。裁定も既知と明記 |
| historical property | 赤 | [test_artifact_admission.py:1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1610) が `AttributeError` |
| dirty certified rejection | 通る | capture/catch は旧実装から存在 |
| historical report projection | 赤 | [test_layer3_report.py:1342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1342) が `KeyError` |
| saved v2 without field | 赤 | 同 1512 の `del` が `KeyError`。schema optionality の assertion ではない |
| saved v3 without field | 赤 | 同上 |
| certified omit and forbid | 通る | 旧 schema の `additionalProperties: false` が注入 field を unknown key として拒否するため |

したがって、構造 pin、dirty certified 負例、certified schema node の3種は単独では全実装 rollback を検出しません。特に certified schema node は C2 単独変異を kill しますが、旧 schema へ丸ごと戻す反例では通ります。

実装追加を個別に戻した場合:

| 戻す実装 | 赤になる箇所 |
|---|---|
| historical property 全体 | property node の [line 1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1610) が `AttributeError` |
| property の `"unknown"` 値 | 同 line 1610 の値 assertion |
| report 投影 | report node の [line 1342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1342) が `KeyError` |
| schema property 定義 | `build_report` 内部の schema 検証が additional-property で先に失敗 |
| certified 禁止句 | [line 1869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1869) の `pytest.raises` が DID NOT RAISE |
| certified field 除去 | 同 1860 の builder 呼出しが unexpected `Layer3ReportError`。assertion へ到達しない |

追加テストには `getattr(..., default)`、`.get(..., default)`、`hasattr`、try/except はありません。追加 production には [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707) の `report.pop(..., None)` が1件あります。これは producer 投影が欠落しても certified 昇格を止めないため、除去が実際に行われたことを certified node 単独では証明できません。

## 既存期待値の保全

- patch は削除行 0 件で、既存の assert、raises、parametrize、node 名の置換はありません。
- ただし既存 fixture の内容は1件変更されています。[test_layer3_report.py:1582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1582) に `del report["current_verifier_conformance"]` が追加されています。期待結果は「epoch のない保存済み certifying v3 を読む」のままですが、fixture は明確に変更されています。
- nested epoch の exact dict 比較は [test_layer3_report.py:1374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1374) にそのまま存在し、新 field は top-level なので比較対象へ混入していません。
- `test_s1_report.py` は patch に hunk 自体がありません。従って epoch 投影 exact dict の変更はありません。

## 変異事前登録との整合

7変異はいずれも現在のコードに成立します。再登録が必要な位置はありません。

| ID | 現在位置と old 逐語 | 検出箇所 |
|---|---|---|
| M1 | [artifact_admission.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:963): `if purpose is CampaignReadPurpose.HISTORICAL_RAW:` / `return recorded.diagnostic` | structure node は line 1587 の呼出しで拒否される |
| M2 | 同 967-974: `try:`、`contract_loader_binding.capture_contract_loader_binding()`、`except contract_loader_binding.ContractLoaderBindingError as exc:`、reason exact `"current-closure-unavailable"` | dirty certified node の [line 1622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1622) が DID NOT RAISE |
| C1 | [layer3_schema.json:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:22): top-level `required` の exact list は新 field を含まない | v2/v3 とも [line 1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1519) で required error |
| C2 | [layer3_schema.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:13): `"not": {"required": ["current_verifier_conformance"]},` | line 1869 の `pytest.raises` が DID NOT RAISE |
| D1 | [artifact_admission.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:394): `return "unknown"` | line 1610 の値 assertion |
| D2 | [layer3_report.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:614): `"current_verifier_conformance": ( admitted_campaign.current_verifier_conformance )` | line 1342 が `KeyError` |
| L1 | [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707): `report.pop("current_verifier_conformance", None)` | certified builder が後段 schema で失敗 |

## schema 禁止条件の実効性

静的な Draft 7 評価は次のとおりです。

- `certifying_input` が存在し exact `true` なら [layer3_schema.json:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:8) の `if` が成立します。
- field が存在すると、`required` が成立し、その外側の `not` が失敗するため report 全体が拒否されます。
- field が不在なら内側の `required` が失敗し、`not` が成立します。
- `certifying_input=false` または欠落時は `then` が適用されず、optional property として exact `"unknown"` のみ許可されます。

従って条件は恒真ではなく、意図した位置にあります。C2だけを削除すると、既知 property になった注入 field が通り、現在のテストは失敗します。

ただし全 schema 変更を旧状態へ戻すと、注入 field は unknown property として top-level `additionalProperties: false` で拒否されるため、同じテストは通ります。これは条件の実効性ではなくテストの rollback 識別力の問題です。

## scope 逸脱

差分は次の5 fileだけです。

- `orchestrator/campaign/artifact_admission.py`
- `orchestrator/campaign/layer3_report.py`
- `orchestrator/campaign/layer3_schema.json`
- `orchestrator/tests/test_artifact_admission.py`
- `orchestrator/tests/test_layer3_report.py`

docs、`output/`、`tools/`、許可外の `orchestrator/` file、`test_s1_report.py` の変更はありません。裁定 §2 の production 4項目と許可されたテスト追加の範囲内です。

## 所見一覧 (ID / real|refuted / 実体 / 成果物影響)

| ID | 判定 | 実体 | 成果物影響 |
|---|---|---|---|
| A-01 | refuted | certified gate、capture/catch、COMMIT loop、token 発行、exact 型境界は差分なし | 今回の差分による certified campaign の新規受理はない |
| A-02 | real | [artifact_admission.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1268) は COMMIT 0件で空回りし、既存テストも受理を要求 | COMMIT 証拠のない campaign に certified view が発行されうるが、今回導入ではない |
| A-03 | real | module global token と constructor 直接呼出しによる exact view 偽造 | dirty E1 historical campaign が current closure と persisted COMMIT 発行経路を迂回して exact 型境界を通れる既知限界 |
| T-01 | real | 新規 structure、dirty certified、certified schema node は旧実装でも通る | これら3 nodeの緑だけでは D1245 実装の存在を証明できない |
| T-02 | real | [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707) の default 付き `pop` | historical 投影欠落時も certified 昇格が継続し、除去処理の存在証明を弱める |
| E-01 | real | [test_layer3_report.py:1582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1582) で既存 fixture を変更 | 保存済み certifying v3 の期待結果は維持されるが、fixture 無変更ではない |
| E-02 | refuted | nested exact dict は line 1374 に残り、`test_s1_report.py` は差分なし | 既存 epoch 投影の exact shape は変わらない |
| M-01 | refuted | 登録7変異の位置と old 逐語がすべて存在 | 再登録不要 |
| S-01 | refuted | schema line 8-14 の `if`、`then`、`not`、`required` 配置は実効的 | certifying report に history-only field は通らない |
| D-01 | real | property は closure の状態にかかわらず constant `"unknown"` | clean current closure の historical report も unknown となり、現在適合の肯定表示はできない。裁定が明示的に受容済み |
| O-01 | refuted | patch の対象は許可された5 fileだけ | scope 外成果物への変更なし |

## 総括

今回の差分による `CERTIFIED_ACCEPTANCE` の受理集合拡大、schema 禁止条件の不発、scope 逸脱、変異位置の消失は確認できませんでした。

一方、証拠面では新規3 nodeが旧実装でも通り、default 付き `pop` が field の実在を要求していません。また、no-COMMIT campaign の certified view 発行と module global token 偽造は、今回未導入ながら実際に通る既存反例です。

pytest や schema probe は実行していません。以上は射影された資料だけによる静的検査です。