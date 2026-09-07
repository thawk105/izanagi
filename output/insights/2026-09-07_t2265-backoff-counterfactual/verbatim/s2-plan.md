## 前提と命名

これは brief v2 に対する段 2 の再起草であり、旧プランは流用しない。編集・実測・pytest・commit は行っていない。

`pin-closure.md` 冒頭の旧名 `BACKOFF_INVERT_STEP` ではなく、brief v2 を正本として次を採る。

- CMake cache option: `CCBENCH_BACKOFF_STEP_POLICY`
- C++ define: `BACKOFF_STEP_POLICY`
- 値域: `0 = stock`、`1 = 常時反転`、`2 = 更新ごとの決定的 1/2 割当`
- 既定値: `0`
- preimage: ccbench pin `511c9538...` + patch A + patch B
- patch C の編集対象: `cmake/Options.cmake` と `include/backoff.hh` のみ
- patch A、patch B、既存の四つの逐語 pin は変更しない

## patch C の CMake 配線

`patches/cicada-adaptive-counterfactual.patch:1-end` は、post-B の `cmake/Options.cmake` に次の二つだけを加える。

- patch B の option 群、`CCBENCH_BACKOFF_STEP_ADAPT` の直後に:

```cmake
set(CCBENCH_BACKOFF_STEP_POLICY 0 CACHE STRING "backoff step policy (0=stock, 1=invert, 2=randomized)")
```

- `ccbench_universal_definitions` の `BACKOFF_STEP_ADAPT=...` の直後に:

```cmake
BACKOFF_STEP_POLICY=${CCBENCH_BACKOFF_STEP_POLICY}
```

`include/backoff.hh` の patch B による macro 欠落検査群の末尾へ:

```cpp
#ifndef BACKOFF_STEP_POLICY
#error "BACKOFF_STEP_POLICY must be defined (0 = stock step policy)"
#endif
```

既存の `BACKOFF_TRACE` 用 `static_assert` の直後へ:

```cpp
static_assert(BACKOFF_STEP_POLICY == 0 ||
                  BACKOFF_STEP_POLICY == 1 ||
                  BACKOFF_STEP_POLICY == 2,
              "backoff step policy must be 0, 1 or 2");
```

policy 選択はすべて `#if BACKOFF_STEP_POLICY ...` とし、`#ifdef BACKOFF_STEP_POLICY` は作らない。policy 0 かつ trace 0 では、更新本体に追加される policy state、LCG、反転処理、診断変数をすべて前処理で落とす。

## 反転点と patch B への重なり

patch B の `patches/cicada-adaptive-dynamic.patch:315-357` にある該当部分は次のとおりである。これは逐語引用である。

```diff
+#if BACKOFF_STEP_ADAPT
+    if (gradient < 0)
+      new_backoff -= adaptive_step_;
+    else if (gradient > 0)
+      new_backoff += adaptive_step_;
+    else {
+      if ((committed_txs & 1) == 0 ||
+#if BACKOFF_DYN_CEILING
+          new_backoff == ceiling_)
+#else
+          new_backoff == kMaxBackoff)
+#endif
+        new_backoff -= adaptive_step_;
+      else if ((committed_txs & 1) == 1 || new_backoff == kMinBackoff)
+        new_backoff += adaptive_step_;
+    }
+#else
     if (gradient < 0)
       new_backoff -= kIncrBackoff;
     else if (gradient > 0)
       new_backoff += kIncrBackoff;
     else {
       if ((committed_txs & 1) == 0 ||
+#if BACKOFF_DYN_CEILING
+          new_backoff == ceiling_) // 確率はおよそ 1/2, すなわちランダム．
+#else
           new_backoff == kMaxBackoff) // 確率はおよそ 1/2, すなわちランダム．
+#endif
         new_backoff -= kIncrBackoff;
       else if ((committed_txs & 1) == 1 || new_backoff == kMinBackoff)
         new_backoff += kIncrBackoff;
     }
+#endif
 
     if (new_backoff < kMinBackoff)
       new_backoff = kMinBackoff;
+#if BACKOFF_DYN_CEILING
+    else if (new_backoff > ceiling_)
+      new_backoff = ceiling_;
+#else
     else if (new_backoff > kMaxBackoff)
       new_backoff = kMaxBackoff;
+#endif
```

C は次の三地点に重なる。反転そのものは二番目の一箇所だけである。

1. patch B `:313` の動的上限更新を閉じる `#endif` の後、`:315` の推奨差分生成より前に、policy が必要なときだけ pre-state を保存する。
2. patch B `:347` の `BACKOFF_STEP_ADAPT` 分岐を閉じる `#endif` の後、`:349` の clamp より前に、推奨差分を反転する。
3. patch B `:357` の clamp 完了後、`:358` の `Backoff_.store` より前に、trace 用の実現判定を行う。

