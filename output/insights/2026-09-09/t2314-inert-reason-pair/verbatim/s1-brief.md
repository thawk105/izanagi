# 段 1 brief — [T-2314] inert 比較の受理条件を「組」2 つのどちらか 1 つへ

**研究前進 (土台):** 計算ノード sandbox backend の再実測 (t316 probe の S6) は、gate が
`stock-inert-preprocess-root-location-only` の緑を返す環境で probe 側が構造的に inconclusive に
なるため開始できない。最小差分は probe の exact 述語を gate の表 (2 組) へ揃えること。

**確定済みユーザー裁定 (D1625、2026-09-04 /rulings 全件 第 8 回):** probe は inert 比較の緑を、
gate の表が定める組 (`stock-inert-preprocess-identical`, `stock-inert-identity`) と
(`stock-inert-preprocess-root-location-only`, `stock-inert-root-location-only`) の
**どちらか 1 つに exact 一致**するときだけ受理し、どちらの組が発火したかを probe の記録に残す。
理由コードだけの二択化、exact 検査の撤去、raw bytes 据え置きは却下済み。**受理集合を変える変更**。

**scope (純増):**
- `tools/pegasus/probes/t316_sandbox_backend_probe.py` `_condition_gate_family_valid` (:346-374、
  現行 :370-371 が 1 組 exact) を 2 組のいずれかへの exact 一致に変える。
- 発火した組を `_condition_gate_receipt_summary` (:310-342) の supply entry へ記録する。(P1)
- `orchestrator/tests/test_t316_sandbox_probe.py` に 2 組それぞれの正例と、組を跨いだ交叉
  (reason=identical × comparison=root-location-only、その逆) の負例を足す。

**scope 外:** gate 本体 (`orchestrator/campaign/condition_meaning_gate.py`) の変更、第 3 の理由コード、
meaning arm の契約変更、新規 gate・検査・台帳・一般化・互換層。

**不変条件:**
- 受理集合は gate の表 (:3691-3706 `status_contract`) を超えない。`require_condition_gate_family`
  の呼出しと `admitted is True`、`observed == expected`、receipt summary 一致の要求を残す。
- meaning arm は `unestablished` / `meaning-witness-undeclared` の exact 要求のまま。
  supply の `terminal_status == "green"`、`driver_id`、`macro == "BACKOFF_FIXED"` も exact のまま。
- `condition_gates` の各 entry に `evidence` key を出さない (既存 test :1146 が禁止)。
- 既存テストの期待値を変えない。緩和・反転・skip・削除を行わない (規律 2)。

**成果物影響 (DW-G05):** 放置すると root-location-only 環境で S6 が `S6_CONDITION_GATE_UNPROVEN`
に固定され、t316 receipt が `go` に到達せず sandbox backend の判定材料を更新できない。

**(P1) 発火した組の記録形 (親の provisional 裁定・攻撃対象):** 現行 summary は supply の
`reason_code` だけを持つ。組は表で一意に定まるので理由コードだけでも識別可能だが、D1625 の
「組を記録する」を素直に読み **`comparison` を明示 field として足す**。

**到達可能性 (DW-O13):** `stock-inert-preprocess-root-location-only` の緑は
`docs/archive/worklog-phase3-0907-1291-1292.md:33` で実測済み。gate 側の正例は
`orchestrator/tests/test_condition_meaning_gate.py:672` にある。

**分割:** 編集面が production 1 file + test 1 file の一枚岩なので実装子 1 単位。
**環境:** 受入は login node の `tools/dev_wave_wait.py acceptance`。probe 実走 (計算ノード dispatch)
は本 wave の scope 外 — 変更は述語の受理集合のみ。
