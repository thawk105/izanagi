# 段 1 brief — dev-wave dynamic-backoff-mechanism (2026-09-05)

## scope (純増だけ)

1. **実装面 (Codex `role=author`、親は直接編集しない)**
   - (a) 新 patch `patches/cicada-adaptive-dynamic.patch`。`patches/cicada-adaptive-params.patch` (以下 A、
     main の sha256 `9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b`、**bytes 不変**) を
     ccbench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` へ当てた木の**上に重ねる**。触る file は A と同じ
     `cmake/Options.cmake` と `include/backoff.hh` だけ。追加する CMake cache option と `#error` 契約は A と同形。
     define 名は本 brief で固定する (単位間の並列化のため):
     `BACKOFF_COUNT_WINDOW` (K 件、0=stock=時間のみ) / `BACKOFF_COUNT_CAP_US` (計数窓の時間上限 µs、
     0=`BACKOFF_UPDATE_US` を使う) / `BACKOFF_STEP_ADAPT` (0/1) / `BACKOFF_STEP_MIN_MILLI` /
     `BACKOFF_STEP_MAX_MILLI` (既定 100000 = stock 刻みと同値) / `BACKOFF_DYN_CEILING` (0/1) /
     `BACKOFF_TRACE` (0/1、D14 契約 `#if BACKOFF_TRACE`、`CCBENCH_TRACE` とは別 macro、perf build では symbol 0 個)。
     既定値はすべて stock 同値。
   - (b) `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` に動的腕の cell 書式を足す
     (5 field 書式はそのまま stock 同値で受理し、拡張 field で動的腕)。A+B の重ね適用、grid contract、genome、
     診断 build の別 run (`BACKOFF_TRACE=1`)、certify mode の exact cell 集合を `tuned` + 動的 1 腕へ。
     **新 path は作らない** (F660: 登録は path なので実測を同 wave で行える)。
   - (c) 登録簿の追随: `orchestrator/campaign/condition_meaning_gate.py` の `DefineSpec` (新 define → 新 patch、
     `inert_values` = stock 同値)、`orchestrator/campaign/screening_driver.py` の `_CONDITION_DEFAULTS`、
     `orchestrator/tests/test_condition_meaning_gate.py` の define 一覧、`orchestrator/tests/test_ccbench_spawn_sites.py`
     の deferred gate ledger (probe の build sink 行番号 1821 / 2124 は probe 編集でずれる)、
     `orchestrator/tests/test_t2187_adaptive_const_probe.py`。
   - (d) 図の生成器 `tools/plotting/plot_dynamic_backoff.py` + test (計測機の外で走らせる。`FIGURE_CONVENTIONS.md`)。
2. **docs (親)**: `docs/dynamic-backoff-preregistration.md` (段 4 で凍結、投入前)、`docs/README.md` 地図、
   `patches/README.md` 表、insight `output/insights/2026-09-05_dynamic-backoff-mechanism/` (段 7)、spool fragment。
3. **実測 (親)**: login node 短走 1 回 (DW-G01) → Pegasus perf 7 job + 診断 1 job + 認証 24 job。

## 確定済みユーザー裁定・正本

- D1505 (律速は更新間隔、上限は効かない)、D1506 (基準線 = 無 backoff + 調整済み adaptive、既定 adaptive 単独比の
  優位を書かない)、D14 (`#if` 契約)、D95 (実装面は Codex author)、規律 1・2 (perf build と診断 build は別 run、
  verifier を緩めない)、F660 (新 path なら実測は後続 wave)、2026-09-02 ユーザー裁定「条件を割って複数ノードへ同時投入、
  見積もりを先に書く」、T-2189 の認証機構 (`--mode certify`、連言 10 項、24 request の group receipt) を変えない。
- **brief 前の実測で見つけた、引数の前提に触れる新事実 (段 4 で再裁定):**
  - **D1576 (2026-09-03)** が「更新窓は一定でなく `Backoff_` とともに伸びる。更新の評価は leader (`thid_==0`) が
    試行を始めた瞬間だけ」と記録している。D1505 の計数ノイズ機序は前提が崩れたが反証されてはいない
    (T-2216 insight §2)。計数窓はこのノイズを直接狙う設計であり成立するが、**発火判定は leader の試行先頭でしか
    評価されない**ことを設計に織り込む。
  - `patches/ledger.json` は D18 第 4 類 ability probe 専用 (`scope: registered-entries-only`、entry 1 件) で、
    A 自身も登録されていない。「ledger へ登録」の実体は (P7)。
  - `patchharness.applied()` は 1 patch 専用で enter 時に pinned-clean を要求するため、そのままでは重ねられない。
  - T-2189 の certify は `.pbs` と driver の両方で `tuned:1:1:1000:2560` を exact に要求する。
  - gen_S は 06:47 JST 時点で Run 40 / 全 request 276。queue 待ちは見積もりに入らない (D612 上書きの対象外)。

## 不変条件

- A の bytes 不変 (pin: `condition_meaning_gate.py:79/84/101`、`test_t2187_adaptive_const_probe.py:23`、probe `:53`、
  `docs/paper-story/README.md`、`figures/README.md`、T-2189 認証の `patch_sha256`)。DW-O09 の path 閉包はこれで全件。
