# [T-2232] 段 6 裁定追補 — レビュー A / B の所見 (2026-09-05、統合 commit 11a7af4b4)

| # | 所見 | 判定 | 対応 |
|---|---|---|---|
| D1 | A-1: 3 箇所の clean 検査 `[[ -n "$(git status ...)" ]]` は `git status` の非 0 を clean と読む (superproject :174、CCBench :204、hydrate source :333) | real、must-fix | 出力を変数へ capture し rc を明示検査 (`status=$(git ... ) \|\| refuse ...`) してから空判定。contract に fragment と「status 非 0 → rc=2」の負例 harness (git stub が rc=1・空 stdout) |
| D2 | A-2: `GIT_*` unset 後に `GIT_OPTIONAL_LOCKS=0` が無く、観測用 `git status` が hydrate source の index を更新しうる | real、must-fix | sanitize 直後に `export GIT_OPTIONAL_LOCKS=0`。contract fragment |
| D3 | A-3: M7 の登録文と試験 mutant の不一致 | nit | 変異台帳の M7 を「`SANITIZED_PATH` を `$PATH` にして shim を PATH から外す」と書き直す (spec はそのまま) |
| D4 | B-1: worktree container 拒否本体が固定されず、login harness は host gate で止まるので到達しない | real、must-fix | rc=2 文言一覧へ追加。bnode stub (`hostname`→`bnode001`) で REPO_ROOT を `<tmp>/.claude/worktrees/x` にした harness を追加し、rc=2・文言・sentinel (git/cmake/python3.10/qstat) 未呼出しを要求 |
| D5 | B-2: `qstat_jobid=${PBS_JOBID#0:}` が契約に無い | real、must-fix | fragment を追加し、`qstat_jobid=$PBS_JOBID` への load-bearing mutant test |
| D6 | B-3: 順序検査が raw `source.index` で dead comment の前置複製に欺かれる | real、must-fix | 順序 marker は heredoc 除去 + comment 行除去した実行面で照合し、各 marker の出現数がちょうど 1 であることを要求。前置複製の負例を追加 |
| D7 | B-4: parametrized fragment mutant の `assert source.count(fragment) == 1` が production 変異時に二重赤を作る。M5 harness は mutant でなく正しい式を評価 | real、must-fix | count 前提を `<= 1` (重複だけ拒否) にし、helper の検出を検査する形へ。M5 は mutant source から `pbs_jobid_path_component=` の実行行を抽出して bash で評価し、`:` が残ることを赤にする |
| D8 | B-5: README が指す insight README が未存在 | refuted (段 7 で作成) | 段 7 で `README.md` を書く。fix 対象外 |
| D9 | B-6: acceptance ledger 被覆 (40 node 増、登録 0) | nit | 焦点走に `test_acceptance_schedule_order.py` を加えて 90% gate を確認。赤なら ledger 更新を Codex fix へ |

fix は 1 単位 (job body + contract テスト)。既存テストの期待値は変えない。fix 後に焦点再レビュー 1 本 (DW-S06-C)、変異 probe → 本走、受入。
