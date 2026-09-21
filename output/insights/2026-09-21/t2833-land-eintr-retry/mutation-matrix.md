# [T-2833] 変異 matrix (final、2026-09-21)

`authority: none` / `default_effect: no-state-change`

- 対象: 独立 clone (main = `2a29a2381afc8bd46c09765ead4bf0a86583b066`)、`tools/mutation_worktree.py --runner-mode dispatch --detached`
- runner: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_dev_wave_land.py -q -rf` (変更 test file の全 node)
- spec sha256: probe `16539f5ab3feab9c7c47d77f5232e33e1b81c768b2c3795b8880e16483514369`、final `4c4553acd3216a29bf510d697534835c3a0aafe8c36eb32a17b74543120d80b0`
- final の要約: baseline PASSED、KILLED 7、SURVIVED 1、MISMATCH 0、matching 8 / 8
- 置換はすべて `tools/dev_wave_land.py` 1 file 内の 1 箇所 (各 old の出現数 1 を生成時に assert)。
- node 名は `orchestrator/tests/test_dev_wave_land.py::test_registered_worktree_paths_` を省いて書く。

| ID | 置換 | 判定 | 赤 node (完全集合) | 赤の理由 (probe の stdout で確認) |
|---|---|---|---|---|
| M0 equivalence-comment | 定数行の末尾に comment | SURVIVED (期待どおり) | なし | — |
| M1 no-retry | `for` / `try` / `except InterruptedError` の 7 行を `path = path.resolve(strict=True)` 1 行へ | KILLED | `retry_interrupted_resolve[1]`、`retry_interrupted_resolve[4]`、`keep_absent_after_interruption`、`propagate_watchdog_during_retry`、`exhaust_interrupted_resolve`、`do_not_retry_other_oserrors[eintr-then-permission]` | 前 4 つは初回 EINTR で `_FoldGateFailure` が上がる、`exhaust` は `assert 1 == 5`、`eintr-then-permission` は呼び出し回数 1 ≠ 2 |
| M2 bound-4 | 定数 5 → 4 | KILLED | `retry_interrupted_resolve[4]`、`exhaust_interrupted_resolve` | 4 回で枯渇して `_FoldGateFailure` / `assert 4 == 5` |
| M3 bound-6 | 定数 5 → 6 | KILLED | `exhaust_interrupted_resolve` | 6 回目の番兵 `AssertionError: sixth resolve must not be called` |
| M4 retry-all-oserror | `except InterruptedError:` → `except OSError:` | KILLED | `do_not_retry_other_oserrors[permission]`、`[eagain]`、`[eio]`、`[eintr-then-permission]`、`keep_absent_after_interruption` | 呼び出し回数 `assert 5 == 1` / `assert 5 == 2` (FileNotFoundError も呼び直される) |
| M5 retry-catches-watchdog | `except InterruptedError:` → `except (InterruptedError, RuntimeError):` | KILLED | `propagate_watchdog_during_retry` | watchdog の例外を呼び直し、3 回目で番兵 `AssertionError: watchdog must escape the second resolve` |
| M6 exhaust-reclassify | 枯渇時の `raise` → `raise _FoldGateInfrastructureFailure("registered worktree path cannot be resolved: interrupted")` | KILLED | `exhaust_interrupted_resolve` | `type(...) is LAND._FoldGateFailure` だけが落ちる (subclass なので `pytest.raises` と文言は通る) |
| M7 exhaust-swallow | 枯渇時の `raise` → `path = path.absolute()` | KILLED | `exhaust_interrupted_resolve` | `DID NOT RAISE _FoldGateFailure` |

- 既存 test の赤は probe・final とも 0。
- M4 の検出は呼び出し回数による。回数 = 1 は 2 回目を呼ばないことの証明なので、「1 回失敗して次は成功する」入力が拒否されることまで押さえる (段 6 レビュー B)。
- M5 には理論上、期限後の実 tick が except 節の中 (1 µs 未満の窓) に落ちると偽 SURVIVED になる余地 (約 10⁻⁵) がある (段 6 レビュー B)。今回の final では KILLED。
