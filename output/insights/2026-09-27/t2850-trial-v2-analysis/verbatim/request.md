/dev-wave の引数 (2026-09-27、逐語)

[T-2850] 試走 v2 (cohort t2850-trial-v2、18 job、2026-09-27 03:40 JST に 3 系列とも series-end・driver rc=0) の後段を進める。正本:
  事前登録 docs/search-repetition-trial-preregistration.md と追補 1・2、D2231・D2254、worklog entry 1875 の carry、job dir
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/、insight
  output/insights/2026-09-26/t2850-trace-concurrent-verify/ と output/insights/2026-09-26/t2850-trial-pause-cost-options/。やること: (1) 欠測
  (品質欠測・LLM 週上限・verify-local-unavailable) と job Elapse の総和を集計し、見積り 22.2〜40.5 node 時間と照合する。(2) 事前登録 §8
  の規則で T_c・対差 SD・課題集合・系列数を計算し、追補 3 に書く。(3) 本比較の node 時間と LLM
  の直列時間の見積りを示し、投入はユーザー確認の後にする (D2212 項 4)。(4) LLM の待ちを node の外へ出す案 (a) は、試走の実測で残る待ちの node
  時間が導入費を上回るときだけ設計する。(5) 本比較の job body では [T-2853] (1'') の保全口 IZANAGI_TRACE_ARCHIVE_ROOT の opt-in
  を有効にする。生成・選択に [T-2851] の留保条件を使わない。時間帯の区切りは入れない (2026-09-26
  のユーザー裁定)。orchestrator/campaign/p3_s4_loop.py の flock 範囲は並走の [T-2104] の担当なので触らない。規律 2
  を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
