# [T-2871] 段 6 裁定 6 (親) — 受入 1 回目 (tip 71f249116 + post-claim merge 8a54cbd27) の赤 1 件

受入: `1 failed, 27899 passed, 74 skipped` (acceptance-child-1.log、claimed main f6772df03)。

| # | 赤 | 原因 | 裁定 | 処置 |
|---|---|---|---|---|
| R15 | `orchestrator/tests/test_check_subprocess_bytecode_guard.py::test_real_repo_clean` | repo 全体の bytecode guard 検査器 (`tools/check_subprocess_bytecode_guard.py`) が `orchestrator/tests/test_p3_s4_loop_policy.py:822` の `subprocess.run([sys.executable, harness, ...], env=...)` を未 guard の Python subprocess として検出 (login で再現、rc=1、指摘 1 件)。本 wave の結合検査が足した子 process 起動で、`-B` も bytecode 抑止の env も無い | real・自分起因 (DW-O18) | fix-5 (Codex、test のみ): 子の argv を `[sys.executable, '-B', harness, ...]` にする。検査器の既存の受理形 (`-B`) に合わせるだけで、T1〜T3 の assert と driver は不変 |

受理・拒否の含意: R15 は結合検査の子 process の起動 flag だけを直し、driver・検査器の受理集合を変えない。通る正例 = `-B` 付きで起動した子が実 `acquire_claim` まで到達する T1 と、検査器 rc=0。拒否されるべき例 (変えない) = `-B` も env の guard も無い Python subprocess は検査器が rc=1 で検出する (今回の赤そのもの)。

変異との関係: 変異 M1〜M5 の置換対象はすべて `orchestrator/campaign/p3_s4_loop_policy.py` で、fix-5 は触らない。final (d7161a2a1) の KILLED は子の起動 flag に依存しない assert (claim 数・stock outcome・系列 state・履歴・digest) で得たので、fix-5 後も同じ理由で赤になる。
