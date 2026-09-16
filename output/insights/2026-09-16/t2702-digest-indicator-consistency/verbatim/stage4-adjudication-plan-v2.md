# [T-2702] plan v2 (親の段 4 裁定を反映、2026-09-16 20:35 JST)

段 2 plan (`plan-v1.md`) と段 3 の 2 レンズ (`consult-A.md` / `consult-B.md`) の所見を裁定した結果。実装子はこの v2 を正として、v1 と食い違う点は v2 に従う。

## 裁定の要点 (何が変わったか)

1. **(P1) を案 A' へ縮める。** 平均化するのは `abort_rate` と `latency_ns` の 2 field だけ。`counters` / `walltime_s` / `maxrss_kb` の単一 rep field は**現行の代表 rep 規則をそのまま保つ** (偶数有効 reps では上側中央 rep = `sorted_tps[n//2]` に最も近い rep を実行順で最初に見つけたもの)。理由: consult A #2 / B #5 — 単一 rep field の代表を変えると perf_preflight の counter_status 分類と calibrator の飽和点・下限点選択にまで届き、本題 2 点の外。無偏な単一 rep 規則は存在しないので「実行順が先」の主張も撤回。
2. **(P3) を P3' (厳格) へ変える。** 偶数有効 reps では、中央 2 rep の `abort_rate` が**両方**非 None のときだけ算術平均、どちらか一方でも None なら None。`latency_ns` も同じ。理由: consult A #4 — 片側の値を採ると「同じ rep 集合・同じ演算」の保証に例外ができ、screening の欠損時挙動 (None → 曖昧として verify) も変わる。P3' は None を現行より増やす方向 (verify 側) にしか動かさない。
3. **奇数有効 reps は現行と bytes 同一** (代表 rep の `abort_rate` / `latency_ns` をそのまま)。偶奇は要求 reps でなく**有効 throughput の個数**で決める。同値 tie は現行の `min(valid, key=abs(tps - sorted_tps[n//2]))` (実行順で先) を保つ。
4. **不変条件の言い直し** (consult A #1 / B #4 を real として採用): verifier の判定規則・fitness (`median_tps`) の式・certified の条件 (全 verify 通過) は不変。ただし bench-first screening (`pipeline.py:2366-2375`) は `abort_rate` を読むので、偶数有効 reps の境界事例では screen-reject ↔ verify 送りが入れ替わりうる (どちらの向きでも verify を経ずに certified にはならない → 規律 2 は緩まない)。「certified 集合が不変」とは主張しない。screening の改変・screening 用の新テストは足さない (scope 外)。
5. **(a) の恒等変換の言い方** (consult A #5): 「CCBench の通常出力 (`result.cc` の `displayTps`) では `latency[ns] = 1e9 * thread_num / throughput` で throughput 由来の量であり、独立した latency 計測ではない」。fallback 経路 (`commit_counts_/actual_extime`) には言及しない。
6. **(P2) 維持**: role 文書 (`.claude/agents/critic.md:14,26-27,36`、`critic-experiment.md:36-37`) は触らない。残件として記録する (裁定パッケージ候補)。8c の役割 payload (`p3_autonomous_workload_trial._metric_projection`、`s8c_generation_projection` の閉列挙) も触らない (consult B #2、残件)。過去 WAL・T-2588 の人手射影は直らない (consult B #3、完了条件は今後の測定に限る)。

## 変更計画 (file:line 粒度、v1 からの差分込み)

### 1. `orchestrator/critic/digest.py`
- `:7-13` module docstring: 指標列挙を throughput / abort_rate / llc_miss / ipc の 4 つにし、帰属例を latency に依らないものへ書き換える (例: 「BACK_OFF 0→1 で throughput が下がるのに abort_rate がほぼ不変なら、backoff は競合を減らしておらず待ち時間のコストだけを払っている、と読める。cache miss / IPC で機序を補強する」)。latency を出さない理由を 1〜2 行で書く (上記 5 の言い方)。
- `:62-64` `INDICATORS` と `HIGHER_IS_BETTER` から `latency_ns` を削除。残る順序は throughput_tps, abort_rate, llc_miss_rate, ipc。
- `:1220-1221` `_fmt` の latency 分岐を削除。
- 他 (`:779` 射影、`:1186-1191` 軸集約、`:1264-1280` 表・軸描画) は `INDICATORS` に追随するので変更なし。WAL の latency を落とす処理は加えない。

### 2. `orchestrator/calibrator/runner.py`
- `:41` の model import に `_median` を追加。
- `capture_measure_point` (`:803`) より前に private helper `_summarize_rep_results(rep_results)` を置く。返値は `(counters, walltime_s, maxrss_kb, abort_rate, latency_ns)`。処理:
  1. `valid = [r for r in rep_results if r[0] is not None]` (元の実行順を保つ)。
  2. `valid` が空なら現行どおり `rep_results[-1][1:]` を返す (空 list は呼出元が例外で排除済み)。
  3. 代表 rep (単一 rep field 用) は**現行と同じ**: `throughputs = sorted(r[0] for r in valid)`, `median_ref = throughputs[len(throughputs) // 2]`, `rep = min(valid, key=lambda r: abs(r[0] - median_ref))`。`counters, walltime_s, maxrss_kb = rep[1], rep[2], rep[3]`。
  4. 有効数が奇数なら `abort_rate, latency_ns = rep[4], rep[5]` (現行と同一)。
  5. 有効数が偶数なら、`(index, r)` を throughput で stable sort し中央 2 要素 `lo, hi` を採る。`abort_rate = _median([lo[4], hi[4]])` を **両方が非 None のときだけ**計算し、どちらかが None なら None。`latency_ns` も同様。`_median` の 2 要素は算術平均なので案 A' と一致する。
  6. helper は `_median` 以外の新規依存を持たない。`digest._mean` は import しない。
- `:1050-1060` (`open_measurement_point` 内) と `:1287-1304` (`measure_point` 内) の代入を helper の返値に置き換える。直前の全失敗判定・直後の `rep_observations` コピーは維持。deferred 側の helper 呼出しは `open_measurement_point` の中に残す。
- throughputs の蓄積順、例外処理、strict mode、完全性検査、returncodes、timestamps、raw counter 証跡、fitness 計算、verifier は変更しない。

### 3. `orchestrator/calibrator/model.py`
- `:68-72` のコメント: `counters` / `walltime_s` / `maxrss_kb` は「代表 rep (throughput の中央値に最も近い rep、偶数有効 reps では上側中央) 由来」、`abort_rate` / `latency_ns` は「throughput と同じ中央値演算: 奇数有効 reps は中央 rep の値、偶数は中央 2 rep の算術平均 (一方でも欠損なら None)」と書き換える。
- `leading_indicators()` docstring (`:88-93`): `latency_ns` は WAL に残す CC 本来のデータだが、CCBench の通常出力では throughput 由来の量なので critic digest は列に出さない、と 1 行足す。
- `_median` (`:236-242`) は変更しない。

### 4. テスト
**`orchestrator/tests/test_critic.py`** — 既存 4 件の更新 + 新規 1 件:
- `:667` `test_load_sorts_by_throughput_and_marginal_back_off`: `"latency_ns" not in bo.means` を断言。`:647` の帰属コメントも latency に依らない文へ。
- `:683` `test_no_wait_axis_is_categorical_LT`: latency 不在と abort_rate の L=0.40 / T=0.50 を断言。
- `:729-732` `test_load_workload_uses_committed_retry_attempt_only`: 期待辞書を明示の 4 key に。
- `:803` `test_load_workload_preserves_legacy_commit_without_build_attempt_id`: 期待辞書を明示の 4 key に。
- 新規 `test_digest_omits_latency_from_projection_table_and_axes` (`:806` 付近): WAL fixture は 5 指標 (latency 含む) を保存。`GenomeLI.li` と全 `AxisEffect.means` が明示した 4 key、`render_text` のヘッダが `genome | throughput_tps | abort_rate | llc_miss_rate | ipc`、本文に `latency` が無い、WAL の `bench_done.leading_indicators.latency_ns` は残る、`HIGHER_IS_BETTER` が明示 4 key、を断言。期待辞書は `INDICATORS` から組み立てない (再導入変異を見逃す)。

**`orchestrator/tests/test_calibrator.py`** — 新規。fixture は `_completed_process(0, stdout=...)` を rep ごとに差し替える iterator 方式。`measure_point(...)` と `capture_measure_point(...).open()` を**別 node** で走らせる (parametrize id は ASCII のみ)。stdout は `throughput[tps]` / `abort_rate` / `latency[ns]` / `maxrss` を明示。`use_perf=False`。
- `test_measure_point_even_reps_average_central_indicators[direct|deferred]`: 実行順 `(tps, abort, latency, maxrss)` = `(400,.9,10000000,100),(100,.8,40000000,200),(300,.6,14000000,300),(200,.2,20000000,400)`。期待: `throughputs` は元順序、`throughput == 250`、`abort_rate == 0.4`、`latency_ns == 17000000`、`maxrss_kb == 300` (上側中央 rep = tps 300 の rep、現行規則)。2 reps `(200,.2,20000000,400),(300,.6,14000000,300)` も同じ node 内で確認 (throughput 250 / abort .4 / latency 17M / maxrss 300)。
- `test_measure_point_odd_reps_preserve_legacy_values[direct|deferred]`: (i) 3 reps 相異なる tps `(300,.3),(100,.1),(200,.2)` → 中央 rep (tps 200) の abort .2・latency・maxrss。(ii) 5 reps。(iii) 同値 tie `[200,200,200]` で abort を `.1,.2,.3` と変える → 実行順で最初 (abort .1) を採る。期待値は手計算の固定値で書き、新 helper を期待値計算に使わない。
- `test_measure_point_even_reps_none_indicator_is_none[direct|deferred]`: 中央 2 rep の abort が `(None, x)` / `(x, None)` / `(None, None)` → いずれも None、`(0, x)` → `x/2`。latency も同じ。None fixture は該当行を省き、abort の counts fallback (`abort_counts_`/`commit_counts_`) も成立させない。外側 rep には値を置き、中央外から補完しないことを確認。
- `test_measure_point_parity_uses_valid_reps_not_requested[direct|deferred]`: 要求 5 で 1 rep が非 0 rc (throughput None) → 有効 4 = 偶数の規則、要求 4 で 1 rep 失敗 → 有効 3 = 奇数の規則。
- `test_measure_point_no_valid_reps_keeps_last_parsed_fields`: 有効 0 件なら最後の解析済み rep の 5 field を保持 (現行)。全実行失敗の例外は既存のまま。
- 既存 `test_scalepoint_leading_indicators` (`:165-174`) は変更しない (WAL 5 key の維持確認)。

### 5. 変異事前登録 (親が実装後に走らせる。実装子は走らせない)
| # | 位置 | 変異 | 期待 | 赤になる test |
|---|---|---|---|---|
| M1 | `runner._summarize_rep_results` | 偶数の abort_rate を平均でなく上側中央 rep の値に戻す | KILLED (diagnostic sensitivity pin) | even_reps_average (abort .6≠.4) |
| M2 | 同 | 偶数の latency_ns を平均でなく上側中央 rep の値に戻す | KILLED (diagnostic sensitivity pin) | even_reps_average (latency 14M≠17M) |
| M3 | 同 | 片側 None のとき残る側の値を返す (P3 の旧案) | KILLED (diagnostic sensitivity pin) | even_reps_none |
| M4 | 同 | 奇数の tie-break を stable sort の中央要素に変える | KILLED (diagnostic sensitivity pin) | odd_reps_preserve (tie ケース) |
| M5 | 同 | 偶奇を有効数でなく要求 `reps` (= `len(rep_results)`) で決める | KILLED (diagnostic sensitivity pin) | parity_uses_valid_reps |
| M6 | `measure_point` 側だけ helper を外し旧 inline 選択へ戻す | KILLED (diagnostic sensitivity pin) | even_reps_average[direct] のみ (deferred は緑) |
| M7 | `digest.INDICATORS` に `latency_ns` を再挿入 | KILLED (diagnostic sensitivity pin) | test_digest_omits_latency… |
| M8 | helper 内の等価変異 (例: `list(...)` → `[*...]`) | SURVIVED (harness 正例) | なし |

全件が構造化値の pin であり、受理集合の変化を観測する変異は無い (DW-M03/M08 の「diagnostic sensitivity pin」として別枠記録)。期待 node は実装後に親が probe で固定する。

## 実装子への制約 (再掲)
- 編集は上記 4 file だけ。docs (`.md`)・role 文書・`pipeline.py`・`s8c_*`・CCBench・schema は触らない。commit しない。
- 既存テストの期待値は上記 4 箇所以外変えない。fixture に現行 hash を焼き込まない。
- テストは `tools/run_tests.py` と `python -m pytest` を使わず、`PYTHONPATH=. python3 orchestrator/tests/test_calibrator.py` / `... test_critic.py` の自走 harness で走らせ、nodeid と結果を報告する。走らせられなければ「実装済み・未実走」と書く。
