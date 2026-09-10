---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2340-backoff-story
seq: 2
---

## 新規

### {{F:t1259-git-snapshot-timeout}}. 受入のt1259 fixtureでGitの未追跡走査が30秒を超えて28件のsetup errorになった [テスト代表性] [計測汚染]

- 事象: T-2340 docs waveのtip59b932731の受入で、test_t1259_qsub_env_delivery_probe.pyの28件がテスト本体の前に落ちた。22563passed/68skipped/28error。
- 根本原因: autouse fixtureの_clean_detached_source_snapshotが実repoの_repo_snapshotを呼び、git ls-files --others --exclude-standard -zが30秒TimeoutExpiredとなった。個別の判定失敗ではなく共有走査の時間境界であり、遅延のI/O要因までは分離していない。
- 切り分け: 同tip・同fileをrun_tests.py --force-dispatchで単独再走し、991541.nqsvで51passed/15.45秒、job Elapse21S、rc0。waveの変更はdocsのみで、当該fixture・probe・Git呼出しは変更していない。
- 恒久対応: docs/dev-wave/operations.mdのDW-O18へ従い、単独非再現を確認して受入を再走する。timeout拡大・fixtureのstub化・除外・汎用gateの新設は行わない。
- 再発検知: setup tracebackのGit argvと30秒TimeoutExpiredを確認し、同tipの単独走と受入を区別して記録する。ログは専用handoffが指すacceptance-child-3とfocus-t1259.log。

## 再発

### F273

- **再発: 2026-09-10** — T-2340 docs wave、tip1f7f21dc9の受入でtest_sigterm_ignoring_child_is_killedがcommunicateの10秒TimeoutExpiredになった。bnode047/gw36/request991511、receiptなし、loadavg54.95。本文・入口・phase差分からlauncher制御への変更はなく、同tipの単独再走991516は1passed/7.53秒、rc0。DW-O18で受入を再走し、期待値・制限値・除外は変えない。
