実装済み・未実走です。段4裁定どおり、指定2ファイルだけを変更し、commit は作成していません。

変更内容:

- [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:87)
  - BASE `15.0` を維持。
  - RATE `0.0086`、独立 CAP `300.0` を追加。
  - LF 要求数と `MAX_BATCH_REQUESTS` から予算を計算する private helper を追加。
  - `git-input-limit` 検査後、単一 `subprocess.run` の `timeout` に算出値を渡すよう変更。
- [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:987)
  - 定数、LF framing、実要求数7,005、両 clamp、単一 subprocess、signature、timeout/failed reason を固定。
  - 既存 input-limit テストを、予算計算より先に拒否することまで強化。

受理・拒否挙動は、stdin なし／空では従来どおり15秒です。合法な LF-framed stdin だけ時間余裕が裁定どおり広がります。量的上限と既存 reason code の条件は変更していません。

### 検査

- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 変更ファイル: 指定された2ファイルのみ

次の範囲を `tools/run_tests.py` で実行しようとしましたが、すべてテスト開始前の rc=16 でした。

- `orchestrator/tests/test_s8c_preregistration_core.py` 全体
- 追加7テスト群＋既存 input-limit nodeid
- 同ファイルの `--collect-only`

原因は `qstat -Q` の `EACCTAUTH Unknown user-id (uid: 31609)` です。したがって、テストの緑や収集成功は主張しません。

### 所有外への波及可能性

- `_git` の所有外 caller: repository safety、commit 解決、`read_blob_at`、commit graph、history namespace、batch-check、batch blob、`prepare_revision`。signature は未変更です。
- 共有 fixture: `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain` は7,005要求で同じ production 式を通ります。180秒定数と xdist group は不接触です。
- consumer test: `test_s8c_preregistration_predicates.py`、`test_trial_registry.py`、`test_p3_autonomous_workload_trial.py`、acceptance receipt／completeness 系。
- production consumer: `p3_autonomous_workload_trial.py` と `trial_registry.py`。module bytes の変更により `core_module_blob_sha256` と activation digest、その下流の admission／lifecycle／receipt bytes は変わり得ます。

### 変異12件との対応

以下の nodeid prefix は `orchestrator/tests/test_s8c_preregistration_core.py::` です。

| # | 落ちる nodeid |
|---:|---|
| 1 | `test_git_timeout_budget_constants_match_preregistered_measurement` |
| 2 | `test_git_timeout_budget_constants_match_preregistered_measurement` |
| 3 | `test_git_timeout_budget_constants_match_preregistered_measurement` |
| 4 | `test_git_timeout_budget_never_exceeds_absolute_cap` |
| 5 | `test_git_timeout_budget_clamps_requests_before_rate_amplification` |
| 6 | `test_git_timeout_budget_from_request_count[real-invariant-r]` |
| 7 | `test_git_timeout_budget_from_request_count[no-trailing-lf]` |
| 8 | `test_git_uses_one_internal_budget_and_preserves_timeout_reason` |
| 9 | `test_git_uses_one_internal_budget_and_preserves_timeout_reason` |
| 10 | `test_git_budget_has_no_caller_override` |
| 11 | `test_git_timeout_generation_commit_and_blob_limits_fail_closed` |
| 12 | `test_git_input_limit_stops_before_subprocess` |

静的対応上、落ちない変異はありません。ただし変異実走は親側で必要です。

## 総括

実装済み・未実走。  
BASE=15.0、RATE=0.0086、独立CAP=300.0を投入した。  
LF要求数とMAX_BATCH_REQUESTSからprivate helperで予算を算出する。  
単一subprocessと全signatureを維持した。  
既存reason code・量的上限・発火順序を維持した。  
変異12件はすべて対応nodeidを持つ。  
静的検査3件はrc=0。  
pytestはPegasus認証エラーで開始前rc=16、緑は未主張。  
docs編集・commit・指定外ファイル変更はない。