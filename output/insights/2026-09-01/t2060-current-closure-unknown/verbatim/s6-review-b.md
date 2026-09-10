## 保存済み成果物の互換

B-01 / refuted / [layer3_schema.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:5)、[layer3_schema.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:13)、[layer3_schema.json:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:22) / 成果物影響: 実装前 schema を通った保存済み v2/v3 report の受理集合は縮小しない。

理由は次の包含関係で静的に確定できる。

- 旧 schema は top-level `additionalProperties:false` だったため、旧 schema を通った report は新 field を持ちえない。
- 新 field は `properties` に追加されたが、`required` にはない。
- certified conditional は fieldが「存在する」場合だけ拒否するため、fieldを欠く既存 report には作用しない。
- v2 reader は [layer3_report.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:262) で v3 schema を複製し、version と `admission_decision` だけを書き換える。新 field は optional のまま残るため、fieldを欠く既存 v2 も通る。
- `certifying_input=true` だが新 fieldを欠く保存済み v3 も conditional を通る。

v2 reader は新たに、人工的な v2 reportへ exact `"unknown"` を入れた形も受理する。しかし値は `"unknown"` に固定され、certifying reportでは禁止されるため、現行適合を偽って広げる経路ではない。

Nit: [test_layer3_report.py:1498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1498) は保存済み実ファイルを列挙せず、現在の fixture reportから fieldを削除して v2/v3 を合成している。互換性自体は上の schema 包含関係で証明できるが、テスト名の「saved」は実体より強い。

## 所有外 consumer への波及

B-02 / refuted / [s8b_oracle_artifacts.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:45)、[s8b_oracle_artifacts.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:165) / 成果物影響: oracle observations の epoch exact key 集合と reason enum は変わらない。

`CAMPAIGN_VERIFIER_EPOCH_KEYS` は従来の8 keyのままであり、validator は引き続き exact集合を要求する。新 fieldは `HistoricalCampaignView` の propertyであって `CampaignVerifierEpoch` の fieldではない。

B-03 / refuted / [s8b_oracle_report.py:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_report.py:566)、[s8b_oracle_report.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_report.py:611) / 成果物影響: `campaign_verifier_epochs` の各 entryに新 fieldは混入しない。

成功、拒否、unavailable の3投影はいずれも従来の8 keyだけを構築している。`current_verifier_conformance` は参照されない。

B-04 / refuted / [layer3_report.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:290)、[s4-adjudication.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s4-adjudication.md:52) / 成果物影響: `s1_report` と Layer 3 の nested epoch exact dict は不変。

新 fieldは nested `_epoch_projection` に足されず、Layer 3 top-levelだけに置かれた。`HistoricalCampaignView` への追加も dataclass fieldではなく propertyなので、既存 epoch projectionを暗黙に増やさない。

一方、歴史 `build_report` の top-level exact shapeと canonical bytesは意図どおり変わる。[layer3_report.py:588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:588) の report全体を比較、hash、再投影する consumer は影響面である。`test_layer3_admission_diagnosis` は焦点集合に入っているが、後述の追加 consumer test が抜けている。

## 裁定との対応 (項目ごとの過不足)

B-08 / refuted / [s4-adjudication.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s4-adjudication.md:61) / 成果物影響: 裁定 §2 の production 4項目に不足・余分はない。

1. property追加: [artifact_admission.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:392) が exact `"unknown"` を返す。充足。
2. 歴史 reportのtop-level投影: [layer3_report.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:608) は nested epochを従来形で作り、[layer3_report.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:614) でtop-levelにだけ追加する。充足。
3. optional schemaとcertified禁止: [layer3_schema.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:13) と [layer3_schema.json:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:242)。`required` 非追加も確認できる。充足。
4. certified昇格時の除去: [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707) で除去し、[layer3_report.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:716) でcertified schema検証する。充足。

B-05 / refuted / [artifact_admission.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:963)、[artifact_admission.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:965) / 成果物影響: certified成果物の受理集合とfail-closed検査は変わらない。

D1245で最優先の意味互換性について、緩和行はない。

