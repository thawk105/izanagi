単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s1-brief.md — 親の段 1 brief。**これ自身も検査対象。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s2-plan-out.md — 段 2 plan。**検査対象。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/verbatim/T-2273-origin.md、D2044-item15.md、D2068.md、D357.md — 依頼と既裁定の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md — 第 4 回診断。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md — 前回の隣接対の実受入 (§2 測定形、§5〜6 系列・走表・判定)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py — plan が引く行 (794〜1000、1036〜1230、1390〜1470、1899〜2000)。必要な範囲だけ grep / sed で引く。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/ (run-series.sh、run-measure.sh、t2825_ab_analyze.py、gate.conf) — 前回の系列投入 script と集計器 (Codex author 作、repo 外)。本 wave で改作して再利用する予定。

## 目的 (レンズ B: 過剰・削除と計測設計)

これは自分たちの受入 test 基盤の高速化 wave の段 3 敵対相談である。brief と plan を守る側に立つな。依頼は「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」「隣接対の実受入で効果を測ってから land」「性能主張は同時刻の対照で」。次を根拠付きで攻撃せよ。

1. **過剰:** plan の変更 (marker・lock・残骸処理・新 test 2 本・既存 test への assert 追加・変異 5 本) のうち、本題 (複製元を局所の写しへ) に不要な部分、より少ない行で等価にできる部分、既存の仕組み (`_T080SharedBases.get` の lock + marker 型) を再利用すれば消せる部分を挙げよ。逆に、削ると正しさの証拠 (受理集合不変の正例、変異の kill) が失われる部分は残せと言え。
2. **削除・局所修正の可否:** さらに単純な形 (例: 写しを 1 つの共有 base key として `get()` に載せる、builder の引数で複製元を渡す等) が等価に成立するか。
3. **計測設計:** 隣接対 (A = 測定時 local main の clean worktree、B = wave tip、T-2825 の形で A/B 3 対、D357) は依頼の「同時刻の対照」を満たすか。対の順序、投入門番、無効走の扱い、判定量 (shard-0 W_0 の対差・対率中央値) と閾値、補助量 (O_max・L) を事前登録として何を書くべきか。T-2825 の probe を改作する際に最小で変えるべき点 (job dir、台帳前提の warm 検査など) は何か。計算量 (受入 1 回 ≈ 0.25 node 時間、2 node 時間以上ならユーザー確認) の見積りは妥当か。
4. **研究前進の示し方:** brief の完了判定 (「land し、対差を記録」) は、5 分上限を満たさなかった場合にどう書くべきか (未達でも land すべきか、D357 の「変化なし」なら land しないか)。事前登録すべき land 条件を提案せよ。
5. **親自身の実測値とその一般化:** brief の数値・主張の出所を検算せよ。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` (番号付き。各所見に 重大度 must-fix / should / nit、根拠、最小是正)
- `## 事前登録の提案` (計測・land 条件)
- `## 総括` (3〜6 行。GO / 修正後 GO / NO-GO)
