所見 [5] は `closed` です。[対象テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2515-author/orchestrator/tests/test_pegasus_calibration_workload.py:78) を以下のように強化しました。

| 所見 | 状態 | 対応 |
|---|---|---|
| [5] job body の検出力不足 | `closed` | 正例 5 値と非 canonical 負例 6 値を実起動し、rc・stage・拒否文言まで検査 |

- 正例: `5 / 20 / 50 / 80 / 95`
- 負例: `+5 / 05 / " 5" / "5 " / ５ / 51`
- invalid protocol を gate 直後の停止点にしたため、変異時も receipt の 60 秒待ちへ入りません。
- 新規 pytest node は 0。既存 node を 1 起動から 11 起動へ拡張しました。見積りは約 0.1 秒/起動 × 11 件 ≈ 1.1 秒（fixture 準備除く、各起動 1 秒未満）。
- production 2 ファイルの SHA-256 は編集前後で一致。docs、台帳、production、共有 fixture は未変更です。

検査結果:

- Python 構文検査: pass
- `git diff --check`: pass
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_job_rechecks_the_submission_workload_and_records_it`: **実装済み・未実走**。規定ランナーが `qstat -Q` rc=1 で dispatch に失敗し、child は未起動でした。

静的な波及可能性:

- caller: production caller への波及なし。
- shared fixture: `conftest.py` や共通 helper の変更なし。既存のローカル copytree・`mkdir` shim・`tmp_path` のみ再利用。
- consumer test: 同 node の実行時間増加のみ。他 node の期待値・skip・xfail・parameterization は変更なし。

## 総括

- job body の正例 5 件・負例 6 件を実起動で固定しました。
- 変異 A は正例、変異 B は `05` の拒否理由検査で検出されます。
- production、docs、台帳は変更しておらず、commit も作成していません。
- 親は利用可能な実行環境で上記 nodeid の正常時 green、変異 A/B の red、各起動 1 秒未満を確認してください。