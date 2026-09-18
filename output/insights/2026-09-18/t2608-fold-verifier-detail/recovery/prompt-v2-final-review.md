単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2608-recovery-v2
必読事項の射影:
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2608-recovery-v2/CLAUDE.md 絶対規律 — 読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2608-recovery/HANDOFF.md — 読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2608-recovery-v2/docs/failures.md F266とF946 — 読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2608-recovery-v2/docs/dev-wave/core.md DW-STOPとoperations.md DW-O23 — 読めなければ即停止。

同じT-2608のland修復とユーザー指示による自己改善の焦点レビュー。対象固定HEAD=063a743d61dcc3707010fb714f677caccddcb167。編集しない。
一括merge9c0300993の親列main b2037abfa / 旧wave2b1015486 / author2975fcf6dをgitで確認し、tools/dev_waves/git_state.pyが選ぶ各親差分を全landed区間で追ってF266が解消したか独立監査する。
本体2fileは旧受入tip7a144e023(25134 passed/69 skipped)から不変。7a144e023のunit後付けmerge ceb258ff7はland rc26、今回の履歴へは含めない。
自己改善commit063a743d6のcore.md/operations.md/再発fragment/worklog差分を読む。同一目的の修復≠次wave、同じ要求の再試行不可≠修復不可、F266接続の明確化である。文書予算内へ縮約した既存安全義務(規律2、postcondition failure停止、rebase/force禁止、受入、同lockでfold)が保存されているか攻撃する。
前回相談は内容出力ありだが見出しが太字でF43未受理。その結論を採用済みとはしない。今回は実物を独立に再検証する。
read-only、pytest緑不要、実測は親。コード/docs/commit/受入/landに触れない。追加gate・一般化は提案しない。予算不足なら途中結論を以下protocolで出して終える。
出力プロトコル: 最初の行に、機械検収用の必須文字列「## 総括」をそのまま書く。太字への置換やfenced code内への埋込みは不可。前回はこの違反だけで結果が未受理になった。
## 総括
GO/NO-GO、must-fix件数、静的のみ・未実走。
## 所見
real/refuted、file:line、影響、最小修正。なければなし。
## 対応表
F266・F946各項のclosed/partial/regressedと証拠、旧受入との差分の限界。
