## 所見ごとの対応表 (F1〜F4 の closed / partial / regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | 非 UTF-8 target bytes の symlink blobを作り、item 非掲載・counter 不変を固定 |
| F2 | closed | `R.MAX_LEDGER_BYTES` 超の valid UTF-8 JSON が retained item になることを固定 |
| F3 | closed | `.md` の NUL 入り valid UTF-8 control を追加し、membership・counter 不変を固定 |
| F4 | closed | typed insight の marker 2 値を positive assertion で固定 |

## 変更した file と行

変更したのは [orchestrator/tests/test_ruleops.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:196) だけです。

- 196–223 行: `.md` NUL control
- 420–442 行: NUL membership と typed marker
- 497–526 行: 非 UTF-8 symlink blob
- 529–543 行: size 上限超過テスト

`tools/ruleops.py`、docs、凍結証拠は編集していません。`git add`、commit も実施していません。

## 追加・変更したテストと固定した内容

- `test_inventory_non_utf8_counter_excludes_out_of_scope_and_nonregular`
  - 実環境で target byte `0xff` の symlink 作成が可能なことを確認。
  - commit 後の mode 120000 blob payload が意図した bytes と一致することを検査。
  - symlink path が `items` に存在せず、`skipped_non_utf8 == 0` を固定。

- `test_inventory_retains_oversize_valid_utf8_blob`
  - `R.MAX_LEDGER_BYTES` から導出した上限超過 valid JSON を専用 fixture として作成。
  - strict UTF-8・JSON 妥当性、item membership、記録された byte 数、counter 不変を固定。

- `inventory_encoding_matrix_repo` / `test_inventory_non_utf8_skip_matrix_and_utf8_formats`
  - 中立名 `kilo.md` に strict UTF-8 の NUL 入り control を追加。
  - membership と既存 `skipped_non_utf8 == 6` を接続。
  - 既存 `output/insights/source.md` の marker が `("none", "no-state-change")` であることを固定。

既存期待値の反転・緩和・削除・skip はありません。

## 走らせた nodeid と結果 (走らせていないものは走らせていないと書く)

次の nodeid を `tools/run_tests.py` 経由で計算ノードへ dispatch しました。

- `orchestrator/tests/test_ruleops.py::test_inventory_non_utf8_skip_matrix_and_utf8_formats`
- `orchestrator/tests/test_ruleops.py::test_inventory_non_utf8_counter_excludes_out_of_scope_and_nonregular`
- `orchestrator/tests/test_ruleops.py::test_inventory_retains_oversize_valid_utf8_blob`

結果は `qstat -Q preflight rc=1` による dispatch infrastructure failure、終了コード 16 でした。pytest 本体は走っておらず、実行済み nodeid は 0 件です。緑は主張しません。

静的検査は以下が rc=0 です。

- `python3 -m py_compile orchestrator/tests/test_ruleops.py`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## 波及可能性

- matrix fixture の既存 consumer 3 件へ `.md` control が追加されます。valid UTF-8 なので既存の skip 内訳 `6/1/5` は変わりません。
- F2 の 1 MiB 超 blob は専用テスト内だけで生成されます。共有 fixture の構築コストは増やしていません。
- F1/F2 の synthetic repo は各 `tmp_path` 内に閉じています。
- `_base_repo` 自体は変更しておらず、F4 は既存 typed insight を読むだけです。
- test collection に node が 1 件増えますが、新規 test file ではないため plain-runner の新規ファイル管理面には波及しません。
- production caller、inventory consumer、docs schema、凍結成果物への変更はありません。

## 残る赤とその理由

製品テストの赤は観測していません。計算ノード dispatch が preflight で失敗したため、焦点テストの合否は未実測です。親による再 dispatch／受入全走が必要です。

## 総括

4 所見は静的にはすべて closed です。指定されたテストファイルだけを強化し、production 実装・既存期待値・受理集合には触れていません。最終 GO 判定には親環境での pytest 実測が残ります。