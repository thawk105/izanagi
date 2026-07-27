# [T-140] 実 set-size 分布の実測 — データ構造軸の地形は存在しない (択 (c) 条件成立)

探索の妥当性文書 (dev-wave t140-setsize、2026-07-28)。worklog (27) のユーザー裁定
「択 (a) 採用、着手前に実 set-size 分布を測る。分布が小さく機序が立たなければ択 (c) =
軸を捨てて [T-139]/[T-144] へ移す」の前提条件を実測で確定した一次資料。
数値の原本 = 同名 `.json` (job staging からの不変コピー)。

## 発見

perf 代表 workload (S2 構成) における commit 時の set size は **max_ope=10 で頭打ちの
小分布**であり、データ構造水準の変異 (container/探索構造の置換) が効く地形は存在しない。

| set | mean | p50 | p90 | p99 | p99.9 | max |
|---|---|---|---|---|---|---|
| read_set_ | 4.954 | 5 | 7 | 8 | 9 | 10 |
| write_set_ | 4.977 | 5 | 7 | 9 | 9 | 10 |
| 合計 | 9.931 | 10 | 10 | 10 | 10 | 10 |

- committed 1,630,508 trx 中、合計 10 (dedup ゼロ) が 93.52%。size 9-10 の重い尾はなく
  (read ≥9 は 0.99%、write ≥9 は 1.01%)、**上限 10 は workload 生成の構造的 cap**
  (`makeProcedure` は毎 trx ちょうど `max_ope=10` ops、include/ycsb.hh:55)
- 分布は独立計算の二項モデルとほぼ一致: Binomial(10, rratio=0.5) + zipf(0.9, 1M) の
  dedup 損失 (sum p_k² = 0.00204 → 合計損失の近似上界 0.092、実測 0.069)。
  例: size=5 のモデル度数 401,268 に対し実測 read 401,351 / write 403,490

## 再現条件と方法

- **workload**: S2 verify 構成 verbatim (`orchestrator/campaign/pipeline.py` S2_FLAGS +
  extime=3) = ycsb_tuple_num=1000000 / zipf_skew=0.9 / rratio=50 / rmw=false /
  max_ope=10 / thread_num=48 / clocks_per_us=2100 (pegasus 登録値)
- **build**: stock silo genome (BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1,
  NO_WAIT_OF_TICTOC=0, WAL=0) + `-DCCBENCH_TRACE=1`、CCBench pin d706650 の使い捨て
  worktree、静的 gflags/glog (tools/pegasus/policy.json の pinned-clean 経路)。
  binary sha256 = c55cc4534c94fda373ae3db2dac7cedb8aec9994b6c0fb3510a1ac180a24ceb9
- **実行**: Pegasus gen_S バッチ 1 node (bnode006、Xeon Platinum 8468 48c)、
  job 0:872886.nqsv、2026-07-28 08:44:45–08:45:26 JST。run 前 loadavg 0.94 (ほぼ専有)。
  一次ログ = `output/env/pegasus/t140-setsize/job-staging/0:872886.nqsv/`、
  ジョブ・集計スクリプト = 同 `job.sh` / `parse_trace.py`
- **導出**: trace の R/W 行数 = commit 時の `read_set_`/`write_set_` サイズ
  (cc/silo/transaction.cc writePhase が両 set を全件 emit)。raw trace (596 MB / 48 file)
  は計算ノード上で digest 化し持ち帰らない (D31)

## 方法論の裏付け (measurement validity)

1. **選択バイアスなし**: abort した trx は同一 `pro_set_` で RETRY する (include/ycsb.hh
   の RETRY ラベルは makeProcedure の後) — committed 分布 = 生成分布。contention
   (abort 573,482) は分布を歪めない
2. **被覆完全**: `commit()` は read-only 含む全 trx が validationPhase → writePhase を
   通る (transaction.cc:693-700)。**trace C 行数 1,630,508 = stdout `commit_counts_`
   (完全一致)**。構造エラー 0、X (lock violation) 行 0
3. **parser の独立検証**: 意味論の異なる smoke workload (tuple200 / rmw=true / max_ope5 /
   t4) で 293,744 trx を集計し、rmw=true の予測どおり read mean 4.69 (200 キーでの
   dedup 損失が可視) / write mean 2.42、commit 数完全一致。合成データで正常系 +
   fail-closed 3 系統 (構造 rc3 / X 行 rc4 / commit 不一致 rc5) も事前検査
4. **規律 1**: trace-enabled build の実測であり、性能値は記録にも判断にも使わない
   (set size は timing 非依存の workload 性質)。分布は環境非束縛 — Pegasus 実測を
   linux-baremetal の軸判断に使える (再取得が要るのは環境束縛量のみ、roadmap §5)

## 解釈 — なぜ機序が立たないか

- 変異対象の `searchReadSet`/`searchWriteSet` は毎 op の線形走査だが、走査長は
  **平均 5、上限 10** で cap される。n≈5 の vector 線形走査に対し hash/tree/sorted 構造は
  定数コスト (hash 計算・分岐・間接参照) で勝てず、presence filter (bloom/bitmap) の
  検査コストも走査 1 回と同額規模
- 尾が伸びる経路が構造的に無い: サイズは `max_ope` の生成時 cap で決まり、データや
  contention では成長しない。「大きい set だけ遅い」型の重尾機序が存在しない
- (27) の 3 候補のうち格納形式・探索構造はこの走査長機序に直接依存し、ともに死ぬ。
  検証順序 (施錠順) の並べ替え効果は既存の sort-strategy 軸 (段 5) が既に保持しており、
  本軸を残す独立の理由にならない

## 裁定条件の適用

裁定 (27) の条件「分布が小さく機序が立たなければ択 (c)」は**成立** — 択 (c) を適用し、
データ構造水準の変異軸を廃止、探索資源は [T-139] (劣化版 Silo の梯子) / [T-144]
(スペクトル補間) へ移す。分布は workload 束縛 (max_ope=10 の生成 cap) の性質であり、
将来 max_ope の大きい workload spec を campaign が採用する場合のみ再測・再評価する。

## 付記 (near-miss)

計測ジョブ 1 回目 (872881.nqsv) は `set -o pipefail` 下の `nm | grep -q` で producer が
SIGPIPE(141) になり **偽赤** で停止した (fail-closed 方向、成果物影響ゼロ)。2 回目で
ファイル経由検査に是正して完走。経緯は failures.md (F44) と job-staging の両 attempt に凍結。
