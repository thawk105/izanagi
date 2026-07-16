# patches/ — Izanagi の CCBench 改変

CCBench (`external/ccbench` submodule = `thawk105/ccbench`) への Izanagi 由来の改変は
**性質ごとに行き先を分ける** (D16。当初は全て out-of-tree patch だった = D6):

| 改変 | 性質 | 行き先 |
|---|---|---|
| スレッドピンニング (`-DLinux`) | CCBench 本物のバグ修正 (Izanagi 非依存) | **submodule `master`** に還元 |
| trace-hook (Silo/si の `#if TRACE` 検証計装) | Izanagi の verifier 入力。`#if TRACE` で観測者効果セーフ | **submodule `izanagi-trace` ブランチ** (submodule が追う) |
| broken-silo (わざと壊した Silo) | verifier の赤検出用 positive control = **テスト用の意図的バグ** | **out-of-tree patch** (このディレクトリ。永久) |
| 合成 variant (例: 静的 backoff `BACKOFF_FIXED`) | Izanagi がフラグ空間外に合成した**評価中の正当な variant** (D18) | **out-of-tree patch** (価値確定まで。昇格は人間判断) |

**broken-silo を patch に隔離する理由 (絶対規律2):** 壊した CC をブランチに commit すると
baseline として誤ビルドされる危険がある。out-of-tree patch なら「赤検出証明をするときだけ
明示的に重ねる」inert 状態を保てる。

**合成 variant を patch に置く理由 (D18):** フラグ空間 (CCBench 定義の最適化フラグ) の外へ
合成した variant は、価値が確定するまで submodule 本体に焼かない。default で stock 不変 (inert)
なので baseline を汚さず、verifier が毎回正しさを確認する。勝てば昇格、負ければ patch のまま記録。

## submodule の階層

```
master (CCBench 本体 + pinning 修正)
  └─ izanagi-trace (+ trace-hook Silo/si)   ← submodule が pin する (.gitmodules の branch)
       └─ broken-silo-norw-validation.patch  ← 赤検出 ablation のときだけ重ねる (out-of-tree)
```

submodule は `izanagi-trace` の特定 commit を pin する (`.gitmodules` の `branch = izanagi-trace`)。
**parent の gitlink は常に特定 commit を固定する**ので再現性は patch 運用時と同じく保たれる。
trace-hook の追加開発は submodule の `izanagi-trace` ブランチに直接コミットし、parent の
gitlink を前進させる (submodule の working-tree dirt を放置しない方針に変わった = D16)。

ビルドモード (絶対規律1: 観測者効果分離):
- **perf ビルド** (`build/`, 既定 `-DTRACE=0`): trace は `#if TRACE` で完全に消える。
  pinning は master 由来で常に有効。性能計測・calibration はこれに当てる。
- **trace ビルド** (`build-trace/`, `-DCCBENCH_TRACE=1`): trace を吐く。正しさ検証専用。
- 実証済み: `TRACE=0` ビルドのバイナリに `izanagi_trace` シンボル 0 個 (`nm`/`strings`)。

---

## broken-silo-norw-validation.patch — verifier の検出力証明 (Phase 1 タスク3, Approach A)

**わざと壊した CC** (positive control)。Silo の `validationPhase()` 条件#1 (read-set の
tidword 再検証 = anti-dependency / stale-read チェック) を **macro `IZANAGI_BREAK_NOREAD_VALIDATION`
で抜く**。stale read が abort されず commit するので、lost-update / write-skew の **G2 cycle が
trace に出現**し、verifier がそれを赤と判定できることを実証する。

- **既定 OFF**: macro 未定義時は `#else` で元の abort が compile-in されるので**挙動は完全に元の
  Silo** (inert)。**正しさ/性能の baseline には絶対に混ぜない** (絶対規律2)。
- **`izanagi-trace` (trace-hook 入り) の上に重ねて適用する** (validationPhase を触る。trace-hook の
  writePhase と非衝突。`git apply --check` で round-trip 確認済み)。

