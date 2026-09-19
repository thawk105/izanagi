## 総括

対象テスト2ファイルを修正しました。**実装済み・未実走**です。

| 所見 | 状態 | 対応 |
|---|---|---|
| REPORT fixture | partial | REPORT の所有TUだけに無条件宣言を追加。実走確認待ち |
| rung1 実 helper 検査 | partial | 実 factory／登録簿を使い、REPORT の宣言型・所有TUと、BACKOFF_FIXED／RUNG1 の `None` を捕捉するテストを追加。実走確認待ち |
| companion 負例の帰属 | closed | meaning arm 単体の検査であり、同じ入力は supply も拒否すると docstring に明記 |

検査結果：

- 指定テスト：rc=16。`qstat -Q` 事前確認失敗で子プロセス未起動。実行 nodeid 数0、pytest所要なし（起動試行約0.41秒）。
- `check_codex_agents.py`：rc=0。
- `check_docs.py`：rc=0。
- `git diff --check`：rc=0。

production 4ファイル、既存の期待値、他macroのfixture、probe、docsは変更していません。commitも作成していません。