post-B に対する中心差分は次の形に固定する。

```diff
 #endif
 
+#if BACKOFF_STEP_POLICY > 0
+    const double izanagi_backoff_step_policy_origin = new_backoff;
+#endif
+
 #if BACKOFF_STEP_ADAPT
     /* patch B の adaptive_step_ による推奨差分 */
 #else
     /* patch B の kIncrBackoff による推奨差分 */
 #endif
 
+#if BACKOFF_TRACE
+    const double izanagi_backoff_trace_recommended_delta =
+        new_backoff - izanagi_backoff_trace_backoff_before;
+    const int izanagi_backoff_trace_recommended_delta_sign =
+        (izanagi_backoff_trace_recommended_delta > 0) -
+        (izanagi_backoff_trace_recommended_delta < 0);
+#endif
+
+#if BACKOFF_STEP_POLICY == 1
+    const double izanagi_backoff_step_policy_delta =
+        new_backoff - izanagi_backoff_step_policy_origin;
+    new_backoff =
+        izanagi_backoff_step_policy_origin - izanagi_backoff_step_policy_delta;
+#if BACKOFF_TRACE
+    izanagi_backoff_trace_assigned_invert = 1;
+#endif
+#elif BACKOFF_STEP_POLICY == 2
+    backoff_step_policy_state_ =
+        backoff_step_policy_state_ * 6364136223846793005ULL +
+        1442695040888963407ULL;
+    const int izanagi_backoff_step_policy_assigned_invert =
+        static_cast<int>((backoff_step_policy_state_ >> 63) & 1ULL);
+#if BACKOFF_TRACE
+    izanagi_backoff_trace_assigned_invert =
+        izanagi_backoff_step_policy_assigned_invert;
+#endif
+    if (izanagi_backoff_step_policy_assigned_invert == 1) {
+      const double izanagi_backoff_step_policy_delta =
+          new_backoff - izanagi_backoff_step_policy_origin;
+      new_backoff =
+          izanagi_backoff_step_policy_origin - izanagi_backoff_step_policy_delta;
+    }
+#endif
+
     if (new_backoff < kMinBackoff)
       new_backoff = kMinBackoff;
 #if BACKOFF_DYN_CEILING
     else if (new_backoff > ceiling_)
       new_backoff = ceiling_;
 #else
     else if (new_backoff > kMaxBackoff)
       new_backoff = kMaxBackoff;
 #endif
+#if BACKOFF_TRACE
+    const double izanagi_backoff_trace_applied_delta =
+        new_backoff - izanagi_backoff_trace_backoff_before;
+    const int izanagi_backoff_trace_inversion_realized =
+        izanagi_backoff_trace_assigned_invert == 1 &&
+        izanagi_backoff_trace_recommended_delta_sign != 0 &&
+        izanagi_backoff_trace_applied_delta ==
+            -izanagi_backoff_trace_recommended_delta;
+#endif
     Backoff_.store(new_backoff, std::memory_order_release);
```

これにより次の四通りが、すべて同じ `:347` 後の反転点へ合流する。

| `BACKOFF_STEP_ADAPT` | `BACKOFF_DYN_CEILING` | 推奨差分 | clamp 上限 |
|---:|---:|---|---|
| 0 | 0 | `kIncrBackoff` | `kMaxBackoff` |
| 0 | 1 | `kIncrBackoff` | 更新済み `ceiling_` |
| 1 | 0 | `adaptive_step_` | `kMaxBackoff` |
| 1 | 1 | `adaptive_step_` | 更新済み `ceiling_` |

窓発火、`gradient`、`gradient_sign`、`adaptive_step_`、`last_gradient_sign_`、`ceiling_` は真の勾配だけで更新される。policy が変更するのは、parity 分岐を含めて完成した `new_backoff - pre_state` の符号だけである。

## policy 2 の決定的 LCG

`include/backoff.hh` の `ceiling_` member と trace state の間へ、policy 2 だけに存在する leader 側 member を置く。

```cpp
#if BACKOFF_STEP_POLICY == 2
  uint64_t backoff_step_policy_state_ = 0x9e3779b97f4a7c15ULL;
#endif
```

更新式は次で固定する。

```text
state = state * 6364136223846793005 + 1442695040888963407  mod 2^64
assigned_invert = (state >> 63) & 1
```

固定 seed から得る最初の 16 割当を、実装から再計算せずテスト側の逐語期待値として次に pin する。

```text
0111001000100110
```

