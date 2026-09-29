単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md — 段 2 plan (攻撃対象)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s1-brief.md — 親の段 1 brief (これも攻撃対象。(P1)〜(P7) は親の provisional 裁定)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/ の T-2273-origin.md・D512-D513.md・D350-D351.md・F264.md — 依頼と既裁定・失敗型の逐語。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md、pin-closure.md — 親の実測と pin 閉包。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py (417〜700 行) と orchestrator/tests/test_s8b_holdout_freeze.py (380〜1200 行)。必要な範囲だけ引く。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う。python の対話実行もできない前提で、論証は読みで行え)。予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。

## レンズ A — 正しさ境界・等価性・既裁定との整合・実効性

plan を守らず検査せよ。親 brief 自身も検査対象である。特に:
1. 局所化 search が `compiled.search(text)` の真偽と一致しない反例を構成せよ。窓の左右端 (off-by-one)、`endpos` による切り詰めで一致が変わる形、重なる出現、literal が alternative 内の異なる offset に現れる場合、`.` が改行に一致しない点、`getwidth()` の戻り値 (Python 3.10 の `sre_parse`、MAXREPEAT、最小幅と最大幅)、helper が非 None を返すのに anchor・lookaround 等が含まれうる文法の穴。helper (`_derive_required_literal`) の現行の受理文法を実際に読んで、「全 match が L を含み長さ ≤ W」の前提がどの行で保証されるか / されないかを示せ。
2. D512 (canonical bytes 不変・読取経路と例外契約不変・自作 parser 禁止・memo は call 内) と D513 (発火回数の番人、knob 禁止、三段分離) と D350 (実際に compile する式から導出) に plan が違反していないか。`getwidth()` の利用は「自作 parser」に当たるか。
3. 既存の番人 test の改訂案が番人を弱めていないか (prefilter を戻す変異・memo を外す変異・局所化を外す変異が、改訂後も単一理由で赤になるか)。F264 (多軸が単軸の欠陥を隠す) の再発がないか。
4. 変異候補の単一理由性・等価変異の有無。
5. 親の実測値 (profile) の読みとその一般化に誤りがないか (例: 50 Hz sample の行帰属、13 回という走査回数の見込み、fixture と実 repo の違い)。

## 出力形式

見出し「## 反例と正しさの所見」「## 既裁定との整合」「## 番人と変異」「## 親の実測の読み」「## 判定」(GO / 修正後 GO / NO-GO と理由)「## 総括」。各所見は file:line と「放置すると report・受理集合がどう変わるか」を 1 行で付けよ。「## 総括」は 5 行以内。
