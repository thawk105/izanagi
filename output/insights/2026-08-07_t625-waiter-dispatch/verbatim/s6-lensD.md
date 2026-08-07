静的レビューのみ実施した。pytest / `check_docs` は未実走であり、実装子報告の結果も独立確認していない。`dev-wave` の fail-closed・局所修復規律を判定基準にした。

## Real 所見

### D-1 — 「第3案」の承認対象を確定できず、F31 だけでは4要素実装を正当化できない

- 主張: 三資料の唯一の実質差分は「待ち条件作成」の有無であり、意味を変える差である。ユーザーの直接発話は「推奨通りで」だけで、その直前に全文案と要約のどちらが提示されたかは資料から判別不能。4要素実装・3要素実装のどちらにも確実な権限がないため、親はユーザー再裁定待ちで停止すべきだった。
- 根拠 (file:line):
  - 案本文は「背景 producer／待ち手の生成・再利用・停止、通知処理、**待ち条件作成**の直前」を含む。`output/insights/2026-08-07_t597-dev-wave-budget/s6c-review.md:50-54`
  - 一次控えは「第3案」と記す一方、「背景 producer・待ち手の生成/再利用/停止、通知処理の直前」と要約し、同句を落とす。`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:345-349`
  - worklog の裁定前候補、エントリ294、現在の「次の一手」も一貫して3要素である。`docs/worklog.md:2307-2312,2727-2734,3115-3119`
  - F31 は、既に成立した decision の制約を後続要約が落とした事例を対象とする。今回の全文側は裁定前の敵対レビュー案であり、それ自体を「decision 本文」と扱える根拠がない。`docs/failures.md:593-602`、`docs/dev-wave/core.md:41-43`
  - `DW-O12` は実行内容を正しく記録する規則であり、裁定との差を後日開示すれば実装してよいという権限ではない。`docs/dev-wave/operations.md:69-72`
- 成果物影響: 4要素版は待ち条件作成時にも `DW-C00` を再読させる受理集合へ拡張する。3要素版には、生産者死亡を束縛する前に待ち条件が確定し、無音待機が worklog／試行台帳から欠落する経路が残る。
- 深刻度: blocker

### D-2 — literal pin が条件24の局所修復を越えて既存key全体へ一般化している

- 主張: A-1 が要求した独立 oracle は `24 → DW-C00` だけで閉じる。`15`/`21`/`22` と非-operation key の完全集合まで固定したのは、親の段4裁定による無断の受入条件拡張である。
- 根拠 (file:line):
  - A-1 は条件24の誤配線だけを問題にしている。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s3-lensA.md:5-10`
  - 実装は `{15,21,22,24}` の参照先と完全key集合を固定する。`orchestrator/tests/test_check_docs.py:4775-4790`
  - `15` は既存テストですでに固定済みである。`orchestrator/tests/test_check_docs.py:4749-4754`
  - 独立2例のない族一般化では局所修復が既定である。`docs/dev-wave/core.md:55-58`
- 成果物影響: `check_docs` 自体の文書受理集合ではなく、テストが受理する契約変更集合が縮む。将来 `21`/`22` を正当に変更したり新しい非-operation key を追加したりする wave は、この無関係な完全集合pinも同時更新しない限り拒否される。変更不能ではないが、未裁定の追加不変条件になる。
- 深刻度: must-fix

### D-3 — worklog 用語として「機械で保証する」がまだ広すぎる

- 主張: 裁定文には「機械で保証する」が残る。最終記録では「`check_docs` が解析可能な条件行のkey・行数・参照pairを検査する」と書くべきで、実行時の再読や3条遵守まで含む「保証」は避ける必要がある。
- 根拠 (file:line):
  - 裁定文の該当語。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:67-72`
  - parser は発火条件セルを保持せず、key・参照pair・parse済み行数だけを比較する。`tools/check_docs.py:3148-3152,3180-3192,3895-3907`
  - 実行時遵守を観測するfieldがないことは裁定自身も認める。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:90-97`
  - 実装子報告上も関連pytestは未実走である。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s5-impl.md:21-23`
- 成果物影響: worklog／最終レポートが、source構造検査を実行時遵守の証明として記録し、proof chain の射程を過大にする。
- 深刻度: must-fix

### D-4 — 「逐語」という説明は不正確だが、行の意味は保存されている

- 主張: 実装は段4の指定行には完全一致するが、元案本文とのbyte単位の逐語一致ではない。ただし意味を変える差は見つからない。
- 根拠 (file:line):
  - 元案の `／` は実装で ` / `、末尾の「直前に `DW-C00` を再読する」は「発火条件」「読む節」の2セルへ分解されている。`output/insights/2026-08-07_t597-dev-wave-budget/s6c-review.md:50-54`、`.claude/commands/dev-wave.md:82,106`
  - 段4が「逐語」と呼んだ実装行には正確に一致する。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:31-35`
- 成果物影響: 発火集合・参照先・台帳値は変わらない。監査記録上の「逐語」を「表形式への意味等価な分割」と訂正するだけでよい。
- 深刻度: nit

## Scope 境界の反証済み事項

- command 入口編集は第三条件に該当する。dispatch 自体を発火させる常読命令であり、L2 reference 内へ置くと自己発火できない。現物も9056 B／最長137文字で予算内。`docs/skill-self-improvement.md:39-50`
- 差分は裁定対象の3ファイルだけで、上記pin一般化以外の追加変更はない。
- scope 外3件の回し方は妥当。B-R3 は新しい成果物fieldとconsumerを要し、A-3 は既存全keyに及ぶparser一般化、A-2/B-R2 は「意味をlint固定しない」現行方針に反する。`s4-adjudication.md:90-97`、`docs/dev-wave/core.md:55-58`、`docs/skill-self-improvement.md:83-84`
- ただし最終報告では、これらを単なる「候補」で終えず、設計択一と推奨案を裁定パッケージとして提示する必要がある。`docs/dev-wave/core.md:72-76`

## Speculative

ユーザーが別画面で全文案を読んでいた可能性と、3要素要約だけを見ていた可能性はどちらも残る。いずれも資料で立証できないため、片方を事実扱いせず blocker とした。

## 総括

blocker は1件あり、「待ち条件作成」を承認済みと扱えるか確定していない。  
land は NO-GO を推奨する。  
ユーザーへ「条件24に待ち条件作成を含める／含めない」を明示的に再裁定してもらうべきである。  
再裁定後、pinを条件24だけへ狭め、受入・変異を実走してから記録する。