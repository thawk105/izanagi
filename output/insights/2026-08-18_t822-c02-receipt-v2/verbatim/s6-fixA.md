## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F5 | partial（実装済み・未実走） | 未使用 namespace f-string と `if True: return` 後方の call を静的に拒否。alias 追跡は追加せず scope を維持 |
| F6 | partial（実装済み・未実走） | 全 chain token を `checked=40` / `excluded=33` / `missing=0` に分類して exact pin。除外 pin 欠落と未知 token を静的に拒否 |
| 回帰 | regressed なし（静的確認） | 受理集合を広げる経路、期待値の緩和・反転・skip・削除なし |

## 変更点

- [s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py)
  - f-string の直接 return、または最終代入名の return のみを namespace 証拠として採用。
  - `if <literal true>: return` 後の statement を `_live_nodes` から除外。
- [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_preregistration_predicates.py)
  - 未使用 f-string と literal-true return 後方 call の負例を追加。
- [test_s8c_preregistration_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_preregistration_invariant.py)
  - entrypoint と全 `reachable_from` hop を分類。
  - 非 identifier、別 module、契約上の未実装 token を理由付きで exact pin。
  - 除外 pin を空にすると赤になる負例を追加。

## 実走

以下の5 nodeidを `tools/run_tests.py` で投入しましたが、`qstat -Q preflight rc=1` により dispatch infrastructure failure（runner `rc=16`）となり、pytest は開始されませんでした。

- `test_c02_namespace_fstring_must_flow_to_return_value`
- `test_c02_call_after_literal_true_return_is_dead`
- `test_machine_contract_function_names_exist_and_checked_set_is_exact`
- `test_machine_contract_exclusion_pin_cannot_be_omitted`
- `test_machine_contract_rejects_prewave_accept_trial_name`

静的確認は成功しています。

- 3所有ファイルの AST parse
- namespace flow: direct/assigned は許可、unused/overwritten は拒否
- literal-true return 後の live call 集合が空
- メタ分類 `40 checked / 33 excluded / 0 missing`
- 空の exclusion pin と未登録 token を fail-closed で拒否
- `git diff --check`

## 未解決

- 正規 runner での pytest 実走が必要です。
- `_live_nodes` は他条件評価器でも共有されるため、親の統合走で C01/C04/C09/C12 周辺も確認対象です。
- 既知の赤3件には触れていません。
- docs、所有外ファイル、receipt側テストは編集しておらず、commitも作成していません。

## 総括

F5/F6 は裁定された限定形で実装し、要求された攻撃形を静的には拒否できています。pytest未実走のため、状態は両方とも `partial（実装済み・未実走）` です。