## 総括

指定ファイルに 2 定数を追加し、assert を変更しました。

- 旧：prereg 記録値 == 現行ファイルの SHA256
- 新：記録値 == 凍結定数、現行 SHA256 == 現行定数、両定数 !=
- 後継テスト：live 比較なし。変更なし。
- 削除した test 関数：0 件。commit なし。

実走結果（nodeid 接頭辞：`orchestrator/tests/test_s8b_oracle_n_pilot.py::`）：

| 関数の個別実行 | rc |
|---|---:|
| `test_r33_protocol_document_loads_from_repository` | 0 |
| `test_r33_successor_protocol_document_loads_from_repository` | 0 |
| `test_protocol_exact_schema_and_preregistered_design`（一時ディレクトリを渡して実行） | 0 |

3 件とも赤 0。全走はランナーの `qstat -Q` 失敗で開始前に rc=16。指定のファイル直接実行は rc=0 ですが、テスト関数は起動されません。

`sha256sum tools/pegasus/oracle_n_pilot.sh`：
`3ceaabd1b8b3759fb24b136f44256e8ae76115dd6d1a283bc205c86de01a0ed1`
— 追補 4 と一致。凍結 prereg 2 本は未変更です。

ただしランナーが `output/pegasus-dispatch/b5e66f163dc7719257f9b7aaa3d52d17/` に診断ファイル 4 本を生成しました。復元の削除操作は自動承認審査（PreToolUse）に防護パスと不透明構文の組合せとして拒否され、残っています。