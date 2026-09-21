## 環境

各コマンドの出力全文と rc。`""` は空出力を表す。

| command | 出力 | rc |
|---|---|---:|
| `hostname` | `pegasus02` | 0 |
| `id -u` | `31609` | 0 |
| `python3 --version` | `Python 3.10.12` | 0 |
| `pwd` | `/work/1/SFC/tanab/izanagi/.codex/worktrees/selfrun-probe-unit` | 0 |
| `git rev-parse HEAD` | `5efd69367b641b9bfbd6fb426478f66ae5762783` | 0 |
| `git rev-parse --show-toplevel` | `/work/1/SFC/tanab/izanagi/.codex/worktrees/selfrun-probe-unit` | 0 |
| `git status --porcelain=v1 --untracked-files=all` | `""` | 0 |
| `command -v /usr/bin/time` | `/usr/bin/time` | 0 |
| `/usr/bin/time -f 'WALL=%e s MAXRSS=%M KB' true` | `WALL=0.00 s MAXRSS=1284 KB` | 0 |
| `ls -d .pytest_cache orchestrator/tests/__pycache__ 2>/dev/null` | `""` | 2 |

開始時、確認対象のキャッシュディレクトリは両方ともなし。

## 実走結果

hook 判定は明示的に取得できていないため `null`。4コマンドとも各1回、process の起動と終了を確認した。

**2. test_t1259_scan_bound.py**

- `command`: `PYTHONPATH=. /usr/bin/time -f 'WALL=%e s MAXRSS=%M KB' python3 orchestrator/tests/test_t1259_scan_bound.py`
- `attempted`: true
- `started`: true
- `hook_verdict`: null
- `process_rc`: 0
- `wall_s`: 1.87
- `maxrss_kb`: 47564
- `executed_count`: 3
- `failed`: []
- `evidence`:

```text
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.1.1, pluggy-1.6.0
rootdir: /work/1/SFC/tanab/izanagi/.codex/worktrees/selfrun-probe-unit
configfile: pytest.ini
plugins: xdist-3.8.0, cov-7.1.0, hypothesis-6.165.2
collected 3 items

orchestrator/tests/test_t1259_scan_bound.py ...                          [100%]

============================== 3 passed in 0.86s ===============================
IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"serial"}
WALL=1.87 s MAXRSS=47564 KB
```

**3. test_floor_pair_job_contract.py**

- `command`: `PYTHONPATH=. /usr/bin/time -f 'WALL=%e s MAXRSS=%M KB' python3 orchestrator/tests/test_floor_pair_job_contract.py`
- `attempted`: true
- `started`: true
- `hook_verdict`: null
- `process_rc`: 0
- `wall_s`: 1.62
- `maxrss_kb`: 34964
- `executed_count`: 22
- `failed`: []
- `evidence`:

```text
PASS test_hostname_gate
PASS test_job_main_gate_order_and_calls
PASS test_no_build_or_output_replacement
PASS test_pbs_and_walltime_binding
PASS test_registry_entries
PASS test_scratch_name_normalizes_colon
PASS test_scripts_parse
PASS test_submitter_argument_set
PASS test_submitter_head_consistency_preflight
PASS test_submitter_main_gate_order_and_calls
PASS test_walltime_values
PASS test_window_gate_boundaries
PASS test_window_id_and_fields
22 passed, 0 failed
WALL=1.62 s MAXRSS=34964 KB
```

`executed_count` は出力全文の `PASS` 22行に基づく。

**4. test_b5_contrast_launch.py**

- `command`: `PYTHONPATH=. /usr/bin/time -f 'WALL=%e s MAXRSS=%M KB' python3 orchestrator/tests/test_b5_contrast_launch.py`
- `attempted`: true
- `started`: true
- `hook_verdict`: null
- `process_rc`: 0
- `wall_s`: 3.29
- `maxrss_kb`: 57076
- `executed_count`: 38
- `failed`: []
- `evidence`:

```text
......................................                                   [100%]
38 passed in 1.99s
IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"serial"}
WALL=3.29 s MAXRSS=57076 KB
```

**5. test_auditor_gate.py**

- `command`: `PYTHONPATH=. /usr/bin/time -f 'WALL=%e s MAXRSS=%M KB' python3 orchestrator/tests/test_auditor_gate.py`
- `attempted`: true
- `started`: true
- `hook_verdict`: null
- `process_rc`: 0
- `wall_s`: 0.37
- `maxrss_kb`: 27684
- `executed_count`: null
- `failed`: []
- `evidence`:

```text
WALL=0.37 s MAXRSS=27684 KB
```

静的確認 `grep -n __main__ orchestrator/tests/test_auditor_gate.py` は出力 `""`、rc=1。全文確認でも `__main__` はなく、これは **test 未実行の偽緑**。件数を示す出力がないため `executed_count` は `null`。

## 作業 repo の変更有無

| command | 開始時の出力全文 | rc | 終了時の出力全文 | rc |
|---|---|---:|---|---:|
| `git rev-parse HEAD` | `5efd69367b641b9bfbd6fb426478f66ae5762783` | 0 | `5efd69367b641b9bfbd6fb426478f66ae5762783` | 0 |
| `git status --porcelain=v1 --untracked-files=all` | `""` | 0 | `""` | 0 |

HEAD と status に差なし。

終了時の `ls -d .pytest_cache orchestrator/tests/__pycache__ 2>/dev/null` は rc=0、出力全文：

```text
.pytest_cache
orchestrator/tests/__pycache__
```

開始時にはなかった上記2ディレクトリが生成された。削除・修正はしていない。

## 総括

コマンド2〜4を実走し、`process_rc / wall_s / executed_count` は順に `0 / 1.87 / 3`、`0 / 1.62 / 22`、`0 / 3.29 / 38`。
コマンド5も process は終了したが、rc=0 は test 未実行の偽緑。
HEAD・status は変化なし。ignored の `.pytest_cache` と `orchestrator/tests/__pycache__` は生成された。
実装・修正・commit は行っていない。この probe の結果は計測でも受入でもない。
