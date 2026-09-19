**判定：静的レビューは GO。固定 commit 全体の最終採用は、親の実測・変異・受入結果が未完のため NO-GO（保留）。** 新規の must／should／nit 所見はありません。

- **fixture／pin 閉包**：`test_paper_story_a2_certification.py:1869` の literal hash は実ファイルと一致。protocol pin は維持されています。`:4891` 以降の pin 負例は、追加した4 sibling と hostname により host 検証を通過します。既存 autouse fixture が staged-source 検証を代替するため、そこで pin 負例が手前 mask される構造もありません。source-role 負例の実 predicate 呼出し assert も維持されています。
- **受理／拒否・検出力**：同ファイル `:2071–2117` では5node正例と、専用policyによる単一nodeの受理・拒否が共存します。既存負例の削除・緩和は見当たりません。M2 の不足／過剰例は malformed・duplicate・head を含まず、count 拒否に到達する入力です。
- **候補テストの到達性**：`test_paper_story_a2_job_contract.py:1076` は `run-workload` capture、終了コード、継承 lock、別jobの dependency path まで要求します。手前で終了して成功扱いになる構造ではありません。ただし予約・staging・preflight は mock であり、実 flock の証拠にはなりません。
- **param ID の consumer**：旧IDの参照は duration ledger に残りますが、`tools/acceptance_shards.py:395–404` は未登録IDを1秒で扱います。今回の変更による選択漏れ・consumer破壊は静的には認めません。
- **probe の証拠範囲**：`t2489_lock_probe.py:114–142,195–238` は実 `bench_lock`、別process／scratch、保持通知→挑戦→解放を使います。同HOME条件と default 対照もあります。compute側が実証するのは抽出した実source assignmentのpath挙動で、実job body全体のexport継承ではありません。

採否で注意すべき具体的反例は、`paper_story_a2_certification.sh:349` により候補が scratch の lock を保持していても、同nodeの default consumer が HOME の別lockを取得できるケースです。`t2489_lock_probe.py:239–243` はこれを意図どおり観測として保存し、正常終了を許します。したがって **probe の rc=0 は候補採用の根拠になりません**。両方向の退行が実測された場合、rulingどおり job body変更と候補専用testを最終diffから除く必要があります。

## 総括

nodes=5 の整合変更と静的な検出力に阻害所見はありません。6ファイルのauthor provenanceを前提にレビューしました。テスト・probe・変異は実行しておらず、未完結果を緑とは判定しません。最終採用は親の実測結果と候補除外判断を待ちます。