1 更新あたりの追加費用は、policy 2 build に限り 64-bit 乗算 1、加算 1、右 shift 1、mask 1、および割当が 1 の場合の差分反転である。状態は更新窓ごとに一度だけ進め、勾配 0、推奨差分 0、clamp 発生時にも進める。

policy 2 の LCG は診断計装ではなく腕の制御意味そのものなので、policy 2 を選んだ性能 build に残ってよい。規律 1 により完全除去するのは `BACKOFF_TRACE` 配下の record、文字列、ring、追加三項目であり、policy 0/1 からは LCG 自体も前処理で消える。

## trace v2 の三項目

`patches/cicada-adaptive-counterfactual.patch` で patch B の record struct、stdout、record 関数引数、aggregate 初期化子を同時に三項目拡張する。record と summary の出力版は `v=2` にする。

出力順は既存 `parity_branch` の後へ固定する。

```text
recommended_delta_sign=<−1|0|1> assigned_invert=<0|1> inversion_realized=<0|1>
```

定義と算出位置は次のとおり。

- `recommended_delta_sign`: policy 適用前、clamp 前の `recommended_backoff - backoff_before` の符号。patch B `:347` 直後で算出する。勾配 0 の parity 分岐も反映するため、`gradient_sign` の別名にはしない。
- `assigned_invert`: policy 0 は 0、policy 1 は 1、policy 2 は当該更新で LCG が割り当てた bit。policy 2 では clamp の成否にかかわらず割当を保存する。
- `inversion_realized`: clamp 後の実差分が、clamp 前の推奨差分の数値上の厳密な負値になったときだけ 1。`assigned_invert == 1` と推奨差分非 0 も連言する。patch B `:357` 後、store 前で算出する。

`inversion_realized == 0` となる経路を全列挙すると次になる。

- policy 0、または policy 2 で `assigned_invert == 0`。
- `assigned_invert == 1` でも、推奨差分が 0。表現可能精度による差分消失もここへ含める。
- 反転候補が `kMinBackoff` より小さく、下限 clamp で大きさまたは符号が失われる。
- 動的上限 off で、反転候補が `kMaxBackoff` より大きく、固定上限 clamp を受ける。
- 動的上限 on で、反転候補が現在の `ceiling_` より大きく、動的上限 clamp を受ける。
- `Backoff_ == ceiling_` かつ負勾配で `ceiling_` が縮小した場合。推奨差分と反転差分のどちらも縮小後の `ceiling_` に clamp され得るため、両腕が同じ負方向または同じ最終値になり、厳密な反転ではない。
- `ceiling_ == 50` の floor 上で負勾配または parity が上限側へ反転候補を出し、上限 clamp により実差分が 0 になる場合。これは「動的上限は変化しないが上限 clamp される」経路として、縮小経路と分けて扱う。

## trace parser と方向的中の層別

`tools/pegasus/probes/t2187_adaptive_const_probe.py:816-922` を次の方針で改訂する。

- `_TRACE_RECORD_RE` は `v=(?P<version>1|2)` と、三項目を順序固定した optional tail を capture する。
- regex だけの optional 化で受理域を広げず、parser が `v=1 ⇔ tail なし`、`v=2 ⇔ tail あり` を連言で検査する。
- `_TRACE_SUMMARY_RE` も version 1/2 を受け、全 record が同じ版であり summary 版とも一致することを要求する。
- v1 の event dict と summary dict は現行の key 集合を維持する。
- v2 だけ event dict に三項目を追加する。
- v2 では `inversion_realized <= assigned_invert`、推奨符号 0 なら realized 0、realized 1 なら `backoff_after - backoff_before == -recommended_delta_sign * step_us` を再検算する。
- v1 と v2 の record 混在、summary 版不一致、v2 tail 欠け、v1 への余分な tail は拒否する。

`_directional_success:843-865` は既存の `scored/successes/rate` を最上位に残す。v2 の場合だけ、更新 i の属性で次の層を追加する。

```text
assigned_forward   assigned_invert == 0
assigned_invert    assigned_invert == 1
realized_invert    inversion_realized == 1
```

各層でも action は実際の `backoff_after - backoff_before`、outcome は更新 i+1 の窓 throughput 差とし、action 0 は従来どおり unscored とする。`realized_invert` が policy 2 の「同一 pre-state で逆の一歩が実現した更新」の解析母集団になる。

## 12 field cell と identity

`tools/pegasus/probes/t2187_adaptive_const_probe.py` の波及先は六箇所すべて扱う。

