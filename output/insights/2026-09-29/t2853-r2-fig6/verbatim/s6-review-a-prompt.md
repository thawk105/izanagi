単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md (レビュー対象の本体。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/verbatim/ 配下の全 file (一次資料の写し。読めなければ即停止)
- /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2853r2-20260929a/ (R2 の測定原本: receipts/、jobs/rr5・jobs/rr50 の scheduler/job.stdout・job.stderr・compute-result.json。読めなければ即停止)
- /work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/ (collect 出力・図・対照表・wrapper・README。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md (原 attempt の結果稿。読めなければ即停止)

あなたは izanagi の dev-wave 段 6 の敵対レビュー子 (read-only) である。対象は wave branch の commit `75749a951` (insight・phase3 の 1 行・worklog fragment) と、repo 外の wrapper `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/tools/t2853_r2_fig6_plot.py`。
書込可能な tmp は無いので静的検査でよい。テストの実走は親が行う。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## レンズ A — 一次資料との照合・正しさ境界

1. insight の数値・識別子 (request ID・host・時刻・Elapse・node 時間の和・effects・median・mean・CI 半幅・abort rate・sha256・src_token・protocol_sha256・pin・source commit) を一次資料 (certification.json・raw-manifest・receipts・job.stderr の会計・job.stdout・対照表・provenance) と照合し、食い違いを全件挙げよ。派生値 (合計・× 5 node・node 時間・「すべて」「だけ」の量化) は原データから再計算せよ。
2. 規律 1 (検証は trace 有効 build、計測は trace 無効 build の別走) と規律 2 (anomaly があれば即 reject、検査を緩めない) が R2 で守られたことを一次資料で確かめよ。job.stdout の verify 行で anomaly が 0 でない行が無いか。
3. wrapper が生成器の検査を緩めていないか (生成器の関数・定数の差し替え、monkeypatch、hash を与えることで他の検査を飛ばす経路)。wrapper が生成器に渡すのは expected_hashes だけか。
4. insight §0 (投入前 commit `a901d51e7`) の約束 (合成しない・原 attempt 不変・結果にかかわらず報告・図の扱い) と、結果後の本文が矛盾しないか。原 attempt の tracked 成果物 (`output/insights/2026-09-07_t2364-paper-story-a2-certification/`) と fig6 が変わっていないか (`git diff 035fc11fa..75749a951 --stat` で確認)。
5. 費用 (§6) の書き方が、見積りと実消費を混ぜていないか。ユーザーに示した見積りを超えた事実が隠れていないか。

## 出力形式

所見ごとに `ID / 重大度 (must-fix・should-fix・nit) / 場所 (file と節) / 何が一次資料と食い違うか / 根拠 (一次資料の path と値) / 直し方` を書く。最後に GO / NO-GO と `## 総括` 節 (3 行以内) を置く。
