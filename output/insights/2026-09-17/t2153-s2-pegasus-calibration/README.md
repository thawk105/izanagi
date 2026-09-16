# [T-2153] S2 縮小 verify 較正を現行 condition gate 下で Pegasus 計算ノードで実走した — driver そのままでは gate の compiler 解決で止まり JSON を産まない。同じ request に依存供給を足した gate CLI では 2 macro とも `unestablished_meaning_macros = []`

- wave: `dev-wave-t2153-s2-pegasus-calibration` / branch `worktree-dev-wave-t2153-s2-pegasus-calibration`
- 起点 main: `b4631a92e` (実測時の worktree HEAD と同一)
- 日付: 2026-09-17 (実測 06:56〜07:04 JST)
- 結論:
  1. **S2 driver (`orchestrator/campaign/s2_verify_calibration.py`、blob `d414d5b1c`) をそのまま Pegasus 計算ノードで
     走らせると、条件 gate の前処理 (`_preflight_condition_gates`) の最初の macro で
     `supply=red/compiler-failed, meaning=red/compiler-failed` になり、RuntimeError で終わる (bnode002、request `2731.nqsv`、
     Elapse 7 秒)。理由は driver が固定する `buildcache.DEFAULT_CXX = "g++-13"` が Pegasus に無いことで、
     configure にも前処理にも届かない。よって `output/env/<…>/calibration/s2_verify_*.json` は生成されず、
     `condition_gates[i].admission.unestablished_meaning_macros` は **S2 driver 経由では観測できない**。
     依頼が予期した `preprocess-failed` (masstree `config.h` 欠落、D2059 同型) は、その手前の段で止まるため到達しない
  2. **同じ request (driver_id / macro / requested 1 / default 0 / S2 の configure 引数 5 本) を gate CLI
     (`python3 -m orchestrator.campaign.condition_meaning_gate`) に渡し、Pegasus で使える compiler と依存供給だけを
     引数で足すと、`IZANAGI_BREAK_NOREAD_VALIDATION` と `IZANAGI_BREAK_HIGHKEY_VALIDATION` の両方が計算ノード
     (bnode003、`2732.nqsv` / `2733.nqsv`) で supply green / meaning green / admitted、
     `unestablished_meaning_macros = []` になった。** T-2153 が toy fixture でしか示せていなかった (a) 型の意味 witness
     が、実 CCBench TU (`cc/silo/transaction.cc`、S2 の broken patch 適用後) で立つことの初の実機実測である
  3. S2 driver を Pegasus で走らせて JSON を得るには、compiler・依存供給・`numactl`・`ENV_TAG` / `clocks_per_us` の
     4 点で driver の固定値を変える必要がある (§5 に列挙)。**本 wave では実装しない** (依頼「修正実装へ広げない」、
     D1986 項 8、D2104 項 10)
- 実装面の差分: 0 件。code・test・patch・dispatch・hooks は無変更。glue script は job dir に置き repo へ入れていない (§9)
- 一次資料: worklog archive 1585 の [T-2153] 項 (未確認事項の原文)、D924 (S2 driver は歴史再現用で pin `dff0f1e`、pegasus 契約は
  `clocks_per_us=2100` / numactl 無し)、D2059 (config.h 欠落の型)、D1986 項 8 (入り口を新設しない)、D2104 項 10
  (gate 側に別経路を持たない)、`orchestrator/campaign/pin.py` (歴史的 driver の再走手順)

## 1. 依頼と守った裁定

依頼は「S2 縮小 verify 構成の較正 (gate 3 点) を現行 condition gate 下で Pegasus 計算ノード (generic dispatch) で実走し、
`unestablished_meaning_macros` が空になるかを確かめる。masstree `config.h` 欠落で前処理 red になりうる — その場合は理由を
構造化して insight に返し、修正実装へ広げない。実装差分ゼロ (計測成果物 + docs)。gate・検査・台帳の追加は scope 外」。

