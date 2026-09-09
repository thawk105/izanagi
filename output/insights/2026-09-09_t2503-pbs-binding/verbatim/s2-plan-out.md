## 1. 修正案

対象: [t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2290)

(P1) の名前付き定数案を採用する。

- 現行 `:2290` の直前に次を定義する。

```python
_RUNTIME_PBS_RELATIVE_PATH = (
    "tools/pegasus/probes/t316_sandbox_backend_probe.pbs"
)
```

- 現行 `:2293` の `.pbs` literal を `_RUNTIME_PBS_RELATIVE_PATH` に置き換える。`_BOUND_RELATIVE_PATHS` の値と順序は現状のまま維持する。
- 現行 `:2337` を次へ変更する。

```python
repo_pbs = repo_root / _RUNTIME_PBS_RELATIVE_PATH
```

これにより、`:2331-2332` の clean 検査と `:2340-2343` の `runtime_sha256` 生成は従来どおり `_BOUND_RELATIVE_PATHS` 5件を使い、PBS 比較だけが意味の明示された同じ定数を参照する。key 集合と `:2339` の例外文言は変えない。

index 2 への単純訂正は退ける。一文字の最小修正ではあるが、tuple 先頭への追加で再び無言でずれる構造を残す。名前付き定数案は新しい gate や互換層を増やさず、同型再発を小さい差分で防げる。

## 2. 共通テスト準備

対象: [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:5)

- `:5-14` の標準ライブラリ import に `os` と `subprocess` を追加する。
- 現行 `:1404` の `_run` の直前に、正例と負例だけで共有する小さな `_prepare_execution_binding_repo` helper を追加する。
- 利用する fixture は pytest 組み込みの `tmp_path` と `monkeypatch`。`conftest.py` に流用可能な tmp Git repo fixture はない。`:1410-1413` の `real_repo_fixture_lock` は実共有 repo 用なので使わない。
- `:1063-1078` の `_run_injected` は `execution_binding` を注入して `_execution_binding` を迂回するため、今回の被覆には流用しない。

helper は次を行う。

1. `tmp_path / "repo"` を作成し、次の5つを独立 literal で作る。

   - `orchestrator/campaign/condition_meaning_gate.py`
   - `tools/pegasus/probes/t316_sandbox_backend_probe.py`
   - `tools/pegasus/probes/t316_sandbox_backend_probe.pbs`
   - `tools/pegasus/policies/t316_sandbox_backend_v1.json`
   - `tools/pegasus/policy.json`

2. `.py` は例えば `b"print('fixture probe')\n"`、`.pbs` は `b"#!/bin/bash\nexit 0\n"` とし、`repo_py.read_bytes() != repo_pbs.read_bytes()` を明示的に assert する。これが変異検出力の前提になる。
3. `shutil.which("git")` が返す executable と `subprocess.run(..., check=True, capture_output=True, text=True)` を使って、tmp repo 内で `git init`、`git add --all`、`git commit`、`git rev-parse HEAD` を行う。commit には `-c user.name=...`、`-c user.email=...`、`-c commit.gpgsign=false` を与える。
4. ambient Git authorityを避けるため、少なくとも `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、`GIT_COMMON_DIR`、object directory系、`GIT_CONFIG_COUNT`、`GIT_CONFIG_PARAMETERS` を `monkeypatch.delenv` し、`GIT_CONFIG_GLOBAL=os.devnull`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_DEFAULT_HASH=sha1` を設定する。この環境は `_execution_binding` 内の実 Git 呼び出しにも適用される。
5. repo 外に runtime spool と `PBS_NODEFILE` を作る。初期 spool は `.pbs` と同じ bytes にする。
6. `probe.socket.gethostname` を `lambda: "compute-test.example"` に差し替え、nodefile に `compute-test.example\n` を書く。
7. 次の環境変数を設定する。

   - `PBS_JOBID="12345.test"`。実際の `_JOB_ID_RE` は [probe.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:57) の `^[A-Za-z0-9._:-]+$` なので合致する。
   - `IZANAGI_T316_EXPECTED_COMMIT=<rev-parse HEAD>`
   - `IZANAGI_T316_EXPECTED_WORKTREE_ROOT=str(repo_root.resolve())`
   - `PBS_NODEFILE=str(nodefile)`
   - `IZANAGI_T316_RUNTIME_PBS=str(runtime_spool)`

8. `repo_root.resolve()` と同じ `Path` を `_execution_binding` に渡す。

## 3. 負例

追加位置: [test_t316_sandbox_probe.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1404) の直前。

`test_execution_binding_rejects_runtime_spool_matching_python_instead_of_pbs` を追加する。

- 共通 helper で clean な実 Git repo を準備する。
- `.py` と `.pbs` が異なることを再確認する。
- repo 外の runtime spool を `repo_py.read_bytes()` で上書きする。bound path 自体は変更しないため Git clean 関門を通過する。
- `probe._execution_binding(repo_root)` を次で囲む。

```python
with pytest.raises(
    ValueError,
    match="^runtime PBS bytes differ from worktree PBS bytes$",
):
```