```sh
SUB=external/ccbench
# submodule は既に izanagi-trace (trace-hook 入り) を pin している。壊しを重ねる:
git -C "$SUB" apply ../../patches/broken-silo-norw-validation.patch
# 壊し+trace 専用ビルド (別 build dir)
cmake -S "$SUB" -B "$SUB/build-trace-broken" -DCMAKE_BUILD_TYPE=Release \
      -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=1 \
      -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 \
      -DCMAKE_CXX_FLAGS="-DIZANAGI_BREAK_NOREAD_VALIDATION=1"
cmake --build "$SUB/build-trace-broken" --target ycsb_silo.exe -j
# 高 contention で走らせ verifier にかける → NON-SERIALIZABLE (exit 1) になるはず
git -C "$SUB" checkout -- cc/silo/transaction.cc   # 壊しだけ revert (izanagi-trace に戻る)
# silo-backoff-fixed.patch も併用していて working-tree 全体を戻す場合は
#   git -C "$SUB" checkout -- .
# (transaction.cc だけの revert では backoff 差分が残り、剥がし忘れた静的 backoff が baseline を汚す)
```

### 実証 (2026-06-18, clean ablation)

同一ワークロード `-ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=50 -ycsb_max_ope=5 -thread_num=4 -extime=1`:
- **壊し ON**: 293,803 commit → trace に **1310 G2 cycle** → verifier **NON-SERIALIZABLE (exit 1)**
- **壊し OFF (素の Silo)**: 285,047 commit → verifier **certified SERIALIZABLE (exit 0)**
- 差は read validation の有無のみ → verifier は壊れた CC を赤・正しい CC を緑と判定する番人だと確認。

---

## broken-silo-highkey-validation.patch — S2 verify 構成の ablation positive control (Phase 3 後続段 1, D36)

**わざと壊した CC** (positive control) の第 2 弾。norw と同じ `validationPhase()` 条件#1 の abort を、
**key id ≥ 1000 のときだけ** macro `IZANAGI_BREAK_HIGHKEY_VALIDATION` で抜く。既存 CorrectnessWorkload
(tuple200 — key id は常に < 200) では**構造的に発火せず緑**、S2 構成 (tuple 1m) でのみ stale read が
commit して G2 が trace に出る = 「小 workload では踏まないデータパス上の違反」を再現する fixture。
S2 verify 構成の付加価値 (規律5 の「効果を測れる ablation」) を機械実証するために存在する。

- **既定 OFF** (macro 未定義 = `#else` で元の abort、完全に元の Silo)。**baseline に絶対に混ぜない** (絶対規律2)。
- **駆動の正本は `orchestrator/campaign/s2_verify_calibration.py`** (apply → 一時 build dir → run →
  verifier → revert を patchharness.applied() 下で機械化。build dir は TMPDIR 配下に毎回 fresh —
  stale CMakeCache の沈黙再利用を排除)。norw の手動手順 (上) はデバッグ用の参考。

### 実証 (2026-07-06, output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json)

- **S2 構成 (1m/t48/skew0.9/rr50/rmw0/max_ope10/extime3)**: NON-SERIALIZABLE、G2 total 5 (exit 1)
- **legacy 構成 (tuple200/t4/rmw=true)**: certified SERIALIZABLE (exit 0)
- 同一 binary・workload 差のみ → S2 構成だけが検出する違反の実在を確認 (詳細 = D36)。

---

## broken-silo-lockskip-validation.patch / broken-silo-early-unlock-validation.patch — write_set 被覆 assert の positive control (Phase 3 後続段 3, D38)

**わざと壊した CC** (positive control) 2 本。段 3 で新設した writePhase の lock 被覆 assert
(izanagi-trace の `#if TRACE`、2 検査点 = lockWriteSet 入口の「獲得被覆」と各 storeRelease 直前の
「保持継続」) が恒真でなく実際に歯を持つことを機械実証する (D38 決定2 の非恒真性 operative proof)。
verifier は commit 経路 (C/R/W) しか trace せず lock 獲得・被覆・torn read が構造的に見えない死角を、
この assert が埋める。

- **broken-silo-lockskip-validation.patch** (`IZANAGI_BREAK_LOCK_COVERAGE`): lockWriteSet で非 INSERT
  tuple の write lock 獲得を skip し、writePhase が被覆なしで書く → 入口検査 (獲得被覆) が
  X (not-locked-at-entry) で赤。
