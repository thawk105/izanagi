## 変更の要約

`orchestrator/campaign/s8b_oracle_driver.py` の docstring 2 箇所だけを修正しました。

- core：error 優先 → token 欠落なら M → sha256 照合の順序、拒否理由の集約継続、loader 非呼出しを明記。
- public：冒頭を「standalone gate。v2 freeze は full launch validation を通らない限り受理しない。」へ変更。続く本文は維持。

`git diff --stat` と `git diff` を確認済み：**1 file changed, 7 insertions(+), 5 deletions(-)**。コード行の変更は **0**。両 docstring は各行 90 文字以内です。

## 所見の対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| RB-1 | closed | docstring を実装の error/token/hash の優先順位に整合 |
| RB-2 | closed | validation の必須実行という説明を、受理の必要条件へ訂正 |

## 実走結果

指定コマンド：**17 passed in 1.27s**、終了コード 0。
指定の `ast.parse`：成功、終了コード 0。
追加の AST 比較：対象 2 docstring を除き HEAD と一致。

nodeid の共通接頭辞は `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py::`。収集結果の全 17 node が PASS です。

```text
test_public_reread_v2_requires_launch_validated
test_public_reread_v2_ignores_injected_ratified
test_core_v2_without_launch_validated_is_refused[both]
test_core_v2_without_launch_validated_is_refused[floor-only]
test_core_v2_without_launch_validated_is_refused[budget-only]
test_core_exact_launch_validated_preserves_predicates[both]
test_core_exact_launch_validated_preserves_predicates[floor-only]
test_core_exact_launch_validated_preserves_predicates[budget-only]
test_core_rejects_launch_validated_subclass
test_public_ratified_load_errors_preserve_refusals[RatifiedFreezeError]
test_public_ratified_load_errors_preserve_refusals[RuntimeError]
test_public_explicit_ratified_error_keeps_early_return
test_public_two_failed_reads_preserve_refusals
test_core_launch_validated_missing_hash_remains_refused
test_public_reread_v1_never_gets_missing_token_refusal
test_cli_gate_check_transports_missing_token_refusal
test_gate_core_signature_has_no_ratified_injection_port
```

## 総括

RB-1・RB-2 は修正完了。受理集合、分岐、refusal 文字列、signature、テスト期待値は変更していません。docs 編集、git add・commit・stash・branch 操作は行っていません。