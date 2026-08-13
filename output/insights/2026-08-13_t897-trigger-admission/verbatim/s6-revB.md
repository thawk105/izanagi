## 所見 1 — block 外の BOM まで拒否し、裁定より受理集合を狭めている

severity: must-fix

根拠:

- 段 4 は「凍結 block 完全一致」または「hole だけ canonical emitter 出力」を受理し、block 外は scope 外としている: `s4-adjudication.md:55-68`。
- 実装は marker block が完全一致していても、source 内の任意位置に BOM があるだけで拒否する: `orchestrator/campaign/build_admission.py:257-268`。
- 追加テストの `N06-bom` は BOM を block 外へ置き、完全一致 block を意図的に拒否している: `orchestrator/tests/test_build_admission.py:359-361`。
- BOM は UTF-8 decode 自体には失敗しないため、`raw.decode()` という裁定済み処理からも導けない追加条件である。

成果物影響: 裁定上は受理される完全一致 block の source が `admission-error` となり、certified 選択が欠落し、WAL・レポートには receipt ではなく abort が残る。

## 所見 2 — 既存の正経路 fixture 2 nodeid が新 gate に先取りされて赤くなる

severity: must-fix

根拠:

`_write_materialized_trigger_source` は marker、`#if`、hole だけの縮小 frame を作り、凍結コメント群を欠き、`#else` 側も `true;` である: `orchestrator/tests/test_campaign.py:5361-5390`。したがって canonical hole でも `FROZEN_TEMPLATE_BLOCK_BYTES` の prefix/suffix に一致せず、`derive_build_admission` で拒否される。

静的に赤となる既存 nodeid は次の 2 件である。

- `orchestrator/tests/test_campaign.py::test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds`
  - `orchestrator/tests/test_campaign.py:5582-5627`
  - 期待する certified/build 2 回へ到達せず、pre-build abort になる。
- `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_crossed_materialized_predicate_and_mask`
  - `orchestrator/tests/test_campaign.py:5629-5665`
  - abort 自体は維持されるが、後段 mask 検査ではなく新 frame gate が先に発火し、期待 error が `trigger binding predicate...` から `trigger axis predicate...` に変わる。

ほかの旧 trigger 負例 10 nodeid は `pipeline._require_materialized_trigger_predicate` を直接呼ぶため、新 gate の影響を受けない: `orchestrator/tests/test_campaign.py:5393-5409`, `:5452-5579`。

成果物影響: このままでは段 6 受入が赤となる。赤を無視すると、source-bound binding と build receipt の統合経路を検証したという変異台帳・レビュー記録が事実と異なる。

## 所見 3 — 変異事前登録 M4/M6 と追加テストの単一帰属が実装形に存在しない

severity: must-fix

根拠:

- 裁定は M4 を「1 物理行制約削除」、M6 を「CR payload 保持処理削除」と登録している: `s4-adjudication.md:130-134`。
- 実装には独立した物理行数検査も CR payload 処理もない。空・複数行・CRLF・CR-only はすべて prefix/suffix または `hole not in _TRIGGER_EXPECTED_HOLE_BYTES` で拒否される: `orchestrator/campaign/build_admission.py:266-277`。
- `N07-nul` は NUL 検査を消しても、NUL を BEGIN marker ID 内へ入れているため marker pair 不整合が先に拒否する: `orchestrator/tests/test_build_admission.py:363-371`。
- `N03-commented-block` は block-comment visibility と骨格 token 残存検査の両方を消す個別変異で赤になり、片方専用 node ではない。
- BEGIN/END が逆順の負例がなく、`begins[0].start() >= ends[0].start()` の単独帰属もない: `orchestrator/campaign/build_admission.py:263-264`。
- `test_trigger_axis_semantic_validator_precedes_class_selection` は gate 削除時も後段 class rejection が発火し、診断文だけが変わる。DW-M03 の kill ではない: `orchestrator/tests/test_build_admission.py:558-567`。
- AST meta-test は呼出し形を pin するだけで受理集合の kill ではない: `orchestrator/tests/test_build_admission.py:581-617`。

個別検査への帰属が成立する nodeid は次のとおり。