- `HISTORICAL_RAW` のearly returnだけが現行 closureを読まない。
- certifiedはE0を拒否し、現行 closure取得失敗を `current-closure-unavailable` として拒否する。[artifact_admission.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:967)
- persisted COMMIT検査は維持される。[artifact_admission.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1268)
- exact `CertifiedCampaignView` 境界も維持される。[artifact_admission.py:1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1315)
- Layer 3 certified経路も除去前にcertified admissionを通る。[layer3_report.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:687)

## 表示が届く経路

B-06 / refuted / [artifact_admission.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:392)、[layer3_report.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:614)、[layer3_report.py:723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:723) / 成果物影響: 新しくrenderする歴史 Layer 3 JSONの実バイトに `"current_verifier_conformance":"unknown"` が入る。

経路は次のとおり。

`HistoricalCampaignView.current_verifier_conformance`
→ `build_report` のtop-level dict
→ `_validate_schema`
→ `render`
→ `_canonical_bytes(report)`
→ `_write_report_atomic` のwrite。

具体的には [layer3_report.py:497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:497)、[layer3_report.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:622)、[layer3_report.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:729)。

既存の保存済み reportは再生成しないため、その旧バイトへ遡及追加はされない。[layer3_report.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:16)

## テスト node の分割

B-07 / real / [test_layer3_report.py:1847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1847) / 成果物影響: certified field除去とschema禁止のどちらが退行したかを単一nodeの赤から一意に判定できない。

(a)から(e)は別nodeで、(e)もparametrizeによりv2/v3の別nodeになる。一方、(f) は次の独立な二理由を同じnodeへ詰めている。

| 変異 | 同じnodeが赤くなる位置 |
|---|---|
| L1: [layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:707) の `pop` 削除 | `build_accepted_report` 内のschema検証で、report返却前に赤 |
| C2: [layer3_schema.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:13) の禁止句削除 | field注入後の `pytest.raises` が成立せず赤 |

したがって `test_certified_report_omits_and_schema_forbids_current_verifier_conformance` は、producer livenessとconsumer schema fail-closedを別nodeへ分割すべきである。

## 焦点走の漏れ

B-09 / real / [s4-adjudication.md:182](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s4-adjudication.md:182)、[s5-author.md:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s5-author.md:53) / 成果物影響: Layer 3 top-level shape、schema、closure hashを読む下流の退行が焦点走だけでは検出されない可能性がある。

実装後の参照再調査で、裁定 §6 の12 fileにない次のconsumer test候補が確認されている。

- `test_autonomous_trial_completeness.py`
- `test_trial_registry.py`
- `test_t126_qualification_artifacts.py`
- `test_official_perf_closure.py`
- `test_s1_known_axes_freeze.py`
- `test_s8b_oracle_driver.py`
- AST closure meta-test

特に `autonomous_trial_completeness.py` は `build_report` の追加top-level keyの直接影響候補として明記されている。[s5-author.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s5-author.md:55)

## 所見一覧 (ID / real|refuted / 実体 / 成果物影響)

| ID | 判定 | 実体 | 成果物影響 |
|---|---|---|---|
| B-01 | refuted | schema optional性とv2 reader | 保存済み旧valid reportの受理集合は縮小しない |
| B-02 | refuted | oracle exact key validator | epoch evidenceのshapeは不変 |
| B-03 | refuted | oracle report projection | 新fieldはoracle observationsへ混入しない |
| B-04 | refuted | nested epochとS-1 projection | exact epoch dictは不変 |
| B-05 | refuted | certified gate、persisted COMMIT、exact view | D1245の意味互換性fail-closedは維持 |
| B-06 | refuted | historical render/write経路 | 新規歴史reportの実バイトへ`"unknown"`が届く |
| B-07 | real | certified test (f) | C2とL1が同じnodeで赤になり原因が一意でない |
| B-08 | refuted | 裁定 §2 production 4項目 | 過不足なし |
| B-09 | real | 焦点test集合 | 追加consumerの退行が焦点走から漏れうる |

## 総括

production実装には、保存済みv2/v3を新たに拒否する変更、oracleやS-1のepoch shape変更、D1245のcertified fail-closed緩和は見当たらない。歴史reportの新規実バイトへ`"unknown"`も到達する。

real所見は2件である。

- certifiedの正例とschema負例が同一nodeに同居し、C2とL1の変異帰属が衝突する。
- 実装後に判明した追加consumer testが裁定 §6 の焦点集合へ反映されていない。

pytestは実行しておらず、緑とは判定していない。