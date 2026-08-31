---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1795-attempt-evidence
seq: 3
---

## 新規

### {{F:pinned-external-session-vanished}}. repo 外へ pin した過去 session が消え、全 wave の受入が決定的に赤になった [テスト代表性] [ドリフト]

- 事象: 受入全走が `orchestrator/tests/test_codex_reasoning_ab.py` の 26 node
  (5 failed + 21 error) で赤になった。本 wave は同 file を 1 byte も変更していない。
  現行 main (`24014bdb259d971571f22b54a8f10a49352b825f`) 単独の probe worktree で
  **同じ内訳 (5 failed + 21 error) が再現した**ので非帰属である。
- 根本原因: 同 file は `~/.codex/sessions` 配下の**特定の過去 session を ID と SHA-256 で
  pin して読む**。pin 先 `019fac6b-4f74-7a03-aa4d-8a9de22b352c` の rollout file は
  実測時点で**存在しない** (`find ~/.codex/sessions -name 'rollout-*019fac6b-*'` が 0 件、
  同 root には 7138 件の rollout がある)。repo 外の可変領域に置かれた成果物を
  同一性で pin したため、その領域の掃除・回転で検査が決定的に落ちる状態になった。
- 影響: 受入全走が緑にならないため、**この状態が続く限りどの wave も land できない**
  (`tools/dev_wave_land.py` は受入受領証を必須とし、赤の走行では受領証が発行されない)。
- 恒久対応: 未定。pin 先を repo 内へ移す、pin を性質述語へ緩める、pin 先の不在を
  fail-closed の skip として表現する、のいずれかを選ぶ判断が要る。**本 wave では対応しない** —
  T-1795 の scope 外であり、他機構の証拠契約に触れるため。
- 再発検知: 未設置。`orchestrator/tests/flaky_test_holds.py` への hold 登録には
  既存 F 番号が要るので、本エントリが land した後に初めて登録できる。