| 変異・検査 | 単独帰属に使える nodeid |
|---|---|
| M2 require 再検査 | `test_runtime_admission_rechecks_trigger_axis_while_receipt_replay_does_not` |
| M3 outer strip | `test_trigger_axis_semantic_admission_rejects_noncanonical_block[tab-indent]`, `[outer-leading-space]`, `[outer-trailing-space]` |
| M5 mask 31 | `test_trigger_axis_semantic_admission_accepts_exact_emitter_bytes_without_binding[mask-31]` |
| M7 frame bytes | `test_trigger_axis_semantic_admission_rejects_frame_mutations[N01-marker-prefix]`, `[N02-marker-case]`, `[N05-mixed-newline]`, `[N09-disabled-if]`, `[N10-other-ifdef]`, `[N11-extra-if-block]`, `[N14-nested-block]` |
| M8 非 ENOENT | `test_trigger_axis_semantic_admission_rejects_non_enoent_read_failure` |
| M9 骨格 token | `test_trigger_axis_semantic_admission_rejects_frame_mutations[N04-marker-id-variant]`, `[N08-markers-deleted]` |
| M10 marker 一意性 | `test_trigger_axis_semantic_admission_rejects_frame_mutations[N13-second-case-varied-block]`, `[N15-duplicate-block]` |
| M11 pristine | `test_trigger_axis_semantic_admission_accepts_pristine_frozen_block` |
| UTF-8 decode | `test_trigger_axis_semantic_admission_rejects_frame_mutations[invalid-utf8]` |
| BOM reject | `test_trigger_axis_semantic_admission_rejects_frame_mutations[N06-bom]` |

帰属不成立は M4、M6、NUL、comment visibility、marker 順序である。

M1 の受理集合 kill は、frame 負例 15 parameter、noncanonical block 負例 8 parameter、`test_trigger_axis_semantic_admission_rejects_non_enoent_read_failure` の計 24 nodeid。precedence と AST meta-test は diagnostic/structural sensitivity に分ける必要がある。

成果物影響: このまま変異を KILLED と記録すると、実際には別 gate に先取りされた nodeidを当該検査の証拠として台帳へ載せ、proof chain と mutation matrix が虚偽になる。

## 所見 4 — `require_build_admission` の不正 `expected_source` 例外順序が変わった

severity: nit

根拠:

- 新しい `_source_map(expected_source)` は sealed body・policy 検証より前に実行される: `orchestrator/campaign/build_admission.py:790-808`。
- 不正な非 `None` 型だけを与え、ほかが正常なら、例外型と文言は従来と同じ `BuildAdmissionError("source は ... exact SourceEvidence ...")`: `orchestrator/campaign/build_admission.py:156-162`。
- 複数引数が同時に不正なら、従来の policy/body エラーより source 型エラーが先になる。
- `None` は従来 `_validate_admission_body` の `if expected_source is not None` を抜けたが、現在は exact-source error になる: `orchestrator/campaign/build_admission.py:731-742`, `:800`。
- 指定 7 test file に、この型・文言・順序を pin する nodeid はない。

成果物影響: production caller は事前に exact `SourceEvidence` を要求するため certified 値は変わらず、 malformed caller の最初の診断だけが変わる。

## 既存 fixture・赤集合の確認

対象 file を実際に扱う状況は次のとおり。

- `test_build_admission.py`: 新規 `_write_trigger_source` が対象 file を作る。既存 synthetic root は作らない。
- `test_buildcache_v2.py`: temporary `ccbench` directory は使うが対象 file は作らない。
- `test_campaign.py`: `_write_materialized_trigger_source` が対象 file を作る。上記 2 nodeid が赤。
- `test_s8a_trigger_sweep.py`: `_mk_template_dir` は対象 file を作るが quarantine 単体用。public admission fixture の root には対象 file がない。
- `test_build_site_gate.py`: temporary root に対象 file はない。coverage の login/suspect test は site gate が evidence 解決より先に止める。
- `test_s8b_floor_campaign.py`: synthetic git fixture は `anchor.txt` だけ。slow canary は実 submodule 由来の対象 file を持つが、正規 patch 経路なので semantic gate を通る。
- `test_p3_build_authority_cli.py`: temporary `ccbench` directoryだけで対象 file は作らない。

従って、新規テストを除く確実な赤集合は所見 2 の 2 nodeidである。

## import 循環・import 不変条件

所見ゼロ。

- import graph は `build_admission → axis_trigger_gating → pin` と `build_admission → reflux_ir → axis_trigger_gating → pin` で DAG。逆向き import はない。
- 新規 import はすべて relative sibling import であり、`test_campaign_import_invariant.py` の R-D は absolute sibling import だけを拒否する: `orchestrator/tests/test_campaign_import_invariant.py:963-983`。
- `emit_predicate` 32 回は pure な文字列生成で、filesystem・subprocess・乱数副作用はない: `orchestrator/campaign/reflux_ir.py:131-141`。
- import 時 `RuntimeError` は定数 drift／hole 重複時だけの決定的 fail-closed。不安定な外部状態には依存しない: `orchestrator/campaign/reflux_ir.py:57-58`, `orchestrator/campaign/build_admission.py:70-84`。

