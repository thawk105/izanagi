## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| 1. loader の iff 不成立 | partial | 実装・負例追加済み。pytest は rc=16 で未実走 |
| 2. scope 外の `campaign_runs` 試験 | partial | 該当試験と不要 import を除去済み。互換性試験は未実走 |
| regressed | なし | 静的検査では検出なし |

## 変更内容

[trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/campaign/trial_registry.py:4490) で、origin start に digest 対象そのものの `launch_admission` record を保持させました。

loader は start 行を読んだ時点で、次を直接照合します。

- `launch_admission.origin_binding` の存在
- `origin_run_plan_sha256` の存在
- carrier の存在
- `launch_admission_sha256` と carrier bytes
- trial、P/C、measurement head、campaign、workload の束縛

terminal projection は origin binding の代理として使用しません。originless start には carrier を追加しないため、書き手の originless bytes は実装上不変です。

[test_trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/tests/test_trial_registry.py:4004) に、start-only loader が以下を拒否する負例2件を追加しました。

- originless start + digest
- origin start - digest

[test_reflux_originless_compatibility.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/tests/test_reflux_originless_compatibility.py:1265) から架空の `campaign_runs` 試験だけを除去しました。非揮発 leaf と closed key 集合の比較は残しています。

## 検査

- `git diff --check`: 成功
- 3ファイルの `py_compile`: 成功
- loader 直接 probe: 正常な2形を受理し、(g)/(h) を拒否
- iff 述語だけを一時無効化した probe: (g)/(h) が双方とも受理され、他層の先行拒否なし。変更は復元済み
- `tools/run_tests.py` による焦点 nodeid 群: rc=16、`child_started=false`
- originless 非揮発 leaf 試験: rc=16、`child_started=false`

したがって pytest の正確な red 集合は未確認です。

## 静的波及

- production caller `p3_autonomous_workload_trial.py:4928` の署名変更は不要です。origin lifecycle start bytesだけに carrier が増えます。
- `test_p3_autonomous_workload_trial.py:11038` は digest 値だけを検査しており、追加 carrierとの静的衝突はありません。
- lifecycle prefix bytesとSHAは origin経路で変わります。originless経路は変わりません。
- carrierを持たない旧形式の origin startは意図的に拒否されます。tracked corpusに該当 lifecycle artifactはありませんでした。
- formal consumerは lifecycle rowを直接decodeしないため、静的な呼出し波及はありません。
- 編集対象は指定された3ファイルだけです。commitは作成していません。

## 総括

所見1は loader が origin binding 実体を直接読む形へ修正し、start-only 負例2件を追加。  
所見2の scope 外 `campaign_runs` 試験を除去し、leaf／closed-key 比較は維持。  
`git diff --check` と `py_compile` は成功。  
直接 probe と述語無効化 probeでは拒否位置と単一理由性を確認。  
pytestは Pegasus dispatch rc=16で子が起動せず、未実走。  
残る赤は実走不能のため不明。  
commitは作成していない。