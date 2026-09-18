# 段 4 裁定 — [T-2498] guard_bash の重量判定を script-executor の内側実行対象へ再帰適用する

親 (dev-wave manager) の裁定。段 2・3 は D1891 が plan + 別系統相談を経て設計を確定済みなので省略した。
この文書が実装子 (author A / author B) と段 6 レビューの唯一の権威である。

## 1. 確定済みユーザー裁定 (逐語要約、変更不可)

- **D1891 (2026-09-09):** `hooks/guard_bash.py` の重量 interpreter 検出について、**既存の script-executor
  parser が抽出した内側の実行対象へ、同じ重量判定を再帰的に適用する**。wrapper module の列挙追加はしない。
  却下: wrapper module の列挙を足す (既に列挙されている)。判定軸を allowlist へ反転する (正当な `python -m`
  を広く拒否する側へ受理集合が動く)。
- **D427:** hooks/ 配下は有効化前 commit (`d92800f49`) を base にした第 2 worktree で Codex author が書き、
  テストは wave worktree で別の author が書く。親が統合 commit → wave branch へ merge → 反転検査。
- **D428:** wave 前後の同一 corpus で `deny → allow` 反転 0 件。1 件でもあれば land しない。
- **D1719:** 第 2 worktree の作業ツリー版は古いので現行 main 全文を射影し、親が sha256 で検算する。
- **D95:** 実装面 (コード・テスト) は Codex role=author。親は直接編集しない。
- 規律 2: 正しさゲート (ここでは重量拒否・admission 拒否) を緩める変更は採らない。

## 2. 現行の受理・拒否 (main 38353207f、`decide(cmd, root, site="PEGASUS_LOGIN")` の実測)

| 形 | 現行 | 修正後の期待 |
|---|---|---|
| `python3 -m pytest -q` | DENY (interpreter の baseline 重量対象 (pytest)) | DENY (不変) |
| `python3 -m cProfile -m pytest -q` | **ALLOW (素通し)** | DENY |
| `python3 -mcProfile -mpytest -q` | ALLOW | DENY |
| `python3 -m cProfile -o /tmp/p.out -m pytest -q orchestrator/tests/test_hooks.py` | ALLOW | DENY |
| `python3 -m profile -m pytest -q` | ALLOW | DENY |
| `python3 -m coverage run -m pytest -q` | ALLOW | DENY |
| `python3 -m pdb -m pytest -q` | ALLOW | DENY |
| `python3 -m trace --trace --module pytest -q` | ALLOW | DENY |
| `python3 -m runpy pytest -q` | ALLOW | DENY |
| `python3 -m cProfile -m cProfile -m pytest -q` | ALLOW | DENY |
| `python3 -m cProfile -m cmake --build build` | ALLOW | DENY (内側 `python3 -m cmake --build` は直接形でも DENY) |
| `python3 -m cProfile -m pytest --collect-only` | ALLOW | ALLOW (非実行形の正例) |
| `python3 -m cProfile -m pytest --help` | ALLOW | ALLOW |
| `python3 -m cProfile tools/run_tests.py` | ALLOW (sanctioned) | ALLOW |
| `python3 -m cProfile /tmp/safe.py` | ALLOW | ALLOW |
| `python3 -m cProfile --help tools/pegasus/exec_calibrate.py` | ALLOW (既存 pin) | ALLOW |
| `python3 -m trace --report -f /tmp/counts tools/pegasus/exec_calibrate.py` | ALLOW (既存 pin) | ALLOW |
| `python3 -m runpy tools/pegasus/exec_calibrate.py` | ALLOW (既存 pin: runpy は path を module 名として失敗) | ALLOW |
| `python3 -m timeit tools/pegasus/exec_calibrate.py` | ALLOW (既存 pin、executor でない) | ALLOW |
| `python3 -m cProfile tools/pegasus/exec_calibrate.py` | DENY (admission、F121) | DENY (不変) |
| `python3 -m pydoc tools/pegasus/collect_receipt.py` | DENY (admission) | DENY (不変) |
| site=OTHER / compute の全形 | ALLOW | ALLOW (不変、重量判定は refusing site のみ) |

## 3. 実装の裁定 (author A の仕様)

対象 file: `hooks/guard_bash.py` のみ。

