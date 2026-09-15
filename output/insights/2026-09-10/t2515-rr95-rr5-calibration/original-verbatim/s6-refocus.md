fix 2 に must-fix はありません。レビュー A [5] は閉じ、レビュー B の real nit は一部だけ残っています。実機で現れた赤は fix 2 が到達可能にした既存の赤です。

## 所見対応表

| 所見 | 判定 | 根拠 | 放置時の影響 |
|---|---|---|---|
| レビュー A [5]: job body の受理集合検査不足 | `closed` | 既存 test node 内で正例 5 値を実起動し、次の protocol gate まで進むことを確認する構造になった。[test_pegasus_calibration_workload.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:142) 非 canonical 6 値は rratio gate の rc、stage、文言を検査する。[test_pegasus_calibration_workload.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:169) これにより `&&` 破壊は正例側、`05` 正規化は負例側で検出される。 | この修正を外すと、全正例拒否で accepted JSON がゼロになる変異、または `05` が canonical `5` として成果物へ進む変異を見逃す。 |
| レビュー B real nit: collected node +11、直列時間増 | `partial` | fix 1 は既存の単一 node 内を 5+6 回の loop にしており、collected node を 11 増やしてはいない。[test_pegasus_calibration_workload.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:78) fix 2 が別の静的 test node を 1 件追加しているため、両 fix 合計の collection 増は +1。[test_pegasus_calibration_workload.py:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:427) 一方、既存 node の shell 起動数は 1 から 11 へ増え、直列時間増は残る。実測秒数は未確認。 | production の値、受理集合、成果物参照は変わらない。影響は test の直列実行時間と collection が +1 されることに限定される。 |

## fix 2 の敵対検査

変数の定義順に破綻はありません。

- `PBS_JOBID` と `PBS_O_WORKDIR` の検証後、`TMPDIR` を確定、作成している。[certify_calibration.sh:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:15) [certify_calibration.sh:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:27)
- `ATTEMPT_DIR` の確定、create-only 作成は selection より先。[certify_calibration.sh:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:41)
- `failure_written` と `write_failure`、ERR trap も selection より先に利用可能。[certify_calibration.sh:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:47) [certify_calibration.sh:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:50) [certify_calibration.sh:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:85)
- selection は `CALIBRATE_PYTHON` と `calibrate_python_rejected` を先に初期化し、各 iteration で `resolved` を代入してから読む。[certify_calibration.sh:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:395) 移動前へ残ったこれらの変数参照はない。
- `run_condition_gate` の関数本体にある `BUILD_SOURCE`、`CCBENCH_BASE`、`configure_argv` は関数定義時ではなく呼出し時に展開される。実際の代入はそれぞれ 561、566、601 行で、呼出しは 612 行。[certify_calibration.sh:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:561) [certify_calibration.sh:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:601)

`CALIBRATE_PATH` の最終値も変わっていません。perf shim は先に作成され、最初の代入、Python のディレクトリを加えた最終代入の順です。[certify_calibration.sh:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:839) [certify_calibration.sh:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:843)

最終値は次のままです。

```text
$TMPDIR/bin:$(dirname "$CALIBRATE_PYTHON"):$PATH
```

条件関門の弱体化もありません。

- 変更されたのは argv 先頭の `python3` から `"$CALIBRATE_PYTHON"` への置換だけ。[s6-fix-diff.patch:177](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2515-calib-rr95-rr5/artifacts/s6-fix-diff.patch:177)
- `BACKOFF_FIXED`、requested value `-1`、`--stock-comparison`、meaning case、`--use-class certified-selection` は維持。[certify_calibration.sh:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:415)
- timeout は 300 秒のまま。[certify_calibration.sh:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:427)
- 呼出しは configure argv 構築後、configure/build 実行前で、silo 限定条件も維持。[certify_calibration.sh:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:611)
- 戻り値を握り潰す `|| true` などはなく、`set -Eeuo pipefail` と ERR trap にそのまま伝播する。[certify_calibration.sh:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:12)

fail-closed の退行もありません。候補不在時は従来と同じ `write_failure 2 interpreter`、同じ文言、`exit 2` です。[certify_calibration.sh:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:408)

発火は build/perf より前へ早まりましたが、完了可能な経路の集合は変わりません。旧配置でも全 protocol が calibrator 起動前に同じ選定を必ず通っていました。非 silo では、以前は build と perf 選定後に失敗していたものが早く失敗するため、失敗経路で残る中間ログは減ります。一方、選定の旧位置までに `PATH` の変更や Python 3.10 候補の生成はなく、`$TMPDIR/bin` に後から作られるのも perf shim だけです。したがって、正常完了できた経路が新たに失敗する条件は見つかりません。

## 静的検査の変異検出力

| 変異 | 判定 | 赤になる理由 |
|---|---|---|
| (a) argv 先頭を素の `python3` に戻す | `KILLED` | `condition_gate_argv` が `"$CALIBRATE_PYTHON"` で始まる完全一致 assertion が失敗する。[test_pegasus_calibration_workload.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:459) |
| (b) selection を関門呼出し後の旧位置へ戻す | `KILLED` | `selection_end < gate_calls[0].start()` が偽になる。[test_pegasus_calibration_workload.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:451) |
| (c) smoke を `True` 固定にする | `KILLED` | version check と、その成功時だけ代入する exact snippet の assertion が失敗する。[test_pegasus_calibration_workload.py:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/orchestrator/tests/test_pegasus_calibration_workload.py:436) |

指定された 3 変異に検出漏れはありません。追加検査は本題に必要ありません。

## 実機証拠との整合

実機の赤は、fix 2 が作ったものではなく、fix 2 が到達可能にした既存の赤です。

- 現行 silo configure は以前から `-DCCBENCH_BACKOFF_FIXED=-1` を含む。[certify_calibration.sh:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:571)
- 関門も以前から `BACKOFF_FIXED`、stock comparison、stock-adaptive-backoff meaning case を検査する。[certify_calibration.sh:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:418)
- source 自身が、現 CCBench pin にこの macro がないことと、silo の既存挙動を裁定待ちで維持していることを記している。[certify_calibration.sh:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-calib-rr95-rr5/tools/pegasus/certify_calibration.sh:607)
- fix 2 の差分は interpreter とその選定位置だけで、macro、pin、meaning case、configure argv、silo 限定条件を変更していない。

したがって、traceback が消えた後の `supply-effectuation: configure-failed` と `runtime-meaning: materialized-branch-invalid` は既存条件の評価結果です。これは must-fix ではなく記録対象です。ただし放置すると silo の rr5/rr95 は関門で停止し、accepted calibration は生成されません。規律 2 により関門を迂回してはなりません。

pytest、変異実走、実機 job はこのレビューでは実行していません。上記の `KILLED` は適用後 source に対する静的な反実仮想判定です。

## 総括

must-fix は 0 件。  
レビュー A [5] は `closed`、レビュー B の実行コスト nit は `partial`。  
fix 2 は関門を弱めず、Python 3.10 選定と fail-closed を正しい順序へ移している。  
実機の構造化された赤は fix 2 が到達可能にした既存の CCBench pin 不整合であり、記録対象である。