- `Cell:172-203`: `extended` の後へ `step_policy: int = 0` と `has_step_policy: bool = False` を追加する。末尾追加にして既存の positional `Cell(...)` を壊さない。
- `parse_cells:313-405`: field 数を `{5, 11, 12}` にする。先頭 11 field の既存処理は共有し、12 番目だけを `step_policy ∈ {"0","1","2"}` として読む。11 field は `step_policy=0, has_step_policy=False`、12 field は `has_step_policy=True`。
- `_validate_grid_contract:411-437`: 重複 configuration tuple に `step_policy` と `has_step_policy` を追加する。これにより 11 field と明示 policy 0 の 12 field は identity 上で異なる。
- `genome_for:527-545`: 既存 5/11 field の canonical genome を変えないため、`BACKOFF_STEP_POLICY` は `cell.has_step_policy` の場合だけ `flags` に明示する。実 build の CMake default が旧形式へ policy 0 を供給する。
- `_cell_identity:548-562`: `cell_format_fields` を `5/11/12` から選ぶ。`step_policy` key は 12 field identity の場合だけ出す。
- `_cell_from_document:565-599`: `cell_format_fields ∈ {5,11,12}` とし、key の存在自体を検査する。12 なのに `step_policy` がない、または 5/11 なのに `step_policy` がある document は、値が 0 でも `group-workload-contract-mismatch` で拒否する。`bool` を int として受けず、`type(value) is int` と値域を検査する。

これにより、余分な key を `.get()` が黙って捨て、異なる document が同じ `Cell` へ収束する経路を閉じる。

`is_stock_control:262-275` にも `cell.step_policy == 0` を加えるが、`has_step_policy` は制御意味ではないため stock 判定へ入れない。

## 新しい trace exact literal

既存 `TRACE_CELLS_TEXT:246-250` は 1 byte も変更しない。その隣に別定数を追加する。

```text
cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2
```

対応する Python 定数名は次とする。

```python
COUNTERFACTUAL_TRACE_CELLS
COUNTERFACTUAL_TRACE_CELLS_TEXT
```

`_validate_backoff_trace_contract:2495-2515` では、文字列と parsed tuple を同じ map entry に束縛する。

```python
trace_contracts = {
    TRACE_CELLS_TEXT: TRACE_CELLS,
    COUNTERFACTUAL_TRACE_CELLS_TEXT: COUNTERFACTUAL_TRACE_CELLS,
}
expected_cells = trace_contracts.get(args.cells)
if (
    expected_cells is None
    or cells != expected_cells
    or args.workloads != ",".join(TRACE_WORKLOADS)
    or args.threads != ",".join(str(value) for value in TRACE_THREADS)
    or workloads != TRACE_WORKLOADS
    or threads != TRACE_THREADS
    or args.rep_index != 0
    or args.reps_per_job != 1
    or args.extime != 3
):
    raise ValueError(...)
```

これは既存 literal の条件を緩めず、新 literal 一本だけを追加する。文字列と parsed tuple の交差組合せも通さない。

通る正例の署名は次である。

```text
cells = COUNTERFACTUAL_TRACE_CELLS_TEXT
workloads = "write-heavy,balanced,read-heavy"
threads = "24,48"
rep_index = 0
reps_per_job = 1
extime = 3
```

落ちる負例四つを逐語で固定する。

- 末尾一文字違い: 最後の `:2` を `:1` にする。
- cell 欠け: 中央の `cw-as-dyn-p1:...:1` cell 全体を落とす。
- 二 literal 連結: `TRACE_CELLS_TEXT + "," + COUNTERFACTUAL_TRACE_CELLS_TEXT`。
- threads 違い: cells は正しいまま `threads = "24"`、parsed tuple は `(24,)`。

## PBS の exact 述語と 12 field 判定

`tools/pegasus/probes/t2187_adaptive_const_probe.pbs:20-22` に、Python literal の comma を plus にした二本目を追加する。

```bash
COUNTERFACTUAL_TRACE_CELLS_RAW='cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2'
```

`pbs:127-134` は colon 数 10、すなわち 11 field だけでなく、colon 数 11、すなわち 12 field も extended とする。

```diff
-  if [[ ${#colon_text} -eq 10 ]]; then
+  if [[ ${#colon_text} -eq 10 || ${#colon_text} -eq 11 ]]; then
     HAS_EXTENDED_CELL=1
   fi
```

5 field の colon 数 4 は従来どおり extended にならない。

`pbs:135-140` は次の連言にする。

```bash
if [[ "$BACKOFF_TRACE" == 1 ]]; then
  if [[ "$CELLS_RAW" != "$TRACE_CELLS_RAW" &&
        "$CELLS_RAW" != "$COUNTERFACTUAL_TRACE_CELLS_RAW" ]] ||
     [[ "$WORKLOADS_RAW" != write-heavy+balanced+read-heavy ||
        "$THREADS_RAW" != 24+48 ]]; then
    echo "backoff trace mode requires one exact diagnostic cell set and exact axes" >&2
    exit 2
  fi
fi
```

