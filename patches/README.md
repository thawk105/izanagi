# patches/ — Izanagi の CCBench 改変

CCBench (`external/ccbench` submodule = `thawk105/ccbench`) への Izanagi 由来の改変は
**性質ごとに行き先を分ける** (D16。当初は全て out-of-tree patch だった = D6):

| 改変 | 性質 | 行き先 |
|---|---|---|
| スレッドピンニング (`-DLinux`) | CCBench 本物のバグ修正 (Izanagi 非依存) | **submodule `master`** に還元 |
| trace-hook (Silo/si の `#if TRACE` 検証計装) | Izanagi の verifier 入力。`#if TRACE` で観測者効果セーフ | **submodule `izanagi-trace` ブランチ** (submodule が追う) |
| broken-silo (わざと壊した Silo) | verifier の赤検出用 positive control = **テスト用の意図的バグ** | **out-of-tree patch** (このディレクトリ。永久) |
| 合成 variant (例: 静的 backoff `BACKOFF_FIXED`) | Izanagi がフラグ空間外に合成した**評価中の正当な variant** (D18) | **out-of-tree patch** (価値確定まで。昇格は人間判断) |
| SS2PL ロック規律スタディ (`ss2pl-lock-protocol-study.patch`) | 合成 variant (D790。既定 `IMPL=0, KIND=1, DLR=1` は stock 逐語)。既定 OFF の待ちグラフ計器 (D791。閉路の立った tick ごとに標準出力へ `ss2pl-wfg/v2` の 1 行 JSON、同じ文字列を durable file にも書く。runner の検証器と 2026-09-17 に接続、一次資料 `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/`) と YCSB target・計数・テスト接続の修正を同梱する。使い方と既知の不足は `docs/cc-diagnostics.md` | **out-of-tree patch** (昇格・上流還元は人間判断) |
| 診断計器 (例: `BACKOFF_NOINLINE`) | perf 帰属用の計器 (D20 第 5 類)。既定 inert — ただし inert は各 patch が witness (実測・実 TU/binary) で個別に立証する義務であり、default-OFF 構文だけでは導けない | **out-of-tree patch** (このディレクトリ) |
| Cicada 版探索・版保持の計器 (`instr-cicada-version-lifetime.patch`、VHash md_2・md_15) | 診断計器 (D20 第 5 類)。`IZANAGI_CICADA_VLIFE` (探索・K 反事実・楽観的 forwarding 候補・GC 境界の計数、md_15 で ro 比率の実行時 flag・公開間隔の分割・境界保持種別を追加) と `IZANAGI_CICADA_LONGTX` (長い tx 2 型、md_15 で種別固定 flag を追加)。既定は preimage と前処理・`.text`・`.rodata` が一致 (実測) | **out-of-tree patch** (preimage = gitlink `68106660`。`ledger.json` には登録しない) |
| mocc 計装 (`instr-mocc-lock-coverage.patch`、mocc の `#if TRACE` lock 被覆・permutation 検査) | Izanagi の verifier 入力 (X/P 行)。D14 契約で perf build から完全除去し、`#line` で TRACE=0 の前処理出力と `.text` を preimage と同一化 | **out-of-tree patch** (preimage = submodule `e9e477ca`。pin 前進 [T-2295] で izanagi-trace 側へ移すかは人間判断) |
| Cicada 計装 (`instr-cicada-trace.patch`、Cicada の `#if TRACE` trace v2、TPC-C 用の重ね `instr-cicada-trace-tpcc.patch` は v3) と broken-cicada 4 本 | verifier 入力 (C / R / W / E) と、その positive control | **out-of-tree patch** (計装は試作・実走用で、`izanagi-trace` 枝への移送と pin 前進は人間判断。壊しは永久) |
| broken-mocc (わざと壊した mocc。[T-2294] の 3 本と後続の hot-update-unlock・skip-canonical-restore) | mocc 計装の positive control = **テスト用の意図的バグ** | **out-of-tree patch** (このディレクトリ。永久) |
| 劣化 rung (例: `silo_ladder_rung1`) | **正しさを保ったまま性能だけを意図的に損なう** ability probe (D18 第 4 類 subtype `evaluation_role=ability_probe`)。研究目標に数えず recovery pipeline へ直結しない | **out-of-tree patch** + `ledger.json` 登録必須 (現行契約は entry 数 1 固定) |

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
- **perf ビルド** (`build/`, 既定 `-DCCBENCH_TRACE=0`): trace は `#if TRACE` で完全に消える。
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
  straight-line code のみ。ただし `silo-backoff-magnitude` の hole は D836 / D901 条項 1 により
  「接尾辞なしの数値 literal 1 個・ちょうど 1 文」へ限定される (骨格 patch のコメント自体は
  identity 保持のため不可触。上書きしたのは受理文法と `src/coder-spec.md` である)。`#include`・型/関数/マクロ定義の追加、生 `#if/#ifdef/#elif`、非決定 builtin
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
`output/insights/2026-06-22_p2-3-critic-leading-indicator-attribution.md`)。
**この収束は CCBench 既定 3 定数 (刻み 100 µs / 上限 1000 µs / 更新間隔 10 µs) の下での観測であって、
適応 backoff という機構一般の劣位ではない** (2026-09-02 追記)。同じ機構でも更新間隔を広げれば
最適帯へ寄り、既定との差は定数の選択だけで出る (D1505 / D1506、一次資料
`output/insights/2026-09-02_cicada-adaptive-three-constants.md`)。そこで backoff の*量*を
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

#### hole の式は v3 (静的値の上限を 9999 へ広げた版) になっている

2026-09-07 に、合成枝 (hole) の**最終 fallback だけ**を「1000 で割った余り」から
「生値から 2000 を引いた値」へ変えた。骨格・マーカー・stock 枝・待機ループ・
`0`〜`2999` の復号結果は 1 byte / 1 数値も変えていない。

**符号化は生値 (`BACKOFF_FIXED` に渡る整数) と物理値 (実際に待つマイクロ秒) を分ける。**

| 生値 | 意味 |
|---|---|
| `-1` | stock の適応 backoff (inert) |
| `0`〜`999` | 一定待ち。物理値 = 生値 |
| `1000+μ` | μ/2 から 3μ/2 の対称 modulo (待ち方の形) |
| `2000+μ` | μ/2 か 3μ/2 を確率半々 (待ち方の形) |
| `3000`〜`11999` | 一定待ち。**物理値 = 生値 − 2000**、すなわち 1000〜9999 マイクロ秒 |

**したがって「生値 = マイクロ秒」ではない。** 静的な 1000 マイクロ秒は生値 3000 で表す。
生値 1000 は静的 1000 ではなく「形 1・振幅 0」であり実質 0 マイクロ秒になる (F718)。
生値 12000 以上と、静的域に無い生値 1000〜2999 は Python 側の codec が拒否する
(`orchestrator/campaign/backoff_extended_sweep.py` の `encode_static_backoff_us` /
`decode_static_backoff_us`)。上限 9999 は設計判断であり、丸めと桁あふれから遠い域に取ってある。

B-10 の shape grid (μ = 2〜100) はこの拡張を使わない。使うのは静的 tail の driver である。
この変更に伴い B-10 事前登録は v5 になり、`patch_sha256` と `formula_sha256` を付け替えた。
v4 の下で完了した 135 cell は v4 のまま残す。

#### hole の式は v2 (B-10 の待ち方符号化) になっている

2026-08-26 の B-10 (待ち方 / 待ち量の直交切り分け) で、合成枝 (hole) の 1 行を待機の*形*も
選べる固定式へ更新した。骨格・マーカー・stock 枝・待機ループは 1 byte も変えていない。

- `-1` = 従来どおり stock の適応 backoff (inert)。
- `0`〜`999` = 従来と**数値的に同一**の一定待ち μ マイクロ秒。
- `1000+μ` = μ/2 から 3μ/2 の対称 modulo。`2000+μ` = μ/2 か 3μ/2 を確率半々。
  どちらも指示値の平均は厳密に μ で、乱数は同じ撹拌器と `backoff()` 入口の `rdtscp` 値だけを使う。
- `3000` 以上は当時 C++ で「1000 で割った余り」へ落ちた。B-10 driver は今も grid 外として
  起動前に拒否する。**この行は v2 当時の記述であり、`3000` 以上の復号は上の v3 で変わった。**

**同じ 0〜999 でも、preprocess 後のソース・`src_token`・variant 識別子は v1 と v2 で変わる。**
既存の凍結成果物・WAL は変更していないが、旧 consumer を再走して**旧 campaign へ resume してはならない**
(同じ campaign に別 ID が積まれる)。逐語と検査の正本は
`orchestrator/campaign/b10_backoff_shape_sweep.py` の `EXPECTED_HOLE_LINE` と実行時 preflight。

#### 式 v1 の patch は `silo-backoff-fixed-v1.patch` として別名で凍結してある

2026-09-16 に、合成枝の式が v2 へ変わる直前の本 patch (v1) を bytes のまま
`patches/silo-backoff-fixed-v1.patch` として保存した (D1098 / D1281、[T-1907])。

| 項目 | 値 |
|---|---|
| 取得元 | `4dfd3785b^:patches/silo-backoff-fixed.patch` (この bytes を入れた commit は `4f7bb3c76`、2026-07-02) |
| git blob | `f7a54445764025112317151106712bb9d97678ab` |
| sha256 | `35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911` |
| 前提とする元 blob | `cmake/Options.cmake` = `b9a3c74`、`include/backoff.hh` = `3db8c08` (CCBench `6656e93` と `511c953` の両方で同一) |

- 中身は v1 の最終版で、合成枝の式 `static_cast<double>(BACKOFF_FIXED)`、noinline 計器、
  EVOLVE-BLOCK マーカー、`BACKOFF_FIXED` 未供給時の `#error` を含む。v2 との差は合成枝の式 1 行だけである。
- 初版 (2026-06-22 の blob `476a128`) とは bytes が同じではない。式の行は同じだが、noinline 計器・
  マーカー・`#error` を含まない。旧 static-backoff sweep の 3 WAL (`output/s1-freeze/` と
  `output/s8b-freeze/` の凍結 file が path と SHA を持つ) を生んだ patch の bytes は WAL にも lock にも
  記録が無いので、この file をその生成時の bytes とは呼ばない。
- 用途は、歴史的な v1 のソースを repo 内の固定 path で参照し、必要なら明示的に適用することに限る。
  旧実験の完全な再現や、現行 consumer が v1 を使うことは保証しない。
- 現行の `silo-backoff-fixed.patch`・各 consumer の参照先・凍結成果物・WAL・`ledger.json` は変えていない。
  この file を自動で読む driver は無い。
- **bytes を pin する検査は置いていない** (依頼が pin・gate・台帳の追加を scope 外とした)。この file を
  改変しないこと。直下の `*.patch` を走査する既存の在庫検査 (define 在庫と `IZANAGI_` token 在庫) の
  走査対象には入る。
- 上の v2 節の「旧 campaign へ resume してはならない」は残す。補足として、現行の `backoff_sweep.py` と
  `backoff_repro.py` は campaign 識別子へ build admission policy を必ず束縛し、policy を持たない旧 lock
  への resume は識別子の照合で拒否する (コードの読解による。実走では確かめていない)。

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

## cicada-adaptive-params.patch / cicada-adaptive-dynamic.patch — Silo 上の Cicada 型 adaptive backoff の 3 定数と、その動的化 (合成 variant, D18 第 3 類)

**A = `cicada-adaptive-params.patch`** (sha256 `9b2153e0…`、bytes 不変) は、stock の `include/backoff.hh` に
焼かれた 3 定数 (刻み `kIncrBackoff` = 100 µs / 上限 `kMaxBackoff` = 1000 µs / 更新間隔 10 µs) を CMake cache option
`CCBENCH_BACKOFF_INCR_MILLI` / `CCBENCH_BACKOFF_MAX_US` / `CCBENCH_BACKOFF_UPDATE_US` (既定 = stock 同値) にする。
測定と裁定は D1505 / D1506、一次資料 `output/insights/2026-09-02_cicada-adaptive-three-constants.md`、
正しさ (調整済み定数 24 trace の認証) は `2026-09-04_t2189-adaptive-serializability-certification.md`。

