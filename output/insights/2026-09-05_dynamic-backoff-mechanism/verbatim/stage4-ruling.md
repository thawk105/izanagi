# 段 4 裁定 — dev-wave dynamic-backoff-mechanism (2026-09-05 07:50 JST)

**プラン (stage2-plan.md) と食い違う場合は本書が勝つ。** 本書に書いていない点はプランどおり。

## 0. 親が一次資料で裏取りした所見 (real)

- A-MF1 **real・採用。** `orchestrator/campaign/source_digest.py:85` の `EVOLVE_BLOCK_SOURCES` に
  `include/backoff.hh` が入っており、`assert_includes_match_head` (同 `:2075`) は dead branch 内も含む
  `#include` 行の列を HEAD と逐語比較する。**patch B は `#include` 行を 1 行も足してはならない。**
  既存 include (`<x86intrin.h>` `<atomic>` `<cmath>` `<iostream>` `atomic_wrapper.hh` `result.hh`
  `tsc.hh` `util.hh`) だけで実装する: ring は生配列、flush は `std::cout`、flush の契機は `atexit` でなく
  **static 記憶域のオブジェクトのデストラクタ** (`ycsb_silo.cc:63` は `return 0` で正常終了する)。
- A-MF12 **real・scope 外 (記録のみ)。** `_is_inert_value` (condition_meaning_gate.py:904) と
  `screening_driver.py:98` の stock 判定は単項。従属 parameter (`COUNT_CAP_US`, `STEP_MIN/MAX_MILLI`) は
  `inert_values=()` で登録し、既定値一致だけを stock とする。toggle 依存の限界は `patches/README.md` に
  書く。probe の build sink は deferred gate 台帳に載っており本 wave の成果物に影響しない (DW-G05)。
- A-MF10 **real・採用。** claim は cell ごとの写像 `CERT_CLAIMS` にし、既存 tuned の literal は byte 不変。
  performance / certification / group receipt の schema は **v2** へ上げる (旧 v1 の凍結 receipt は
  本 wave のコードで再検証しない。`plot_t2187_adaptive_consts.py` は v1 のまま触らない)。
- B-MF08 / A-Nit2 **real・採用。** 見積もりは 4.25 s/process。認証は T-2189 insight の verify 87〜459 秒が
  一次資料で、brief の「52 分/job」は T-2228 の別 job の値の取り違え (親の誤り)。
- B-MF03 / A-MF6 **real・採用。** `last_backoff_` は `uint64_t` なので sub-µs の刻みは偽ゼロ/逆符号勾配を
  作る (T-2216 §3)。**刻みは整数 µs だけ**: step_min=1、step_max=4 (1→2→4)。`last_backoff_` の型は変えない。
- A-MF7 / B-MF04 **real・採用。** 動的上限は整数演算・単調: 上限で負勾配なら `ceiling = max(ceiling/2, 50)`
  (整数除算)、正勾配なら `min(ceiling*2, kMaxBackoff)`。下限 50 µs は T-2187 が測った既知点。
  `static_assert(kStepMax * 4 <= 50)`。上限を更新した後に一歩を計算し、新上限へ clamp する (プランどおり)。
- B-MF02 **real・採用。** cap = 10240 µs (T-2187 段 3 で 2560 とほぼ重なる点)。
- B-MF05 / A-MF4 **real・一部採用。** (P1 改) 計数窓の検査は時間で間引く: 経過 < `update_us` なら counter を
  読まず false (stock と同じ安価判定)。経過 ≥ `update_us` で sum を取り、`count ≥ K` または
  経過 ≥ cap で更新。scan は 1 窓に 1 回だけになり sham polling 腕は不要。「長い更新間隔」との識別には
  **時間のみ 10240 µs の腕 `tuned-u10240` を 7 番目の腕として同 job に足す** (T-2187 段 3 は別走)。
