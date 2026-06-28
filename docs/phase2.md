# Phase 2 — パラメータ探索

**目的:** CCBench の最適化フラグ空間を探索し、入力 workload に最速の CC 構成 (genome) を見つける。
roadmap §2 層2(a) **パラメータ粒度を主軸**。空間は有限 (silo 2^4→no-wait XOR 制約で 8、anatomy §3) なので
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
within-run 変動係数 (CV = 標準偏差/平均) 2.28% = 1 測定の品質ゲート / 採否 floor は between-run 3.0% (A2/D19)、
`output/env/linux-baremetal/calibration/`)。**性能計測は単一テナント直列**
(絶対規律4)。ビルド・trace 検証は並列可 (`lock.py` の bench_lock はベンチのみ排他)。

段階導入 (規律5): P2-0 から順に。各タスクの効果は ablation で測れるようにする。

---

## P2-0: 全 silo variant のビルド + verifier 大規模 sanity (タスク6 の残り)

パラメータ variant は理屈上全緑のはず = verifier の大規模 sanity。**計測なし** (do_bench=False)。
- [x] silo 8 genome を `genome.SILO_SPACE.enumerate()` で列挙し、loop で
      build(trace+perf)→verify→no-bench commit を回す
- [x] **8 genome 全て certified** を確認 (false-red が出たら verifier か genome 空間の不整合 →
      `output/insights/` に記録)。当初 12 から no-wait XOR 制約で 8 に縮小 (両 0=livelock を除外)
- [ ] 規律1 再確認: 全 perf build に izanagi_trace symbol 0 (`nm`)

**完了条件:** silo 全 genome が certified。verifier が大量の正しい variant を緑と判定できる実証で、
Phase 1 の「赤を出せる」(タスク3) と対になる「緑を取りこぼさない」の大規模実証。

## P2-1: 測定安定性 (2)(4) の必須化 (§3.6) — 完了

Phase 1 で配線済みの (1)(3) (noise floor + 反復中央値・変動係数) の上に (2)(4) を積む (`orchestrator/calibrator/stability.py`)。
- [x] 外れ値→自動再測定 (`remeasure_until_stable`): 反復内の変動係数 (CV = 標準偏差/平均) > 閾値 (既定 5%)
      なら settle 後に測り直し。規定ラウンド (既定 3) で収束しなければ `unstable` フラグ
- [x] 採否は分布比較 (`compare`): noise floor 以下の差は「差なし」に丸め、超える差は Mann-Whitney U 検定で
      有意性判定 (重い統計機構は不要)
- [x] unstable variant は分布比較から除外 (呼び手が責任)。沈黙して 1 点採用しない
- [x] **A2 精緻化**: 採否の floor は **between-run** noise floor (別 run で測る variant/baseline の差の下限、3.0%)。
      within-run の変動係数 (2.28%) は 1 測定の品質ゲート用で採否には使わない。Mann-Whitney U は反復数が
      小さい (5) と完全分離で常に有意になる弱い sanity ゆえ、主防壁は between-run floor 丸め。floor 近傍
      (floor〜1.5×floor) の faster/slower は `near_floor` フラグを立て cross-run 再現で裏取り要とする (D19)

**完了条件:** 達成。変動係数が不安定な測定は自動で再測定/除外され、採否は点比較でなく分布比較 (between-run floor
丸め + Mann-Whitney U) で行われる。テスト 109 passed。

## P2-2: silo 全探索 (最初の実探索) — 完了

- [x] loop を**実 fitness** (確定 calibration) で 8 genome 全評価 (直列・env=linux-baremetal)。
      3 workload × 8 = 24 評価が全て certified serializable・abort 0
- [x] 代表 workload (read-heavy=rratio95 / balanced=50 / write-heavy=5, skew0.9) ごとに最速構成を特定
- [x] 結果を D12 材料レポート (`campaigns/<id>/reports/`) + 横断 summary に射影

**完了条件:** 達成。全探索の最適構成が WAL (生 tps + 実行コマンド) + 材料レポートで再現可能に特定。
最速構成 = **read-heavy: B0-T-W0 / balanced・write-heavy: B0-L-W0** (B0-L-W0 が 2/3 で1位・read-heavy で
同点1位 = 全体最強)。知見: BACK_OFF=0 が支配、no-wait は contention 域で即abort が有利。LLM 探索 (P2-5) の
ground truth。途中で前セッションの孤児 livelock による計測汚染を検知・対処
(insight 2026-06-22_orphan-livelock-contaminated-measurement.md)。

## P2-3: leading indicators の WAL 記録 + critic 実体化 (§3.5) — 完了

throughput スカラーだけでは探索が 8-12 iteration で停滞する (Jitskit)。leading indicators を毎評価
記録し critic に渡す。
- [x] leading indicators (abort_rate / latency / llc_miss_rate / ipc) を fitness と一緒に WAL
      (STAGE_BENCH_DONE) に記録。abort_rate は no-wait/backoff の効果が直接出る CC-native 最重要指標
- [x] `critic.md` を agent-architecture 仕様で生成 (帰属→次手、**書き込みなし**) + 機械準備 `critic/digest.py`
      (genome 別 LI + フラグ軸の限界効果)
