**実装済み・未実走です。** 所有8ファイルだけを変更しました。commit・テスト・job投入は行っていません。所有外の `test_hooks.py` に、登録簿の `reason` 更新に伴う既知の不一致が1件あります。

### 1. 着手前の現行挙動

**(a) driver**

`_header(arm, workload, series, block, repo_root)` は cohort=`t2797-beta-v1`、purpose=`pilot` を固定し、limits は次の2文でした。

- `Parent intervention and actual input delivery are not mechanically guaranteed.`
- `Pilot only; does not establish preregistration section 10 completeness.`

`run_series` は位置引数 `arm, workload, series, block`、keyword-only の `ledger_root, prebuild_receipt, repo_root, k2=None, runner=default_runner` を受けました。`run_block_stock` は `workload, block` と同様の keyword-only 引数（k2なし）です。

`main(argv=None)` の実行コマンドは `run-series`／`run-block-stock`。共通引数は workload・block・ledger-root・receipt、series 側には arm・series・K2引数があり、purpose はありませんでした。`weights-material`／`expected-inputs` も既存入口です。

**(b) job body**

B-5必須配列は ARM・WORKLOAD・SERIES・BLOCK・LEDGER_ROOT。mode の値、armとの組合せ、座標、絶対ledger path、既存モードとの排他を検証し、modeなしのB-5 envを拒否していました。driver argv は実行コマンド、series側のarm・series、共通引数、LLMだけのK2引数から構築していました。

**(c) launcher**

`_validate_job` は write-heavy・series 1・block 1 と4 armの形、LLMだけのK2を要求。`validate_pilot_cap` は予算定数、4 jobの順序、出力分離、53 session／上限60を検証していました。

`build_job_environment` はthirdparty・repo外出力を検査し、LLMだけに4 K2 envを追加。`_qsub_argv` は探索 `08:00:00`、stock `03:00:00`。`launch` は全job構築→全freshness検査→dry-runまたはmkdir・投入の順で、途中失敗時は即時終了でした。

**(d) report**

registered headerにはpurpose一致、非空cohort、必要キー・型・既存予算、`legacy+performance`・3 rounds、探索の `block=(series-1)//4+1`、stockの `series=block` を要求します。`build_report` はcohort一意性や構成・identity整合も検査します。実行順・block間隔の認可は検査しません。

### 2. 変更ファイルと箇所

| ファイル | 主な変更 |
|---|---|
| [b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/campaign/b5_generator_contrast.py:554) | 定数追加（45行）、`_header`、`run_series`（721行）、`run_block_stock`（844行）、`main`にpurposeを接続。pilot limits保持。block拒否追加なし |
| [b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/tools/pegasus/b5_contrast_launch.py:262) | schedule、Decimal walltime、registered job/env、全件事前検査、dry-run／submit、CLI追加 |
| [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/tools/pegasus/p3_s4_loop_pegasus.sh:67) | 任意purpose検証、modeなし拒否、registeredのみargv追加（664行） |
| [admission_registry.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/tools/pegasus/admission_registry.json:36) | launcherのreasonだけ更新 |
| [test_b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/tests/test_b5_contrast_launch.py:307) | schedule・walltime・実Git tree・env／argv・CLI・投入失敗テスト |
| [test_b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/tests/test_b5_generator_contrast.py:1100) | 実report接続、pilot bytes、stock purpose、実CLI接続 |
| [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/tests/test_p3_s4_loop_job_contract.py:2198) | 既存shell fixtureによるpurpose検証・伝播・pilot互換 |
| [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:2853) | launcherのGit／pilot qsub／registered qsub専用目録追加 |

scheduleは36順序行で108 arm系列を記述し、stockを含む117 jobを返します。

### 3. 静的検査

| 実行内容 | 結果 |
|---|---|
| `python3 -B -`：変更Python 6ファイルを`compile`／`ast.parse`で構文確認 | rc=0。コード・テスト本体は未実行、pyc生成なし |
| `bash -n < tools/pegasus/p3_s4_loop_pegasus.sh` | rc=0 |
| `git diff --check` | rc=0 |
| `python3 -B -`：HEADと現行ソースの定義・JSONフィールド・shell末尾を比較 | rc=0 |
| `git status --short` | rc=0。変更は所有8ファイルのみ |

編集用Pythonコマンドとファイル引数形式の`bash -n`は、hookがjob body実行として拒否しました（プロセス未起動、rcなし）。編集は`apply_patch`、shell構文確認は標準入力方式で完了しました。

### 4. meta-testへの影響