- **broken-silo-early-unlock-validation.patch** (`IZANAGI_BREAK_EARLY_UNLOCK`): writePhase で tuple
  データ書き込み前に lock を release し torn-read 窓を開ける → storeRelease 直前検査 (保持継続) が
  X (lock-lost-before-write) で赤。2 検査点が別々に歯を持つことを分離実証する。
- **verdict は indeterminate** (non-serializable ではない): X 行は verifier の Integrity カウンタ
  `lock_coverage_violations` に配線され clean()→indeterminate に倒す (cycle を生まないので
  serializable=False とは両立不能、D38 決定1)。
- **既定 OFF inert**: 裸マクロ (`IZANAGI_BREAK_*`、`CCBENCH_` 接頭辞なし) ゆえ pipeline から定義不能。
  baseline に絶対混ぜない (broken-silo と同じ隔離規約、絶対規律2)。
- **駆動の正本 = `orchestrator/campaign/s3_lock_coverage.py`** (apply → 一時 build → run → verifier +
  assert → revert を機械化)。実証 (2026-07-06, `output/env/linux-baremetal/calibration/s3_lock_coverage.json`
  all_pass): stock=X0/certified、lockskip 単一スレッド=total_cycles==0 (verifier certify) かつ
  lcv>0/indeterminate、early-unlock=保持破れのみ。

---

## silo-backoff-fixed.patch — 静的 backoff (合成 variant, D18) + noinline (診断計器, P2-4) + EVOLVE-BLOCK 骨格 (Phase 3, D22)

このパッチは izanagi の silo backoff 追加を 3 つ束ねる: **(1) `BACKOFF_FIXED`** = 量を単一軸に固定する合成 variant (D18)、**(2) `BACKOFF_NOINLINE`** = perf 帰属用の診断計器 (P2-4)、**(3) `EVOLVE-BLOCK` マーカー骨格** = Phase 3 で coder (LLM) が合成する純 timing 変異の編集面 (D22)。いずれも `cmake/Options.cmake` + `include/backoff.hh` を触り、既定値で inert (stock 不変)。

### EVOLVE-BLOCK マーカー — Phase 3 coder の編集面 (kickoff タスク2, D22/phase3.md)

Phase 3 で coder (LLM) が CCBench コードを diff で書く領域を、`backoff()` 内の `now_backoff` 計算
(BACKOFF_FIXED の `#if/#else/#endif`) に `// EVOLVE-BLOCK-BEGIN <id>` / `// EVOLVE-BLOCK-END <id>`
で画定した (id=`silo-backoff-magnitude`)。**P2-4 inert-patch (D18) の一般化** — 「フラグで枝を切り替える
inert 軸」を「coder が #if 枝の中身を合成する編集面」へ昇格させた骨格。

- **領域内は二枝**: `#if BACKOFF_FIXED >= 0` = coder 合成枝 / `#else` = stock 逐語温存 / `#endif`。
- **マーカー・#else 枝・#if/#else/#endif 骨格は人間が一度入れた不可触骨格**。coder が触るのは #if 枝の
  中身だけ (auditor のレビュー対象を局所化)。
- **閉じた領域制約** (D23 道Y、Phase 3 タスク3 の hook が機械執行予定): #if 枝は既存 silo API を呼ぶ
  straight-line code のみ。`#include`・型/関数/マクロ定義の追加、生 `#if/#ifdef/#elif`、非決定 builtin
  (`__DATE__` 等) を禁止 → 「digest が見る枝 = 実ビルドがコンパイルする枝」を構造保証する。
- **inert は preprocess 後ハッシュで実証**: マーカーは `//` コメントゆえ `cpp -E -P` で除去される +
  既定 `BACKOFF_FIXED=-1` は `#else`=stock を選ぶ → working-tree の preprocess 出力が HEAD 原本と
  **byte-identical** (sha256 `7664020a…`、D23 と不変) → stock genome は cache-hit (規律2、観測者効果なし)。
  source_digest (`orchestrator/campaign/source_digest.py`) が毎評価でこの inert/合成の identity を判定する。
