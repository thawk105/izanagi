単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md — レビュー対象の統制稿 (新規、未 commit)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/README.md — 「results 系列」節の表に足した 2026-09-18 の 1 行 (レビュー対象)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/README-results-series.md — results 系列の規則 (逐語)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/parent-brief.md — 親の段 1 brief と実測要点 (親自身も検査対象)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/t1998-balanced-stock-inline-preregistration.md — 事前登録 v1 (一次資料)。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json — 権威 bytes。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/reservation.json — 権威 bytes。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/campaign.lock — 権威 bytes。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl — campaign WAL (40 record、JSONL)。読めなければ即停止。
- /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740.submit.jsonl — 投入受領証。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2589-consumer-repair/decision-final.json — consumer の判定 JSON (2026-09-14)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/wal-table-parent-derived.txt — 親が WAL から導出した表 (親の導出も検査対象)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/wal-two-arms-full-records.txt — 登録 2 arm の WAL 5 record 全文 (親の抽出)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md — 投入・回収・1 回目の解析。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md — consumer 是正と認証。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/output/insights/2026-09-15/t1998-landed-main-recheck/README.md — 着地後 main での再解析。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/orchestrator/campaign/t1998_stock_inline_pair.py — consumer (定数と判定規則)。読めなければ即停止。

## 依頼 (レンズ A: 数値・逐語・識別子の照合)

あなたは read-only の敵対レビュー子である。書き込み可能な tmp は無いので pytest 緑は要求しない。静的検査だけでよい。
テストの実走は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

対象は docs のみの wave で、成果物は「[T-1998] balanced stock-inline 対の単独 results 稿」1 本と README の表 1 行である。
この稿は append-only の凍結物で、着地後は in-place で直せない。**着地前に、稿に書かれた数値・識別子・逐語引用・
field 名・日付・件数が一次資料の現物と一致するかを攻撃せよ。** 稿を守らず、検査せよ。親の brief と親が導出した表も検査対象である。

攻撃観点 (すべて現物で確かめる):
1. 稿の表 (§1.1〜§1.4、§2.1〜§2.5、§5.1、§5.4) の全数値・全 sha256・全 field 名を、result.json / reservation.json /
   campaign.lock / wal.jsonl / submit.jsonl / decision-final.json の現物と突き合わせる。1 桁でも違えば must-fix。
2. 稿の逐語引用 (事前登録 §2 / §4 / §6 / §9、2026-09-14 README §2.2「受理集合は広がる」、README の results 系列規則) が
   原文と一致するか。言い換えを「逐語」と称していないか。
3. 稿が「一致した」「再計算で一致」と書く命題 (median、cv = 標本標準偏差/平均、ratio、improvement_percent、lock/WAL sha、
   事前登録 blob sha、a551cdd3 の blob sha) を、自分でも WAL の tps 配列から再計算して確かめる。
4. 稿の §2.3 が書く「検査条件の argv は成果物に無い」「legacy 条件 1 回ずつ」「verify_done → bench_done の順」を WAL の
   ts と payload で確かめる。
5. 稿の §2.4 の 8 点表 (variant id、BACK_OFF、BACKOFF_FIXED、src_token 前置、5 標本、median、cv 4 桁、commits/aborts) を
   WAL の記載順と現物で確かめる。行 2 の source_bytes_sha256 が事前登録 §4.2 の「正しくない」値と同じ bytes かも確かめる。
6. 稿の §2.5 の時系列 (UTC/JST の換算、Elapse 712、job 開始・終了) を qstat / job stdout 末尾 / WAL ts / receipt で確かめる。
   (job stdout は /work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced.stdout)
7. 稿の §5.1 の sha256 表 (file 名・bytes 数・record 数) を現物で確かめる (sha256sum を自分で計算してよい)。
8. 稿の件数の主張 (限定 20 件、欠落 10 件、23 file、40 record、63 blob、insight README 5 本) を数え直す。
9. README の表 1 行の数値・件数・語が稿と整合するか。
10. 稿が「一次資料からのみ」と言いながら、実は横断稿 (docs/paper-story/results/2026-09-16-b7-three-run-materials.md) や
    版 (docs/paper-story/2026-09-17.md) からしか取れない命題を書いていないか (出所の無い数値・命題を探す)。

出力形式 (Markdown、日本語):
- `## 所見` — 各所見に `must-fix` / `should-fix` / `nit` の重さ、稿の節・行の位置、現物の値、稿の値、根拠 (file と field)。
  所見が無い観点は「観点 N: 不一致なし (確かめた対象を列挙)」と書く。
- `## 親の brief への異議` — 親の brief / 導出表で誤っている点 (無ければ「なし」と根拠)。
- `## 総括` — must-fix の件数、should-fix の件数、nit の件数、着地を止めるべきかの判定 (止める / 止めない) と 1 行の理由。
