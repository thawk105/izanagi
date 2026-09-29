# [T-2853] R2 fig6 — A-2 (stock 対 fixed 10 / 5 µs) を現行の certification driver・現行 policy (5 node) で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-09-29 JST。wave `dev-wave-t2853-r2-fig6` (背景 job)、着手時の基準 = local main `035fc11fa`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig6 は試算 1.70 で暫定不要)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` §2.2 (fig6 の経路)、先例 `output/insights/2026-09-28/t2853-r2-fig8b/README.md`。
- 原 attempt: `t2364-20260907b` (`output/insights/2026-09-07_t2364-paper-story-a2-certification/`、結果稿 `docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md`、図 `docs/paper-story/figures/fig6_a2_certification_observed_positive.*`)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 結果を見てから地位・報告の仕方を変えないためである。

1. **地位。** R2 attempt は、fig6 の測定設計 (A-2 policy の 4 cell: rr5 の stock `BACK_OFF=0` 対 fixed 10 µs、rr50 の stock 対 fixed 5 µs。
   48 thread・1,000,000 record・Zipf 0.9・read-modify-write 無効・max operations 10・3 秒・5 反復、各 cell で legacy 1 + performance 5 の正しさ検査) を、
   固定 genome・LLM なしで 1 回測り直す**再現パッケージの試行**である。原 attempt `t2364-20260907b` の置換でも取り消しでもない。
2. **形。** 現行 repo の driver `tools/pegasus/submit_paper_story_a2_certification.sh` を、現行 main の detached checkout から、現行 policy
   `orchestrator/campaign/paper_story_a2_certification.v2.json` (`scheduler.nodes = 5`) と現行 CCBench pin `6810666` で投げる (2 job: rr5・rr50)。
   driver・job body・policy・生成器は変えない。
3. **原 attempt と条件が違う点 (結果の前に列挙する)。** 原 attempt は 1 node の policy・CCBench pin `511c953`・izanagi source `31ec382a7` で走った。
   R2 は 5 node の policy (正しさ検査を兄弟 node へ分ける経路) と pin `6810666` で走る。`511c9538..68106660` の CCBench 差分は `cc/mocc/transaction.cc` だけで、
   silo の source と adopted cell に当てる `patches/silo-backoff-fixed.patch` の対象 (`cmake/Options.cmake`・`include/backoff.hh`) は同一である。
   性能の bench は head node で行い、原 attempt と同じく trace 無効 build で測る。これらの差は R2 を「同一条件の再走」と呼ばない理由として書き、差の効果は推定しない。
4. **合成しない。** R2 と原 attempt の標本・median・効果・outer status を合成しない。統合 status、プール推定、attempt をまたぐ有意水準の保証を作らない。
   数値の近さ・符号の一致を再現精度として評価しない。
5. **原 attempt は不変。** 原 attempt の成果物 (`output/insights/2026-09-07_t2364-…/`)・fig6・結果稿は凍結物のまま保持し、R2 の結果で書き換えない (規律 7)。
   R2 の値は本 insight で原 attempt の値と並べて記録するだけである。R2 の `collect` は repo 外の一時 root へ書かせ、repo の tracked destination へは書かない。
6. **結果にかかわらず報告する。** R2 の outer status が `observed-positive` でも `reject` でも indeterminate でも、1 job だけの完走でも、未完走でも、そのまま本 insight に書く。
   失敗した job は取り下げず、得られた観測値と失敗理由を記述的に開示する。起動時の検査で測定前に落ちた job (campaign・WAL・測定なし) は、
   新しい attempt ID で同じ形のまま投げ直し、落ちた attempt ID・request ID と理由を記録する。
7. **正しさ。** anomaly が出た cell は即 reject (規律 2)。正しさ検査は原 attempt と同じく job 内の trace 有効 build の別走で行い、
   計測は trace 無効 build で行う (規律 1、driver の既存経路)。検査を緩めて描く・記録することはしない。
8. **図と表。** 原 fig6 と同じ生成器 `tools/plotting/plot_a2_certification.py` (bytes 不変) を repo 外の wrapper から呼び、R2 の certification・raw manifest の sha256 だけを
   生成器の既存の差し替え口 (`main(..., expected_hashes=...)`) に渡して描く。対照表 (原 attempt と R2) も同じ生成器の読み込み関数 `load_measurements` (全検査つき) で作る。
   生成器が R2 の入力を検査で拒否した場合は検査を外して描かず、拒否理由と得られた値を表で記録する。図の caption は生成器が記録から組む既定文のまま変えない。
9. **主張の範囲を増やさない。** outer status は protocol の status であって研究の成功宣告ではない。性能の certification は正しさの certification と別の段で、
   R2 の性能 status も原 attempt と同じく他の workload・機体・pin へ転移すると言わない。
10. **trace 保全口 (D2233) は使わない。** driver の `qsub -v` は job へ渡す環境変数を固定で列挙しており、`IZANAGI_TRACE_ARCHIVE_ROOT` を渡す口が無い。
    有効化には driver の変更が要り、本 wave の範囲外である。R2 の trace は保全されず、R1 (保存 trace の再判定) の入力にはならない。

## 1. 費用の見積りと確認 (投入前)

- 投入形: 2 job (rr5・rr50) × 5 node、gen_S、walltime 6 h (予約上限 60 node 時間)。
- 見積り ((a) Elapse): 同じ A-2 policy・同じ 5 node 形の probe attempt `t2489-20260918a` (request `4978` / `4979`、`output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md` §2) の
  Elapse 680 s + 728 s に node 数 5 を掛けて 7,040 node 秒 = **1.96 node 時間**。repro-rest の 1.70 (B-7 の Elapse を当てた試算) より直接の値なので、こちらを使う。
- 開発の検査: 受入全走 1 回 ≈ 0.25 node 時間 (見積り、DW-S04 は受入を免除しない)。
- 合計 ≈ **2.21 node 時間** で線 (2 node 時間) を越えるので、投入前にユーザーの確認を取る。