**B = `cicada-adaptive-dynamic.patch`** は **pin `511c9538` + A を当てた木だけを preimage とし、A の上に重ねる**
(pin 単独には当たらない)。触るのは A と同じ `cmake/Options.cmake` と `include/backoff.hh` の 2 file で、
**`#include` 行を 1 行も足さない** (`source_digest.assert_includes_match_head` は `include/backoff.hh` の include 行を
HEAD と逐語比較するため)。CMake option 7 つ (既定はすべて stock 同値、`#ifndef ... #error` で欠落を止める):

| option | 既定 | 意味 |
|---|---|---|
| `CCBENCH_BACKOFF_COUNT_WINDOW` (K) | 0 | 0 = stock の時間判定。K>0 = 経過 ≥ `UPDATE_US` (counter を読む最小間隔) かつ (commit 数 ≥ K または 経過 ≥ cap) で更新 |
| `CCBENCH_BACKOFF_COUNT_CAP_US` | 0 | 計数窓の最大間隔 (0 = `UPDATE_US`)。K=0 のとき inert |
| `CCBENCH_BACKOFF_STEP_ADAPT` | 0 | 1 = 勾配符号が前回と同じなら刻み ×2 (上限 STEP_MAX)、反転または 0 なら ÷2 (下限 STEP_MIN)。整数 µs だけ |
| `CCBENCH_BACKOFF_STEP_MIN_MILLI` / `_MAX_MILLI` | 100000 | 適応刻みの下限 / 上限 (1/1000 µs)。`STEP_ADAPT=0` のとき inert |
| `CCBENCH_BACKOFF_DYN_CEILING` | 0 | 1 = 実効上限 `ceiling_` を持ち、上限に当たって負勾配なら半減 (下限 50 µs)、正勾配なら倍増 (上限 `MAX_US`) |
| `CCBENCH_BACKOFF_TRACE` | 0 | D14 契約の `#if BACKOFF_TRACE` 診断計器。leader の更新ごとに (窓の経過・commit 数・発火理由・前後の `Backoff_`・勾配符号・刻み・上限・parity 分岐) を 64-byte aligned の ring (65,536 件) に溜め、正常終了時に `IZANAGI_BACKOFF_TRACE v=1 …` 行として stdout へ流す。**perf build (0) では symbol・文字列とも 0 個** (probe が `nm` / `strings` で fail-closed に検査)。`CCBENCH_TRACE` (verifier 用) とは別 macro |

- 時刻 seam: `check_update_backoff_at(now, committed)` / `update_backoff_at(now, committed)` を本体にし、production の
  `check_update_backoff()` / `update_backoff(committed)` は `rdtscp()` を渡す wrapper。既定値では制御流が stock と一致する
  (`orchestrator/tests/test_dynamic_backoff_transitions.py` が pin + A 単独の driver と `Backoff_` 列の一致を固定)。
- `last_backoff_` は stock どおり `uint64_t` のまま。sub-µs の刻みは偽ゼロ勾配を作る (T-2216 §3) ので、B の刻みは整数 µs に限る。
- 登録簿: 7 define は `orchestrator/campaign/condition_meaning_gate.py` の `DefineSpec` (patch_rel = B) と
  `screening_driver.py` の `_CONDITION_DEFAULTS` に登録。**toggle 依存の限界**: `_is_inert_value` は単項で、従属 parameter
  (`COUNT_CAP_US`, `STEP_MIN/MAX_MILLI`) は既定値一致だけを stock と扱う (toggle が on のときの意味は見ない)。
  probe の build sink は deferred gate 台帳に載っており、この限界は本 wave の成果物に影響しない。
- **`ledger.json` には登録しない**: 同台帳の scope は D18 第 4 類 ability probe 専用で、真の consumer
  `orchestrator/campaign/silo_ladder_rung1_contract.py` が entry 数 1 を exact に要求する。B は第 3 類の合成 variant。
- driver は既存の `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` (拡張 cell 書式 11 field、`--backoff-trace`
  の診断 mode、certify の exact 2 値)。事前登録は `docs/dynamic-backoff-preregistration.md`。

## cicada-adaptive-counterfactual.patch — 方向的中の反実仮想対照 (合成 variant, D18 第 3 類, [T-2265])

**C = `cicada-adaptive-counterfactual.patch`** は **pin `511c9538` + A + B を当てた木だけを preimage
とし、B の上に重ねる** (pin 単独にも pin+A にも当たらない)。触るのは A / B と同じ
`cmake/Options.cmake` と `include/backoff.hh` の 2 file で、**`#include` 行を 1 行も足さない**。
CMake option は 3 つ (既定はすべて stock 同値)。step policy と seed は
`#ifndef ... #error` で欠落を止め、terminal deadline は trace 有効時だけ同じ欠落検査を行う。

| option | 既定 | 意味 |
|---|---|---|
| `CCBENCH_BACKOFF_STEP_POLICY` | 0 | 0 = stock / 1 = 常に反転 / 2 = 更新ごとに 1/2 で無作為に反転。`static_assert` で 0/1/2 に限る |
| `CCBENCH_BACKOFF_STEP_POLICY_SEED` | 11400714819323198485 | policy 2 の決定的 LCG の種。`STEP_POLICY != 2` のとき inert |
| `CCBENCH_BACKOFF_TRACE_TERMINAL_US` | 0 | count-closed terminal event の期限。0 = 無効。trace 有効時だけ値域検査と実装が残り、cohort 2 は 5000000 を使う |

- **反転点は 1 箇所。** `#if BACKOFF_STEP_ADAPT` 枝と非 `STEP_ADAPT` 枝の共通の出口の後、clamp の前。
  反転するのは `new_backoff` に付いた差分の符号だけで、parity 分岐 (`gradient == 0`) が選んだ一歩も含む。
- **真の勾配のまま更新するもの:** 窓の発火判定・勾配・`adaptive_step_`・`last_gradient_sign_`・`ceiling_`。
- policy 2 の割当は `state = state * 6364136223846793005 + 1442695040888963407 (mod 2^64)` の bit 63。
  勾配 0・推奨差分 0・clamp のときも毎更新で進める。既定 seed の最初の 16 割当は `0111001000100110`
  (実装を読まずに式から独立再計算して一致を確認)。
- count cap は `elapsed / clocks_per_us_ >= cap_us` で判定し、巨大 cap と TSC 換算値の積を作らない。
  `clocks_per_us_ == 0` は CLI の実在入力なので更新判定を止め、整数 0 除算を避ける。この比較は
  trace 計装ではなく CC 本来の機構であり、trace 無効 build にも残る。
- **診断 trace の stdout は v=3 へ上がる** (`#if BACKOFF_TRACE` の中だけ。規律 1)。既存 12 項目の書式と順序は
  変えず、`recommended_delta_sign` / `assigned_invert` / `inversion_realized` / `both_actions_feasible`
  / `terminal_flush` の 5 項目を足す。**`both_actions_feasible` は割当を適用する前**に pre-state から求める
  (`inversion_realized` での層別は処置後選択になり偏るため、偏らない副解析の材料を先に残す)。
  通常 event は `terminal_flush=0`。cohort 2 では init から 5000000 us 以後の最初の count 閉鎖を、
  controller 更新と LCG 割当の前に `trigger=3 assigned_invert=-1 terminal_flush=1` として 1 件だけ記録する。
  terminal を記録した呼出しだけ controller 更新を止める。その後は controller と LCG 割当を通常どおり進め、
  trace event の追加だけを抑止するため、terminal は常に末尾になる。worker と extime も通常どおり進む。
  summary は `updates` = 通常 event 数、`retained` = 保持した通常 event 数、`dropped` = 失った通常 event 数、
  `flushes` = terminal event 数。terminal 1 件なら `retained=updates`、`dropped=0`、`flushes=1`、
  terminal 0 件なら `updates=retained=通常 event 数`、`dropped=0`、`flushes=0` である。
  driver の parser は旧 stdout v=1/v=2 と新 v=3 を版ごとの連言で受理し、混在・版不一致・項目欠け・
  余分な項目を拒否する。正規化後の schema は terminal 無しの既存 v3 を継続受理し、terminal 付きだけ
  `izanagi-dynamic-backoff-trace/v4` とする。
- cell 書式は 5 / 11 field を不変のまま **12 field** を足す (12 番目 = `step_policy` ∈ {0,1,2})。
  11 field と明示 policy 0 の 12 field は identity 上も区別する。
- 診断走行の exact 述語には **2 本目の literal** を足した (Python と `.pbs` の 2 層に同じもの)。
  **正しさゲートの認証 cell 受理集合は exact 2 cell から exact 4 cell へ制御された拡張を行った。**
  A の hard pin と既存の逐語 pin は変えていない。
  診断入力の受理集合は exact literal 1 本ぶんの**制御された拡張**であり、「緩めていない」とは言わない。
- 登録簿: 3 define は `orchestrator/campaign/condition_meaning_gate.py` の `DefineSpec`
  (patch_rel = C) と `screening_driver.py` の `_CONDITION_DEFAULTS` に登録する。terminal option の
  inert 値は 0 で、trace 専用の CMake 入力として扱う。
- patch stack は A → B → C の exact 順序。既存 cohort 1 の artifact は schema v3 のまま、
  count-closed terminal を要求する cohort 2 の artifact は schema v4 とし、
  事前登録の exact 3 腕・3 workload・threads 24/48・rep 0・reps 1・extime 3 の診断走行にだけ、
  `counterfactual_preregistration` として凍結済み
  `docs/backoff-counterfactual-preregistration.md` の bytes の SHA-256 を記録する。ほかの格子には
  この field を付けない。旧 `prereg_sha256` は旧事前登録の測定条件束縛として残す。
- **科学的な限界:** policy 1 と policy 0 は別走行で最初の更新から軌跡が分岐するので、
  答えられるのは「制御器が選んだ向きの方策全体が throughput に効くか」までであり、
  **同一軌跡上の反実仮想ではない。** policy 2 が同一 pre-state の対照に近づくが、
  **[T-2265] wave では一切測定していない** (F660 により機構の着地と実測を分けた)。
  一次資料は `output/insights/2026-09-07_t2265-backoff-counterfactual/README.md`。

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

## cicada-forwarding-variant.patch — Cicada の選択的 forwarding (合成 variant, D18 第 4 類, VHash 論文 md_6)

VHash 論文 (`docs/paper-story-vhash/`) の「cold 境界 (論理的な K 版) で発火する選択的 forwarding」の試作。
物理的な hot 配置は作らず、「先頭から K 版より奥を辿る必要がある」read で transaction の timestamp を前進させる (構成 C)、
または同じ条件で abort して新しい timestamp で再実行する (構成 F)。GC の保護 (ThreadWtsArray / ThreadRtsArray / MinRts / MinWts) は変えない。
**正しさ検査 (Cicada の検査器) を通していない。この patch を使った値はすべて「未検証の診断値」であり、serializable とは書かない。**

- **preimage:** CCBench pin `68106660686232781bca3be792a750d3e19d7a8a` の `cc/cicada/transaction.cc` と `cc/cicada/ycsb_cicada.cc`。
  `include/*.hh`・`include/ycsb.hh`・`common/runner.hh` は変えない。