Python 側の正例と四負例を comma/plus の違いだけで PBS 側にも対応させ、二層の exact 述語を同じ commit で変更する。

## patch stack と artifact identity

`tools/pegasus/probes/t2187_adaptive_const_probe.py:59-68` に以下を追加する。

```python
PATCH_C_REL = "patches/cicada-adaptive-counterfactual.patch"
PATCH_C = ROOT / PATCH_C_REL
```

`EXPECTED_PATCH_A_SHA256` は変更しない。

`_patch_stack_identity:602-626` は C の存在と SHA-256 を検査し、順序を逐語で A+B+C にする。既存 key は残し、新 key を加える。

```python
{
    "patch_sha256": a_sha256,
    "dynamic_patch_sha256": b_sha256,
    "counterfactual_patch_sha256": c_sha256,
    "patch_stack": [
        {"path": PATCH_A_REL, "sha256": a_sha256},
        {"path": PATCH_B_REL, "sha256": b_sha256},
        {"path": PATCH_C_REL, "sha256": c_sha256},
    ],
    ...
}
```

`_applied_patch_stack:629-649` は次を fail-closed に検査する。

- pin 単独へ B/C は当たらない。
- A 後へ B は当たる。
- A+B 後へ C は当たる。
- C の `patch_files` は B と同じ二 file の exact 集合。
- 適用順は A、B、C。
- outer A cleanup が三枚すべてを戻す。

新 hash key の明示伝播が必要な箇所も落とさない。

- `_validated_certification_row:1962-1965`
- group 一様性検査 `:2079-2100`
- `_group_receipt_payload:2162-2165`
- `_validate_published_group:2201-2289` は `expected_patch_identity.items()` により自動追従することをテストで pin
- performance/trace payload の `**patch_identity` は自動追従

## 登録簿と既存 pin の追随

`orchestrator/campaign/condition_meaning_gate.py:73-123` に次を追加する。

```python
"BACKOFF_STEP_POLICY": DefineSpec(
    ROUTE_CMAKE_CACHE,
    _SILO_OWNER,
    "ycsb_silo.exe",
    "patches/cicada-adaptive-counterfactual.patch",
    inert_values=("0",),
),
```

`SUPPLY_DOMAIN_MACROS:229` は自動追従する。runtime meaning witness は新設しない。

`orchestrator/campaign/screening_driver.py:49-59` へ:

```python
"BACKOFF_STEP_POLICY": 0,
```

`orchestrator/tests/test_condition_meaning_gate.py` は次を同時に直す。

- exact supply 集合 `:2397-2416` に `"BACKOFF_STEP_POLICY"` を追加。
- patch B だけを抽出する `dynamic_specs:2435-2488` は変更しない。
- patch C だけを抽出する `counterfactual_specs` を新設し、一要素の exact 集合、owner TU、target、`inert_values=("0",)` を pin。
- `_CONDITION_DEFAULTS` の値 0 を exact に検査。
- CMake cache route 件数 `:2504-2506` を `19` から `20` へ変更。
- CXX flags route 件数 16 は変更しない。

`tools/plotting/plot_dynamic_backoff.py:217-265` は:

- `_common_identity` に `counterfactual_patch_sha256` の full hash 検査を追加。
- `expected_stack:254-263` を A+B+C の三要素へする。
- エラー文を `ordered A+B+C stack` にする。

`orchestrator/tests/test_plot_dynamic_backoff.py:34-39` の `PATCH_STACK` に C の偽 hash entry を三番目として追加し、既存 A/B の偽 hash は変更しない。正しい三枚 stack は受理し、C 欠け、B/C 順序逆転、C hash 不一致を拒否する既存または追加ケースを置く。

## CMake 配線の歯

遷移 compile は `-D` 直渡しなので、次の二系統を別に設ける。

- `orchestrator/tests/test_dynamic_backoff_transitions.py` に `test_patch_c_has_exact_cmake_cache_and_universal_definition_wiring` を追加する。patch C と適用後 `Options.cmake` の双方に、既定値 0 の cache 行と `BACKOFF_STEP_POLICY=${CCBENCH_BACKOFF_STEP_POLICY}` が各一回だけ存在することを逐語 pin する。既定値 1、define 行欠け、名前違いを拒否する。
- `orchestrator/tests/test_t2187_adaptive_const_probe.py` の define 集合 pin 付近 `:1349/:1358` に `BACKOFF_STEP_POLICY: 0` を加え、`test_twelve_field_step_policy_reaches_production_build_genome_without_stub` を追加する。実体 `parse_cells` と実体 `genome_for` を呼び、12 field policy 2 の実 `Genome.flags["BACKOFF_STEP_POLICY"] == 2` と canonical genome 内の値を検査する。mock や代替 stub は使わない。

