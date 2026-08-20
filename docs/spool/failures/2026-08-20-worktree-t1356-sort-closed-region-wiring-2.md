---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: worktree-t1356-sort-closed-region-wiring
seq: 2
---

## 新規

### {{F:originless-baseline-role-hash-drift}}. role file 変更が別ファイルの frozen baseline を追随なしで壊す [手順漏れ]

- 事象: [T-1356] の `.claude/agents/auditor.md` 編集後、受入全走で
  `orchestrator/tests/test_reflux_originless_compatibility.py` が赤になった。
  acceptance-red-check の実測 (`main_rerun_rc=0`・`wave_rerun_rc=1`) で本 wave 由来と
  確定するまで、一見無関係な別 wave の変更が原因と誤診断した (詳細は worklog 本文)。
- 根本原因: 同ファイル360行の `_PRE_WAVE_ORIGINLESS_BASELINE` (frozen JSON blob 定数) が
  auditor role の `role_file_sha256`・`effective_prompt_sha256` の2値を保持しており、
  この2つのフィールドは `_MAIN_DERIVED_LEAF_PATHS` (main 進行で変わる値として意図的に
  マスクされる4カテゴリ) に含まれない設計のため、**role file (`.claude/agents/*.md`) を
  変更するたびに、このファイルの frozen baseline を手動で追随させる必要がある**。
  この consumer は本 wave の段1-4 の pin 閉包調査 (`grep -rn "coder-v4-autonomous-sort\.md
  \|agents/auditor\.md"`) では発見できなかった — baseline が opaque な単一行 JSON blob で
  path を literal 参照しないため。
- 恒久対応: なし (機械検査は未整備)。当面は role file を変更する wave が受入全走で
  この赤を実測してから気づき、都度追随修正する運用に留まる。恒久対応候補としては
  (a) `_MAIN_DERIVED_LEAF_PATHS` へ role hash 系フィールドを追加してマスク対象にする
  (baseline がこれらの値を意味的に検証しなくなるトレードオフが要る、別 scope の判断)、
  (b) role file 変更を検知して baseline 自動再生成する script、のいずれも本 wave では
  実装しない (規律5、scope外)。
- 再発検知: 次に role file (`.claude/agents/*.md`) を変更する wave が受入全走で
  `test_reflux_originless_compatibility.py` の赤を踏んだ時点で顕在化する (lint 化は未実装)。