- A-MF5 / B-MF06 **real・採用。** trace record は `seq, tsc, window_us, window_commits, trigger(count|cap|time),
  backoff_before, backoff_after, gradient_sign, step_us, ceiling_us, ceiling_changed, parity_branch`。
  「的中」は probe が offline で計算する **方向的中 (directional success)**: 更新 i の action 符号
  (backoff_after − backoff_before の符号) と、更新 i+1 で観測した throughput 差の符号の一致。action 0 は
  unscored。「accuracy」と呼ばない。
- A-MF3 **real・採用。** trace 静的状態は `alignas(64)`。診断の軌跡は「計装系の軌跡」と明記し perf build へ
  外挿しない。
- A-MF2 **real・採用。** perf build の検査は `nm -C | grep izanagi_backoff_trace` = 0 に加え
  `strings | grep IZANAGI_BACKOFF_TRACE` = 0 (printf/cout の文字列 literal は inline 化で消えない)。
  probe が perf mode で両方を fail-closed に検査し JSON に記録、診断 mode は両方 ≥ 1 を要求。
- A-MF8 **一部採用。** 親の生死確認で tuned を A 単独と A+B で build し sha を比較、不一致なら
  `objdump -d --no-show-raw-insn` の `.text` (アドレス除去) を比較して記録する。inert の主張は
  「.text 同一」までとし、不一致なら「同 job 内 A+B build 同士の比較」に主張を限定する。
- A-MF9 **real・採用。** `patch_sha256` は A の意味を永久に保つ。追加: `dynamic_patch_sha256`、
  `patch_stack` (順序付き list)、`patch_stack_sha256` = sha256(`"izanagi-patch-stack/v1\n"` +
  各行 `"<path> <sha256>\n"`)。probe は A の sha を literal `EXPECTED_PATCH_A_SHA256 =
  "9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b"` と実行前に照合して fail-closed。
- A-MF11 **real・採用。** 拡張 cell・`--backoff-trace`・動的 certify では `IZANAGI_T2187_OUT_DIR` を必須にし、
  `.pbs` と driver が `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/` 接頭辞を検査する。
- A-MF13 **real・採用。** patch B に **時刻 seam** を入れる: `check_update_backoff_at(now, committed)` と
  `update_backoff_at(now, committed)` を本体とし、production の `check_update_backoff()`/`update_backoff()`
  は `rdtscp()` を渡す wrapper。C++ の遷移 test (`orchestrator/tests/test_dynamic_backoff_transitions.py`
  が小さな driver `.cc` を g++ で compile して走らせる。compile は 1 TU、-O0、数秒) で K 境界・OR・刻み ×2/÷2 の
  上下限・上限単調・floor 50・stock 経路の逐語同値 (K=0 で counter を読まない) を合成入力で固定する。
  この driver は DW-G01 の login node 生死確認にも使う。
- B-MF07 **real・採用。** 7 job の腕の実行順は rep i が「7 腕の巡回 (開始位置 i)」。probe は与えられた順で走り
  JSON に順序と hostname を記録する。
- B-MF09 **real・採用。** probe は点ごとに append-only JSONL journal (`<out>.journal.jsonl`) を書き、最後に
  JSON をまとめる。欠測規則は prereg §6。
- B-MF10 **refuted (裁定として不採用)。** ユーザー引数が「同じ wave で動的版にも trace-enabled + verifier を通す」
  と明示。認証は perf/診断の完了後に (performance artifact の path/sha を束縛する契約上、同時投入は不可)
  pilot 1 本 → 残り 23 本の順で無条件に投入する。費用は 1 job ≈ prologue + trace build + run + 陽性対照 +
  verify (87〜459 s) で 15〜25 分、24 job で 6〜10 ノード時間、上限 24 × 2.25 h。