後者が検査する production consumer は、driver 本体の `genome_for(cell, backoff_trace=...)`、同じ `Genome` を渡す `source_digest.resolve_evidence:3053-3059`、および `buildcache.build:3074-3085` である。5/11 field の正例では flag が明示追加されず、12 field の正例でだけ CMake build input に到達することを対で pin する。

## 遷移テストの改訂

`orchestrator/tests/test_dynamic_backoff_transitions.py` を次のように変更する。

- `:14-16` に `PATCH_C` を追加。
- `DEFAULT_DEFINES:18-30` と全 variant の undef/define 群 `:108-200` に `BACKOFF_STEP_POLICY` を追加。
- fixture `patched_sources:467-502` で `after_b` を保存した後に C を適用し、`after_c` を保存する。
- compile 対象と policy runtime variant は `after_c` を使い、既存の B-only variant は policy 0 比較用に残す。
- `WARNING_COMPILE_VARIANTS:40-86` は policy 3 値 × `STEP_ADAPT` 2 値 × `DYN_CEILING` 2 値 × `TRACE` 2 値の直積 24 組に置換する。各 tuple を具体的な `-D` 群へ展開し、単に `policy in {0,1,2}` を assert する恒真テストにはしない。
- 全 24 組を `g++ -std=c++17 -O0 -Wall -Wextra -Werror -fsyntax-only` で compile する。
- dyn ceiling が 1 の組では `STEP_MIN=1000`、`STEP_MAX=4000` とし、既存の `kStepMax <= 50/4` 制約に正しく入れる。
- `BACKOFF_STEP_POLICY=-1` と `3` は compile failure と static assertion 文言を要求する。

追加する主要テスト署名と正負例は次のとおり。

| テスト署名 | 通る正例 | 拒否または検出するもの |
|---|---|---|
| `test_counterfactual_patch_requires_a_plus_b_and_preserves_include_lines` | pin+A+B に C が適用可能 | pin、pin+A への C 適用、編集 path 増加、include 行増加 |
| `test_all_24_step_policy_compile_variants_are_warning_clean` | 24 tuple 全件 rc 0 | 一組でも compile/warning failure |
| `test_step_policy_static_assert_rejects_out_of_domain_values` | 0、1、2 | −1、3 |
| `test_policy_zero_matches_patch_b_transitions_exactly` | B-only と C/policy0 が `100→101`、`100→99`、parity の逐語列で一致 | policy 0 の反転や LCG advance |
| `test_policy_one_reverses_safe_positive_and_negative_recommendations` | pre-state 100、ceiling 1000 で正勾配 `(p0,p1)=(101,99)`、負勾配 `(99,101)` | 同方向、clamp 後反転、勾配 state の反転 |
| `test_policy_inversion_is_shared_by_all_step_ceiling_combinations` | 四組すべて安全な正勾配で `(101,99)` | 一つの compile-time 分岐だけ反転を迂回 |
| `test_policy_two_assignment_sequence_is_exact` | 最初の 16 bit が `0111001000100110` | seed、乗数、加数、抽出 bit、更新時期、毎回 reset |
| `test_trace_v2_records_parity_recommendation_not_gradient_alias` | gradient 0、偶数 parity で `recommended_delta_sign=-1` | `gradient_sign` の流用 |
| `test_inversion_realized_is_one_only_for_unclamped_exact_inverse` | pre-state 100 の policy1 で assigned 1、realized 1 | sign だけを見て大きさを無視 |
| `test_inversion_realized_is_zero_at_lower_and_fixed_upper_clamps` | lower/upper の各 record が realized 0 | clamp 前の値で realized を決定 |
| `test_dynamic_ceiling_shrink_can_make_both_arms_equal` | `ceiling_=Backoff_=200`、負勾配で p0/p1 とも最終 100、p1 realized 0 | 境界を反転成功として数える |
| `test_trace_preprocesses_out_of_trace_zero_builds` | trace 0 で三項目、ring、trace literal が全て不在 | 診断計装の性能 build 漏出 |

逆符号の本検査には `Backoff_ == ceiling_` の負勾配を使わず、`Backoff_=100`、`ceiling_=1000` を使う。境界同値は別テストで「反転が実現しない」ことだけを検査する。

## driver と PBS の focused test

`orchestrator/tests/test_t2187_adaptive_const_probe.py` に以下を追加または追随させる。

