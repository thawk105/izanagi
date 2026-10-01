# [T-2853] R2 fig10 — B-7 (fixed 5 µs × 3 workload) を現行の certification driver・現行 policy (5 node)・現行 CCBench pin で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-10-01 JST。wave `t2853-r2-fig10` (背景 job、branch `worktree-t2853-r2-fig10`)、着手時の基準 = local main `5f9e8c549`、投入 checkout = local main `db710338d`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig10 = B-7 fixed 5 µs × 3 workload、5 node、3.40 node 時間)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` (fig10 の経路)、先例 `output/insights/2026-09-29/t2853-r2-fig11/README.md`・`output/insights/2026-09-29/t2853-r2-fig6/README.md`。
- 計算の承認: D2305 項 9 (ユーザー裁定、fig10 の 3.40 node 時間を承認、1 図 1 タスク)。
- 原 attempt: `b7f5-20260919a` (tracked 成果物 `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/`、結果稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`、
  図 `docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.*`)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 以後この節は書き換えない (訂正は追記で行う)。

1. **地位。** attempt `b7f5-r2-20261001a` は、B-7 の測定設計 (policy `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json`、sha256 `c6b24050…`、study `paper-story-b7-fixed5-regression`、
   3 workload rr5 (write-heavy)・rr50 (balanced)・rr95 (read-heavy) の各々で stock (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) 対 fixed 5 µs (`BACK_OFF=1`, `BACKOFF_FIXED=5`)、
   48 thread・1,000,000 record・Zipf 0.9・read-modify-write 無効・max operations 10・3 秒・各 cell 5 標本の中央値比較、正しさは legacy 1 + performance 5) を、
   固定 genome・LLM なしで 1 回測り直す**再現パッケージの試行**である。原 attempt `b7f5-20260919a` の置換・追認・反復ではない。
2. **形。** 現行 repo の driver `tools/pegasus/submit_paper_story_a2_certification.sh` を、local main `db710338d` の detached checkout から現行 policy (`scheduler.nodes = 5`、gen_S、walltime 12:00:00) で投げる。
   driver は workload ごとに 1 request を出す (3 request × 5 node、job 名 `paper-b7-fixed5`)。driver・job body・policy・生成器は変えない。
3. **原 attempt と条件が違う点 (結果の前に列挙する)。** 原 attempt は izanagi source `c18a80967`・CCBench pin `511c953`・5 node × 3 request (2026-09-19) で走った。
   R2 は source `db710338d`・CCBench pin `6810666` で走る。`511c953..6810666` の CCBench 差分は `cc/mocc/transaction.cc` だけで、silo の source と adopted cell に当てる
   `patches/silo-backoff-fixed.patch` の対象 (`cmake/Options.cmake`・`include/backoff.hh`) は同じだが、R2 は原 attempt と同じ build・同じ node・同じ日時ではない。
   これらの差は R2 を「同一条件の再走」と呼ばない理由として書き、差の効果は推定しない。
4. **合成しない。** 原 attempt と R2 の標本・中央値・効果・床値判定・outer status を互いに合成しない。統合 verdict、プール推定、attempt をまたぐ有意水準の保証を作らない。
   数値の近さ・符号の一致・判定の一致を再現精度として評価しない。
5. **attempt 数と停止基準。** attempt 数は 1。停止基準は「この 1 attempt (3 request) の結果を、outer status が `certified` でも `reject` でも、indeterminate でも、一部 request だけの完走でも、未完走でも、そのまま報告する」。
   起動時の検査で測定前に落ちた request (campaign の build・bench が 1 つも始まっていないもの) に限り、原因が driver・policy・依存元の変更を要しないなら、新しい attempt id で同じ形のまま 1 回だけ投げ直してよい。
   落ちた request ID・attempt id・理由は記録し、取り下げない。測定が始まった後の失敗は投げ直さず、その結果を報告する。
   **費用の条件:** 本走の見積りは原 attempt の NQSV 会計 Elapse (386 + 841 + 1,218 s) × 5 node = **3.40 node 時間** (承認量と同じ)。受入 1 回の見積りは約 0.26。
   測定前に落ちた request の Elapse × 5 node を実費として足し、投げ直した後の見込み (実費 + 3.40) が承認量 3.40 を大きく超える (1.2 倍の 4.08 を超える) ときは、投げ直す前に land 調整役へ示し直す。
6. **正しさ。** 正しさは job 内の trace 有効 build の別走で判定し (規律 1)、anomaly が出た cell は即 reject とする (規律 2)。性能は trace 無効 build で測る。
   検査を緩めて描く・記録することはしない。
7. **床値判定の規則 (結果より前に固定)。** R2 の各 workload の床値判定は、原 attempt・生成器と同じ規則「効果 (adopted 中央値 / stock 中央値 − 1) < −floor (厳密) なら regression、そうでなければ no-regression」で、
   floor は生成器が pin する同じ 3 file `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json` (sha256 `25b4d2a0…`・`a94dc83e…`・`23c024e4…`) の `between_run.cv` とする。
   R2 には結果稿が無いので、親が collect 後に R2 の `certification.json` の `effects` と上の floor から生成器とは別の計算で判定を出して本 insight に記録し、それを描画時の「記録された判定」とする。
   床値判定は有意差の判定ではなく、床値の測定 (2026-09 上旬、別 binary・別 node) と R2 の同一性は設定上のものである (原 attempt の結果稿と同じ限定)。
8. **図と表。** 原 fig10 と同じ生成器 `tools/plotting/plot_b7_fixed5_regression.py` (sha256 `f78da66d…`、bytes 不変) を repo 外の wrapper から呼んで R2 の図を描き、原 attempt と R2 を同じ生成器の読み込み関数 `load_evidence` (全検査つき) で
   attempt ごとに別々に読んだ対照表を並べる。wrapper が差し替えてよいのは、R2 の入力を指す識別子 (attempt id・certification / raw-manifest の sha256。sha256 は collect 後の bytes を本 insight に記録した定数とし、入力から自己計算しない)、
   項 7 の「記録された判定」、caption の地位・役割語だけで、測定値の受理条件 (hash 照合・schema・study・cell・5 標本・正しさ・source binding・trace 無効の性能標本) とレイアウト検査は変えない。
   生成器が R2 の入力を検査で拒否した場合は検査を外して描かず、拒否理由と得られた値を表で記す。
9. **原成果物は不変。** 原 attempt の tracked 成果物・結果稿・既存 fig10 は凍結物のまま保持し、R2 の結果で書き換えない (規律 7)。R2 の `collect` は repo 外の空 dir を `--repo-root` にして materialize し、
   policy の `tracked_destination` (原 attempt の tracked leaf) へは書かない。
10. **主張の範囲を増やさない。** outer status は protocol の 3 workload の連言の答えであって、有意差・研究の成否・B-7 の充足判定 (D2044 項 3) を判定しない。性能は認証しない。
    R2 の値を他の機体・pin・protocol・採用値へ外挿しない。
11. **trace 保全口 (D2233) は使わない。** driver の `qsub -v` は job へ渡す環境変数を固定で列挙し、`IZANAGI_TRACE_ARCHIVE_ROOT` を渡す口が無い。driver は変えないので、R2 の trace は保全されず R1 (保存 trace の再判定) の入力にならない。
12. **待ち行列の扱い。** 投入の直前に `qstat` を見て、生成器対照の本走 (job 名 `izs4loop` 系) に待ち (QUE) があれば、投入後に本 wave の request の優先度を `qalter -p` で下げる (本走を追い越さない)。
