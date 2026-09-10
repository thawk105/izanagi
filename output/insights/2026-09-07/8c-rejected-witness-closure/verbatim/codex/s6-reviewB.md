## pin の独立検算

変更後 builder の戻り値だけを使い、fixture の `_canonical_bytes` / `_sha256` と production helper は使わず、標準 `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)` と `hashlib.sha256` で再計算した。

| entry | 独立再計算した長さ / SHA-256 | 判定 |
|---|---|---|
| `build_authority_manifest` | `1512` / `006b05079fe8c73bc379945446766c729672fcf1a01cdc298f1cbf8ab3ccf162` | 一致。変わるべきでない entry |
| `build_execution_provenance` | `484` / `3691de16e9c1a749e62b5401736b7320a26777113ab89082b6678f38f48abad4` | 一致。変わるべきでない entry |
| `build_launch_admission_inputs` | `962` / `5e0992a5f6c132d24fc392522cd8e77bda656b726b4ff7070462857e3dcc13bb` | 一致。source-closure digest の固定長置換により hash だけ変化 |
| `build_ordered_wal_projection` | `1914` / `9729a84ea7a64fb724c61ae8e1cf47579d66b8749446902007cb0ba623698c2f` | 一致。abort payload 拡張により長さと hash が変化 |
| `build_recovery_envelope_inputs` | `14909` / `d28b266e498df8a15167ed880c713fdaf6b140bb4400f78acb96903b330029d6` | 一致。固定長 digest の波及で hash だけ変化 |
| `build_result_evidence_record` | `1848` / `d4579e061f28a7dbca8813b6717e2fe4ed90906134c82d127df4b2ebfa9cf31f` | 一致。constraint、source-closure、WAL digest が固定長で変化 |
| `build_source_closure_record` | `1704` / `7988bd17287b97cc136032b388362646e1b736c654e199e089e66e0e5408a502` | 一致。runtime path の 7 byte 増分どおり |

変わるべき 5 entry はすべて変わり、変わるべきでない 2 entry は変わっていない。

[test_reflux_result_evidence.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_result_evidence.py:24) の 4 pin も独立導出と一致した。

- raw record: `d4579e061f28a7dbca8813b6717e2fe4ed90906134c82d127df4b2ebfa9cf31f`
- ledger evidence: 同じ raw bytes の SHA-256 なので同値
- outer: `sha256(bytes.fromhex(salt) + domain + canonical({evidence_sha256,outcome}))` = `ff042352f18c8182afa1483c07b8405fe46d1ac84b4ba6e14ee1c9415c233781`
- wrong-domain: `sha256(domain + raw)` = `ddfba4f4378180881809538818c926bb774ad735635a0dcb76993c3863062476`
- raw record 長: `1848`。literal と一致し、変更前後で不変
- anomaly constraint: `c17af4fe39df550b032ab8e672f27db22be2ca16458aeeed8662f0a3bac8b2c8`

[test_reflux_origin_fixture_builder.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_origin_fixture_builder.py:107) の緑は、7 builder の現在の戻り値と baseline の全 entry が独立 canonicalizer で exact 一致することを含意する。一方、builder 自体の意味的正しさ、production schema、別 process 間の決定性、baseline 外の pin、golden 4 層は含意しない。

## must-fix

1. [reflux_formal_consumer.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:835) の anomaly 検査は production の導出関係を閉じていない。

   `types=["ww"]` と `reason.type="rw"` の不一致、未知 `type="bogus"`、`edge.from=True`、`length=True`、長さ 0/1 の version list を実際に `_valid_witness_anomaly()` へ渡すとすべて `True` になった。[model.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:347) の `WW/WR/RW`、[model.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:381) の `types` 導出、[dsg.py:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:562) の phenomenon 分類に合わせ、次を要求する必要がある。

   - `length`、`from`、`to` は exact int
   - cycle 長は最低 2
   - version は存在時に exact int 2 要素
   - reason type は `WW/WR/RW` のみ
   - edge `types` は reason type の出現順重複除去と exact 一致
   - phenomenon は全 edge type から再導出した値と一致
   - WW/WR/RW ごとの version field 有無が production と一致

   成果物影響: production が生成できない anomaly が qualifying rejection として P6 receipt と terminal projection を取得できる。

