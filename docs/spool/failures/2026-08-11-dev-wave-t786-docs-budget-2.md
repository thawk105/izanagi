---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t786-docs-budget
seq: 2
---

## 新規

### {{F:reflow-breaks-line-anchored-pins}}. 縮約 wave の reflow だけで行束縛 pin が壊れた [手順漏れ] [防壁の射程誤認] [T-786]

- 事象: docs の byte 予算を空ける縮約中、**文字を 1 つも削らず改行位置だけを変えた 2 箇所**で
  `check_docs.py` が赤になった。(1) `DW-S06-C` の
  「並列 fix の統合後、焦点再レビューは全体へ `reasoning=high` で 1 本でよい。」を次行と連結したら
  `DEV_WAVE_DW_S06_C_REASONING_HIGH_SENTENCE` の adoption pin と不一致になった。
  (2) `.claude/commands/dev-wave.md` の「`DW-O13` は段 2 プラン前が期限」を
  `段 2` と `プラン前` の間で改行したら、D2 巻き戻し構造の正規表現
  (`` `DW-O13`.*?段 2 プラン前 ``) が空白込み literal を見つけられず「D2 巻き戻し構造がない」で落ちた。
- 根本原因: pin の粒度が「節の内容」ではなく **行単位の exact 一致**または
  **空白を含む literal の連続一致**であり、縮約 wave が既定で行う reflow (行送りの詰め直し) が
  その粒度に抵触する。縮約は「意味等価なら安全」という前提で行われるが、
  **これらの pin は意味でなく bytes と行境界を見ている**。
- 恒久対応: `docs/dev-wave/core.md` の `DW-S07` が既に要求する
  「docs commit 後に repo scan invariant と影響テストを再走して閉じる (F34)」を、
  縮約 wave では**節を 1 つ書き換えるたび**に `python3 tools/check_docs.py` で実行する
  (本 wave はこれを実施し、2 件とも land 前に検出・修復した)。
  機械側の検知は `tools/check_docs.py` の
  `_check_dev_wave_reasoning_effort_pins` と `D2_ROLLBACK_STRUCTURE` が既に担っており、
  いずれも fail-closed で rc=1 を返す。
- 再発検知: `orchestrator/tests/test_check_docs.py::test_command_docs_guard_positive_controls`
  の `command_startup_routing_blockquoted` と、本 wave が追加した
  `stage6-relocated` / `decoy-blockquoted` が、同種の行境界変更を positive control として固定する。
