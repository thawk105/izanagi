# [T-428] 受理経路の事実地図 (Explore 子の実測、2026-08-04)

worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring`
すべて実測 (ファイルを読んで確認した事実)。推測は明示。

## 1. reflux_ir.py の公開 API (127 行)

- `SCHEMA_ID` = "izanagi-trigger-gate-ir/v1" (reflux_ir.py:19)
- `TriggerGateIR` frozen dataclass (78-83)。`mask` は厳密 int かつ 0..31 (`_validate_mask`, 55-58)。
  bool / int サブクラス / float / str は reject
- `parse_wire(value) -> TriggerGateIR` (99-108): 厳密 str・長さ 5・全文字 "0"/"1" 以外は即 reject。
  LSB-first
- `encode_wire(ir) -> str` (111-114)、`emit_predicate(ir) -> str` (117-127): C++ 1 行代入文を生成
- `RefluxIRError` (47-48): 常に "invalid reflux IR" 固定文言、`__context__` なし (disclosure-free)
- `_TriggerGateIRMeta` (61-75): `campaign.reflux_ir` と `orchestrator.campaign.reflux_ir` の
  二重 import 経路を相互受理
- module load 時に `GATEABLE_REASONS != _EXPECTED_REASONS` なら RuntimeError (43-44、順序 drift ガード)
- ビット順 = `GATEABLE_REASONS` (axis_trigger_gating.py:50-51):
  lock-conflict, update-absent, readvali-tid, readvali-locked, node-vali

## 2. 現行の production 受理経路 (p3_s4_loop_trigger_gating.py、847 行)

```python
# p3_s4_loop_trigger_gating.py:101-109
@dataclass
class CoderProposalTriggerGating:
    axis: str
    implementation: str   # 自由文字列。__post_init__ なし = 型・語彙とも無検査
    justification: str = ""
    confidence: str = "medium"
