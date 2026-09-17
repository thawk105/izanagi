単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/parent-brief.md — 親 brief (検査対象。研究前進・scope・確定済み裁定・不変条件・provisional 裁定 P1〜P4)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/plan-out.md — 段 2 plan (検査対象)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/user-utterances.md — 本 wave のユーザー発話 3 件の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/worklog-2026-07-27-25.md — 2026-07-27 (25) ユーザー裁定 8 件の原文。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/phase3-2026-07-27-revision.md — phase3.md の 2026-07-27 / 07-31 / 08-01 改訂節。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/paper-story-2026-09-17-excerpts.md — 最新論文ストーリーの Silo 固定 / C-1 の 5 箇所。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/roadmap-excerpts.md — roadmap 層1・層2 (b1/b2)・§8・§9。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1360.md — 段 7 cross-protocol に残るのは実装。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D579.md — mocc は変異探索面にしない。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/roadmap-history-README.md — roadmap 改訂セレモニーの正本。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/paper-story/2026-09-17.md — 最新論文ストーリー全文 (§3 主張の階層、§6 言えること/言えないこと、§8 A/B/C 群)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/related-work/literature-map/izanagi_literature_map.md — 関連研究地図 (方向 B の候補の有無)。読めなければ即停止。

## 依頼 (レンズ A = 論文価値・主張の線引き・研究の順序)

あなたは親 brief と段 2 plan を**守らず検査する**敵対相談役である。親 brief 自身も検査対象である。read-only で、pytest 実走は不要 (静的検査でよい)。

ユーザーの動機は「論文のパンチが弱い」であり、提案は「(A) クロスプロトコル対応を可能にしておく」「(B) クロスプロトコルの道具として CCBench 側に近年の新しい手法を追加する」の 2 方向である。親は P1 で A→B の順序を provisional に裁定した。次を攻撃せよ:

1. **パンチは本当に強まるか (P3):** silo に加えて mocc で certified な variant を 1 件合成し、stock との比較 1 対を取ったとき、paper-story §3 の主張階層 (評価器 / システム / LLM 固有 / 無人自律) のどの主張が、どの文面で強まるか。逆に「10 protocol から選ぶ」「descriptor 駆動の因果」「一般性」のどれが**依然として言えない**か。§6「言えないこと」・§7 過大主張チェックリストと照合し、silo+mocc で新たに言える文を最大 3 文、言えない文を最大 3 文、根拠 (paper-story の行) つきで書け。**もし「パンチは強まらない・別の投資の方が強い」と判断するなら、その代替 (例: A-1 本走の認可、B-1 既知軸最良の超越、B-5 LLM 固有性の対照) を根拠つきで挙げよ。**
2. **順序 A→B (P1) の攻撃:** B (CCBench へ近年手法を追加) を先にする合理性はあるか。CCBench は第三者 submodule で新 protocol の追加は C++ 実装 + trace-hook + 証明面 + 較正を要する。literature map に候補は載っているか (載っていなければ「候補 0 件」と書く)。B の成果が論文の何に効くか (道具の追加は主張か、それとも前提整備か)。A の道具立てが protocol 汎用になる前に B を始めたときの二重費用を具体的に挙げよ。
3. **解除の射程:** 親は「2026-07-27 裁定 (1) の『当面』を終える」を「合成対象 protocol の拡大 (mocc を 2 例目) と C-1 を必要条件 B 群へ」に限定し、裁定 (2) (8b selector 優先度下げ) は据え置くとした。この線引きは整合するか。「複数プロトコルから選ばせる問題設定」(selector) と「複数プロトコルで合成できる」(合成対象の拡大) を分ける言い方は paper-story の記述と矛盾しないか。
4. **roadmap §9 E の順序 (P4):** 「以上の後に cross-protocol と最適化移植 (b2) を判断する」の判断を今行うことが、roadmap-history README の改訂セレモニー (自律改訂 = 版凍結 + decisions、大改訂 = ユーザー確認、協議改訂 = セレモニー不要) のどれに当たるか。2026-07-27 改訂が「roadmap 本体の改訂は本裁定に含まれない」とした先例と同じ扱いで足りるか。
5. **親の実測値と一般化:** 親 brief の事実記述に、一次資料で裏付けのない一般化 (例:「基盤は較正まで進んでいる」「性能比較 0 件」「D579 で変異探索面外」) が無いか。段 2 plan の裏取り結果と突き合わせ、食い違いを列挙せよ。
6. **段 4 裁定案:** 上を踏まえ、親が段 4 で採るべき裁定を「採用 / 修正して採用 / 却下」で P1〜P4 ごとに書き、修正なら修正文を書け。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: 所見の件数 (real / refuted の内訳)、P1〜P4 の採否、パンチが強まるかの一言)。続けて上の 1〜6 を見出しにして書く。各所見は「所見 → 根拠 (file:line) → 影響 (放置時に裁定パッケージ・論文の何が変わるか) → 是正案」の 4 項で書く。
