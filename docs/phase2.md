# Phase 2 — パラメータ探索

**目的:** CCBench の最適化フラグ空間を探索し、入力 workload に最速の CC 構成 (genome) を見つける。
roadmap §2 層2(a) **パラメータ粒度を主軸**。空間は有限 (silo 2^4→相互排他で 12、anatomy §3) なので
**初手は全探索**。全探索で得た最適を ground truth とし、LLM 誘導探索の到達速度を比較する
(roadmap §9 / 論文の図)。

**副産物:** パラメータ variant は CCBench 由来のフラグ組み合わせなので理屈上**全部正しい** →
**verifier の大規模 sanity check** (Phase 1 verifier 信頼性の総仕上げ)。

**Phase 2 完了の定義:**
- silo 全 genome を実 fitness で評価し、workload 別の最速構成を WAL + 材料レポートで再現可能に特定できる
- 測定安定性 §3.6 (2)(4) が自動執行される (反復内 CV 閾値超で自動再測定→`unstable`、採否は分布比較)
- critic が leading indicators を読んで「次に試す方向」を構造化指示に変換できる
- 全探索 vs LLM 誘導の到達 iteration を比較したデータが出る

**サブエージェント:** + critic, profiler (`docs/agent-architecture.md` の仕様で実体化)

**環境:** 計測は linux-baremetal の確定 calibration (records=1m / 48 thread / skew0.9 / reps5、
noise floor CV 2.28%、`output/env/linux-baremetal/calibration/`)。**性能計測は単一テナント直列**
(絶対規律4)。ビルド・trace 検証は並列可 (`lock.py` の bench_lock はベンチのみ排他)。

段階導入 (規律5): P2-0 から順に。各タスクの効果は ablation で測れるようにする。

---

## P2-0: 全 silo variant のビルド + verifier 大規模 sanity (タスク6 の残り)

パラメータ variant は理屈上全緑のはず = verifier の大規模 sanity。**計測なし** (do_bench=False)。
- [ ] silo 12 genome を `genome.SILO_SPACE.enumerate()` で列挙し、loop で
      build(trace+perf)→verify→no-bench commit を回す
- [ ] **12 genome 全て certified** を確認 (false-red が出たら verifier か genome 空間の不整合 →
      `output/insights/` に記録)
- [ ] 規律1 再確認: 全 perf build に izanagi_trace symbol 0 (`nm`)

**完了条件:** silo 全 genome が certified。verifier が大量の正しい variant を緑と判定できる実証で、
Phase 1 の「赤を出せる」(タスク3) と対になる「緑を取りこぼさない」の大規模実証。

## P2-1: 測定安定性 (2)(4) の必須化 (§3.6)

Phase 1 で配線済みの (1)(3) (noise floor + 反復中央値・CV) の上に (2)(4) を積む。
- [ ] 外れ値→自動再測定: 反復内 CV > 閾値 (初期 5%) なら settle 後に測り直し。規定ラウンド
      (初期 3) で収束しなければ `unstable` フラグ
- [ ] 採否は分布比較: noise floor 以下の差は「差なし」に丸め、超える差は Mann-Whitney U で有意性判定
      (重い統計機構は不要)
- [ ] unstable variant は分布比較から除外し insight に「測定不能」記録 (沈黙して 1 点採用しない)

**完了条件:** CV 不安定な測定が自動で再測定/除外され、採否が点比較でなく分布比較で行われる。

## P2-2: silo 全探索 (最初の実探索)

- [ ] loop を**実 fitness** (確定 calibration) で 12 genome 全評価 (直列・env=linux-baremetal)
- [ ] 代表 workload (read-heavy / write-heavy / high-contention) ごとに最速構成を特定
- [ ] 結果を D12 材料レポート (`campaigns/<id>/reports/`) に射影

**完了条件:** 全探索の最適構成が WAL + レポートで再現可能に特定される (LLM 探索の比較基準)。

## P2-3: leading indicators の WAL 記録 + critic 実体化 (§3.5)

throughput スカラーだけでは探索が 8-12 iteration で停滞する (Jitskit)。leading indicators を毎評価
記録し critic に渡す。
- [ ] perf カウンタ (lock contention / cache hit率 / allocator contention 等) を fitness と一緒に
      WAL に記録 (calibrator.runner は既に perf を取れる → 評価経路に接続)
- [ ] `critic.md` を agent-architecture 仕様で生成 (結果を読んで次の方向を指示、**書き込みなし**)
- [ ] critic が生カウンタを組み合わせて設計選択に帰属させ、次に試す genome の方向を構造化指示で返す

**完了条件:** critic が leading indicators から具体的な次手を出せる (ablation: critic 有/無で探索効率比較)。

## P2-4: profiler 実体化 (二段構え)

- [ ] `profiler.md` を agent-architecture 仕様で生成
- [ ] screening 通過した上位 variant にだけ perf/FlameGraph (trace-disabled build, 規律1)
- [ ] many-core スケール懸念 (lock acquisition %, NUMA リモートアクセス等) を診断し critic/層3 に渡す

**完了条件:** profiler が上位 variant の many-core スケール懸念を解釈して返す。

## P2-5: LLM 誘導探索 vs 全探索 (Phase 2 の主実験)

- [ ] critic フィードバックで次の genome を選ぶ LLM 誘導ループ (ランダム変異でなく過去結果で方向づけ)
- [ ] 全探索の最適への到達 iteration を全探索 (12 全部) と比較
- [ ] (任意) cicada/oze 等に protocol を広げ空間を大きくして比較を強化

**完了条件:** 「LLM 誘導が N iter で最適到達 vs 全探索 M」の比較データ (論文の図)。

---

## 当面の着手順

1. **P2-0** (verifier 大規模 sanity) — 計測なしで安全・高速。Phase 1 verifier 信頼性の総仕上げ。
2. **P2-1** (測定安定性ロジック) — machine 非依存の純ロジック + モックテスト (calibrator と同型)。
3. **P2-2** (実 fitness 全探索) — ここから本格的な実機計測 (直列)。

P2-3 以降 (critic/profiler/LLM 誘導) は探索の骨格が回り始めてから足す。