1. **内側 program の抽出関数を新設する** (名前は author が決める。例 `_script_executor_program`)。
   入力 `(module, args)`、出力 `(kind, value, rest)` または `None`。
   - `module` が既存 parser の射程 (`_SCRIPT_EXECUTOR_MODULE_OPTIONS` の key、または
     `coverage` / `coverage.__main__` の `run` 副命令) にあり、かつ `_MULTI_TARGET_EXECUTOR_MODULES`
     (pydoc / doctest / unittest) に**含まれない**ときだけ抽出する。multi-target は内側 program を実行しない。
   - option の消費規則 (値を取る option、密着値、`--`、help、`trace --report`) は既存
     `_script_executor_targets` と**同じ表・同じ規則**を使う。共通 helper へ括り出してもよいが、
     **`_script_executor_targets` の返り値は全入力で不変**でなければならない (既存テストが pin する)。
   - `-m` / `--module` (と密着形) → `kind="module"`、`value=<module 名>`、`rest=<以降の全 token>`。
     `runpy` の最初の positional も `kind="module"`。
     **module 形は `_PYTHON_MODULE_RE.fullmatch(value)` のときだけ返す** — path のような不正 module 名は
     Python が import に失敗して何も実行しないので再帰しない (既存 ALLOW pin `-m runpy tools/pegasus/
     exec_calibrate.py` を守るため)。
   - 最初の positional (`--` の直後を含む) → `kind="script"`、`value=<token>`、`rest=<以降>`。
   - help option・非実行 mode (`trace --report`)・program 不在・`coverage` の `run` 以外は `None`。
   - 新しい module 名・option 名を表へ**足さない** (D1891)。

2. **`_heavy_segment_violation` へ再帰を挿入する。** 位置は **shell command-string 再帰 block
   (`if head in {"bash","sh","zsh"} and depth < 2:`) の直後、`_is_sanctioned` 早期許可の前**。
   理由は shell と同じ — sanctioned な target を持つ executor 形が内側の pytest を隠せないようにする。
   - `_python_module_invocation(head, args)` が `(module, module_args)` を返し、上の抽出関数が
     `(kind, value, rest)` を返したら、**同じ raw_head** で内側 segment を合成し
     `_heavy_segment_violation(inner_seg, repo_root, depth + 1)` を呼ぶ。violation があれば返す。
   - 合成の不変条件: 合成した segment を `_heavy_head_and_args` → `_python_prefix_invocation` に
     通すと、抽出した `(kind, value, rest)` と同じ解釈になること (round-trip)。
     module: `[raw_head, "-m", value, *rest]`。script: `[raw_head, value, *rest]`
     (value が `-` で始まるときだけ `[raw_head, "--", value, *rest]`)。
   - **深さ上限は設けない。** 合成 segment は元 segment より必ず短くなる (module: 3+len(rest) <
     5+len(rest)、script: 2+len(rest) < 4+len(rest)) ので停止は保証される。docstring にこの根拠を書く。
     shell 再帰の `depth < 2` は流用しない (2 重 wrapper `-m cProfile -m cProfile -m pytest` に届かせる)。
   - 内側の非実行形 (`--collect-only` / `--help` 等) は既存判定 (`_pytest_nonexecuting`) がそのまま
     効くので、再帰側で別扱いしない。

3. **変えないもの:** `_SCRIPT_EXECUTOR_MODULE_OPTIONS`、`_SCRIPT_EXECUTOR_OUTPUT_OPTIONS`、
   `_MULTI_TARGET_EXECUTOR_MODULES`、`_script_executor_targets` の返り値、`_script_targets`、
   `_executor_output_violation`、`_interpreter_residual_violation`、`_baseline_first_token_violation`、
   `_python_pytest_args`、admission 判定、非 refusing site の挙動、`decide()` の signature。

4. **やってはならない:** 列挙追加、allowlist 反転、一時無効化 flag、env / argv 上書き、
   `hooks/guard_write.py` の編集、テスト・docs の編集、`git add` / `git commit`。

## 4. テストの裁定 (author B の仕様)

対象 file: `orchestrator/tests/test_hooks.py` のみ。既存テストの期待値は変えない。追加するのは:

