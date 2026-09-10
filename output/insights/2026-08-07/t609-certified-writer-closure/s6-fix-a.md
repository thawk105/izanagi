## 所見対応表

pytest 未実走のため、実装済みでも `closed` とは申告せず全件 `partial` とします。

| 所見 | 状態 | 対応 |
|---|---|---|
| R2 | partial | runtime の `env_tag` / `clocks_per_us` を exact 型検査。equality spoof と `1800.0` の負例を追加 |
| R3 | partial | selector を比較前に exact `ExecutionEnvironmentContract` 検査。custom-equality subclass 負例を追加 |
| R4 | partial | screening prepare に認可と runtime 値を必須化し、layout/WAL より前に集中述語を実行。production 3 caller を配線 |
| R5 | partial | `admit()` 直前に、repo 配下の import 済み全 module bytes を `source_commit` blob と照合。不一致・blob 不在を拒否。fail-open drift 負例を追加 |
| R6 | partial | M2 fixture を runtime 同値のまま `isolation_policy` だけ異なる exact dataclass へ再照準 |
| R7 CLI | partial | floor/T126 の実 receipt・protocol・ledger・qsub fixture を作り、実 `admit()` と CLI 正例を追加 |
| R8 | partial | `numactl` の `None` 分岐と shape 検査を単一 gate に統合 |
| R10 | partial | T126 walltime を `source_commit` 由来 reservation policy から取得。floor/T126 walltime が異なる正例 fixture を追加 |
| R11 | partial | 2件の `Signature.bind()` 入力へ `authorization_contract=object()` を追加 |
| regressed | なし | 静的監査上なし。実走未了のため動的回帰は未判定 |

## 変更ファイル

- [execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/campaign/execution_guard.py): R2/R3/R8
- [screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/campaign/screening_driver.py): R4 の早期認可
- [backoff_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/campaign/backoff_sweep.py)、[s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/campaign/s6_sort_sweep.py)、[s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/campaign/s8a_trigger_sweep.py): screening 認可配線
- [certified_writer_preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/campaign/certified_writer_preflight.py): R5 の import closure 検査
- [certified_writer_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/campaign/certified_writer_admission.py): R10 の mode 別 walltime
- [certified_writer_fixtures.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/tests/certified_writer_fixtures.py): R5/R7/R10 共用 fixture
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/tests/test_campaign.py): R2/R3/R5/R6/R7/R10
- [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/tests/test_screening_driver.py): R4
- [test_trigger_gate_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-a/orchestrator/tests/test_trigger_gate_binding.py): R11

既存 assert、`pytest.raises`、skip/xfail は変更・削除していません。R6/R11などは入力のみ変更しました。docs、shell、B' 所有テスト、R1/R9には触れていません。commit/add/push も未実施です。

## 検査結果

焦点テストを次の nodeid で `python3 tools/run_tests.py ... -q` に投入しました。

- `test_runtime_authorization_rejects_equality_spoof_and_float_clock`
- `test_build_selector_rejects_custom_equality_subclass`
- `test_m2_pipeline_rejects_forged_contract_even_when_runtime_matches_it`
- `test_p2_actual_floor_and_t126_admission_accept_valid_evidence`
- `test_m8_preflight_rejects_fail_open_domain_module_drift`
- preflight CLI 既存3 node
- screening の新規早期拒否・既存正例
- trigger signature binding

結果は `qstat -Q preflight rc=1` による dispatch infrastructure failure、runner `rc=16` で、**全 nodeid 未実走**です。collect-only も同じ理由で未実走でした。緑とは報告しません。submodule marker 欠落も表示されましたが、targeted run は続行予定であり、停止原因は dispatch 失敗です。

静的検査結果:

- 変更・未追跡 Python 11ファイル: AST parse 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- `python3 -m orchestrator.campaign.queue_state`: キュー状態は観測不能
- 新設したのは `test_*.py` ではなく共用 fixture module のため、新規テストファイル用 meta-test は非該当

## 所有外への波及可能性

- `tools/pegasus/floor_campaign.sh` と `t126_qualification.sh` は新しい module closure gate を消費し、source commit と異なる import bytes を最初の書込み前に拒否します。
- B' 所有の `test_pegasus_floor_tools.py` / `test_t126_pegasus_tools.py` は未変更です。wrapper 正例には新しい共用 fixture の結線が必要です。
- T126 の submitter、qualification driver、collector、identity verifier は reservation policy の既存 consumerです。今回、preflight だけがその commit blob の walltime を新たに参照します。
- `REQUIRED_CODE_IDENTITY_PATHS`、凍結 manifest、wrapper identity key 集合は変更していません。
- screening の全 production caller 3箇所は配線済みです。

## 受理・拒否挙動

- 新規拒否: 非 exact runtime 型、非 exact selector 型、未認可 screening prepare、source commit と異なる import module、対応 blob 不在。
- R5 は bytes 不一致・blob不在を exit 3、Git/read 環境不備を exit 4へ倒します。
- T126 は共有 policy の project/queue/nodesを維持し、walltimeだけを commit 由来のT126固有 policyへ切り替えました。floor は従来どおり共有 floor walltimeです。
- `numactl` は gateを統合しただけで、受理集合は変えていません。
- R6/R7/R11はテスト・入力のみで、production の受理集合を変えません。
- 静的監査上、裁定表にない方向の受理集合変更はありません。

## 直せなかった項目

A' 担当の未実装項目はありません。ただしテスト実走不能のため、全所見の動的 closure と回帰なしは未確認です。R1、R9、R7 wrapper 正例はB'担当として未変更です。

## 総括

A' 担当9項目は実装・テスト追加まで完了しました。R5では import 済み repo module 全件を receipt の `source_commit` blobへ束縛しています。環境制約で焦点テストは `rc=16` の未実走なので、最終判定は全件 `partial（実装済み・未実走）` です。