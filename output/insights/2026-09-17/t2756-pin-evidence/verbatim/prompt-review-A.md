単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/README.md — 段 5 で親が書いた成果物 (再承認材料 3 点)。**これがレビュー対象**。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/runs.json — 親の checker 実走索引。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/trace0-gcc11.report.json — checker の生 report (GCC 11.4)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/trace0-clang14.stderr.txt — clang 14 の stderr。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/candidate-commits.txt — 候補 4 commit の fuller log。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/candidate-diff.txt — 祖先性・raw diff・diffstat・trace.hh blob の親実測。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/github-ls-remote.txt — GitHub の ref 一覧 (2026-09-17)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/s4-adjudication.md — 段 4 の親裁定 (段 3 所見の採否)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/consult-A.md — 段 3 レンズ A の所見 (あなたの前段)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D297.md — 検査の保証名と設計理由。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D1603.md — 材料 3 点の定義。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D2114.md — 起点裁定。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_trace0_preprocess_identity.py — checker 本体。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/orchestrator/campaign/source_digest.py — `_cpp_normalize` 等。読めなければ即停止。

## 依頼 (段 6 敵対レビュー A: 正しさ境界 — 材料 (1)(2) の逐語が事実と保証の範囲に収まっているか)

あなたは read-only の敵対レビュー子である。段 5 の成果物 README (材料 1〜3、特に §0〜§3) を、**事実との一致**と**保証の言い過ぎ / 言い足りなさ**の観点で攻撃せよ。pytest・checker の再実走は不要 (親が実走済み、生 report は verbatim)。段 3 レンズ A の所見が README に反映されているか、反映が誤っていないかも検査せよ。

攻撃対象:
1. README §2 の候補表・4 commit 表・来歴の 3 箇条が verbatim (candidate-commits / candidate-diff / github-ls-remote) と一致するか。数値 (+141、+31、+2 −1、+111、+7 −9)、日付、trailer の要約、blob `570e35e3…`、GitHub 側の branch 名。誤りは行を名指しして訂正案を書け。
2. README §3.1 の表と箇条が report JSON / runs.json / stderr と一致するか (rc、schema、context 数、`include_line_count`、policy、define map 4 種の列挙、digest 2 種、compiler version 文字列、sha256 の先頭)。version-body digest の記述 (`b713e6ab…` が policy と一致) の書き方が admission toolchain の同一性を示唆していないか。
3. README §3.2 の保証範囲の逐語が、checker docstring・D297・D780・D774・D723・T-1584 §6 の限界を落としていないか、逆に checker が保証しないことを保証するように読めないか。「必要条件の一つ」の位置づけ、D986 との関係の記述 (「全面閉塞を主張しない」「単純形は T-1584 が修理」「D774 で据え置き」) が事実か — `docs/decisions.md` の D774 / D986 見出しと `docs/phase3.md` の [T-1644] 行を `grep` で現物確認せよ。
4. README §3.2 の分岐被覆表 (指令ごとの出現数と両枝検査の有無) を候補 blob (`git -C <worktree>/external/ccbench show e9e477ca1b55348ab4530de0b1cf663ce4555290:cc/mocc/transaction.cc`) で検算せよ。
5. README §3.3 の clang 原因説明が verbatim の probe file (clang-probe-*.txt / gcc-probe-*.txt) と一致するか。「候補の拒否ではない」と「clang での同一性は未確認」の両方が書かれているか。
6. README §0 / §1 / §5 が「前進可能」「承認」「合格したので」と読める文を含まないか。含むなら行を名指しせよ。逆に、判断材料として必要なのに欠けている事実 (例: 候補が local only である帰結、checker report が proof chain 外) があれば挙げよ。
7. README 全体で、親の推測・一般化が事実の顔をしている箇所 (例: 「orchestrator/campaign に record の head_sha を読む consumer は無い」「d706650 の silo 2 件が保持されている先例」) を現物で検算せよ。検算できないものは「未検証」と書け。

各所見は「所見 / 根拠 (README の節・行、verbatim 名、file:line) / 正しさ境界 or 整合・実効性 / must-fix or nit / 是正案 (README のどの文をどう書き換えるか)」の形で書け。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: must-fix 件数、nit 件数、事実誤りの件数、段 3 レンズ A の未反映件数、「前進可能」と読める文の有無)。続けて上の 1〜7 を見出しにして書く。
