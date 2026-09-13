## 追記した nodeid の件数と、その所要の出所

58 件。対象ファイルの 55 件と、同じ JUnit 内の `test_ccbench_spawn_sites.py` の未登録 3 件です。指定の実測 JUnit を正本生成器で処理しました。推定値・placeholder はありません。

## 既存登録が 1 byte も変わっていないことの確認方法と結果

更新前の bytes と比較し、既存 23,049 件の行が完全一致しました。追加行を除き、件数欄を戻すとファイル全体も元の bytes に一致しました。

## JUnit に無くて追記できなかった nodeid

無し（0 件）。対象ファイルの定義・パラメータから確認した 55 件すべてが JUnit にあります。

## 実走結果

共通 command：
`python3 tools/update_acceptance_duration_ledger.py`

共通入力：
`/home/SFC/tanab/.claude/jobs/3f23d4a5/tmp/t2566/junit-focus.xml`

| オプション | rc | 結果 |
|---|---:|---|
| `--add-only` | 0 | 58 件追加 |
| `--add-only --check` | 0 | bytes 一致 |
| `--check` | 1 | 焦点走だけから生成する全体台帳とは不一致 |

補助検証は「追加は対象の 55 件のみ」という仮定で AssertionError になりました。不変性の検証はその前に通過済みです。差分で追加 3 件も指定 JUnit の実測値と確認しました。

## 守れなかったこと

境界違反は無し。変更は所有台帳のみで、commit・docs 編集・テスト実行はしていません。

## 総括

対象の 55 件をすべて登録しました。  
指定 command により、同じ JUnit の未登録 3 件も追加されました。  
既存登録は byte 単位で保持されています。  
`--add-only --check` は成功し、`--check` 単独は不一致でした。

補助検証の再実行は PreToolUse hook に拒否されました。理由は、防護パスと不透明構文の同居が分類不能という判定です。その後、読み取り専用の `git diff` で確認しました。