| 裁定 | 内容 | 本 wave での扱い |
|---|---|---|
| 依頼 | 実装差分ゼロ、届かなければ理由を構造化して返す | driver は無変更。止まった段と reason code を §4 に、要る変更を §5 に列挙するだけで実装しない |
| D1986 項 8 / D1936 項 17 | 依存物をつなぐ入り口を新設しない | 既存 CLI + 既存 generic dispatch + `git clone` / `git apply` + 既存の依存 install prefix の組み合わせだけで走らせた (T-2213 と同じ形) |
| D2104 項 10 | `config.h` 欠落は prebuild 側で解く。gate 側に別経路は持たない | gate に触れていない |
| pin.py / D924 | 歴史的 driver の pin `dff0f1e` は張り替えない。再走は submodule を `dff0f1e` へ checkout して行う | detached submit-tree の submodule だけを `dff0f1e` へ detach した (wave worktree の pointer は不変) |
| 規律 1・2 | trace / 正しさ gate を緩めない | 測定は前処理判定のみ。trace-enabled build は起動していない |

## 2. brief 前に判明した、依頼の前提を変える 4 事実

すべて login node で実測した (逐語は `verbatim/login/`)。

| # | 事実 | 帰結 |
|---|---|---|
| N1 | S2 driver は `PIN = "dff0f1e"` を固定し、現行 submodule は `511c9538e` (3 commit 先)。`assert_pinned_clean` が `HEAD (511c9538e4e8) が pin (dff0f1e) と不一致` で rc=1 (M0a) | driver そのままでは gate の手前で止まる。pin.py が「正しい安全側動作」と定める設計であり、再走手順 (submodule を `dff0f1e` へ) に従った |
| N2 | Pegasus (login と計算ノードは同一 image、T-2213) に `g++-13` / `gcc-13` / `numactl` が無く、gflags / glog も system install されていない (`/usr/include/{gflags,glog}` 不在)。あるのは g++ 11.4.0 / cmake 3.22.1 | gate は `_resolve_compiler("g++-13")` で configure より前に `compiler-failed` になる。D2059 型の `preprocess-failed` には届かない |
| N3 | gate CLI `condition_gate_cli` は S2 の `_require_condition_gate` と同じ API 列 (`capture_define_inputs` → `make_define_request` → `evaluate_define_supply_effectuation` → `evaluate_define_runtime_meaning` → `require_condition_gate_family`、use_class `raw-measurement`) を呼ぶ | 供給を `--configure-arg=` で足すだけで、S2 の preflight と同じ request を実機で切り分けられる |
| N4 | S2 は `ENV_TAG="linux-baremetal"`、`CLK=1800`、`NUMA=["numactl","--interleave=all"]`、出力 path `<repo>/output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.{json,md}` を固定している (D924 が pegasus 契約 = 2100 / numactl 無しと明記) | driver そのままでは `output/env/pegasus/…` は生成されず、生成されても env tag が誤る |

既存成果物 `output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json` (2026-07-06、commit `9606c668c`) は
`condition_gates` を持たない (`all_pass = true`、`chosen_extime = 3`)。本 wave はこの file の bytes を変えていない。

## 3. 何をどう測ったか

すべて既存の部品で、新しい機構は無い。

