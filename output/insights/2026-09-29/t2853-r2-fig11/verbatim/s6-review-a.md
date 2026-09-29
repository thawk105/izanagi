## 判定

**NO-GO。** 現在の数値は一次資料と一致しますが、図の再実行時に R2 入力の固定 hash が受理条件として働きません。

## 所見

**A-F1 — must-fix：R2 の hash 検査が自己照合になっている。** wrapper は入力ファイルから計算した SHA-256 を、その同じ入力の期待値として生成器へ渡します（[wrapper:61](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/tools/t2853_r2_fig11_plot.py:61)、[wrapper:130](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/tools/t2853_r2_fig11_plot.py:130)）。これにより生成器の固定 hash 表による検査は使われません（[生成器:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/tools/plotting/plot_a2_certification.py:129)）。insight は自己計算値であることを明記していますが、同時に「測定値の受理条件は差し替えていない」と記します（[README:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-29/t2853-r2-fig11/README.md:140)）。**放置した場合：** certification と manifest が後から整合的に変わっても再描画が受理され、図の値や表示 status が変わり得ます。**推奨処置：** wrapper の期待値を今回記録した固定 SHA-256（`0a6008d1…`、`7799a064…`）にし、変更時は描画を拒否する。WAL・raw・正しさ・source binding の相互照合は残っており、現時点の anomaly を受理した証拠はありません。

**A-F2 — should-fix：対照表が receipt 上の R2 node 数を `unknown` と表示する。** [比較表:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-29/t2853-r2-fig11/figures/fig11_comparison.md:8) は `receipt unknown` ですが、reservation に束縛された `allocation-qstat.stdout` の `Execution Hosts(JSVNO)` には `bnode087`〜`bnode091` の **5 host** が同一行にあります。wrapper の正規表現は一行一 host の形しか読みません（[wrapper:147](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/tools/t2853_r2_fig11_plot.py:147)）。**放置した場合：** 表だけが実在する割当て証拠を欠落として示します。**推奨処置：** 複数 host を同一行から数え、束縛済み receipt の値 `5` を表に反映する。

## 照合したもの

- NQSV 原本は request `35349.nqsv`、5 job、15:17:25〜15:35:01 JST、Elapse 1,061 秒。費用は `5 × 1061 ÷ 3600 = 1.4736` node 時間で、記載の 1.47 と一致します。`driver_rc=0`、finish-group と collect の記録も一致します。
- R2 の 5 標本から、stock 中央値 **10,325,830**、平均 **10,383,298.6 ± 176,681.3**、fixed2 中央値 **9,787,402**、平均 **9,811,373.8 ± 106,923.1** を再計算しました。効果 **−0.05214379860989382**、`reject` と一致します。元 attempt の標本・平均・CI・効果 **−0.057841193339621455** も一致します。abort rate は記録値 0.1554／0.1445 と一致します。
- R2 の両 cell は raw 上で正しさの各 6 走が `pass`・`serializable`、trace 有効です。性能標本は trace 無効で、certification の両 cell は `certified`・`bound`。規律 1・2 に反する実測値は見つかりませんでした。
- insight 記載の collect 成果物 hash、provenance の入力・出力 hash、図・表の原本と写しを照合し、一致しました。reproduction の argv は静的には実行可能な形です。read-only のため再実行はしていません。
- §0 の commit `c231b9042` は **15:12:21 JST**、投入開始は **15:16:53 JST**。`git diff 035fc11fa..HEAD` で元 attempt の tracked 成果物、結果稿、既存 fig11 の変更はありません。

## 総括

記録された測定値と現在の図は整合しています。A-F1 を直し、固定した入力からの再描画を親が確認すれば、受理条件と provenance の主張が揃います。