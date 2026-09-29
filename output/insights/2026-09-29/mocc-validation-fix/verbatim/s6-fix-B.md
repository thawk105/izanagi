## 変更内容

- [moccfix_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/moccfix-b/output/runs/moccfix-b/tools/moccfix_probe.py): `CCBENCH_TRACE` を `1`/`0` に修正。各 arm の build 後、benchmark 前に `cc/mocc/transaction.cc` の実 compile 命令で TRACE 値と計器 define を検査します。F 対照の件数を R0 と verifier を通った走だけで集計し、無効走数を別 field に追加。未使用の `legacy_selftest()` を削除しました。SHA-256: `e70ee41d22f96e773cb31eba2013c11440f605bdd20f3f9bdc9f68614e40e991`
- [run_judge.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/moccfix-b/output/runs/moccfix-b/tools/run_judge.sh): 両 compiler の結果に応じて結果名を選び、F→X の全文 diff を `F-to-X.diff` に保存して変更 path 数・hunk 数を report に記録します。SHA-256: `fba54d64d862a4e609fa0e86f57d3f11426c8ade03ad2ea6062ca508cfd2383a`

arm 定義の真偽値は `trace` と `probe` のみでした。文字列化されるのは `trace` だけで、今回修正しました。`probe` は条件分岐に使われ、文字列化されません。arm 定義 JSON は編集していません。

## 検査の実走結果

| command | rc | 結果 |
|---|---:|---|
| `PYTHONPYCACHEPREFIX=/tmp/moccfix-pycache python3 -m py_compile output/runs/moccfix-b/tools/moccfix_probe.py` | 0 | 通過 |
| `PYTHONPYCACHEPREFIX=/tmp/moccfix-pycache python3 output/runs/moccfix-b/tools/moccfix_probe.py selftest` | 0 | 10/10 通過。既存の期待値は変更なし |
| `bash -n output/runs/moccfix-b/tools/run_judge.sh` | 0 | 通過 |
| `PYTHONPYCACHEPREFIX=/tmp/moccfix-pycache python3 /tmp/moccfix_compile_check.py` | 0 | T_X 負例を拒否。N_X 実ファイルも拒否。`-DTRACE=0` に直した一時コピーは通過 |

指定された N_X の実 compile 命令は、正例と説明されていましたが、実際には **`-DTRACE=False`** でした。検査関数がこれを拒否するのは意図どおりです。build・benchmark・verifier・dispatch は実行していません。

## S6-1〜S6-5 の対応表

| 項目 | 状態 | 根拠 |
|---|---|---|
| S6-1 | partial | 修正と build 後検査は実装済み。T_X 負例は拒否し、修正した一時正例は通過。指定 N_X 実ファイルは `False` のため通過不可 |
| S6-2 | closed | 両方 `expected_failure=true` の場合だけ意図した修理差分、両方 rc=0 なら合格、その他は理由未確定 |
| S6-3 | closed | 全文 diff の保存と変更 path 数・hunk 数の report 記録を実装 |
| S6-4 | closed | F 対照を有効走で集計し、`F_invalid_runs` を追加。X 成功式・反復数・arm 構成は維持 |
| S6-5 | closed | 未使用関数だけ削除 |

## 総括

道具の修正と許可された検査は完了しました。残る検査上の不一致は、指定された N_X 証拠ファイル自体が `-DTRACE=0` ではなく `-DTRACE=False` を含む点です。