- **macro (未定義 = 0 = stock と同じ前処理結果):**
  - `CICADA_FWD_ENABLE` (owner `cc/cicada/transaction.cc`): forwarding の本体。実行時 flag `--cicada_fwd_policy=c|f` (既定 c)、`--cicada_fwd_k` (既定 3、1〜256)。
  - `CICADA_FWD_COUNT` (同 owner、ENABLE=1 のときだけ意味を持つ): 計数。正常終了時に `CICADA_FWD_V1 {json}` を 1 行出す
    (thread 別: triggers, attempts, success, read_mismatch, write_constraint, conflict, ineligible, no_target, special_after_forward, f_aborts,
    advance_clock_sum, pos_before_sum, pos_after_sum)。**計数入り build の throughput は性能値に使わない。**
  - `CICADA_LONGTX` (owner `cc/cicada/ycsb_cicada.cc`): 長い transaction の 2 型を作る Cicada 専用 workload。実行時 flag
    `--cicada_long_threads` (既定 0 = YcsbWorkload と同じ)、`--cicada_long_kind=many_ops|wait_after_reads`、`--cicada_long_ops` (1000)、
    `--cicada_long_rratio` (90)、`--cicada_long_wait_us` (1000)、`--cicada_wait_reads` (10)。正常終了時に `CICADA_LONGTX_V1 {json}` を 1 行出す。
- **登録:** 3 macro とも `orchestrator/campaign/condition_meaning_gate.py` の許可ドメイン (DEFINE_SPECS・witness・site 数 11 / 4 / 4) に登録済み。
  **`patches/ledger.json` には登録しない** — 同 ledger は `silo_ladder_rung1` 専用で entry 1 件を契約が要求する
  (`orchestrator/campaign/silo_ladder_rung1_contract.py` の ledger 検査)。依頼文 (md_6) の「ledger の entry」とはこの点で食い違い、契約を優先した。
  macro 名に `IZANAGI_` 接頭辞を使わないのは合成 variant の命名慣行 (`BACKOFF_FIXED`、`MOCC_TEMP_PREDICATE`) に合わせたもので、登録の代わりではない。
- **driver:** `orchestrator/campaign/vhash_forwarding_prototype.py` (`smoke` / `run --workload normal|many_ops|wait_after_reads` / `aggregate --raw ...`)。
  build ごとに条件 gate の supply / meaning を通してから build する。stock 腕は `CICADA_LONGTX=1` だけの build (forwarding のコードは前処理で消える)。
- **一次資料:** `output/insights/2026-09-29/vhash-forwarding-prototype/README.md`。

## cicada-forwarding-gc.patch / cicada-forwarding-gc-broken-early-publish.patch — forwarding を Cicada の GC 回収境界へつなぐ構成 E と、その壊し正例 (合成 variant, D18 第 4 類, VHash 論文 md_14)

VHash 論文 (`docs/paper-story-vhash/`) の新規性の芯 U0 (abort せず既読を保った前進を、版の回収境界へ反映して保持期間を縮める) を確かめる試作。
`cicada-forwarding-variant.patch` (md_6、構成 C) の**上に重ねる** patch で、読み取りの後に待つ transaction が待機の安全点で自分の timestamp を前進させ、
確定してから GC 用の公開値 (ThreadWtsArray) を上げて GC flag を立てる (構成 E、小モデル md_10 の SP の形、D2290)。
回収そのもの (gc_versions、後続の確定版で回収 = R10) は変えない。
**正しさの判定の上限は indeterminate で、serializable・certified とは書かない。この patch を使った値は「未検証の診断値」として扱う** (検査の結果は一次資料)。

- **preimage:** CCBench pin `68106660686232781bca3be792a750d3e19d7a8a` に `patches/cicada-forwarding-variant.patch` を当てた `cc/cicada/transaction.cc` と
  `cc/cicada/ycsb_cicada.cc`。trace patch (`instr-cicada-trace.patch`) → md_6 → 本 patch の順でも当たる。`include/*.hh` は変えない。md_6 の patch は変えない。
- **macro (未定義 = 0 = md_6 適用後と同じ前処理結果):**
  - `CICADA_GC_SAFEPOINT` (owner `cc/cicada/transaction.cc`、companion `CICADA_FWD_ENABLE=1`): 待機の安全点関数。実行時 flag `--cicada_gc_mode=off|hb|e` (既定 off)。
    hb = GC flag を立てるだけ (ThreadWtsArray・ThreadRtsArray は tx 開始時の値のまま)。e = それに加えて前進 (事前確認 → 既読版 rts を t′ へ CAS-max → seq_cst fence →
    版列を観測し直して可視を確認 → 確定) を試し、**成功したときだけ**別 step で ThreadWtsArray := t′、ThreadRtsArray := max(旧, t′−1) を公開する。失敗したら hb と同じ。
    tx の途中で読み取り下限を最新の MinWts−1 へ上げる形は、待機中に既読版を回収させるので採らない (一次資料 §S7)。安全点では gc_versions を呼ばない。read-only・abort 済み・scan・特殊操作の後は何もしない。
  - `CICADA_GC_WAIT` (owner `cc/cicada/ycsb_cicada.cc`、companion `CICADA_GC_SAFEPOINT=1`・`CICADA_FWD_ENABLE=1`・`CICADA_LONGTX=1`): md_6 の wait_after_reads の待機を
    `--cicada_gc_slice_us` (既定 0 = md_6 と同じ単一 sleep) ずつに分け、各 slice 末で安全点関数を呼ぶ。待機の前後で保持版検査を行う。
  - `CICADA_GC_COUNT` (owner `cc/cicada/transaction.cc`、companion なし = stock の build でも使える): GC の診断と E の計数。`--cicada_gc_sample_us` (既定 10)。
    正常終了時に `CICADA_GC_V1 {json}` を 1 行出す (等間隔標本の回収境界の遅れ・論理生存版数・MinRts を決めた thread、公開 event、begin 標本、保持時間、thread 別の E の計数と保持版検査)。
    **計数入り build の throughput は性能値に使わない。**
- **壊し正例 `cicada-forwarding-gc-broken-early-publish.patch`:** 本 patch の上に重ねる無マクロの無条件 patch (新しい `#if` を足さない)。E の試行の最初に
  ThreadWtsArray := t′・ThreadRtsArray := t′−1・GC flag を立て、確認に失敗しても戻さない (小モデルの UG1 + UF1 相当)。検査専用で、計測には使わない。
- **登録:** 3 macro を `orchestrator/campaign/condition_meaning_gate.py` の許可ドメインへ登録 (DEFINE_SPECS・witness・site 数 3 / 2 / 7)、
  `orchestrator/campaign/screening_driver.py` の既定値表と登録簿テストの件数を 3 macro 分だけ追随 (先例 md_6 と同じ足跡、判定・受理述語と既存 entry は不変)。
  **`patches/ledger.json` には登録しない** (D2288 と同じ理由: 同 ledger は `silo_ladder_rung1` 専用で entry 1 件を契約が要求する)。
- **driver:** `orchestrator/campaign/vhash_forwarding_prototype.py` の `gc-smoke` / `gc-run --workload normal|many_ops|wait_after_reads [--wait-us 1000|10000] [--skew 0.9|0]` / `gc-aggregate --raw ...`。
  md_6 の `smoke` / `run` / `aggregate` は変えていない。比較の Cicada 設定は md_11 の観測最良 `BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0`。
- **一次資料:** `output/insights/2026-09-29/vhash-gc-connection-prototype/README.md`。

## cicada-forwarding-target.patch / cicada-forwarding-target-broken-ignore-mismatch.patch — 構成 C・E の前進先の選び方の knob と、その壊し正例 (合成 variant, D18 第 4 類, VHash 論文 md_21)

構成 C (md_6) と構成 E (md_14) の前進先 (目標時刻) の選び方を実行時 flag で切り替える試作。`cicada-forwarding-variant.patch` → `cicada-forwarding-gc.patch` の**上に重ねる** patch で、
**確認・確定・公開の行は変えず**、目標時刻の計算・1 tx 1 回の抑止・計数だけを足す。**既定 flag では md_6・md_14 と同じ目標と同じ計数行 (V1) になる。**
**正しさの判定の上限は indeterminate で、serializable・certified とは書かない。この patch を使った値は「未検証の診断値」として扱う** (検査の結果は一次資料)。

- **preimage:** CCBench pin `68106660686232781bca3be792a750d3e19d7a8a` に variant → gc を当てた `cc/cicada/transaction.cc`。trace patch (`instr-cicada-trace.patch`) → variant → gc → 本 patch の順でも当たる。
  変更は `cc/cicada/transaction.cc` だけで、`include/*.hh` と md_6・md_14 の patch は変えない。
- **macro:** 新設なし。既存の `CICADA_FWD_ENABLE`・`CICADA_FWD_COUNT`・`CICADA_GC_SAFEPOINT`・`CICADA_GC_COUNT` の内側だけに足した (新しい `#if` 系 directive は 0、
  全 macro 未定義の前処理は gc 適用後と一致)。条件 gate の登録簿 (`condition_meaning_gate.py`) は変えていない。
- **実行時 flag (既定 = 現行):** `--cicada_fwd_target=min|max|partial` と `--cicada_fwd_once` (`CICADA_FWD_ENABLE` の内側)、`--cicada_gc_target=now|max` と `--cicada_gc_once` (`CICADA_GC_SAFEPOINT` の内側)。
  `max` は既読の可視区間に収まる最大の自 thread 形式の時刻 (各既読版の直上の非 aborted 版の wts の最小より小さい最大、「今」で打ち切る)、`partial` は C で目標に届かなくても可視区間の上端まで進む、`once` は 1 tx で目標計算に入るのは 1 回。
  既定以外の flag では計数行を `CICADA_FWD_V2` / `CICADA_GC_V2` (V1 の全 field + `target`・`once`、thread 別 `no_room`・`once_skipped`・`uncapped`、C は `short_success`) で出す。
  **計数入り build の throughput は性能値に使わない。**
- **壊し正例 `cicada-forwarding-target-broken-ignore-mismatch.patch`:** 本 patch の上に重ねる無マクロの無条件 patch (新しい `#if` を足さない)。E の事前確認と再観測の既読不一致の判定を ok とみなし、
  その試行が成功したら `forced_success` を数え、GC 行を常に V2 で出す。検査は E-now (`--cicada_gc_target=now`) で走らせる (E-max は可視区間の内側に目標を取るので到達しない)。検査専用で、計測には使わない。
- **登録:** 条件 gate の登録簿は不変。`orchestrator/tests/test_ccbench_spawn_sites.py` の重ね patch 用の表 `_OVERLAY_BASE_DEFINE_INTERFACES` に
  `cicada-forwarding-gc.patch` の `CICADA_GC_SAFEPOINT` と `cicada-forwarding-variant.patch` の `CICADA_FWD_COUNT` を足した (本 patch の文脈行に両 macro の `#if` が入るため。
  期待件数は不変)。**`patches/ledger.json` には登録しない** (D2288 と同じ理由)。
- **driver:** `orchestrator/campaign/vhash_forwarding_prototype.py` の `target-run --workload normal|many_ops|wait_after_reads [--wait-us 1000|10000] [--skew 0|0.6|0.9] [--smoke]` / `target-aggregate --raw ...`。
  既存の `run` / `gc-run` / `aggregate` / `gc-aggregate` は変えていない。比較の Cicada 設定は md_11 の観測最良。
- **一次資料:** `output/insights/2026-09-29/vhash-forwarding-target-policy/README.md`。

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
  **SWO・permutation 保存・D41 の全 gate を満たす場合に限り**、順序自体は serializability を変えない
  (D41 の objection 1 読み替え)。この条件を外れた comparator (非 SWO 等) は下の positive control が
  示すとおり UB・要素欠落を招くので「安全な変異面」ではない — 安全性は gate 通過に条件づく。同梱の
  合成枝は条件を満たす正当な comparator の一例 (`storage_`/`key_` 順)。

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

## silo_ladder_rung1.patch — 劣化梯子 rung 1 (ability probe、D18 subtype) + ledger.json

**正しさを保ったまま性能だけを意図的に損なう** rung (write-lock CAS の単一 global mutex 直列化 +
identity シンボル + REPORT 第 2 マクロ下の per-worker footer)。[T-139] 裁定 (worklog 2026-07-29
(45)/(54)) による恒久化。設計と実測の正本 =
`output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md` (要件束 = 設計 insight §6)。