- **process目録**：既存走査はcampaign／calibrator配下だけです。launcherの追加起動箇所には専用のexact目録を追加しました。
- **job env／argv契約**：既存B-5・非B-5テストの期待値は無変更。既存shell fixtureで新purposeケースを追加しました。
- **registry／runbook投影**：class・primary_gate・evidenceは不変。投影表への変更は不要です。
- **hook golden**：`test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes` はreasonを含む完全一致のため、**現差分では不一致になると静的に確認**しました。所有外なので未編集です。
- **plain runner**：4テストファイルの既存 `_run()`／`__main__` は維持しました。
- **login資源・起動規約**：`test_hooks.py`／`test_codex_hooks.py` の分類、`test_login_headroom.py` の資源判定面を確認。分類・headroom経路は変更せず、launcherはGit照会とqsubだけです。
- **campaign import契約**：driverのbootstrap・相対import構造は維持しています。

### 5. 変異と検出予定node

以下は**未実走の検出予定**です。D＝`test_b5_generator_contrast.py`、L＝`test_b5_contrast_launch.py`、J＝`test_p3_s4_loop_job_contract.py`。

| 変異 | node | 変更箇所を通る根拠 |
|---|---|---|
| MA1 | D::`test_registered_header_consumed_by_existing_report` | 実producerの保存ledgerを実`build_report`へ渡し、invalid・registered分岐・pilot不一致を確認 |
| MA2 | D::`test_purpose_cohort_mapping` | 実`_header`のcohortをliteral比較 |
| MA3 | D::`test_pilot_header_bytes_unchanged` | HEAD・host・env・deadlineを固定し旧header期待bytesと比較 |
| MA4 | D::`test_registered_block_stock_header` | 実`run_block_stock`からheaderとreportを確認 |
| MA5 | L::`test_registered_schedule_coordinates` | 実scheduleの系列→blockをliteral表と比較 |
| MA6 | L::`test_registered_schedule_llm_four_per_stage` | stage別LLM数と6順序×2を独立集計 |
| MA7 | L::`test_registered_schedule_six_orders_twice` | 6順序×2とblock内の先後2対ずつを集計 |
| MA8 | L::`test_registered_stage_job_counts` | stage別12／15／12とstockのstage 2を確認 |
| MA9 | L::`test_registered_job_specific_submit_trees` | 実Git treeをjob ID別に割当て、全cwdを照合 |
| MA10・MA11 | L::`test_registered_walltime_decimal_boundaries` | 実walltime関数を2.5等で呼び、ceil・stock係数をliteral照合 |
| MA12 | L::`test_registered_environment_exact` | 実stage構築後の全env・argvを完全一致比較 |
| MA13 | L::`test_registered_dry_run_has_no_side_effects` | 実tree検査を通し、mkdir／qsubを禁止して確認 |
| MA14 | L::`test_four_qsub_argv_and_explicit_environment_are_exact` | 既存pilot完全一致テストをそのまま維持 |
| MA15 | J::`test_b5_purpose_invalid_before_prebuild` | 実shellで空・未知purposeの早期拒否理由を確認 |
| MA16 | J::`test_b5_registered_purpose_reaches_driver` | 実shell→driver境界の末尾argvを確認 |

MA6はblock回転を外してもLLM4本だけなら成立するため、同nodeで順序出現数も検査します。M0はコメントのみの等価変異としてSURVIVED期待です。

### 6. 所有外への波及

- `test_hooks.py:3275` のlauncher reason literal更新が親側の残件です。検出nodeは上記4106行のテストです。
- report・report consumerテスト、子`p3_s4_loop.py`、pipelineは無変更。headerのキー追加・削除もありません。
- 既存`submit_tree`／`FakeRunner`／shell fixtureを含め、既存テスト・共有fixture定義は変更なしと静的比較しました。
- launcher既存関数は`main`の振分け以外変更なし。非B-5末尾driver分岐もbytes一致を確認しました。
- docs・output・事前登録・role定義は無変更です。

### 7. 親の実走候補

計算ノードの所定経路で、まず変更した3機能テストファイル全体と、上表のMA nodeを実行してください。追加候補は次です。

- `test_ccbench_spawn_sites.py::test_b5_submitter_process_launch_inventory_is_exact`
- `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `test_plain_runner_coverage.py`
- `test_check_docs.py` のadmission投影関連node
- `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`（親によるreason golden更新後）

## 総括

実装単位Aと指定変異の検出用テストを追加し、静的検査を完了しました。**実装済み・未実走であり、green／KILLEDは未確認です。** 親への残件は、所有外hook goldenのreason更新と焦点走・変異走・受入です。