- [x] critic を実 LI に実走 → 設計選択に帰属 (BACK_OFF=1 は abort 減でも ipc 崩壊で遅い / no-wait は
      workload で L↔T 反転 / WAL は write 比率比例の純損) + recommend/avoid/uncertainty を構造化で返した

**完了条件:** 達成。critic が leading indicators (throughput 単独でない) から機序を推定し設計選択に帰属、
具体的な次手 (BACK_OFF=0 固定・no-wait 出し分け・新軸「中間 backoff」) を出した。ablation の原理
(L↔T 反転の見落としを critic が防ぐ) も提示。定量 ablation (critic 誘導 vs ランダムの到達 iter) は P2-5。
insight 2026-06-22_p2-3-critic-leading-indicator-attribution.md。

## P2-4: profiler 実体化 (二段構え) — 完了

- [x] `profiler.md` を agent-architecture 仕様で生成 (perf 実行・spin/lock/NUMA/IPC 解釈、書き込みなし)
- [x] screening 通過した上位 variant にだけ perf record (trace-disabled build, 規律1)。backoff ケーススタディの
      sweet-spot variant 群を対象に `perf record -e cycles,instructions`。診断ノブ `BACKOFF_NOINLINE` (inert patch) で
      spin を独立シンボル化し有用 IPC を分離 (`orchestrator/campaign/backoff_profile.py`)
- [x] many-core スケール懸念を診断し critic/層3 に渡した。profiler を実データで実走し
      hotspot/scale-risk/mechanism/uncertainty を構造化で返す ([P0] 機序純度を解消: sweet-spot で有用 IPC 一定 =
      total IPC 崩壊は純 spin 希釈、over-throttle で有用 IPC 二次低下。decisions D20 / insight 追記)

**完了条件:** 達成。profiler が backoff variant の many-core 機序 (spin 希釈・有用 IPC・over-throttle) を解釈して返し、
backoff ケーススタディの最後の穴 [P0]「なぜ速いか」を sweet-spot 域で機序的に閉じた。perf 下 tps は overhead 込みで
headline 非使用 (絶対値は stock build)、単一テナント直列 (規律4)。定量 ablation (profiler 有/無) は P2-5 と地続き。

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

---

## Phase 3 着手前 must (Phase 1 完了監査 2026-06-28 が示した繰り延べ項目)

Phase 1 は完了条件を満たす (blocks なし) が「完璧」でなく、4軸監査で出た穴のうち **silo 探索 (Phase 2) を
脅かす H1 admission fails-closed / H2 between-run noise floor は完了** (A1 / A2 = 2026-06-28、between-run を
実測し compare/report を配線、read-heavy rank3/4 の過大主張を是正。[[decisions]] D19)。残りは **Phase 3
(LLM が別 protocol/コードを合成する) で初めて load-bearing になる**ので、段階導入 (規律5) として
Phase 3 着手の直前に消化する (今やると過剰修正):

- **S4 規律3 の配線**: verifier の構造化 anomaly (cycle/edge/EdgeReason) が `pipeline.py` の境界で件数だけに
  潰れ critic/planner に流れていない。Phase 2 (列挙=全 variant 緑) では無害だが、**赤を出す Phase 3 で規律3 が
  死ぬ**。red 時 `result_to_dict(vr)` を WAL abort payload に載せ次手生成が読む経路を 1 本通す。
- **H3 hooks の実体化**: `hooks/` の規律1/2 機械防壁は placeholder。**LLM が C++ variant を書く瞬間**に第二防壁が
  必要 (hooks/README に明示済み)。
- **S2 certify workload = perf workload の一致**: 検証 (tuple200/thread4) と計測 (1m/thread48) が別。合成 variant が
  「小 workload では踏まないデータパス」を持つと緑 certify と赤い実行が食い違う。perf 構成 (の縮小版) でも 1 回
  verify + broken-silo 同一フラグ赤検出を消化 (insight の follow-up [P1])。
- **S1 trace-hook の別 protocol 拡張**: silo+si のみ instrumented。別 protocol を探索素材に入れる Phase で同型 hook を
  追加 (ermia は cstamp<<1 の罠を worklog 記録済み)。それまでは「silo+si 以外は探索外」を維持。
- **C1 campaign-id drift (A2 で露呈)**: 6/28 の ODR-fix gitlink 前進 (CCBENCH_COMMIT 6656e93→dff0f1e) が
  content-addressed campaign-id (D13) を移動させ、歴史的 p2-2/backoff campaign の report が現 config では孤立した
  (生成器が現 commit で id を再計算するため WAL を引けない)。ODR fix は ADD_ANALYSIS=0 perf build に inert なので
  6/22 測定は意味的に有効。A2 では測定時 commit (6656e93) を供給して忠実に再生成した。**恒久対応の選択肢**:
  (a) report 生成器が campaign dir を discover する (現 config から再計算しない)、(b) inert な submodule fix では
  campaign-id を据え置く版マッピング、(c) 現 pin で p2-2/backoff を再 run。Phase 2 の探索を本格再開する前に決める。
