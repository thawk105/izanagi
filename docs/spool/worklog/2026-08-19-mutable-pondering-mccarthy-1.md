---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: mutable-pondering-mccarthy
seq: 1
title: '[T-324] は entry (586) で T-1132/T-1133/T-1134 (D438) として既に land 済みと判明した — (617) の独立確認と本 wave の直接コード確認で再確認し、台帳 carry を是正した (実装差分ゼロ、branch worktree-mutable-pondering-mccarthy)'
---

## 本文

- [T-324] (2026-08-16 /rulings 全件裁定「事前登録の文書側を T-1132/T-1133/T-1134 と同一 wave で
  land する」) は 2026-08-16 entry (586) で T-1132/T-1133/T-1134 の実装 (D438) として既に main へ
  land 済みだった。2026-08-17 entry (617) ([T-1250] wave の副次実測) が `git cherry` で関係 4
  branch の未着地 commit 0 件を独立確認し「台帳 carry の整理は別 transition に残す」としていた —
  本 wave がその transition である。
- brief 前実測で直接コード確認した。`orchestrator/campaign/s8c_preregistration_evidence.py` の
  `_MACHINE_EVALUATORS` は D438 決定 (1) の baseline 6 条件 (C01/C04/C09/C10/C11/C12) を含む 9 条件
  登録済み、`_evaluate_c11` の証拠 (承認上限定数・3 入口予算 validator・`generation_projection`
  第二層射影) と `effective_at()` の二段束縛 (内容 commit / 発効 commit 分離) は、いずれも D438
  決定 (2)(4) と現物一致した。
- 実装差分ゼロのため `DW-S04` に従い変異 matrix を免除する。段 2/3 も省略した — brief 前実測で
  既に別 ID で解決済みと判明した軽量パス (entry 673 [T-715]・687 [T-1198]・690+692 [T-1408] と
  同型、[T-1410] が明文化の裁定待ちとして記録した precedent 運用、本 wave が 5 例目)。
- 段 7 前の real-repo 焦点テスト実測: `test_s8c_preregistration_core.py` +
  `test_s8c_preregistration_invariant.py` + `test_s8c_preregistration_predicates.py` = 594 passed /
  0 failed (bounded local, 63.89s)。
- エージェント工数: 子 0 本 (親が直接調査、軽量パスのため codex plan/consult を省略)。

## 次の一手差分

### 完了

- [T-324] 2026-08-16 entry (586) の T-1132/T-1133/T-1134 (D438) 実装により、要求 (事前登録の
  文書側 3 件の改訂を同一 wave で land する) は既に充足済みと確認した。2026-08-17 entry (617) の
  独立確認、本 wave の直接コード確認、real-repo 焦点テスト (594 passed) で健全性を再確認した。
  追加実装なし。
  remaining: none
  base: deee5a5a74cf3c47134421f8eeef3bcb3db4b10e1f03e08b3a96d5e20398ef59
