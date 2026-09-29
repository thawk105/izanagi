---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-land-cleanup-enforce
seq: 3
---

## 再発

### F1036

- **再発: 2026-09-29** — 段 9 の自己撤去 (D2163・D2197) の導入後も、9/29 に land した wave 約 35 本のうち約 10 本で子木の `remove-child` が rc=20 で拒否され、子木と子 branch が残った。fix 巡ごとに新しい子木を作る運用 (1 wave で `git worktree add` 25〜31 回) の途中版の木は所有 path が main と一致せず、repo に入れない probe・作図の木は所有 path が空で、統合証明が構造的に成り立たない。撤去中に他 wave の land で main が進んで rc=30 になった wave が 4 本、撤去を呼ばずに終了した wave が 2 本あった。恒久対応: {{D:child-archived-removal}} (退避してから撤去する経路、main 前進の許容、compare-and-delete、終了時 hook、`DW-S05-A` の同木・同 branch 再利用と補助木登録)。再発検知: `orchestrator/tests/test_dev_wave_cleanup.py` の退避撤去の正例・負例 (`test_remove_child_archive_requires_landed_wave`・`test_remove_child_archive_stops_when_wave_moves_after_backup`・`test_remove_child_main_advance_during_removal_completes` ほか) と `orchestrator/tests/test_hooks.py` の `test_cleanup_stop_*`。
