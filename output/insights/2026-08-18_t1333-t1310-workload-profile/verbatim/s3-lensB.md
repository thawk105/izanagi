```text
所見 B-01 / 探索側で descriptor と実 benchmark の scale 変異を Layer-3 が再計算しない

根拠
- s2-plan.md:316-323 は「descriptor scale が entry と一致」を要求する。
- autonomous_trial_completeness.py:571-586 は descriptor について
  "descriptor_schema": descriptor.get("schema_version")
  "descriptor_sha256": content_digest
  だけを期待し、descriptor["scale"] を entry から再投影しない。
- autonomous_trial_completeness.py:587-589 は search_config の records/threads だけを比較する。
- p3_autonomous_workload_trial.py:691-709 の三 sink は独立しており、s8b_descriptor.py:92-97 は任意の正整数 scale を受理する。
- p3_autonomous_workload_trial.py:2843-2856 の cell には PerfConfig 自体が保存されない。

具体例: 探索 ycsb-a の `_descriptor_for` だけを `records=200_000, threads=8` に変異させる。campaign は entry の 100,000/4、PerfConfig も 100,000/4、descriptor digest は変異後 descriptor と整合する。Layer-3 は全て自己整合として通せる。`_perf_for` だけの scale 変異はさらに cell から不可視である。

深刻度: must-fix

成果物影響: accepted campaign の descriptor、実測 benchmark、report/ledger の scale reference が分離し、探索結果の比較対象が誤る。

所見 B-02 / P2 の「三 sink 内 literal が実射影に使われる」が plan では満たされず、oracle source も未束縛

根拠
- s1-brief.md:61-63 は `records`/`threads` を三 sink 内の `1_000_000`/`48` literal として実際の射影に使うと定める。
- s2-plan.md:56-71 は formal entry を
  "records": authority["records"],
  "threads": authority["threads"],
  とし、s2-plan.md:98 は「検査済みの records / threads 変数を使う」とする。literal は拒否条件であり、射影値ではない。
- s8b_oracle_driver.py:747-764 は freeze 文書の Mapping から `PerfConfig` を作る。
- s8b_ratified_freeze.py:948-959, 1021-1025, 1062-1089 は v2 で unknownness と snapshot hash を検査するが、module 表との `candidate_id/records/threads/ycsb` 四 key 比較をしない。
- `load_ratified_freeze` は s8b_ratified_freeze.py:1341-1345 の `_verify_generation_semantics` を通すだけで、`s8b_holdout_freeze.verify_document` を呼ばない。

schema-valid な `freeze["holdouts"]["H1"]` に `records=2_000_000` を入れると、`_perf_for_holdout` は通過する。一方、module 表の 1,000,000/48 から作る descriptor も通常の descriptor validation を通過する。両 consumer の境界に共通 digest/assert がない。

深刻度: must-fix

成果物影響: oracle の floor/選択・benchmark report が module/arm descriptor と異なる scale を参照する。

所見 B-03 / formal campaign の spec_content が Layer-3 で探索値に固定されたまま

根拠
- s2-plan.md:65-68 は formal entry に `FORMAL_NON_CERTIFYING_SPEC_CONTENT` を設定する。
- s2-plan.md:301-314 は formal campaign の search values だけを profile-aware にする。
- autonomous_trial_completeness.py:597-602 は依然として
  `identity.get("spec_content") != _AUTONOMOUS_SPEC_CONTENT`
  を要求する。
- p3_autonomous_workload_trial.py:673-678 の現行 `_campaign_for` は exploratory spec を固定している。

formal campaign が plan 通り別 spec_content を持つと、scale、scope、source record が正しくても `campaign-chain` で拒否される。

深刻度: must-fix

成果物影響: formal non-certifying run が Layer-3 report/ledger へ到達せず、formal 受理集合から全件落ちる。

所見 B-04 / selector 整合検査の予定位置が現行 admission 呼出し順と矛盾する

根拠
- s2-plan.md:261-269 は workload/profile 整合を「registry admission 後、campaign identity 前」に置く。
- p3_autonomous_workload_trial.py:927-1002 の `_trial_launch_admission` は、p3_autonomous_workload_trial.py:988-996 で既に `_prepare_campaign_identity` を呼び、:997-1000 で campaign binding を検査する。
- run_trial も p3_autonomous_workload_trial.py:3336-3345 で `_trial_launch_admission` を先に呼び、:3367-3377 で再導出する。
- CLI も p3_autonomous_workload_trial.py:3802-3809 で selector を渡す前に admission を作る。

formal manifest を exploratory selector で指定した入力は、selector mismatch の前に formal entry から campaign identity を生成する。逆に selector 検査を admission より前へ移すと、holdout の U4 gate と intended profile mismatch の優先順位が変わる。

深刻度: must-fix

成果物影響: campaign_id、拒否理由、U4 受理集合のいずれかが変わり、formal/exploratory の誤 profile が preflight に混入する。

所見 B-05 / `_prepare_manifest_campaign_identity` が T-1349 の別 identity sink として残る

根拠
- p3_autonomous_workload_trial.py:899-905 は descriptor を sealed arm input から取り、flags は `WORKLOADS[workload]` から取る。
- p3_autonomous_workload_trial.py:903-915 はその二つを `_campaign_for` に渡すが、producer own descriptor、legacy freeze、arm resolver own descriptor の比較をしない。
- s2-plan.md:430-436 の mutation anchor は `_prepare_campaign_identity` だけで、manifest helper の同じ assert を明記していない。
- `test_p3_autonomous_workload_trial.py:5312-5320` はこの別経路を直接使用する。

producer entry を変更した状態でも manifest preflight は campaign identity を生成でき、後段の runtime gate とは別の descriptor/campaign reference を発行できる。

深刻度: should-fix

成果物影響: manifest の campaign_id と実行時 descriptor/benchmark の参照が食い違い、registry/acceptance で別理由の拒否または誤参照になる。

所見 B-06 / formal pilot_scope の completeness consumer が固定値のまま

根拠
- s2-plan.md:281-289 は `_common_payload`、generation validator、campaign checker、receipt checker の全てを entry-derived にする。
- autonomous_trial_completeness.py:1056-1058 の `_check_payload_validation_receipt` は entry 引数を持たない。
- autonomous_trial_completeness.py:1139-1155 は
  `"pilot_scope": _PILOT_SCOPE`
  を固定し、:1272-1281 の caller も expected scope を渡さない。
- s8c_generation_projection.py:621-654 も `_validate_common_payload` の `PILOT_SCOPE` 固定である。

formal payload が別 scope を出すと receipt gate が探索 scope として拒否する。これを避けるため expected scope に default を付けると、formal scope の明示検査を bypass できる。

深刻度: must-fix

成果物影響: formal role payload/receipt が全件 reject されるか、逆に scope mismatch の受理集合が拡大する。

所見 B-07 / provenance record が三箇所の自己一致だけで、loaderとの意味結合がない

根拠
- s2-plan.md:209-222 は source record を exact-key object として構築する。
- s2-plan.md:224-240 は run-start、report、campaign の byte 同値を新 completeness 検査に要求する。
- しかし三箇所の値を同時に `source/path/loader/sha256` 改変しても、byte 同値だけでは通る。
- `load_legacy_freeze` 自体は s8b_ratified_freeze.py:1376-1394 で path/hash を検査するが、生成された source record の全 field と loader 実体を比較しない。

深刻度: should-fix

成果物影響: report/ledger が実際とは異なる legacy source、path、loader を provenance reference として記録できる。

所見 B-08 / `expected_pilot_scope` の直接 validator 呼出しが既存テスト列挙から漏れている

根拠
- s2-plan.md:505-509 は helper 更新と二つの既存テストだけを列挙する。
- test_s8c_generation_projection.py:404-414 は `validate_coder_payload` を直接呼ぶ。
- test_s8c_generation_projection.py:523-534 は `validate_planner_payload` を直接呼ぶ。
- 両方とも plan が追加する必須 `expected_pilot_scope` を渡していない。

引数を必須化すればテストは実行時 TypeError で落ちる。default を追加すれば、programmatic caller が expected scope なしで formal payload を検証できる。

深刻度: should-fix

成果物影響: 受入全走が壊れるか、scope validation の bypass が残り、formal payload の受理集合が意図より広がる。

P 判定
- P1: 現行の ycsb-only 射影と s2-plan.md:114-136 の独立 golden は、m3-baseline.json:3,48,93 の hash を保つ方向で矛盾なし。ただし実測は未実施。
- P2: formal scale literal を実射影へ使うという brief と、module records/threads を射影する plan が矛盾する。
- P3: legacy loader の選択自体は一致するが、oracle consumer と provenance の独立再計算が不足する。
- P4: closed selector の方針は妥当だが、admission 前後の順序が未解決。
- P5: scope 値の分離方針は妥当だが、receipt/checker/test の consumer threading が不足する。

C01 は所見なし。s2-plan.md:329-345 と s8c_preregistration_evidence.py:1423-1440 の順序から、status は UNSATISFIED のまま reason が `workload-projection-mismatch` から `ratified-generation-reference-absent` へ移る予測で整合する。

GO / NO-GO: NO-GO
```

## 総括

最大の穴は、探索側の descriptor/PerfConfig を Layer-3 が独立再投影せず、自己一致だけで通す点。  
P2 の formal scale 射影と v2 oracle の source 分離も未解消。  
formal は spec、selector 順序、pilot_scope で受理不能になる経路が残る。