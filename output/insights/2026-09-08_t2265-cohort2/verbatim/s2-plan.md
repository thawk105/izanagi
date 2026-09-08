## 実装前提と設計裁定

対象 HEAD は `cc9bba523ac7804aadb7891d686bf4c925789a3f`、tracked tree は clean である。

推奨する実装は、単純な「終了時の部分窓 flush」ではなく、次の count-closed terminal flush である。

1. nominal `extime=5` 秒経過時に main thread が trace 専用の terminal request を立てる。
2. worker は停止せず、leader が次に `window_commits >= 10000` を満たした時点で terminal event を 1 件記録する。
3. terminal event では backoff 更新、LCG 更新、割当を行わない。
4. main thread は terminal event 完了を待ってから `quit=true` にする。

これなら、受理された terminal event も `window_commits >= 10000` となり、全ての残存割当に後続窓を与えられる。commit が永久停止した場合は event を捏造せず run timeout として成果物を不成立にする。

親 P3 の「部分窓を flush」はこの保証を持たない。要求どおり実装骨格は後述するが、採用してはならない。

## S2: patch C の改訂

現行箇所は `patches/cicada-adaptive-counterfactual.patch:385-395` の cap 判定、`:283-373` の trace record/state、`:435-448` の event 作成、`:612-678` の ring 追加、`:702-707` から始まる `leaderBackoffWork` hunk である。

時間 cap は 0 にしてはいけない。現行意味では 0 は無効ではなく `BACKOFF_UPDATE_US` へのフォールバックである。cohort 2 では signed 64 bit 最大値 `9223372036854775807` us を使い、事実上無効化する。この値は現行 `patches/cicada-adaptive-counterfactual.patch:205-213` の条件、すなわち非負整数かつ 0 または `BACKOFF_UPDATE_US` 以上を満たし、unsuffixed decimal としても `long long` に収まる。

巨大 cap との乗算 overflow を避けるため、`:391-395` は次の同値な除算比較へ変える。`clocks_per_us_ > 0` は既存実行契約である。

```diff
 const size_t cap_us =
     kCountCapUs == 0 ? kUpdateBackoffUs : kCountCapUs;
 if (committed_txs - last_committed_txs_ >= kCountWindow ||
-    elapsed >= clocks_per_us_ * cap_us)
+    elapsed / clocks_per_us_ >= cap_us)
   return true;
```

trace は v3 とし、terminal event を通常更新と区別する。

```diff
 #if BACKOFF_TRACE
 struct izanagi_backoff_trace_record {
   ...
+  int izanagi_backoff_trace_terminal_flush;
 };

 struct alignas(64) izanagi_backoff_trace_state {
   ...
   uint64_t izanagi_backoff_trace_updates = 0;
+  uint64_t izanagi_backoff_trace_flushes = 0;
   uint64_t izanagi_backoff_trace_dropped = 0;
+  std::atomic<bool> izanagi_backoff_trace_terminal_requested{false};
+  std::atomic<bool> izanagi_backoff_trace_terminal_recorded{false};
 };
 #endif
```

通常 event は従来どおり controller update と LCG 割当を表し、`terminal_flush=0` とする。terminal event は `terminal_flush=1`、numeric trigger 3、`assigned_invert=-1` とし、割当を持たないことを sentinel で表す。`recommended_delta_sign=0`、`inversion_realized=0`、`both_actions_feasible=0` は terminal では非適用値であり、解析器は利用しない。

`leaderBackoffWork` の count 条件成立後、通常の `update_backoff_at` より前へ次の骨格を置く。

```cpp
#if BACKOFF_TRACE
if (izanagi_backoff_trace_terminal_requested()) {
  backoff.izanagi_backoff_trace_record_terminal(
      sample_now, sum_committed_txs);
  izanagi_backoff_trace_mark_terminal_recorded();
  return;
}
#endif
backoff.update_backoff_at(sample_now, sum_committed_txs);
```

`izanagi_backoff_trace_record_terminal` は `last_time_` と `last_committed_txs_` から窓を作るが、これらの controller state、`Backoff_`、`adaptive_step_`、`ceiling_`、`backoff_step_policy_state_` を変更しない。特に policy 2 の LCG は terminal event では進めない。

正確な終了 handshake は patch C に新しい `common/runner.hh` hunk を加え、upstream `external/ccbench/common/runner.hh:294-310` を次の形にする。

