## 所見

**F1 · should-fix — v1 図の provenance に、再生成できないコマンドが記録されている。**

根拠: wrapper は [draw_single の argv](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/wrapper/t2853_r2_fig8b_plot.py:199) に原生成器の直接起動を記録する。しかし原生成器の [v1 経路](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:669) は原 cohort 1 の固定入力を読む。R2 の [図 provenance](/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/figure/fig8_r2a_b10_static_tail.provenance.json) に載るコマンドをそのまま使っても、R2 の入力を選択できない。

放置時の影響: provenance の再生成コマンドは入力欠落で停止し、記録された R2 図を再生成できない。

推奨: provenance の `reproduction` に実際の wrapper と `r2-single` の引数を記録する。生成器の測定値検査とレイアウト検査は維持する。

## 検査境界

wrapper が差し替える属性は、v2 の `COHORTS[1/2]` 内の group ID・日付・report dir・入力 hash・結果稿と `CLAIM_BOUNDARY_V2`、v1 の `GROUP_ID`・`REPORT_JSON`・`REPORT_DAT`・`COMPLETE_JSON`・`PINNED_SHA256` である。関数は v2 の `_caption_v2`・`make_figure_v2`、v1 の `_caption`・`make_figure` を包む。入力先と期待 SHA の変更は**受理する入力集合に効く**。caption と見出しの置換は表示語に効き、v2 見出しの font size 変更はレイアウトに効く。[wrapper](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/wrapper/t2853_r2_fig8b_plot.py:67)

測定値については原生成器の `load_measurements` を使い、verdict、`gate_passed`、failures、stock pin、SHA、DAT、正しさの検査を差し替えていない。`_publish_outputs` のレイアウト検査も通る。表の例外は「拒否」として出力され、黙って受理されない。v2 の拒否は [逐語ログ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/verbatim/draw-r2.log:7) と [README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:210) に掲載されている。検査を外さず、同じ生成器の v1 経路で各 group を描いたため、投入前の §0 項 7 との矛盾は認めない。非合成、「飽和しない」への読み替え、規律 1・2・7 に反する記述も見つからなかった。

## 総括

**NO-GO**。数値と判定の食い違いは見つからなかったが、F1 の再生成記録を修正してから受理する。

独立に確かめた値は次のとおり。

- R2 の 6 job ID `32554–32559`、host `bnode021–026`、Elapse `838/837/836/841/836/842` 秒（合計 `5,030` 秒）、sweep `822.21/821.26/820.24/824.76/820.30/826.56` 秒。根拠は [job root](/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/) と [会計ログ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/verbatim/elapse.log)。
- R2-a の JSON・DAT・complete の SHA-256 は `e8868253…`・`14c43f03…`・`d176c97f…`、R2-b は `e8a88886…`・`c7f731e7…`・`be55381d…`。6 件とも [README §3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:93) と一致。
- 4 group の verdict、failures、各 24 cell の gate、各 18 区間の状態、正しさ各 `120 certified / 0 anomaly`、事前登録 commit・blob・spec、source commit を原報告と照合した。さらに反復値から**全 96 点の平均・95% CI**、**全 72 区間の状態と 36 組の L・throughput 比**を再計算し、README との差は 0 件。
- R2-a／R2-b の PNG、PDF、provenance の各 SHA-256 と、insight に写した PNG の bytes を照合し、一致した。投入前 commit `f22dad793` は **08:10:22 JST**、最初の投入は **08:11:11 JST**。