## 挿入位置と本文

現行 [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/p3_s4_loop_pegasus.sh:317) の `claim_root` 検査終了、すなわち現行 321 行目の後かつ `prebuild_source_root=` の前へ次を挿入する。`TMPDIR` は現行 149 行目で `export TMPDIR=$scratch` 済みである。

```bash
POLICY=$repo/tools/pegasus/policy.json
if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  refuse "policy file missing, not regular, or a symlink"
fi
policy_output=$(
  "$PY" -I -B - "$POLICY" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    policy = json.load(handle)
keys = (
    "gflags_source_path",
    "gflags_expected_head",
    "glog_source_path",
    "glog_expected_head",
)
for key in keys:
    if type(policy.get(key)) is not str or not policy[key] or "\n" in policy[key]:
        raise SystemExit(f"invalid policy field: {key}")
for key in ("gflags_expected_head", "glog_expected_head"):
    if re.fullmatch(r"[0-9a-f]{40}", policy[key]) is None:
        raise SystemExit(f"invalid policy git pin: {key}")
for key in keys:
    print(policy[key])
PY
)
readarray -t policy_values <<<"$policy_output"
if [[ ${#policy_values[@]} -ne 4 ]]; then
  refuse "policy yielded an unexpected field count"
fi
GFLAGS_SOURCE_PATH=${policy_values[0]}
GFLAGS_EXPECTED_HEAD=${policy_values[1]}
GLOG_SOURCE_PATH=${policy_values[2]}
GLOG_EXPECTED_HEAD=${policy_values[3]}

CC_PATH=$(command -v gcc)
CXX_PATH=$(command -v g++)

# 出典: floor_scoping.sh:205-283。pinned gflags/glog build prologue を同手順で踏襲。
if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  refuse "gflags source path missing"
fi
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD)
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  refuse "gflags source HEAD mismatch"
fi
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all)
if [[ -n "$GFLAGS_STATUS" ]]; then
  refuse "gflags working tree is dirty"
fi

GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
mkdir "$GFLAGS_BUILD_DIR"
gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
timeout 60 "${gflags_configure_argv[@]}"
timeout 60 "${gflags_build_argv[@]}"
timeout 60 "${gflags_install_argv[@]}"

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  refuse "glog source path missing"
fi
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD)
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  refuse "glog source HEAD mismatch"
fi
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all)
if [[ -n "$GLOG_STATUS" ]]; then
  refuse "glog working tree is dirty"
fi

GLOG_BUILD_DIR="$TMPDIR/glog-build"
GLOG_INSTALL_DIR="$TMPDIR/glog-install"
mkdir "$GLOG_BUILD_DIR"
glog_configure_argv=(cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DWITH_GTEST=OFF -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$(realpath "$CC_PATH")"
  "-DCMAKE_CXX_COMPILER=$(realpath "$CXX_PATH")")
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
timeout 120 "${glog_configure_argv[@]}"
timeout 120 "${glog_build_argv[@]}"
timeout 120 "${glog_install_argv[@]}"

export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"
```

現行 160-165 行目の sanitized PATH では shim 内に `python3` しかないため、静的確認結果は `command -v gcc` が `/usr/bin/gcc`、`command -v g++` が `/usr/bin/g++`。その `realpath -e` はそれぞれ `/usr/bin/x86_64-linux-gnu-gcc-11`、`/usr/bin/x86_64-linux-gnu-g++-11` だった。

## CMAKE_PREFIX_PATH の扱い

exact export は両 install の成功後、かつ現行 323 行目の `prebuild_source_root=` より前に置く。以後 unset、上書き、局所 subshell 化をせず、現行 365 行目の prebuild 呼出しと 433-445 行目の両 driver 分岐へ継承させる。現行 34 行目の初期 sanitize は残す。

移植元から落とす、または適応する箇所は次のとおり。

- `$TOOLS/policy.json` は移植先に `TOOLS` がないため `$repo/tools/pegasus/policy.json` に適応する。
- `CMAKE_PATH`、compiler/cmake の path・version 出力、gflags/glog の HEAD・status 出力は provenance file 用なので落とす。
- 6 command の `$PROVENANCE_DIR/*.stdout` / `*.stderr` redirect は落とし、argvと timeout は変えず job 標準出力・標準エラーへ流す。
- `CMAKE_PREFIX_PATH_PREVIOUSLY_SET`、previous value、`cmake-prefix-path.json` heredoc は D1773(b) により落とす。初期 sanitize 済みなので旧値保存も不要。
- 移植元の TMPDIR 作成、Python 選択、floor driver 呼出しは移植先に既存実装があり、prologue 本体ではないため移さない。