2. [reflux_formal_consumer.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:942) は `verify` schema と `integrity.clean` の公開導出関係を検査していない。

   `stats` を完全に省き、`integrity={"clean": true}` だけにしても現在の連言を通る。余分 key、非ゼロの `orphan_reads` と `clean=true` の矛盾、不正な `permutation_violation_details` も無視される。段 4 の「untyped JSON の schema と導出関係を再検査する」という条件を満たすには、`trace_dir` 除去後の verify、stats、integrity、permutation details の exact key 集合と、`clean=true` が公開する違反 counter/detail との整合を閉じる必要がある。terminal 外枠の exact gate を求める所見ではない。

   成果物影響: malformed verify payload に対して formal receipt、evidence root、report/lifecycle reference が発行される。

3. [dsg.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:524) は理由順が process 間で決定的ではなく、[s4-adjudication.md:45](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s4-adjudication.md:45) の根拠が偽である。

   同じ 2 transaction 入力で、二つの共通 WW key の順が `PYTHONHASHSEED` により `["b","a"]` と `["a","b"]` に変わり、anomaly digest はそれぞれ `4a0f6a...` と `b9fb0f...` になった。consumer で list を正規化するのではなく、producer の集合走査を `sorted(...)` にして report 生成時点の順序を固定するのが再照準先である。

   成果物影響: 同一 trace が process ごとに別 constraint class、result record、receipt/reference digest を生みうる。

4. [test_reflux_formal_consumer.py:1055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:1055) の B-060-M8 負例は単一理由性を満たさない。

   `total_cycles=True` と `anomaly_count=True` を同時に置くため、total 側だけを `isinstance(..., int)` へ緩めても anomaly_count の exact-type gate が拒否する。`total_cycles=True, anomaly_count=1` へ再照準すれば、`True == 1` により対象 gate だけを検査できる。

   成果物影響: 現状の mutation 成果物では M8 を KILLED と登録できず、型 gate の認定が虚偽になる。

5. [s4-adjudication.md:235](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s4-adjudication.md:235) の「材料レポートは変わらない」は誤り。

   [p3_autonomous_workload_trial.py:3618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/p3_autonomous_workload_trial.py:3618) は変化する `formal_receipt_sha256` と `evidence_root_sha256` を report に格納し、同 projection は lifecycle と [trial_registry.py:6311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/trial_registry.py:6311) の acceptance receipt に伝播する。正しくは「cell の測定材料と certified 選択集合は不変だが、report artifact 全体、lifecycle terminal、acceptance receipt は変わる」である。

   成果物影響: report、journal/lifecycle、acceptance receipt の bytes と digest は変わるが、測定 cell と `OriginSealed` event payload は変わらない。

## 4 語の取り残し

- `candidate_attributable`

  旧 WAL field の唯一の executable hit は [test_reflux_formal_consumer.py:944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:944) の legacy 負例であり意図的。`candidate_attributable_rejected` は source-closure policy の別 fieldとして、fixture builder、source-closure production、`test_reflux_source_closure.py` に計 4 live hit があり、取り残しではない。

- `truncated`

  旧 FC07 field の唯一の executable hit は同じ legacy 負例の [test_reflux_formal_consumer.py:945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:945)。他の live hit は WAL tail、critic diagnostic、sort oracle、proposal bundle、acceptance output など別概念である。

- `witness_class_sha256s`

  executable hit は [test_reflux_formal_consumer.py:946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:946) の legacy 負例 1 件だけ。

- `wal.abort.payload.witnesses`

  production/test executable hit は 0。残るのは `docs/decisions.md`、archive worklog、過去 insight の歴史記録だけである。

