実装済み・未実走です。

新設したテストは [`test_validate_generations_delegates_once_with_same_mapping()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-contract-generation/orchestrator/tests/test_env_contract.py:427) です。既存の public 負例テストは残しています。

- 有効な一世代 mapping を渡し、private helper を spy に monkeypatch。
- spy の呼び出し回数が1回であることを `len(calls) == 1` で検査。
- 引数が元の mapping と同一オブジェクトであることを `calls[0] is mapping` で検査。
- M10で委譲行をno-opにするとspyが呼ばれず、回数assertだけを理由に赤になります。
- private helper内部の連番検査などはspyで完全に置換されるため、それらの削除・緩和変異ではこのテストは赤になりません。
- `monkeypatch` fixtureが終了時に属性を自動復元するため、他テストへ漏れません。

所有外への静的な波及可能性は、pytest collection nodeが1件増えること、ファイル単位runnerの対象件数が増えること、外部のmutation台帳・node一覧が新テスト名への更新対象になりうることです。repo内に同名の固定参照はありません。productionコード、API、受理集合、golden hashには変更ありません。

`py_compile` と `git diff --check` は成功しました。pytestは実走しておらず、緑とは主張しません。docs編集・commitも行っていません。

## 総括

- 委譲専用spyテストを1件追加。
- 同一mappingでの1回呼び出しを直接固定。
- M10ではspy未呼び出しだけを理由に赤になる。
- private helper内部の検査変異はspyにより遮断。
- 既存public負例は維持。
- production・docs・既存期待値は未変更。
- 実装済み・未実走。