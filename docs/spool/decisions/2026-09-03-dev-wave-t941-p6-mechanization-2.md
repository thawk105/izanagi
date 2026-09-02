---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-t941-p6-mechanization
seq: 2
---

## {{D:p6-second-ordering-dependency}}. P6 の機械実装は本番 origin provisioning の後にしか始められない

**決定:** P6 の機械実装 wave は、本番 origin provisioning が裁定・実施されるまで着手しない。
所有の確定 (どの task が P6 を持つか) は着手条件の一部でしかなく、それだけでは着手条件を満たさない。
本決定は所有の裁定を覆さず、着手条件として別に必要な前提を明示するものである。

**理由:**

- 本番 origin の登録は 0 件である (`orchestrator/campaign/reflux_origin_authority_v2.json` の
  `origins` が空配列)。
- 本番 runtime は構造的に作れない — `orchestrator/campaign/reflux_origin_ledger.py:2914-2915` の
  `_initialize_locked` は `store.fixture` でなければ `production runtime initialization is forbidden`
  で停止する。この経路をどう作るかは 8c 結線設計 §11 の V-7 であり、2026-08-12 の裁定により
  V-8 の後と順序づけられている。V-8 は「費用内訳の再提出待ち」で今も未裁定である。
- 意味的充足契約 v1 (D156 が発効) の発火条件は「real candidate binary・real trace であり、origin と
  attempt への帰属が成立する (fixture 由来は不可)」と明記している。本番 origin が存在しない状態では、
  実装しても発火せず、`DW-G04` の「発火条件を満たす既存 artifact path か計測 ID を brief に書ける
  場合だけ実装する」を満たせない。
- D156 のコア要件 (1) は「admission 結線まで含めた end-to-end calibration」であり、admission は
  本番 origin を要する。したがって部分実装は認定へ到達せず、`NOT_IMPLEMENTED` のまま残る。
- 2026-08-12 の裁定が定めた「V-6〜V-10 の裁定まで結線実装 wave を起票しない原則、発行 3 条件 0/3、
  本番 authority entry 0、閉じた成果層 0/11、D114 上限 1 は不変」は、その後の一括裁定
  (2026-09-02 の 374 件、2026-09-03 の 31 件) のいずれでも解除されていない。

**あわせて記録する実装上の事実:** 着地済みの 8c formal consumer は本番形状の WAL record を読めない。
`orchestrator/campaign/reflux_formal_consumer.py:722-729` の `_wal_trigger()` は root の
`record["kind"] == "TriggerGateBinding"` と root `trigger_binding` を要求するが、production の producer
(`orchestrator/campaign/wal.py:1354-1359` の `log_trigger_binding()`) は
`stage=trigger_gate_binding.WAL_RECORD_STAGE` と `payload` へ書く。provisioning が済んでも、
それだけでは本番 origin の projection は witness 検査より手前で落ちる。この修理は provisioning の
裁定と独立に必要である。

**却下した選択肢:**

- **witness 層だけを先に実装する** — 発火経路が無いため fixture 上でしか評価されず、
  「呼び手が無く一度も評価されない部品」の欠陥型に当たる。2026-09-02 の cap-lift 受領証 wave が
  同じ理由で撤退した先例がある。加えて意味的充足契約 SC-02 は 4 adapter 各々の正例到達を合接要求
  するため、部分実装を「契約を機械化した」と呼ぶことは実装したふりになる。
- **材料レポート renderer の結線を先に行う** — 同結線は「P6 不在のまま繋ぐと完全性を主張できない
  中間状態を読む結線になる」という理由で P6 実装 wave へ同梱されたものであり、P6 が
  `NOT_IMPLEMENTED` のまま結線しても、独立の reader / verifier module へ隔離してもこの懸念は
  解消しない。段 3 の敵対 2 レンズが互いを見ずに同じ結論へ到達した。
- **fixture を本番相当とみなして発火条件を満たしたと数える** — 契約が明示的に禁じている。
- **設計文書の過去の実測をそのまま現在の事実として使う** — 却下する。P6 契約設計 §3.2.1 の
  「`verify_done` payload に `build_attempt_id` が無い (実測)」は 2026-08-03 時点の測定であり、
  現行の `orchestrator/campaign/pipeline.py:1485` は明示的に書いている。測定時点の事実は事実として
  残るが、着手条件の判定には現物の再実測を使う。
