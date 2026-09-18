## 総括

**GO（独立静的監査として）。新統合tipのland可否は、親の正規runnerによる受入後に確定してください。**

対象は `b2037abfa..4dfc6ba8398df622ec27461003aa43b24a12b0ad`。今回、成果物の値・受理集合・参照を不当に変える新規must-fix、または未記録の裁定前提違反は見つかりませんでした。

A-3の委譲範囲は未知性層2に限定されています。receipt履歴・静的検証・epoch比較・refusal集約・invalid拒否は維持されています。段6訂正後の鮮度契約とも一致します。

## 所見表

以下の `C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/` です。closedは静的確認の判定であり、新tipの実走成功を意味しません。

| 項目 | 判定 | 根拠・影響 |
|---|---|---|
| 同一root／HEAD／世代の委譲条件 | closed | `C/t080_freeze_migration.py:2232`。exact型、root、outer／inner HEAD、active世代のSHA・番号・commit、列挙digestを照合。不成立時は通常scan＋zero-hitへ戻る。 |
| full validationとreportの対応 | closed | `C/s8b_ratified_freeze.py:3550`。C2-4完全一致とartifact再捕捉の後にreportをdeep-freezeしてtokenへ格納。凍結文書との束縛も両側で検査。 |
| receipt静的検証・履歴・invalid | closed | `C/t080_freeze_migration.py:2335`、`C/s8b_oracle_driver.py:190`・`:210`。委譲によって他の検査や無条件refusal集約を省く経路は見つからない。 |
| epoch／E3b／旧RA-1・RA-3 | closed | `C/s8b_oracle_driver.py:1531`。同じtokenでreceiptを再解決し、4要素のepochを比較。再launch・再走査を追加せず、既存E3bの同一object消費を維持。 |
| **旧RR-1：copy後の親root読取り** | **closed（指摘経路）** | `T/test_s8b_ratified_freeze.py:1035`。接続分岐は必要材料のcopy内実在を先に要求し、calibrationもcopyから読む。selector roleはbase構築時に取得。欠落時の親fallbackを防ぐ7条件の負例も存在。 |
| 旧RR-3：変異証拠未完 | closed（旧tip） | final A/Bのspec hash一致、baseline成功、12 KILLED＋コメント変更1 SURVIVEDを確認。m2bは実際に `refused→completed` を観測しており、診断文字列だけのkillではない。 |
| 旧RR-2：時間目標 | partial | 通常受入300秒以内、base／copy別の削減量は未証明。今回の正しさblockerにはしない。 |
| 旧RR-4：報告の量化 | partial | 旧handoffには訂正対象の記述が残る。回収記録では「接続8＋draft1」「baseはkeyごと」を使い、中断走から個別PASS集合を断定しない。 |
| 全consumer・T-2776境界 | closed（静的） | driver、holdout adapter／CLI、memo、driftguards、admission、report、直接constructorと生成scriptを照合。token省略経路は従来動作。official clean scan、走査除外、hold、chain／G bytesに変更なし。 |

旧RR-1の閉鎖は、**base構築自体が親repoを読まなくなったという意味ではありません**。shared-baseのlockもreal-repo writerとの排他を証明しません。この既存残余を「競合完全解消」と記録しないでください。

## 未実走／残余

- **新統合tipのテスト・変異・受入は未実走。** 旧finalの対象は両方とも `e2b3cc483`。production 3ファイルと焦点4テストファイルは統合後も同一、全13 anchorも一意ですが、新tipの緑へ読み替えません。
- 変更Python 12ファイルのAST解析、`run_block`の15 refusal-returnを静的確認しました。テスト成功の代替ではありません。
- 同名ファイルの内容交換によるhit増減は検出しません。例えばgate後に既存のnamespace外ファイルへhitを書いても、HEAD・名前集合が不変なら保持reportが使われます。これはF1と旧decisions fragmentに明記済みのsingle-tenant残余であり、新発見ではありません。「campaign-startで内容鮮度を再検証済み」とは主張できません。
- 実A／X発効後の正例は未実測です。chain／X2／Gのland、実A／X発行、コード・テスト編集は行っていません。