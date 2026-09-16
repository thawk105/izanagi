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
| mocc 計装 (`instr-mocc-lock-coverage.patch`、mocc の `#if TRACE` lock 被覆・permutation 検査) | Izanagi の verifier 入力 (X/P 行)。D14 契約で perf build から完全除去し、`#line` で TRACE=0 の前処理出力と `.text` を preimage と同一化 | **out-of-tree patch** (preimage = submodule `e9e477ca`。pin 前進 [T-2295] で izanagi-trace 側へ移すかは人間判断) |
| broken-mocc (わざと壊した mocc 3 本) | mocc 計装の positive control = **テスト用の意図的バグ** | **out-of-tree patch** (このディレクトリ。永久) |
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
入り) で、現 pin 511c9538 には当たらない (`git apply --check` が拒否する。test で固定)。

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