| テスト署名 | 通る正例 | 拒否する負例 |
|---|---|---|
| `test_parse_cells_accepts_legacy_dynamic_and_policy_forms` | 5、11、12 field を各一つ | 6〜10、13 field、空 field |
| `test_parse_cells_rejects_invalid_step_policy` | 末尾 0、1、2 | −1、3、空、`True` 相当文字 |
| `test_eleven_and_explicit_policy_zero_have_distinct_identity` | 11 field と同値の `:0` 付き 12 field が別 identity | `has_step_policy` を tuple から落とす変異 |
| `test_cell_document_round_trip_requires_policy_key_presence_to_match_format` | `_cell_identity(12-field)` の round trip | 12 で key 欠け、11/5 で余分な key、bool policy |
| `test_genome_for_policy_cell_supplies_real_build_define` | 12 field policy 2 が実 `Genome` に 2 を持つ | flag 欠け、値 0 への潰れ |
| `test_patch_stack_identity_is_exact_ordered_a_b_c` | 三 path と再計算 digest が一致 | C 欠け、順序違い、C hash 改変 |
| `test_patch_c_uses_numeric_if_and_adds_no_include` | `#if BACKOFF_STEP_POLICY`、include 差分 0 | `#ifdef`、三 file 目、include 追加 |
| `test_parse_backoff_trace_accepts_v1_and_exact_v2` | 既存 v1 行と三項目付き v2 行 | v2 tail 欠け、v1 tail 付き、版混在、summary 版違い |
| `test_directional_success_v2_is_stratified_by_current_assignment` | forward、assigned invert、realized invert の三層が exact count | following event の属性で誤って層別 |
| `test_backoff_trace_contract_accepts_only_two_exact_cell_literals` | 既存 literal と新 literal を個別に受理 | 指定した四負例 |
| `test_pbs_marks_eleven_and_twelve_fields_extended` | colon 数 10、11 | colon 数 4 を extended 扱い |
| `test_pbs_trace_gate_contains_two_exact_literals_only` | 既存または新 literal と exact axes | prefix、substring、二 literal 連結、threads 24 |
| `test_define_inventory_includes_step_policy_default_zero` | define/default exact 集合 | 登録欠け、既定値 1 |

v1 正例は旧形式をそのまま用い、event dict に新 key が増えていないことまで比較する。v2 正例は `recommended_delta_sign=1 assigned_invert=1 inversion_realized=1` を持ち、前後差分を `100→99`、`step_us=1` として parser の再計算も通す。

## 恒真になり得る assert の排除

実装時に特に避ける assert は次である。

- 生成側と同じ LCG 式で期待系列を計算する。期待値は逐語 `0111001000100110` とする。
- parser 自身で作った `Cell` を parser 結果の期待値に使う。label、field 数、policy、identity key を個別に比較する。
- `p0 != p1` だけで反転成功とする。安全な pre-state で `101/99` と `99/101` を exact 比較する。
- `Backoff_ == ceiling_` の負勾配を逆符号の主検査に使う。
- 24 値の parameter list を作っただけで 24 compile を証明する。各 compile の rc と stderr を個別に確認する。
- PBS 内に新 literal が含まれることだけを見る。二本だけを exact OR する条件式と axes の連言まで pin する。
- patch stack の期待値を `_patch_stack_identity()` 自身から作る。path 順序はテスト側の逐語三要素にする。
- CMake option 名の単なる出現だけを見る。cache 既定値と universal definition の双方を別々に一回ずつ要求する。

## 変異事前登録候補

段 4 へ渡す候補は次の 18 件とする。本段では発行も走行もしない。

| 変異 | 赤になるテスト |
|---|---|
| M1 cache default `0→1` | CMake cache exact test |
| M2 universal definition 行を削除 | CMake exact test、Genome consumer 系も不整合になる冗長 gate |
| M3 policy 分岐を `#if→#ifdef` | patch 静的検査、policy0 compile/runtime の冗長 gate |
| M4 static assertion が 3 を許す | out-of-domain compile test |
| M5 policy 0 でも反転する | B/C policy0 exact transition test |
| M6 policy 1 の反転を削除 | safe positive/negative exact transition test |
| M7 反転点を clamp 後へ移す | lower/upper clamp と realized test |
| M8 一つの STEP_ADAPT/DYN_CEILING 分岐内だけに反転を置く | 四組 runtime test、24 compile のうち一部も赤になり得る冗長 gate |
| M9 LCG seed を変更 | 16 bit exact series test |
| M10 LCG multiplier、increment、上位 bit のどれかを変更 | 16 bit exact series test |
| M11 LCG state を更新ごとに seed へ戻す | 16 bit exact series test |
| M12 `recommended_delta_sign = gradient_sign` | gradient 0 parity trace test |
| M13 realized を符号一致だけで判定 | exact magnitude、clamp、ceiling shrink test |
| M14 v2 tail を optional のまま無条件受理 | v1/v2 malformed parser test |
| M15 12 field の policy 値域検査を削除 | invalid step policy parse test |
| M16 document の key presence 検査を削除 | cell document mismatch test |
| M17 exact predicate を prefix、membership、二 literal 連結許可へ緩和 | Python 四負例と PBS static gate の冗長 gate |
| M18 C を stack、plot、登録簿のいずれか一箇所から落とす | patch identity、plot stack、supply exact 集合、件数の複数層が赤になる冗長 gate |