## 契約テストの改訂

現行 [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_p3_s4_loop_job_contract.py:131) の `required` へ、少なくとも次の label と literal fragment を加える。

| label | fragment literal |
|---|---|
| `dependency-policy-path` | `POLICY=$repo/tools/pegasus/policy.json` |
| `dependency-policy-fields` | `"gflags_source_path",\n    "gflags_expected_head",\n    "glog_source_path",\n    "glog_expected_head",` |
| `dependency-compilers` | `CC_PATH=$(command -v gcc)\nCXX_PATH=$(command -v g++)` |
| `gflags-head-exact` | `"$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD"` |
| `gflags-dirty-all` | `GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all)` |
| `gflags-configure-root` | `gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"` |
| `gflags-configure-definitions` | `-DCMAKE_POSITION_INDEPENDENT_CODE=ON -DREGISTER_INSTALL_PREFIX=OFF` |
| `gflags-build-argv` | `gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)` |
| `gflags-install-timeout` | `timeout 60 "${gflags_install_argv[@]}"` |
| `glog-head-exact` | `"$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD"` |
| `glog-dirty-all` | `GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all)` |
| `glog-configure-definitions` | `-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"` |
| `glog-build-argv` | `glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)` |
| `glog-install-timeout` | `timeout 120 "${glog_install_argv[@]}"` |

現行 352-370 行目の order marker は、`claim_root` と `prebuild_source_root` の間を次の literal 順にする。

```python
'claim_root="$repo/output/env/',
"POLICY=$repo/tools/pegasus/policy.json",
'GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD)',
'timeout 60 "${gflags_install_argv[@]}"',
'GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD)',
'timeout 120 "${glog_install_argv[@]}"',
'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"',
"prebuild_source_root=",
'"$PY" - "$prebuild_receipt"',
```

現行 396-411 行目の refusal 一覧へ、`policy file missing, not regular, or a symlink`、`policy yielded an unexpected field count`、`gflags source path missing`、`gflags source HEAD mismatch`、`gflags working tree is dirty`、`glog source path missing`、`glog source HEAD mismatch`、`glog working tree is dirty` を加える。

現行 415-492 行目の fragment mutant へ加える literal は次のとおり。

| label | fragment | replacement |
|---|---|---|
| `dependency-policy-path` | `POLICY=$repo/tools/pegasus/policy.json` | `POLICY=/tmp/policy.json` |
| `dependency-compilers` | `CC_PATH=$(command -v gcc)\nCXX_PATH=$(command -v g++)` | `CC_PATH=$(command -v gcc)\nCXX_PATH=$(command -v gcc)` |
| `gflags-head-exact` | `"$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD"` | `"$GFLAGS_SOURCE_HEAD" != ""` |
| `gflags-dirty-all` | `GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all)` | `GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=no)` |
| `gflags-build-argv` | `gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)` | `gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 47)` |
| `glog-configure-definitions` | `-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"` | `-DWITH_UNWIND=ON "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"` |
| `glog-install-timeout` | `timeout 120 "${glog_install_argv[@]}"` | `timeout 60 "${glog_install_argv[@]}"` |

現行 326-343 行目の禁止検査は、prefix だけを whitelist signature として分離する。`--no-build`、include・launcher、shim の拒否は残す。

