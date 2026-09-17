単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/brief.md (親 brief、検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-plan.md (段 2 plan、検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/proposed-edits.md (候補文言と byte 差。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1893.md (ユーザー裁定の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1798.md (P1 収容時の裁定。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/origin-insight-excerpt.md (P2/P6 の原典と「なぜ止まらないか」。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/workers.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/core.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/operations.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/.claude/commands/dev-wave.md (入口、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/skill-self-improvement.md (routing の正本、不変。読めなければ即停止)

## 目的
これは自分たちの開発手順書 (dev-wave の docs) の docs-only 変更の設計レビューである。ユーザー裁定 D1893 で採った P2 (段 3・6 のレンズ 1 本を「過剰・削除」レンズに固定) と P6 (研究前進か実測欠陥の根拠が無い scope 外所見は起票せず記録のみ) を `docs/dev-wave/` へ収容する計画 (plan) と親 brief を、**レンズ B = 過剰・削除**で点検する。これは P2 が定めるレンズそのものを本 wave 自身に先行適用するものである。plan を守らせるのではなく、欠陥を指摘するのが役目である。親 brief 自身も検査対象である。

## レンズ B の問い (過剰・削除)
1. **実測欠陥への対応**: 各編集 (E1〜E7) は D1893 / 原典 insight が示す実測欠陥 (所見→T 起票の出口が無い、段 3/6 に削除方向のレンズが無い) に直接対応しているか。対応していない編集 (装飾・一般化・予算のためだけの変更) を挙げよ。削減原資の編集 (E3/E4/E6/E7) は「予算のため」だが、それ自体が過剰でないか (もっと少ない編集数で同じ bytes を捻出できるか)。
2. **削除・局所修正で済まないか**: P2 を「新しい語を足す」形でなく「既存の語を置き換える」形で収容できているか。3 本目のレンズにしていないか (Q1)。P6 を 1 文の置換で収容できているか (Q3)。もっと短い文言で同じ効力が出るなら提案せよ (byte 数付き)。
3. **恒真化・空回り**: 新文言は判定可能か。「研究前進か実測欠陥の根拠」は親が毎回「根拠あり」と書けば通ってしまわないか。原典 insight の A-2 (「何を進めるか」だけでは恒真化) と同型の穴があれば、判定可能にする最小の語を提案せよ (bytes 付き)。逆に、厳しすぎて正当な所見 (正しさ欠陥) まで記録止まりにする穴があれば挙げよ。
4. **scope の膨張**: brief と plan が、ユーザー引数「本題の 2 項反映だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」を守っているか。段 6 に review を入れる判断 (brief 分割方針) は過剰か、DW-C00 の「受理集合が変わる段では省かない」に照らして必要か。
5. **親の実測値とその一般化**: 「持ち越し 638 項」「製品行 +12,070」を P2/P6 の因果根拠として使っていないか (D1798 の A-9 と同じ注意)。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。
- 所見は 1 件ずつ「B-n / 対象 / 主張 / 根拠 (file:line) / 放置時に成果物 (手順書の義務・受理集合) がどう変わるか / 推奨 (採用・条件付き・却下)」の形で書く。

## 出力形式
## 所見 (B-1 …)
## より短い文言の提案 (bytes 付き)
## 総括
