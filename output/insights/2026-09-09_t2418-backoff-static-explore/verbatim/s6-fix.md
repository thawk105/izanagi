## F1 の修正

T2418 report が返す `.dat` / `.json` の basename を、独立 literal で検証する assert を2件追加しました。

## F2 の修正

`T2418_MEANING_WITNESS_STATUS` を共有定数として定義し、`meaning_witness_status` を以下へ同値で追加しました。

- `search_config`
- JSON report top level
- `.dat` provenance comment

定数値と3箇所の搭載を、production 定数を参照しない literal で固定しました。

## F3 の修正

既存 run-path test の materializer を spy 化し、以下を直接検証しました。

- 4/5 committed: 0回
- 5/5 committed: 1回

既存の CLI 完走テストは維持しています。

## 実走したテストと結果

実行コマンド:

`PYTHONPATH=. python3 orchestrator/tests/test_backoff_extended_sweep.py`

範囲: `orchestrator/tests/test_backoff_extended_sweep.py` の全 nodeid、47件。

結果: `47 passed in 5.39s`

## 実走できなかったもの

指定された実行制約に従い、他のテストファイルやリポジトリ全体のテストは未実走です。テストの新設・改名はないため、新たな単位に対する meta-test は発生していません。

## 所有外の caller・共有 fixture・consumer test への波及可能性

関数 signature、artifact stem、既存 field、共有 fixture は変更していません。F2 は additive field のため、top-level や provenance のキー集合を完全一致で検査する所有外 consumer には波及する可能性があります。投影内の既存 T2266 consumer 拒否テストを含む全47件は通過しました。

## 総括

許可された [実装ファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2418-fix1/orchestrator/campaign/backoff_extended_sweep.py) と [テストファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2418-fix1/orchestrator/tests/test_backoff_extended_sweep.py) のみを変更し、F1〜F3を修正しました。commit・git操作は行っていません。