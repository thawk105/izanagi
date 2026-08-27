---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: dev-wave-t2018-condition-meaning-gate-codex-resume
seq: 3
---

## 再発

### F42

- **再発: 2026-08-28** — 新production process site `condition_meaning_gate._run_process` を実装したが、親の焦点走は新test・直接consumer・plain-runner/duration metaまでで、repo-wide `test_ccbench_spawn_sites.py` のreviewed inventoryを落とした。最終受入で18,326 passed / 61 skipped後に2赤となり露出し、explicit non-CCBench siteへexact 1件を追加して2 node緑を確認した。

### F43

- **再発: 2026-08-28** — 段5 Codex authorがコードと有効な最終報告を残してexit 0だったが、fence外のexact `## 総括` が無くvalidator rc=1 / failure_class=f43_fragmentになった。差分と未受理報告を保全し、別authorが同じdirty treeを再監査してaccepted outputを発行するまで採用しなかった。

### F537

- **再発: 2026-08-28** — 変異finalを共有primaryのwave worktreeから2回走らせ、childは両回baseline PASSED・8/8 KILLEDだったが、primaryの `.codex/worktrees/` untracked集合変動でwrapperがshared_snapshot_matches=false / rc125に倒れた。結果を不受理にし、既存手順どおり独立common-dir cloneへ切り替えてrc0を取り直した。

### F618

- **再発: 2026-08-28** — 共有checkoutを観測rootに含むfinal変異1走目が並行landでrc125になった。terminal ledgerとteardown完了を確認しても8/8を採用せず、local submodule sourceをno-fetchで初期化した独立cloneをsource-repoに使い、shared_snapshot_matches=trueを再取得した。
