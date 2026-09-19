## must-fix

なし。指定された検出の欠落、受理集合の意図しない拡張、成果物を壊す変更は確認できませんでした。

## should-fix

なし。

## 削れるもの

追加 20 ケースについて、ケース単位で削除できる重複は確認できませんでした。

- 正常／退行の全件 materialize、成功数 1／2 の partial 拒否、workload／cell の shape 不足は、それぞれ異なる分岐を検査しています。
- 重複検出の 6 追加 param は、同 study・他 study・接頭辞衝突・逆方向の干渉を分けています。
- policy bytes pin は裁定が認めた固定値です。tmp path は fixture から組み立てられ、実行ごとに変わる SHA の焼き込みはありません。

## refuted

1. **「closed set 追加を超えた変更」ではない。**  
   `git diff 657e1e5a7 c18a80967 --stat` は指定の **5 files、376 insertions、12 deletions** のみ。module の変更は定数・canonical path・job 名・環境集合・shape・説明文です。新 gate、partial 一般化、job body、plotter、docs の変更はありません。

2. **要求された検出は揃っている。**  
   `orchestrator/tests/test_paper_story_a2_certification.py:2575` に全件 materialize の正常／退行 2 param、`:2666` 付近に adopted genome・未知 key・shape 不足、`:2681` に非 canonical 拒否、`:2695` に partial 不変があります。  
   `orchestrator/tests/test_paper_story_a2_job_contract.py:1131` に重複検出、`:1352` に 3 request 契約があります。後者は実 submitter を wrapper 経由で呼び、実際の qsub argv と receipt を比較しており、性質だけを眺める恒真テストではありません。

3. **判定規則 v2 の field 名と計算は実装に一致する。**  
   `orchestrator/campaign/paper_story_a2_certification.py:2682` は 5 標本の median、`:2924` は `cells[].performance.median_tps`、`:2933` は workload ごとの median 比 − 1、`:3017` は `effects`、`:3019` は `a4_noise_floor_status="open"` を出力します。  
   注意すべき読み方も裁定で処理済みです。`:2998` の outer status は全 effect が正なら `observed-positive`、それ以外は `reject` となるため、**床以内の微減でも reject になり得ます**。これは床超退行や anomaly と同義ではありません。また、cell に median が残っていても correctness／source binding が不成立なら effect は出ません。`ruling-s4.md:28` と `:30` の規則がこの誤読を防いでいます。

4. **既存不変条件は維持されている。**  
   上記 diff に A-2／A-6 policy と指定の旧 attempt leaf は含まれません。policy bytes は基準 commit と直接比較して一致しました。現行実装の canonical 化で再計算した protocol SHA も既存 pin と一致します。

   | policy | bytes SHA 接頭辞 | protocol SHA 接頭辞 |
   |---|---|---|
   | A-2 | `f8a778060076` | `d99f08bcc50c` |
   | A-6 | `682e0f4ed980` | `21427e71793e` |

5. **実投入の identity は確認できる。**  
   durable attempt の `b7f5-20260919a/receipts/submission.json:1` は rr5／rr50／rr95 にそれぞれ `10807/10808/10809.nqsv`、source commit に `c18a80967…` を記録しています。`preregistration.json:1` の policy SHA は `c6b24050d17c4bc552d254ce65e328b3a6edca919387b5720b4e025ea78b0df1` で、checkout の bytes と一致します。

6. **親のログと author 報告は矛盾しない。**  
   focus は **307 passed**。meta は local の cap OOM 後、計算ノードへの dispatch で **1071 passed / 6 skipped、child rc=0** です。author は自身の実走を rc=16・子未起動と明記しており、親の後続実走とは別です。両ログの「受入全走ではない」という限定は維持すべきです。  
   `brief.md:93` の A-2 SHA、`ruling-s4.md:16` の既存 pin、`:42` の submitter 273／365 行、`:26` の床値はいずれも実体と照合できました。prereg source digest `678b7203…` も `docs/t1998-balanced-stock-inline-preregistration.md:87` に存在します。

## 裁定パッケージ候補

なし。

## 総括

レンズ B では実装修正を要する real 所見なし。  
追加は所有範囲内で、要求された 20 ケースに検出上の役割があります。  
collect 出力は判定規則 v2 に必要な field を備えています。  
未確認：実 attempt の最終測定値・collect 成否、および変異の KILLED／SURVIVED。  
本レビューでは pytest を実行していません。