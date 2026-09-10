## 直した内容 (file:line)

- [test_codex_reasoning_ab.py:1103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:1103): skip 正例を新設。
- [test_codex_reasoning_ab.py:1134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:1134): 重複負例を `_resolve_required_historical_rollouts` の直接呼び出しへ変更。
- [test_codex_reasoning_ab.py:1156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:1156): SHA 不一致負例も同様に変更。

## 変異 B2 / B3 で赤になる node と assertion

- B2: `test_historical_rollout_preflight_duplicate_is_red` が `pytest.raises(TOOL.ValidationError, match="...rollout count is 2, expected 1")` で `DID NOT RAISE` となる。
- B3: `test_historical_rollout_preflight_sha_mismatch_is_red` が `pytest.raises(TOOL.ValidationError, match="POS rollout sha mismatch")` で `DID NOT RAISE` となる。

## 新設した skip 正例

`test_require_historical_rollouts_skips_with_expired_label_reason` を追加しました。不在入力で `_require_historical_rollouts` が `pytest.skip.Exception` を上げ、理由に失効 label が含まれることを検査します。

## 実走結果 (nodeid と範囲、赤の内訳)

実装済み・未実走です。次の関連 4 node を runner に指定しましたが、Pegasus の queue preflight が infrastructure failure、rc=16 となり、pytest child は起動されませんでした。

- `test_historical_rollout_preflight_skips_missing_label`
- `test_require_historical_rollouts_skips_with_expired_label_reason`
- `test_historical_rollout_preflight_duplicate_is_red`
- `test_historical_rollout_preflight_sha_mismatch_is_red`

テスト由来の赤は 0 件です。未起動のため合格とも扱いません。

## 未実走・未確認

- pytest の 4 node は未実走。
- AST parse と `git diff --check` は成功。
- runner が自動生成した dispatch artifacts は除去済みです。`git status --short` は対象ファイル 1 件だけを示しています。

## 総括

BF-01 のみ修正しました。既存の例外型、`match`、rc assertion、期待値は変更していません。golden の SHA256、`ROLLOUT_SHA256`、`SESSION_IDS`、`TASK_MANIFEST` の pin 値も変更していません。