- **既定 OFF・裸マクロ** (`IZANAGI_SILO_LADDER_RUNG1`、pipeline から定義不能)。#else に stock 逐語温存
- **stock は常に patch 非適用 tree から build** (行追加型 patch の OFF 状態は `__LINE__` シフトで
  binary 非同一 — 設計 insight §3.4-1)
- **dedicated-driver-only**: 駆動の正本 = `orchestrator/campaign/silo_ladder_rung1.py`
  (correctness/gap-job/collect/verify-result)。通常 campaign・recovery pipeline へ接続しない
- **`ledger.json`**: 機械可読台帳 (closed schema)。`ability_probe: true` /
  `research_goal_eligible: false` / `projection_policy` (coder/planner 射影からの除外字面) を持ち、
  新 rung は登録必須。ただし現行契約 (`orchestrator/campaign/silo_ladder_rung1_contract.py`) は
  entry 数を 1 に固定しており、2 本目の rung を足すだけでは契約検査が違反を記録する —
  登録は必要条件であって、現行 ledger に新 rung を入れる入口が在るという意味ではない。
  射影 tripwire (`orchestrator/campaign/projection_guard.py`) が
  3 つの loop loader でこの policy を執行する (字面回帰検知 — origin 保証ではない)
- 実証 (2026-07-29, request 873917): trace t4 で certified serializable / trace-disabled t48
  N=1m で stock 比 ≈4.4% (W-cal)・≈10.7% (W-hw)、証拠 =
  `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` + raw bundle (pytest が再束縛)

---

## broken-silo-write-intent-{erase,forge,opswap,ptrswap}.patch — write-intent shadow の positive control ([T-152])

**わざと壊した CC** (positive control) 4 本。W 行 emit と lock 被覆検査が同じ `write_set_` を
再走査するため、EVOLVE 枝の要素喪失・捏造が「write が少ない/多いだけの直列化可能な履歴」として
certified になる死角を閉じる **write-intent shadow** (API enqueue の (storage,key,op,rcdptr) を
`#if TRACE` の thread_local shadow へ鏡映し writePhase の W emit loop で双方向照合、I 行 emit)
が歯を持つことを機械実証する。**実装 commit は izanagi-trace ブランチ側** (pin 前進はユーザー
裁定待ち — それまで pinned producer は I を emit しない)。4 本とも挿入位置は validationPhase の
P 検査後・lockWriteSet 前 (P を発火させない単一理由設計)。

- **erase** (`IZANAGI_BREAK_WRITE_INTENT_ERASE`): pop_back で 1 要素喪失 →
  I (intent-missing-from-write-set) のみで赤。
- **forge** (`IZANAGI_BREAK_WRITE_INTENT_FORGE`): 先頭要素を INSERT op で複製追加 (INSERT は
  X 検査対象外) → I (write-set-entry-without-intent) のみで赤。
- **opswap** (`IZANAGI_BREAK_WRITE_INTENT_OPSWAP`): 先頭要素の op_ を DELETE へ改変 (要素数
  不変) → I 2 行 (missing + unexpected) — op 識別子の歯。
- **ptrswap** (`IZANAGI_BREAK_WRITE_INTENT_PTRSWAP`): 要素 2 個の rcdptr_ を交換 → I 4 行/txn —
  rcdptr 識別子の歯。
- **既定 OFF inert**: 裸マクロで pipeline から定義不能 (broken-silo と同じ隔離規約、絶対規律 2)。

**駆動の正本 = `orchestrator/campaign/t152_write_intent_coverage.py`** (対象 ccbench sha は
`IZANAGI_T152_CCBENCH_SHA` で明示、stock/abort 行使/BOMB smoke + broken 4 の 7 run、
単一理由 = I 以外の integrity 全 counter 0 を機械判定)。実証 (2026-07-29,
`output/env/pegasus/characterization/t152_write_intent_coverage.json`): stock 3 run は
I=0/certified (偽陽性なし・BOMB で U/I/D の 3 producer を動的被覆)、broken 4 run は
cycles==0 (verifier 単独なら certify) のまま I だけが赤 → indeterminate。

## instr-mocc-lock-coverage.patch — mocc の lock 被覆・permutation 計装 ([T-2294])

mocc (`cc/mocc/transaction.cc`) に Silo と同じ 2 種の `#if TRACE` 検査を入れる。**真実源は RWLOCK
(`ReaderWriterLock` の counter、`-1` = writer 保持) と CLL (`CLL_` の `LockElement`)** であり、Silo の
Tidword ベース計装 (`instr-silo-*.patch`) は転用しない。preimage は submodule
**`e9e477ca1b55348ab4530de0b1cf663ce4555290`** (branch `izanagi-t1943-mocc-g2-readfrom-witness`、mocc trace v2 hook
入り) で、旧 pin 511c9538 には当たらない (`git apply --check` が拒否する。test で固定)。

- **X (lock 被覆) 3 検査点** — writePhase 内、非 INSERT の write のみ:
  (1) **入口** = C/R/W emit 直後: `CLL_` に `key_ == rcdptr_` ∧ writer `mode_` ∧ `lock_ == &rcdptr_->rwlock_` の要素があり、かつ
  counter が `W_LOCKED` でなければ `X … not-locked-at-entry`。
  (2) **payload 直前** = UPDATE の `memcpy` / DELETE の `remove_value_if_present` の直前: counter が `W_LOCKED` でなければ
  `X … lock-lost-before-write`。
  (3) **publish 直前** = tidword の `__atomic_store_n` 直前: 同条件で `X … lock-lost-before-publish` (mocc は payload・publish・
  `unlockCLL()` が別なので Silo より 1 点多い)。
- **P (permutation 保存)** — validation の `sort(write_set_)` 前後で `size()` と `rcdptr_` multiset を比較し、不変でなければ
  `P size-changed` / `P rcdptr-set-changed`。**P が証明するのは write_set_ sort に対する size と record-pointer multiset の保存だけ**
  で、CLL の順序や施錠順の正しさは主張しない。
- **D14 契約と `#line` 例外**: 実行コード・宣言・`#include <set>` は全て literal `#if TRACE` の first branch 内にある。例外として
  各 `#endif` の直後に preimage の論理行番号を復元する `#line N` だけを置く (`#line` は code を生まない preprocessor 指令)。
  これが無いと後続 `ERR`/`NNN` の `__LINE__` immediate と rip 相対 lea が動き、TRACE=0 binary が preimage と一致しなくなる
  (login probe: comment 30 行で 14 箇所)。
- **規律 1 の witness (2 層)**: (i) 正本 = `orchestrator/tests/test_mocc_proof_surface.py::test_instr_patch_keeps_trace0_preprocess_identical`:
  無 patch と patch 適用後の `transaction.cc` を `g++ -E -DTRACE=0 -DRWLOCK …` (line marker を残す) し、marker を論理行番号へ畳んだ
  (行番号, 非空本文) 列の一致を要求する。`#line` の値が ±1 ずれても赤 (生 byte 一致は `#line` が marker を増やすので構造的に不可能)。
  (ii) 補助 = driver の `trace0_text_identical` check: 無 patch TRACE=0 と patch 適用 TRACE=0 の `objdump -d` (行頭アドレスだけ除去) が
  一致し、`nm -C` の `izanagi` と `strings -a` の `izanagi_trace` / `IZANAGI_` が 0 (JSON `trace0` に両 binary の sha256 と差分行数)。
  source と build の dir 名長は揃える (`__FILE__` 文字列長の差で .rodata が動き lea が 158 行ずれる、login 実測)。
- **RWLOCK 無しの build は暗黙に fail-closed**: `CLL_` / `rwlock_` は `RWLOCK` 定義時にしか宣言されず compile error になる。
  `#error` は置かない (裸 define 登録簿が `RWLOCK` を新設 interface と数えるため)。
- **既知限界**: counter に owner ID が無いため「CLL が stale で他 worker が同じ lock を再取得した」状態は入口検査で区別できない。
  driver の YCSB workload に DELETE は無く、DELETE 経路の検査点は build と静的読解でのみ確認されている。verifier core の P 説明文
  (`orchestrator/verifier/parse.py`) は Silo の `validationPhase` を前提に書かれている (本 wave では verifier を無編集)。
- **verifier の読み手**: 既存 consumer が X → `integrity.lock_coverage_violations`、P → `permutation_violations` に配線し、いずれも
  verdict を indeterminate に倒す (非 certified)。`orchestrator/verifier/model.py` の proof-surface 判定は patch 適用 source を
  X/P evidence-present と判定し、無 patch の e9e477ca / 511c9538 は evidence-absent = 非 certified のまま。
- **実証** (2026-09-07、Pegasus gen_S job 979791、`output/env/pegasus/calibration/s3_mocc_lock_coverage.json`、**14 check all_pass**):
  stock 1 thread = 190,384 txn / 893,376 非 INSERT write で X 0・P 0・certified、stock 4 thread = 203,460 txn で同じく silent。
  TRACE=0 は nm / strings 0、`.text` 差分 0 行、toolchain は policy (gcc/g++ 11) と一致。

---

## instr-mocc-lock-coverage-pin-candidate.patch — X/P hook の pin 候補再現資料 ([T-2844])

preimage は `e9e477ca1b55348ab4530de0b1cf663ce4555290`。branch
`izanagi-mocc-xp-instrumentation` の C = `68106660686232781bca3be792a750d3e19d7a8a`
を可搬に再構成する資料であり、producer や C checkout に重ねる第二の正本ではない。
変更対象は `cc/mocc/transaction.cc` だけ。旧計装の適用結果との差は `<set>` include 1 行の削除と
`std::multiset<const void*>` から `std::unordered_multiset<const void*>` への宣言 2 箇所の置換だけである。
`#line` 7 行は保持し、include 行列は BASE と同一 (`trace.hh` が `<unordered_set>` を供給する)。
旧 patch・旧 JSON は BASE + 旧計装という命題の証拠として保持する。

driver の `--candidate-oid` mode は候補 commit の単一親・raw diff・再構成 blob を build 前に照合し、
C 上で旧行列と同じ 6 走 (stock / lockskip 各 single・high、perm-erase / early-unlock 各 single) を行う。
実走で検査する命題は所定の X/P 発火と verdict、および旧 14 check の範囲である。
P の動的負例は size 違反までで、同サイズ pointer 置換・多重度の保存は source 契約で固定する。
公開 run の `other_integrity_clean` は観測値であり、新しい合否条件にはしない。
候補の実走証拠は `s3_mocc_xp_pin_candidate.json` に別途保存し、旧実測を候補へ引き継がない。
TRACE=0 の正本は D297、driver の nm / strings / 正規化逆アセンブル一致は補助である。
`.text` bytes 一致、hot 経路の再立証、I 被覆は主張しない。候補 mode の build も NON_ADMISSIBLE の診断である。
2026-09-23 [T-2858] で C を現行 pin に採用した (D2227 項 1、値の正本は `orchestrator/campaign/pin.py` の `CURRENT_PIN`)。
本 patch と旧計装 patch の preimage は引き続き e9e477ca であり、C の checkout に重ねない (C は同じ計装を既に含む)。

---

## broken-mocc-lockskip-validation.patch / broken-mocc-permutation-erase.patch / broken-mocc-early-unlock.patch — mocc 計装の positive control ([T-2294])

**わざと壊した CC** 3 本。上の計装が恒真でなく歯を持つことを、実体を名指しして機械実証する。preimage は e9e477ca + `instr-mocc-lock-coverage.patch`。

- **broken-mocc-lockskip-validation.patch** (`IZANAGI_BREAK_MOCC_LOCK_COVERAGE`): validation の writer lock 獲得 `lock(rcdptr_, true)` を
  skip → 入口 (`not-locked-at-entry`) と保持 2 理由が全て正数。1 thread では cycles 0 のまま X で indeterminate、4 thread では
  本物の non-serializable (cycle) も出る。
