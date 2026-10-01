単独段 dispatch: stage=review; sandbox=read-only; parent=/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md (レビュー対象。commit 0b952aa74。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/docs/spool/failures/2026-10-01-t2853-r2-fig2c-1.md (failures fragment。レビュー対象。読めなければ即停止)
- /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/s1-brief.md (親の段 1 brief。これも攻撃対象。読めなければ即停止)
- /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-md_4.txt と /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-common.txt (依頼と共通指示。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-09-28/t2853-r2-fig8b/README.md (前例。必要な節だけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/docs/spool/failures/README.md (fragment の形式。読めなければ即停止)

## レンズ B — 過剰・誤読・削除

あなたは read-only の敵対レビュー子である。静的に検査する (書き込み可能な tmp は無い前提)。
依頼 (md_4) の「成果物」「所有」「scope 外」に照らして、README と fragment を攻撃する:
1. 依頼が求めた項目 (投入・Elapse・正しさ・表・図・原 attempt との比較・言えないこと、spool fragment) の欠落。
2. 過剰: 依頼の scope 外への踏み出し、主張の範囲を広げる表現 (再現性・性能・機序・採否の示唆、「同じ」「再現した」と読める文)、§0 の約束 (合成しない・数値の近さを再現精度として評価しない) に反する書き方。
   削ってよい節・重複・本題を埋もれさせる記述。
3. 誤読: 第三者 (論文の読者・再現パッケージの利用者) が誤解しうる記述 (R2 の地位、原図との関係、生成器と依存の版、wrapper の位置づけ、再現コマンドの実行可能性、費用の実測と見積りの区別)。
4. 計算の分け方の誤り (README §6・failures fragment) の記述が事実に忠実か、自己弁護に寄っていないか、恒久対応が実体を指すか (宣言だけの恒真な対応でないか)、型タグが適切か、fragment の形式 (README の規則) を満たすか。
5. brief の前提 (P1: 原 source commit から投げる、軽量版で段 2・3 を省く) に穴が無いか。

## 出力

所見ごとに ID・重大度 (must-fix / should-fix / nit)・根拠 (path と該当文)・修正案を表で書く。放置したとき成果物 (insight・台帳) の何がどう誤るかを 1 行添える。
最後に `## 総括` 節を置き、GO / NO-GO と理由を書く。予算が切迫したら途中結論をこの形式で書き終えること。委任 (spawn_agent 等) をしない。
