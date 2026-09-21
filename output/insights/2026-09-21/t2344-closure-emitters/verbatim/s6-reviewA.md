## 所見 1: 段 4 が corpus 条件を独自に免除している

**real / must-fix**

根拠: [s4-ruling.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/s4-ruling.md:45) は実在 corpus 条件の未充足を認め、同 commit 収載を優先しています。しかし [rulings-verbatim.md:156](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/rulings-verbatim.md:156) の D2193 は、同 commit 条件と実在 corpus 条件を**両方**明記しています。D2194 項 4 も D2193 を参照しており、corpus 条件の免除は明示していません。

旧 exact-63 が前進後に発生した実測は、予防的収載の合理性を支えますが、exact-85 の実在確認や条件免除の根拠にはなりません。実装子の逸脱ではなく、段 4 裁定への帰属です。

直し方: exact-85 corpus の wire 列・記録 commit の宣言順を照合して条件充足を示すか、直前 grammar に限る条件免除を裁定パッケージとして明示的に確定してください。事後に覆せる形での開示だけでは不足です。

## 所見 2: exact-85 の certified 流入は壊せなかった

**refuted / nit（修正不要）**

根拠: `orchestrator/campaign/campaign_lock.py:587,904,943,961`、`orchestrator/campaign/artifact_admission.py:1058,1198,1216`。

通常 validator は exact-96 の集合のみを受理します。歴史 decoder の現行ラップは通常 decoder を先に通り、exact-85 は専用 authority／decoded 型へ分岐します。purpose は decode 前に exact enum を検査し、certified gate も歴史 epoch 型を拒否します。これらの既存関数は変更前との AST 比較でも不変でした。

直し方: 不要。

## 所見 3: exact-85 validator の禁止条件に破れは見つからなかった

**refuted / nit（修正不要）**

根拠: `orchestrator/campaign/campaign_lock.py:775`、`orchestrator/tests/test_campaign_lock_codec.py:1007,1051`。

authority の exact key 集合、正の exact int、sorted wire 列、lowercase 64 桁 hex を検査し、blob map は独立 literal の宣言順で再構成しています。84／86／同数別集合85／順序違い／現行96／95 は拒否されます。兄弟 exact-63 validator と識別子だけを置換したソースが完全一致し、例外文面・検証順の取り違えもありません。

直し方: 不要。

## 所見 4: scope 凍結・path 対応・固定値は独立検算で一致した

**refuted / nit（修正不要）**

根拠: `orchestrator/campaign/artifact_admission.py:125,259,309,1149`、`orchestrator/tests/test_artifact_admission.py:382,3549,3959`。

変更前 `5efd69367` の Git blob と AST literal を比較し、旧現行85と歴史85の tuple、および scope 2 定数の UTF-8 bytes が完全一致しました。旧24／62／63の定数も不変です。scope 対から path tuple への対応に取り違えはありません。

production を import せず再計算した epoch／path hash の4値は、裁定とテスト内 literal に一致しました。hash preimage は domain・宣言順path・digest のままで、scope は入りません。

直し方: 不要。

## 所見 5: 未知 grammar 負例と既知 grammar の衝突は見つからなかった

**refuted / nit（修正不要）**

根拠: `orchestrator/tests/test_campaign_lock_codec.py:315,676,714,790,1007`、`orchestrator/tests/test_artifact_admission.py:2206,3373,3636,3896`。

「96から末尾11本を落とした85」を未知 grammar とする負例はありません。exact-63／85の subset は先頭の `env_contract.py` を除去し、既知の62／84への誤認を避けています。既存 `paths[:-1]` は62から61、62の superset は未知path付き63なので、既知63とは別集合です。順序違いは集合ではなく wire 列の拒否を検査しています。

直し方: 不要。

## 所見 6: 既存テストの緩和はなく、新11本の拒否も到達可能

**refuted / nit（修正不要）**

根拠: `impl-diff.txt` 全42ハンク、`orchestrator/tests/test_artifact_admission.py:3774,4029`、`orchestrator/campaign/contract_loader_binding.py:518`。

9ファイルの着地内容は差分の新 blob と一致しました。既存テストの期待反転・緩和・削除・skip／xfail追加はありません。既存22本の drift node は decorator を含む AST が不変で、新11本は独立 literal と現行tupleの追加部分が一致します。

dirty bytes は capture の disk対HEAD比較で例外となり、中央 gate が `E1-stale / current-closure-unavailable` に変換します。commit後の受理は既存 gate の仕様どおりです。

なお、追随は厳密には値変更だけではありません。layer3 は85の歴史ケース追加、s8b は独立scope assertion追加も含み、いずれも検査強化です。図provenanceはscope値の更新だけです。

直し方: 不要。

## 所見 7: 焦点走の赤は0件

**refuted / nit（修正不要）**

根拠: [focus-f1-summary.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/focus-f1-summary.md:8)。

親報告は job `14685.nqsv`、**4441 passed／9 skipped／0 failed／0 error** です。帰属を切り分ける赤はありません。実装子の「未実走」は先行する報告で、親の後続実走と矛盾しません。本レビューでは pytest を実行していません。

直し方: 不要。

## 総括

**NO-GO：段4の corpus 条件免除が拘束裁定と整合していません。**
コード上の certified 隔離、validator、scope、hash、負例は静的検査で壊せませんでした。
最大の risk は、未充足条件を実装 wave の解釈で免除したまま収載を確定することです。
ファイル変更・pytest実行は行っていません。