- **broken-mocc-permutation-erase.patch** (`IZANAGI_BREAK_MOCC_PERMUTATION`): sort 直後に `pop_back()` → `P size-changed` だけ
  (`rcdptr-set-changed` は 0)。
- **broken-mocc-early-unlock.patch** (`IZANAGI_BREAK_MOCC_EARLY_UNLOCK`、**balanced**): 入口検査の後に非 INSERT を `w_unlock()`、
  publish 検査の後・tidword store の前に `w_lock()` で再取得する。counter が `-1 → 0 → -1 → 0` と均衡するので 1 thread run が完走し、
  入口 0 / `lock-lost-before-write` と `lock-lost-before-publish` が正数 = **保持検査だけの歯**を独立に立証する。単純な `w_unlock()`
  挿入は counter を `0 → 1` に壊して次の writer が永久 spin する (`cc/mocc/lock.cc` の `w_unlock` は `counter_++`)。
  裸 directive は file scope の 1 箇所だけ (`static constexpr bool izanagi_break_mocc_early_unlock`) で、2 site は `if constexpr` で従う
  (condition gate は「owner file 内で directive はちょうど 1 回」を要求する)。
- **既定 OFF inert**: 裸マクロ (`CCBENCH_` 接頭辞なし) で pipeline から定義不能。`condition_meaning_gate` / `screening_driver` /
  spawn_sites の裸 define 登録簿に 3 本とも登録済み。baseline に絶対混ぜない (絶対規律 2)。
- **駆動の正本 = `orchestrator/campaign/s3_mocc_lock_coverage.py`** (compute 専用。policy 束縛の gcc/g++、`--third-party-cache` 必須、
  TRACE=1 × 4 + TRACE=0 × 2 の build、6 run、verifier、`compute_checks` 14 key を JSON へ)。`_build_variant` は materializer 登録簿で
  NON_ADMISSIBLE (診断 build、性能値の出所にならない)。configure 引数に CCBench が使わない CMake 変数を渡してはいけない —
  condition gate は configure の stderr 警告 (未使用変数) を fail-closed で red にする (2026-09-07 実測、`RULE_LAUNCH_COMPILE`)。
- **実証** (2026-09-07、job 979791、同 JSON): lockskip 1 thread = 136,905 txn、X 1,927,227 (3 reason 各 642,409)、cycles 0、indeterminate;
  lockskip 4 thread = X 2,382,127、cycles 3,754 (non-serializable); perm-erase = P 221,097 (全て size-changed)、X 0;
  early-unlock = 146,072 txn 完走、`not-locked-at-entry` 0、`lock-lost-before-write` 685,184、`lock-lost-before-publish` 685,184。

---

## broken-mocc-hot-update-unlock.patch — mocc の hot 経路 (update の早期 w_lock) 専用の positive control ([T-2772]、D2134 項 4)

**わざと壊した CC** 1 本。T-2294 の 6 走には hot/cold を弁別する記録が無く、hot 経路 (`update()` の温度述語 true 側で validation 前に w_lock を取る枝) の実行証拠が無かった。本負例は「hot 経路が実行され、既存の X 3 検査点がそこでも歯を持つ」ことを負例の発火で機械化する (計数行は足さない、D2134 項 4)。preimage は e9e477ca + `instr-mocc-lock-coverage.patch`。

- **裸 define `IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK`、balanced**: file scope の 1 directive で `static constexpr bool izanagi_break_mocc_hot_update_unlock = TRACE != 0` (OFF は `false`) と `static thread_local Tuple* izanagi_hot_update_pending` を宣言し、3 site は `if constexpr` で従う。(1) `update()` の hot 分岐 (論理行 459) で `lock(tuple, true)` が成功した直後に `w_unlock()` して pending に記録 (CLL の writer 記録は残す)、(2) `writePhase()` の publish 検査の後・tidword store の前に `pending->rwlock_.w_lock()` で**直接**再取得、(3) `abort()` の `unlockCLL()` 前にも同じ再取得。`TxExecutor::lock()` で再取得すると stale CLL で早期 return し `unlockCLL()` が counter を `0 → 1` に壊すので使わない。各 block の後に `#line` (17 / 460 / 1069 / 1195) で論理行を復元する。
- **発火 workload U = `ycsb_rratio=0, ycsb_rmw=false, ycsb_max_ope=1`** (他は T-2294 の SINGLE/HIGH と同じ)。全操作が `Ope::WRITE` → `tx.update()` の直接呼出で read_set_ を作らない blind update 1 操作。多操作では次の `lock()` の canonical restore が stale CLL 要素を再解放しうるので balanced にならない — **保証は U に限る**。
- **regime は runtime gflag `-temp_threshold`** (0 = hot 強制、21 = cold 強制 (`TEMP_MAX` 20 超)、10 = 既定)。温度は `construct_RLL()` の `failed_verification_` を持つ read でしか上がらないので、blind update では既定閾値で述語は常に false (cold と同じ挙動)。
- **保証名 (D2134 項 4)**: 「stock 等価述語における hot-update 負例の到達と、既存 X 3 検査点の検出」。4 site 全被覆・read 側 hot 経路・RLL 再試行・候補ごとの空振り検査・DELETE 経路の動的被覆は含意しない。
- **既定 OFF inert**: 裸マクロ (`CCBENCH_` 接頭辞なし) で pipeline から定義不能。`condition_meaning_gate` (DefineSpec / witness) / `screening_driver` / spawn_sites の裸 define 登録簿に登録済み。baseline に絶対混ぜない (絶対規律 2)。
- **駆動の正本 = `orchestrator/campaign/s3_mocc_mutation_proof.py`** (compute 専用。旧 driver `s3_mocc_lock_coverage.py` の helper を import で再利用し、旧 driver・旧 JSON・旧 14 check は不変)。36 走 = 3 regime × {1, 4} thread × {stock-W、stock-U、lockskip-W、perm-erase-W、early-unlock-W、hot-update-unlock-U}、受入必須 25 走だけを 32 check に対応させ、観測のみ 11 走は完走 (`matrix_runs_complete_and_terminated`) だけを要求する。別 integrity 異常 (version_dups 等) の clean を要求するのは stock 12 走・hot-update の cold/default 4 走・1 thread の必須負例 7 走だけで、4 thread の負例は lock を故意に欠くため同じ版の重複が正当に起きうる (記録のみ、certified は verifier の値をそのまま残す)。run ごとに実 argv・終了状態・timeout・verifier の raw record を JSON `output/env/pegasus/calibration/s3_mocc_mutation_proof.json` に残す。
- **実証** (2026-09-18、Pegasus gen_S job 5096.nqsv、Elapse 791 秒、fix 後 driver、**32 check all_pass**): hot 強制 (閾値 0) 1 thread = 697,364 txn で
  `not-locked-at-entry` / `lock-lost-before-write` / `lock-lost-before-publish` が各 697,364 (1 txn 1 回ずつ)、P 0、cycle 0、R 行 0、indeterminate。
  hot 4 thread = 2,431,108 txn を timeout なしで完走し X 7,241,088 (reason 別正数は保証しない、観測)。cold (21) / 既定 (10) の 4 走は stock-U と同じく
  certified で沈黙 (1 thread ≈ 110 万 txn、4 thread ≈ 360〜380 万 txn)。stock-W / stock-U 12 走 certified (hot 強制 4 thread でも cycle 0)、
  lockskip cold / default は t1 = 3 reason 正数の indeterminate・t4 = cycle 3,622〜3,882 の non-serializable、perm-erase t1 = P だけ、early-unlock t1 =
  保持 2 reason だけ。trace0 (無 patch ↔ 計装のみ) は nm / strings 0、`.text` 差分 0 行、論理行列 543 行一致。fix 前 driver の compute-1 (5045.nqsv、
  794 秒) も同型で all_pass。
- **観測 (設計が予見していなかったもの、記録のみ)**: (1) lockskip は hot 強制でも 3 reason が正数 — 多操作 txn では `lock()` の canonical restore が先に取った
  早期 w_lock を解放して CLL から消すため、validation の lock skip がそのまま入口違反になる。(2) perm-erase の hot 強制は `pop_back()` で落ちた要素の早期
  w_lock が CLL に残り、read 検証が「W_LOCKED かつ write_set_ に無い」として abort するので 1 秒の commit が 20〜55 txn に落ちる (P は 1,111〜620,462 と
  走ごとに大きく変わる = ほぼ全 abort + backoff の挙動で、受入必須の述語 (I・P>0・X 0・cycle 0・txn>0) は満たす)。

---

## mocc-temperature-predicate-variant.patch / instr-mocc-lock-coverage-temperature.patch — mocc 温度述語 template (proof 用骨格) と計装の template 版 ([T-2773]、D2134 項 1・6・8)

**proof 用 template (CC-native 骨格) 1 本と、その上で使う計装 patch 1 本。** どちらも [T-2773] (mocc の auditor-live 相当の機械実証 wave 2) の
成果物であり、mocc の変異探索・pin 前進・正式な軸採用のいずれも認可しない (D2134 項 9、ユーザー決定 2026-09-19 = 軸オンボーディング段階 A 承認と
wave 2 の実証認可のみ)。preimage は submodule `e9e477ca` (template)、`e9e477ca` + template (計装 template 版)。

- **`mocc-temperature-predicate-variant.patch`** (touch set = `cmake/Options.cmake` + `cc/mocc/transaction.cc`): `cc/mocc/transaction.cc` の温度述語 4 site
  (`read_internal` 296 / `update` 459 / `delete_record` 566 / `construct_RLL` 970、行番号は e9e477ca) の `loadepot.temp >= FLAGS_temp_threshold` を file-scope helper
  `mocc_is_hot(std::uint64_t temp, std::uint64_t threshold)` (anonymous namespace、`inline`) の呼出へ置換し、helper 本体内に**唯一の** EVOLVE-BLOCK
  (marker id `mocc-temperature-predicate`、hole = `return temp >= threshold;` の 1 行、`#else` 側は stock 等価述語の逐語 = frame) を置く。970 の
  `|| (*itr).failed_verification_` は両枝で保存。flag は `cmake/Options.cmake` の universal 相乗り `CCBENCH_MOCC_TEMP_PREDICATE` → `MOCC_TEMP_PREDICATE`
  (既定 0)。**OFF (0) では helper の宣言も 4 site の分岐も消え、原文が逐語で選ばれる** (`#ifndef MOCC_TEMP_PREDICATE #error` で供給漏れは build 失敗)。
  外側 guard 行 `#if MOCC_TEMP_PREDICATE // file-scope helper` は source 内で完全一致 1 行 = condition gate の一意 witness。読取契約 (値渡しの `temp` /
  `threshold` と bool / 整数定数の比較・論理結合だけ。`FLAGS_*`・`thid_`・`result_`・CLL/RLL/read/write set・乱数・時刻・TRACE・呼出・副作用を禁止) は
  `orchestrator/campaign/axis_mocc_temperature.py` (`SYNTAX_CONTRACT_*`、禁止例の列挙であって完全な blacklist ではない) と `.claude/agents/auditor.md` 型 16 の
  mocc 追記が正本。**DQ (`diff_quarantine.py`) pass は物理行の封じ込めだけを示し、一式性・純粋性・停止性・読取契約の充足を示さない。**
- **`instr-mocc-lock-coverage-temperature.patch`** (touch set = `cc/mocc/transaction.cc` のみ): `instr-mocc-lock-coverage.patch` ([T-2294]、不変) の 6 hunk の
  検査本文・`#if TRACE` guard・検査対象操作との前後関係を byte 不変で保ち、`#line` 7 箇所だけを template 適用後の論理行 (17/990/991/1158/1169/1187/1195 →
  36/1025/1026/1193/1204/1222/1230、offset = helper 19 行 + 4 site の増分 4 行 × 4) へ再生成したもの。旧計装 patch は template 適用後の source に `git apply`
  できず (hunk 1 の context 不一致)、本 patch は template なしの e9e477ca に当たらない。本文保存は driver の `instrumentation_body_preserved` check
  (追加行列の一致・hunk 前後 context の一致・`#line` 列 = 旧 + 実測 offset) で機械化する。
