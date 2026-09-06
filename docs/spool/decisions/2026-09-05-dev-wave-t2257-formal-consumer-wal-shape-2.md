---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-05
wave: dev-wave-t2257-formal-consumer-wal-shape
seq: 2
---

## {{D:formal-consumer-production-wal-trigger-shape}}. 8c formal consumer の FC05C は production の trigger binding record だけを読み、旧形状は拒否する

**決定:** `orchestrator/campaign/reflux_formal_consumer.py` の `_wal_trigger()` は、ordered WAL projection の records のうち
`stage == trigger_gate_binding.WAL_RECORD_STAGE` の record がちょうど 1 件あることを要求し、その record の outer key 集合
`{variant, stage, env_tag, ts, payload}`、outer 値の型 (`variant` / `env_tag` は str、`ts` は bool でない有限数)、payload の
key 集合 `{build_attempt_id, trigger_gate_binding}` を exact で閉じ、raw binding を `trigger_gate_binding.validate_record(require_source=False)`
で検証してから `{mask, candidate_wire = encode_wire(TriggerGateIR(mask)), trigger_gate_binding_commitment = commitment(binding)}` へ
射影し、ledger 側 `trigger_binding` と exact 比較する (FC05C)。root `kind` / `trigger_binding` の旧形状、stage 不一致、重複、余分 key、
root shadow (root と payload の attempt 併存)、不正 raw、mask / commitment / source の不一致はすべて FC05C で拒否する。両受け・互換層は置かない。

**理由:**
- production producer (`wal.log_trigger_binding()`) は `stage` + `payload` 形状しか書かない。D1555 が記録した食い違い (consumer が
  root `kind` を要求) は、provisioning の裁定と独立に本番 projection を witness 検査より手前で落とす。
- `require_source=False` は、source の有無が `to_record()` の canonical JSON に含まれ commitment 一致検査で捕まるためであり、
  source の必須性は admission 側 (`wal.validate_trigger_bindings()` の receipt 有無) の責務である。
- 出力 bytes の型契約 (`wal.py` の `parse_line`) は canonical-list 経路の projection では通らないので、consumer が同じ契約を敷く。
- 判定材料の独立性: WAL 側の mask / wire / commitment は raw binding から再構成し、ledger 側の値と別入力から導く。fixture の
  `candidate_wire` は consumer の `encode_wire` と独立な LSB-first 実装で作り、ビット順の共通変異を露出させる。

**却下した選択肢:**
- 旧形状と production 形状の両受け — 受理集合が広がり、fixture 由来の形が本番へ紛れ込む経路を残す (規律 2、DW-G05)。
- 不正 raw に別 reason code を新設する — 正しさを強めず外部判定面を増やすだけ。
- terminal record の `kind` 検査 (`_validate_wal_outcomes`) を同じ wave で直す — 依頼の名指し外で FC07 の受理集合まで変わる。
  別 carry ({{T:formal-consumer-terminal-stage-shape}}) として起票し、それまで本番 projection は FC05C を通った後 FC07 で止まる。

**限界 (DW-O13):** ledger 側 `trigger_binding` の production producer は未実装で、値は契約 (`reflux_result_evidence` の exact keys、
`commitment()`) から導いたものであり実測ではない。producer が将来 record 形状を変えたときは、裁定済みなら consumer と逐語 literal を
更新し、未裁定なら producer 側の回帰として扱い、旧 literal の互換受理を足さない。