正しい実装では spool と `.pbs` が異なるため、目的の比較行 `:2338-2339` でこの例外になる。比較対象を `.py` に戻した変異では hash が一致して例外が出ず、`pytest.raises` が失敗する。前段の設定不備による別の `ValueError` は完全一致の `match` で偽陽性にしない。

## 4. 正例

同じく現行 [test_t316_sandbox_probe.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1404) の直前に `test_execution_binding_binds_runtime_spool_to_pbs` を追加する。

- helper が作った `.pbs` と同じ runtime spool のまま `_execution_binding` を呼び、正常に dict が返ることを確認する。
- 次を確認する。

```python
pbs_sha256 = probe._sha256_file(repo_pbs)
assert binding["runtime_sha256"]["runtime_pbs_spool"] == pbs_sha256
assert (
    binding["runtime_sha256"][
        "tools/pegasus/probes/t316_sandbox_backend_probe.pbs"
    ]
    == pbs_sha256
)
```

この正例も比較先を `.py` にした変異では指定例外で落ちるため、負例と相互補完になる。

## 5. 既存 test への影響

- [test_t316_sandbox_probe.py:1282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1282) は `_execution_binding` 全体を1引数 lambda へ差し替える。関数名、引数、呼び出し方法を変更しないため影響しない。
- 同ファイル内で `_execution_binding` を直接参照する既存箇所は `:1282` だけである。
- `:1063-1078` の既存 probe tests は `execution_binding={"test_injected": True}` を渡すため、新定数の影響を受けない。
- `_BOUND_RELATIVE_PATHS` の値と順序を維持するため、[probe.py:2331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2331) の dirty 検査と `:2340-2343` の receipt key 集合は不変。
- [PBS job body:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54) から `:80` は既に committed `.pbs` と spool を比較しており、編集不要。
- 新規関数名は `test_` で始まり、[test_t316_sandbox_probe.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1404) の `_run` もファイル全体を `pytest.main` へ渡すため通常収集される。
- tmp repo だけを読むので `conftest.py:258-520` の実 repo inventory への登録は不要。acceptance ledger に未知 node がなくても、`conftest.py:1631-1664` は未知 duration を順序決め用の既定 cost として扱い、収集を拒否しない。

## 6. 副作用の棚卸し

repo 内で直接 bytes が変わるのは次の2ファイルだけ。

- `tools/pegasus/probes/t316_sandbox_backend_probe.py`
- `orchestrator/tests/test_t316_sandbox_probe.py`

他の成果物、pin、台帳の更新は無し。brief `:42-44` により現行 probe の file SHA/blob pin は repo 内 hit 0件、`FROZEN_MANIFEST` に t316 はなく、acceptance duration ledger は未知 node を許容することが確認済みである。`.pbs` job body 自体も変更しない。

将来の再実測 receipt では、変更された `.py` に対応する `runtime_sha256` の値は新しい hash になるが、key 集合は変わらない。既存 receipt を書き換える作業は発生しない。

## 7. リスクと落とし穴

- `conftest.py:239-255` の autouse fixture が差し替えるのは `site_policy.socket` だけであり、今回 import 済みの `probe.socket` ではない。テスト自身で `probe.socket.gethostname` を必ず差し替える。
- fake hostname と nodefile の短縮名が一致しないと `probe.py:2319-2322` で比較前に落ちる。両方を `compute-test.example` に固定する。
- hostname を実値のままにすると Pegasus login node 上では `probe.py:2312-2315` が意図どおり拒否するため、login node test が環境依存で落ちる。
- `expected_root` と関数へ渡す `repo_root` の resolve 状態が違うと `:2309-2311` で落ちる。同じ resolved `Path` を双方に使う。
- 5つの bound path のいずれかが未commitまたはcommit後に変更されると `:2330-2335` で落ち、比較先の回帰を検査できない。spool は必ず repo 外へ置く。
- runtime spool と nodefile は `resolve(strict=True)` されるので、環境変数設定前に実ファイルを作る。
- ambient `GIT_DIR`、global signing、SHA-256 object formatなどを残すと tmp repo の HEAD一致や40桁検査が環境依存になる。Git環境の隔離と SHA-1 指定を helper 内で行う。
- Git executable がない場合に skip すると変異検査が消える。`shutil.which("git") is not None` を assert し、依存欠落は明示的に赤にする。
- 負例で単に「何らかの `ValueError`」を期待すると、前段関門の失敗でも通ってしまう。既存の例外文言を完全一致で検査する。

## 8. 検証計画

この plan 段では pytest を実走しておらず、緑とは報告しない。

親の実装後に、追加する正例・負例の2 node、続いて `orchestrator/tests/test_t316_sandbox_probe.py` 全体を正規 runner 経由で実測する。特に負例が目的の例外まで到達することと、既存 `test_publish_preflight_einval_stops_before_measurement` が維持されることを確認する。

## 総括

採用案: `.pbs` path を名前付き `_RUNTIME_PBS_RELATIVE_PATH` にし、tuple と比較行の両方から参照する。index 2 の直接参照は再発耐性がないため採らない。

負例の要点: clean な tmp Git repo で `.py` と `.pbs` を異なる bytes に固定し、`.py` と同じ spool が既存文言で拒否されることを `_execution_binding` の実走で確認する。

未解決の疑問: 設計上の未解決事項はない。pytest の実測結果だけが親の実装段に残る。