## 所見対応表 (closed/partial/regressed)

| 所見 | 判定 | 対応 |
|---|---|---|
| must-fix 1 | partial | 1巡目の変更を維持。未実走 |
| must-fix 2 (A) | partial | 公開経路の正例を実装済み・未実走 |
| must-fix 2 (B) | partial | 公開API負例4ケースを実装済み・未実走 |
| nit 1 | partial | 1巡目の変更を維持。未実走 |

closed と判定した所見はありません。

## 追加した正例

`test_aggregate_public_issue_load_and_preregistration_pin`

- workload が5／50／95の3 spec、各2窓・2セル。
- 全セル被覆、各窓40標本中1標本の欠測。
- 異なる3値の exact 最大を発行→読戻し→§5 pin解決で確認。
- v2、全入力のsummary／specのpath・hash、exact値、非保証の節・項目、成果物pinの一致をassert。
- 公開APIで再発行が `artifact_exists` となり、既存bytesが保持されることもassert。

## 追加した負例と停止 code

| ケース | assertした停止code |
|---|---|
| 期待spec列を固定してsummaryを1件除外 | `aggregate_spec_closure_error` |
| 成果物を非最大値へ変更し、float hex・外側hashを更新 | `aggregate_reconstruction_error` |
| 非最大入力の非保証項目を1件除外し、外側hashを更新 | `aggregate_reconstruction_error` |
| 1入力のenv_tagを変更し、較正seam・spec／summary hashを整合 | `aggregate_identity_error` |

identity負例は、変更入力が単体発行・読戻しを通ることもassertします。停止codeは未実走の期待値です。

## 変更した関数

今回の変更は `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` への追加のみです。

- `_aggregate_public_sources`
- 上記正例1関数
- summary欠落、成果物改変2ケース、identity不一致の負例3関数

既存関数・fixture・decorator・期待値と、issuer本体は今回変更していません。

## 実走結果 (nodeid と範囲)

試行コマンド：

```bash
PYTHONPATH=. python3 -m pytest orchestrator/tests/test_p3_b4_floor_artifact_issuer.py -q
```

対象はissuerテストファイル全体。**実走nodeidは0件**です。AST構文解析と対象2ファイルの `git diff --check` は成功しましたが、テスト成功には数えていません。

PreToolUse hook の `guard_bash` が、Pegasusログインノードでのpytest直接実行を拒否しました。診断はqsub／qloginによる計算ノード実行を要求しています。

## 波及の静的列挙

- 本体の追加変更がないため、所有外callerの実行時挙動への新たな変更はありません。
- 新fixtureは共有helperを呼びますが、既存helperは変更していません。
- Git・較正のmonkeypatchはテスト単位です。集約関数の差し替えはありません。
- material reportのresolver→loader→evaluator経路、既存consumer testは未実走です。
- spec間のwindow出力path共有も新正例に含め、1巡目の変更を公開経路で検査する構成です。

## 未実走・未完了

追加5ケースと既存テストの実走確認が残っています。

材料レポートへの到達は追加していません。合成repoにはfloor入力だけがあり、公開builderが要求するprerun publication・raw analysisがありません。既存 `immutable_publication` は別途証拠を構築するfixtureで、そのまま渡せる構成ではないため、指定どおりpin解決までで止めました。

## 総括

(A)(B)は実装済み・未実走です。  
既存期待値、docs、duration ledger、所有外ファイルは変更していません。  
`git add`・commitは行っていません。