- **負例 (DENY になるべき、site="PEGASUS_LOGIN"):** §2 の「ALLOW → DENY」全行 + 綴り差の族
  (`-mcProfile -mpytest`、`-qmcProfile -m pytest`、`python3.10 -Bm profile -s cumulative -m pytest`、
  `-m coverage run --branch -m pytest`、`-m coverage run -m pytest.__main__`、`-m pdb -m _pytest.main`、
  `-m trace --trace --module pytest`、`-m runpy pytest`、`-m cProfile -o /tmp/x -- -m pytest` は
  **含めない** (`--` の後は script)、`env FOO=1 nice -n 0 python3 -m cProfile -m pytest`、
  `bash -lc 'python3 -m cProfile -m pytest -q'`、2 重 wrapper `-m cProfile -m cProfile -m pytest`、
  script 形 `-m cProfile pytest`、`-m cProfile -m pytest tools/check_ai_provenance.py` (借用でも DENY))。
  各 assert の失敗 message に「executor 越しの重量実行が login で通った」の趣旨を書く。
- **正例 (ALLOW を維持、site="PEGASUS_LOGIN"):** `-m cProfile -m pytest --collect-only`、
  `-m cProfile -m pytest --help`、`-m coverage run -m pytest --collect-only`、`-m cProfile /tmp/safe.py`、
  `-m cProfile -- /tmp/safe.py --version`、`-m runpy tools/pegasus/exec_calibrate.py` (既存 pin の再掲)、
  `-m cProfile -m timeit x`、`-m cProfile -m json.tool /tmp/a.json`。
- **不変 (非 refusing site):** 負例の代表 3 形を `site="OTHER"` と `site="PEGASUS_COMPUTE"` (既存テストが
  使う site 名を踏襲) で ALLOW。
- **既存拒否の正例維持:** `python3 -m pytest -q` DENY、`-m cProfile tools/pegasus/exec_calibrate.py` DENY を
  同じテスト群に再掲 (変異 M1 で直接形が壊れないことの目印)。
- 変異 matrix が node を名指しするので、テスト関数名は `test_bash_login_executor_recursion_*` の prefix で揃え、
  負例・正例・不変を **別関数**にする (1 変異 1 赤理由、DW-M01)。
- 子は pytest を走らせられない。module を import して各関数を直接呼び、正例関数は現行 main でも通ること、
  負例関数は現行 main で **赤になる** (DID NOT RAISE ではなく AssertionError) ことを確かめて報告する。

## 5. 変異事前登録 (実装後に anchor を確定、DW-M01)

| id | category | 位置 | 期待 |
|---|---|---|---|
| M0 | equivalent | 新設関数の docstring / comment だけ | SURVIVED |
| M1 | negative | 再帰呼び出しを恒偽化 (`if False and …`) | KILLED (負例関数) |
| M2 | negative | 抽出関数の module 形 (`-m` / `--module`) を `None` に落とす | KILLED (負例 module 形) |
| M3 | negative | `coverage run` 経路を落とす | KILLED (負例 coverage) |
| M4 | negative (過剰拒否の正例、DW-M01) | 合成 segment から内側 args (`rest`) を落とす → `--collect-only` が消え拒否 | KILLED (正例関数) |
| M5 | negative | script 形の抽出を落とす | KILLED (負例 script 形 `-m cProfile pytest`) |
| M6 | negative | `_PYTHON_MODULE_RE` 検査を外す | KILLED (正例 `-m runpy tools/pegasus/exec_calibrate.py`) |
| M7 | negative | multi-target 除外を外す (pydoc/doctest/unittest も再帰) | 赤理由が 1 つに絞れなければ登録しない (実装後判断) |
| M8 | negative | 再帰位置を `_is_sanctioned` 早期許可の後へ移す | 対照。既存 corpus に sanctioned target + 内側 pytest の形が無ければ等価 = SURVIVED 対照として登録 |

## 6. 親の検査 (子は行わない)

焦点走 (`tools/run_tests.py` で test_hooks / test_codex_hooks / test_codex_worker_launch / test_plain_runner_coverage /
test_ccbench_spawn_sites)、D428 反転検査 (job dir の runner、pre = main 38353207f、post = wave tip、corpus =
test_hooks.py の全 command 文字列 + §2 の形)、変異 matrix (計算ノード)、受入全走、provenance 監査、check_docs。
