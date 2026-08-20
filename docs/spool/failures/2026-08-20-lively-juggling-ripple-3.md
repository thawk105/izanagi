---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: lively-juggling-ripple
seq: 3
---

## 新規

### {{F:acceptance-wave-must-match-branch-suffix}}. `dev_wave_wait.py acceptance`の`--wave`は実branch名の suffix一致を要求する未文書化制約 [手順漏れ]

- 事象: 背景job worktree (`EnterWorktree`が自動生成した branch `worktree-lively-juggling-ripple`)
  で、job dir/成果物命名に使っていた task-descriptive な slug
  (`dev-wave-t1434-4-codex-reasoning-ab-model-refactor`) をそのまま
  `dev_wave_wait.py acceptance --wave <slug>`へ渡したところ、`error:
  stage=preflight-branch rc=2`で即座に拒否された。
- 根本原因: `tools/dev_wave_wait.py`の`_identity_preflight`が
  `branch.endswith(wave)`(該当行は`git symbolic-ref --short HEAD`で得た現branch名の末尾一致)
  を要求する。`dev_wave_codex.py --wave`にはこの制約が無いため、段2〜段6のcodex dispatchでは
  問題が顕在化せず、段6終盤の受入投入で初めて発覚した。`docs/dev-wave/operations.md`の
  DW-O01/DW-O20等にはこの制約の記載が無い。
- 恒久対応: memory
  `/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/memory/acceptance-wave-flag-must-match-branch-suffix.md`
  に回避策を記録した (docs追記はscope外と判断)。要旨: `dev_wave_wait.py acceptance`・
  （推定）`dev_wave_land.py`の`--wave`引数には、job dir命名でなく実branch名の末尾一致部分
  (`worktree-<random>`形式なら`<random>`部分) を渡す。`git symbolic-ref --short HEAD`で
  実branch名を確認してから決める。
- 再発検知: 未整備 (`tools/check_wave_startup.py`等の既存gateはこの不一致を検出しない)。