- B-MF11 **一部採用。** 新 generator `tools/plotting/plot_dynamic_backoff.py` は書く (ユーザー引数) が、
  `plot_t2187_adaptive_consts.py` の helper (t 分位点、layout 検査、atomic save) を import して重複しない。
  図は 3 枚: (i) thread 軸 7 系列、(ii) 対内 log 比の forest (H1〜H7 の判定を図示)、(iii) 診断。
- B-MF12 **real・採用。** probe は `repo_head` (PBS_O_WORKDIR の `git rev-parse HEAD`)、
  `prereg_sha256` (`docs/dynamic-backoff-preregistration.md` の bytes)、patch stack を JSON に記録する。
- B-MF01 **real・採用。** 仮説 H1〜H7 と判定式を prereg §4 に凍結 (下記)。
- N-01/N-02 **採用。** 機械 label は hyphen 形 (`cw`, `cw-as`, `cw-as-dyn`, `tuned-u10240`)、表示は同じ綴り。
  「Silo 上の Cicada 型 adaptive backoff」と書く。
- P7 **plan の結論を採用。** `patches/ledger.json` に entry を足さない (rung1 contract が entry 数 1 を exact 要求、
  `silo_ladder_rung1_contract.py:517` を親が確認)。登録は `patches/README.md` と `DefineSpec`。

## 1. 確定した腕 (7 cell、書式は 5 または 11 field)

```text
none:0:100:1000:10
stock:1:100:1000:10
tuned:1:1:1000:2560
tuned-u10240:1:1:1000:10240
cw:1:1:1000:2560:10000:10240:0:100:100:0
cw-as:1:1:1000:2560:10000:10240:1:1:4:0
cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1
```

11 field = `label:back_off:step_us:ceiling_us:update_us:count_window:count_cap_us:step_adapt:step_min_us:step_max_us:dyn_ceiling`。
`update_us` は K>0 のとき「最小間隔 (counter を読む間引き)」、`count_cap_us` は「最大間隔」。
`step_min_us`/`step_max_us` は `step_adapt=0` なら inert (stock 既定 100/100 を書く)。
certify の exact cell 集合 = `{tuned:1:1:1000:2560, cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1}`。

## 2. patch B の確定仕様 (プランの差分案を次で上書き)

- 追加 include なし。CMake option 7 つと `#error`/`static_assert` はプランどおり。
- `check_update_backoff_at(now, committed)`: K=0 なら `chkClkSpan(last_time_, now, clocks_per_us_*kUpdateBackoffUs)`
  (stock 逐語)。K>0 なら経過 < update_us → false、それ以外で `committed - last_committed_txs_ >= K` または
  経過 ≥ cap (cap=0 なら update_us) → true。`leaderBackoffWork` は K>0 のとき「経過 ≥ update_us」を
  先に見てから sum を取る (counter を読むのは 1 窓に 1 回)。
- `update_backoff_at(now, committed)`: stock 本体を逐語で保ち、`#if BACKOFF_STEP_ADAPT` / `#if BACKOFF_DYN_CEILING`
  / `#if BACKOFF_TRACE` の枝を足す。刻み: 初回は `kIncrBackoff`、以後は非ゼロ符号が前回と同じなら ×2
  (上限 kStepMax)、反転または 0 なら ÷2 (下限 kStepMin)、当該更新で使う。上限: `uint64_t ceiling_` を
  `kMaxBackoff` で初期化、`Backoff_ == ceiling_` かつ負勾配で `max(ceiling_/2, 50)`、正勾配で
  `min(ceiling_*2, kMaxBackoff)`、その後に一歩、最後に `[kMinBackoff, ceiling_]` へ clamp。
- trace: `alignas(64)` の static 生配列 ring 65,536 件 + 計数、record 12 field (§0)、flush は static
  デストラクタで `std::cout` に `IZANAGI_BACKOFF_TRACE v=1 ...` と `IZANAGI_BACKOFF_TRACE_SUMMARY v=1 ...` を出す。
  名前はすべて `izanagi_backoff_trace` 接頭辞、定義は `#if BACKOFF_TRACE` の内側だけ。

