単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- 対象 commit: wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess の HEAD `56f8e97c0` (親 `51f896352`)。差分は `git diff 51f896352 56f8e97c0` (2 file)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/T-2273-origin.md — 依頼の逐語 (本題の実装だけ、仮想リスク向けの gate・検査・台帳・一般化は scope 外)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md — 段 4 裁定 (plan v2、計測の事前登録)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md — 段 1 前の profile。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s5-author-impl-out.md — 実装子の報告。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。出力は最終メッセージ本文に全文書け。

## レンズ B — 過剰・削除・効果

実装を守らず検査せよ。特に:
1. 過剰: 段 4 の plan v2 を超える追加 (helper・cache・test・parametrize・assert) と、削っても番人・等価性が保たれるもの。逆に plan v2 が要求したのに欠けているもの。
2. 効果: 変更後の `_scan_one` で、profile の律速 2 行 (正規表現 search・共通 literal の in) がどう変わるか。新たに増える費用 (`sre_parse.parse` を `_scan_one` 呼出しごとに行う費用、`find` の反復、軸 literal が大量に出現する text での窓 search の反復、`contains_by_literal_rel` の key 生成) が効果を食う条件。発行 child 1 回あたり `_scan_one` は約 13 走査 × 3 呼出し。
3. 計測設計: s4-ruling.md「計測の事前登録」(再 profile の 70 % 条件、隣接 3 対、land 区分 i/ii/iii、補助量、計算量) が、この実装の効果を判定するのに十分か・過剰か。
4. 実装の記録 (commit message の主張) が実装・test と食い違っていないか。

## 出力形式

見出し「## 所見」(各所見: 重大度 must-fix / should-fix / nit、file:line、根拠、放置すると成果物 (受入時間・land 判定・記録) がどう変わるか 1 行)「## 効果の見込み」「## 判定」(GO / 修正後 GO / NO-GO)「## 総括」。「## 総括」は 5 行以内。
