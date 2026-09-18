単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/brief.md (親 brief、検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-plan.md (段 2 plan、検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/proposed-edits.md (候補文言と byte 差。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1893.md (ユーザー裁定の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D227.md (予算原資の条件。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1798.md (P1 収容時の裁定。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/workers.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/core.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/operations.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/mutation.md (段 6 U 節 DW-M02 の正本。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/.claude/commands/dev-wave.md (入口、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/tools/check_docs.py (pin と予算の実装、不変。読めなければ即停止)

## 目的
これは自分たちの開発手順書 (dev-wave の docs) の docs-only 変更の設計レビューである。ユーザー裁定 D1893 で採った P2 (段 3・6 のレンズ 1 本を「過剰・削除」レンズに固定) と P6 (研究前進か実測欠陥の根拠が無い scope 外所見は起票せず記録のみ) を `docs/dev-wave/` へ収容する計画 (plan) と親 brief を、**レンズ A = 正しさ境界・整合**で点検する。plan を守らせるのではなく、欠陥を指摘するのが役目である。親 brief 自身も検査対象である。

## レンズ A の問い (正しさ境界・整合)
1. **安全義務の消失**: 削減原資 E3 / E4 / E6 / E7 は D227 の 3 条件 (同一読点・上位互換・単一正本化) を本当に満たすか。担い手節の逐語を並べ、削る文の要素で担い手に無いものを 1 つずつ挙げよ。特に E4 (DW-S06-B の列挙) と E7 (operations.md preamble) は、担い手が「入口」(L0) であることを根拠にしているが、入口の逐語がその要素を本当に含むか確かめよ。
2. **正しさゲートへの波及**: 変更が規律 2 (正しさゲートを緩めない)・変異義務 (DW-S04 の免除条件、DW-M01)・受理集合に触れていないか。P6 の「起票せず記録」が、正しさに関わる所見 (verifier・gate の欠陥) を黙らせる経路にならないか。「実測欠陥」の語が正しさ欠陥を含むと読めるか、読めなければ文言を提案せよ。
3. **pin と構造検査**: `tools/check_docs.py` の pin (reasoning pin、`CODEX_FIRST_REFERENCE_LITERALS`、`DEV_WAVE_LAND_HELPER` 系、D2/D4 構造 regex、層予算) と E1〜E7 の衝突を、該当する関数名・定数名を挙げて検証せよ。親の「触れない」主張を鵜呑みにしない。
4. **既存正本との二義化**: P2 の新文言と `DW-G05` 第 2 段落 (過剰実装の既存規範)、P6 の新文言と `docs/skill-self-improvement.md` routing 2 (裁定パッケージ) や `DW-G05` 第 1 段落 (nit/backlog) が二義化しないか。同じ判断を 2 箇所で違う条件で書いていないか。
5. **親の実測値とその一般化**: 層予算の残 bytes、pin の一覧、持ち越し 638 項などの実測値のうち、一般化が飛躍しているものを挙げよ。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。
- 所見は 1 件ずつ「A-n / 対象 / 主張 / 根拠 (file:line) / 放置時に成果物 (手順書の義務・受理集合) がどう変わるか / 推奨 (採用・条件付き・却下)」の形で書く。

## 出力形式
## 所見 (A-1 …)
## 削減原資の要素対照表
## 代替案 (あれば)
## 総括
