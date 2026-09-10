## 実 runner が例外捕捉 rep で出す形の実測

実 runner の両経路を確認しました。

- 例外捕捉時に `execution_failure=True` を設定。
- `finally` で rc、counter、perf を保存。
- throughput 算出前に `continue` するため、例外 rep の `throughput` は `None`。

根拠: [runner.py:957](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix2/orchestrator/calibrator/runner.py:957)、[runner.py:1171](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix2/orchestrator/calibrator/runner.py:1171)

## 置いた負例 (file:line) とその入力

[test_s8b_floor_campaign.py:9475](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix2/orchestrator/tests/test_s8b_floor_campaign.py:9475)

入力は 1 rep で、次の形です。

- exact 7 key
- `rep_index=0`
- `returncode=0`
- `counter_status="complete"`
- `missing_perf_events=[]`
- `perf_raw` は 4 イベント完備
- `throughput=None`
- `execution_failure=True`
- `ScalePoint.throughputs=[]`

現行期待値は `rep_integrity_failures=1`、`exec_failures=1`、qualified throughputs は `[]` です。

## 他の連言が先に偽にならないことの根拠

test 内で対象連言以外を個別に検査しました。key 集合、型、rep 位置、rc、derived status、missing 一致、`perf_raw` の Mapping 性と exact 4-key、`derived_status="complete"` はすべて真です。

`throughput=None` は complete 述語の条件ではなく、実 runner の例外時出力と一致します。raw throughput 列と `ScalePoint.throughputs` もともに空なので整合検査を通ります。

## M6 を殺すことの確認方法と結果

[test_s8b_floor_campaign.py:9526](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix2/orchestrator/tests/test_s8b_floor_campaign.py:9526) に、`execution_failure is False` だけを除いた局所射影を書き下しました。

同一入力で結果は次のように変化します。

- 現行: `rep_integrity_failures=1`
- M6 相当: `rep_integrity_failures=0`
- 両方: `exec_failures=1`、throughputs `[]`

したがって M6 適用時は現行期待値で赤になります。

## 実走した nodeid と結果

実走 nodeid:

`orchestrator/tests/test_s8b_floor_campaign.py::test_execution_failure_true_alone_prevents_complete_rep_projection`

結果: **PASS**。一時 script から import して直接実行し、rc=0 でした。

指定の file 直接実行は rc=0、出力なしで、self-run harness がないため収集 0 件でした。一時 script は確認後に削除済みです。

## 総括

M6 を単一理由で殺す負例を追加しました。本作業で変更した追跡下 file は `orchestrator/tests/test_s8b_floor_campaign.py` のみです。production、`docs/`、`output/` は変更せず、git と commit も実行していません。