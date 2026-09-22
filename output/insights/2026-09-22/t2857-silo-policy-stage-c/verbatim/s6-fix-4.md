## 照合した実行経路

以下はソースと提供ログの静的照合です。`C`＝`orchestrator/campaign`、`Q`＝`orchestrator/tests`、`E`＝`external/ccbench`。実機の `compile_commands.json` 自体は今回提供されていません。

| case群 × 外部との交点 | 照合先 file:line | 結果・対応 |
|---|---|---|
| 全build：owner TU選択 | `E/cmake/ProtocolHelpers.cmake:32`、`C/condition_meaning_gate.py:1902` | 不一致。4 targetからYCSBの出力だけを選択するよう修正 |
| 全build：target・成果物 | `E/cmake/ProtocolHelpers.cmake:34`、`C/s3_lock_coverage.py:230` | 一致。`ycsb_silo.exe`、`build/cc/silo/ycsb_silo.exe` |
| coverage・smoke：依存物準備と分離 | `C/s3_mocc_lock_coverage.py:257`、`C/silo_policy_coverage.py:684` | 一致。準備stockを先行し、case別・trace/perf別にbuild dirを分離 |
| norw×2：workload・結果 | `C/s2_verify_calibration.py:80`、`C/pipeline.py:161` | 一致。S2構成・3秒・NUMA、cycles/verdict/exit_code/commitsを取得 |
| lockskip・early-unlock×2：workload・X理由 | `C/s3_lock_coverage.py:73`、同`:148` | 一致。SINGLE_FLAGS、traceからX理由を集計 |
| 負例6：前処理証拠 | `patches/broken-silo-policy-lockskip-validation.patch:10` | lockskipの固定インデント依存を修正。対象文の連続性は維持 |
| 焦点3・probe変異5・共有対照：CLIと集計 | `E/include/ycsb.hh:20`、`E/cc/silo/include/common.hh:32`、`E/common/result.cc:34` | 一致。flag名・型、abort/commit出力がparserと対応 |
| 同上：probe出力 | `patches/instr-silo-function-policy-probe.patch:54`、`E/common/runner.hh:298` | 正常終了はstdoutのworker別TLS destructor出力を取得。verifierより先にparseするよう修正 |
| no-clamp・prefix unlock両出口：timeout | `patches/silo-function-policy-variant.patch:88`、`E/cc/silo/transaction.cc:255` | 長時間待機・lock待機と120秒timeoutが対応。理由名を維持し、上限・部分出力を追加記録 |
| no-reload・no-limit・hook欠落3・wrong-reason | 各 `patches/broken-silo-policy-*.patch:5`、`C/silo_policy_coverage.py:65` | 方策・probe設定・変異箇所の対応に不一致なし。動的検出は未確認 |
| 全trace：verifier CLI・JSON | `orchestrator/verifier/cli.py:48`、同`:90`、`orchestrator/verifier/report.py:126` | 引数・cwd・結果fieldは一致。verifier timeoutで既取得の観測を失う点を修正 |
| flag境界4：override・エラー文 | `patches/silo-function-policy-variant.patch:35` | 一致。前処理の結合形式 `-o…`／依存ファイル指定も除去するよう補強 |
| TRACE=0：診断コード不混入 | `C/silo_policy_coverage.py:611` | 通常buildのargvと前処理結果を確認する経路に不一致なし |
| smoke：stock＋4方策、verify・bench | `C/pipeline.py:193`、`C/silo_policy_coverage.py:635` | 1M／48 threads／skew 0.9／3秒、同構成bench各1走で一致 |
| smoke：honest identity | `C/source_digest.py:2413`、`C/silo_policy_coverage.py:642` | materializeしたsourceから取得し、build前後比較・方策別token判定を維持 |

## 直した内容

- `C/silo_policy_coverage.py:387`：owner TUとYCSB target出力の両方が一致する1行だけを受理します。`output`なしの`-o`形式も扱い、該当0行・複数行は拒否します。
- 同`:406`、`:464`：前処理で結合形式の出力指定を除去し、lockskip証拠をインデントに依存させなくしました。対象文が存在しない場合や`continue`が別文の場合は受理しません。
- 同`:510`：trace timeoutの上限と取得済みstdout/stderrを保存します。不完全な出力からprobe成功を生成しません。
- 同`:527`：probe・commit・X理由をverifier実行前に取得し、verifier timeoutでも保持します。`verifier-timeout`は`trace-timeout`と区別し、変異検出成功にはなりません。

## 確認の実測

- 変更した2ファイルの `python3 -m py_compile`：終了コード **0**。
- AST・テキスト読み取り：build sink **379行**と`Q/test_ccbench_spawn_sites.py:2935`のpinが一致。pin変更なし。
- テストmoduleのimport、テスト・driver・buildの実行なし。

追加した以下のnodeはすべて**実装済み・未実走**です。接頭辞は`orchestrator/tests/test_silo_policy_coverage.py::`です。

- `test_owner_command_selects_ycsb_from_four_targets_and_rejects_ambiguity`
- `test_preprocess_strips_output_and_dependency_forms_and_replaces_defines`
- `test_lockskip_evidence_ignores_preprocessor_indentation_but_requires_target`
- `test_trace_timeout_preserves_partial_output_and_exact_reason`
- `test_verifier_timeout_keeps_run_witnesses_without_becoming_trace_timeout`
- `test_verify_cli_and_projection_match_verifier_result`
- `test_run_cli_trace_location_counters_probe_and_bench_projection`

既存テスト全件と、driverの`coverage`／`smoke`も**実装済み・未実走**です。

## 変えていないことの根拠

編集操作は指定されたdriverとテストの2ファイルだけです。既存assert、condition gate、必須集合の完全一致、norwの`exit_code == 1`、機構変異の赤集合、焦点到達要件は変更していません。

patch・docs・output・その他tracked fileへの書込み、gitコマンド、commit操作は行っていません。

## 未了と疑問

- 実機でのbuild・焦点到達・変異検出は未確認です。patch内部に追加の実行時欠陥を確定する証拠は得ていません。
- 期待するtrace timeoutは3走で計360秒です。ただしcoverageは準備込み24 build・通常19 verifier呼出し、smokeは11 build・10 verifier呼出しがあり、各verifier上限600秒から**全体1時間以内は保証できません**。完走所要の実測が必要です。
- 強制終了されたworkerのTLS destructor出力は取得できません。今回保存するのは既に出力された部分だけで、期待timeoutの3変異はいずれもprobe無効です。

## 総括

I1と、I2の照合で見つけた前処理・観測保持の問題を修正し、回帰テスト7件を追加しました。構文検査は成功、実機での合格確認は未実施です。