| 部品 | 現物 |
|---|---|
| S2 driver | `orchestrator/campaign/s2_verify_calibration.py` (blob `d414d5b1c`)、無変更 |
| 判定器 | `python3 -m orchestrator.campaign.condition_meaning_gate` (blob `df3addc7b`)、無変更 |
| 計算ノード投入 | `python3 tools/pegasus/dispatch_compute.py --task generic --walltime … -- <argv>` (blob `9778e56cb`)。clean env (HOME / PATH 等のみ)、cwd = 投入元 checkout |
| M1 の木 | detached submit-tree `<job dir>/submit-tree-s2` (superproject `b4631a92e`、`tools/dev_wave_submodule_init.py` で再帰初期化後、submodule だけ `dff0f1ef2a4b…` へ detach。superproject は gitlink dirty `M external/ccbench` のみ) |
| M2 の木 | `/work/1/SFC/tanab/dev-wave-scratch/t2153-s2-pegasus-20260917/ccbench-dff0f1e-{norw,highkey}` — `external/ccbench` の shared clone を `dff0f1e` で detach し、`patches/broken-silo-norw-validation.patch` (sha256 先頭 `6f2ec73561eaf1ba`) / `patches/broken-silo-highkey-validation.patch` (`1c2daa8762ac89dd`) を `git apply` (S2 の `patchharness.applied` と同じ操作)。両 patch は `dff0f1e` にも現行 `511c953` にも `git apply --check` で当たる |
| compiler / cmake | `/usr/bin/x86_64-linux-gnu-g++-11` (11.4.0) / `/usr/bin/cmake` (3.22.1)。M1 は driver 固定の `g++-13` |
| 依存 (M2 のみ) | gflags / glog: 既存 prefix `/work/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install`。FetchContent: 永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache/{masstree,mimalloc,googletest}` (masstree に `config.h` あり = build 済みで汚れている cache。gate は build しないので `config.h` の実在が要る。T-2213 と同じ形) |
| request (M2) | `--driver-id orchestrator.campaign.s2_verify_calibration --macro <M> --requested-value 1 --default-value 0` + configure 引数 = S2 の `STOCK_G.cmake_defines()` 4 本 (`-DCCBENCH_BACK_OFF=1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0`) + `-DCCBENCH_TRACE=1` — ここまで S2 の `_require_condition_gate` と同一。追加は Pegasus 用の供給 4 本 (`-DCMAKE_PREFIX_PATH=<gflags>;<glog>`、`-DCMAKE_C_COMPILER=…gcc-11`、`-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=<cache>/<name>`) と `--cxx …g++-11` |
| M1 の argv | `env TMPDIR=/scr python3 -m orchestrator.campaign.s2_verify_calibration` — driver は `tempfile.gettempdir()` で空き 20 GB を要求するため、計算ノードの `/scr` を指した (driver の挙動は不変) |

argv の逐語は各 `verbatim/dispatch-<req>/request.json` の `args`。

## 4. 結果

| 走行 | 場所 | 対象 | 到達段 | 結果 | 逐語 |
|---|---|---|---|---|---|
| M0a | login | S2 driver そのまま、submodule `511c953` | `assert_pinned_clean` | rc=1 `patchharness: HEAD (511c9538e4e8) が pin (dff0f1e) と不一致 — 別版の tree に patch を当てない (fails-closed)`。単独性・空きディスクの検査は通過 | `verbatim/login/m0a-s2-asis-511c953.stderr.txt` |
| M0b | login | gate CLI、NORW、供給あり、g++-11 | 全段 | rc=0、supply **green** `requested-default-preprocess-different`、meaning **green** `declared-compile-time-branch-selection-observed`、admitted true、`unestablished_meaning_macros = []` | `verbatim/login/m0b-gate-norw.stdout.jsonl` (3 行 JSON) |
| **M1** | **bnode002、`2731.nqsv`** (queue 待ち 5.2 s、Elapse 7 s、child rc 1) | **S2 driver そのまま、submodule `dff0f1e`** | `_preflight_condition_gates` の 1 本目 (NORW) | **RuntimeError `condition gate rejected IZANAGI_BREAK_NOREAD_VALIDATION: supply=red/compiler-failed, meaning=red/compiler-failed`**。単独性・空きディスク (`/scr`)・pinned-clean は通過。stdout 0 byte、JSON / md 未生成。patch は `applied()` の finally で復元され submodule は clean に戻った | `verbatim/dispatch-2731/` |
| **M2a** | **bnode003、`2732.nqsv`** (queue 待ち 5.2 s、Elapse 9 s、child rc 0) | gate CLI、`IZANAGI_BREAK_NOREAD_VALIDATION` | 全段 | supply green / meaning green / **admitted、`unestablished_meaning_macros = []`** | `verbatim/dispatch-2732/` |
| **M2b** | **bnode003、`2733.nqsv`** (queue 待ち 5.2 s、Elapse 8 s、child rc 0) | gate CLI、`IZANAGI_BREAK_HIGHKEY_VALIDATION` | 全段 | supply green / meaning green / **admitted、`unestablished_meaning_macros = []`** | `verbatim/dispatch-2733/` |

判定器が保存した前処理の証拠 (要点。全 field は各 stdout の JSON):

| 走行 | owner TU sha256 | requested bytes / digest | control (default) bytes / digest | meaning (requested / default) |
|---|---|---|---|---|
| M0b login NORW | `7267fe9f8929…` | 4,514,644 / `58260d06748a…` | 4,514,738 / `e0f007a6387e…` | selected 1 / completed 1 ・ selected 0 / completed 1 |
| M2a compute NORW | `7267fe9f8929…` | 4,514,644 / `58260d06748a…` | 4,514,738 / `e0f007a6387e…` | 同上 |
| M2b compute HIGHKEY | `bc79697eba67…` | 4,514,997 / `cac4cfde664b…` | 4,514,798 / `87287a1f2f61…` | selected 1 / completed 1 ・ selected 0 / completed 1 |

NORW は login と計算ノードで前処理 bytes・digest が一致するので、**判定は環境に依らない** (T-2213 と同じ性質)。
witness は `owner-tu-compile-time-conditional-branch-selection`、開始指令は `#if IZANAGI_BREAK_NOREAD_VALIDATION` /
`#if IZANAGI_BREAK_HIGHKEY_VALIDATION` (`cc/silo/transaction.cc` 388 行、patch が挿入する枝)。要求値 1 で枝が選択
(1,1)、既定値 0 で非選択 (0,1) という T-2153 の toy 実測と同じ対 (selected, completed) が実 TU で観測された。

