実装は完了しましたが、Pegasus の dispatch 障害により pytest は未実走です。段 6 契約に従い、全所見を `partial` とします。

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | `partial` | exact `str` 化と `__format__` CR 注入テストを実装。未実走 |
| F2 | `partial` | 単独埋め込み CR の policy 拒否テストを追加。未実走 |
| F3 | `partial` | `git ls-tree -rz` による path/blob 実在確認を追加。未実走 |

### 変更ハンク

- [s8c_preregistration.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/campaign/s8c_preregistration.py:963)
  - 文字列化結果を `"".join(...)` で exact built-in `str` に固定。
  - 検査した `text` をそのまま Git spec に使用し、`__format__`・`__str__`・`__radd__` 等の subclass hook 再介入を防止。

- [test_s8c_preregistration_core.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/tests/test_s8c_preregistration_core.py:208)
  - `git ls-tree -rz --full-tree` で exact candidate path を探索し、その blob 内容まで直接照合する helper を追加。

- [test_s8c_preregistration_core.py:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/tests/test_s8c_preregistration_core.py:1030)
  - 既存 CRLF/LF fixture に controlled path/blob の直接確認を追加。

- [test_s8c_preregistration_core.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/tests/test_s8c_preregistration_core.py:1040)
  - 単独埋め込み `\r` の独立 case を追加。
  - 一時 Git repo の軽量 probe では、単独埋め込み CR は別 blobへ alias せず intended blob を返しました。そのため「Git alias 防止」ではなく、裁定された policy としての拒否を固定しています。

- [test_s8c_preregistration_core.py:1058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/tests/test_s8c_preregistration_core.py:1058)
  - `__format__` 時だけ CR を注入する `str` subclass 回帰テストを追加。hook が呼ばれず、検査対象の文字列が指す intended blob を返すことを要求。

### 検査結果

以下を `tools/run_tests.py` へ指定しましたが、`qstat -Q preflight rc=1`、runner `rc=16` で停止し、実行数は 0 件でした。

- `test_read_blob_at_accepts_normal_path`
- `test_read_blob_at_rejects_embedded_path_control_chars[embedded-cr]`
- `test_read_blob_at_rejects_embedded_path_control_chars[embedded-lf]`
- `test_read_blob_at_rejects_standalone_embedded_cr_as_policy`
- `test_read_blob_at_uses_checked_text_without_str_subclass_format_hook`
- `test_read_blob_at_rejects_control_chars_after_single_stringification`

`--collect-only` も同じ dispatch 障害で未実行です。代替の静的確認では、両変更ファイルの AST parse と `git diff --check` が成功しました。

### 受理集合と波及

CR/LF を含まない通常の exact `str`・`Path` の受理集合と返り値は不変です。CR/LF 拒否も維持しています。変更点は、細工された `str` subclass が検査後に Git 向け文字列を差し替えられなくなったことだけです。

NUL・tab・その他制御文字、`./` 正規化、非文字列そのものの拒否は追加していません。

所有外では `read_blob_at` の全 consumer に exactification が波及しますが、固定 ASCII path と通常の契約 path の挙動は変わりません。production module bytes の変更により、commit 後の module hash／activation report digest は変化します。契約 JSON、freeze 成果物は未変更です。

変更は許可範囲内の次の 2 ファイルだけです。docs 編集、stage、commit は行っていません。

## 総括

F1〜F3 はすべて実装済みです。  
単独埋め込み CR は alias せず、policy 拒否として固定しました。  
受理集合の変更は subclass hook 迂回の閉鎖だけで、裁定外文字には触れていません。  
Pegasus dispatch 障害のため pytest は未実走で、3 所見とも `partial` です。