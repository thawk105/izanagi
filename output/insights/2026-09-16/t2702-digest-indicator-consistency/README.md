# [T-2702] digest の leading indicator 行から latency を外し、偶数 reps の abort_rate / latency_ns を throughput と同じ中央値演算に揃えた

- 日付: 2026-09-16
- wave: dev-wave-t2702-digest-indicator-consistency (branch `worktree-dev-wave-t2702-digest-indicator-consistency`)
- 起票: archive `docs/archive/worklog-phase3-0916-1548.md` の [T-2702] (T-2588 wave が 2026-09-16 に起票)。
  実測の出所は `output/insights/2026-09-16/t2588-k2-loop-roundtrip/README.md` の critic 所見 (a)(b)
- 基準: local main 8f17db5981a689789916fcc56ccf373b10347e1a (CCBench submodule はその pin 511c9538e)
- 実装 commit: 106c0ec04 (Codex author = gpt-6-astra / medium、親は manager)、文言 fix commit: d586abff5 (段 6 レビュー A の nit 2 件、文言だけ、Codex fix 子)
- 段 2 plan / 段 3 敵対 2 レンズ / 段 6 レビュー 2 レンズ + fix 1 本の逐語は `verbatim/` に置く

## 1. 何を直したか (本題の 2 点だけ)

**(a) `latency_ns` を critic digest の列から外した。** CCBench の通常出力 (`external/ccbench/common/result.cc` の
`displayTps`) は `result = (commit + batch_commit) / extime` から `latency[ns] = 1e9 / result * thread_num` と
`throughput[tps] = result` を続けて出す。thread 数が固定の campaign では latency は throughput の恒等変換で、
独立な機序信号ではない。`orchestrator/critic/digest.py` の `INDICATORS` / `HIGHER_IS_BETTER` から外し、
表・軸の限界効果・`_fmt` から消えた。WAL の `bench_done.leading_indicators.latency_ns` は CC 本来のデータとして残す
(b10 sweep の `representative_latency_ns` や 8c の役割 payload が読む)。恒等変換の主張は「CCBench の通常出力では」に
限定する — `benchparse.throughput_tps` の fallback (`commit_counts_/actual_extime`) は batch を含まず丸めも違う
(段 3 レンズ A 所見 5)。

