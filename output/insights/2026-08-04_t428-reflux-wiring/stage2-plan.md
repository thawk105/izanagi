# [T-428] 段 2 実装プラン案

採用案は、`implementation` を廃止する wire-only の一括切替と、trigger 専用 `binding/v1` の導入である。P1・P3・P4・P5に賛成、P2は「mask→正準述語→materialize 済み source→SourceEvidence→variant/build cache」の鎖を同時に検証する条件付きで賛成する。

## 1. 新しい受理・binding 契約

coder proposal は次だけを受理する。

```json
{
  "coder": {
    "axis": "silo-backoff-trigger-gating",
    "wire": "10100",
    "justification": "...",
    "confidence": "high|medium|low"
  }
}
```

- `wire` は厳密な `str`、長さ 5、文字は `0|1` のみ。空白・改行・数値・bool・旧 `implementation` は拒否。
- 左から LSB-first で、順序は `axis_trigger_gating.py:50-51` の `lock-conflict / update-absent / readvali-tid / readvali-locked / node-vali`。
- `1=その要因で backoff`、`0=skip`。`kUnset=true` は coder に書かせず、凍結 emitter が常に付加する。
- 受理後の C++ は必ず `parse_wire → TriggerGateIR → emit_predicate` で作る。raw C++ の互換入口は残さない。
- 全 32 wire（`00000` を含む）を受理集合とする。

WAL・provenance・report が共有する binding は、次の exact closed schema とする。

```json
{
  "trigger_gate_binding": {
    "schema_version": "izanagi-trigger-gate-binding/v1",
    "ir_schema": "izanagi-trigger-gate-ir/v1",
    "mask": 5,
    "predicate_sha256": "<emit_predicate(IR) の lowercase sha256>",
    "source": null
  }
}
```

source 確定後は `source` を次の exact object に置き換える。

```json
{
  "src_token": "<SourceEvidence.src_token>",
  "source_bytes_sha256": "<SourceEvidence.source_bytes_sha256>"
}
```

`source` キー自体は常に必須とし、receiptless pre-build reject だけ `null`、build admission receipt を持つ `build_start` では object 必須とする。wire と mask を二重保存せず、wire は `encode_wire(TriggerGateIR(mask))` で復元する。

## 2. ファイル別編集計画

### 受理点・proposal schema・唯一経路化

- [projection_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/projection_guard.py:30)（30–31, 273–315）

  - Before: coder 共通 schema は必ず `{"axis","implementation"}`、`require_coder_value` だけで分岐し、値は無検査。
  - After: trigger 専用 mode（例 `coder_contract="trigger-wire"`）を追加する。この mode だけ required=`{"axis","wire"}`、optional=`{"justification","confidence"}` とし、`implementation` と `value` を unknown key として拒否する。
  - trigger mode と `require_coder_value=True` の併用は設定誤りとして拒否する。
  - key 閉包後に `parse_wire()` を呼び、固定 `RefluxIRError` のまま値域も閉じる。既定 mode は現状の implementation schema とし、sort/backoff の呼出しを無変更に保つ。

