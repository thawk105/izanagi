| residual | status (`closed` / `partial` / `regressed`) | exact evidence | concrete DW-G05 impact |
|---|---|---|---|
| 1. gitlink pure deletion versus replacement by normal blob/tree, including old worktree identity and common modules metadata cleanup with unchanged evidence | `closed` | Target の blob/tree path は [`_normal_entry_paths()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:1001) で保持され、replacement は [`path/.git` と common `modules/path` のみを残存検査](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:1034)、pure deletion は path 全体と modules metadata を検査します。静的テストは pure deletion の両残存→worktree-only cleanup→metadata cleanup と同一 A/T/audit を固定し（[test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:606)）、normal tree では target blob の維持、旧 `.git` identity、metadata-only、同一 evidence の `already-landed` を固定（[test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:670)）、normal blob も独立固定しています（[test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:752)）。 | 残余なし。純削除の厳格な受理集合を維持しつつ、正当な gitlink→blob/tree 置換は旧 identity と modules metadata の cleanup 後、監査列を変更せず受理できます。 |
| 2. option-insensitive obvious alternate Python land helper and direct Git ff command detection, with ordinary prose/non-land/non-ff positives | `regressed` | 指定された `python3 -u` と `git --no-pager/-c` 負例は静的に固定されています（[test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py:2388)）。しかし Python regex は interpreter 後の任意 token を無差別に飛ばすため（[check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:245)）、非-land の `python3 -m py_compile tools/alternate_land.py` も一致します。Git regex も `merge` より前の任意 token を許すため（[check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:251)）、非-merge の `git rev-parse -- merge --ff-only` も一致します。追加 positive は別名 Python script と `git merge` の `--ff-only` 不在だけで、この実行 selector/subcommand 誤認を固定していません（[test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py:2422)）。 | 必須 `check_docs` が正当な read-only validation/inspection command を alternate land と誤認し、Claude/Codex の docs acceptance set を縮小します。これにより otherwise-valid な certified 選択・レポート・台帳を含む wave の記録／land が不当に遮断されます。 |

Fix-3 regression:

- option 対応のため追加された任意-token wildcard が、Python の実行 selector（`-m`/`-c`）と Git の最初の subcommand を識別せず、非-land／非-ff command を新たに拒否します。

Style/nit/backlog:

- なし。

## 総括

NO-GO