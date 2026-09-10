# [T-1721] A-1 sized study の変異 matrix

- `authority: none` / `default_effect: no-state-change`
- 対象 commit: `e22f5ac65073b74e232e03319982e97a0cabb9e5`
- runner: `python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_paired.py
  orchestrator/tests/test_paper_story_a1_job_contract.py
  orchestrator/tests/test_p3_exploration_namespace.py -q -rf --force-dispatch`
- spec: `mutation-spec-final.json` (sha256 `1c903b80d05f04cb0b28a6878db3e5f925a4beb698a19fb03f6b430c6bc048c4`)
- 台帳: `mutation-ledger.json`

## 本走の結果

baseline **PASSED** (233 passed)。登録 9 件が**全件 KILLED**、SURVIVED と MISMATCH は 0。

| 変異 | 位置 | 期待 node 数 | 結果 |
|---|---|---|---|
| `MUT-T1721-LEN-STATS` | `positional_statistics` の長さ検査 | 1 | KILLED |
| `MUT-T1721-LEN-ARM` | `_validate_arm` の長さ検査 | 4 | KILLED |
| `MUT-T1721-ABOVE-FLOOR` | 判定 1 (`abs(mean) - h > B`) | 2 | KILLED |
| `MUT-T1721-BELOW-FLOOR` | 判定 2 (`abs(mean) + h <= B`) | 2 | KILLED |
| `MUT-T1721-VARIANCE-FLAG` | `variance_plan_breach` | 2 | KILLED |
| `MUT-T1721-PUBLISH-GATE` | 全 workload 終端要求 | 1 | KILLED |
| `MUT-T1721-OVERREJECT-POSITIVE-CONTROL` | 長さ検査を過剰に狭める | 23 | KILLED |
| `MUT-T1721-POLICY-FROZEN-DESIGN` | 凍結設計値との固定値比較 | 2 | KILLED |
| `MUT-T1721-POLICY-DF-AND-FROZEN-DESIGN` | 上記 + 自由度整合検査 (両層) | 3 | KILLED |

正例対照は受理集合を過剰に狭める向きの変異で、23 件の検査が赤化した。受理集合を縮める wave の
過剰拒否を検出する登録である (DW-M01)。

## 再照準の erratum (DW-M02)

**初回 probe で `MUT-T1721-POLICY-DF` (自由度整合検査 `df != reps - 1` の単独無効化) が SURVIVED した。**
初回結果は消さずここに残す。

原因は遮蔽である。同じ関数の直後にある凍結設計値との固定値比較
(`if any(workload.get(key) != value for key, value in expected.items())`) が同じ入力を先に弾く。
`WORKLOAD_DESIGNS` は `df` を含むため、自由度が不整合な policy は固定値比較だけで拒否される。

実効 gate へ再照準し、両層同時変異まで裏取りした。

- 固定値比較だけを潰す → 2 node が赤化 (`reps-k-mismatch`, `k-mismatch`)
- **両層を同時に潰す → 3 node が赤化** (上記 + `df-mismatch`)

差分の `df-mismatch` が、自由度検査が実際に効いていることの証拠である。単独では発火しない
**冗長 gate** として、単独変異は本走の証拠から外した (DW-M03)。

## 走行時の異常 (変異判定ではない)

再照準の probe は 2 度、dispatch の待ち行列で止まった。

- 1 回目: baseline が `rc=16` / `artifact_error: receipt scheduler_logs.stdout.path がない`。
  所要 903 秒で、`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE` の既定 900 秒に一致する。
  混雑時の infra 失敗であり、変異判定でも実装の赤でもない。
- 2 回目: `--resume` は `rc=16` で終わった baseline を再実行せず、記録済み attempt を読み直して
  同じ判定で止まった。走り直すには `--out` / `--attempt-out` / `--scratch-root` を新しくした
  新規走行が要る。
- 3 回目: 同 env を 5,400 秒へ広げ、出力先ごと新規にして完走した。

## 還元判断

CCBench 本体への還元候補は含まない。
