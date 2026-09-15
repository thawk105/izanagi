## 変更前の挙動

時間判定は `CLI予約 + 600 ≤ 6610 ≤ 要求7200`。その他の受理・拒否条件とともに、変更後も同じです。

計測未完了の部分標本から accepted を新たに作りません。ただし、公開後の TERM では accepted な公開物と wrapper の非ゼロ終了が併存しえます。この既存挙動も変えていません。

## 実装

指定の2ファイル・3箇所だけを変更しました。

- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/tools/pegasus/certify_calibration.sh:10)：変更後10–24行のコメント、787–806行の formula。1080 の意味、3250 の内訳、8840 の保証限界・未計上処理、未実行の予約定数、公開後 TERM の限界を記載。
- [test_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/orchestrator/tests/test_pegasus_tools.py:212)：212–239行の逐語 pin。代入式と formula 全体を固定し、検査を緩めていません。

`6610` の代入式、PBS `02:00:00`、要求 `7200`、reserve `600` は維持。両 policy と `cli.py` は HEAD との差分なし。`finalize_reserve(600)` はコメント・formula 両方に残しています。

## 実走結果

指定コマンドを実行しました。

```bash
PYTHONPATH=. python3 orchestrator/tests/test_pegasus_tools.py
```

- 範囲：同ファイル全体、**69 passed／14.25秒／rc=0**
- 対象 nodeid：`orchestrator/tests/test_pegasus_tools.py::test_certify_uses_frozen_cli_names_and_reservation_exports` を含む[全69件一覧](/tmp/t2563-impl-test-nodeids.txt)
- `git diff --check`：rc=0
- 所有外テストは未実走です。

## 波及の静的列挙

参照関係から確認した範囲です。

| 参照元 | 読み取り経路・波及 |
|---|---|
| `test_pegasus_tools.py` | script の直接読込、断片実行、資材コピー。全体を実走済み |
| `test_pegasus_calibration_workload.py:408,518,550,606,734,749,795` | `JOB.read_text()` から workload・build・argv 等を検査。430・1504行の fixture コピーにも新版が入る |
| `test_official_perf_closure.py:536` | `_production_perf_files()` が script を走査。perf 実行箇所は未変更 |
| `test_ccbench_spawn_sites.py:871` | `_production_build_sources()` が script を走査。build 箇所は未変更だが行番号は移動 |
| `test_pegasus_policy_registry.py:327,487` | tracked source の heredoc を読み、移設済み policy key の参照を検査。参照処理は未変更 |
| `submit_certify.sh:117` | script SHA を取得。新版の submit receipt に新しい SHA が記録される |
| `make_acquisition_receipt.py` → `schema_v2.py:423` | formula は非空文字列として検証。新文面も条件を満たす |
| `calibration_verify.py`／`collect_receipt.py` | 成果物・receipt の hash に新文面が反映される。現行 formula による再計算はない |

共有 fixture `conftest.py::valid_reservation_environment` は7200を持つ合成入力で、script を読みません。`test_schema_v2.py::_valid_document` も変更不要です。

## 総括

**指定の記述変更を実装し、69件のテストが成功しました。受理・拒否条件は不変です。**

docs・過去 receipt は未編集、commit・push は未実施です。最大経路を収容する時間式再凍結は未解決であり、T-2563 の完了とは扱いません。