```diff
 storeRelease(start, true);
 for (std::size_t i = 0; i < FLAGS_extime; ++i) { sleepMs(1000); }
+#if BACKOFF_TRACE && BACKOFF_COUNT_WINDOW > 0
+Backoff::izanagi_backoff_trace_request_terminal();
+while (!Backoff::izanagi_backoff_trace_terminal_recorded()) {
+  _mm_pause();
+}
+#endif
 storeRelease(quit, true);
 for (auto& th : thv) th.join();
```

この追加は `#if BACKOFF_TRACE` の first branch 内だけにあり、`BACKOFF_TRACE=0` の性能 build と correctness certification buildからコンパイル時に消える。必要な `<atomic>` と `_mm_pause` は既存 include で供給されるため include 追加は不要である。

親案どおり部分窓を即時 flush するなら、上の request を count gate の成立前に処理し、その時点の commit 差を記録すればよい。

```cpp
#if BACKOFF_TRACE
if (izanagi_backoff_trace_terminal_requested()) {
  backoff.izanagi_backoff_trace_record_terminal(
      rdtscp(), sum_committed_txs);  // 0 もありうる
  izanagi_backoff_trace_mark_terminal_recorded();
  return;
}
#endif
```

これは最後の割当に following を作るが、`window_commits=0` を構成上排除できず、短い exposure による rate の高分散も作る。したがって実装候補としては明示するが採らない。

trace summary は意味を分離する。

- 通常 controller update が N 件なら `updates=N`。
- terminal record は controller update ではないため `flushes=1`。
- `seq` は通常 event が `0..N-1`、terminal event が `N` で連続する。
- drop がなければ `retained=N+1`、`dropped=0`。
- parser は `updates + flushes == retained + dropped` を検査し、cohort 2 ではさらに `flushes=1`、`retained=N+1`、terminal が末尾だけであることを要求する。
- ring overwrite が起きた成果物は従来どおり不適格であり、位置除外で救済しない。

出力例は次の契約にする。

```text
IZANAGI_BACKOFF_TRACE v=3 ... trigger=1 ... assigned_invert=0 ... terminal_flush=0
IZANAGI_BACKOFF_TRACE v=3 ... trigger=3 ... assigned_invert=-1 ... terminal_flush=1
IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=N flushes=1 retained=N+1 dropped=0
```

patch C が `common/runner.hh` も触るため、`tools/pegasus/probes/t2187_adaptive_const_probe.py:723-759` の「A/B/C は同じ path 集合」契約は、C だけ exact 3 path

```text
cmake/Options.cmake
include/backoff.hh
common/runner.hh
```

を要求する形へ変える。任意の superset は受理しない。

`patches/README.md:288-320` も、2 file という記述、trace v2、extime 3 固定、認証 exact 2 cell を更新する。

## S3: cohort 2 の cell と観測長

cohort 2 の exact 12-field cell は次の 3 本とする。新 label にして cohort 1 との取り違えを文字列段階で閉じる。

```text
cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0
cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1
cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2
```

Python の comma-separated literal は次である。

```text
cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0,cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1,cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2
```

`.pbs` の plus-separated literal は comma を plus に置き換えた逐語とする。

観測長は nominal `extime=5` 秒とする。実際の停止は「5 秒経過後の最初の count closure」であり、通常は段 1 実測の窓長 2.5 ms から 10.8 ms 程度だけ延びる。停止まで commit が再開しない場合の有限上限はなく、外側の per-run timeout が成果物不成立として止める。

driver の変更は次のとおり。

