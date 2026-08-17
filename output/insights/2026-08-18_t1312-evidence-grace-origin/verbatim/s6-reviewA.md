## 静的照合

論理時計を `T = state.started_ns` とすると、preflight 境界は `T+0.10`、spawn 境界は `T+0.12`、監視 sample は `T+0.13, 0.14, ...` です。[test_codex_worker_launch.py:3523](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:3523)

| deadline 起点 | deadline | 停止 sample | `supervision_drain` |
|---|---:|---:|---:|
| `state.started_ns` | `T+0.05` | 最初の poll `T+0.13` | `0.01` |
| `preflight_now_ns` | `T+0.15` | 3 回目 `T+0.15` | `0.03` |
| `spawn_completed_ns` | `T+0.17` | 5 回目 `T+0.17` | `0.05` |

3 値は異なり、新設テストは旧起点と preflight 起点の双方を殺せる。恒真ゲートではありません。phase は spawn 境界から supervision 完了境界までを算出しています。[codex_worker_launch.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:424)

監視中の生存 process 経路では `_monotonic_ns()` は 1 周 1 回です。[codex_worker_launch.py:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1803) 2 回目は `process.poll()` が終了を返した自然終了経路だけです。[codex_worker_launch.py:1808](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1808) `no_rollout` は生存し続けるため、5 poll と `0.05` の実測はコードと整合します。[test_codex_worker_launch.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:1404)

retry では attempt 1 後の `polling=True` が attempt 2 の最初の絶対時刻を `0.01` 進め得ますが、preflight wrapper が `polling` と `spawn_sample_pending` をともに初期化してから `0.10` を加えます。[test_codex_worker_launch.py:3532](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:3532) 絶対 offset は増えても attempt 2 の各 phase 差は `0.10 / 0.02 / 0.05` のままで、状態汚染はありません。

`git diff` 上、production の機能変更は spawn sample の共用と deadline 起点だけです。[codex_worker_launch.py:1793](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1793) `max_wall_clock_s` の preflight 判定、running 判定、`state.started_ns` による attempt wall clock は不変で、D498 を超える受理集合拡張は見つかりませんでした。[codex_worker_launch.py:1765](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1765) [codex_worker_launch.py:1842](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1842) [codex_worker_launch.py:2004](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:2004)

### A1

- 主張: help 文言の追加が既存の literal 契約を argparse の折返しだけで破壊し、焦点走を既知の赤にしている。
- 根拠: help 文字列が長くなった箇所は [dev_wave_codex.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/dev_wave_codex.py:99)、折返しを正規化せず完全な `--max-wall-clock-s` を要求する箇所は [test_dev_wave_codex.py:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_dev_wave_codex.py:603)。
- 具体的な失敗シナリオ: 現在の terminal 幅では evidence help が `--max-wall-` と `clock-s` に分割され、意味上は正しい help に対して assertion が失敗する。親実測の 180 passed / 1 failed と一致する。
- 重大度: **must-fix** — 成果物影響: 受入走が赤のままで段 6 を閉じられず、実装を統合可能な成果物にできない。

### A2

- 主張: `0.3` 化した `no_rollout` 使用テスト 2 本は、子が stdout を出す前に deadline が来ても同じ assertion 集合を満たし、「session は見えたが rollout が無い」経路を保証しない。
- 根拠: `thread.started` は子プロセス内で flush される [test_codex_worker_launch.py:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:1295) [test_codex_worker_launch.py:1391](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:1391)。関門は空の `session_ids` と rollout 不在を OR で扱う [codex_worker_launch.py:1883](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1883) 一方、該当テストは session 数を検査しない。[test_codex_worker_launch.py:4364](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:4364) [test_codex_worker_launch.py:6123](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:6123)
- 具体的な失敗シナリオ: spawn 後 0.3 秒以上子が schedule されない入力では、`session_ids=[]` のまま最初の disjunct で強制停止し、両テストは rollout 欠落を一度も観測せず通る。`no_thread` テストは emit より前に待つ設計なので、空 session が本来の検査対象であり、この問題には該当しない。[test_codex_worker_launch.py:1382](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:1382)
- 重大度: **should-fix** — 成果物影響: stdout の session-id 取り込み退行が検出されず、正当な worker が missing evidence で拒否されて wave 成果物を失う退行を通し得る。

## 総括

起点判別、時計呼出し数、retry 状態、D498 の受理集合境界はいずれも正しい。  
実装修正が必要な所見は、既知の help テスト赤 1 件。  
テスト検出力には、`0.3` 化した `no_rollout` 2 本の別経路成立が残る。  
pytest は実走しておらず、親提示の実測を前提とした静的レビューである。