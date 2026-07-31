# 段6 fix 第3巡 — U2 Group Name / symbolic worker 閉鎖

- 旧 `s6-fix3-u2` worker は `run.log.done=137` で終端 receipt 不成立だったため、出力を採用しなかった。
- 残存 owner bytes を新規隔離 job
  `/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-fix3-u2-finalize-resume/`
  の単一 workspace-write completion worker で監査した。
- completion は exit 0、`tools/check_codex_output.py` green、
  `closed 2 / partial 0 / regressed 0`。
- fix 対象は U2 所有の次の 4 files だけ:
  `tools/pegasus/test_dispatch.py`、`tools/run_tests.py`、
  `orchestrator/tests/test_pegasus_test_dispatch.py`、
  `orchestrator/tests/test_run_tests_nproc.py`。
- NQSV `Group Name` を per-job qstat、lookup candidate、receipt / WAL、resume の全 consumer で
  policy account/group へ exact 束縛し、wrong-group 負例と same-group 正例を置いた。
- compute の `auto` / `logical` は文字列で U1 resolver へ渡し、返値を実 pytest argv へ反映する。
  OTHER の symbolic 表記は維持する。spy は両 spelling を異なる返値で固定した。
- 4 対象外の tracked + nonignored untracked manifest と HEAD 差分 hash は worker 開始・終了で一致。
- 統合後 staged patch SHA-256 =
  `1f98a868d24b0009b017abb9d7204651ba9b6aa0e63964e94c040ce0b90105b7`。
- worker は Python 3.10 の compile と `git diff --check` だけを実行した。
  pytest、mutation、build、qsub、qstat、qdel は未実走であり、green / KILLED は主張しない。
