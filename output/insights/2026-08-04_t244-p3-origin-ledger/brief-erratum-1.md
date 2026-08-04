# brief erratum 1 — 先行実装の見落とし (2026-08-04、段 2 実行中に親が実測)

親 brief の「既存被覆と純増検出力」節は**言い過ぎ**であった。訂正する。

## 実測した先行実装 (`orchestrator/qualification/`、T-126)

- `attempt_ledger.py` (473 行) = **create-only の series-global hash-chain 台帳**。
  event に `event_index` / `previous_event_sha256` / `event_sha256` を持ち (`:23-32`)、
  genesis は `_ZERO = "0" * 64` (`:23`)。`replay_attempt_ledger()` (`:169`) が event 列から
  state を再導出し、`event_index` の連番と chain の連続を検査する (`:196`)。
- **2 相 commit と idempotent 化が既にある。** `initial_intent` → `initial_submitted`、
  `retry_intent` → `retry_submitted`、`attempt_outcome_pending` → `attempt_outcome`
  (`:29-32`)。`prepare_outcome()` (`:439`) / `finalize_outcome()` (`:468`) が pending を
  bytes 単位で照合し (`:253`, `:461-464`)、`append(..., idempotent=True)` (`:436`, `:466`) で
  二重適用を防いでいる。**これは本 wave の crash replay とほぼ同型である。**
- `series.py` の `SeriesFSM` (`:243`) と `replay_ledger()` (`:66`) が、同じ形の FSM を series 層で持つ。
- `artifacts.py` の `QualificationWriteCapability` (`:121`、immutable・root 束縛) と
  `CreateTargetExistsError` (`:52`) が create-only の write capability を実装している。
- **`t126_reservation_policy_v1.json` は committed な reservation policy JSON である。**
  予算相当の値 (walltime、cap、reserve、`wmax_s`) をコードでなく tracked file に置き、
  `schema_version` を持つ。**親 brief の (P4)「予算は caller 注入の immutable policy」の先例**である。
- テストは `test_t126_qualification_artifacts.py` / `_contract.py` / `_driver.py` の 3 本。

## 訂正後の純増検出力

「単一 in-flight・CAS・idempotent replay・削除耐性の 4 vector が repo に一度も無い」は**誤り**である。
正しくは次に限る。

- **reflux origin の文脈**での 4 性質 (T-126 は qualification 投入の文脈で、対象も state も違う)
- **削除耐性 (anchor)** — T-126 の台帳も create-only だが、**台帳ごと消された場合の外部錨は持たない**
  (親の grep 実測: `qualification` 側にも anchor 相当は無い)
- **予算上限の注入と fail-closed** — T-126 の policy は walltime 系で、query / iteration 予算ではない

## 段 3・段 4 へ渡す論点 (親の裁定ではなく攻撃対象)

1. 新規 leaf が T-126 の idiom を**踏襲すべきか、共有化すべきか、意図的に分けるべきか**。
   共有化は `orchestrator/qualification/` という別 package を触ることになり、
   「新規 leaf に閉じる」という本 wave の scope を越える可能性がある。
2. T-126 の 2 相 commit が本 wave の 4 crash 窓を**すでに解いているか**。解いているなら、
   本 wave の新規性は削除耐性と予算注入だけに縮む。
3. `DW-G03` (族一般化には独立 2 例) の観点で、hash-chain 台帳が 2 例目になるなら、
   共通化を**制度化してよいのか、まだ早いのか**。