したがって変更後に旧名前を前提に残る live production consumer は 0 件である。

## 所有外への波及

参照関係から得た焦点 test 集合は段 4 の 12 file と一致する。

| test file | 到達関係 |
|---|---|
| `test_ccbench_spawn_sites.py` | `reflux_source_closure.py` の process-site repo scan |
| `test_p3_autonomous_workload_trial.py` | source closure・builder を直接 import、P3 から formal consumer を実行 |
| `test_reflux_formal_consumer.py` | consumer・source closure・builder を直接 import |
| `test_reflux_origin_artifacts.py` | builder 出力を直接使用 |
| `test_reflux_origin_binding.py` | source closure・builder を直接使用 |
| `test_reflux_origin_client.py` | formal result・builder・`OriginSealed` commit を直接使用 |
| `test_reflux_origin_fixture_builder.py` | builder と baseline 全 entry |
| `test_reflux_origin_topology.py` | builder 由来 recovery envelope |
| `test_reflux_originless_compatibility.py` | P3 test helper を経由する間接 consumer |
| `test_reflux_result_evidence.py` | builder と golden 4 pin |
| `test_reflux_source_closure.py` | source closure・builder を直接使用 |
| `test_trial_registry.py` | formal projection・builder・acceptance receipt を直接使用 |

名指しされた production consumer はすべて対応 test を持つ。

- `p3_autonomous_workload_trial.py` → `test_p3_autonomous_workload_trial.py`
- `trial_registry.py` → `test_trial_registry.py`
- `reflux_origin_client.py` → `test_reflux_origin_client.py`

12 file 外では `autonomous_trial_completeness.py` と `s8c_acceptance_receipt.py` が serialized projection の下流 consumer だが、変更された FC07 fieldや fixture builderを参照せず、projection schema/reason は不変である。旧/new pin literal の hitもないため、今回の差分だけで赤になる外部 test は見つからなかった。

## 変異 15 件の帰属判定

| id | 対象実在 | 帰属 | 落ちる実 nodeid |
|---|---|---|---|
| M1 | 実在 | 成立。reason だけ不一致 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_candidate_reason_with_valid_verify` |
| M2 | 実在 | 成立。verdict だけ不一致 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_candidate_verdict_with_valid_reason` |
| M3 | 実在 | 成立。dict 型は保ったまま clean だけ偽 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_dirty_integrity_with_valid_cycle` |
| M4 | 実在 | 成立 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_serializable_true_with_reject_verdict` |
| M5 | 実在 | 成立 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_certified_true_with_reject_verdict` |
| M6 | 実在 | 成立。型と total/count equality は通る | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_anomaly_count_different_from_list_length` |
| M7 | 実在 | 成立。count/list relation は通る | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_truncated_verifier_anomaly_list` |
| M8 | 実在 | **不成立**。anomaly_count exact-type gate が先に残る | 現在の `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_boolean_cycle_counts` は mutant でも落ちる |
| M9 | 実在 | 成立。counter は 2 件に整合し、先頭 digest も一致 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_two_anomalies_even_when_first_digest_matches` |
| M10 | 実在 | 成立。ring 以外の構造と digest は更新済み | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_ring_position_mismatch_with_matching_digest` |
| M11 | 実在 | 成立。anomaly exact-key gateだけに違反 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_anomaly_extra_key_with_matching_digest` |
| M12 | 実在 | 成立。空 dict の digestまで record/ledgerへ反映 | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_empty_anomaly_with_matching_digest` |
| M13 | 実在 | 成立。record と全 ledger member を同じ別 digestへ更新して FC04/FC09を通す | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_witness_digest_mismatch_after_other_gates_pass` |
| M14 | 実在 | 成立。productionのみ、fixtureのみ、両方の変異を runtime-path検査または literal assert が捕捉 | `orchestrator/tests/test_reflux_source_closure.py::test_positive_fixture_validates_all_issuance_checks` |
| M15 | 実在 | 成立。全 baseline entry の独立 exact 比較 | `orchestrator/tests/test_reflux_origin_fixture_builder.py::test_baseline_schema_and_every_entry_match_independent_recalculation` |