- [p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:54)

  - `54–76`: 凍結 `parse_wire` / `emit_predicate` と新 binding helper を import。
  - `101–109`: mutable `implementation: str` を `@dataclass(frozen=True)` の `wire: str` へ変更し、`__post_init__` でも `parse_wire` を実行。direct construction も受理点に数える。
  - `118–139`: coder 文字列用 blacklist gate から、trusted emitter 出力に対する内部 drift assertion へ格下げする。候補の受理集合をこの grep に依存させず、異常時は入力や mask を含まない固定エラーで停止する。
  - `349–402`: `_quarantine_and_audit` 冒頭で毎回 wire を再 parse し、正準 predicate を一度生成。それだけを `L.quarantine`、diff reject recorder、auditor digest に渡す。reject にも source-null binding を付ける。
  - `417–438`: `search_config["trigger_gate_binding_schema"]="izanagi-trigger-gate-binding/v1"` を追加し、spec 文言を wire-only に更新する。campaign ID が変わることは意図した epoch 分離。
  - `461–502`: `run_campaign(..., trigger_gate_binding=<candidate spec>)` を追加。dry-pass/reject/build の全 outcome に同じ canonical binding を載せる。
  - `503–530`: build 後は validated `build_start` binding を outcome にコピーする。duplicate は既存 WAL を再検証した後、その binding を回収する。
  - `571–601`: docstring と combined proposal loader を `wire` に変更し、trigger schema modeを使用。`implementation` fallback は置かない。
  - `604–670`: provenance entry に outcome と同一の `trigger_gate_binding` を追加する。独立再導出せず完全一致を要求する。
  - `675–710`: `--preview-diff IMPLEMENTATION.txt` を `--preview-wire WIRE` に置換。preview も同じ parse/emitter helper を通す。
  - `783–801`: fixture C++ を wire（stock 相当なら `11111`）へ変更する。

- [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:190)

  - `190–197, 223–228`: runtime coder contract / gating spec を C++ から 5-bit wire へ変更。
  - `326–349`: parser の exact keys を `axis,wire,justification,confidence` とし、`parse_wire` で検査。旧 key と余剰 key は拒否。
  - `409–424`: fixture provider は世代ごとに wire を返す。
  - `562–580`: preview は trusted emitter 出力だけを quarantine へ渡す。
  - `1440–1448`: `dataclasses.asdict(coder)` が wire schemaを永続化することを固定。
  - `1473–1487`: harness outcome の binding を trial report に保持。
  - `1492–1501`: critic projection には binding・mask・wireを追加しない。I3 の開示境界を保つ。

### materialize・build cache 束縛

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop.py:161)

  - `161–221`: `render_hole` / `quarantine` は変更しない。trigger caller が正準 predicate だけを渡すことで materialize を唯一経路化する。
  - `234–251`: `record_diff_reject` に keyword-only optional binding を追加し、指定時だけ `build_start` payload へ複写する。未指定時の variant ID・payload key 集合・sort/backoff 挙動は現状どおり。

- 新規 `orchestrator/campaign/trigger_gate_binding.py:1–末尾`

  - `BINDING_SCHEMA`、lock key、payload key、exact validator を一か所に置く。
  - mask は毎 sink で strict `int` かつ `0..31` を再検査する。
  - `predicate_sha256` は `emit_predicate(TriggerGateIR(mask))` から再計算する。
  - producer helper は `SOURCE_REL` の marker/hole が一行であり、正準 predicate と byte-exact に一致することを SourceEvidence 確定時に検査する。
  - candidate-only/source-bound の二形以外、余剰・欠落 field、不正 SHA、入力を含む例外文を拒否する。
  - replay/admission が同じ validator を呼ぶ。WAL と artifact admission に別実装を作らない。

- [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/loop.py:96)

  - `96–110`: keyword-only `trigger_gate_binding=None` を追加し、lock marker と引数の有無を双方向照合する。
  - `153–174`: startup replay が binding を検証してから terminal skip を決める。
  - `181–208`: SourceEvidence 確定不能の receiptless `build_start` に source-null binding を付ける。
  - `216–237`: binding spec を `evaluate` に渡す。
  - `238–256`: evaluate 外例外の abort は active attempt の build_start binding に帰属させ、別 binding を再導出しない。

- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/pipeline.py:61)

  - `61–67`: `variant_id` は変更しない。
  - `435–452`: keyword-only binding spec を追加。
  - `554–614`: pre-build failure の `build_start` に source-null binding を記録。
  - `572–610`: current `SourceEvidence` と materialized hole を検証後、source-bound binding を生成。
  - `616–626`: `build_start` に source-bound binding を追加し、外側 `src_token`、build-admission receipt source、binding source の完全一致を要求。
  - `648–660` および env-contract 側 build 呼出し: binding が参照したものと同じ `src_tok` / `SourceEvidence` を trace・perf の両 cache 呼出しへ渡す。
  - `buildcache.py` 自体は変更しない。cache key は既に source-content `src_token` を含むため、mask の第二キーを増やさず、同一 evidence の使用を境界テストで固定する。