## 3. 段 5 の分割 (3 単位、素集合)

| 単位 | 所有 | worktree |
|---|---|---|
| A | `patches/cicada-adaptive-dynamic.patch`、`orchestrator/tests/test_dynamic_backoff_transitions.py` (+ driver `.cc` は test が生成) | wave worktree |
| B | probe `.py`/`.pbs`、`condition_meaning_gate.py`、`screening_driver.py`、`test_condition_meaning_gate.py`、`test_ccbench_spawn_sites.py`、`test_t2187_adaptive_const_probe.py` | `.codex/worktrees/dynbackoff-b` |
| C | `tools/plotting/plot_dynamic_backoff.py`、`orchestrator/tests/test_plot_dynamic_backoff.py` | `.codex/worktrees/dynbackoff-c` |

docs (`patches/README.md`、`tools/plotting/README.md`、`docs/README.md`、prereg、insight) は親。
`patches/ledger.json` は非変更。B は A の bytes を統合時に受け取る (B の patch 適用 test は統合後に緑)。

## 4. 変異の事前登録 (DW-M01、実装後に old 逐語を固定して spec 化)

| ID | 位置 | 変異 | 赤にする層 (単一理由) |
|---|---|---|---|
| M1 | patch B | `#if BACKOFF_TRACE` → `#ifdef BACKOFF_TRACE` | test_t2187 の D14 静的検査 |
| M2 | patch B | `>= kCountWindow` → `> kCountWindow` | 遷移 test (K 境界) |
| M3 | patch B | 計数窓の `||` → `&&` | 遷移 test (cap 単独発火) |
| M4 | patch B | 刻み ×2 の上限 clamp 削除 | 遷移 test (step_max) |
| M5 | patch B | 上限 floor 50 → 0 | 遷移 test (floor) |
| M6 | patch B | 負勾配で上限 ×2 (単調性反転) | 遷移 test (単調) |
| M7 | probe | 11 field の `K=0 ⇒ cap=0` 検査を削除 | parse test |
| M8 | probe | certify cell 集合に 3 つ目を許す | certify exact test |
| M9 | probe | `EXPECTED_PATCH_A_SHA256` の照合を削除 | patch identity test |
| M10 | registry | `_DEFINE_SPECS` から 1 define を落とす | inventory test |
| M11 | plot | t 分位点 → 1.96 | plot test |
| M12 | pbs | 拡張 cell の OUT_DIR 必須化を削除 | pbs test |
| M13 (positive) | probe | 等価変異 (`list(x)`→`[*x]`) | SURVIVED 期待 |

## 5. DW-O13 (既存 exact 述語の受理形拡張)

certify の cell 述語は親が構築する exact 値 2 つ (§1) だけを受理する。到達可能性: 両 cell とも本 wave の
perf grid に実在し、時間予算 (prologue 540 + build 900 + run 180 + 陽性対照 120 + verifier 5400 + margin 300 =
7440 < 8100) は不変。

## 6. 投入設計 (prereg §3/§7 と同じ)

- perf: 7 job (rep 0..6、腕順は巡回)、各 7 cell × 3 workload × 8 threads = 168 process ≈ 168 × 4.25 s = 11.9 分
  + 7 build ≈ 3.5 分 + prologue 2 分 ≈ 17.5 分、walltime 40 分。canary は perf rep0 自身 (先に 1 本投げ、
  build/journal が進むのを確認してから残り 6 本を投げる。queue が空なら同時)。
- 診断: 1 job、`--backoff-trace`、3 動的腕 × 3 workload × threads {24,48} = 18 process ≈ 8 分、walltime 40 分。
- 認証: perf 完了後、pilot 1 本 (read-heavy slot 0) → 残り 23 本、walltime 2:15。
- 出力: `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/{perf,trace,certify}/`。
