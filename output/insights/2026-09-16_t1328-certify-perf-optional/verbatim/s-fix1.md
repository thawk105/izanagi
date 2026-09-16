# 段 6 fix 報告 (1 巡目) — [T-1328]

## 変更した file と assertion の旧 → 新

変更は [orchestrator/tests/test_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/orchestrator/tests/test_pegasus_tools.py) の承認済み4テストと専用 helper 2件のみです。

| 対象 | 旧 → 新 |
|---|---|
| policy・順序検査 | 候補全滅で即時失敗 → 最終 PATH → canonical probe → receipt 判定 → argv 生成。selection／symlink は候補成功時のみ。既存 policy・event・unsupported 検査を維持。 |
| 候補全滅 | 必ず rc=2 → unavailable は rc=0・receipt 引数あり、available は引数なし。selection／symlink／failure 不在を確認。probe_error は rc=2・argv 不在も確認。新契約に合わせ改名。 |
| unsupported smoke | 必ず停止 → literal perf の結果で継続。`<not supported>` 保存・候補非選択を維持。 |
| calibrate 失敗 | `USE_PERF` 未定義 → `USE_PERF=1` を設定し、既存 rc=7・failure・job-result・argv assertion をすべて維持。no-perf の receipt 引数・rc=1・終端保存を追加。 |

production・他のテスト・docs は変更せず、commit・push も行っていません。

## 実走した nodeid と結果

`PYTHONPATH=.` の自走 harness を使用。以下は `orchestrator/tests/` 起点で、`::*` は全 parameter を含む全件です。

| 実走範囲 | 緑 | 赤 |
|---|---:|---:|
| `test_pegasus_tools.py::*` | 72 | 0 |
| `test_pegasus_calibration_workload.py::*` | 79 | 0 |
| `test_calibrator_certify.py::*` | 86 | 0 |
| `test_official_perf_closure.py::*` | 7 | 0 |
| **合計** | **244** | **0** |

修正対象の実走 nodeid：

- `test_certify_perf_stage_is_policy_driven_fail_closed_and_precedes_calibrate`
- `test_perf_stage_all_candidates_failed_uses_canonical_receipt[unavailable,available,probe_error]`：各 parameter
- `test_perf_stage_rejects_not_supported_smoke_output[unavailable,available]`：各 parameter
- `test_calibrate_failure_survives_err_trap_and_writes_job_result`：内部で rc=7／rc=1 の両対照

`git diff --check` も成功。未実走は repository 全 suite、実認証 job、性能測定、変異実走です。

## ホスト環境依存の排除

- 候補全滅・unsupported の2件は Python directory を含め PATH を隔離し、literal perf を fixture で固定しました。
- `REPO_ROOT` は実 repo を指定し、実 canonical probe module を使用しました。
- policy 検査はソースを検査し、終端検査は明示した `USE_PERF` と timeout stub の rc を使用します。
- 揮発する hash・日付・ホストの perf 有無は期待値へ追加していません。

実行対象は `certify_calibration.sh` の候補選択から argv 保存まで、および argv 生成から job 終端までの production 断片です。後者は **stub 検証であり、実 `os.execv` の証明ではありません**。

## 残る赤と帰属

指定範囲に残る赤はありません。承認外のテスト関数・クラスが不変であることも AST 比較で確認しました。

## 総括

承認された4件の契約移行を完了しました。  
指定4ファイル全244件を実走し、すべて緑です。  
production・他テスト・docs の編集、commit・push は行っていません。