### replay・artifact admission・report

- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:584)

  - `584–593`: lock の binding schema marker を strict に読む helper を追加。未知 version は marker 無し扱いにせず拒否。
  - `606–713`: attempt topology に先立ち、新 trigger campaign の全 `build_start` に binding があることを検査。receiptless は `source:null`、receipt-bearing は source object と admission receipt/outer `src_token` の一致を要求。
  - `716–747`: `replay` が state 復元前に binding validator を必ず通す。
  - `750–765`: `records_by_stage` による duplicate/outcome 回収も validator を迂回しない。
  - 後続 stage は `build_attempt_id` で binding 所有 start に帰属させ、payload を各 stage に複製しない。

- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/artifact_admission.py:424)

  - `424–495`: exact overlay 分類は先に行う現順序を維持。
  - `497–529`: exact pre-policy snapshot の歴史分類も維持。
  - `531–589`: post-policy trigger artifact では schema marker v1 と binding validator を必須化。marker 有りで binding 欠落・空 build-start 集合・source/mask/predicate 不一致なら admission reject。
  - `548–570`: binding source と `build_admission.source`、outer `src_token`、再計算 `variant_id` を同時に比較。
  - post-policy trigger で marker 欠落を「legacy」と推定しない。既知歴史物でなければ downgrade として拒否する。

- [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/layer3_report.py:87)（87–117, 205–217）

  - production edit は不要。WAL event payload 全体が report の variant events に複写されるため、raw mask を含む binding は既に formal report へ到達する。
  - 境界テストで byte-equivalent な binding の残存を固定する。段 3 が「nested event payload は report 契約に数えない」と裁定した場合だけ明示列を追加する。

### coder 定義・Codex parity・文書

- [.claude/agents/coder-v4-autonomous-trigger-gating.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/.claude/agents/coder-v4-autonomous-trigger-gating.md:3)（3, 9–14, 20–35, 62–115, 119–149）

  - 出力対象を C++ から 5-bit wire に変更し、bit 順・極性・`kUnset` が emitter 専権であることを記す。
  - output key を `implementation` から `wire` に変更。`tools: []`、fresh context、リーク遮断は不変。

- `orchestrator/codex_roles/manifest.json:820–947`

  - trigger role の説明・projection instruction・output schema を wire に追随。
  - `wire` に `type:string` と `pattern:"^[01]{5}$"`、`additionalProperties:false` を設定し、`implementation` を削除。

- `.codex/role-adapters/coder-v4-autonomous-trigger-gating.json:8,112–133,180–183`

  - source body snapshot、developer instructions、logical output schema を同じ契約へ更新。runtime blocked/static dormant は維持。

- `orchestrator/codex_roles/policy.py:331–339,461–480`

  - trigger role の semantic output gate で axis と exact wire を検査し、旧 implementation を拒否。

- `orchestrator/codex_roles/review_ledger.py:22,41,62,99–102,188`

  - source/description/schema/adapter bytes の各 pin を、agent 定義変更後の明示レビューを経て更新する。機械的な一括再生成だけで承認済み扱いにしない。

- `docs/phase3-s8a-trigger-runbook.md:55–93`

  - coder 出力例、preview CLI、proposal JSON、build 前確認を wire/binding v1 に更新する。

- `docs/decisions.md:末尾`

  - D96 に従う新 D を実装・境界テストと同一 commit に追加する。D96 自体は編集しない。

## 3. provisional 裁定 P1〜P5

- P1: 賛成。`implementation` byte照合方式は、自由 C++ parser を残し二重 schema・正規化差・エラー開示面を温存する。wire-only と trusted emitter の一経路に閉じるべきである。

