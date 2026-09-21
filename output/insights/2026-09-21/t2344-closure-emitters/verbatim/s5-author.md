## 実装

**プランv2を指定9ファイルに実装済み・未実走です。** commit／branch／push／mergeは行っていません。

- 現行tupleをexact-96へ前進。既存85本の順序を保ち、`closure-head.json.proposed`との全順序一致を確認。
- exact-85の独立literal、専用歴史validator、decoder分岐、凍結scopeを追加。
- codec 4群・admission 6群を新設。新11本のdrift検査と既存22本の検査を分離して維持。
- layer3、timeout、図provenance、s8b unavailable scopeの期待値を追随。

## 受理範囲とscope

変更前は通常v2が85、歴史入口が85／63／62／24。変更後は通常v2が96のみ、歴史入口が96／85／63／62／24です。旧grammarをcertifiedへ通す緩和はありません。

現行scopeは96／173／77と指定日付・commitへ更新。歴史85のscopeは変更前の文字列とUTF-8 bytesで一致します。旧63／62／24のvalidator、通常decoder、epoch hash式のソース不変を静的照合しました。

## 固定値の独立算出

productionをimportせず、変更前tupleのAST literalと`closure-head.json.proposed`から標準ライブラリで算出しました。

`b_i = SHA256(ASCII("epoch closure fixture {i}\n"))` とし、宣言順で以下を計算しています。

- path hash：`SHA256(Σ(path UTF-8 + NUL))`
- epoch：`E1:`＋`SHA256(b"campaign-verifier-epoch/v1" + Σ(path UTF-8 + NUL + b_i))`

裁定の4値すべてと一致しました。

| 値 | 算出結果 |
|---|---|
| 現行96 epoch | `E1:244d998f35b0f7deae215a4053d9dde5acf60fc0775e4ea4c7a315579e7da07a` |
| 現行96 path hash | `5c2c4a6a45ec44f46d655f1d9c43f1d877d5547fc46ff308fbdaa61df6683af4` |
| 歴史85 epoch | `E1:bc8a6c8c6fd792ab6f21f22107f5313fb64ef0be1d6f8c97a15065998c423dc7` |
| 歴史85 path hash | `bea3624661166dbe20df206ebd1e4f855f8c13e39721ab67e8b19d981bd6b5a1` |

期待固定値はテスト内のliteralであり、実行時に再生成しません。

## 検査結果

実行コマンドは次のrunnerに、指定されたテスト6ファイルを渡したものです。

```text
PYTHONDONTWRITEBYTECODE=1 IZANAGI_TASK_RUN_AUTO_RECORD=0 python3 tools/run_tests.py -n 0 -p no:cacheprovider <焦点6ファイル>
```

`qstat -Q preflight rc=1`、runner rc=16、`child_started=false`で停止しました。**実走nodeidは0件**です。Pegasus規律に従い、`python3 -m pytest`の直接起動はしていません。

静的検査では、9ファイルの構文、独立期待tuple、旧validator・scope・hash式の不変、既存テスト名の保持、未知grammar負例、`git diff --check`を確認しました。runnerが自動生成したdispatch用4ファイルは削除し、最終差分は指定9ファイルのみです。

焦点走・変異M0〜M13・受入全走は親での実行が必要です。

## 制約meta-testと所有外への波及

静的に洗い出した再検査対象は以下です。いずれも未実走です。

- `test_plain_runner_coverage.py`：自走harness／allowlist検査。
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
- `test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact`
- growth／flaky／foldのhold契約と`test_hold_inventory.py`。

所有外への波及を静的に確認しました。

- `ident.py`、`verify_fanout_worker.py`、`p3_b4_wiring_probe.py`：現行capture対象が96本へ拡大。
- `b10_backoff_static_tail_formal.py`、`layer3_report.py`：85は歴史型で読取。`b10_backoff_shape_sweep.py`のexact-24限定は維持。
- `campaign_lock_test_support.py`とs8a／s6／bench-first／t1998等のfixture：現行tuple列挙により96本へ追随。
- `test_s8b_verdict.py`／`test_s8b_oracle_judge.py`：report fixtureを共有。今回そのhelperは変更していません。

## 総括

exact-96への前進とexact-85の歴史収載を、独立literalのテストと同時に実装しました。
旧validator・scope・epoch hash式の不変は静的確認済みです。
最大のriskは実走未確認であることです。親のcommit済み木で焦点走・変異試験・受入全走が必要です。