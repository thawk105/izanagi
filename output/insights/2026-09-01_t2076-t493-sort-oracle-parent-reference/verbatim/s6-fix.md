## 総括

- must-fix のテスト変更を実装しました。
- 既存 node の期待メッセージと例外型は変更していません。
- authority 層の新しい回帰 node を追加しました。
- pytest は基盤エラーで起動できていないため、状態は「実装済み・未実走」です。`closed` は申告しません。

## 変更した file

- [orchestrator/tests/test_s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_s1_known_axes_freeze.py:673)
  - `test_verify_rejects_one_byte_freeze_tamper` の改竄対象を変更。
  - `test_verify_rejects_sort_name_tamper_at_authority_layer` を追加。
  - production code、docs、凍結 JSON は未変更です。

## 選んだ改竄 byte とその根拠

top-level `what` 値の `"S-1"` を `"X-1"` にする、`S`→`X` の1 byte置換を選びました。

`what` の値は schema のキー集合確認だけでは検査されず、sort authority、trigger 束縛、source path/SHA、generator SHA のいずれにも使われません。そのため後段の機械再構成比較まで到達し、従来どおり完全一致メッセージを検査できます。

新規 node は凍結 JSON の `"sp_dd"`→`"xp_dd"` を直接再現し、`build_document()` を使わず `_validate_schema` の authority エラーを固定します。

## 実走した検査

- `git diff --check -- orchestrator/tests/test_s1_known_axes_freeze.py`: PASS
- 次の2 nodeを共通 runnerで指定しましたが、`qstat -Q` preflight が失敗し `rc=16`、`child_started=false` でした。pytest自体は未実走です。
  - `test_verify_rejects_sort_name_tamper_at_authority_layer`
  - `test_verify_rejects_one_byte_freeze_tamper`

## 未解決・親の裁定が要る点

追加裁定が要る点はありません。親環境で上記2 node、特に submodule が見える状態で既存 one-byte nodeの実走確認が必要です。