- P2: 条件付き賛成。mask を `variant_id` に直接足さない判断は妥当。`variant_id:61-67` は materialized source の `src_token` を既に含み、32 mask の正準 emitter は相異なる source を作る。mask を足すと同じ source identity の二重会計と既存 ID 契約の分岐を生む。ただし、mask と source token を並べて記録するだけでは不足であり、正準 predicate hash、実 hole、同じ SourceEvidence、outer variant、両 build-cache 呼出しまで一鎖で照合することを採用条件とする。

- P3: 賛成。ただし「binding field が無いから歴史物」は不採用。positive lock marker と exact snapshot/overlay hash で epoch を判定する。

- P4: 変更必須。coder が C++ を返す契約のまま harness だけ wire を要求すると、正しい role 出力が常に拒否される。agent 定義・unattended supervisor・manifest・dormant adapter・policy・review pins を同一変更単位で追随させる。

- P5: 目的には賛成するが実行場所を補正する。`pegasus02` で pytest は直接走らせず、親が `tools/run_tests.py` を起動して計算ノードへ dispatch する。性能実測は行わない。`check_codex_agents`、`check_docs`、commit 後の provenance 監査も必要。

## 4. coder 契約の互換手順

互換は dual-read ではなく atomic epoch cutover とする。

1. agent 定義、runtime role contract、proposal loader、projection guard、manifest/adapterを同時変更する。
2. binding schema marker追加で campaign IDを変え、旧 campaignへの新 proposal resumeを防ぐ。
3. 旧 proposal JSON・旧 raw role output は歴史記録として bytes 不変で保存するが、新 loader では受理しない。
4. 移行が必要になった場合だけ、32 個の監査済み正準 predicateとの byte-exact 一致から wireへ変換する offline migration を別途行う。production loaderに C++ fallbackを置かない。
5. `projection_guard` は trigger modeだけ key集合を差し替えるため、sort/backoff の `implementation` / `value` schemaと衝突しない。

## 5. 歴史 artifact の判別

現在追跡されている旧 trigger loop campaign `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` は既存 overlay の exact bytes に一致し、従来どおり `overlay-denied` とする。binding 欠落を理由に分類を変更しない。

判別順は次で固定する。

1. exact overlay `(path/id, campaign.lock SHA, WAL SHA)`。
2. exact pre-admission snapshot。
3. post-policy artifact。
4. post-policy trigger では lock marker v1 必須。欠落は原則拒否。
5. legitimate な post-policy/pre-T428 trigger artifact が追加発見された場合だけ、個別の lock/WAL hashを grandfather 登録する。field absenceだけによる包括的 legacy扱いは禁止。

これにより、marker v1 があるのに binding が無い artifact、markerだけ削った downgrade artifact、binding 内の `source` fieldだけを落とした artifactはいずれも拒否できる。

## 6. D96 新 D の骨子

仮題は「[T-428] trigger-gating 候補受理を固定 5-bit wire と binding/v1 に閉じる」。番号は land 時の spool 順で採番する。

新 D には次を記録する。

- 背景: D149 leaf は監査済みだが production 到達性ゼロで、現行は任意 C++ を受理する。
- 決定: wire-only schema、凍結 parser/emitter 唯一経路、binding/v1、positive epoch marker。
- identity: mask は WAL/provenance/report に残すが `variant_id` へ直接追加せず、source evidence経由で束縛。
- history: exact snapshot/overlayだけを非遡及扱いし、field absenceを legacy判定に使わない。
- role contract: Claude agent・unattended contract・dormant Codex parityを一括変更。
- 却下案: C++ byte照合、dual schema、mask の直接 variant ID化、marker欠落の包括 legacy化、凍結 IR/golden/history bytes編集。
- 研究状態: 受理集合は32点へ縮小するが、`MAX_APPROVED_GENERATIONS=1` と cap-lift FAIL は不変。
- 境界テスト追随一覧と結果。D96 が却下した consumer AST 閉包 checker は新設しない。

