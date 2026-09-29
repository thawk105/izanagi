単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- 対象 commit: wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess の HEAD `56f8e97c0` (親 `51f896352`)。差分は `git diff 51f896352 56f8e97c0` (2 file: orchestrator/campaign/s8b_holdout_freeze.py、orchestrator/tests/test_s8b_holdout_freeze.py)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md — 段 4 裁定 (plan v2・変異 M1〜M6 の登録)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/D512-D513.md、D350-D351.md、F264.md — 既裁定・失敗型の逐語。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s5-author-impl-out.md — 実装子の報告 (自己申告であり検査対象)。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。出力は最終メッセージ本文に全文書け。

## レンズ A — 正しさ境界・等価性・既裁定との整合

実装を守らず検査せよ。特に:
1. `_search_localized` と `_scan_one` の変更が `compiled.search(text)` の真偽・report の canonical bytes を変える反例 (窓の端、重なり、`getwidth()` の値、`sre_parse.parse` と `re.compile` の flag・解釈の差、str subclass の text・非 exact str の式、`_derive_required_literal` が None の軸、共通 literal が None で軸 literal だけ非 None になる経路の有無、例外の型・文言の変化、`sre_parse` の import が Python 3.9 / 3.10 / 3.11+ で起こす差)。
2. `contains_by_literal_rel` の cache が `_ScanMemo` の identity 束縛・内容変化拒否の後でだけ再利用されるか。memo が異なる texts object を持つとき・memo なしのときに cache が漏れないか。D512 (memo は 1 回の search_repository に閉じる) に反しないか。
3. test が恒真になっていないか (F264 型の多軸 mask、spy が機構を通らない、期待値を実装から導いて同義反復になる)。変異 M1〜M6 が登録した番人で単一理由で赤になるという実装子の申告の妥当性。
4. 既存の番人の改訂 (数える単位の移動) が番人を弱めていないか — prefilter を戻す変異・memo を外す変異・局所化を外す変異がそれぞれ殺されるか。
5. ソースと test に軸 key と具体値の連続 literal (自己汚染) が無いか。

## 出力形式

見出し「## 所見」(各所見: 重大度 must-fix / should-fix / nit、file:line、反例または根拠、放置すると report・受理集合がどう変わるか 1 行)「## 変異と番人」「## 判定」(GO / 修正後 GO / NO-GO)「## 総括」。「## 総括」は 5 行以内。