現計画で歯がない領域も明記する。

- 16 更新より後の LCG 系列、長期の 1/2 比率、統計品質。
- LCG の実機命令数、branch prediction、throughput への費用。
- policy 1/2 の実 workload 上の性能差と因果効果。
- trace ring overflow時の新三項目の保持。
- 複数 `Backoff` instance 間で seed が同じことの性能上の影響。
- compiler が行う同値変形や生成 assembly の形。
- 新腕の serializability certification。
- 実測、図再生成、事前登録発行、上流還元。

これらは本 wave の「実測なし」という scope の外なので、新 gate を追加しない。

## 並列編集の素集合

単位 A の編集 path は次の二つだけである。

```text
patches/cicada-adaptive-counterfactual.patch
orchestrator/tests/test_dynamic_backoff_transitions.py
```

単位 B の編集 path は次である。

```text
tools/pegasus/probes/t2187_adaptive_const_probe.py
tools/pegasus/probes/t2187_adaptive_const_probe.pbs
orchestrator/campaign/condition_meaning_gate.py
orchestrator/campaign/screening_driver.py
orchestrator/tests/test_condition_meaning_gate.py
orchestrator/tests/test_t2187_adaptive_const_probe.py
tools/plotting/plot_dynamic_backoff.py
orchestrator/tests/test_plot_dynamic_backoff.py
```

二集合は素である。`patches/README.md` はどちらにも含めず、親が統合後に書く。patch A/B、admission registry、insight、事前登録文書、図 artifact は編集しない。

## patches README に親が書く内容

`patches/README.md:224-258` の adaptive 節へ、親が次を追記する。

- C は pin+A+B 専用の第三 patch であり、A/B の bytes は不変。
- C の二 file 制約と include 不変。
- `CCBENCH_BACKOFF_STEP_POLICY` の 0/1/2 と既定 0。
- 反転点は推奨差分生成後、clamp 前の一箇所。
- gradient、adaptive step、last sign、dynamic ceiling は真の勾配で更新される。
- policy 1 は逆方策全体の性能腕であり、同一軌跡上の反実仮想ではない。
- policy 2 は固定 seed LCG による更新単位の割当で、`inversion_realized=1` に層別して同一 pre-state の一歩を問う。
- LCG の seed、式、先頭 16 bit、更新費用。
- trace 行 v2 の三項目と v1 parser 互換。
- 12 field cell と 11 field末尾 0 の identity 区別。
- trace exact literal は既存一本を保ち、新一本だけを追加。
- patch stack と provenance は A+B+C。
- policy 非 0 は既存 certification 2 cell の対象外で、次 wave の別 certification が必要。
- 方向的中 0.50 から throughput 等価は導けない。
- 本 wave は実測、図再生成、事前登録発行を行わない。

## 検査順序

実装後は、親の正規 test runner を通して次の順で確認する。

1. patch C の適用閉包、二 file 集合、include 不変、CMake 静的配線。
2. 24 組 compile、policy 0/1/2 遷移、LCG 系列、trace 三項目。
3. 5/11/12 field、document identity、Genome consumer、v1/v2 parser。
4. Python/PBS exact 述語、登録簿 exact 集合、cache route 件数 20。
5. patch stack A+B+C と plot consumer。
6. repo 規律に従う docs、Codex agents、provenance 検査。

この read-only 段では一件も実走していないため、「緑」とは報告しない。

## 総括

patch C は推奨差分完成後かつ clamp 前の一箇所に policy 0/1/2 を置く。  
policy 2 は固定 seed LCG、trace v2 は推奨符号・割当・厳密な反転実現を記録する。  
driver は既存 5/11 field を保ったまま 12 field と A+B+C identity を追加する。  
Python/PBS の exact gate は既存 literal を緩めず二本目だけを追加する。  
24 組 compile、CMake consumer、既存 registry/plot pin、18 変異候補で閉包する。