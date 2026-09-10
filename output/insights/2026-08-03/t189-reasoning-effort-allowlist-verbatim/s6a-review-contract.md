## 所見

### V5 の `build_child_argv` E2E 負例が存在しない

- 深刻度: must-fix
- 根拠: plan v2 は E2E 負例を必須としている [s4-adjudication.md:131](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s4-adjudication.md:131)。実装された負例は二つの直接検査を一関数にまとめており [test_dev_waves_schema.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:272)、両 membership を外すと最初の `parse_worker_spec` assertion で停止して argv 側へ到達しない。`build_child_argv` の既存テストは `effort="high"` の正例だけである [test_dev_waves_worker.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_worker.py:47)、[test_dev_waves_worker.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_worker.py:79)。
- 失敗シナリオ: `parse_worker_spec` と `validate_child_argv` の membership を同時に削除 → `WorkerSpec(effort="none")` が child argv まで通るが、現行テストは実 child 経路の過剰受理を観測しない。
- 成果物影響: repo-policy 外の effort が試行台帳・receipt に入り、材料レポートと certified 選択の根拠を誤った構成へ帰属させる。

### 正例が正本から独立せず、V7〜V9 の期待赤を実経路で出せない

- 深刻度: must-fix
- 根拠: 面 2 は `CLAUDE_EFFORTS` 自体をループする [test_dev_waves_cli.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:151)、面 3 も同様である [test_dev_waves_schema.py:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:286)。面 1 は五値をハードコードしているが、実起動前の正本 membership assertion で停止する [test_codex_worker_launch.py:554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:554)、[test_codex_worker_launch.py:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:562)。正本自体の縮小は別の exact meta-test が検出する [test_effort_levels.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_effort_levels.py:39) が、plan v2 の期待 node [s4-adjudication.md:138](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s4-adjudication.md:138) とは異なる。
- 失敗シナリオ: `CLAUDE_EFFORTS` から `low` または `max` を削除 → 面 2・3 の正例はその値を実行せず緑のまま。Codex の `max` 削除では面 1 が fake launch 前に落ち、live 経路を検査しない。
- 成果物影響: 正当な `low` / `max` 試行が過剰拒否され、台帳行と比較材料が欠落して certified 選択が変わりうる。

### `test_effort_levels.py` 単独では通常 import 経路を検査しない

- 深刻度: nit
- 根拠: 正本を `spec_from_file_location` で直接ロードしている [test_effort_levels.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_effort_levels.py:16)。通常 import は別の consumer test が間接的に通す [test_dev_waves_cli.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:33)。
- 失敗シナリオ: `tools.dev_waves` の package 解決だけが壊れる → `test_effort_levels.py` の単独 runner は成功しうる一方、実 CLI は import error で起動不能になる。
- 成果物影響: entrypoint が起動前に止まるため値の偽記録はないが、試行台帳と材料レポートを生成できなくなる。

### docstring に T-183 / T-184 の ownership 参照がない

- 深刻度: nit
- 根拠: plan v2 は未実装部分の所有を docstring に書く契約である [s4-adjudication.md:72](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s4-adjudication.md:72)。実装は model 依存性と非保証範囲までは記すが、所有先を記していない [effort_levels.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/effort_levels.py:7)。指定された四つの説明内容自体は揃っている。
- 失敗シナリオ: `gpt-5.4-mini` × `max` が repo gate を通って backend で拒否される → limitation は読めるが、恒久対応を T-183 / T-184 へ追跡できない。
- 成果物影響: 材料レポートの limitation 参照から恒久対応の所有先が欠落するが、受理集合や台帳値は変わらない。

## 契約確認

- 正本は [effort_levels.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/effort_levels.py:17) にあり、両定数とも五値で `none` はない。
- `launcher.py` は四値 [launcher.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/launcher.py:85)、`spec.py` は二値 [spec.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/spec.py:70) のままで、増減はない。
- 面 1・2 は `choices=` [codex_worker_launch.py:2476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:2476)、[cli.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/cli.py:93)。面 3 は形検査後に membership がある [schema.py:802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:802)、[schema.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:858)。
- `none` は `_EFFORT_RE` の先頭 `n` と残り `one` の双方に一致し、長さも上限内である。したがって単独 membership 削除時、負例は別検査でなく過剰受理により赤になる。
- 面 1 の rc=2 は `invalid choice` と `--reasoning` も同時確認するため、fake child/path 由来の rc=2 と区別できる [test_codex_worker_launch.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:542)。
- `kind` assertions は例外発生確認に付随しており、診断文字列だけの pin ではない。`HIGH` のテストだけが意図どおり diagnostic sensitivity pin である [test_dev_waves_schema.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:293)。
- `check-receipt --expect-reasoning`、`_validate_receipt`、`ReasonCode`、schema JSON は未変更。既存 assertion の反転・緩和・skip・削除、現行 hash の新規差し込み、揮発診断 payload の pin もない。
- CLI `_run()` は全15関数を列挙し、新規2関数も登録済み [test_dev_waves_cli.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:390)。
- 受理集合の変化は、面 1・2では「従来受理した任意の指定文字列」から五値への縮小、面 3では `_EFFORT_RE` の言語から五値への縮小だけである。大文字・前後空白・空文字は面 1・2で新規拒否、面 3では従来から形検査で拒否される。いずれも裁定された値域外入力であり、意図外の blocker はない。

## 総括

- GO / NO-GO: **NO-GO** — blocker はないが、V5 E2E 欠落と V7〜V9 の正例検出力不足が must-fix。
- blocker: **0件（なし）**。
- 新テストは値域検査を外したとき赤になるか: **Yes** — V1〜V4 の各単独 gate は過剰受理により赤になる。ただし V5 の要求された E2E 証拠は存在しない。
- 正例が全5値を被覆しているか: **No** — 現行正本では五値を回るが、正本縮小から独立した実経路被覆になっていない。
- pytest: **走らせていない**。本レビューは `git diff --cached` と実コードの静的検査のみ。