単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results

## 必読事項の射影

これは自分たちの論文材料 (統制稿) の検算レビューである。次の絶対パスだけを読む。**この射影に挙げた file が
読めなければ即停止し、その旨を出力に書く。** 停止規則の射程はこの射影 file に限る — 自分で探した path が
不在でも、それは停止理由にしない。差分は commit 前の作業ツリー (untracked の新 file 1 本 + README の 1 行追加)
であり、親が起草した。親は原成果物 3 件の SHA-256 実計算と、`.dat` からの 5 反復平均・変動係数の再計算を
済ませている。

**レビュー対象 (これが本題)**

1. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`
2. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/README.md` の
   「results 系列（`results/` サブディレクトリ）」節の表 (2026-09-16 の `b10-static-tail-not-observed` の行が今回の追加)

**照合に使う一次資料 (repo 外、read-only で読む)**

3. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.json`
4. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.dat`
5. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal-complete.json`
6. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260915T061814Z-545445-write-heavy/completion.json`
7. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260915T061814Z-545445-write-heavy/qstat-f.stdout`
8. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260915T061814Z-545445-write-heavy/env/ccbench-worktree.json`
9. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260915T061814Z-545445.submit.jsonl`

**照合に使う一次資料 (repo 内)**

10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/b10-backoff-static-tail-preregistration.md`
    (§3、§4.1〜§4.7、§7 を主に使う)
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/output/insights/2026-09-16/b10-tail-formal-submit/README.md`
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/output/insights/2026-09-15/t2266-tail-band/README.md`
13. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/output/insights/2026-09-16/t2647-b10-tail-downstream.md`

## レンズ

**逐語と数値の検算。** 稿に書いてある値・field 名・JSON path・引用・SHA-256 が、一次資料の現物と
**1 つずつ一致するか**だけを点検する。主張の過大さや限定の欠落は別のレビュー子が担当する。

## やること

1. **稿の §1〜§4 に現れるすべての数値**を一次資料で検算する。集団 verdict、workload の state、18 区間の
   `qhat` / `qL` / `qU` / `L` / `U` / `U_flat` (小数第 4 位)、24 cell の 5 反復平均 (throughput は小数第 1 位、
   abort 率は小数第 6 位)、変動係数 (小数第 2 位、%)、生標本 (24 cell × 5 = 120 の throughput と 120 組の
   aborts / commits)、格子と raw 値、測定順と seed、job id、開始時刻 (JST)、ホスト、所要秒、identity の各 digest、
   正しさ記録の件数、`perf_bin_sha256` の相異数、事前登録 commit・blob・spec の SHA-256。
   **一致しないものを名指しする。** `L` が `1 − 2^qU` と一致するかも確かめる。
2. **field 名と JSON path が実在するか**を確かめる。稿が「〜という field が記録している」と書いている箇所
   (例: `campaigns[].identity.correctness_flags`、`completion.scheduler.job_start_epoch`、`points[].correctness[].payload.certified`、
   `source_measurement`、`confirmed_nonmonotonicity`、`upward_wiggle`) は、その field が現物にあるか。
   無い field を根拠にしている箇所があれば名指しする。
3. **SHA-256 を自分で再計算**して、稿の §1.1・§4.1・§4.3 の値と突き合わせる (repo 外 3 件、repo 内 4 件)。
4. **引用が逐語か**を確かめる。稿が事前登録の文言を鉤括弧で引いている箇所 (§4.5 の固定表現、§4.4 の
   `U_flat` の説明、§3 の throughput 併記要求) は、現物と 1 文字ずつ一致するか。言い換えているのに引用の形に
   している箇所があれば名指しする。
5. **「資料がこう書いている」という帰属が正しいか。** 稿は出所を分けている (例: ホストは `qstat-f.stdout`、
   `freeze_trees_sha256` は job root の `completion.json`、再導出の byte 一致は insight 11、探索走 argv の未保存は
   同 insight §3.4)。**帰属が逆になっている箇所、混ざっている箇所を探す。**
6. **入口 README の 1 行**の数値・稿名・列の内容が稿の本文と整合するか。特に「限定 14 件」「24 cell」
   「性能 120 rep・正しさ 120 記録」が本文の実数と合うか**数えて**確かめる。
7. **桁区切り・丸め・符号**の誤りを探す。負号が U+2212 (−) で統一されているか、百分率の丸めが揃っているか。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物の bytes を変える案を出さない。
- 数値を版 (`docs/paper-story/2026-09-14.md`) や insight の表から取らない。**数値の出所は原成果物 (3〜9) だけとする。**
  insight 11〜13 は帰属と文言の照合にだけ使う。
- 所見が無いなら「無い」と根拠つきで書く。検算したことを書かずに「問題なし」とだけ返さない。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物 (統制稿・入口の表・下流の執筆) の値・受理集合・参照がどう変わるか**を 1 行で書く。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 数値の検算
## field 名と JSON path
## SHA-256 の再計算
## 引用の逐語性
## 出所の帰属
## 入口 README の 1 行
## 総括
