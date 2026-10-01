単独段 dispatch: stage=review; sandbox=read-only; parent=/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md (レビュー対象。commit 0b952aa74。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/comparison.md (対照表。読めなければ即停止)
- /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/s1-brief.md (親の段 1 brief。これも攻撃対象。読めなければ即停止)
- /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001/tools/t2853_r2_fig2c_plot.py (repo 外の wrapper。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/tools/plotting/plot_b10_extended_backoff.py (生成器。読めなければ即停止)

## レンズ A — 一次資料との照合・正しさ境界

あなたは read-only の敵対レビュー子である。書き込み可能な tmp は無い前提で静的に検査し、必要な再計算は読み取りと手計算 (またはファイルを書かない python -c 等の読み取りだけの計算) で行う。
README の数値・判定・量化 (「すべて」「だけ」「一致」「単調」など) を、一次資料から独立に再計算・再照合する。親の記述を信じない。

一次資料:
- R2 の出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001/` (submit receipt、3 job root の completion.json / reservation.json / campaigns/*/runs/wal.jsonl / reports/*.dat、*.stderr の NQSV 会計)
- 原 attempt `/work/1/SFC/tanab/b10-backoff-grid-runs5/` (同じ構造)、原図の provenance `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json`
- R2 図の provenance `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/figures/fig2c_r2_b10_extended_backoff.provenance.json`
- 逐語ログ `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/verbatim/`

確かめること (最低限):
1. job ID・host・開始終了・Elapse・合計 (10,836 s、3.01 node 時間)・source commit・CCBench・凍結 digest・campaign id を一次資料と照合。
2. 正しさ: R2 と原 attempt の WAL の verify_done 行を数え、93/93 certified・anomaly 0・serializable を独立に確かめる。WAL に verify 失敗や commit 欠落が無いか。
3. 表: 少なくとも各 workload の 0 µs・最大点・900 µs について、WAL の反復値から平均と t 分布 95% CI 半幅 (df=4、t=2.7764451…) を再計算し、comparison.md と README §4 の最大点表と照合。README の「単調に下がる」主張を表の全行で確かめる。
4. wrapper が生成器の受理条件・レイアウト検査・provenance 検査を緩めていないか (差し替えた定数が README §5.2 の列挙どおりか、列挙外の差し替えが無いか、置換回数 assert の有無)。R2 図の provenance の input sha256 が実ファイルと一致するか。
5. §0 (投入前に commit 0221383cf で固定) の約束 (合成しない・再現精度として評価しない・結果にかかわらず報告・検査を外さない) を、後の節が破っていないか。
6. 原図 (`docs/paper-story/figures/fig2c_*`) が wave で変わっていないか (`git -C <wave worktree> diff 5f9e8c549..0b952aa74 --stat` など読み取りだけの git)。

## 出力

所見ごとに ID・重大度 (must-fix / should-fix / nit)・根拠 (path と値)・修正案を表で書く。数値の食い違いは「README の値 / 再計算値」を並べる。
最後に `## 総括` 節を置き、GO / NO-GO、照合した項目と結果 (一致した件数)、照合できなかった項目を書く。予算が切迫したら途中結論をこの形式で書き終えること。委任 (spawn_agent 等) をしない。
