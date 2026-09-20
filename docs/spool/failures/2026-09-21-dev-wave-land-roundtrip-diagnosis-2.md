---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-land-roundtrip-diagnosis
seq: 2
---

## 再発

### F672

- **再発: 2026-09-20 (6・7 例目、事後集計で判明)** — 22:36:34 JST の k2-loop-originals-lost-downstream (land it=1、path `<job dir>/dev-wave-t1505-a1-sized-submit/submit-tree`) と 22:39:11 JST の [T-2813] (land-2、path `<job dir>/dev-wave-t2792-a1-sized-attempt2/submit-tree`) が同型 (`registered worktree path cannot be resolved: [Errno 4] Interrupted system call`、`release_safe=true` / `retryable_same_request=false`、main 不変)。どちらも他 wave の登録 path で、同時刻に land が 3 本並んだ混雑窓。**source で確認した呼び出し位置:** `_registered_worktree_paths` は `_run_fold_gate` の `with _FoldGateOuterWatchdog(...)` の中 (`_execute_fold_gate` 先頭) で呼ばれ、watchdog は `setitimer(ITIMER_REAL, 0.1, 0.1)` で SIGALRM を 100 ms 周期に handler 付きで送る。`Path.resolve(strict=True)` → `posixpath._joinrealpath` は `os.lstat` / `os.readlink` を使い、CPython 3.10.12 の C 実装に EINTR の自動再試行 loop は無い (PEP 475 の対象外)。「その SIGALRM が Lustre の遅い metadata 呼び出しを中断して `InterruptedError` になった」は整合する未検証の仮説 (静穏時 probe 460 回 × 2 で 0 回、混雑時の再現は未実施)。EINTR 型は既存 5 件 + 本 2 件 = 7 件 (別型の ENOENT 1 件は含めない)。**復旧の是正:** 本項の「受入を取り直して新しい request を作るしかない」は現行 source と合わない — 非 retryable の拒否は順番票の entry を削除するが receipt は消費されず main も不変で、同じ tested tip / landing tip / receipt の再投入は `_register_land_turn` が新しい seq で新規登録して検査を再実行する (成功は保証しない)。k2-loop は拒否の 31 秒後に再投入して landed (受入不要、失うのは順番)。恒久対応の候補 (`InterruptedError` を armed 区間内で有界に再試行、期限監督は保つ) は `output/insights/2026-09-21/land-roundtrip-diagnosis/README.md` §5.1 の裁定パッケージ。
