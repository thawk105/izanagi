## 所見 — 正しさと上流の品質

修理 hunk に **must-fix / should の所見はありません**。F と A を byte 単位で照合すると、差分は指定された read set 検査の 1 hunk だけです。[修理後の transaction.cc](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/review/A/cc/mocc/transaction.cc:1061) は裁定 R1 の位置に acquire 再読を置き、epoch・tid の不一致で既存の版不一致と同じ状態・計数を設定して abort し、`max_rset_` に `check` を使っています。既存の `#line` 値と `#if TRACE` 区間も不変です。これらを削ると、裁定どおりの修理または G2 の窓を閉じる根拠が崩れます。

lock 読みの後に版を再読するため、対象の publish がその間に入れば版の不一致で拒否できます。ただし、この論証は版が同じ値へ戻らない範囲と、一次資料 §2 の対象経路に限られます。[Tidword の定義](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/verbatim/ccbench-F/cc/mocc/include/tuple.hh:14) の有限幅による ABA まで解消する主張ではありません。未使用変数・shadow・型変換・整形について、静的検査で成立する CI 攻撃は見つかりませんでした。build とテストは依頼どおり実行していません。

## 所見 — 過剰・削除と commit message

- **should — 観測した G2 の説明が両側の窓を含意する。** [msg-X.txt](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/msg-X.txt:12) の “two transactions do this to each other's read sets … which we observed” は、両取引がこの割り込みを受けた事例を観測したように読めます。[切り分け §2・§5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-validation-fix/output/insights/2026-09-29/t2872-mocc-g2-split/README.md) が示す必要条件は片側の窓で、5 witness の片側で一致しています。放置すると上流への観測説明が事実を超えます。「この窓が片側の rw 辺で生じると G2 を許し得る」とし、5 件の内訳は直接一致 2 件・推論 3 件と短く限定してください。

- **should — “only adds a reason to abort” は変更全体には当てはまらない。** [msg-X.txt](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/msg-X.txt:20) と [修理後の transaction.cc](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/review/A/cc/mocc/transaction.cc:1076) を照合すると、abort 条件の追加に加え、`max_rset_` の入力も変わります。放置すると上流には commit TID に影響し得る変更が伝わりません。「既存の拒否条件は維持し、再読不一致を追加で拒否する。`max_rset_` は検査した版から計算する」と書けば正確です。全スケジュールの受理集合が厳密に部分集合になる、とまでは主張しないでください。

- **nit — “through the existing version-mismatch path” は実装上の同一経路ではない。** [msg-X.txt](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/msg-X.txt:17) に対し、[修理後の transaction.cc](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/review/A/cc/mocc/transaction.cc:1066) は別の分岐で同じ状態と計数を設定します。放置時の影響は上流への説明の精度だけです。“using the same abort state and analysis counter as the existing version-mismatch check” などに直してください。

2 行のコメント、比較用変数、`ADD_ANALYSIS` の計上は過剰とは判断しません。コメントは裁定の指定量で理由を述べ、変数は検査済みの `check` を保持し、計上は既存の版不一致との分類をそろえています。「Silo と同じ」は [Silo の検査](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/verbatim/ccbench-F/cc/silo/transaction.cc:453) と照らして `max_rset_` に検査済みの版を使う範囲なら正確です。

## 総括

**hunk は R1〜R3 に適合し、静的レビューで修理を止める欠陥は見つかりませんでした。** commit message の観測表現と変更範囲の説明は、上記 2 件を直すのが適切です。CI build・テストの通過は未確認です。