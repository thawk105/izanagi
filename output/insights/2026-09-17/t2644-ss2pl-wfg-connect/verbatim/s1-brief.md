# 段 1 brief — [T-2644] SS2PL 待ちグラフ計器と検証器の接続 (親、2026-09-17 00:40 JST)

基準: local main `20a92f6a6`。worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect`。
本 brief は親の provisional な見立てであり、段 2・3 の子は brief 自身も検算・点検の対象とする。

## 研究前進

D791 の受理条件 (wait-for graph 閉路の持続性で受理、hang は証拠にしない) を実データで独立判定できる
計器→検証器の経路を初めて成立させる。`docs/cc-diagnostics.md`「既知の不足」1 件目を解消し、silo 等の
後続 CC 調査で deadlock 証拠を採る土台になる。

**完了判定:** 計装 build (arm `phase1`: `IMPL=1 KIND=0 DLR=0 WFG=1`) の計算ノード 1 走の実データで、runner の
production 経路 (`_admit_output` → `_extract_snapshots` → `validate_deadlock_evidence`) が `accepted_cycle ≠ None`
を返し、4 条件それぞれの判定材料 (辺の実 holder・3 枚同一・counter 不変・timed_out) が受領証に残る。
閉路が立たなければ「その窓で観測されなかった」と記録し、失敗扱いにしない。

## scope (本題の接続だけ)

1. **計器 (patch の `wfg.cc` / `ycsb_ss2pl.cc`)**: 閉路が立った watchdog tick ごとに標準出力へ 1 行 JSON event を出す。
   schema は検証器の要求形 — `nodes[thread_id, attempt, wait_lock_id, request_mode, commit_count, abort_count,
   held_locks[{lock_id, mode}]]`、`edges[waiter_thread_id, holder_thread_id, lock_id, request_mode, holder_mode,
   compatible:false]`。file 出力 (durable) も同じ field 名へ揃える。
2. **計器**: hang して kill される走行でも build 軸 4 つが読めるよう、起動時 (chkArg 後) に `ShowOptParameters()`
   相当の行を出す (`#if SS2PL_WFG_DIAG` 内)。**起票に無い 5 件目の断絶** — 現行は全 worker join 後にしか出ず
   (`external/ccbench/common/runner.hh:316`)、`_admit_output` が `parse_runtime_axes` で必ず落ちる。
3. **runner `_run_phase_trial`**: `-ss2pl_wfg_output=<trial ごとの scratch path>` を渡す (WFG=0 の性能 arm には渡さない —
   flag が `#if SS2PL_WFG_DIAG` 内でしか定義されず gflags が unknown flag で落ちる)。file の最終 JSON を受領証に残す。
4. **test (`orchestrator/tests/test_ss2pl_lock_study.py`)**: 計器の出力形の fixture 文字列が `_json_events` →
   `_extract_snapshots` → `validate_deadlock_evidence` を通る正例、旧 field 名 (`waiting_lock_id`/`waiter`) が受理されない負例、
   起動時軸行の parser 正例。
5. **1 走 probe** (Codex author が書く。job dir へ保全、repo へ commit しない): runner の production 関数
   (`clone_network_free` → `_apply_patch` → `build_target(arm="phase1")` → `_run_phase_trial(phase="phase1")`) を呼び、
   結果 JSON を書く。generic dispatch で計算ノードへ。
6. **docs (親)**: `docs/cc-diagnostics.md`「既知の不足」・`patches/README.md` の行を接続後の事実へ更新。過去の観測報告は否定しない。

**scope 外 (別起票):** phase2 の `acquisition_paths` counter 契約 (`_phase2_counters` :2476 が要求、計器は出さない)、
`tools/pegasus/ss2pl_lock_study.sh:207` の `policy[name + "_source_path"]` 破損 (T-548 後追い、policy.json に同 key は無い)、
検証器への tick 連続性検査の追加、他 protocol への計器配線、runner の新 mode、仮想リスク向け gate/検査/台帳。

## 確定済みユーザー裁定

D791 (4 条件、計器は既定 OFF compile-time、証拠は計装ビルドのもの)、D790 (patch 既定 `IMPL=0 KIND=1 DLR=1` は stock 逐語、inert)、
D16/D18 (out-of-tree patch、submodule へ commit しない)、D95 (実装面は Codex author)、D2022。逐語は同 dir の `verbatim-*.md`。

## 不変条件

- I1 (規律 1): `SS2PL_WFG_DIAG=0` build から計器が消える。`wfg.cc` は CMake で条件追加、stdout event・起動時軸行も
  `#if SS2PL_WFG_DIAG` 内。性能 arm の `_wfg_absence_evidence` (:2054) と inert witness が引き続き緑。