```python
allowed = 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"'
prefix_assignments = [
    line for line in body.splitlines()
    if re.search(r"(?<![-A-Za-z0-9_])CMAKE_PREFIX_PATH(?:\+)?=", line)
]
if prefix_assignments != [allowed]:
    raise AssertionError("forbidden-cmake-environment-injection")

order = (
    'timeout 60 "${gflags_install_argv[@]}"',
    'timeout 120 "${glog_install_argv[@]}"',
    allowed,
    '"$PY" - "$prebuild_receipt"',
)
if any(body.count(marker) != 1 for marker in order):
    raise AssertionError("forbidden-cmake-environment-injection")
positions = [body.index(marker) for marker in order]
if positions != sorted(positions):
    raise AssertionError("forbidden-cmake-environment-injection")

forbidden_assignment = re.search(
    r"(?m)^\s*(?:export\s+)?(?:CMAKE_PROJECT_INCLUDE"
    r"(?:_BEFORE)?|CMAKE_PROJECT_TOP_LEVEL_INCLUDES|"
    r"CMAKE_(?:C|CXX)_COMPILER_LAUNCHER)=",
    body,
)
if forbidden_assignment is not None:
    raise AssertionError("forbidden-cmake-environment-injection")
```

現行 535-545 行目の parametrize へ、部分値、別変数値、2 回目を加える。

```python
pytest.param(
    'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR"', id="partial-prefix"),
pytest.param(
    'export CMAKE_PREFIX_PATH="$OTHER_GFLAGS:$OTHER_GLOG"',
    id="different-prefix-variables"),
pytest.param(
    'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"',
    id="second-exact-prefix"),
```

位置負例と受理正例も固定する。

```python
def test_dependency_prefix_before_install_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    exact = 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"'
    anchor = 'timeout 120 "${glog_install_argv[@]}"'
    mutant = source.replace(exact + "\n", "", 1).replace(
        anchor, exact + "\n" + anchor, 1)
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_forbidden_job_constructs(mutant)


def test_exact_dependency_prefix_export_is_accepted() -> None:
    _assert_forbidden_job_constructs(JOB.read_text(encoding="utf-8"))
```

## admission registry

変更不要。[admission_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/admission_registry.json:106) の class、reason、primary gate、evidence は、依存の private build を足しても「PBS compute job body」という分類から変わらない。

[test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_hooks.py:3050) の class 鏡像と同 3209-3214 行目の exact entry 鏡像も現状のまま整合する。無内容な registry 更新や鏡像変更は行わない。

## consumer 閉包

`git grep` 相当の結果から、実行される consumer と影響は次のとおり。

- `test_p3_s4_loop_job_contract.py`: job body、registry、README を直接読む。禁止検査は現状のままだと新 export で赤になるため、上記改訂が必須。
- `orchestrator/tests/test_hooks.py`: registry の class と全 entry を鏡像化する。registry 不変なら赤要因なし。
- `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py`: README の admission 表・tag・fenced command と registry を検査する。§0 表と qsub fenceを変えなければ赤要因なし。
- `orchestrator/tests/test_pegasus_calibration_workload.py`: README を読むが、検査対象は calibration submitter の文言であり今回の §7 修正とは独立。
- `tools/pegasus_admission_registry.py`: registry の汎用 loader。registry 不変なら影響なし。
- `docs/pegasus-runbook.md:508` は分類の投影行であり不変。`docs/decisions.md`、archive、`output/insights` の grep hit は履歴参照で、実行 consumer ではない。

## README §7 の案

```markdown
- `python3.10` を解決し、interpreter-only shim を PATH 先頭に置く。`cmake` / compiler の wrapper・launcher は置かない。
- policy pin 済み gflags/glog を `$TMPDIR` へ build/installし、exact な `CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` を prebuild 前から driver 本走まで保持する。別 provenance file は作らない (D1773)。
```

## (P1)〜(P7) への所見

- (P1) 同意。移植元の8個の `fail 2` は同文 message の `refuse` に写す。
- (P2) 同意。`--untracked-files=all` を両 source で保つ。
- (P3) 条件付き同意。今回の静的解決値は `/usr/bin/gcc`、`/usr/bin/g++` だが、親実測で buildcache の compiler manifest と一致を確認する。
- (P4) 同意。6 command の出力は job 標準出力・標準エラーへ流す。
- (P5) 同意。receipt schema は変えず、job-private prefix が build identity に入ることを受容する。
- (P6) 同意。`claim_root` 検査後、`prebuild_source_root=` 前が最小で明確な挿入点である。
- (P7) 同意。compute 実走は land 条件にせず、queue 状態を見て段4で決める。

## 総括

変更対象は job body、契約テスト、親が更新する README の3 file。policy、registry、hooks、buildcache、driverは変更不要である。pytest は実行しておらず、緑とは判定していない。