## 5. S2 driver が Pegasus で JSON を産むまでに要る変更 (列挙のみ、実装しない)

driver そのままで止まる段を順に辿ると、次の 4 点が独立に立ち塞がる。いずれも driver の固定値であり、
依頼の「実装差分ゼロ」「修正実装へ広げない」に従って本 wave は触れていない。

1. **compiler:** `_require_condition_gate` と `_broken_build_and_verify` と `buildcache.build` が `buildcache.DEFAULT_CXX` (`g++-13`)
   を使う。Pegasus には無い (M1 の停止点)。site policy で解決する経路が既存 Pegasus driver にはあるが、S2 は使っていない
2. **依存供給:** S2 は gate にも `buildcache.build` (legacy v1、FetchContent 供給の引数なし) にも依存物を渡さない。計算ノードは
   外部ネットワーク不在で gflags / glog も system に無いので、compiler が解決できても configure が落ちる
   (gate なら `configure-failed`)。供給を足しても masstree が prebuild 済みでなければ `preprocess-failed` (D2059 の型) になる
3. **`numactl`:** `_run_once` が `numactl --interleave=all` を前置する。Pegasus に無い (D924: pegasus 契約は numactl 無し)
4. **環境契約:** `ENV_TAG="linux-baremetal"` / `CLK=1800` 固定。Pegasus は `pegasus` / `2100` (D924)。出力 path も
   `output/env/linux-baremetal/…` 固定で、既存の linux-baremetal 成果物を上書きする

加えて pin: driver は `dff0f1e` を固定し、現行 tree (`511c953`) では pinned-clean assert で止まる (N1)。これは設計 (pin.py) であり
変更対象ではない — 再走は submodule を `dff0f1e` へ checkout して行う。

**gate 3 点 (contention 再現 / trace 規模 / 赤検出力) は測っていない。** 1〜4 が揃わない限り driver は gate 1 に届かない。
本 wave の実測は「S2 の preflight が要求する条件 gate が実 TU で admitted になる」ところまでである。

## 6. B-10 の meaning witness に関わる事実 (記録)

- T-2153 が `CONDITIONAL_BRANCH_WITNESSES` に足した (a) 型 (`#if` 枝選択) の witness は、toy TU (1585 の生死実験) だけでなく
  **実 CCBench TU + 実 patch + 実 compiler (g++ 11.4.0) + 実 CMake configure** で `declared-compile-time-branch-selection-observed`
  になる。2 macro とも計算ノードで再現し、login と bytes 一致
- B-10 の campaign が使う macro (backoff shape 系) は本 wave の 2 macro と別物であり、**B-10 の witness そのものを測ったのではない**。
  本 wave が示すのは機構 (登録済み `#if` 枝の選択観測) が実 TU で働くことまでで、B-10 側の各 macro については別途その request で
  取る必要がある
