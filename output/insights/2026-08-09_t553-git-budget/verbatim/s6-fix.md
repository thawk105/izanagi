F1〜F4 を実装しました。編集・未 commit は指定の2ファイルだけです。A所見5、B M-02/M-03、invariant test には触れていません。

## 修正内容

- F1: [test_s8c_preregistration_core.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1003)
  - `real-invariant-r` を中立な `legal-linear-example` に改名。
  - [同ファイル:1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1025) に実repo検査を追加。
  - `git rev-list --count HEAD` 1回と、production の source/evidence/generation paths から `R` を動的導出。
  - 現在値は `(2347 + 1) × 3 = 7044`。golden literal は置かず、予算式との一致と `> 15.0` を検査。

- F2: [同ファイル:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1070)
  - stdin を `MAX_BATCH_REQUESTS × 2` 行へ強化。
  - budget伝播、成功時1 call、`TimeoutExpired → git-timeout`、timeout時1 callを維持。

- F3: [同ファイル:1112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1112)
  - `_git_text` をsignature検査へ追加。
  - parameter名を `timeout` / `budget` / `deadline` の部分一致で検査。
  - `_build_parser()` の全subparserを辿り、全option文字列にも同じ部分一致検査を追加。

- F4: [s8c_preregistration.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:95)
  - RATEの実測値、25.6倍、安全係数4、確定値0.0086を記載。
  - CAPのRATE非依存性、受入全走・30分walltimeとの比率、生実測path、再較正条件を記載。
  - 定数値は変更なし。

## 検査結果

pytest は実装済み・未実走です。

`python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_core.py -q` を起動しましたが、`qstat -Q preflight rc=1` のdispatch infrastructure failureで停止しました。pytest nodeidは1件も実行されておらず、緑は主張しません。

通過した静的検査:

- 両ファイルのAST parse
- `git diff --check`
- `python3 -B tools/check_codex_agents.py`
- `python3 -B tools/check_docs.py`

## 修正後の変異対応表

以下は未実走の静的適用結果です。

| # | killするnodeid | 静的確認 |
|---:|---|---|
| 1 | `test_git_timeout_budget_constants_match_preregistered_measurement` | RATE 1/10をliteral pinが検出 |
| 2 | 同上 | BASE < 15.0を検出 |
| 3 | 同上 | 従属CAP=445.0を検出 |
| 4 | `test_git_timeout_budget_never_exceeds_absolute_cap` | CAPの`min`削除で445.0となる |
| 5 | `test_git_timeout_budget_clamps_requests_before_rate_amplification` | CAP=1000隔離下でrequest clamp削除を検出。構造sensitivity pin |
| 6 | `test_git_timeout_budget_from_request_count[not-byte-length]` | `len(stdin)`算出を検出 |
| 7 | `test_git_timeout_budget_from_request_count[no-trailing-lf]` | 末尾fragment数え落としを検出 |
| 8 | `test_git_uses_one_internal_budget_and_preserves_timeout_reason` | 固定15秒では123.25秒伝播assertが赤 |
| 9 | 同上 | 100,000行を50,000行単位に分割すると成功側が2 callsとなり赤。今度はkill |
| 10 | `test_git_budget_has_no_caller_override` | `_git_text`、部分一致parameter、再帰列挙CLI optionのoverrideを検出。今度はkill |
| 11 | `test_git_timeout_generation_commit_and_blob_limits_fail_closed` | `TimeoutExpired`変換削除を検出 |
| 12 | `test_git_input_limit_stops_before_subprocess` | input-limit後方移動でbudget helperが先に発火 |

## 所有外への波及可能性

- caller: `activation_report_at` / `effective_at` / `prepare_revision`、CLI `check` / `prepare-revision`。signatureは不変。
- consumer: `p3_autonomous_workload_trial.py`、`trial_registry.py`、evidence evaluator。時間gate以外の契約変更なし。
- shared test: `test_s8c_preregistration_invariant.py` のcandidate fixtureとxdist groupは不接触。
- consumer tests: invariant、predicates、trial registry、autonomous workload trialは親の全走対象。
- moduleコメントでbytesが変わるため、`core_module_blob_sha256` は新commitに追随する。literal外部pinは静的検索上なし。
- CR path alias、byte-heavy測定、無stdin tailの所見はscope外のまま。

## 総括

F1〜F4を指定2ファイルだけで修正。  
定数値・production受理集合・reason code・呼出回数は変更なし。  
変異9はMAXの2倍入力で複数callを検出する。  
変異10は`_git_text`、部分一致名、全CLI optionを検査する。  
実repo予算はliteralなしでHEADとproduction pathsから追随する。  
静的検査は通過。  
pytestはdispatch障害のため未実走。  
docs編集・commit・禁止ファイル接触なし。