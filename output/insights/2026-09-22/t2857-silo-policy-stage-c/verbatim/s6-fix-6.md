## 直した内容

- K1：prefix unlock 変異を action-abort 出口と上限出口の2枚に分離。各変異は他方の unlock を保持。
- K2：`prefix_held_limit_aborts`・`prefix_held_action_aborts` を計数・出力・parse に追加。
- `focus/abort0` を追加し、両変異の合格には同方策・同 workload の対応する prefix 保持下到達を要求。
- 結果 JSON に、到達証拠は別 probe 走であり変異走自身の証拠ではない旨を追加。
- 新 patch の token 許容集合と build sink の行番号 pin を追随。

## 確認の実測

成功：

- 骨格→更新 probe→各機構変異9枚の `git apply --check`／適用。
- 骨格→各負例3枚の同確認。
- probe・両 prefix 変異から抽出した計数部／`lockWriteSet` の単独 TU：BREAK=0/1、計6構成で `g++ -std=c++17 -Wall -Wextra -Werror -fsyntax-only` 成功。周辺型は stub。
- 変更した Python 4ファイルの `py_compile` 成功。

以下は実装済み・未実走。test node は `orchestrator/tests/test_silo_policy_coverage.py::` 配下：

- `test_prefix_exit_case_configuration`
- `test_prefix_unlock_patches_remove_only_the_target_exit`
- `test_strict_patch_stacks_and_one_site_mutations`
- `test_prefix_limit_requires_prefix_held_limit_reach`
- `test_prefix_conflict_requires_prefix_held_action_reach`
- `test_probe_parser_requires_prefix_held_exit_keys`

driver `orchestrator.campaign.silo_policy_coverage coverage` も実装済み・未実走。pytest・build は未実行。

## 変えていないことの根拠

最終 `git status` の差分は許可された7ファイルのみ。docs・他の機構変異 patch は未変更。index／履歴を書き込む git 操作なし。作業ディレクトリは削除済み。

既存 assert は変更していません。trace-timeout、certified、必須集合・赤集合の完全一致、既存到達条件も維持しました。

## 未了と疑問

`test_coverage_reuses_controls_and_separates_prefix_exits` の既存期待「23 build」「両出口で同じ patch」は、新構成の「24 build」「出口別 patch」と矛盾します。

期待値変更禁止に従い、この2点は未変更です。追随可否を確認しましたが回答未受領のため、この node は現状、新構成と不整合です。動的合格も未確認です。

## 総括

K1・K2 の実装修正と許可された静的確認は完了しました。ただし、既存テストの期待値2点の不整合が未了であり、全体完了・動的合格とは報告しません。