- `tools/pegasus/probes/t2187_adaptive_const_probe.py:59-64`: 既存 `TRACE_SCHEMA_VERSION=v3` を残し、cohort 2 専用 `COHORT2_TRACE_SCHEMA_VERSION="izanagi-dynamic-backoff-trace/v4"` を追加する。
- `:84-86`: `docs/backoff-counterfactual-cohort2-preregistration.md` への別 path を追加する。v2 path は変更しない。
- `:272-276`: 既存 `COUNTERFACTUAL_TRACE_CELLS_TEXT` をそのまま残し、新しい `COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT` と parsed tuple を追加する。
- `:691-759`: patch C の exact path 集合を上記 3 path に変更する。
- `:935-959` と `:1026-1121`: trace v1/v2 をそのまま受理しつつ v3 record、trigger 3、`terminal_flush`、summary の `flushes` を追加する。版と field の連言を exact に検査し、v1/v2 へ terminal field が付く形、v3 で field が欠ける形、terminal が末尾以外にある形を拒否する。
- `_validate_backoff_trace_contract` `:2732-2758`: table value を `(expected_cells, expected_extime)` にし、既存 2 literal は extime 3、新 literal は extime 5 と exact 対応させる。workload、threads、rep、reps は不変。
- `_artifact_contract_metadata` `:2761-2791`: cohort 1 の述語を一字も緩めず、その後へ cohort 2 の exact cells、axes、extime 5 の独立分岐を置く。cohort 2 だけ schema v4 と新事前登録 SHA を記録する。どちらにも一致しない trace に事前登録 fieldを付けない。
- `:3304-3355`: metadata が返した schema と prereg SHA を top level と各 row にそのまま投影する。
- `:3430-3495`: parser が返した terminal event と拡張 summary を無加工で成果物へ保存する。

`.pbs` の変更は次のとおり。

- `tools/pegasus/probes/t2187_adaptive_const_probe.pbs:21` の次に cohort 2 raw literalを追加する。既存 raw literalは不変。
- `:67-87` に `EXTIME=${IZANAGI_T2187_EXTIME:-3}` を追加し、ASCII positive integerを検査する。
- `:149-156` の trace gate に第三の exact literal を加え、旧 2 literal には extime 3、新 literal には extime 5 を要求する。
- performance branch `:389-401` に `--extime "$EXTIME"` を追加する。現在は default 3 に暗黙依存している。
- 現行 `:415` は certification branch の `--extime 3` であって cohort trace の長さを決めていない。新 certification cell では後述の expected extime 5を渡せるよう `--extime "$EXTIME"` にするが、旧 certification cell は PBS gate で 3 のまま固定する。
- `:5` の `elapstim_req=00:40:00` は変更不要である。

現行 18 run の中央値 137.2 秒から、固定費を `137.2 - 18*3 = 83.2` 秒と見積もると、5 秒化後は `83.2 + 18*5 = 173.2` 秒である。段 1 の min/max に同じ36秒を足すと約171.9から174.7秒、terminal待ちは通常さらに11ms未満である。40分 walltime は十分であり、12 job は約3分ずつ、複数ノード同時投入なら queue を除く wall clock は最遅 job 程度になる。

## S4: cohort 2 専用解析 module

新規 path は `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py` とし、旧 `backoff_counterfactual_analysis.py` は変更しない。

写経単位は次のとおり。

- `backoff_counterfactual_analysis.py:98-119`: fail、SHA、exact type helper。
- `:121-179`: build、event、trace binding。ただし新 patch C digest、schema v4、terminal contractへ置換する。
- `:181-233`: cell identity と genome exact binding。cell label、cap、extime、patch C SHA、新事前登録 SHAだけを置換する。
- `:236-379`: row/artifact loader。18 row、3 x 3 x 2 axes、既存12 seed、各 policy 内 binary/genome一意性は継承する。
- `:382-428`: `_run_difference`。v2の位置除外と0 commit規則を逐語継承し、terminalをfollowing専用にする。
- `:431-565`: cluster summary、secondary、判定。`EQUIVALENCE_MARGIN`、t値、12 cluster 等重み、判定境界は変更しない。
- `:567-694`: public APIと副次層。module名、version、prereg SHAだけを cohort 2 にする。

位置除外は現行 `:386-399` と同じ順序を維持する。

```python
events = run["events"]
analysis_events = events[1:]
if any(event["window_commits"] == 0 for event in analysis_events):
    return inconclusive("window_commits_zero")
```

0 commit scan は subgroup membership より前に行い、terminal eventも含める。terminalの0 commitだけを除外したり、部分層だけを計算したりしてはならない。

event列を通常 event `e[0]..e[n-1]` と terminal `f=e[n]` とすると、v2位置除外後の式は次になる。

```text
Y[r,i] = ln(T[r,i+1] / T[r,i])  i = 1,...,n-2
Y[r,n-1] = ln(T[r,f] / T[r,n-1])
```

terminalは最後の `following` としてだけ使う。`Z[r,f]` は定義しない。割当数、割当率、`recommended_delta_sign`、`both_actions_feasible`、time blockのcurrent eventにはterminalを入れない。terminalをcurrentとして扱う実装はschema violationにする。

LCG検査は次の署名で row の適格性検査に入れる。