- マーカー走査による digest 対象集合の動的化は non-blocking で繰延 (現状は固定集合 `EVOLVE_BLOCK_SOURCES`、
  D23)。マーカーは `//` コメントで digest に不感ゆえ、固定集合のままでも honest。

**フラグ空間外への最初の踏み出し** (Phase 2→3 の橋渡し)。CCBench の backoff は Cicada 由来の
**適応 backoff** (leader が throughput 勾配で global backoff 値を hill-climbing) で、それが 48thread
高競合で throughput を殺す値に収束しているのが `BACK_OFF=1` の正体だった (critic の帰属、
`output/insights/2026-06-22_p2-3-critic-leading-indicator-attribution.md`)。そこで backoff の*量*を
**静的固定する新フラグ `CCBENCH_BACKOFF_FIXED`** を導入し、量を単一軸として sweep する。

- 変更: `cmake/Options.cmake` (cache var + `ccbench_universal_definitions` に `BACKOFF_FIXED`) と
  `include/backoff.hh` (`backoff()` 内で `#if BACKOFF_FIXED >= 0` なら固定値、`#else` で stock の
  適応 `Backoff_`)。
- **既定 -1 で inert**: preprocess 後ソースが原本と同一になる (`#else` 句を選ぶ) → stock genome は
  cache hit で実証 (B0-L-W0 perf hash 不変)。baseline を汚さない (絶対規律2)。
- **わざと壊したものではない**: backoff は timing のみ変え CC 論理は不変 → serializable。verifier で
  certified を確認済み (`BACKOFF_FIXED=50` で 355,549 commit / 0 anomaly)。pipeline が毎評価ゲートする。
- 使い方: genome に `BACKOFF_FIXED` フラグを足すと `-DCCBENCH_BACKOFF_FIXED=<us>` が渡る。
  driver = `orchestrator/campaign/backoff_sweep.py` (BACK_OFF=1 + 量 sweep を高 abort workload で計測)。

### BACKOFF_NOINLINE — perf 帰属用の診断計器 (P2-4)

backoff ケーススタディ [P0] の機序純度を解くため、backoff() の `_mm_pause`+`rdtscp` busy-wait スピンを
perf record で分離して「有用 IPC」を測る計器。`backoff()` は -O2 で `TxExecutor::abort` に inline され
独立シンボルにならない (perf で spin を関数単位に切り出せない)。`#if BACKOFF_NOINLINE` で
`__attribute__((noinline))` を付け、`Backoff::backoff` を独立シンボル化する。

- **既定 0 で inert**: noinline を付けないので命令列・挙動とも stock 不変。観測者効果も実測で確認
  (BACKOFF_NOINLINE=1 fix10 = 2,623,221 tps vs stock 2,603,521 = +0.76%、between-run floor 3.0% 内)。
  → 機序分析 (spin%/有用 IPC) は noinline build で測り、headline throughput は stock build を引く。
- 使い方: genome に `BACKOFF_NOINLINE` を足すと `-DCCBENCH_BACKOFF_NOINLINE=1`。
  driver = `orchestrator/campaign/backoff_profile.py` (`perf record -e cycles,instructions` →
  `Backoff::backoff` の cycle%/instruction% を分離 → 有用 IPC)。**規律1**: trace と直交 (診断専用)。
  **規律4**: 単一テナント直列・pgrep gate。perf 下 tps は overhead 込みなので headline には使わない。

```sh
SUB=external/ccbench
# izanagi-trace の上に重ねる (Options.cmake / backoff.hh を触る。trace-hook と非衝突)
git -C "$SUB" apply ../../patches/silo-backoff-fixed.patch
# 例: 静的 backoff=50us の variant を build (BACK_OFF=1 必須)
cmake -S "$SUB" -B "$SUB/build-bf50" -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF \
      -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 \
      -DCCBENCH_BACK_OFF=1 -DCCBENCH_BACKOFF_FIXED=50
cmake --build "$SUB/build-bf50" --target ycsb_silo.exe -j
```