成果物影響: 現状の import 構造では certified 選択・レポート・台帳値は変わらない。

## 凍結 receipt bytes

所見ゼロ。

- `_ADMISSION_KEYS` は不変: `orchestrator/campaign/build_admission.py:583-587`。
- policy preimage、`GeneratorId`、`ReviewId` は不変: `orchestrator/campaign/build_admission.py:106-124`, `:516-524`。
- admission body と `receipt_sha256` の生成式は不変: `orchestrator/campaign/build_admission.py:709-722`。
- `validate_build_admission_receipt` は新 validator を呼ばず、WAL replay も source-less のまま: `orchestrator/campaign/build_admission.py:814-825`, `orchestrator/campaign/wal.py:1115-1129`。

同じ受理済み `SourceEvidence` に対する key 集合・body・`policy_sha256`・`receipt_sha256` は 1 byte も変わらない。

成果物影響: 既存 receipt の SHA、cache identity、WAL replay 値は維持される。

## 5 経路 + coverage/frequency

新 semantic validator 単体の判定はすべて accept である。

- coverage/frequency: template patch の pristine block は完全一致。instrumentation/misattr patch は block 外だけを変更する: `s8a_trigger_coverage.py:257-268`, `s8a_trigger_freq.py:147-153`。
- S8a stock: flag 0 でも pristine block なので semantic accept: `s8a_trigger_sweep.py:442-459`。
- S8a candidate: `quarantine` は入力を canonical emitter に正規化し、元 hole の 2-space indent を付けて書く: `p3_s4_loop.py:212-224`, `:226-240`, `:272-275`。結果は正確に `PREDICATE_HOLE_INDENT + emit_predicate(...)`。
- S1 direct comparison: `system_gate` / `ident_all` は同じ patch+quarantine 経路、他 configuration は trigger marker 不在の no-op: `s1_direct_comparison.py:534-571`, `:608-620`。
- S8b floor/oracle: どちらも `s1_direct_comparison.prepare_cell` を再利用する: `s8b_floor_campaign.py:1212-1257`, `s8b_oracle_driver.py:1433-1498`。
- extime calibration: template patch後に同じ quarantine を通す: `s1_verify_extime_calibration.py:336-364`。

ただし S8a stock は「semantic validator accept」と「後続の provenance class 受理」を区別すべきである。template patch 下の dirty evidence に capability がなければ、既存 class selection が別理由で拒否しうる。この点は新 validator の判定結果ではない。

## 後段を mask する検査

新 gate が発火すると次は走らない。

- pipeline の source-bound mask/predicate 検査: `orchestrator/campaign/pipeline.py:787-814`。
- legacy cache sidecar canonicality/current identity: `orchestrator/campaign/buildcache.py:892-915`, cache-hit call `:1576-1586`。
- v2 completion manifest/preimage/current admission identity: `orchestrator/campaign/buildcache.py:939-980`, cache-hit call `:1363-1370`。

## 性能

所見ゼロ。ただし実時間は未計測である。

実 source は 23,507 bytes。通常の `pipeline.evaluate` は derive、pipeline require、trace build require、perf build require の計 4 回 validator を通すため、1 evaluation あたり 94,028 bytesを Python loop で走査し、4 回 open/readする: `pipeline.py:768-778`, `:851-862`; `buildcache.py:1273-1277`, `:1538-1542`。

32候補でも走査量は約 3 MiBで、各候補の configure/build/trace/bench に比べ支配的とは考えにくい。cache hit でも4回発火するため、親が測るなら 23,507-byte実 sourceに対する `_cpp_block_comment_ranges` と derive+require の反復時間を分けて測れば帰属できる。

成果物影響: 想定規模では値は変わらない。極端に遅い場合だけ wall budget 超過によりレポート行が未完となる。

## 段 4 裁定との差分

- must-fix の差分は所見 1 の block 外 BOM 拒否。
- 裁定が要求した block bytes、32 emitter、pristine、marker 一意性、骨格 token、ENOENT/no-op、非 ENOENT reject、derive/require 結線、receipt replay 非結線は実装済み。
- N12 は段 4 で明示的に RP-2／scope 外: `s4-adjudication.md:96-100`。実装子が未実装とした判断は裁定どおりである。

## 総括

must-fix は3件です。実経路の canonical candidate・pristine characterization は semantic validator を通り、receipt bytesと import topologyも保全されています。一方、裁定外の BOM 拒否、既存 integration test 2件の確実な赤、M4/M6を中心とする変異帰属不能は、段6の受入・証拠台帳を閉じる前に解消が必要です。