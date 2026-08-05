# 段 2 実装プラン

結論として、現行の `MAX_APPROVED_GENERATIONS = 1` を維持する範囲なら実装可能である。行番号は現行 tip `cfda4abe` 基準であり、追記後は関数名を anchor とする。以下は静的読解による計画であり、pytest の実測や緑判定は行っていない。

## 1. 編集点

| ファイル・現行行 | 編集内容 |
|---|---|
| [orchestrator/campaign/p3_s4_loop.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:241) | `diffq_variant_id()` は変更しない。`record_diff_reject()` 終端の `:271` 後へ `CriticIdentityProjection` と `make_critic_identity_projection()` を追加する。 |
| `orchestrator/campaign/p3_s4_loop.py:276-294` | `make_critic_digest()` に keyword-only の `identity_projector` を追加し、`render_rejections()` へ渡す。既定値 `None` は既存 caller の生 ID 描画を維持する。 |
| [orchestrator/critic/digest.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:556) | `render_rejections()` に任意の構造化 projector を追加する。文字列置換ではなく、各 dataclass field の描画直前に射影する。 |
| `orchestrator/critic/digest.py:583-585` | verify-red の `variant`、`src_token` を射影する。 |
| `orchestrator/critic/digest.py:624-631` | liveness の `variant`、`src_token` に加え、`extra` 内の `build_attempt_id` と `build_admission_receipt_sha256` を射影する。 |
| `orchestrator/critic/digest.py:642-649` | diff-quarantine の `variant`、`src_token` を射影する。 |
| `orchestrator/critic/digest.py:673-691` | 非 stock の verify-abort `variant` を射影する。 |
| [orchestrator/campaign/p3_autonomous_workload_trial.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:917) | auditor declassification の versioned policy 定数と、payload 値を SHA-256 で束縛する会計 helper を追加する。`_invoke()` の role-attempt event に `declassifications` を記録する。provider payload の key は増やさない。 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:989-1012` | auditor skip event は provider に開示していないため `declassifications: []` とする。 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:1696-1712` | `generation_record["harness"]` には実 ID を残す。その後 campaign WAL から projector を作り、critic payload の `harness_result.variant` と再描画した digest だけを射影する。 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:1700-1701` | 既成 digest テキストの置換はしない。digest artifact がある場合、同じ WAL から `make_critic_digest(..., identity_projector=...)` を再実行する。 |
| [orchestrator/campaign/autonomous_trial_completeness.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/autonomous_trial_completeness.py:183) | `declassifications` がある event の形、policy ID、pointer、value hash を検証する。旧 v2 report の受理集合を狭めないため、field 欠落は legacy として許す一方、現 producer が必ず発行することは producer test で固定する。 |
| [orchestrator/tests/test_p3_autonomous_workload_trial.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:146) | `_RecordingFixture` に既存 `payloads` を残したまま `payload_bytes` を加え、`A._canonical_json_bytes(payload)` を provider 呼出し直前に保存する。wire を指定できる coder fixture を追加する。 |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py:771-846` | 既存 planner/coder/critic key-set assert を維持し、auditor の exact key set も追加する。関係テスト、declassification 会計テストを直後に追加する。 |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py:95-132` | `_fake_drive_with_finite_metrics()` が no-build campaign に任意の「admitted digest」を置く旧 fixture を廃止する。このテストは metrics 射影だけを担当させる。 |
| [orchestrator/tests/test_critic.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:441) | verify/liveness/diff/verify-abort と liveness provenance extra を一つずつ異なる sentinel で埋め、全射影点を検査する test を追加する。 |
| [orchestrator/tests/test_p3_s4_loop.py:695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:695) | WAL 初出順、campaign reset、append 後の既存 label 安定性、label から実 ID を引けること、WAL bytes 不変を検査する。 |
| [orchestrator/tests/test_autonomous_trial_completeness.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_autonomous_trial_completeness.py:208) | account が存在する場合の正例と、pointer/policy/value hash 改変の拒否例を追加する。legacy fixture は field なしのまま受理されることも固定する。 |
| [orchestrator/tests/test_reflux_ir.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_reflux_ir.py:14) | test-only の複合 schema identity 定数と、その二つの preimage を計算する helper/test を追加する。 |
| `docs/decisions.md:9040` | 次の空き番号、現 tip なら D186 を追記する。 |
| `docs/phase3.md:478-487` | U-1〜U-3 実装済みの限定を記録する。ただし D114 cap=1、P2 全体未充足、cap-lift 不可は維持する。 |
| `docs/worklog.md:3269` | 親による baseline-red、実装後受入、mutation 実測が終わった時点で結果を追記する。 |

次のファイルは意図的に編集しない。

- `orchestrator/campaign/pipeline.py:87-93` の `variant_id()`。
- `orchestrator/campaign/p3_s4_loop.py:241-271` の WAL ID と WAL record。
- `orchestrator/campaign/reflux_ir.py`。
- `orchestrator/campaign/trigger_gate_binding.py:98-108` の 32 点 universe。
- `orchestrator/tests/reflux_ir_expected_goldens.py:24-57`。規範変更なしに golden を更新してはならない。
- `s3-lensA.md`、`s3-lensB.md`、`s4-adjudication.md`。いずれも履歴・裁定正本として不変。

新規 production ファイルは不要である。

## 2. U-1: critic 境界の射影

### ラベル規則

`make_critic_identity_projection(layout, fallback_variants=...)` は次の規則にする。

1. `wal.read_records(layout)` の正規順で `STAGE_BUILD_START` を読む。
2. `src_token == "stock"` の record は候補 ordinal に数えず、critic でも `stock` と表示する。
3. 非 stock または `src_token` 欠落の候補について、実 `variant` の campaign 内初出順に `candidate-0001`、`candidate-0002` …を振る。
4. 同じ build-start に属する値は次へ射影する。

   - `variant` → `candidate-0001`
   - `src_token` → `candidate-0001/source`
   - `build_attempt_id` → `candidate-0001/attempt`
   - `build_admission_receipt_sha256` → `candidate-0001/admission`

5. replay された同じ `variant` は最初の label を再利用し、append により既存 label を振り直さない。
6. no-build fixture のように WAL がなく `outcome.variant` だけがある場合は、`fallback_variants` の出現順で同じ形式を発行する。
7. 空文字列と `None` はそのまま、非空の未知 ID は critic payload 構築時に拒否する。生値へ fallback しない。
8. projector は `_run_workload()` の campaign ごとに作り、module-global cache を持たない。

campaign を跨いだ label は意図的に安定させない。同じ実 ID でも各 campaign の最初なら `candidate-0001` になる。trusted 側では `(campaign_id, label)` をキーにするため再解決可能だが、critic へ campaign ID と実 ID の対応表は渡さない。

campaign 内では WAL 初出順が不変なので、再起動・再描画後も同じ label になる。

### provenance から実 ID を引く経路

新しい秘密台帳は作らない。次の既存経路を正本にする。

1. `(campaign_id, candidate-N)` から同じ規則で N 番目の適格 `STAGE_BUILD_START` を選ぶ。
2. その `WalRecord.variant` と payload の `src_token`、`build_attempt_id`、receipt hash を得る。
3. 現 generation では `report.cells[].generations[].harness.variant` が同じ実 IDを保持する。
4. build 経路では `s8a_trigger_sweep_provenance.json` の iteration entry と `_wal_attempt_provenance()` でも実 variant/build attempt を照合できる。

これは campaign-local provenance であり、未発行の `origin_id` に束縛した「origin scope ID」ではない。`origins: []` の現状で後者を名乗ってはならない。

### critic へ届く候補由来文字列の全棚卸し

| 観測面 | 現行 source | 処置 |
|---|---|---|
| `harness_result.variant` | `p3_autonomous_workload_trial.py:1706` | `project("variant", ...)`。 |
| verify-red の `variant` / `src_token` | `digest.py:583-585` | 両方を射影。 |
| liveness の `variant` / `src_token` | `digest.py:624-627` | 両方を射影。 |
| liveness `extra.build_attempt_id` | `pipeline.py:713-722` → `digest.py:630-631` | `candidate-N/attempt`。S 由来ではないが、run ごとの乱数差を sink から除く。 |
| liveness `extra.build_admission_receipt_sha256` | 同上 | source evidence を含み 32 点で識別子になり得るため `candidate-N/admission`。親 brief が見落としているチャネルである。 |
| diff-quarantine の `variant` / `src_token` | `digest.py:642-645` | 両方を射影。現 trigger 経路の src は通常空。 |
| verify-abort の `variant` | `digest.py:673-690` | 非 stock だけ射影。 |
| screening | `digest.py:636-640` | 現 renderer は `genome` しか描かず、`variant`/`src_token` は出さない。さらに `make_critic_digest()` は `load_screen_rejections()` を渡していない。射影点はない。 |
| green digest の genome/flags | `digest.py:490-515` | trigger axis では固定 genome で P に属するため維持。 |
| verdict、anomaly、integrity、liveness reason、rc/commits/aborts、workload、metrics | `digest.py:586-671`、`:684-690` | 公開観測 P と定義し維持する。 |
| diff subtype/reason/region/marker/evidence | `digest.py:646-667` | canonical 32-wire の auditor reject では公開された code/count。非 canonical coder text の `sha256_12` evidence は今回の S domain 外であり、広いコード候補非干渉の残余として記録する。 |
| `trigger_gate_binding_commitment` | raw outcome | `harness_result` の closed projectionにそもそも入らない。 |
| coder wire、working diff | proposal/raw artifact | critic payload には入らない。auditor だけ U-2 の例外。 |

## 3. 決定 (4): 関係的非干渉検査

### S と P

Secret `S` は generation 1 の coder が返す正準 5-bit wire、すなわち `{"0","1"}^5` の32点とする。

S の決定的派生物も secret 側に含める。

- `emit_predicate(parse_wire(S))`
- `working_diff` と `diff_digest`
- `src_token`
- `diffq_variant_id` / build `variant_id`
- build admission receipt hash
- trigger binding commitment

公開入力 `P` は次を固定する。

- workload=`ycsb-a`、generation=1、同一 descriptor/binding。
- schema、pilot scope、scientific claim、attempt/stop policy。
- planner input/output、coder input、baseline metrics、empty whiteboard。
- harness の `outcome`、`verdict`、metrics、`stop_reason`、iteration、ran。
- digest の公開 rejection class、reason、genome、workload、counts。
- 比較に乱数が入る場合は同じ random coins とみなす。今回の no-build fixture は乱数を使わない。

### fixture harness

`orchestrator/tests/test_p3_autonomous_workload_trial.py` に一つの test node を置く。

`test_role_sink_bytes_are_indistinguishable_except_auditor_declassification`

構成は次のとおり。

1. `_RecordingFixture` を継承した coder fixture に wire を注入する。generation は全 run で 1 のままにし、P を変えない。
2. 32 wire それぞれについて、fresh `run_root` で同じ

   `run_trial(provider_kind="fixture", do_build=False, ...)`

   を実行する。既存の injected `drive` と `preview` を使い、新しい driver は作らない。
3. `preview` は S から canonical predicate、working diff、SHA-256 digest を作る。他 field は一定にする。
4. `drive` は outcome/metrics/stop reason を一定にし、variant だけを

   `diffq_variant_id(fixed_genome, emit_predicate(parse_wire(S)))`

   とする。raw digest marker には variant/src-token sentinel を書く。
5. test では `make_critic_digest` を structure-aware fake renderer に差し替える。baseline はこの関数を呼ばず raw marker を読むが、実装後は projector を渡して再描画する。この差で digest handoff も実際に試験する。
6. `_RecordingFixture.invoke()` で provider 呼出し直前の `A._canonical_json_bytes(payload)` を保存する。

assert は dict でなく bytes に対して行う。

- planner: 32 run の `payload_bytes` の集合サイズが 1。
- coder: 同じく 1。
- auditor: 生 bytes は32通り。JSON を decode し、テスト側の独立な literal set `{"/working_diff", "/diff_digest"}` だけを除去して再 canonicalize すると集合サイズが1。それ以外の差は失敗。
- critic: U-1 後は全32 run の bytes 集合サイズが1。
- trusted report の raw `harness.variant` は32/32 distinct のまま。射影が WAL/provenance まで侵食していないことも assert する。

### baseline で赤くなることの実証手順

恒真化を避けるため、実装は次の順に分ける。

1. `_RecordingFixture` 拡張と上記関係テストだけの patch を `cfda4abe` に適用する。
2. 親が計算ノードへ当該 nodeid だけを dispatch する。
3. planner/coder と auditor の限定差 assert を通過した後、最後の

   `len(set(critic_sink_bytes)) == 1`

   で失敗することを記録する。
4. 静的な期待値では、wire `00000` と `11111` の raw ID はそれぞれ `diffq-bf7e87fe70c0` と `diffq-ed02320290e3` で異なる。全32点も既存式では一意である。
5. 失敗記録後に U-1 production patch を重ね、同じ nodeid を再実行する。

テストに `xfail`、baseline 分岐、`if projection_available` は入れない。baseline-red と実装後の受入は同一 test bytes を使う。

## 4. U-2: auditor declassification 会計

provider payload の値と key は維持し、attempt event に次の機械可読 record を付ける。

```json
{
  "policy_id": "t244-auditor-diff-declassification/v1",
  "policy_sha256": "<policy object の canonical SHA-256>",
  "disclosures": [
    {
      "json_pointer": "/working_diff",
      "transform": "identity",
      "value_sha256": "<実 payload value の canonical SHA-256>"
    },
    {
      "json_pointer": "/diff_digest",
      "transform": "sha256-hex-of-/working_diff",
      "value_sha256": "<実 payload value の canonical SHA-256>"
    }
  ]
}
```

policy 定数には次を literal で固定する。

- `source_class = "candidate-wire"`
- `current_precondition = "raw-ir-equals-effective-ir/v1"`
- `sunset_trigger = "reflux-control-separates-raw-and-effective-ir/v1"`
- successor の `working_diff_source = "independent-canonical-emitter-from-raw-ir/v1"`
- successor の `allowed_json_pointers = ["/working_diff"]`
- successor の `forbidden_json_pointers = ["/diff_digest"]`

`_invoke()` は auditor を provider に渡す前に account を作るため、response が invalid でも開示は記録される。pre-audit で auditor 自体を呼ばない場合は空配列である。

検査は次の二層にする。

- producer test: 現行の全 auditor attempt が account を持ち、payload の実値 hash、二つの pointer、policy hash が一致する。
- completeness test: account が存在する場合の closed shape と改変を検査する。旧 v2 report の field 欠落は legacy として許し、親 brief の「現行受理集合を狭めない」を守る。

rollback 条件は散文コメントだけにせず、policy 定数と exact test の双方へ置く。reflux-control 実装 wave ではこの test が期待値更新を要求し、`diff_digest` を successor の許可集合へ残す変更を黙って行えない。

## 5. U-3: schema identity

production は一切変更せず、`test_reflux_ir.py` の検証層で次の二要素を固定する。

1. `orchestrator/campaign/reflux_ir.py` 全 source bytes の SHA-256。
2. `_validated_golden_assignments()` が確認した `EXPECTED_CASES` の32 tuple nodeについて、各 node の正確な source bytesを行順に連結した SHA-256。

現 tip の静的値は次である。

- emitter source: `3d9cdca1fca57b1aef58865ee0f6ac3fd03bb5794ad4dbb867796db881eef463`
- golden 32 rows: `69d8274fa03829d89dd706f7a0bb16d52ea71b608c51f5db5f5cdb1ead497165`

`EXPECTED_IR_SCHEMA_IDENTITY` はこの二値を literal で持つ。期待値を実測値から同じ test 内で組み立ててはならない。

追加 nodeid は次とする。

`orchestrator/tests/test_reflux_ir.py::test_ir_schema_identity_binds_emitter_source_and_32_golden_rows`

既存の

`test_golden_has_no_production_import_and_production_has_no_golden_consumer`

は無変更で残す。production は golden を import せず、golden 側も production を import/executeしない。

全 source bytes を identity とするため、コメントだけの変更でも identity は変わる。これは behavior hash ではなく「emitter source identity」という U-3 の選択をそのまま実装した保守的な契約である。

## 6. D96 手続

候補の build/certify/reject 集合は変えない。`diffq_variant_id()`、`pipeline.variant_id()`、WAL、proof chain、32 predicate の受理集合も不変である。

一方、critic recipient 境界では「許される値」が raw candidate ID から campaign-local label へ狭まる。また U-3 に新しい schema identity gate を追加する。したがって公式 candidate 集合は不変でも、境界 acceptance policy は変わると判定し、D96 を保守的に適用する。

新 D、現 tip なら D186 の骨子は次とする。

1. U-1〜U-3 のユーザー裁定を authority とする。
2. WAL/provenance は実 ID、critic sink だけ opaque label とする。
3. label の初出順、stock 除外、campaign-local reset、再開安定性、逆引き経路を規範化する。
4. auditor の現開示を explicit declassification とし、successor 条件を固定する。
5. IR identity を `emitter-source-sha256 + independent-32-golden-rows-sha256` とする。
6. candidate accept/reject 集合と D51 WAL identity は変えない。
7. D114 cap=1 を維持し、この実装を cap-lift や D121 P2 全体の充足根拠にしない。
8. keyed hash、WAL ID 変更、critic trusted 化、字面 tripwire、production の golden import を却下する。
9. test-only patch が baseline critic bytes を赤にした実測を decision evidence に記録する。

同一変更単位で更新する境界 test は次である。

- `test_p3_autonomous_workload_trial.py:803-829`: planner/coder/auditor/critic の exact key set。
- 同ファイル新規関係 test: 許可 field の値依存。
- `test_critic.py:441` 以降: 全 renderer identity channel。
- `test_p3_s4_loop.py:695` 以降: WAL ID 不変・label 順序・campaign scope。
- `test_reflux_ir.py:216-257`: production/golden 独立性と複合 identity。
- `test_autonomous_trial_completeness.py:208` 以降: declassification account。

## 7. 既存テストへの波及予測

### 実装が正しく、fixture/期待値が古いもの

- `test_p3_autonomous_workload_trial.py:95-132` の `_fake_drive_with_finite_metrics()` は、no-build の非 admitted layout に任意の描画済み digest を置いている。structured re-render 後は不正な fixture なので削除または digest 非生成へ直す。
- 同ファイル `:771-846` は auditor key set を検査していない。既存 assert を弱めず auditor exact set を足す。
- attempt event を exact fixture 化する新しい test では `declassifications` の追加に追随する。

### 赤くなれば実装誤りと判断する既存テスト

- `orchestrator/tests/test_p3_s4_loop.py::test_diffq_variant_id_deterministic_and_proposal_sensitive`  
  WAL ID を変えた、または projector を producer 側へ置いた誤り。
- `orchestrator/tests/test_campaign.py::test_variant_id_deterministic_and_sensitive`
- `orchestrator/tests/test_campaign.py::test_trigger_fixture_has_32_unique_predicates_source_bytes_and_variant_ids`  
  build variant の preimage を変えた誤り。
- `orchestrator/tests/test_critic.py::test_load_rejections_reads_verify_red_only` の `variant/src_token` assert  
  loader/WAL を匿名化して trusted provenance を壊した誤り。
- `orchestrator/tests/test_critic.py::test_render_rejections_liveness_hints_and_other_counts`  
  公開 failure reason/count まで消した誤り。
- `orchestrator/tests/test_p3_s4_loop.py::test_make_critic_digest_reflux_off_drops_red_section`  
  reflux on/off の合流点を変えた誤り。
- `orchestrator/tests/test_reflux_ir.py::test_golden_has_no_production_import_and_production_has_no_golden_consumer`  
  production から golden を参照した誤り。
- `orchestrator/tests/test_reflux_ir.py::test_all_32_predicates_match_independent_golden_byte_for_byte`  
  schema identity 追加に乗じて emitter/golden の規範値を変えた誤り。
- `test_p3_autonomous_workload_trial.py:814-829` の既存三 role key set  
  account を provider payload に混ぜるなど、recipient schema を不要に変更した誤り。
- `test_p3_autonomous_workload_trial.py:2591-2597` の report top-level exact set  
  declassification を新しい top-level report field にした誤り。本計画では role event 内なので不変。

上記以外の既存 test に期待値変更は予測しない。`render_rejections()` と `make_critic_digest()` の projector は opt-in であり、既存 caller の既定描画を変えないためである。

## 8. 変異事前登録

以下は「正しい実装 → mutant」の `old→new` である。いずれも所有範囲内で発火し、外部 driver の import や既存ハッシュの wire 字面化に依存しない。

| # | 対象 file:line | 変異 old→new | 殺す test nodeid |
|---|---|---|---|
| 1 | `p3_autonomous_workload_trial.py:1706` | `projection.project("variant", outcome.get("variant"))` → `outcome.get("variant")` | `test_p3_autonomous_workload_trial.py::test_role_sink_bytes_are_indistinguishable_except_auditor_declassification` |
| 2 | `p3_autonomous_workload_trial.py:1700-1711` | structured `make_critic_digest(...identity_projector=...)` → `digest_path.read_text(...)` | 同上 |
| 3 | `digest.py:583-585` | projected verify `variant/src_token` → raw fields | `test_critic.py::test_render_rejections_projects_every_candidate_identity_channel` |
| 4 | `digest.py:624-627` | projected liveness header → raw fields | 同上 |
| 5 | `digest.py:642-645` | projected diff-quarantine header → raw fields | 同上 |
| 6 | `digest.py:683` | `project("variant", s.variant)` → `s.variant` | 同上 |
| 7 | `digest.py:630-631` | projected attempt/receipt extra → raw `lv.extra` | `test_critic.py::test_liveness_projection_hides_attempt_and_admission_identity` |
| 8 | `p3_s4_loop.py:新設 projector factory` | campaign-local projector → module-global projector reuse | `test_p3_autonomous_workload_trial.py::test_role_sink_bytes_are_indistinguishable_except_auditor_declassification` |
| 9 | `p3_s4_loop.py:新設 WAL scan` | `wal.read_records(layout)` 順 → raw variant の辞書順 | `test_p3_s4_loop.py::test_critic_identity_projection_uses_wal_first_occurrence` |
| 10 | `p3_autonomous_workload_trial.py:新設 policy` | pointers `["/working_diff","/diff_digest"]` → `["/working_diff"]` | `test_p3_autonomous_workload_trial.py::test_auditor_declassification_account_is_exact_and_pins_sunset` |
| 11 | 同 policy | successor `forbidden_json_pointers=["/diff_digest"]` → `[]` | 同上 |
| 12 | `test_reflux_ir.py:新設 identity helper` | `_PRODUCTION_PATH.read_bytes()` または golden row bytes → `IR.SCHEMA_ID.encode()` / `b""` | `test_reflux_ir.py::test_ir_schema_identity_binds_emitter_source_and_32_golden_rows` |

mutation 実測は親が計算ノードで行い、各 mutant の第一失敗 nodeid、復元後の受入結果を記録する。

## 9. 却下・縮小すべき案

- P1 は「現行 cap=1 の campaign-local label」としてのみ成立する。実 `origin_id` に束縛した origin-scope ID という解釈は `origins: []` のため成立しない。
- P1 は将来の複数 generation に対する一般的非干渉証明にはならない。初出 label は候補の再出現・同一性パターンを保存し得るため、cap-lift 時は別裁定が必要である。
- P2 の test-layer oracle は成立する。production runtime gate 化は terminal report 経路を再び危険にするため却下する。
- P3 は literal 二要素として成立する。ただし「期待 hash を同じ test 内で観測値から生成する」案は恒真なので却下する。
- P4 は成立するが、親 brief の M2 は事実を一部誤認している。`digest.py:683` は screening ではなく verify-abort であり、screening は `:636-640`、しかも genome しか描かない。
- 親 brief は liveness `extra.build_admission_receipt_sha256` と `build_attempt_id` の描画も見落としている。U-1 を variant/src-token だけで終える案は却下する。
- keyed hash は32点 codebookで再識別でき、campaign 間 linkability も残すため却下する。
- WAL key の匿名化は D51 provenance を壊すため却下する。
- 描画済み digest への正規表現・substring 置換は、未知の identity channel を黙って通すため却下する。

## 総括

- 現行の単一 generation 制約下では、U-1〜U-3 と関係検査は実装可能である。
- 最大の技術的 risk は、campaign 初出ラベルが複数 generation では候補の同一性パターンを漏らし得る点である。
- したがって本 wave は D121 P2 全体や cap-lift の根拠にはできない。
- WAL、variant ID、raw report、provenance は実 ID のまま維持し、射影は critic sink 直前だけに置く。
- baseline-red は test-only patch を先に `cfda4abe` へ当て、同一 nodeid の critic bytes 比較で実測する必要がある。
- auditor の diff/digest は塞がず、値 hash 付きの明示的 declassification として会計する。
- U-3 は production と golden の相互 import なしに、source bytes と独立32行の literal hash で実現できる。
- 親 brief の誤りは `digest.py:683` を screening とした点と、liveness extra の識別子チャネルを落とした点である。
- さらに「origin scope ID」は現 authority では実装不能であり、正しくは campaign-local label と呼ぶべきである。
- 本回答は静的プランのみで、pytest・受入・mutation の実測結果は主張しない。