価値が確定したら (sweep で stock を上回るなら) izanagi-trace / upstream への昇格は**人間が判断**する
(D18、CLAUDE.md「勝手に上流へ PR を出さない」)。

---

## variant-*.patch — coder 編集の固定 (Phase 3)

coder (LLM) の EVOLVE-BLOCK 編集を orchestrator が diff 監査のうえ patch 化したもの
(silo-backoff-fixed.patch の骨格 + 合成枝の中身、を素の tree に一発で当てる合成 diff)。
`patchharness.applied()` で apply → resolve → build → revert の順に使う。

- **variant-noop-else-copy.patch** — kickoff 完了条件 1 (identity 後方互換)。合成枝 =
  #else 枝の逐語複写。src_token=stock に解決され cache-hit することの実証用。
- **variant-backoff-static50.patch** — kickoff 完了条件 2 (合成枝 1 周)。静的 50us
  (sweep 済み非勝者点 — リーク制御)。certified 緑。
- **variant-backoff-red-1e9.patch** — 後続段 2 (S4 consumer)。合成枝 = 1e9 µs (1000 秒)
  の過大 backoff で trace-timeout (liveness-red) を**意図的に**出す赤 variant。値の根拠:
  trace timeout 120 秒の 8 倍で決定的に発火し、driver 異常死で孤児化しても約 17 分で
  spin を抜けて自然終了する (無限に CPU を焼かない)。**隔離規約 (broken-silo と同型):**
  perf/correctness の baseline・正系列 campaign に決して混ぜない。専用 campaign
  (search_tag=s4-red-consumer) でのみ評価する。buildcache に成果物は入るが cache-hit は
  同一 src_token に限られるため正系列で再利用されることはない。

---

## silo-sort-variant.patch — write_set 施錠順序 comparator 軸の骨格 (Phase 3 段 5, D41)

段 5 (sort-strategy) の coder 編集面。write_set の lock 獲得順序を決める comparator を、stock の
`WriteElement::operator<` (silo_op_element.hh) の代わりに coder (LLM) が合成する軸。D22 で撤回された
案を 3 レンズ敵対レビューで条件付き採用した (D41、実装前必須 7 点)。

- `cmake/Options.cmake` に universal 相乗りの `CCBENCH_SORT_VARIANT` (既定 0 = stock、silo 専用だが
  protocol CMakeLists が ALLOWLIST 外改変になるのを避けるため universal に相乗り、他プロトコルには
  無害なマクロが渡るだけ、D41 決定5) を足し、`validationPhase()` の sort 呼び出しに EVOLVE-BLOCK
  マーカー (id=`silo-writeset-sort`) を画定。`#if SORT_VARIANT` 枝が coder 合成 comparator、`#else` が
  stock 逐語温存。値でなくコード片 (comparator) の変異のため `BACKOFF_FIXED` の数値 sentinel でなく
  単純な on/off スイッチ。
- **既定 0 で inert**: preprocess 後ソースが原本と byte-identical (`#else` を選ぶ) → stock genome は
  cache-hit (規律2、D18/D23 sentinel 規約)。閉じた領域制約は backoff 軸と同型 (既存 silo API を呼ぶ
  straight-line code のみ・新依存/生 preprocessor 指令/非決定 builtin 禁止、D23 道Y)。
- **順序は correctness の入力にならない** (trace schema は C/R/W/X のみで lock 獲得順を見ない) ため、
  comparator 変異は serializability を壊さない = 安全な変異面 (D41 の objection 1 読み替え)。同梱の
  合成枝は正当な comparator の一例 (`storage_`/`key_` 順)。

---

## broken-silo-permutation-erase.patch / broken-silo-permutation-swap.patch / broken-silo-sort-nonswo.patch — sort 軸の positive control (Phase 3 段 5, D41)

**わざと壊した CC** (positive control) 3 本。段 5 の死角 1 (非 strict-weak-order comparator の UB —
libstdc++ の introsort が SWO 契約違反で OOB read/write・要素欠落を無音で起こしうる。かつ D38 の被覆
assert は comparator に関わらず常に通るのでこの軸に歯を持たない) を閉じる **permutation 保存検査**
(sort 直前後の `write_set_.size()` と `rcdptr_` multiset の不変性、`#if TRACE` 内、D41 決定2) が
歯を持つことを機械実証する。