- **同一性の 3 比較と保証名** (設計 §8、D1687): (i) 無 template ↔ template OFF = **実 resolver (`source_digest`) が定める正規化前処理 source identity の
  stock 一致** (`src_token="stock"`)。**実 TU・binary の完全同一は主張しない** — 無 template と OFF の TRACE=0 `.text` は論理行 1193 の `ERR;` の `__LINE__` 即値
  (1193 → 1228、template は `#line` を持たない) で 2 行相違する (login 実測 2026-09-19)。(ii) OFF ↔ ON-B (hole = `!(temp < threshold)`) は別 identity。
  (iii) 同一 template 状態の計装なし ↔ あり = TRACE=0 の (論理行, 非空本文) 列一致 (OFF 543 行 / ON-B 548 行)。(iii) は TRACE=1 検査本文の有効性を保証しない
  (それは本文保存 check が担う)。旧 pin ↔ pin 候補の D297 比較は別 T。
- **駆動の正本 = `orchestrator/campaign/s3_mocc_template_proof.py`** (compute 専用。wave 1 driver `s3_mocc_mutation_proof.py` と T-2294 driver の helper を import で
  再利用し、旧 driver・旧 JSON・旧 check は不変)。build 5 本 (ON-B TRACE=1 計装あり / ON-B TRACE=0 計装なし・あり / OFF TRACE=0 / 無 template TRACE=0) +
  template ON-B の stock 12 走 (W / U × hot 0 / cold 21 / default 10 × 1 / 4 thread、すべて certified & silent を要求) + 上記 3 比較 + DQ 13 対照 (benign 受理 /
  stock 枝改変 = frame-altered / 970 fallback・CLL・RLL・validation・X・P・write_set_ 登録 477・RLL の write-set 登録 905〜913 の侵食 = outside-region /
  生指令・comment splice = hole-escape / HEAD 不整合 anchor = malformed) + deny-only 4 対照 (`auditor_gate.apply_mandatory_deny_only_veto`) + consumer 束縛
  3 対照 (`axis_mocc_temperature.require_proof_binding`: 別名 template 拒否・別 OID 拒否・正しい値の literal は通過) + auditor 定義 (tools = Read/Grep/Glob、
  型 8/9/13/16・チェックリスト 11/12/13 の mocc 項目、正しさの形だけを写す `auditor_projection`) + 旧 proof (wave 1 JSON 32 check、T-2294 JSON 14 check) の
  sha 鎖と all_pass → JSON `output/env/pegasus/calibration/s3_mocc_template_proof.json` (schema `s3-mocc-template-proof/v1`、30 check)。
  **この 12 走は template ON-B の正常系対照であり、template 上で hot 負例が発火したことは主張しない** (hot 経路の実行証拠は wave 1 の固定 producer に束縛された
  経路共通証拠、`hot_path_evidence` は wave 1 JSON への参照)。4 site 全動的被覆・read 側 hot・RLL 再試行・DELETE も主張しない。
- **gate (`orchestrator/tests/test_mocc_template_proof.py::test_mocc_mutation_surface_requires_auditor_live`)**: 鍵 = (a) `patches/*.patch` のうち
  `cc/mocc/transaction.cc` の hunk に `EVOLVE-BLOCK-BEGIN` を加える patch の存在、または (b) `orchestrator/campaign/axis_*.py` のうち `SOURCE_REL` が mocc で
  `MARKER_ID` / `TEMPLATE_PATCH` を持つ module の存在。EBS 所属は鍵にしない (D2134 項 6)。発火時は上記 JSON の実在・all_pass・sha 鎖・束縛・auditor 定義を要求する。
  任意の直書き経路・全 consumer 経路を閉じたとは主張しない。実 loop driver (consumer) は未導入で、導入時にその実 checkout との束縛検査が別途要る。
- **実証** (2026-09-19、Pegasus gen_S request 11161.nqsv、Elapse 352 秒、driver HEAD 2d76e785f、**30 check all_pass**): OFF digest = stock digest
  (`6454d9f3…`)、ON-B `41f52341…`、論理行列 OFF 543 / ON-B 548 一致、ON-B の binary は nm izanagi 0 / strings 0 / `.text` 差分 0 行、12 走すべて serializable・
  certified・cycle 0・X = P = 0 (U は R 行 0、4 thread ≈ 350〜368 万 txn)、verifier wall 最大 52.9 秒、condition gate 3 本 green。
