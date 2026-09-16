## 実装した内容 (file:line)

- [autonomous_trial_completeness.py:5036](orchestrator/campaign/autonomous_trial_completeness.py#L5036)：厳密な failure-only 述語、束縛検査、非 certifying receipt を追加。
- 同ファイル `:5134`／`:5223`：`failure_only_diagnostic=True` と `--failure-only-diagnostic` を追加。root 指定時は従来検証を実行。
- [test_autonomous_trial_completeness.py:5698](orchestrator/tests/test_autonomous_trial_completeness.py#L5698)：実 producer を使う正例・負例を追加。

既存テスト本文、既存 2 免除、cross-binding／Layer-3 chain 本体は無変更です。

## 現行挙動 (scope 前)

着手時ソースで確認した範囲：

- identity 付き failure は root 無しで拒否。root があっても directory／build population 要件で拒否され得る。
- fatal-empty／厳密 campaignless fallback は既存免除。
- admitted cell は root 必須。

変更前の実走はしていません。変更後の既定経路は既存テスト全件で確認しました。

## (D) 束縛導出の根拠

producer `p3_autonomous_workload_trial.py`：

- `:2754`：invoke ごとの query count 加算。journal 件数と report accounting を照合し、0 件も検査。
- `:2761`／`:4177`：provider artifact 宣言には arm digest が必要。exploratory の digest は `None` なので、矛盾する宣言を拒否。
- `:2808`〜`:2867`：valid invocation は raw 書込み完了後に記録されるため、raw 参照と実 bytes を必須検査。
- `:2845`〜`:2858`：invalid invocation の追加 error artifact は取得可能性次第。不在を report から証明できないため、**invalid／skipped role を対象外に限定**。
- `:4323`／`:4394`〜`:4410`：proposal 保存は preview 後。未宣言の場合も、早期停止を report の状態と照合。

既存 Layer-3 chain を直接呼びます。`campaigns/<ID>` 配下という包含保証は申告していません。

## (G) の選択

**diagnosis 付き 2 形を許可集合から削除しました。** 実 finalizer 由来の正例を本段では確立していません。厳密 diagnosis を持つ入力も新述語で拒否する負例を追加しました。

## 実走結果

指定自走 harness を使用：

- `orchestrator/tests/test_autonomous_trial_completeness.py::*`：**282 passed、529.58 秒**。既存 259＋新規 23 nodeid。[全 nodeid 一覧](/tmp/t1232-collected.txt)
- producer 側の以下 5 nodeid：**5 passed、6.12 秒**。
  - `test_cli_default_is_literal_one_by_ast`
  - `test_finish_trial_status_follows_both_critic_phases_by_ast`
  - `test_role_payload_validators_are_immediately_before_provider_invoke_by_ast`
  - `test_run_trial_routes_exactly_five_terminal_sites_through_formal_helper`
  - `test_transport_admission_error_persists_verified_partial_report`

最終の赤はありません。既存本文の不変、台帳 coverage、`git diff --check` も成功しました。

変異試験と投影外 meta-test は未実走です。M4 の件数検査は既存 accounting 検査とも重複するため、helper 削除だけを単独防護の kill と数えられません。

## 波及の静的列挙

- producer `:3956`／`:3974` は個別検査を直接呼び、今回の API 分岐を通りません。
- producer test `:3096` の既定 API caller は実走成功。
- 共有 `ratified_enforcement_source` fixture は無変更。
- brief が挙げる HEAD 読取りテスト、registry consumer、凍結 pin は投影外で再読・実走していません。全リポジトリの網羅確認とは扱いません。
- admitted／mixed 負例の nodeid は `test_failure_only_diagnostic_rejects_admitted_or_mixed_cells[admitted|mixed]` です。

## 台帳

**23 件**を暫定 `0.0` で追加。実測値ではなく、親による上書き用です。既存値は不変、`nodeid_count` は **23141**。

## 総括

所有 3 path の実装・検証を完了しました。commit・docs 編集はしていません。新経路は明示 opt-in の非 certifying 診断検証であり、invalid-role・diagnosis 付き形、正式系列の回復は対象外です。