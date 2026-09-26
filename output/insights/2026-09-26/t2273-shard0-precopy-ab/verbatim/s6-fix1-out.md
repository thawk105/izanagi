## 所見ごとの対応

| 所見 | 状態 | 変更箇所・自己検査 |
|---|---|---|
| RA1＝RB1 | closed | [runner:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_runner.py:650) P の child 環境値を記録し、未設定の `T2273_LOCAL_OUTPUT_SOURCE` を `None` に戻した。P 環境値を持つ合成対は有効。 |
| RA2 | closed | [plugin:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:471) import と写し生成を thread 内へ移動。静的検査で hook 本体に import がなく、thread 内にあることを確認。 |
| RA3 | closed | [plugin:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:38) file の path・size・mode・mtime と directory の path 集合を分けて digest 化。directory size だけの差は一致し、file mtime の差は不一致。 |
| RB2 | closed | [analyzer:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:857) 全 builder key に A/P 各 1 件の digest を要求。P digest 欠落の合成対は無効。 |
| RA5＝RB3 | closed | [analyzer:959](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:959) 集計を有効対に限定。有効 2 対の系列は「判定保留 (取り直し)」となり、(b) を名指ししない。 |
| RA4 | closed | [analyzer:937](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:937) 必須欠測を無効条件に追加。P 固有の `copy.list` 欠測だけを除外一覧に明記。両ケースを合成対で確認。 |
| RA6＝RB4 | closed | [analyzer:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:901) 実際の memo 例外の構造化文から超過を判定。合成 log で対の除外と P の件数 1 を確認。 |
| RB5 | closed | [analyzer:980](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:980) 有効対の key 別・条件別中央値で phase を選び、key・phase・値を出力。総和なら別 phase を選ぶ fixture で確認。 |

## 自己検査

`python3 -m py_compile`（3 ファイル）、`git diff --check`、合成 fixture の `--ab-dir`・`--ab-series`、発行 child の compile と元の文順の静的検査は通過しました。変更は所有する 3 ファイルのみです。

## 限界・未解決

pytest suite、計算ノードでの本走は**実装済み・未実走**です。所有外の test・conftest と既存 caller は変更していません。

## 総括

裁定の 8 件を修正し、合成入力で判定を確認しました。既存 `run`・`pair` 向けの変更は未設定値の回復に限っています。commit は作成していません。