- **n=1 定性 (D38 決定 4 の点 5 / 6、機械 `all_pass` には入れない)**: 候補 3 本 (A1' = validation の writer lock 削除 (marker 外)、A2' = hole を
  `FLAGS_clocks_per_us` 依存に、B' = hole を `!(temp < threshold)`) を fresh な read-only auditor に独立監査させた素材と実応答は
  `output/insights/2026-09-19/t2773-mocc-template-wave2/auditor-n1.md`。

## silo-function-policy — 関数群・複数 hook・状態の軸の骨格 + probe + positive control (Phase 3 段階 C、D2214、[T-2857])

LLM が Silo の待機と lock 競合応答を関数単位で書く軸 (手順書 `docs/axis-onboarding.md` §4 第 3 列)。設計の正本 =
`output/insights/2026-09-21/silo-function-synthesis-space/README.md` + D2214、段階 C の記録 =
`output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md`。軸定数は `orchestrator/campaign/axis_silo_function_policy.py`、
api header の単一正本は `orchestrator/campaign/silo_function_policy_api.hh`、手書き方策は `orchestrator/campaign/silo_function_policy_hand/`。

- **silo-function-policy-variant.patch** — 骨格 (template patch)。`cmake/Options.cmake` の universal 相乗り
  (`CCBENCH_SILO_POLICY_VARIANT`、既定 0) と `cc/silo/transaction.cc`。**既定 0 で inert** (領域・骨格・呼出し点・要因記録が
  すべて `#if SILO_POLICY_VARIANT` の内側で、preprocess 後に原文一致 → src_token="stock")。0 / 1 以外の値と、軸 ON で
  `BACK_OFF != 1`・no-wait flag が 1 / 0 でない・前提 macro の未定義は `#error`。軸 ON では api block の埋込み、単一 marker
  (id=`silo-function-policy`) の hole (`izanagi_silo_policy` の本体、既定本文 = `abort0`)、骨格所有の thread_local 状態・要因・
  PRNG・上限つき待機器・noipa wrapper、abort 後 1000 µs / lock 50 µs / tuple ごと 32 周の上限、待機後の再読込、上限・abort・
  未知 action での prefix unlock 出口、要因記録 7 点、成功 commit 後の成功通知。要因記録は待機を決める CC 本来の状態で、
  `#if TRACE` に入れない (規律 1)。PIN 前進はしない。
- **instr-silo-function-policy-probe.patch** — 検証専用計装 (焦点試験と機構変異の走だけ骨格の上に重ねる)。macro
  `IZANAGI_SILO_POLICY_PROBE` (`CCBENCH_` 外、`-D` だけで供給)。worker 別の独立計数、焦点方策 `focus` の戻り値の符号化
  (3 hook の実呼出し回数を他 hook の戻り値の下位 bit に載せる) との照合、7 記録点の site id と要因の照合、成功 commit 後の比較、
  prefix を保持したままの上限出口・action-abort 出口の到達を数え、thread 終了時に 1 行出す。template patch に入れない
  (入れると diff-of-diffs が崩れる)。既知の限界: `broken-silo-policy-wrong-reason.patch` の走では、変異の複製ループが
  prefix 保持下の到達計数に追随しておらずこの 2 計数が 0 のまま出る (この変異の判定は同計数を使わない)。
- **broken-silo-policy-norw-validation.patch / broken-silo-policy-lockskip-validation.patch** — 既存の norw / lockskip 負例の
  軸 ON 版 (骨格の上に当てる、既存 macro `IZANAGI_BREAK_NOREAD_VALIDATION` / `IZANAGI_BREAK_LOCK_COVERAGE` を再利用)。
  既存 patch は骨格が文脈を変えるので当たらない。early-unlock は既存 `broken-silo-early-unlock-validation.patch` を骨格の上に
  厳密適用して使う。
- **broken-silo-policy-{no-clamp,no-reload,no-limit,no-prefix-unlock,no-prefix-unlock-limit,no-abort-hook,no-lock-hook,no-commit-hook,wrong-reason}.patch**
  — 骨格の仕組みを 1 つずつ壊す機構変異 (骨格 → probe の上に 1 枚だけ当てる、相互排他)。共通の裸 macro
  `IZANAGI_BREAK_SILO_POLICY` を各 1 site の `#if` で使う。prefix unlock は出口ごとに 1 枚 (`no-prefix-unlock` =
  action-abort 出口、`no-prefix-unlock-limit` = 上限出口) で、各 patch はもう一方の出口の unlock を残す。no-limit は
  非検出対照 (検出力の主張に使わない)。**既定 OFF inert・裸 macro は CCBENCH_ 外 = pipeline から定義不能**
  (broken-silo と同じ隔離規約、規律 2)。

**駆動の正本 = `orchestrator/campaign/silo_policy_coverage.py`** (sub-command `coverage` = 負例・焦点試験・機構変異・flag 境界・
TRACE=0 の不混入、`smoke` = stock と手書き方策 4 本の生死確認)。gate を掛けない依存物準備の build を最初に 1 回行い、
condition gate は 1 回に macro 1 個。診断 build は NON_ADMISSIBLE で、certified 候補とは称さない。
実証 (2026-09-22、Pegasus 計算ノード、`output/env/pegasus/calibration/silo_function_policy_coverage.json` /
`silo_function_policy_smoke.json`): coverage は 33 case・61 check すべて真 (norw non-serializable・exit 1、lockskip X 2 種、
early-unlock 保持欠落のみ、hook 解除 3 件と要因誤記録は宣言した赤集合と完全一致、再読込削除で retry 後の取得成功 0、
clamp 削除と prefix unlock 2 出口は trace-timeout、上限削除は certified、flag 境界 4 種は `#error`、TRACE=0 は不混入)。
smoke は 5 case・30 check すべて真 (stock と 4 方策が legacy / 性能構成 verify とも serializable、honest identity)。

---

## broken-silo-{read-lock-check,…} 11 本 / control-silo-{double-abort-backoff,reverse-write-order,conservative-abort} 3 本 — 検出期待表の新規 silo 変異 ([T-2847])

verifier が何を検出し何を判定しないかを実測で示すための変異 14 本。設計 (期待の層と発生条件) は
`output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §4、V 番号はその表のもの。
**broken-silo** 11 本は正しさ (または宣言範囲外の規則) を変える変異、**control-silo** 3 本は正しさを保つ
対照 (誤検出を測る側)。いずれも pin `e9e477ca` の `cc/silo/transaction.cc` に**単独で**当てる
(同時適用しない。特に V18 と V35 は同じ代入を逆方向に変える)。

| V | patch | 裸マクロ | 変更 |
|---|---|---|---|
| V17 | broken-silo-read-lock-check | `IZANAGI_BREAK_READ_LOCK_CHECK` | 他者が lock 中の読み key での abort を外す (版一致検査は残す) |
| V18 | broken-silo-no-write-tid-max | `IZANAGI_BREAK_NO_WRITE_TID_MAX` | commit TID の元から書く key の現版を外す |
| V19 | broken-silo-fixed-commit-version | `IZANAGI_BREAK_FIXED_COMMIT_VERSION` | commit 版を非 genesis の固定値 (1,1) にする |
| V20 | broken-silo-published-version-mismatch | `IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH` | UPDATE で tuple に公開する版だけを C/W 行と違う値にする |
| V21 | broken-silo-tail-commit-omission | `IZANAGI_BREAK_TAIL_COMMIT_OMISSION` | 終了 flag が立った後の取引で writePhase を呼ばず成功を返す |
| V22 | broken-silo-stale-read-payload | `IZANAGI_BREAK_STALE_READ_PAYLOAD` | read の再確認で 2 度目の TID を採り payload を取り直さない |
| V23 | broken-silo-corrupt-write-payload | `IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD` | 公開する payload の先頭 byte を反転 (版・lock は正常) |
| V24 | broken-silo-skip-node-validation | `IZANAGI_BREAK_SKIP_NODE_VALIDATION` | node map の検証 (phantom 防止) を外す |
| V26 | broken-silo-stale-read-own-write | `IZANAGI_BREAK_STALE_READ_OWN_WRITE` | 自分の書いた key の read で旧 tuple の payload を返す |
| V27 | broken-silo-repeat-update-buffer | `IZANAGI_BREAK_REPEAT_UPDATE_BUFFER` | 同じ key への 2 度目の update で write buffer を誤って書く |
| V35 | broken-silo-no-read-tid-max | `IZANAGI_BREAK_NO_READ_TID_MAX` | commit TID の元から読んだ版を外す (Silo の TID 規則を破る) |
| V31 | control-silo-double-abort-backoff | `IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF` | abort 後の backoff を 2 回呼ぶ |
| V32 | control-silo-reverse-write-order | `IZANAGI_BREAK_REVERSE_WRITE_ORDER` | write set を全 worker 共通の逆順で並べる |
| V33 | control-silo-conservative-abort | `IZANAGI_BREAK_CONSERVATIVE_ABORT` | 要素数が偶数の非空 write set の取引を lock 前に abort する |

- **既定 OFF inert:** 各 patch は `CCBENCH_` 外の裸マクロ 1 個の `#if` 枝に閉じ、未定義で pin と一致する。
  pipeline の genome からは定義できない (broken-silo と同じ隔離規約、絶対規律 2)。
  条件 gate (`orchestrator/campaign/condition_meaning_gate.py`) の許可ドメインへの登録は、既存の壊し patch と同じく
  driver の `-DCMAKE_CXX_FLAGS=-D<macro>=1` 経路で build するためのもので、判定基準は変えない。
- **発火診断:** マクロ有効時だけ、変異が枝に入った回数 (reached)・元コードと違う挙動を実際に生んだ回数 (changed)・
  changed を含む取引が commit した回数 (committed) を relaxed atomic で数え、process 終了時に stderr へ
  `T2847_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>` の 1 行を出す (V18・V21・V35 は追加の数も出す)。
  「盲点として certified」と「未発生」を分けるための記録であり、verifier の判定には使わない。
- **駆動:** 既存の `orchestrator/campaign/s2_verify_calibration._broken_build_and_verify` (patch 適用・condition gate・
  commit 証人つき verifier) を repo 外の起動器から呼ぶ。実走の記録は `output/insights/2026-09-23/t2847-mutation-run/`。

## broken-mocc-skip-canonical-restore.patch / control-mocc-negated-temperature-predicate.patch — 検出期待表の新規 mocc 変異 ([T-2847])

設計書 (`output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §4) の mocc 2 行。
pin C (`68106660`、mocc の X/P 計装を含む) の `cc/mocc/transaction.cc` に**単独で**当てる
(`instr-mocc-lock-coverage.patch` は重ねない。C には同じ計装が入っていて当たらない)。

| V | patch | 裸マクロ | site | 変更 |
|---|---|---|---|---|
| V25 | broken-mocc-skip-canonical-restore | `IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE` | 5 | 逆順に取った lock の正準順への復元 (解放と CLL_ 除去) を飛ばし、逆順の lock を持ったまま追加で取る。upgrade でなく、対象 tuple と再取得先が保持中の lock と重ならないときだけ (同じ lock の二重取得・二重解放を避ける) |
| V34 | control-mocc-negated-temperature-predicate | `IZANAGI_BREAK_MOCC_NEGATED_TEMPERATURE_PREDICATE` | 9 | 温度述語 4 site を `!(temp < threshold)` へ等価変形する対照 |

- **既定 OFF inert:** 裸マクロ 1 個の `#if` 枝に閉じ、未定義の枝を除いた全文が pin C とバイト一致する (patch 適用後の file 自体は `#if` 行の分だけ異なる)。pipeline の genome からは定義できない
  (broken-silo と同じ隔離規約)。条件 gate への登録は driver の `-DCMAKE_CXX_FLAGS=-D<macro>=1` 経路で build するためで、判定基準は変えない。
- **発火診断:** 有効時だけ `T2847_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>` と追加の数
  (V25 は `skipped_locks`、V34 は site 別の評価回数と `temp == threshold` の評価回数) を process 終了時に stderr へ 1 行出す。
  V34 の changed は定義上 0。run timeout で止めた process では出ないことがある。verifier の判定には使わない。
- **駆動:** 既存 mocc driver (`orchestrator/campaign/s3_mocc_mutation_proof.py`) の build・verify 関数を repo 外の起動器から呼ぶ
  (既存 4 本も同じ起動器で pin C 上に単独で当てた)。実走の記録は `output/insights/2026-09-26/t2847-mocc-run/`。

## instr-si-trace-v2.patch / broken-si-first-updater-wins.patch / broken-si-read-uncommitted-version.patch — si の trace v2 化と検出期待表の si 変異 ([T-2847])

pin C (`68106660`) の si の emitter は v1 (C 行 5 field、E 行なし) のままで、現行 parser に拒否される
(下の「トレース形式」)。`include/trace.hh` は共有 header で、本来の置き場 (D16 の `izanagi-trace` 枝) への移送と
pin 前進は人間の判断なので、ここでは out-of-tree patch として置く (D16 の T-109 例外と同じく `#if TRACE` の内側だけ)。

| patch | 裸マクロ | site | 変更 |
|---|---|---|---|
| instr-si-trace-v2 | なし (無条件の計装) | — | `cc/si/transaction.cc` の `#if TRACE` 内で C 行を v2 の 7 field (`C txid thid 1 cstamp read_count write_count`) にし、R/W の後に `E txid` を出す。件数は R/W と同じコンテナの `size()` で独立 witness ではない。`thid_` は `uint8_t` なので `std::size_t` へ変換して書く。`#if TRACE` の外は pin C とバイト一致 |
| broken-si-first-updater-wins (V29) | `IZANAGI_BREAK_SI_FIRST_UPDATER_WINS` | 7 | `install_version()` の committed 後の first-updater-wins の abort だけを外す (inflight 分岐と CAS 再試行は残す) |
| broken-si-read-uncommitted-version (V28) | `IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION` | 5 | `read_internal()` の版選択の status 除外だけを外し、snapshot 条件は残す。未完成の body や回収後に再利用された版を読みうる (異常終了も結果として記録する) |

- **重ね方:** 壊し 2 本は pin C → `instr-si-trace-v2.patch` → 壊し patch の順に当てる (touch set はどれも `cc/si/transaction.cc` だけ)。
  壊し patch は裸マクロ 1 個の `#if` 枝に閉じ、未定義の枝を除いた全文が v2 適用後の file とバイト一致する。
  条件 gate への登録は `-DCMAKE_CXX_FLAGS=-D<macro>=1` 経路で build するためで、判定基準は変えない。
- **発火診断:** 有効時だけ `T2847_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>` を process 終了時に stderr へ 1 行出す。
  verifier の判定には使わない。
- **si の判定の上限:** si には X/P の証拠面が無いので、巡回があれば non-serializable、無ければ indeterminate で、certified にはならない
  (使い道は巡回の検出)。update / delete が同じ key の read set 要素を消すので、同じ取引で読んで書いた key の R 行は trace に残らない。
- **駆動:** repo 外の起動器 (driver の policy・toolchain・patch 適用・単独性検査を import し、build の target を `ycsb_si.exe`、
  verify を `--protocol si` にした局所版)。実走の記録は `output/insights/2026-09-26/t2847-si-run/`。

---

## instr-cicada-version-lifetime.patch — Cicada の版探索と版保持の診断計器 (VHash md_2、2026-09-29)

**診断計器** (D20 第 5 類)。stock Cicada (preimage = gitlink `68106660686232781bca3be792a750d3e19d7a8a`、Cicada 関連 file は
`511c9538` と同一) の `cc/cicada/include/transaction.hh` と `cc/cicada/transaction.cc` だけを触る。`util.cc`・`ycsb_cicada.cc`・
共有 header `include/ycsb.hh`・`common/runner.hh` は触らない (condition gate の meaning 検査は owner TU `transaction.cc` の前処理だけを見るので、
分岐は owner TU とそれが include する header に置く)。`ledger.json` には登録しない (同台帳は D18 第 4 類 ability probe 専用で entry 数 1 固定)。

- **`IZANAGI_CICADA_VLIFE`** — stock の既存走査が訪れた版だけから数える (追加の鎖走査なし)。site
  (read_update / read_ronly / blind_write / rmw_latest / precheck / install / readcheck / writecheck) 別の hop 数と位置
  (read は latest 起点、validation は走査の開始点起点、raw の `position_origin`)、K∈{1,2,3,4,8} の深い read 数と
  「観測時点の楽観的 forwarding 候補」数、既読 0 件の深い read、MinRts 公開ごとの境界年齢 (timestamp 空間、負値は別計数。公開は
  `leaderWork()` の前後で `GCFlag[0]` が 1→0 になったことで判定し、同値の再公開も数える)・公開間隔 (rdtscp)・回収時年齢
  (生成基準・上書き基準)・install/切離し数、長短別の tx 統計を thread 別の固定長配列 (総 worker ≤ 256) に数え、プロセス終了時に
  `IZANAGI_CICADA_VLIFE_JSON ` + 1 行 JSON を出す。**計器入り build の throughput は性能値に使わない** (規律 1)。`SINGLE_EXEC=1` は対象外。
- **`IZANAGI_CICADA_LONGTX`** — 長い tx の 2 型。(a) 待機型: worker 1 が `commit()` 冒頭 (read phase 末) で
  `-worker1_insert_delay_rphase_us` だけ rdtscp spin で待つ (CCBench 論文 §7.2 の作り方)。(b) 操作数型: batch worker
  (thid ≥ `-thread_num`、`-batch_th_num` 本) の手続きを `begin()` で `-batch_max_ope` 個まで同じ分布・読み比で伸ばす (retry では伸ばし直さない)。
  stock の `WORKER1_INSERT_DELAY_RPHASE=1` 分岐 (未定義識別子 3 件で compile error、実測) と表示だけの `batch_*` flag は触らない。
- **既定 inert の witness:** (i) `orchestrator/tests/test_vhash_cicada_vlife.py::test_patch_default_preprocess_matches_stock`
  (touched TU の前処理を行番号・行マーカーのファイル名・include 行まで stock と比較。patch の `#line` はファイル名なしの `#line N`)、
  (ii) 駆動 smoke の stock と既定 patch の正規化 `objdump -d` と `.rodata` の一致、`nm -C` の izanagi 0 件、`strings -a` の izanagi 文字列集合の一致。
  2026-09-29 の Pegasus 計算ノード smoke (33984.nqsv) で全部成立。一次資料 `output/insights/2026-09-29/vhash-cicada-version-measure/README.md`。
- **駆動の正本 = `orchestrator/campaign/vhash_cicada_vlife.py`** (sub-command `smoke` / `measure`、materializer は NON_ADMISSIBLE、
  2 macro は condition gate の supply・meaning を通す)。measure は smoke JSON の witness と較正 (N の選定) を再計算して束縛する。
  作図 `tools/plotting/plot_vhash_cicada_vlife.py` (複数 raw を併合、図 3 枚)。
- **md_15 の拡張 (計器行 schema 2、2026-09-29、VHash md_15)** — 新しい macro は足さず既存 2 macro の下だけで、
  (a) 実行時 flag `-izanagi_ronly_pct` (既定 −1 = YCSB の生成のまま。0〜100 なら新しい手続きの初回 `begin()` だけで確率 r% で全 op を READ に、
  それ以外は少なくとも 1 op を write にする。retry では変えない) と `-izanagi_long_kind` (0 = 生成のまま、1 = 長い tx の worker を update、2 = ro に固定) を足し、
  (b) ro read の観測鎖・先頭 K 版・既読区間に限定した楽観的適格数 (`readonly_candidate`) と同じ母集団の `readonly_reads`、
  (c) 公開間隔の flag 機会の時刻分割 (各 worker の実際の GC flag 上げ時刻と「ro commit も同じ timer 条件で上げたら」の時刻を、事象の時点の公開世代の slot に記録。
  leader は全 flag を見たら公開の前に世代を進め、遅れて揃った公開は検出時に進めて `dc_late_epoch` に数える。ro commit の経路は flag と `gcstart_` を読むだけで書かない)、
  (d) 境界年齢・公開間隔・ro snapshot 年齢の厳密和、境界保持 tx の種別、同値再公開の件数を出す。driver は旧 24 条件と schema 1 の読取りを残し、
  主格子 60・skew 0 対照 12・調整済み genome の 12 条件を足した (調整済み genome は `cmake_cache_variable_for_axis` の CMake 変数で build し、
  compile_commands の -D を照合する)。measure のレコード数は 1M 固定 (smoke の較正は参考記録)。作図 `tools/plotting/plot_vhash_readonly_share.py` (図 4 枚)。
  既定 inert は拡張後の patch でも smoke (35800.nqsv、patch sha256 `fafdd862…`) で成立。condition gate の VLIFE 分岐 witness は owner TU 37 / header 9。
  一次資料 `output/insights/2026-09-29/vhash-readonly-share/README.md`。

---

## instr-cicada-trace.patch / broken-cicada-{skip-read-recheck,no-rts-update,stale-read-ro}.patch — Cicada の trace と正例 (VHash 論文の前提 G0、2026-09-29)

pin C (`68106660`) の `cc/cicada/` には `#if TRACE` の計装が無い。D16 の本来の置き場 (`izanagi-trace` 枝) への移送と pin 前進は
人間の判断なので、gitlink を動かさずに**試作・実走用の out-of-tree patch** として置く (si の [T-2847] と同じ根拠。D16 の T-109 例外は流用しない、D579)。
`patches/ledger.json` には登録しない (entries 1 件固定)。

| patch | 裸マクロ | 変更 |
|---|---|---|
| instr-cicada-trace | なし (無条件の計装) | `cc/cicada/` の `#if TRACE` 内だけ。書く txn は `cpv()` 後・set clear 前、read-only txn は `commit()` の早期 return 前に trace v2 (C / R / W / E) を出す。版 = wts の上下 32 bit (`hi = wts>>32`、`lo = wts & 0xffffffff`)、初期版 (`initial_wts`) は genesis `(1,0)`。R の版は `ReadElement` に読んだ時点で保存した wts (commit 時の値との食い違い件数を `CICADA_TRACE_READ_WTS_MISMATCH n=` で出す)。`ycsb_cicada.cc` の main で `initial_wts` を渡し、TRACE build は `CICADA_TRACE_INITIAL_WTS=` を出す (未設定で emit に達したら異常終了)。`INLINE_VERSION_OPT` かつ `INLINE_VERSION_PROMOTION` の組合せは TRACE=1 で `#error` (D1464 の区別は未実装)。`#else` 側の `#line` で TRACE=0 の行番号を保つ |
| broken-cicada-skip-read-recheck | なし | validation の read set 再検査で、読んだ版が今の可視版と違っても abort しない |
| broken-cicada-no-rts-update | なし | `readTimestampUpdateInValidation()` の呼出しを外す |
| broken-cicada-stale-read-ro | なし | read-only txn の可視版選択で、txn 内の偶数番目の読みに限り可視版の 1 つ古い committed 版を選ぶ |

- **重ね方:** 壊し 3 本は pin C → `instr-cicada-trace.patch` → 壊し patch の順に厳密適用する (touch set は壊しが `cc/cicada/transaction.cc` だけ、
  instr が `cc/cicada/` の 4 file)。壊しは裸マクロを持たない無条件 patch なので、既定で重ならず、正例の build にだけ当てる。
  新しい `#if` 条件に書く語は `TRACE` だけで、`IZANAGI_` の語を含まない (条件 gate の定義一覧・裸マクロ登録の照合を変えない)。
- **発火診断 (壊しだけ):** 事象を commit した txn の分だけ stderr の `CICADA_BREAK_EVENT slug= tx_wts= key= a_wts= b_wts=` に全件出し、
  終了時に `CICADA_BREAK_FIRED slug= reached= changed= committed=` を出す。verifier の判定には使わず、repo 外起動器の帰属解析だけに使う。
- **Cicada の判定の上限:** X / P / I の証拠面が無いので、巡回があれば non-serializable、無ければ indeterminate で、certified にはならない。
- **実証:** stock (instr のみ) は YCSB の K・W・R cell の 7 走行で巡回 0・integrity 数値項目 0・C 行 = commit 数。壊し 3 本は全部
  non-serializable で、判定器の代表 witness 20 件中 20 件が壊した経路に帰属した。TRACE=0 は YCSB target の 3 TU で命令列が pin と一致
  (tpcc / bomb / sbomb の TU は未比較)。未対応 = scan の phantom・insert / delete・版昇格・`group_commit>0`・YCSB 以外。
  駆動は repo 外の起動器 (si の起動器を雛形に target `ycsb_cicada.exe`・`--protocol cicada`)。記録は `output/insights/2026-09-29/vhash-cicada-verifier/`。
- **pin 前進時:** 4 本とも pin C に対して作った。pin を進めたら厳密適用と生死確認を取り直す。

## instr-cicada-trace-tpcc.patch / broken-cicada-insert-past-ts.patch — Cicada の TPC-C trace (v3) と insert の正例 (VHash 論文の前提 G0 の続き、2026-09-29)

TPC-C は表だけが違う同じ key bytes を持つので、判定器が既に受理する trace v3 (表番号付き、D2224 / D2225) で出す。v3 の部品
(`include/trace.hh` の v3 出力関数と取引種別の thread-local 文脈、`include/tpcc.hh` の文脈設定と trace build の全 commit 計数) は pin C に無く、
CCBench の C1' `6aa7a58f` (pin C の子、header 2 file だけ) にある。md_14 が使う `instr-cicada-trace.patch` の bytes と YCSB の v2 出力を
変えないため、TPC-C 用は別の重ね patch にした。`patches/ledger.json` には登録しない (entries 1 件固定)。

| patch | 裸マクロ | 変更 |
|---|---|---|
| instr-cicada-trace-tpcc | なし (無条件の計装) | `cc/cicada/` の `#if TRACE` 内だけ。`traceCommit()` が `izanagi_trace::tpcc_tx_type()` を 1 回読み、非 0 なら v3 (C = `txid thid hi lo nR nW 0 0 tx_type`、R / W の表 = 要素の `storage_`)、0 なら既存 v2 の式をそのまま通す。E の直後に文脈を 0 へ戻す。`tpcc_cicada.cc` の main で `initial_wts` を渡し `CICADA_TRACE_INITIAL_WTS=` と終了時報告を出す (ycsb と同形)。`#else` 側の `#line` で TRACE=0 の行番号を保つ |
| broken-cicada-insert-past-ts | なし | `insert()` で作る新版の wts を自分の wts ではなく begin 時の `rts_` にする (insert した行が、自分より前に直列化された読み手にも見える) |

- **重ね方:** C1' `6aa7a58f` (以降) → `instr-cicada-trace.patch` → `instr-cicada-trace-tpcc.patch` (→ 壊し patch) の順に厳密適用する。
  pin C 単独に重ね patch を当てた TRACE=1 build は作れない (C1' の部品が要る)。既存の壊し 3 本もこの上に重ねられる (touch set が素)。
  新しい `#if` 条件に書く語は `TRACE` だけで、`IZANAGI_` の語を含まない。
- **発火診断 (壊しだけ):** 既存 3 本と同形で、事象行に `table=` を足した `CICADA_BREAK_EVENT slug=insert-past-ts tx_wts= table= key= a_wts= b_wts=` と
  終了時の `CICADA_BREAK_FIRED`。判定には使わず、repo 外起動器の帰属解析だけに使う。
- **実証:** stock の TPC-C 5 走行 (insert だけの mix の t1・t4、StockLevel を増やした mix の t4、Delivery を含む全 mix の t1) で巡回 0・integrity 数値項目 0・
  存在履歴違反 0・C 行 = commit 数。insert-past-ts は non-serializable で、orphan read 1,144,962 件の全部と巡回 1 件の辺が壊した insert に帰属した。
  既存の skip-read-recheck を TPC-C に重ねた版は巡回 2,135 件、代表 witness 20 件中 20 件が帰属した。TRACE=0 は tpcc / bomb / sbomb の各 3 TU
  (既存計装のみ) と tpcc の 3 TU (C1' + 既存計装 + 重ね patch) で命令列が pin C と一致。
- **未対応:** Delivery を含む全 mix (F cell) の 4 thread は、stock Cicada 自体が `gc_records()` の `ERR` で落ちる (trace の有無に依らない、11 回中 11 回。機序は未特定)。
  範囲読みの phantom・不在の読み・BOMB / SBOMB の trace・campaign 接続・certified は対象外。記録は `output/insights/2026-09-29/vhash-cicada-verifier-ext/`。
- **pin 前進時:** C2' 系へ pin が進んだら、重ね順の厳密適用と生死確認を取り直す。

---

## トレース形式 (verifier = タスク2 の入力契約)

trace-hook の**実装**は submodule `izanagi-trace` ブランチにある (Silo は `writePhase` の `maxtid`
確定後、si は `si_commit` の write install 直後に emit)。出力する**形式**は verifier
(`orchestrator/verifier/`) の入力契約なのでここに記録する。

per-thread ファイル `trace_<thid>.log`、1イベント1行。1 trx の records は連続し、
**`C` で開き `E` で閉じる**:

```
C <txid> <thid> <epoch> <tid> <read_count> <write_count>
                                          committed txn。<epoch>,<tid> = commit順 = この trx が産んだ版ID。
                                          末尾 2 個は、この trx が続けて emit する R 行数と W 行数の宣言。
R <txid> <key_hex> <ver_epoch> <ver_tid>  read。見た版 (ver_epoch,ver_tid)
W <txid> <key_hex> <op> <epoch> <tid>     write。op∈{U,I,D}。新版 = この trx の commit (epoch,tid)
E <txid>                                  txn 終端。C の宣言件数と実件数が一致することの照合点
```

**これが trace v2 であり、現行 verifier が受理する唯一の形式である** ([T-816]、2026-08-12)。
`C` が 5 token の旧形式 (v1、`E` 行なし) は拒否する — 途中で切れた trace を
「欠落なし」と誤って certified にする偽陰性 (FN-2) を閉じるため。
v1 期に凍結された証拠 (`output/env/pegasus/silo_ladder_rung1/` の raw bundle) は
bytes を保存したまま再検証を退役した。

このほかに `#if TRACE` の検査 assert が emit する行がある: `X` (lock 被覆違反、D38)・
`P` (permutation 保存違反、D41)・`A` (abort 要因、D48)・`I` (write-intent 被覆違反、[T-152] —
実装は izanagi-trace ブランチ側、pin 前進まで pinned producer は emit しない)。書式と意味論の
正本は `orchestrator/verifier/parse.py` の module docstring と各 patch 節。
X の reason token は `not-locked-at-entry` / `lock-lost-before-write` (Silo、D38) に加え、mocc では
`lock-lost-before-publish` ([T-2294]、payload と publish が別のため) を使う。verifier は reason を自由 token として数える。
P の reason は `size-changed` / `rcdptr-set-changed` の 2 語だけを認識し、それ以外は `unknown` として同じく indeterminate に倒す。

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