```python
def _validate_assignment_lcg(
    events: list[dict],
    *,
    seed: int,
    binding: str,
) -> None:
```

初期 `state=seed` から通常 eventごとに

```python
state = (
    state * 6364136223846793005
    + 1442695040888963407
) % (2**64)
expected = (state >> 63) & 1
```

を計算し、eventの `assigned_invert` とexact比較する。terminalではstateを進めず、`assigned_invert=-1` を要求する。

不一致は outcome上の `inconclusive` ではない。成果物の割当束縛違反として `_fail(...)` から `ValueError` を送出し、`analyze_counterfactual` は結果objectもdecisionも返さない。署名上の意味は「入力不適格として解析開始前に拒否」である。

通る正例は seed `5744733223455690259` である。

```text
initial state = 5744733223455690259
state 1 = 6518640240862848934  -> bit63 0
state 2 = 9241845631126672253  -> bit63 1
state 3 = 4137125854916374856  -> bit63 0
state 4 = 14162348237756801783 -> bit63 1
assigned_invert = [0, 1, 0, 1]
```

この4 eventの後に `assigned_invert=-1, terminal_flush=1` を置く正例をtest fixtureにする。通常eventの2番目を0へ反転した負例は `ValueError` になる。

新testは `orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py` とし、最低限次を持たせる。

- `test_assignment_lcg_accepts_exact_positive_sequence_and_rejects_one_bit_flip`
- `test_seq_zero_is_excluded_before_pairing_under_cohort2`
- `test_terminal_flush_is_following_only_and_does_not_consume_lcg`
- `test_terminal_zero_commit_makes_whole_primary_inconclusive`
- `test_nonterminal_events_require_count_trigger_and_count_window`
- `test_terminal_summary_requires_one_flush_and_contiguous_seq`
- `test_exact_cohort2_cells_extime_patch_and_preregistration_are_bound`
- `test_final_normal_assignment_changes_estimate_through_terminal_following_window`
- `test_tost_and_practical_superiority_constants_match_v2`

## S5: plot 拡張

`tools/plotting/plot_dynamic_backoff.py` は単一 `TRACE_CELLS` を全schemaへ使っているため、単にtupleへ3 labelを追加すると既存18-row artifactを54-rowと誤認する。次のexact set分離が必要である。

- `:57-61`: cohort 2 diagnostic schema v4を追加する。
- `:76`: `LEGACY_TRACE_CELLS`、`COHORT1_TRACE_CELLS`、`COHORT2_TRACE_CELLS` の3 exact tupleへ分け、schema/gridごとのclosed tableを作る。
- `:80-87`: cohort 1の3 policy labelとcohort 2の3新labelをcell specへ追加する。cohort 1はcap10240、cohort 2はcap9223372036854775807。
- `:89-97`: 12-field labelを`cell_format_fields=12`とし、別のexact `step_policy`表で0/1/2を検査する。11-fieldの明示policyなしと12-field policy 0を同一視しない。
- `_common_identity` `:219-299`: 現在の `extime_s == 3` hard pin `:254-257` は親 briefから漏れている。diagnostic contractからexpected extimeを渡し、旧setは3、新setは5を要求する。任意のpositive extime受理にはしない。
- `_parse_event` `:459-498`: 12-field eventでは4つのpolicy fieldをexact type/rangeで検査する。cohort 2ではさらに`terminal_flush`を要求し、terminal以外の`assigned_invert`は0/1、terminalだけ-1、triggerはterminalだけ`flush`を許す。
- `_parse_trace_run` `:524-599`: cell setを引数化し、cohort 2では通常eventが全てcount、terminalがexactly oneかつ末尾、`window_commits >= count_window`であることを検査する。
- summary `:561-566`: v1/v2は現行式を維持し、v3 terminalでは`updates + flushes == retained + dropped`、`flushes=1`、`retained=len(events)`、`dropped=0`を要求する。
- `_parse_diagnostic` `:602-662`: schema、grid spec、cell orderから1つのexact contractを選び、18 row集合を作る。既存schemaの受理を壊さない。
- `_diagnostic_values`とfigure `:1283-1346`: global `TRACE_CELLS` ではなく、parsed artifactのcell orderを使う。新label用の色もexact mapへ追加する。

