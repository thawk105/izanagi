---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2314-inert-reason-pair
seq: 1
---

## {{D:t316-receipt-records-fired-inert-pair}}. t316 の条件関門受領証は発火した組を comparison field として記録し、schema 版は上げない

**決定:** D1625 が求める「どちらの組が発火したかを probe の記録に残す」を、
`tools/pegasus/probes/t316_sandbox_backend_probe.py` の `_condition_gate_receipt_summary` が作る
supply entry へ `comparison` という scalar field を足す形で実装する。値は
`supply.evidence.get("comparison")` であり、`evidence` mapping 自体は受領証へ出さない。
`SCHEMA_VERSION` (`t316-sandbox-backend-probe/v1`) は上げない。

**理由:**
- 理由コードだけでも gate の表から組は逆算できるが、それでは受領証**単体**が組の第 2 座標を
  保持しない。D1625 は組を記録せよと言っており、逆算可能性は記録ではない。
- scalar 1 つなら issuer capability も evidence 全体も漏れない。受領証の各 entry へ
  `evidence` key を出さないという既存の検査もそのまま通る。
- 添字ではなく `.get` を使うのは、gate が production 発行の**赤** supply record を正当なものとして
  返し、その evidence に `comparison` key が無いためである。添字だと判定関数が例外で脱出し、
  fail-closed の inconclusive が process 失敗に変わる。
- 版を上げないのは、既発行の v1 receipt に `condition_gates` 自体が無く、閉じた key schema も
  reader も現行コードに存在しないためである。各 receipt は production の SHA-256 と commit を
  保持しており、同じ v1 内の意味差は execution binding で識別できる。

**却下した選択肢:**
- 理由コードだけを記録し comparison を旧値のまま置く — D1625 が明示的に却下している。
- `evidence` mapping ごと受領証へ出す — 受領証から evaluator 専用の情報を復元させない設計に反し、
  既存の検査にも抵触する。
- `SCHEMA_VERSION` を上げる — 「v1 は exact closed shape」という前提が現行コードに無く、
  上げると既発行 receipt との関係を別途定義する必要が生じる。前提を採るなら別途裁定する。
