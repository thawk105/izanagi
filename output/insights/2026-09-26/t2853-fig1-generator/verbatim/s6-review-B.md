## 所見

- **B-M1** — [plot_p2_5_search_cost.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:174): caption と図題にスレッド数・レコード数・skew がない。[作図規約 §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/FIGURE_CONVENTIONS.md:65) が求める測定条件を、読者が後継図から特定できない。WAL の `run_cmd` から実値を取り、caption に含める。値を抽出できない場合は出力を止める。

- **B-S1** — [plot_p2_5_search_cost.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:90): `greedy_p_lt`、greedy の最小・最大など、描画にも caption にも使わない値まで照合している。これらだけが変わっても後継図の値は変わらず、入力の受理だけが狭まる。照合を描画値とその算出に必要な値へ絞り、`checked_keys` もそれに合わせて減らせる。

- **B-S2** — [test_plot_p2_5_search_cost.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/orchestrator/tests/test_plot_p2_5_search_cost.py:19): M6 の seed 変更では `load_data()` 内の照合が先に失敗するため、指定された write-heavy 度数の assert には到達しない。変異は殺せても「度数テストが seed を検出した」という帰属にはならない。変異表を照合による kill に直すか、度数を直接試す経路を用意する。

- **B-S3** — [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-fig1-redraw/s1-brief.md): 親の「全一致」は同 brief 自身が記す旧図 greedy 四角の画素差 0.04〜0.05 を含められない。1.3 秒もその環境での probe 時間に限る。また P3 と certified・被覆検査は受理集合を変えるので、段 2・3 省略理由の「受理集合に触れない」は成立しない。旧新両図の画素照合を終えるまで、全一致を結論にしない。

## 削らない判断

P3 の**描く値**の照合は残す。再計算経路が変われば旧図と違う値を描けるため、fig13 の再計算一致要求と同じ実効性がある。8 構成被覆も、欠けた landscape が探索コストと random／oracle の参照値を変えうるので残す。記録上 certified の確認は E0 の記録を使う範囲で意味がある。現行 `replay.assert_complete` は verification evidence も要求するため、そのまま代用できない。共有化のための `orchestrator/` 変更は scope 外。

## 変異の帰属

M1〜M5、M7〜M10 は指定した検査または実データ読込への帰属が静的に確認できる。**M6 は単一理由性なし**：度数 assert より先に P3 照合で落ちる。C0 は test の docstring だけで、静的には生存する。いずれも実走結果ではない。

## 判定

**NO-GO**。測定条件を caption に入れ、旧新図の値照合を完了してから再判定する。

## 総括

実データの読込・描画テストはこのレビューでは実走していない。P3 と landscape の中核検査は残し、描かない値の照合を削る余地がある。