既存CLIのperformance/diagnostic identity一致は緩めない。したがって、cohort 2 diagnosticを実際に既存の3図CLIへ渡すには、同じrepo head、patch stack、driver、extime 5のperformance artifactも必要である。S7の12 trace jobだけではこの条件を満たさない。S5で保証できるのはparser、trajectory、diagnostic panelの理解までで、既存performance artifactとの不正な結合は拒否する。

`orchestrator/tests/test_plot_dynamic_backoff.py` では既存fixtureを残したまま、cohort 1 v2 event fixtureとcohort 2 v3 terminal fixtureを別に追加する。

## S6: policyが0でないcellの直列性認証

追加するexact certification cellsは次の2本である。

```text
cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1
cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2
```

`tools/pegasus/probes/t2187_adaptive_const_probe.py:227-248` に2つの `Cell` 定数を追加し、`CERT_CELLS` を旧2件プラス新2件のexact tupleにする。`CERT_CLAIMS` も同じ4 keyのexact mapにし、新claimはrecords 1,000,000、threads 48、extime 5、3 workloads、8 slots、24 trace、policy値、policy 2のdefault compile seedを明記する。

`_certification_contract` `:1185-1283` はraw string allowlistとparsed `Cell` membershipの二重検査を維持する。cellごとのexpected extimeを

```python
CERT_EXTIME_BY_CELL = {
    CERT_TUNED_CELL: 3,
    CERT_DYNAMIC_CELL: 3,
    CERT_COHORT2_POLICY1_CELL: 5,
    CERT_COHORT2_POLICY2_CELL: 5,
}
```

としてexact比較する。threads 48、1 workload、reps 1、slot 0..7、24 result paths、予算条件は変えない。

受理形を増やすが、緩みは入れない。署名は次である。

- 許可されるraw literalは4本の列挙のみ。
- suffix、label、cap、policy、複数cell、空白差を含む別文字列は拒否する。
- parsed cellも`CERT_CELLS` exact membershipを通す。
- cellごとのextime対応をexactにする。
- workload、thread、slot、group24件、positive control、target verifier、identity、namespace、performance artifact bindingは不変。

通る正例:

```text
cells=cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1
workloads=balanced
threads=48
extime=5
reps-per-job=1
rep-index=0
```

落ちる負例:

```text
cells=cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775806:1:1:4:1:1
```

capが1違うため`certification-cell-mismatch`で拒否する。

`CERT_CELLS`だけでは足りず、次も追随する。

- `_validate_dynamic_certification_namespaces` `:879-902`: `cell == CERT_DYNAMIC_CELL` ではなく、列挙済み3 dynamic certification cellのmembershipでnamespaceを要求する。
- `_validated_certification_row` `:1985-2007`: cellを先に復元し、cell別extimeでworkload flagsと`extime_s`を検査する。
- `_certify_main` `:2847-2857`: performance identityのfull bindingを全dynamic certification cellへ適用する。
- payload `:2883-2917`: cell別extimeとclaimを記録する。
- `main` `:3248-3258`: policy 2のseed必須検査をperformance pathへ移す。certificationのpolicy 2は明示seedを禁止したまま、`genome_for`のdefault seedを使う。
- `.pbs:158-220`: cert raw allowlist、dynamic namespace判定、output namespace判定を4-cell exact setへ追随させる。
- `.pbs:415`: cell別の`EXTIME`を渡す。

認証buildは次の二重trace契約で別jobになる。

- `BACKOFF_TRACE=0`: adaptive diagnostic trace、terminal handshake、trace文字列、trace symbolは完全除去。
- `CCBENCH_TRACE=1`: serializability verifier用transaction traceは有効。
- cohort 2の反実仮想jobは逆に`BACKOFF_TRACE=1`の診断専用であり、certification jobとは同じbinaryでも同じrunでもない。

必要job数は、新cellごとに3 workloads x 8 slotsで24、2 cellで48 certification jobである。これに両cellを含む`BACKOFF_TRACE=0` performance artifactを作る1 jobが必要なので合計49 jobとなる。

既存認証ではverify相が87.1から458.9秒だった。extimeを3秒から5秒にするとtransaction trace量が概ね5/3倍になるため、単純比例ではverify約145から765秒、build/prologue込みで1 job数分から15分程度を見込む。各jobの外側walltimeは既存の2時間15分overrideを維持する。48本を十分なnodeへ同時投入した場合の実wall clockは最遅jobとqueue待ちで決まり、verify相のaggregateは約1.9から10.2時間である。

