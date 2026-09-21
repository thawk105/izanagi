1. **変更前の挙動**

B-5 と非 B-5 の既存 3 経路（proposal 単独、proposal＋pair、fixture）は、未設定入力では `IZANAGI_BENCH_LOCK` 未設定で driver を起動し、既定の home 共有 `~/.izanagi/bench.lock` を使用していました。

2. **変更箇所**

- [p3_s4_loop_pegasus.sh:661](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a1/tools/pegasus/p3_s4_loop_pegasus.sh:661)：B-5 driver 直前に指定の export を追加。他の bytes は HEAD と一致することを確認しました。
- [test_p3_s4_loop_job_contract.py:1219](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a1/orchestrator/tests/test_p3_s4_loop_job_contract.py:1219)：harness で外部 lock 値を除去し、stub が環境を別 JSONL に追記。戻り値 3 要素と既存 evidence 辞書比較は維持。
- 同ファイルの `_read_driver_environment:1412`、default test:1908、pair test:1930、`_assert_b5_driver_history:2013`：観測 assert を追加。B-5 の期待値は harness の scratch-base と固定 PBS_JOBID の `:`→`_` 規則から独立に構成。全 arm・rc と stock 未設定／0 をカバーします。

3. **静的検査**

| コマンド・検査 | 結果 |
|---|---|
| `bash -n tools/pegasus/p3_s4_loop_pegasus.sh` | hook が実行前に拒否。rc なし・未実施 |
| `python3 -B - <<'PY' … compile(…, 'exec') … PY` | rc=0。ファイルを生成せず Python 構文確認 |
| `python3 -B - <<'PY' …` による bytes・AST literal 確認 | rc=0 |
| `git diff --check` | rc=0 |
| `git status --short` | rc=0。所有 2 ファイルのみ変更 |

4. **meta-test への静的影響**

以下は実走結果ではなく、コード・literal・差分の確認結果です。

| 対象 | 追加行の影響 |
|---|---|
| `_assert_static_job_stage_order` | 30 marker 全て出現 1 回、順序不変 |
| `B5_PINS`／`test_b5_fragment_mutants_have_one_static_failure` | 全 19 pin が各 1 回。新規 pin なし、削除変異の欠落理由に干渉なし |
| `test_b5_duplicate_driver_and_late_branch_are_rejected` | driver 数・分岐抽出アンカー不変。追加行も移動対象 block 内 |
| `test_job_body_has_valid_stdin_shell_syntax` | heredoc・制御構造を変えない export 文。実検査は未実施 |
| `test_k2_argv_expansion_is_proposal_only` | K2 展開数・proposal 内の位置不変 |
| harness のアンカー置換 | bootstrap／SANITIZED_PATH／scratch_base 全て各 1 回 |
| `_shell_submitter_violations` | export は submitter 宣言・qsub・間接呼出しに該当しない |
| `STOCK_PINS`／stock fragment mutants | 全 7 pin が各 1 回、不変 |
| registered fragment mutants／禁止 CMake・shim・no-build 検査 | 対象 literal・順序・禁止パターンに干渉なし |
| trap・拒否 rc・PBS_JOBID・resolver 検査 | 対象部分は bytes 不変 |
| B-5 fallthrough mutant | 既存の起動数 assert が環境 assert より先。二重起動の検出理由を維持 |

5. **所有外への波及**

- `test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench`：依存 source 解決・configure 順序は不変。
- `test_hooks.py`：registry 分類・固定エントリ・実行 inventory の path は不変。
- `b5_contrast_launch.py`／`test_b5_contrast_launch.py`：job body の path・argv 契約は不変。
- 外部から当 harness／evidence 辞書を利用する Python caller は検索範囲で見つかりませんでした。共有 fixture の変更はありません。
- job body の SHA は変わりますが、既存の実行時 SHA 記録処理は維持。過去の記録は編集していません。

6. **未実走・親の焦点走候補**

**実装済み・未実走**です。親が計算ノードで走らせる候補は、`orchestrator/tests/test_p3_s4_loop_job_contract.py::` を接頭辞とする次の nodeid です。

- `test_b5_actual_shell_one_driver_and_trap_rc`
- `test_b5_stock_off_preserves_single_b5_call`
- `test_default_job_invokes_driver_once`
- `test_pair_job_invokes_one_driver_with_both_modes`
- `test_b5_fallthrough_mutant_is_killed_by_shell_call_count`
- `test_complete_k2_environment_reaches_actual_job_driver_argv`

加えて同ファイル全体の meta-test、上記 consumer test、事前登録 M1〜M4 の変異確認を推奨します。

## 総括

所有 2 ファイルのみ実装しました。テスト、commit、docs 編集は行っていません。

shell 構文検査は、自動 PreToolUse hook が対象を Pegasus ログインノード上の dispatch-required 実行体として拒否したため未完了です。