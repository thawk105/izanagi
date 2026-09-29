# [T-2853] R2 fig11 — A-6 read-heavy 正式 certification (fixed 2 µs 対 stock) を現行 driver・現行 policy (5 node)・現行 CCBench pin で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-09-29 JST。wave `dev-wave-t2853-r2-fig11` (背景 job)、着手時の基準 = local main `035fc11fa`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig11 は試算 1.69 node 時間で暫定確認不要)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` §2.2 (fig11 の経路)、先例 `output/insights/2026-09-28/t2853-r2-fig8b/README.md`。
- 元 attempt: `a6-20260908b` (tracked 成果物 `output/insights/2026-09-08_t2411-paper-story-a6-certification/`、結果稿 `docs/paper-story/results/2026-09-18-a6-certification-reject.md`、図 `docs/paper-story/figures/fig11_a6_certification_reject.*`)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 以後この節は書き換えない (訂正は追記で行う)。

1. **地位。** attempt `a6-r2-20260929a` は、A-6 の測定設計 (policy `paper-story-a2-certification-policy/v2`、study `paper-story-a6-certification`、
   protocol SHA-256 `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`、workload rr95、cell `rr95-stock` (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) と
   `rr95-fixed2` (`BACK_OFF=1`, `BACKOFF_FIXED=2`)、各 5 標本の中央値比較、正しさは legacy + performance) を、固定 genome・LLM なしで 1 回測り直す
   **再現パッケージの試行**である。元 attempt `a6-20260908b` の置換・追認・反復ではない。
2. **A-6 の attempt 系列に加えない。** 結果稿 §3.2 (T-2430) は「新しい反復 attempt は行わない」と定め、D1870 は attempt に数えるには事前登録と `tracked_destination` の新 leaf が要るとする。
   R2 はそのどちらも改訂しない。R2 の結果は policy の `tracked_destination` (元 attempt の tracked leaf) へ materialize せず、repo 外の出力親へ collect する (§1)。
   R2 の値を A-6 の主張・結果稿・fig11 の判定へ遡って入れない。
3. **元 attempt との違いを結果より前に明記する。** R2 は現行 repo (`035fc11fa`) の certification driver・現行 policy (`scheduler.nodes = 5`、正しさ検査を兄弟 node へ分ける経路)・
   現行 CCBench pin `6810666` で走る。元 attempt は source `ae8a767eb`・1 node・pin `511c953` だった。`511c953..6810666` の CCBench 差分は `cc/mocc/transaction.cc` だけで silo の source は同じだが、
   R2 は元 attempt と同じ build ではない。protocol の preimage は pin を含まないので protocol SHA-256 は同じになる。
4. **合成しない。** 元 attempt と R2 の標本・中央値・効果・outer status を互いに合成しない。統合 verdict、プール推定、attempt をまたぐ有意水準の保証を作らない。
   数値の近さ・符号の一致を再現精度として評価しない。
5. **attempt 数と停止基準。** attempt 数は 1。停止基準は「この 1 request の結果を、`certified`/`reject` のいずれの outer status でも、`indeterminate` でも、未完走でも、そのまま報告する」。
   起動時の検査で測定前に落ちた場合 (campaign の build・bench が 1 つも始まっていない場合) に限り、原因が driver・policy・依存元の変更を要しないなら、新しい attempt id で同じ形のまま 1 回だけ投げ直してよい。
   落ちた request ID・attempt id・理由は記録し、取り下げない。測定が始まった後の失敗は投げ直さず、その結果を報告する。
   **費用の条件:** 本走の見積りは 1 request × 5 node で 1.47 node 時間 (同じ A-6 protocol・5 node 形の `a6-20260909b` の Elapse 1,057 s)、受入 1 回の見積りは 0.25 で、合計 1.72 (D2212 項 4 の線 2 node 時間の下)。
   測定前に落ちた request の Elapse × 5 node を実費として足し、投げ直した後の見込み合計 (実費 + 1.47 + 0.25) が 2.0 未満のときだけ投げ直す。2.0 以上ならユーザーの確認を得るまで投げない。
6. **正しさ。** 正しさは job 内の trace 有効 build の別走で判定し (規律 1)、anomaly が出た cell は即 reject とする (規律 2)。性能は trace 無効 build で測る。
   検査を緩めて描く・記録することはしない。
7. **図と表。** 元の fig11 と同じ生成器 `tools/plotting/plot_a2_certification.py` (bytes 不変) で R2 の図を描き、元 attempt と R2 を同じ生成器の読み込み関数で読んだ対照表を並べる。
   生成器が R2 の入力を検査で拒否した場合は検査を外して描かず、拒否理由と得られた値を表で記す。描くための repo 外 wrapper は caption の地位・役割語だけを差し替え、測定値の受理条件とレイアウト検査は変えない。
8. **原成果物は不変。** 元 attempt の tracked 成果物・結果稿・既存 fig11 は凍結物のまま保持し、R2 の結果で書き換えない。
9. **主張の範囲を増やさない。** outer status は当時と同じ protocol の中央値比較の答えであって、有意差・between-run floor 超の退行・研究の成否を判定しない。
   性能は認証しない (performance certification ではない)。R2 の値を他の read 比率・他の機体・他の pin・他の protocol へ外挿しない。
10. **trace 保全口 (D2233)。** 投入 driver `submit_paper_story_a2_certification.sh` は `qsub -v` へ渡す環境変数を固定で列挙し、`IZANAGI_TRACE_ARCHIVE_ROOT` を job へ渡す口が無い。driver は変えないので保全口は使わない。
    R2 の trace は保全されず、R1 (保存 trace の再判定) の入力にならない。
