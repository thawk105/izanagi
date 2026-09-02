## 所見

### 1. receiptless WAL では不正な genome が protocol として発効する

- **主張:** `_campaign_protocol()` は floor 用の最小 parser を WAL にも使用しており、`mocc|garbage` のような非 canonical 値を `mocc` と判定する。receiptless `build_start` は既存の exact parser を通らない。
- **根拠:** 共有 helper は `|` 後方を検査しない [genome.py:127](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/genome.py:127)。Layer 3 はこれを直接使用する [layer3_report.py:334](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/layer3_report.py:334)。一方、exact parser は整数化と再 canonical 化まで行う [artifact_admission.py:744](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/artifact_admission.py:744) が、receiptless start は先に `continue` する [artifact_admission.py:1185](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/artifact_admission.py:1185)。追加テストも malformed body を含まない [test_layer3_report.py:2926](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_layer3_report.py:2926)。
- **成果物影響:** malformed な receiptless campaign が、要求された no-match ではなく mocc/silo floor を Layer 3 report に帰属できる。
- **判定:** must-fix
- **確信度:** 高

### 2. trace-hook admission がコメントだけでも真になる

- **主張:** 3 regex は独立に文字列を探すだけで、コメント、dead preprocessor branch、呼出しと guard の対応を検査しない。逆に include を共通 header に置く正当な移植は偽になる。
- **根拠:** include、guard、hook の regex 定義 [between_run_floor.py:124](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:124) と単純 conjunction [between_run_floor.py:137](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:137)。例えば active include と guard に `// izanagi_trace::emit_abort(...)` を添えるだけで真になる。これが唯一の build 前 gate である [between_run_floor.py:291](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:291)。テストは実 call の合成正例しか持たない [test_between_run_floor.py:217](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:217)。
- **成果物影響:** 実 hook のない protocol が admission を通り、根拠のない between-run floor JSON を生成できる。
- **判定:** must-fix
- **確信度:** 高

### 3. create-only 化が半端な公式出力を再実行不能にする

- **主張:** JSON を先に確定作成し、その後に Markdown を構築・作成するため、後半の例外で JSON だけが残る。次回は create-only precheck が再生成を拒否する。
- **根拠:** 既存検査 [between_run_floor.py:210](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:210)、JSON 作成 [between_run_floor.py:214](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:214)、Markdown 作成 [between_run_floor.py:240](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:240)。テストは「開始前から JSON がある」場合だけを検査する [test_between_run_floor.py:191](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:191)。
- **成果物影響:** producer が失敗終了しても consumer が読める JSON だけが残り、通常の再実行では修復できない。
- **判定:** must-fix
- **確信度:** 高

### 4. 裁定の15 file 外にも直接 consumer test がある

- **主張:** 焦点走15 file は最小閉包ではない。変更 module の直接 import、属性参照、schema/source 内容走査を持つ test が追加で存在する。
- **根拠:** 例として Layer 3 consumer [test_autonomous_trial_completeness.py:26](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_autonomous_trial_completeness.py:26)、s6/s8a consumer [test_bench_first_real_wal.py:23](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_bench_first_real_wal.py:23)、freeze consumer [test_s1_known_axes_freeze.py:547](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_s1_known_axes_freeze.py:547)、schema 内容走査 [test_s8b_oracle_driver.py:4976](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_s8b_oracle_driver.py:4976)。
- **成果物影響:** Layer 3 chain、freeze inventory、変更 schema の回帰が焦点走だけでは検出されない。
- **判定:** nit。最終全走が実施されれば補完される。
- **確信度:** 高

## 閉包の差分表

