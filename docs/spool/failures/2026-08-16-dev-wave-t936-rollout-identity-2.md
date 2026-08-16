---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t936-rollout-identity
seq: 2
---

## 新規

### {{F:codex-evidence-nfc-from-repo-and-parent}}. 子が書いた文字でなく repo と親の artifact に混ざった分解形文字が codex 子の evidence を 2 度全損させた [手順漏れ] [コンテキスト浪費]

- 事象: [T-936] wave で codex 子の実行が 2 度 `evidence_status=invalid` / `launcher_rc=1` になり、
  完走した成果物が丸ごと不採用になった。合計 1,591 秒・27,118 bytes を失った。
  1 度目 = 段 2 plan 子 (613 秒 / 15,723 bytes、受領証 `plan-5fd59cc1`)。
  2 度目 = 段 3 レンズ A 子 (978 秒 / 11,395 bytes、受領証 `consult-sol-c50db370`)。
  いずれも `codex_exit_code=0` で内容も完成しており、失敗は本体と無関係である。
- 根本原因: `orchestrator/codex_roles/events.parse_jsonl` は JSONL が Unicode NFC であることを
  要求する。`tools/codex_worker_launch.py` はこの検査に落ちた行を `stdout_invalid` とし、
  `_evidence_status` が `invalid` を返して不採用にする。既知の対策 (memory
  `codex-output-must-be-nfc`) は**子自身が書く文字**だけを想定しており、次の 2 経路を覆っていなかった。
  - 経路 1 (repo 由来): `orchestrator/tests/test_codex_reasoning_ab.py` の
    `metacharacters` variant は `e` + COMBINING ACUTE ACCENT (U+0301) の escape を含む。
    子が pytest を走らせて失敗 trace が出ると、その文字が tool 出力として
    `attempt-*.events.jsonl` へ流れる (破損行 = 56 行目、466,292 bytes、type=`item.completed`)。
  - 経路 2 (親由来): **親が経路 1 の事故を handoff へ記録する際、grep 出力の分解形を
    そのまま貼った。** 子は prompt が名指ししていない job dir を自分で探索して読み、
    その 1 文字を出力へ載せた (破損行 = 113 行目)。
    **事故の記録それ自体が次の事故の原因になる型である。**
- 恒久対応: memory `codex-output-must-be-nfc` を上記 2 経路まで広げる
  ((a) 子 prompt へ pytest の `-q --tb=no -rf` 限定と「`\uXXXX` は escape の字面で書く」を書く、
  (b) **job dir 全体を NFC clean に保つ** — 子は prompt が名指ししない file も読む)。
  **`docs/dev-wave/operations.md` の `DW-O02` への追記は L1.5 予算に収まらず見送った** —
  最小形 (3 行) でも unique footprint が 9,808 bytes となり予算 9,566 bytes を超える。
  予算を上げず、削除可能な節も既に尽きている ([T-127] 裁定と先行 2 wave の実証) ため、
  入口編集は {{T:devwave-nfc-rule-budget}} としてユーザー裁定へ返す。
- 再発検知: 親が wave 中に job dir と insight を走査する probe
  (`scan_nfc.py` — 結合文字を 1 つでも検出したら報告)。本 wave では事故 2 の直後に導入し、
  以後の全 artifact 追加時に走らせて混入 0 を維持した。
  受領証側では `attempts[].evidence_status` が `invalid` になるため、
  `launcher_rc=1` を見たら**まず evidence_status を読む**。
