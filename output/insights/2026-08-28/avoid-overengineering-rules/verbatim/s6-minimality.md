## 総括

結論は `real` 3件です。共通 dispatcher からの到達性と Claude/Codex next-tasks の意味一致は確認できました。一方、4差分に共通する判断文には、最小修正を逆に排除しうる条件、主目的に必要な機能を候補外にする欠落、自己申告を止めきれない実証条件があります。

### F1 [P1] 局所修正まで「局所修正では足りないこと」を要求している

対象文は、追加実装・追加防壁を候補にする条件として「既存機構の再利用・局所修正では足りないこと」を課しています。[repo差分](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s5-repo.patch:24)、[Claude next-tasks](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s5-personal-claude.patch:7)、[Codex next-tasks](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s5-personal-codex.patch:7)

しかし局所修正自体も通常は「追加実装」です。既存関数への条件分岐追加で欠陥を直せる場合、その候補は「局所修正で足りる」ため文面上の必要条件を満たしません。意図した最小案を落とし、広い仕組みだけを検討対象にする逆転が起きます。

- 成果物影響: next-tasks が最小修正を候補外にし、dev-wave が正当な局所 fix を must-fix にできず、rulings がその案を不採用推奨にできます。
- 判定: 「追加実装」が局所的なコード、テスト、文書変更を含むなら real。これらを含まないという既存の一意な定義が全入口にあれば refuted ですが、射影資料にはありません。
- より小さい代案: 「既存機構の再利用・局所修正で足りる場合はそれを選ぶ。それより広い追加は、足りないことを示せる場合だけ」と二段に言い換えるだけで足ります。

### F2 [P1] 許可理由が欠陥と受入要件だけで、現在の主目的が抜けている

追加を許す目的が「実在する正しさ欠陥の解消」または「現在の受入要件の充足」に限定されています。一方、既存 rulings は主目的である CC 自動合成との距離も推奨根拠にする契約です。[repo差分](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s5-repo.patch:8)

未実装の中核機能は、既存動作の正しさ欠陥でも、まだ定義されていない受入要件でもありません。また「追加手段そのもの」の明示要求ではなく、上位目的だけが既裁定である場合は例外にも入りません。

- 成果物影響: CC 自動合成の主経路に必要な新機能や、既裁定済み目的を前進させる実装が next-tasks から脱落し、rulings では不採用推奨になりえます。これは母集合を過剰案以外にも狭めます。
- 判定: 現在の目的に必要だが、欠陥修正、現受入、具体的手段の明示要求のどれでもない候補が1件でもあれば real。全候補が必ず三分類のどれかになる契約があれば refuted です。
- より小さい代案: 許可理由へ「現在の目的の達成」を一語句追加し、「現在の目的の達成、実在する正しさ欠陥の解消、または現在の受入要件の充足」とします。

### F3 [P2] 「示せる」だけでは自己申告を排除できない

段4裁定では「追加必要性は自己申告でなく確認する」と採用しています。[s4-adjudication.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s4-adjudication.md:6) しかし実装文は、対象機構と不足内容を挙げて「示せる」ことしか要求していません。候補作成者が未確認の不足を文章化するだけでも形式上通ります。

- 成果物影響: 仮想リスクを具体的な機構名で言い換えただけの framework、gate、検査を除外できず、今回の規則が候補の説明量だけを増やして採否を変えない可能性があります。
- 判定: 実在資料や実測なしの説明だけで候補が通るなら real。四つの入口すべてに、この条件へ適用される確認義務が別途明記されているなら refuted です。
- より小さい代案: 「示せる」を「既存資料または実測で確認できる」に置換します。新しい checker は不要です。

## 到達性と重複の確認

- dev-wave は共通 dispatcher から確実に到達します。Claude dispatcher は段1、段4、段6で `DW-G05` を読む契約です。[current-claude-dev-wave.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-dev-wave.md:65) Codex 側も同 dispatcher を全文読み、その段・条件直前に参照節を読み直します。[current-codex-dev-wave.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-codex-dev-wave.md:17) Codex Skill への重複追記は不要です。
- rulings も到達します。Codex Skill は `.claude/commands/rulings.md` を全文読み、そのまま実行する契約です。[current-codex-rulings.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-codex-rulings.md:12)
- Claude/Codex next-tasks の追加文は同一で、配置も双方の選定規則内です。入口間の意味差はありません。ただし F1からF3も同じ意味で共有されています。
- rulings の「全件索引した上で」は既存の全件索引契約と表面的には重なりますが、除外基準を収集ではなく推奨だけへ適用する境界を明示するため、行動を変えない同義反復とは判定しません。
- 新しい checker、台帳、節、予算増を必要とする修正はありません。read-only レビューのため検査は実行していません。