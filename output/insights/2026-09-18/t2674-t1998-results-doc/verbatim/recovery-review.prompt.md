単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex
必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/HANDOFF.md — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/CLAUDE.md — 絶対規律のみ。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/projection/D1874.md — 読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/projection/D1993.md — 読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/projection/D2044-item3.md — 読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/projection/D2120-item15.md — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/docs/paper-story/README.md — results系列。読めなければ即停止

T-2674の旧tip e3f4d277ff11471adf79a1b01ebfc637106260fbからのdocs成果回収を独立監査してください。親briefも攻撃対象。実装/編集/commitは禁止。書込可能tmpがないため静的検査だけでよく、pytest緑を要求しない。予算が尽きそうなら必ず途中結論を出力形式どおり書いて終える。

対象はこのworktreeの docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md、README追加行、output/insights/2026-09-18/t2674-t1998-results-doc/、docs/spool内の同wave fragment。旧レビュー2本・焦点再レビューはinsight/verbatimにある。既存must-fix8の閉鎖とef74d66c6による残partial修正を確かめる。親は旧受入の成功未証明記述を訂正する予定なので、その指摘は既知として区別する。

原典は稿§5が指すrepo外root、consumer decision-final.json、repo内事前登録、測定commit a551cdd3014708993475108f014aacbf32c21137のblob。必要な原典を実際に読み、値・hash・記録範囲・限定を検算する。全生ログを出力しない。絶対規律2/7を緩めず、現行差だけで過去を無効化しない。F1型の一次資料と転写/派生値の不一致、誇大な量化、資料にない保証、consumerとproducer判定の混同、A-1推定量との混同、B-7昇格を検査。過剰な追加gateや台帳の提案は不要。

旧最終受入の /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/old-final-6-3.junit.xml は2失敗のtestcaseだけを抽出して読む。旧rc70を成功扱いしない。実装差分0とt1259 setup timeoutとの帰属についても静的に検査する。

出力: ## 所見 (must-fix/should-fix/nit、file:line・原典・成果への影響、real/refuted)、## 対応表 (旧findingのclosed/partial/regressed)、## 親briefへの異議、## 総括 (着地阻害の有無と未検証範囲)。凍結稿の誤りなら系列規則を守れる最小是正を提案し、無断in-place修正を要求しない。