- **broken-silo-permutation-erase.patch** (`IZANAGI_BREAK_PERMUTATION`): sort 直後に 1 要素を
  pop_back → 要素欠落。permutation 保存検査が P (size-changed) で赤。
- **broken-silo-permutation-swap.patch** (`IZANAGI_BREAK_PERMUTATION_SWAP`): sort 直後に 1 要素の
  `rcdptr_` を別要素で上書き (size 不変・multiset だけ変化) → erase の相補形。検査が
  P (rcdptr-set-changed、size-changed ではない) で赤。size だけ見る検査では捕まらないことも実証する。
- **broken-silo-sort-nonswo.patch** (非 SWO comparator, D41 決定1): EVOLVE-BLOCK 内に反対称性を破る
  comparator (`&a != &b` = 相異なる 2 要素で comp(a,b)/comp(b,a) が両真) を置く。libstdc++ introsort を
  `write_set_.size() >= 16` (partitioning 閾) で hang させる (release/ASan 両ビルドで確認)。
  「小サイズで crash しない」は安全の証拠にならない (D41 死角1) — 必須条件 1 (ASan/UBSan で
  「クラッシュしない」と「メモリ破壊が無い」を区別) の一次防壁。
- **既定 OFF inert**: `IZANAGI_BREAK_PERMUTATION*` は裸マクロで pipeline から定義不能。sort-nonswo は
  `SORT_VARIANT` 枠内だが意図的破壊ゆえ専用 characterization でのみ重ねる。baseline に絶対混ぜない
  (broken-silo と同じ隔離規約、絶対規律2)。
- **駆動の正本 = `orchestrator/campaign/s5_permutation_coverage.py`**
  (`output/env/linux-baremetal/calibration/s5_permutation_coverage.json` に実走結果)。

---

## silo-backoff-trigger-gating — abort 要因 gate 軸の骨格 + positive control (Phase 3 段 8a, D48)

段 8a (axis-proposer) 由来の初の軸。abort 要因 (施錠競合 / read-vali ×2 / node-vali /
absent) で `Backoff::backoff()` の発火可否を gate する。軸定義の正本 = シート insight
(`output/insights/2026-07-10_s8a-stage-b-sheet-backoff-trigger-gating.md`) + D48。
軸定数 (MARKER_ID/`_BASE`/PIN 等) は `orchestrator/campaign/axis_trigger_gating.py`
(C 段成果物 — D 偵察器と E 段 driver の両方がここから import する、axis-onboarding §1)。

- **silo-backoff-trigger-gating-variant.patch** — 骨格 (template patch)。要因 enum +
  file-scope thread_local + 7 代入点全 store + begin() sentinel リセット + gate 器 +
  EVOLVE-BLOCK マーカー (id=`silo-backoff-trigger-gating`、hole = gate 述語の代入 1 行のみ。
  `Backoff::backoff` 呼出と gate 変数はマーカー外 = coder 不可触) + `cmake/Options.cmake`
  universal 相乗り (`CCBENCH_BACKOFF_TRIGGER_GATING`、既定 0)。**既定 0 で inert**:
  骨格全体が `#if BACKOFF_TRIGGER_GATING` 囲みで preprocess 後に原文一致 →
  stock genome は src_token="stock" (D48 決定 2/F1、identity 実証済み 2026-07-10)。
  要因記録は gate が perf ビルドで読む CC-native メタデータ — `#if TRACE` に入れては
  いけない (規律 1 の「CC 本来のもの」側)。PIN 前進はしない (D48 決定 2)。
- **instr-silo-backoff-trigger-gating-tally.patch** — 検証専用計装 (characterization
  時のみ骨格の上に重ねる)。abort() 冒頭で `A <要因>` 行を emit (`#if
  BACKOFF_TRIGGER_GATING && TRACE`)。**template patch に入れない理由:** 入れると
  variant の TRACE=1/0 preprocess 差分が pinned HEAD のそれと食い違い diff-of-diffs
  (`assert_trace_diff_matches_head`) が全ループ評価で fails-closed になる。骨格 store は
  coder 不可触 (DiffQuarantine 行単位拒否) ゆえ C 段の一度きりの歯の証明で記録正確性は
  ループ中も構造的に不変。
