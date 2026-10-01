単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md (対象。commit e9a21bef5。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/docs/spool/failures/2026-10-01-t2853-r2-fig2c-1.md (対象。読めなければ即停止)
- /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/codex/s6-review-a.md と /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/codex/s6-review-b.md (前回の所見。読めなければ即停止)
- /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-common.txt と /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/request-md_4.txt (依頼と共通指示。読めなければ即停止)

## 焦点再レビュー

あなたは read-only のレビュー子である (書き込み可能な tmp は無い前提で静的に検査する)。前回の所見 A-01、B-01〜B-05 への修正 (commit 0b952aa74 → e9a21bef5、
`git -C /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c diff 0b952aa74 e9a21bef5` で読み取りだけ) が所見を閉じたかを判定する。
- 所見ごとに closed / partial / regressed / open の対応表を作り、根拠 (該当文) を添える。
- 修正で新たに書いた事実 (当時の規則の引用、依存の sha256 `aa168498…`、基準 main `5f9e8c549`、「0〜900 µs の 28 点」、原 read-heavy の 1000 µs が 10.275) は一次資料
  (共通指示の原文、`git -C <上の worktree> show 5f9e8c549:tools/plotting/plot_backoff.py` の sha256、R2 図の provenance の `dependencies`、`comparison.md`) と照合する。
- 修正による新しい誤り・過剰・削除漏れ (新所見) があれば、重大度 (must-fix / should-fix / nit) を付けて書く。

最後に `## 総括` 節を置き、GO / NO-GO を書く。予算が切迫したら途中結論をこの形式で書き終えること。委任 (spawn_agent 等) をしない。