- I2 (規律 2): `validate_deadlock_evidence` (:2415-2473) の述語を緩めない。`holder_holds_lock:true` の主張枝でなく
  `held_locks` の実証枝 (`_holder_evidence` :2372) を通す。計器側の連続 3 回一致は残すが検証器はそれに依存しない。
- I3: patch は現行 pin `511c9538` へ `git apply --check` rc=0 を保つ (2026-09-17 に rc=0 を実測)。
- I4: 既存 test の期待値を変えない (`_persistent_cycle_snapshots` :1404 の 3 test は同 schema なのでそのまま緑のはず)。
- I5: 計器の watchdog は worker 自身に閉路検出させない (D791 却下案)。snapshot は registry mutex 下で一貫して取る。

## 成果物

patch 改版 + runner 差分 + test (1 commit、Codex author)、insight `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md`
(受領証の複写、probe の sha256/bytes、判定 4 条件の材料)、worklog / decisions fragment。

## 並列分割

段 5 実装子 A (所有: `patches/ss2pl-lock-protocol-study.patch`、`tools/pegasus/run_ss2pl_lock_study.py`、
`orchestrator/tests/test_ss2pl_lock_study.py`)、実装子 B (所有: probe `tools/t2644_wfg_probe.py`、親が実行後 job dir へ退避)。

## 受入・実測環境

unit test 焦点走は `tools/run_tests.py` の既定判定に従う。login は `cmake --build` と benchmark 実行を guard が拒否するので、
計装 build と 1 走は generic dispatch (gen_S、walltime 00:40:00、`python3.10` 明示 — 計算ノード既定 python3 は 3.9)。
依存: gflags/glog prefix `/work/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install` (実在確認済み)、thirdparty は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/thirdparty-src` (hydrate 済み、5 pin 一致、runner の
`_validate_thirdparty` rc=0)。gen_S は RUN 18 / QUE 0 (00:38)。受入全走は `dev_wave_wait.py acceptance`。

## (P) 親の provisional 裁定 — 攻撃対象

- (P1) 伝達は stdout event を一次にする (runner の既存 `_json_events` :2240 経路。SIGTERM/KILL 後も pipe 内の flush 済み行は
  `communicate()` が回収する)。durable file は同 schema の副次成果物として残す。file 一次に変えると runner 側の改変が大きい。
- (P2) field 名は検証器側へ揃え、計器側を変える。検証器の述語は無変更。
- (P3) 計器は閉路が立った tick だけ event を出し、`tick` (単調番号) を data として載せる。検証器の連続 3 枚検査は emit 列の
  上で行い、tick 連続性は検証器に足さない。
- (P4) node に `held_locks` を出し、`holder_holds_lock` は出さない。
- (P5) 1 走の動作点は high-contention (`ycsb_tuple_num=100, zipf 0, 48 threads, extime 10, hard timeout 60 s` =
  `_run_phase_trial` 既定 :2856-2861)。原 study はこの点で 6 node 閉路を報告 (`verbatim-report-cycle.md`)。
- (P6) watchdog は現行どおり連続 3 回一致で file を書いて停止する (event は 3 枚出て終わる)。
- (P7) 起動時の軸行は `#if SS2PL_WFG_DIAG` 内でのみ出す (性能 build の bytes を変えない)。

## 変更面のアンカー表 (2026-09-17 の現物、行番号は worktree のもの)