- 前処理判定は compiler 版 (g++-13 → g++-11) に依らないと見ているが、これは同一 request を両 compiler で比べた結果ではない。
  linux-baremetal (g++-13) 側の同じ request は本 wave では取っていない

## 7. 前提・限界

- (P1) M2 の依存供給は永続 cache (`config.h` あり) を使った。hydrate 直後の staging (`config.h` 無し) で `preprocess-failed` になる型は
  D2059 / T-2650 で実測済みなので、本 wave では取っていない (規律 4)
- (P2) M1 の `TMPDIR=/scr` は driver が honor する POSIX の knob で、driver の挙動を変えていない。`/scr` の空きが 20 GB 未満なら
  driver は disk 検査で止まっていたはずで、通過したことは `verbatim/dispatch-2731/` の traceback (到達段が preflight) が示す
- (P3) M2 の compiler は Pegasus にある g++-11。S2 が固定する g++-13 とは版が違う (§6)
- (P4) M1 の pin `dff0f1e` は pin.py が定める再走手順であり、pin の張り替えではない。submit-tree は使い捨てで、wave worktree の
  submodule pointer は `511c953` のまま
- gate CLI と S2 の preflight は同じ API 列だが、S2 は `applied()` の中で gate を呼ぶ。M2 は `git apply` 済みの clone を
  `--source-root` に渡した。適用操作は同じ (`patchharness.apply_patch` = `git apply`) で、適用後の owner TU sha256 は M0b / M2a / M2b
  が記録している
- 本 wave は計算ノードの 3 job (合計 Elapse 24 秒) だけを使い、trace-enabled build・benchmark・verifier は起動していない

## 8. 踏んだ罠

- **同一 checkout からの generic dispatch は 1 本ずつしか走らない。** `dispatch_compute.py` は qsub 直前に pending orphan hold
  (`output/pegasus-dispatch/orphan-hold.json` + `orphan-holds/unknown-<hex>.json`、`phase: pending-qsub`、`request_id: null`) を
  create-only で置き、**receipt を永続化する終端まで解放しない** (`persist_receipt_then_release_pending`)。qsub 受理後も
  request が RUN の間ずっと残る (07:02:31 JST に実測、2732 は RUN 中で hold は `pending-qsub` のまま)。M2b を M2a の 5 秒後に同じ
  wave worktree から投げたところ `orphan-hold` で rc=16 (infra、child 未起動) になり、M2a の終端後に投げ直して通った。
  M1 は別 checkout (submit-tree) だったので同時に走れた。並列に投げるなら checkout を分ける
- `--configure-arg -D…` (空白区切り) は argparse が拒む (T-2213 の再掲)。等号形で書いた

## 9. 逐語一覧

`verbatim/` 配下。job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-s2-pegasus-calibration/` に使い捨て launcher
(`run-m1-s2-driver.sh` sha256 先頭 `705438f873178fc0`、`run-m2-gate.sh` `8a3a5cd3c334864e`) と login 側の log がある
(repo へ入れない、D1786 / compute probe の規律)。

| path | 内容 |
|---|---|
| `login/m0a-s2-asis-511c953.stderr.txt` | M0a の traceback (pin 不一致) |
| `login/m0b-gate-norw.stdout.jsonl` | M0b の gate 出力 3 行 (supply / meaning / admission の canonical JSON) |
| `dispatch-2731/{request,receipt,result,compute-visible}.json` | M1 の dispatch request (argv の逐語)、receipt (bnode002、queue 待ち、会計)、result、compute-visible |
| `dispatch-2731/izdw-0530498306.o2731.txt` / `.e2731.txt` | M1 の job stdout (0 byte) / stderr (traceback + NQSV 会計) |
| `dispatch-2732/…` | M2a (NORW) の同上。stdout は gate JSON 3 行 (`.o2732.jsonl`) |
| `dispatch-2733/…` | M2b (HIGHKEY) の同上 (`.o2733.jsonl`) |

receipt.json は dispatcher が job stdout の tail を `scheduler_logs.stdout.tail` に埋め込むため `.o` と内容が重なる。一次は `.o` file、
dispatch の帰属 (host / request / queue 待ち / 会計) は receipt。