ただしpolicy 2 certificationはdefault seedのbinaryしか認証しない。cohort 2の12個のseed別binaryすべてをexact認証するなら、policy 1の24件にpolicy 2の12 seed x 24件を加えた312 certification jobと、seed別performance artifactが必要になる。さらにcohort 2の24 thread条件は現行certification contractの外である。最小変更の49 jobを「全cohort 2 binaryの認証」と表現してはならない。

## 既存成果物と凍結物の保持

次のpathは編集しない。

- `docs/backoff-counterfactual-preregistration.md`
- `orchestrator/campaign/backoff_counterfactual_analysis.py`
- `orchestrator/tests/test_backoff_counterfactual_analysis.py`

旧解析器の `PATCH_C_SHA256` `:33-40`、cohort 1 cells `:41-50`、extime 3 `:315-327`、位置除外と0判定 `:382-428` はそのまま残す。これにより既存12成果物の受理集合と判定は変わらない。

新patch CのSHAは新事前登録、driver新成果物、新解析器だけへpinする。旧成果物に記録された旧patch C SHAを現行file SHAへ書き換えたり、旧解析器に複数SHAを受理させたりしない。

## 追随が必要なliteral pinとtest

必ず編集する箇所は次である。

- `orchestrator/tests/test_dynamic_backoff_transitions.py:710-768`: patch fixtureに`common/runner.hh`をcopyし、C適用後のrunner本文を保持する。
- 同`:731-753`: pin、pin+A、pin+A+Bへのpatch C適用可否を3-path patchで再確認する。
- 同`:1145-1170`: changed path exact tupleを2本から3本へ変更し、runner hookがnumeric `#if BACKOFF_TRACE`内であることを検査する。
- 同`:1096-1102`: static assertを不変確認し、巨大capで除算比較になるtestを追加する。
- 同`:1326-1355`: patch側LCG literal pinは不変のまま維持する。
- 同`:1376-1432`: trace record versionをv3へ追随し、terminal sentinelを通常eventへ混ぜない。
- 同`:1492-1527`: `terminal_flush`、request flag、runner waitが`BACKOFF_TRACE=0` preprocessから消えることを追加する。
- 同`:1530-1536`: emitter期待値をv3 summaryへ変更する。
- `orchestrator/tests/test_t2187_adaptive_const_probe.py:38-56`: cohort 2 cellsとcert cellsのexact literalを追加する。
- 同`:1303-1334`: performance branchが`--extime "$EXTIME"`を渡すよう期待値を変更する。
- 同`:1611-1665`: `_applied_patch_stack`のC path集合を3本へ変更する。
- 同`:1728-1751`: certification正例を4cellへ増やし、負例を維持する。
- 同`:1754-1870`: v1/v2受理を残したままv3 terminal、summary、版混在の正負例を追加する。
- 同`:1947-2015`: cohort 2 artifact schema v4、4-cell claims、cell別extimeをpinする。
- 同`:2139-2206`: cohort 1 prereg metadata testを不変保持し、cohort 2 exact predicateと新SHAの別testを追加する。
- 同`:2227-2234`: policy 2 certificationのdefault seed受理と明示seed拒否を区別する。
- 同`:2247-2272`: PBSのseed、extime、cert raw allowlistへ追随する。
- 同`:2320-2400`: 新dynamic cert cellsにもnamespaceとperformance identityが必須であることをparameterizeする。
- 同`:2423-2460`: trace contractのextime対応を旧3、新5で検査する。
- 同`:2463-2520`: 「2 exact literals」を「3 exact literals」に変え、混合集合、欠落cell、wrong extimeを負例にする。
- 同`:2523-2539`: Python/PBS raw literalのbyte一致を3本へ増やす。
- 同`:2542-2597`: max capを持つ12-field cellのclassificationを追加する。
- `orchestrator/tests/test_ccbench_spawn_sites.py:923-945`: driver編集後のcert build sinkとmain build sinkの実行行を再導出し、説明の`exact 2 cell`を`exact 4 cell`へ更新する。
- 同`:2688-2716`: expected tupleと説明文の重複pinも同じ値へ追随する。
- `orchestrator/tests/test_plot_dynamic_backoff.py:23-60`: schema、cell set、config fixtureを追加する。
- 同`:75-117`: cohort 2 extime 5、schema v4、patch C identity fixtureを追加する。
- 同`:200-260`: producer trace fixtureへv2 policy eventとv3 terminal eventを追加する。
- 同`:388-448`: A+B、旧A+B+C、新A+B+Cのschema/identity受理を分ける。
- 同`:632-647`: terminal fields、summary、following-onlyをround-trip検査する。
- `patches/README.md:288-320`: 3 path、trace v3、terminal count flush、新cell、extime 5、cert exact 4 cellへ更新する。