- 既定値 stock 同値: 新 define をすべて既定にした A+B build が、機構としては A 単独と同じ振る舞い。
- perf build (`BACKOFF_TRACE=0`) の binary に診断 symbol 0 個 (`nm` で示す。symbol 名は `izanagi_backoff_trace` 接頭辞)。
- certify の連言 10 項・陽性対照・24 request を変えない。認証は正しさだけで、性能値は全部**未認証**と書く。
- 凍結 artifact (T-2187 図・T-2189 認証 receipt・`izanagi-job-evidence/t2187-adaptive-3const/`) に書き込まない。
  本 wave の結果は別 dir `izanagi-job-evidence/dynamic-backoff/` に置く。

## 割れうる前提 (親の provisional 裁定、段 3 の攻撃対象)

- **(P1) 計数窓:** `check_update_backoff()` を「(committed_sum − last) ≥ K または経過 ≥ cap」に置き換える。
  K=0 なら従来の時間判定 (stock)。leader の試行先頭でしか評価されないので、K 到達の検知は遅れうる。それでよい。
- **(P2) 適応刻み:** 勾配符号が直前と同じなら刻み ×2 (上限 `STEP_MAX`)、反転なら ÷2 (下限 `STEP_MIN`)。
  勾配 0 の parity 分岐は「反転」と扱う。初期刻み = `kIncrBackoff`。`STEP_ADAPT=0` で固定刻み (stock)。
- **(P3) 動的上限 (最小実装):** `DYN_CEILING=1` のとき実効上限 `ceil_` を持ち、`Backoff_` が `ceil_` に当たって勾配が負なら
  `ceil_` を半減 (下限 = 刻み × 4)、勾配が正で当たれば ×2 (上限 `kMaxBackoff`)。「効果なし」を事前登録する腕。
- **(P4) 認証の範囲:** 動的 3 腕のうち全機構 on の 1 腕だけを 24 request (3 workload × 8 slot) で認証する。
  他 2 腕はその部分集合 (compile-time で落ちる) で、未認証と明記する。
- **(P5) 重ね適用:** probe は `applied(A)` の中で B を `apply_patch` し、exit の `revert_worktree` (`git checkout -- .`) が
  両方を戻す (B は新規 file を作らない)。全 6 cell を A+B で build する。生死確認で `tuned` を A 単独と A+B で build して
  binary sha を比べ、一致すれば inert の直接証拠、不一致なら差を記録し基準線は同 job 内の A+B build 同士で比べる。
- **(P6) 投入設計と見積もり:** ノードは rep 軸 (7 job × 1 rep、各 job が 6 cell × 3 workload × threads
  {6,12,18,24,30,36,42,48} = 144 run、extime 3 s)。前回 T-2187 段 2 (5 cell、120 run) は 8.5 分だったので
  1 job ≈ 6 build (~3 分) + prologue (~2 分) + 144 × ~3.6 s (~9 分) ≈ 15 分、walltime 40 分。診断 1 job: 動的 3 腕 ×
  3 workload × threads {24, 48}、`BACKOFF_TRACE=1` build、≈ 8 分。認証 24 job: T-2189 実測 (検査 23 分、job 約 52 分)
  から 1 job ≈ 55 分、walltime 2:15。計算ノード時間 ≈ 7×0.25 + 0.15 + 24×0.9 ≈ 24 ノード時間。queue は別勘定。
- **(P7) ledger:** `patches/ledger.json` の schema は ability probe 専用なので、新 patch は `patches/README.md` の表と
  `DefineSpec` registry へ登録し、`ledger.json` には classification を偽らずに書ける entry 形 (合成 variant、D18 第 3 類)
  が consumer (`tools/mutation_fanout.py` / `check_branch_rescue.py` / `s1_direct_comparison.py`) を壊さないと段 2 で
  確認できた場合だけ entry を足す。確認できなければ足さず理由を記録する。
- **(P8) 診断 run:** probe の performance mode に `--backoff-trace` を足し、genome に `BACKOFF_TRACE=1` を入れる。
  binary は stdout に `Backoff_` 軌跡 (更新ごとの時刻・値・勾配符号・的中) を出し、probe が JSON へ要約を書く。
  診断 build の throughput は headline に使わない。
- **(P9) 腕の値:** none / stock (100/1000/10、陽性対照) / tuned (1/1000/2560) / cw (刻み 1、上限 1000、cap 40960、
  K 10000) / cw+as (cw + adapt、step_min 0.25、step_max 8) / cw+as+dyn。K=10000 は tuned の 2560 µs 窓に入る
  約 10,000 commit (48 thread、4 M tps) と同じ計数。cap 40960 は T-2187 段 3 で悪化が見えた点。

## 成果物の形

patch B、probe 差分、tests、prereg doc、plot generator、insight (図 3 種: thread 軸 6 系列、診断 = `Backoff_` 軌跡と
勾配符号的中率、認証要約)、spool fragment (worklog 1、decisions 1〜2)、変異台帳 (DW-M01)。

## 並列分割方針

単位 A = patch B (C++/CMake)。単位 B = probe/pbs/tests/registry 追随 (define 名は本 brief で固定済みなので A と並列可)。
単位 C = plot generator + test (入力 JSON schema は probe の既存 `cells[]` に `count_window` 等の field を足す形で B と合意)。
段 6 fix は所見の file 集合で分ける。

## 実測環境

login node = brief 前提の実測と生死確認 1 回 (build と 1 秒走)。Pegasus gen_S = perf / 診断 / 認証。
runbook `docs/pegasus-runbook.md` §3・§7.5・§8。結果は `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/`。