| 面 | 実装が追随させた集合 | 自分が見つけた集合 | 差分 |
|---|---|---|---|
| production 編集 | 裁定どおり8 file | 同じ8 file | なし |
| screening API caller | `backoff_sweep.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py` | 同じ3 caller | なし |
| production reverse import | 報告では `SILO_SPACE` consumer 等を総称 | 上記に加え `backoff_extended_sweep.py`、`backoff_repro.py`、`backoff_sweep_report.py`、`backoff_overthrottle.py`、`backoff_requested_us.py`、`autonomous_trial_completeness.py`、`p3_autonomous_workload_trial.py`、`s1_known_axes_freeze.py`、`s1_verify_extime_calibration.py`、`sort_comparator_authority.py`、`tools/check_trace0_preprocess_identity.py` | 今回変更した symbol を使わないものが多く、production 追随漏れとは判定しない。ただし test closure には入る |
| test 変更 | 8 file | 同じ8 file | なし |
| 焦点走 | 裁定の15 file | 15 fileに加え `test_autonomous_trial_completeness.py`、`test_backoff_requested_us.py`、`test_bench_first_real_wal.py`、`test_check_trace0_preprocess_identity.py`、`test_coder_effect_gate.py`、`test_layer3_admission_diagnosis.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_build_authority_cli.py`、`test_reflux_ir.py`、`test_s1_known_axes_freeze.py`、`test_s8b_oracle_driver.py`、`test_sort_comparator_authority.py`、`test_t126_pegasus_tools.py`、`test_t126_qualification_artifacts.py`、`test_trial_registry.py` | 追加15 file |
| 動的・内容参照 | `test_s8b_floor_campaign.py`、`test_official_perf_closure.py`、`test_ccbench_spawn_sites.py`、`test_pegasus_floor_scoping.py` | 同集合に `s1_expected_goldens.py`、`t080_freeze_migration.py`、`test_s1_known_axes_freeze.py`、`test_s8b_oracle_driver.py`、`test_t126_pegasus_tools.py` | freeze/schema/path inventory が追加 |
| 新規 test file の meta-test | 新規 file なし | 新規 file なし | なし |

## 報告と実装の突き合わせ

確かめられたもの:

- production 8 file、test 8 file、計16 file だけが変更されている。
- M1〜M4 に対応する test 関数は実在する。代表は [test_screening_driver.py:231](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_screening_driver.py:231)、[test_layer3_report.py:2838](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_layer3_report.py:2838)、[test_between_run_floor.py:236](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:236)、[test_campaign.py:227](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_campaign.py:227)。
- 実在4 floor は変更後 `load_between_run_floor()` で読めた。`git diff --quiet -- output` も rc=0。
- 実在 Layer 3 report 7件中、対応対象の v2 6件は変更後 schema 検証を通過した。v1 1件は従前どおり非対応で、今回の回帰ではない。
- silo stem、mocc stem、3 caller の protocol 転送、4-field Layer 3 match、legacy 根拠 field はコードに存在する。
- test の skip、xfail、削除、期待値反転はない。Layer 3 fixture 変更も既存 assertion の緩和ではない。
- scope 外の `registered/`、within-run producer、tictoc/cicada、certified mocc 経路に差分はない。

確かめられなかったもの:

- [author.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/author.md:15) の「20 selector + 3 selector」を実際に runner へ渡した履歴。selector 一覧や runner receipt が射影資料にない。
- `rc=16 / child_started=false`、dispatch directory 3件の削除、`check_codex_agents.py` と `check_docs.py` を当時実行した事実。現在のファイル状態だけでは履歴を証明できない。
- [author.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/author.md:17) の「15 file はすべて実装済み」は表現が広い。15 file は存在するが、実際に変更された test は8 fileである。
- pytest、mutation、焦点走は報告どおり未実走。今回も実走していない。

## 実装のどこが正しいか

- mocc は `BACK_OFF`、`TEMPERATURE_RESET_OPT`、`KEY_SORT` の3ブール、8 genome で、RWLOCK、delay、YCSB限定性の注記も裁定どおり。
- silo baseline は従来の canonical 値を維持し、mocc baseline は CMake の stock defaults と一致する。
- silo の出力 stem は不変で、mocc だけ `_mocc` が挿入される。
- 現行 source では silo admission が真、mocc が偽になり、拒否位置も build前にある。
- screening の3 production caller は実 baseline genome の protocol を渡している。
- Layer 3 は WALから protocol を取り、floorを `(protocol, records, threads, workload)` で照合する。legacy genome無し within-run は siloだけに限定し、根拠も出力する。
- 既存4 floor、既存v2 report 6件の可読性と tracked bytes は維持されている。
- 禁止範囲の実装、既存 test の緩和、新規 test file は見つからなかった。

## 総括

must-fix は3件。最重要は、コメントだけでも通る trace-hook admission 述語である。  
receiptless WAL の非 canonical genome が protocol として発効する穴も閉じる必要がある。  
create-only writer は JSON/Markdown の半端 publish を防ぐ必要がある。  
pytest、mutation、焦点走は未実走で、親による実測が必要。