- **broken-silo-trigger-misattr.patch** — **わざと壊した記録** (positive control)。
  施錠競合を `IZANAGI_BREAK_TRIGGER_MISATTR` 定義時に kNodeVali へ故意誤記録。
  serializability 無傷 (verifier 緑のまま = trace schema の死角の実走証明) だが
  YCSB の構造ゼロ検査 (node-vali==0 のはず) が赤になる = 検査の歯。**既定 OFF inert・
  裸マクロは CCBENCH_ 外 = pipeline から定義不能** (broken-silo と同じ隔離規約、規律 2)。

**駆動の正本 = `orchestrator/campaign/s8a_trigger_coverage.py`** (骨格+計装 t4/t1 +
misattr t4 の 3 run、保存則 = A 行総数==abort_counts_ / 構造ゼロ / 赤の歯を機械判定)。
実証 (2026-07-10, `output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json`):
skeleton t4 = 8066 abort 全数一致・構造ゼロ 5 種すべて 0・certified / t1 = abort 0 /
misattr = node-vali>0 で赤 (保存則は破れない = 保存則だけでは捕まらないことも機械証明)。

---

## トレース形式 (verifier = タスク2 の入力契約)

trace-hook の**実装**は submodule `izanagi-trace` ブランチにある (Silo は `writePhase` の `maxtid`
確定後、si は `si_commit` の write install 直後に emit)。出力する**形式**は verifier
(`orchestrator/verifier/`) の入力契約なのでここに記録する。

per-thread ファイル `trace_<thid>.log`、1イベント1行。1 trx の records は連続 (C → その R/W 行):

```
C <txid> <thid> <epoch> <tid>             committed txn。<epoch>,<tid> = commit順 = この trx が産んだ版ID
R <txid> <key_hex> <ver_epoch> <ver_tid>  read。見た版 (ver_epoch,ver_tid)
W <txid> <key_hex> <op> <epoch> <tid>     write。op∈{U,I,D}。新版 = この trx の commit (epoch,tid)
```

- `txid` = グローバル単調 id (TRACE ビルド限定の atomic)。1 trx の C/R/W をまとめるためだけ。
- `key_hex` = キー生バイトの小文字 hex (YCSB は 8byte big-endian)
- **版ID = (epoch,tid)。** 同一キー上では producer trx を一意に決める (ww 競合で tid が単調増加)。
- **genesis 版 = (epoch=1, tid=0)** (初期 DB ロード、producer 無し)。si は cstamp=0 がこれに自然一致。

### verifier が辺を復元する方法

- **wr 辺** (T_w → T_r): R の (key,e,t) を、commit (e,t) でその key を書いた W の trx (producer) に対応付け
- **ww 辺**: 同一 key を書いた trx を (epoch,tid) 順に並べる
- **rw 辺 (anti-dependency)**: R が版 V を読み、別 trx が同 key により新しい版を書いたら T_r → T_w
- **G2**: rw 辺を1本以上含む cycle

### trace-hook の検証実績

- タスク1 (Silo): trace の C 行合計 = ベンチ `commit_counts_` 完全一致、非 genesis read の 100% が
  producer に matchable・ORPHAN 0・版重複 0、`TRACE=0` ビルドに trace シンボル 0。
- タスク3B (si): si=本物の write-skew を 3576 G2 として検出、同 workload で Silo は緑 (real-CC discrimination)。
- **ermia cross-check の罠 (将来増分):** `ermia` (SSN on=serializable) を green oracle にするには
  `cc/ermia/transaction.cc` にも hook が要るが、版 cstamp が `cstamp<<1` (低ビット=SSN flag,
  `ssn_commit:561`) で si と違い、commit 経路も `ssn_commit`/`ssn_parallel_commit` の2系統。
  version id 写像をこの shift に合わせないと全 read が orphan 化する。`izanagi-trace` に追加する想定。
