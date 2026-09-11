## 総括

現物の4箇所は既に改行エスケープになっており、ASTで文字列値が実改行になることを確認しました。修正パッチは旧文字列に一致せず適用されていません。本段の変更はありません。

| 所見 | 判定 | 確認結果 |
|---|---|---|
| 二重エスケープ4箇所 | partial | 31・35・36・69行の文字列値は正常。実機未確認 |
| 回帰 | 未判定 | pytest・build・全6 arm・M1/M2は未実走 |

変更行：なし。確認対象は `orchestrator/manual_probes/test_t2397_a1_source.py` の上記4行です。

検証範囲は静的AST確認のみです。抽出shellの構文・終端、JSONL出力、gate/build/verify失敗時の挙動は未実走のため、closed／greenとはしていません。

所有外変更・共有fixture変更・期待値の弱化はありません。波及先は既存dependency stagingとbuild証拠JSONLの出力です。テスト新設・改名はなく、追加の制約meta-testはありません。親のcontract-loader-driftには手を加えていません。