M8 の再照準案は既存 nodeid の入力を `total_cycles=True, anomaly_count=1` にすること。このとき基準実装は total の exact-type gate で落ち、`isinstance(True, int)` mutant だけが後続 equality を通る。

## fixture と production 形の突き合わせ

[fixture builder:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/reflux_origin_fixture_builder.py:414) と [report.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/report.py:96) を比較した。fixture literal 自体に差はない。

- abort payload: `reason`, `build_attempt_id`, `build_admission_receipt_sha256`, `verify`, `workload` — production `_abort()` と一致
- verify: `verdict`, `certified`, `serializable`, `stats`, `integrity`, `anomaly_count`, `total_cycles`, `anomalies` — production の `trace_dir` 除去後と一致
- stats: `txns`, `reads`, `writes`, `keys`, `edges`, `abort_reasons` — 一致
- integrity: `clean`, `orphan_reads`, `version_dups`, `dup_txids`, `genesis_commits`, `missing_txids`, `write_version_mismatch`, `malformed_keys`, `framing_violations`, `framing_violation_details`, `lock_coverage_violations`, `write_intent_violations`, `permutation_violations`, `permutation_violation_details`, `notes` — 全 15 key 一致
- permutation details: `counts`, `sample`, `unknown_reason_sample` — 一致
- counts: `size-changed`, `rcdptr-set-changed`, `unknown` — 一致
- anomaly: `phenomenon`, `length`, `cycle`, `edges` — 一致
- edge: `from`, `to`, `types`, `reasons` — 一致
- reason: `type`, `key`, `u_ver`, `v_ver` — optional keyを含む production 形
- `types=["rw"]` と reason `type="rw"` は [model.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:347) の `WW="ww"`, `WR="wr"`, `RW="rw"` と一致

`sample=[]` は正しい空形だが、非空 sample item の `observation` と thread hint 形はこの fixtureでは正例になっていない。fixture の不一致ではない。

## scope 外だが real

- D1715 の terminal outer exact shape、重複、root shadow は未閉包。裁定パッケージ候補のまま。
- production result-evidence producer と共有 constraint-class 発行規則は依然不在。端から端までの本番閉包ではない。
- `Integrity.clean()` は proof-surface と commit-witness 状態も使うが、それらは `result_to_dict()` に全て出ていない。公開 counter の矛盾は今回閉じられるが、clean 全体を独立再計算するには verifier evidence schemaまたはproducer境界の別裁定が必要。
- occurrence txidを含む digestを「class」と呼ぶ意味、および同一 reason の重複扱いは段 4記載どおり別裁定候補。

## refuted

- baseline と golden pin の誤計算、raw長の変化は否定した。全値が独立再計算と一致。
- 変わるべき entry の取り残し、変わるべきでない entry の巻き込みは否定した。
- fixture verify payload と production `result_to_dict()` の key差は否定した。
- 旧4語を読む live production箇所は否定した。残る旧形は意図的legacy負例だけ。
- 第三の operational pin は否定した。旧/new digest literalはbaselineとgolden file以外にない。
- M1〜M7、M9〜M15の単一理由性疑いは否定した。M8だけ不成立。
- 新規test file、`check_docs.py`変更、docs invariant変更、process-site増減はない。commitは既存7 fileだけで `git diff --check` も空だった。

## 総括

pin 7 entry、golden 4値、raw長1848は正しい。  
旧fieldのlive取り残しと焦点12 file外の未検査consumerは見つからない。  
must-fixはanomaly導出関係、verify内部schema、producer順序決定性、M8帰属、成果物影響記述の5件。  
fixture形とledger eventは正しいが、report/lifecycle/acceptance receiptは不変ではない。