**(b) 偶数有効 reps の `abort_rate` / `latency_ns` を throughput と同じ中央値演算にした。** 変更前は
`orchestrator/calibrator/runner.py` の 2 経路 (`capture_measure_point` 内 `open_measurement_point` と
`measure_point`) が `median = sorted(tps)[n // 2]` (偶数では上側中央) に最も近い rep を代表とし、その rep の
abort_rate / latency_ns をそのまま入れていた。一方 `ScalePoint.throughput` と pipeline の `median_tps` は
中央 2 点の平均である。T-2588 の走行 (2 反復 `[727985, 710664]`) では headline 719324.5 tps に対し abort 7.75% /
latency 5494.6 ns が速い側の 727985 の rep から取られていた (`1e9*4/727985 = 5494.62` で検算一致)。
変更後は helper `_summarize_rep_results` が両経路で使われ、有効 throughput の個数が偶数なら throughput 順の
中央 2 rep の abort_rate / latency_ns を算術平均 (`model._median` の 2 要素) にする。**一方でも None なら None**
(P3')。奇数有効 reps と、counters / walltime / maxrss の単一 rep field は現行の規則 (上側中央、同値なら実行順で先)
のまま — 5 field の値は変更前と同一である (段 6 レビュー A 所見 2 が現物で確認)。

## 2. 裁定 (段 4) — 何を選び、何を退けたか

| 争点 | 裁定 | 理由 |
|---|---|---|
| (b) の修正形 | 案 A' = abort_rate / latency_ns だけを中央 2 rep の平均にする | 案 B (単一 rep のまま tie-break) は偶数で必ず tie になり規則が全て。案 C (throughput 順と独立な per-rep 中央値) は奇数の意味が変わる。案 A (counters 等も「実行順が先」の rep へ) は perf_preflight の counter_status 分類と calibrator の飽和点・下限点選択に届く (段 3 レンズ A 所見 2 / B 所見 5) ので本題の外 |
| None 混在 | P3' = 両方非 None のときだけ平均 | 片側の値を採る P3 は「同じ rep 集合・同じ演算」に例外を作り、screening の欠損時挙動も変える (レンズ A 所見 4) |
| 不変条件 | verifier の判定規則・fitness (`median_tps`) の式・certified の条件 (全 verify 通過) は不変。**certified 集合が不変とは主張しない** | bench-first screening (`pipeline.py:2366-2375`) は abort_rate を読む。baseline も同じ規則で集約されるが比は保存されず、偶数有効 reps の境界事例で screen-reject ↔ verify 送りが両方向に入れ替わりうる (レンズ A 所見 1 / B 所見 4 が反例で示した)。どちらの向きでも verify を経ずに certified にはならない (規律 2 不変)。screening の改変・screening 用の新テストは足さない (scope 外) |
| role 文書 | 触らない (残件) | `.claude/agents/critic.md:14,26-27,36` と `critic-experiment.md:36-37` は latency を独立指標として列挙・帰属例に使う。role 入力を変えると K0/K1 アームの条件が黙って変わる (T-2703 と同型の射程裁定が要る)。B-4 事前登録は発効前 draft で hash 欄は未記入なので凍結 pin は無い。**role bytes を据え置いても digest 自体が変わるのでアーム入力不変とは言えない** (レンズ A 所見 6) |
| 8c の役割 payload | 触らない (残件) | `p3_autonomous_workload_trial._metric_projection` / `s8c_generation_projection` の閉列挙は D118 系の裁定で固定。latency_ns の key は残り、偶数 reps の値は今後の測定で新しい集約になる |
| 過去 WAL / T-2588 の人手射影 | 直らない | digest は保存済み `leading_indicators` を読み再集約しない。T-2588 の 7.75% は旧集約の値として残る。完了条件は「critic digest と今後の runner 集約」に限る |

段 4 で撤回した親の主張: 「P3' は None を現行より増やす方向にしか動かさない」— 同値 tie に反例がある
(実行順 `(80,None),(80,.1),(80,.1),(80,.9)` → 旧 None / 新 .1、段 6 レビュー A 所見 1)。裁定 4 は両方向の変化を
既に許容しているので実装は不変。

## 3. consumer / producer の列挙 (段 1 + 段 3 の補正)

- digest 経由: `p3_s4_loop.make_critic_digest` → critic (claude_projected_provider / p3_b4_closed_critic、
  digest は非空文字列としてしか検査されず列を要求しない)、`online_digest.py`、`p3_b4_wiring_probe.py`、
  `search_baselines.py` (throughput のみ)、`backoff_sweep_report.py` (throughput/abort_rate/ipc、latency 不使用。
  `abort_rate or 0` で None を 0% と描く既存挙動は別件)
- WAL `leading_indicators` 直読 (digest を経ない): `p3_autonomous_workload_trial._metric_projection`、
  `s8c_generation_projection`、`autonomous_trial_completeness`、`layer3_report` (object passthrough)、`guided.py`
  (誘導 WAL へ複写)、`backoff_extended_sweep*` (`representative_latency_ns`、reps=5)、
  `plot_b10_extended_backoff.py` (5 反復必須、WAL latency と throughput の逆数関係を検査 — 奇数なので不変)、
  `plot_a2_certification.py` (abort_rate の範囲検査)、`s8b_*` placeholder、`pipeline.py:2366-2375` の screening
- 偶数有効 reps になりうる producer: `p3_s4_loop.default_perf` / `p3_kickoff` / `p3_s4_red` / `demo` /
  `p3_autonomous_workload_trial` (reps=2)、`between_run_floor.py` と `pegasus_floor_scoping.py` (WITHIN_REPS=10、
  floor は `pt.throughputs` から、abort_rate は表示・記録のみ)、calibrator 既定 `sweep_reps=3` / `noise_reps=10`。
  要求 5 reps でも 1 rep 失敗で有効 4 になる (偶奇は要求数でなく有効数)
- pin 閉包: `runner.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` (HEAD blob 束縛) と source closure 列挙の
  member、`digest.py` は `p3_b4_closed_critic.projection_closure_manifest` / `p3_b4_raw_record_producer` の member
  (実行時 hash、記録済み pin なし)。calibration 成果物の path/SHA pin (`env_contract.py`) は既存 JSON を変えない

## 4. 実測

- 焦点走 (変更 module を参照する test 43 file + `test_plain_runner_coverage.py`、tip 106c0ec04、計算ノード
  request 1963.nqsv): 6135 passed / 12 skipped / 0 failed (290 s)
- 変異 matrix (`mutation/`): まず probe 走 (8 件を SURVIVED 登録、runner argv = `test_calibrator.py` + `test_critic.py`、
  tip 106c0ec04) で観測 node を集めた — M1/M2 は calibrator 6 node、M3/M4/M5 は 2 node、M6 は direct 側 3 node、
  M7 は critic 5 node、等価変異 M8 は calibrator 0 node。runner.py を変異させた M1〜M6 と M8 では
  `test_critic.py` の admission 系 46 node が追加で赤になり、その集合は 7 変異で完全一致した
  (runner.py は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の HEAD blob 束縛 → contract-loader-drift。
  段 6 レビュー B 所見 7 のとおり検出ではない)。そこで本走は spec を 2 本に分けた (fix commit d586abff5):
  runner 用 (M1〜M6 KILLED 期待 = probe の calibrator 観測 node、M8 SURVIVED、argv = `test_calibrator.py`) は
  **baseline PASSED・6/6 KILLED・M8 SURVIVED・MISMATCH 0・期待 node 完全一致**、digest 用 (M7、argv =
  `test_critic.py`) は **baseline PASSED・1/1 KILLED・MISMATCH 0**。全件が構造化値の pin で受理集合の変化は
  観測しない (DW-M03/M08 の diagnostic sensitivity pin として別枠)。probe の観測はレビュー B の机上予測と
  node 単位で一致した
- 全史 provenance 監査: 106c0ec04 で 10603 件・新規違反なし (Pegasus request 1944.nqsv)、d586abff5 で 10604 件・
  新規違反なし (login node bounded local)
- 受入全走: 本記録 commit を含む tip に対して land 前に 1 回だけ投入する。README 作成時点では未実施

## 5. 残件 (裁定パッケージ候補、本 wave では触らない)

1. role 文書の latency 記述 4 箇所 (`.claude/agents/critic.md:14,26-27,36`、`critic-experiment.md:36-37`) —
   digest と食い違う。役割入力の変更なので K0/K1/B-4 の射程裁定と同時に扱う (T-2703 と同型)
2. 8c の役割 payload (`_PERF_KEYS` / `_SOURCE_METRIC_KEYS` の latency_ns) — D118 の閉列挙。外すなら別裁定
3. counters / walltime / maxrss の代表 rep は偶数で上側中央のまま — perf のある環境では llc/ipc 列が速い側に寄る。
   平均化は perf_preflight の分類と calibrator の点選択に届くので別 wave
4. `backoff_sweep_report.py` が None の abort_rate を 0% と描く既存挙動
