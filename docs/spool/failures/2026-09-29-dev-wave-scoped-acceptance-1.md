---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-scoped-acceptance
seq: 1
---

## 新規

### {{F:child-worktree-stale-index-lock}}. 実装子の終了後、子木の gitdir に 0 byte の index.lock が残り、残差 commit が add-all で落ちた [手順漏れ]

- 事象: 縮小受入 wave の段 5 で、Codex 実装子の作業が終わった直後 (2026-09-29 23:56 JST) に子木の
  `.git/worktrees/scoped-acc-author/index.lock` が 0 byte で残り、起動器の終端 commit と待ち手の `--commit-worktree` が
  どちらも `worktree-commit: failed reason=add-all` で落ちた (起動器 rc=3、待ち手 rc=70)。子の成果物 (7 file) は作業木に残っていた。
- 根本原因: 未特定。lock を作った process は、確認した時点では子木を cwd・argv に持つ process が親の shell 以外に無く、残っていなかった。
  F359 (子の sandbox は Git 管理領域に書けず lock を作れない) とは逆に、lock が作られて残っている。
- 恒久対応: なし (1 例)。回復は、子木を cmdline・cwd の両方で走査して生存 process が無いことを確かめてから lock を削除し、
  同じ done file で待ち手を `--commit-worktree` 付きで再実行する (Codex author の trailer 付きで commit された)。
- 再発検知: 起動器の `.done` が 3、待ち手の log に `worktree-commit: failed reason=add-all` が出たら、子木の gitdir の `index.lock` を見る。

## 再発

### F42

- **再発: 2026-09-30** — 縮小受入 wave で新設した `orchestrator/tests/test_scoped_acceptance.py`・`test_scoped_acceptance_land.py` (どちらも `tmp_path` 等の fixture に依存) を pytest 専用 allowlist に載せず、親の焦点走 3 回の file 集合にも `test_plain_runner_coverage.py` を入れていなかった (DW-O26 の義務の取りこぼし、2026-09-26・09-27 と同じ位置)。独立 clone で行った効果測定の受入全走 1 回目で赤 1 件として現れ、allowlist に 2 行足して閉じた (1e97b58e0)。本 wave の実受入は空振りしていない。