## 7. 境界テスト

### `test_p3_s4_loop_trigger_gating.py`

既存 `1095–1186` の arbitrary implementation / blacklist 中心テストと、`1215` 以降の loader fixture を wireへ書き換える。

- `test_coder_proposal_accepts_exact_32_wires_only`: 32点だけを direct constructor/loaderで受理。
- `test_old_implementation_key_and_arbitrary_cpp_are_rejected_before_quarantine`: 旧 key・C++・余剰 keyを materialize 前に拒否。
- `test_all_32_wires_materialize_byte_exact_frozen_emitter`: quarantineへ渡る文字列を独立 golden 32点と照合。
- `test_wire_bit_order_is_gateable_reason_order_lsb_first`: bit順と極性を固定。
- `test_preview_and_run_share_canonical_materialization`: preview/build経路の diff bytes一致。
- `test_diff_and_auditor_rejects_record_candidate_binding`: pre-build rejectにも source-null binding。
- `test_drive_copies_same_binding_to_wal_provenance_and_outcome`: 独立再導出による差を禁止。
- `test_duplicate_recovery_revalidates_and_returns_existing_binding`: replay迂回を禁止。
- dry-pass、digest mismatch、fixture、proposal roundtrip の既存テストは wire fixtureへ追随。

### `test_p3_s4_loop.py`

- `96–167` の render/quarantineテストは無変更で維持。
- all-three-loader fixture の trigger coderだけ wireへ変更。
- `test_trigger_wire_schema_does_not_change_sort_or_backoff_coder_schema` を追加。
- `test_record_diff_reject_without_binding_preserves_legacy_payload` と、binding指定時だけ追記されるテストを追加。
- `diffq_variant_id` の既存 implementation基準は変更しない。

### 既存 leaf/構造検疫

- `test_reflux_ir.py`: production editに追随させず、17本・32 goldenを独立 oracleとして全走。凍結台帳は無変更。
- `test_diff_quarantine.py`: 38本を無変更で全走。構造 containment層が広いこと自体は維持する。

### 追加 consumer テスト

- `test_p3_autonomous_workload_trial.py`
  - `test_parse_coder_accepts_wire_and_rejects_implementation`
  - `test_fixture_provider_emits_only_wire`
  - `test_preview_uses_canonical_emitter`
  - `test_trial_report_keeps_binding_but_critic_projection_omits_it`

- `test_campaign.py`
  - `test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds`
  - `test_trigger_prebuild_abort_has_candidate_binding`
  - `test_replay_rejects_missing_mask_predicate_and_source_mismatch`
  - `test_records_by_stage_cannot_bypass_trigger_binding_validation`
  - `test_trigger_binding_does_not_enter_variant_id_preimage`

- `test_artifact_admission.py`
  - `test_new_trigger_artifact_requires_binding_schema_marker`
  - `test_new_trigger_artifact_rejects_missing_or_mismatched_binding`
  - `test_marker_absence_does_not_claim_unproven_history`
  - 既存 overlay/history fixture の classification と bytes が不変であること。

- `test_layer3_report.py`
  - `test_trigger_binding_survives_in_build_start_event_payload`

- `test_codex_agents.py`
  - agent source/manifest/adapter schema parity。
  - wire pattern、旧 implementation拒否。
  - `tools: []` と runtime blocked状態が不変。

## 8. 実装子2体の所有分割

APIを段4で先に凍結すれば、ファイル素集合は作れる。

子A「受理経路・schema・唯一経路化」:

- `p3_s4_loop_trigger_gating.py`
- `projection_guard.py`
- `p3_autonomous_workload_trial.py`
- `.claude/agents/coder-v4-autonomous-trigger-gating.md`
- `orchestrator/codex_roles/manifest.json`
- `.codex/role-adapters/coder-v4-autonomous-trigger-gating.json`
- `orchestrator/codex_roles/policy.py`
- `orchestrator/codex_roles/review_ledger.py`