```

受理順序:
1. `load_proposal_file` (571-601): `json.load` →
   `projection_guard.assert_closed_proposal_schema(d, require_auditor=True, require_coder_value=False)`
   (585-587) は**キー集合のみ**検査。`c["implementation"]` を無検査で dataclass へ (592-594)。
   `assert_no_ability_probe_material` (600) は ability-probe の字面 tripwire で IR と無関係
2. `_quarantine_and_audit` (358-402)、呼び出し元 `_run_one_iteration_resolved` (480-484、
   `applied(TEMPLATE_PATCH)` 内):
   - `L.quarantine(sub, coder.implementation, ...)` (369、L = campaign.p3_s4_loop) — 唯一の構造検査 + materialize
   - `check_syntax_contract(coder.implementation)` (378、定義 118-124) —
     `SYNTAX_CONTRACT_FORBIDDEN` (axis_trigger_gating.py:58-64: thid_, result_, read_set_,
     write_set_, node_map_) の識別子境界 grep。hit で subtype="syntax-contract" reject (127-139)
   - `assert_digest_matches(auditor, working_diff)` (388) + verdict != "pass" reject (390-400)
   - 通れば `run_campaign` (496-502) で build/verify/bench へ
3. fixture 経路: `main()` の `--run-iteration` なし分岐は固定文字列
   `fixture_impl = "  izanagi_gate_pass = true;"` (789) — 配線確認専用

**結論: 5-bit wire・reflux_ir の語彙制限は現状どこにも存在しない。**

## 3. consumer 閉包 5 面の現状

- (a) 受理点 = 上記 2。reflux_ir への参照なし
- (b) proposal schema = Python 検査のみ (projection_guard.py)。
  `_CODER_REQUIRED = {"axis", "implementation"}` (30)、`_CODER_OPTIONAL = {"value", "justification",
  "confidence"}` (31)。`assert_closed_proposal_schema` (273-315) は `_assert_key_set` (248 付近、
  260-270) でキー名集合の一致だけ。**値の型検査なし** (implementation が str であることすら見ない)。
  JSON Schema ファイルは存在しない
- (c) materialize = `p3_s4_loop.quarantine()` (184-221)。`render_hole` (161-171) で hole 行を
  implementation で置換、`write=True` かつ `res.passed` なら `sub/source_rel`
  (= cc/silo/transaction.cc、SOURCE_REL = axis_trigger_gating.py:24) へ上書き (217-220)。
  `reflux_ir.emit_predicate` は呼ばれていない
- (d) build cache = `pipeline.variant_id(genome, src_token)` (pipeline.py:61-67) =
  sha256(genome.canonical() + "|src=" + src_token)。`src_token` は source_digest.py が
  **materialize 後の working-tree ソース (EVOLVE_BLOCK_SOURCES = include/backoff.hh,
  cc/silo/transaction.cc、source_digest.py:79) を g++ -E -P で前処理した bytes の sha256**。
  implementation は間接束縛のみ。**"mask" という概念は production のどこにも存在しない**
  (grep 0 件: p3_s4_loop_trigger_gating.py, p3_s4_loop.py, wal.py, pipeline.py, source_digest.py,
  artifact_admission.py)。diff_quarantine.py docstring (25-29) 自身が
  「cache/replay class 束縛を欠くため admission 層は閉じていない」と明言
- (e) replay = `wal.replay()` (716-747): stage 遷移・committed/aborted・attempts の復元のみ。
  **implementation の再検証なし** (全文確認済み)。`records_by_stage()` (750-765) も同様

## 4. wiring 4 要件の現状 (すべて未実装、実測)

- wire→mask→predicate 唯一経路化: reflux_ir に存在するが production から不使用。
  偵察側 `s8a_trigger_sweep.py` の `predicate_for` (215-223 付近) は recon 専用で別系
- raw mask ↔ source digest / variant ID 束縛: mask 概念自体が無い
- WAL/provenance/report での同束縛: WAL 書込 (`record_diff_reject`, p3_s4_loop.py:234-251) の
  payload = {genome, src_token, build_attempt_id, reason, diff_quarantine} のみ。
  provenance entry (`_append_provenance_entry` 呼出、p3_s4_loop_trigger_gating.py:655-660) =
  {proposal_path, auditor_diff_digest, variant, outcome} のみ。mask/wire フィールドなし
- binding 欠落 artifact の proof chain 拒否: 検証器候補 =
  `artifact_admission.require_admitted_campaign` (600-610) / `classify_campaign` (590 付近) —
  WAL・campaign.lock・legacy overlay ledger の整合検証のみ。mask 検証は無い。
  「proof chain」という identifier は production に無く、artifact_admission が最有力候補 (推測)。
  `hooks/guard_write.py` は別物 (tool 書込保護で、runs/・campaign.lock・build-variants のみ。
  reports/ は対象外 — p3_s4_loop_trigger_gating.py:189 のコメント)

## 5. 受理集合を固定する既存境界テスト (D96 対象)

- `test_reflux_ir.py` (502 行、17 test): IR 単体契約 + golden 32 点 byte 一致。
  golden 側の production 非依存は `test_golden_has_no_production_import_and_production_has_no_golden_consumer`
  (216-240) が固定。reflux_ir.py 自体の production 非到達を直接 assert するテストは無い
- `test_p3_s4_loop_trigger_gating.py` (1513 行、59 test): 主要なもの —
  `test_check_syntax_contract_clean_and_forbidden` (1095-1099)、
  `test_check_syntax_contract_requires_identifier_boundary` (1102-1106)、
  `test_quarantine_and_audit_rejects_forbidden_identifier` (1109-1132)、
  `test_quarantine_and_audit_dry_pass_when_clean_and_digest_matches` (1158-1169)、
  `test_quarantine_and_audit_raises_on_digest_mismatch` (1172-1186)、
  `test_load_proposal_file_roundtrip_and_fails_closed` (1215-)
- `test_p3_s4_loop.py`: `test_render_hole_preserves_indent_and_replaces_only_hole` (96)、
  `test_quarantine_passes_clean_backoff_value` (108)、`test_quarantine_rejects_directive_in_hole` (117)、
  `test_quarantine_write_occurs_only_after_structural_validation` (127)、
  `test_quarantine_rejects_marker_forgery_in_hole` (145)、`test_quarantine_fails_closed_on_broken_template` (157)
- `test_diff_quarantine.py` (38 test): 構造 containment のみ固定
- これらは「受理集合 = 任意 1 行 C++」を前提に固定されており、縮小で追随更新が要る

## 6. reflux_ir の import 元 (全列挙)

`reflux_ir|TriggerGateIR|parse_wire|encode_wire|emit_predicate` の grep (worktree 全体):
`orchestrator/campaign/reflux_ir.py` (定義元) と `orchestrator/tests/test_reflux_ir.py` のみ。
**production 到達性ゼロ (実測)。**