変更不要だが静的に再確認するpinは次である。

- `orchestrator/tests/test_condition_meaning_gate.py:2537-2561`: patch Cのdefine集合はpolicyとseedの2つのまま。
- 同`:2564-2583`: CMake default literalも変更しない。
- `orchestrator/tests/test_backoff_counterfactual_analysis.py:21-50` と`:430-456`: cohort 1の旧patch C、v1/v2 prereg SHA pinは変更しない。

親 briefの`test_dynamic_backoff_transitions.py:1202`はtest開始位置ではなく、現物では`test_patch_c_cmake_cache_default_is_zero`内のpatch読込み行である。test自体は`:1193`開始である。

## 段5の所有分割

親案の3 unitを維持するが、path集合を次へ修正する。互いに素集合である。

- Unit A: patchとC++構造。
  - `patches/cicada-adaptive-counterfactual.patch`
  - `patches/README.md`
  - `orchestrator/tests/test_dynamic_backoff_transitions.py`

- Unit B: producer、PBS、certification、spawn pin。
  - `tools/pegasus/probes/t2187_adaptive_const_probe.py`
  - `tools/pegasus/probes/t2187_adaptive_const_probe.pbs`
  - `orchestrator/tests/test_t2187_adaptive_const_probe.py`
  - `orchestrator/tests/test_ccbench_spawn_sites.py`

- Unit C: cohort 2解析とplot consumer。
  - `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py`
  - `orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py`
  - `tools/plotting/plot_dynamic_backoff.py`
  - `orchestrator/tests/test_plot_dynamic_backoff.py`

親が先に新事前登録を凍結し、そのSHA、schema v4、3 cell literal、extime 5、terminal summary契約、patch Cの予定path集合を3 unitへ同じinterfaceとして渡す。Unit Aのpatch完成後に確定するpatch C SHAはUnit B/Cがliteralへ反映する。旧v2文書、旧解析器、旧解析test、condition gate testはどのunitも所有しない。

## 変異事前登録候補

| 変異 | 変異箇所 | 期待する赤 |
|---|---|---|
| cap比較を乗算へ戻す | `patches/cicada-adaptive-counterfactual.patch:391-395` | `test_cohort2_max_cap_uses_overflow_safe_comparison` |
| terminal request直後に部分窓を記録する | patch Cの新`leaderBackoffWork` hunk、現`:702-707`後 | `test_terminal_flush_waits_for_count_boundary`、`test_nonterminal_and_terminal_windows_are_commit_closed` |
| terminalでも`update_backoff_at`を呼ぶ | patch C新terminal branch | `test_terminal_flush_does_not_apply_assignment_or_advance_lcg` |
| runnerのrequest/waitを`#if BACKOFF_TRACE`外へ出す | patch C新`common/runner.hh` hunk、upstream`:297-300` | `test_trace_preprocesses_out_of_trace_zero_builds` |
| flushを`updates`へ加算する | patch C現`:364-368`と`:668-676`相当 | `test_parse_backoff_trace_accepts_exact_v3_terminal_summary` |
| v3 terminalの`assigned_invert`を0にする | patch C新terminal record | `test_terminal_flush_is_following_only_and_does_not_consume_lcg` |
| 解析器LCGの加算定数を1変える | 新解析moduleの`_validate_assignment_lcg` | `test_assignment_lcg_accepts_exact_positive_sequence_and_rejects_one_bit_flip` |
| terminalの0 commitをzero scanから外す | 新解析moduleの`_run_difference`、旧写経元`:399-406`相当 | `test_terminal_zero_commit_makes_whole_primary_inconclusive` |
| cohort 2のextimeを任意positiveで受理する | driver`:2738-2757`相当 | `test_backoff_trace_contract_binds_each_literal_to_its_exact_extime` |
| certificationをprefixやparsed値だけで受理する | driver`:1185-1199` | `test_public_certification_accepts_four_exact_cells_and_rejects_near_literals` |
| PBSからcohort 2 raw literalの一項を外す | `.pbs:149-156`相当 | `test_three_layer_trace_literals_are_byte_identical` |
| plotでterminalを中間位置に許す | plot`:459-498`と`:552-566`相当 | `test_cohort2_terminal_event_must_be_unique_and_last` |