子B「binding・admission/replay・境界テスト」:

- 新規 `trigger_gate_binding.py`
- `loop.py`
- `pipeline.py`
- `p3_s4_loop.py`
- `wal.py`
- `artifact_admission.py`
- 上記全 test ファイル

親所有:

- 新 D、runbook、phase/worklog、最終 checker・テスト・commit。

段4で binding helper の関数名・payload schema・loop/pipeline引数を固定してから並行開始する。role pinの明示レビューが間に合わない場合は、子Aのagent本文変更→人間レビュー→manifest/adapter/ledger更新だけ直列化する。

## 9. 変異事前登録

| ID | 変異 | 殺すテスト |
|---|---|---|
| A1 | `implementation` fallbackを復活 | old-key/C++ reject |
| A2 | wire長・文字・型を緩和 | exact 32 + invalid corpus |
| A3 | bit順をMSB-firstへ反転 | reason-order test、32 golden |
| A4 | previewだけraw入力を使用 | preview/run equality |
| A5 | emitterを迂回して手書きC++を渡す | all-32 materialize golden |
| A6 | unattended parser/fixtureだけ旧schemaのまま | autonomous trial tests |
| B1 | build_startからbindingを省略 | replay/admission missing tests |
| B2 | maskまたはpredicate SHAを単独改変 | canonical binding validator |
| B3 | binding sourceとadmission sourceの比較を削除 | source mismatch/cache spy |
| B4 | replay validationを削除 | replay tamper test |
| B5 | `records_by_stage`だけ検証を迂回 | duplicate/records test |
| B6 | artifact admission validationを削除 | admission tamper test |
| B7 | marker欠落を一律legacy扱い | unproven-history test |
| B8 | maskをvariant ID preimageへ追加 | unchanged variant-ID contract |
| B9 | provenance/reportでbindingを再導出 | WALとのexact equality test |

## 10. リスクと段3への攻撃依頼

- replayは source bytesを保持しないため、mask→predicate SHA は再計算できても、predicateが source digestの中に実在した関係は producer-time検査とSourceEvidenceの鎖に依存する。協調的なWAL全面改竄への暗号学的防御ではない。
- `src_token` が対象行を確実に含み、全32 maskで別source identityになる前提を敵対確認する必要がある。
- raw maskの durable記録がI3/D48のfirewallと両立するか。少なくともcritic/coderへの転送は禁止する。
- redundantになった syntax blacklist/auditor を内部drift gateとして残す意義と、単なる儀式化の危険。
- all-zero wireの意味、LSB-first、`1=backoff` の極性誤読。
- nested WAL event payloadを正式な「reportへの同梱」と数えてよいか。
- post-policy/pre-binding trigger artifactが未追跡領域に存在しないか。
- source-null bindingを許すreject reasonの閉集合と、crash途中のreceiptless attemptの扱い。
- campaign ID変更により旧proposal resumeが切れることを意図した互換破壊として確定できるか。
- agent/adapter hash更新に必要な明示レビューが機械的cachebusterへ退化しないか。

この段2ではread-only静的調査のみで、pytest・py_compile・ファイル編集は実施していない。

## 総括

- trigger受理をexact 5-bit wireへ縮小し、C++は凍結parser/emitterだけから生成する。
- binding/v1をWAL・provenance・report・SourceEvidence・cache・replay・admissionへ一鎖で通す。
- maskはvariant IDへ直接足さず、既存src_token identityを維持する。
- 歴史物はpositive markerとexact hashで判別し、field欠落をlegacy判定に使わない。
- coder契約と全runtime/manifest/adapter consumerはatomic cutoverする。
- D96新Dと境界テストを実装と同一commitに含める。
- 段3にはsource-bindingの証明強度、mask開示、歴史epoch、report契約を重点攻撃として渡す。