# [T-2702] 段 1 brief (親、2026-09-16 20:05 JST)

依頼 (ユーザー引数、逐語): [T-2702] digest の leading indicator 行の整合を直す。(a) `latency_ns` は `1e9 * threads / tps` で throughput の恒等変換なので独立な指標として提示しない (出所 `external/ccbench/common/result.cc:52-56` は読むだけで CCBench は改変しない、D16/D18/D20)。(b) reps が偶数だと代表 rep が速い側へ寄り、同じ行の throughput (真の中央値) と abort_rate / latency (代表 rep) が別の量になる (`orchestrator/calibrator/runner.py:1053-1055`)。どちらも [T-2588] の走行で実測・検算済み。digest の consumer (planner / coder / critic への射影、layer3) を段 1 で列挙し、schema を変えるなら D828 に従う。Codex author = D95。規律 2 を緩めない。本題の 2 点だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

**研究前進:** critic / planner が読む digest 行から「情報ゼロの列 (latency)」と「速い側に寄った代表 rep の abort_rate」を除き、段 4 ループ (T-2588 で 1 巡閉じた K2 実験) の機序帰属が偽の信号を読まない状態にする。完了判定 = 偶数 reps の走行で digest 行の throughput と abort_rate が同じ rep 集合の同じ演算になり、digest に latency 列が出ない。

**前提の実測 (親が一次資料で確認済み):**
- `external/ccbench/common/result.cc:52-56` — `latency[ns] = 1e9 / result * thread_num`、`throughput[tps] = result`。恒等変換。CCBench は改変しない。
- `orchestrator/calibrator/runner.py:1053-1055` (measure_point 経路) と同 `:1289-1294` (deferred floor 経路、同型) — `median = throughputs[len//2]` (偶数で上側) → `rep = min(valid, key=|tps-median|)`。counters / walltime / maxrss / abort_rate / latency_ns の 5 field がこの rep 由来。
- `orchestrator/calibrator/model.py` — `ScalePoint.throughput` は `_median` (偶数は中央 2 点の平均)。`leading_indicators()` は throughput (中央値) と abort_rate/latency_ns (代表 rep) を 1 dict に混ぜる。`pipeline.py` の `median_tps` は `analyze.noise_floor` の `statistics.median` (同値)。
- T-2588 insight の検算 `1e9*4/727985 = 5494.62 = latency_ns 記録値` を再計算して一致。
- 偶数 reps の本番経路: `p3_s4_loop.default_perf` / `p3_kickoff` / `p3_s4_red` / `demo` / `p3_autonomous_workload_trial` (すべて reps=2)。calibrator・b10 sweep・p2_2 は reps=5 (奇数、影響なし)。

**scope (本題 2 点だけ):**
- (a) `orchestrator/critic/digest.py`: `INDICATORS` / `HIGHER_IS_BETTER` から `latency_ns` を外し、表と軸の限界効果に出さない。docstring の「latency 3 倍」帰属例 (module docstring 11-13 行) を恒等変換に依らない例へ書き換える。WAL の `leading_indicators.latency_ns` は残す (CC 本来のデータ、b10 sweep の `representative_latency_ns` が読む)。
- (b) `orchestrator/calibrator/runner.py` の 2 経路: 代表 rep の選び方を throughput の真の中央値 (`_median`) と整合させる。
- テスト: `orchestrator/tests/test_critic.py` の latency 断言 (667, 683 行) と `test_calibrator.py` に偶数 reps の正例を Codex author が書く。
- docs-only: `.claude/agents/critic.md:14,26-27` と `.claude/agents/critic-experiment.md:36-37` の指標列挙・帰属例 (latency を独立指標として読ませる記述) — (P2) 親の provisional: 本 wave では触らず記録に留める (role 入力の変更は K0/K1 アーム条件を変える、T-2703 と同型の射程裁定が要る。B-4 事前登録は発効前 draft・hash 未記入なので pin は無い)。

**scope 外:** WAL / layer3 schema の変更 (leading_indicators は `{"type":"object"}` で自由形、追加不要)、8c 役割 payload の key 集合 (`s8c_generation_projection._PERF_KEYS` 等、D118 系の裁定で閉列挙)、新 gate・検査・台帳、counters の平均化。

**digest / leading_indicators の consumer 列挙:**
1. `critic/digest.py render_text` → `p3_s4_loop.make_critic_digest` → critic (claude_projected_provider / p3_b4_closed_critic)。`online_digest.py` (P2-5 critic-experiment)、`p3_b4_wiring_probe.py:1677`。`INDICATORS`/`HIGHER_IS_BETTER` の外部参照なし (digest.py 内と test のみ)。
2. `GenomeLI.li` 直読: `backoff_sweep_report.py` (throughput/abort_rate/ipc のみ、latency 不使用)。
3. WAL `bench_done.leading_indicators` 直読 (digest を経ない): `p3_autonomous_workload_trial._metric_projection` (8c planner/coder/critic payload、latency_ns を含む閉列挙)、`s8c_generation_projection` (`_PERF_KEYS`/`_SOURCE_METRIC_KEYS`)、`autonomous_trial_completeness._DIAGNOSTIC_METRICS`、`layer3_report` (object passthrough + perf_observation 検証は llc/ipc のみ)、`backoff_extended_sweep*` (`representative_latency_ns`、reps=5)、`s8b_*` の placeholder。
4. 人手射影 (T-2588 の K2 loop): 親が `current_perf` に throughput/abort_rate_pct を書く (latency は渡していない)。

**pin 閉包 (DW-O09):** `runner.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` (HEAD blob 束縛 → 未 commit で contract-loader-drift の偽赤) と source closure 列挙 (`test_t671_source_binding` / `test_official_perf_closure` / `test_artifact_admission` / `paper_story_a1_paired` / `test_s8b_floor_campaign`) の member。いずれも path 列挙で bytes hash pin ではない。`digest.py` は `p3_b4_closed_critic.projection_closure_manifest` の member (実行時 hash。admission record JSON は未発行、事前登録の hash 欄は未記入 → 凍結 pin なし)。記録済み digest テキスト 3 件 (output/campaigns/*/…_digest.txt) は golden 比較なし。FROZEN_MANIFEST / generator sha pin: hit 0。

**割れうる前提 (親の provisional 裁定・攻撃対象):**
- (P1) (b) の修正形 = 案 A: 有効 rep を throughput で整列し、奇数なら中央 rep、偶数なら中央 2 rep について abort_rate / latency_ns を算術平均 (= `_median` と同じ演算を同じ rep 集合へ)。counters / walltime / maxrss は平均できないので偶数では中央 2 rep のうち実行順が先の rep を採る (throughput 方向の系統偏りを持たない決定的規則)。奇数 reps では現行と bytes 同一。対案 B = 単一代表 rep のまま真の中央値最近接 + tie-break (偶数は常に tie で規則が全て)、対案 C = throughput 順と独立な per-rep 中央値 (奇数の意味が変わる)。
- (P2) role 文書 (critic.md / critic-experiment.md) は本 wave で触らない (上記)。
- (P3) None 混在: 中央 2 rep の一方が None なら残る側の値、両方 None なら None (`digest._mean` と同じ)。

**不変条件:** fitness (`median_tps`) と verdict は不変。WAL/layer3 の key 集合は不変。CCBench 不変。奇数 reps の出力 bytes は不変。規律 2 を緩めない。

**分割方針:** 実装 1 単位 (Codex author 1 本、digest.py + runner.py + test 2 file)。

**受入・実測環境:** login node で焦点走 (統合 commit 後)。受入全走は計算ノード。
