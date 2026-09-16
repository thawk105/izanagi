# 段 6 fix 報告 (2 巡目) — [T-1328]

## 原因の判定

**親の仮説は、fixture の欠陥として再現できた。** 修正前、ログインノードの通常実行では対象2件とも成功したが、親 Python に `SIGTERM=SIG_IGN` を設定すると、両方が報告と同じ `assert 0 == 2` で失敗した。失敗時の receipt も両方 `status=available / reason=available / rc=0` だった。

ただし、元の計算ノードの signal 設定は直接観測していないため、当該実走の原因確定とは区別する。

別原因の検討：

- **shebang の interpreter 解決:** `sys.executable` の絶対パスを使用。同じ interpreter のまま signal 設定だけで成否が変わった。
- **PATH 隔離の破れ:** PATH は fixture 用 directory に限定。呼出しログでも fixture の `base/perf` が canonical probe を受けていた。
- **xdist worker 環境:** worker を使わない直列実行でも再現したため、再現に xdist は不要。
- **tmp の noexec:** fixture の実行ログと正常な receipt 生成を確認。今回の再現原因ではない。

## 変更した file と fixture の旧 → 新

| file | 変更 |
|---|---|
| `orchestrator/tests/test_pegasus_calibration_workload.py` | `perf_fixture` の自己終了を SIGTERM → SIGKILL |
| `orchestrator/tests/test_pegasus_tools.py` | `_run_perf_stage` 内の fixture の自己終了を SIGTERM → SIGKILL |

それぞれ理由をコメントで追加。期待値・他 parameter・共有構造は変更していない。

## 選んだ手段が継承された signal 設定に強い理由

SIGKILL は無視・捕捉・ブロックできないため、親の signal 処理設定に依存せず fixture 自身を終了させる。既存 production の `rc < 0` → `probe-signal` → `probe_error` を通り、断片の rc=2 を引き続き要求する。

## 実走した nodeid と結果

すべて `pegasus02`、`PYTHONPATH=.` で実走。

| 範囲・条件 | 結果 |
|---|---|
| `test_pegasus_tools.py` 全件：自走 harness | **72 passed** |
| `test_pegasus_calibration_workload.py` 全件：指定の `pytest.main` 形式 | **79 passed** |
| 下記2 nodeid：修正前・通常設定 | **2 passed** |
| 下記2 nodeid：修正前・SIGTERM 無視を継承 | **2 failed**（報告と同じ赤） |
| 下記2 nodeid：修正後・SIGTERM 無視を継承 | **2 passed** |

対象 nodeid：

- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_perf_preflight_argv[probe_error]`
- `orchestrator/tests/test_pegasus_tools.py::test_perf_stage_all_candidates_failed_uses_canonical_receipt[probe_error]`

`git diff --check` 成功。`b8e2e06dd` との差分は上記2 fixture の変更だけ。

## 残る赤と帰属

今回の修正後の実走に赤はない。計算ノードでの再検証は未実施で、親の dispatch 検証に委ねる。ログインでの成功だけをもって計算ノードでも修復済みとは主張しない。

## 総括

SIGTERM 無視の継承による fixture の誤動作を再現し、SIGKILL へ変更した。  
通常全151件と、SIGTERM 無視を継承した対象2件が成功した。  
production・他テスト・docs は変更せず、commit・push は行っていない。