| 面 | file:line | 内容 |
|---|---|---|
| 計器 gflag | `patches/ss2pl-lock-protocol-study.patch:110-113, 122-125` | `common.hh`: `DEFINE_string(ss2pl_wfg_output)` / `DECLARE_string` は `#if SS2PL_WFG_DIAG` 内 |
| 計器 必須検査 | `patches/ss2pl-lock-protocol-study.patch:2196-2198` | `util.cc chkArg`: `FLAGS_ss2pl_wfg_output.empty()` なら ERR |
| 計器 軸行 | `patches/ss2pl-lock-protocol-study.patch:2216-2229` | `util.cc ShowOptParameters()`: 4 軸を 1 行で表示 (`": SS2PL_WFG_DIAG "` literal はここ 1 箇所) |
| 計器 出力 | `patches/ss2pl-lock-protocol-study.patch:2432-2481` | `wfg.cc cycle_json`: file 用 JSON。node = `thread_id, attempt, waiting_lock_id, requested_mode, commit_count, abort_count`、edge = `waiter, holder, lock_id, requested_mode, holder_mode` |
| 計器 終端 | `patches/ss2pl-lock-protocol-study.patch:2482-2492` | `terminal_json`: `cycle_found:false` + 計数 |
| 計器 watchdog | `patches/ss2pl-lock-protocol-study.patch:2494-2521` | 10 ms tick、`cycle_signature` 連続 3 回一致で `durable_replace` して return |
| 計器 durable | `patches/ss2pl-lock-protocol-study.patch:2414-2431` | tmp + fsync + rename + dir fsync |
| 計器 起動/停止 | `patches/ss2pl-lock-protocol-study.patch:2523-2546` | `ss2pl_wfg_start` (watchdog 起動) / `ss2pl_wfg_stop` (join、未書込なら terminal) |
| 計器 registry | `patches/ss2pl-lock-protocol-study.patch:2548-2620` | `register_worker` / `before_wait` / `acquired` / `acquire_failed` / `released` / 計数 |
| 計器 main | `patches/ss2pl-lock-protocol-study.patch:2626-2694` | `ycsb_ss2pl.cc`: `chkArg` → `displayWorkloadParameter` → `ss2pl_wfg_start` → `ccbench::run` → `ss2pl_wfg_stop` |
| 計器 hook 配線 | `patches/ss2pl-lock-protocol-study.patch:1382-1418` | `transaction.cc publish_wait / publish_acquired / publish_failed / publish_released` |
| 計器 CMake | `patches/ss2pl-lock-protocol-study.patch:1-56, 2694-2709` | `wfg.cc` は `CCBENCH_SS2PL_WFG_DIAG EQUAL 1` でのみ sources に追加 |
| CCBench 終端 | `external/ccbench/common/runner.hh:98-100, 316` | extime sleep → quit → join → `ShowOptParameters()` (join 後) |
| runner 定数 | `tools/pegasus/run_ss2pl_lock_study.py:40-48, 75-84` | `ARM_CONFIG` (phase1 = impl1 kind0 dlr0 wfg1)、`WFG_DIAGNOSTIC_IDENTIFIERS` |
| runner 軸 parser | `tools/pegasus/run_ss2pl_lock_study.py:2173-2185` | `parse_runtime_axes`: `ShowOptParameters()` 行が無ければ ContractError |
| runner event | `tools/pegasus/run_ss2pl_lock_study.py:2240-2252` | `_json_events`: `{` で始まる行だけ JSON として拾う |
| runner 抽出 | `tools/pegasus/run_ss2pl_lock_study.py:2347-2355` | `_extract_snapshots`: `event["wfg_snapshot"]` か、`nodes`+`edges` を持ち `event` に `wfg` を含む event |
| runner 述語 | `tools/pegasus/run_ss2pl_lock_study.py:2358-2473` | `_node_signature` / `_edge_is_incompatible` / `_holder_evidence` / `_edge_signature` / `_has_directed_cycle` / `validate_deadlock_evidence` |
| runner phase2 | `tools/pegasus/run_ss2pl_lock_study.py:2476-2504` | `_phase2_counters` (scope 外)、`_observed_conflict_count` |
| runner 受理 | `tools/pegasus/run_ss2pl_lock_study.py:2507-2567` | `_admit_output`: cache 束縛 → 軸 → workload flag → binary sha → events → metrics (phase1 は `require_metrics=False`) |
| runner process | `tools/pegasus/run_ss2pl_lock_study.py:2684-2716` | `_run_process`: `communicate(timeout)` → SIGTERM → 2 s → SIGKILL、`timed_out` / `termination` |
| runner argv | `tools/pegasus/run_ss2pl_lock_study.py:2719-2724` | `_workload_argv`: `-clocks_per_us -extime -thread_num -ycsb_*` |
| runner phase trial | `tools/pegasus/run_ss2pl_lock_study.py:2846-2903` | `_run_phase_trial`: argv 組立 (:2856)、timeout 60/62 (:2860)、`_admit_output` (:2863)、抽出・判定 (:2870-2872)、受領証 dict |
| runner controls | `tools/pegasus/run_ss2pl_lock_study.py:2905-2945` | phase1/phase2 × 2 点 × 3 trial |
| runner build | `tools/pegasus/run_ss2pl_lock_study.py:2091-2148` | `build_target`: condition gate → configure → build → compile definition 検証 → sha |
| test 正例/負例 | `orchestrator/tests/test_ss2pl_lock_study.py:1404-1477` | `_persistent_cycle_snapshots` (`holder_holds_lock:true` を使う合成) と 3 test |
| test loader | `orchestrator/tests/test_ss2pl_lock_study.py:17-30` | `driver = _load(...)` で runner を module として import |
| docs | `docs/cc-diagnostics.md:106-121, 190-201` | 必要な入力 / 既知の不足 (親が更新) |
| docs | `patches/README.md:12` | 計器の行 (親が更新) |