runner hook削除とterminal requestを立てない変異は、どちらも同じ「terminal未生成」node集合で落ちるため冗長である。片方だけを本登録し、もう片方はprobe用に留める。

summaryの`flushes`削除と`retained=updates`への変更も、同じparser summary node集合になる可能性が高い。probeでnode集合が同一なら冗長として一方を落とす。

## 親briefへの攻撃

- P2の「capを観測長以上にすれば0 commitは構成上不可能」は通常窓にしか成立しない。部分flush、cap timerがmeasurement開始前から進む経路、nominal extime超過、commit停止中の終了で0が出る。巨大capとcount-closed terminalを組み合わせて初めて、受理eventについて構成上の非0を言える。
- P3はbrief`:39-40`で「extime後の最初の窓閉鎖まで」と「短い部分窓を作らない」と定める一方、今回の必須事項は「最後の部分窓をflush」としており相互に矛盾する。部分flushはrateの分母が短く高分散になり、固定count窓と異なる分布を最後の1対だけへ混ぜる。最後になる更新自体も先行割当の速度効果に依存し、持ち越しを含む。
- P3の部分flushで`updates`へevent数を足すと、`trace_summary.updates`がcontroller update数ではなくなり契約衝突する。`flushes`を別fieldにしなければならない。
- P4の「CのSHAはfileから算出されるのでliteral pinを壊さない」は不十分である。Cのbytes変更でも`_patch_stack_identity:691-720`のC SHAとstack SHAは変わり、新patch Dを足す場合と同じく成果物identityへ波及する。また`test_dynamic_backoff_transitions.py:1145-1170`はCのexact path集合をliteral pinし、`:1530-1536`はtrace v2をpinしている。
- patch Cに正確なrun終了hookを入れると`common/runner.hh`が第三pathになり、driver`:743-747`のsame-path検査、README`:288-290`の2 file記述も壊れる。P4のscope見積りから漏れている。
- P5は`CERT_CELLS`と`_certification_contract`だけでは成立しない。namespace、performance artifact identity、cell別extime、claims、group row/receipt validator、PBS raw gate、mainのpolicy 2 seed順序まで波及する。
- P5の最小48-job認証はpolicy 2のdefault seedと48 threadだけを認証する。12 seed別binaryと24 threadを含むcohort 2全体の認証ではない。
- P6は解析moduleだけに閉じない。producerが新prereg SHAとschema v4を付け、plotが新event/schemaを読む必要がある。特にplotの`extime_s == 3` pin `:254-257`はbriefの変更面から漏れている。
- `.pbs:415`はcohort traceではなくcertification branchのextimeである。trace performance branchは現状`--extime`を渡しておらずdefault 3に依存している。
- plotの波及はbrief記載の`:76/:87/:96/:474`だけではなく、`_common_identity:219-299`、row/grid検査`:524-662`、figure loop`:1283-1346`にも及ぶ。

## 静的検査

この段ではpytestを実走せず、緑も要求しない。段5での最低限の静的確認は、Python全編集fileの`ast.parse`、PBSの`bash -n`、patchの`git apply --stat`とhunk/path列挙、旧v2文書と旧解析器のSHAまたは`git diff --exit-code`、trace0 preprocess上のterminal文字列不在、spawn sink行番号のAST再導出で足りる。C++ build、pytest、計算nodeでのliveness、12 trace job、49 certification/performance jobの実測は親が行う。

## 総括

採るべき設計択一: 巨大有限capと、extime後の最初のcount closureを割当なしterminal eventとして記録する方式。部分窓より非0とfollowingを同時に構成保証できるため。
親briefのprovisional裁定のうち覆すべきものと根拠: P2の全event保証、P3の部分flush、P4の局所変更主張を覆す。terminal 0、rate偏り、第三patch pathとstack identity波及が現物上存在する。
実装できないと判断した項目と理由: 部分flushのまま0 commitを構成上排除すること、最小49 jobで12 seedかつ24/48 thread全binaryを認証すること、S7のtrace成果物だけを既存performance図へ結合することは、それぞれ停止時commit、cert exact axes、plot identity契約により不可能。