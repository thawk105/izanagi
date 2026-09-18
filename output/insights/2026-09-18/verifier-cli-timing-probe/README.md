# verifier CLI 単独計時 probe — read-heavy (rr95・3 秒・48 thread・1M records) の trace 有効 bench 1 反復を計算ノード 1 本で走らせ、生成 trace (17.13M commit・204M 行・6.52 GB) に対する `python3 -m orchestrator.verifier` の別 process 実行時間 421.7 秒を、trace 生成時間 3.3 秒と分けて 1 回観測した

- wave: `worktree-dev-wave-verifier-cli-timing-probe` (台帳 ID 未起票、entry 1654 [T-2229] の scope 外項)
- 起点 local main: `c8e8dc06f`。実装面の差分 0 (insight と worklog fragment のみ)。probe (Codex `role=author` 作) は repo へ入れず job dir に保全 (§6)。実装変更がないため変異テストの対象外
- **新規の測定投入は計算ノード job 1 本** (`5868.nqsv`、bnode041、smoke + 本走、Elapse 628 秒)。本走は **1 条件・1 反復・1 node の観測**であり、既往の「23 分」(D1554 / D2144) の内訳・代表所要時間・CC 性能を**確定しない**。D2144 の試算 (条件付き) を置き換えない (絶対規律 7)
- 当時の判定 (`correctness_certified`) は昇格も降格もさせない。本走の verdict は現行 verifier の出力をそのまま転記する (規律 2・7)
- **現行 verifier は 2026-09-02 の並列化 (T-2191) 後の code** で、D2144 が扱った `ed8a676b` 当時 (並列化前) の verifier とは別物である。本書の T_verify は「現行 CLI の既定 (parse worker 16) で 1 回」の値で、当時の値の再現ではない
- 段 6 の独立レビュー 2 本 (read-only codex、`gpt-6-astra` / medium) の所見と対応は §7

---

## 1. 一行で

本走 (bnode041、2026-09-18 15:32〜15:40 JST) で、campaign `ed8a676b` の反復と同じ動作点の trace 有効 bench process は **wall 3.344 秒** (rc=0、commit witness 17,128,612、abort 3,066,603) で終わり、生成 trace (48 file、204,048,743 行、6,520,332,111 bytes) に対する **`python3.10 -B -m orchestrator.verifier` は別 process で wall 421.707 秒 (7 分 1.7 秒)**、rc=0 `serializable` / `certified` (17,128,612 txn、296,980,787 edge、anomaly 0、integrity clean) だった。pipeline と同じ C 行数え直しは 16.858 秒。3 つの和は 441.909 秒で、内訳は bench 0.76% / 数え直し 3.81% / verifier **95.43%** (この 1 回の観測の内訳であり、当時の反復の内訳ではない)。

D2144 が契約 (`subprocess.run(timeout=120)`) から置いた「bench process は約 120 秒以下 (条件付き)」に対し、この観測の bench process は 3.344 秒で、trace 無し版の別走実測 3.35〜3.42 秒 (t2229 README §4 の参考値) と同程度だった。**これは 1 回の観測であり、上限の書き換えではない。**

---

## 2. 条件と識別

### 2.1 条件 (campaign `ed8a676b` の identity_preimage と同じ動作点)

| 項目 | 値 | 出所 |
|---|---|---|
| protocol / target | silo / `ycsb_silo.exe` | campaign.lock |
| CCBench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` (当時の campaign と現行 pin が同一) | campaign.lock `ccbench_commit`、`git submodule status` |
| configure defines | `-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` | 参照 genome `none` = `{BACK_OFF:0, BACKOFF_FIXED:-1}` + `_BASE` (`orchestrator/campaign/b10_backoff_shape_sweep.py`)、trace は `buildcache._v2_commands` の `-DCCBENCH_TRACE=1` |
| workload argv | `-ycsb_tuple_num=1000000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=95 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3 -clocks_per_us=2100` | records 1M / threads 48 / extime 3 / clocks_per_us 2100 / read-heavy の 4 key (campaign.lock)。形は pipeline `_run_trace` の `[binary] + [-k=v …] + [-clocks_per_us=N]` |
| numactl | なし (Pegasus g1 契約 `numactl=()`) | `orchestrator/campaign/env_contract.py` |
| env / cwd | `IZANAGI_TRACE_DIR=<trace_dir>`、cwd=`<trace_dir>`、`<trace_dir>/log/` を先に作る | `_run_trace` と同形 |
| trace_dir | 計算ノード local `/scr/verifier-timing-thko_kya/trace` (`TMPDIR` も同 scratch) | campaign と同じ node-local 配置 |

当時の campaign 木は `patches/silo-backoff-fixed.patch` (当時 sha256 `36cd974c…`、`git show 0a07481b8:patches/silo-backoff-fixed.patch` で照合) を当てていた。本 probe は patch を当てず stock pin を build し、`-DCCBENCH_BACKOFF_FIXED` は渡していない (stock の `cmake/Options.cmake` に無い変数)。**この差で主張できるのは backoff 動作の対応までである。** `include/backoff.hh` は `cc/silo/include/transaction.hh` L9 (と `common/runner.hh` L55) が無条件に include し、`Backoff backoff_` (transaction.hh L51, L69) はコンパイル対象に残る。`cc/silo/transaction.cc` の `#if BACK_OFF` (L42, L719) が除くのは `backoff()` と leader 更新の**呼出し**であり、当時の patch が足す定義 (`BACKOFF_FIXED` / `BACKOFF_NOINLINE`、`ccbench_universal_definitions`) と backoff.hh の変更は当時のコンパイル入力に入っていた (当時の `BACKOFF_FIXED=-1` は stock 分岐、`BACKOFF_NOINLINE=0`)。したがって**コンパイル入力の同一性も binary の bytes 同一性も主張しない**。一致を確認したのは workload argv と上に列挙した defines である。build 経路も campaign の `buildcache` v2 (receipt・policy token 付き。`-fmacro-prefix-map` / `-fdebug-prefix-map` / `-DCMAKE_SKIP_RPATH=ON` を足す、`buildcache.py` `_binary_path_cmake_defines`) ではなく plain cmake (T-2774 と同形: `-DCCBENCH_CCACHE=OFF`、compiler launcher 空、`-DCMAKE_CXX_FLAGS=` 空) である。同じ source・同じ defines で build dir だけが違う smoke と本走の binary も sha256 が一致しない (原因は特定していない)。

### 2.2 識別 (本走、`run/main/result.json` の `bindings`)

| 項目 | 値 |
|---|---|
| job / node | request `5868.nqsv` (gen_S)、bnode041、`Intel(R) Xeon(R) Platinum 8468`、affinity 48 CPU、site `PEGASUS_COMPUTE` |
| job の時刻 (JST) | Created 15:30:10、Started 15:30:18、Ended 15:40:42、Elapse 628 秒 (smoke + 本走。`dispatch-run.log` の accounting) |
| 本走の時刻 (UTC) | 開始 06:32:31.75 → bench Popen 06:32:58.93 → bench 終了 06:33:02.27 → verifier Popen 06:33:35.85 → verifier 終了 06:40:37.55 → 終了 06:40:41.98 |
| repo HEAD (superproject) | `c8e8dc06f33891aa2fd6345063b30ca11b52fe6d` |
| CCBench source | `patchharness.checkout(511c953…)` の使い捨て worktree、`assert_pinned_clean` = true |
| binary | `/scr/verifier-timing-thko_kya/build/cc/silo/ycsb_silo.exe`、sha256 `2a27e0800cbb1235139d251796176085c5a3cc62dbb4491bc89edab3f10f6931` |
| toolchain | `/usr/bin/x86_64-linux-gnu-gcc-11` / `g++-11` (version body sha256 `b713e6ab…`、policy `tools/pegasus/mocc_trace_v1_policy.json` sha256 `66ea7135…` の束縛)、gflags `e171aa2d…`、glog `8f9ccfe7…`、masstree / mimalloc / googletest は hydrate 済み staging |
| verifier の interpreter | `/usr/bin/python3.10` (3.10.12) |
| verifier module (file 別 sha256) | `cli.py 68e690c6…`、`core.py 4d70c244…`、`dsg.py e77eaabd…`、`model.py 59136847…`、`parse.py 1aedb77a…`、`report.py e68e31a0…`、`commit_receipt.py 106e0dcc…`、`__init__.py 56c7fb4c…`、`__main__.py 9a06c813…` (全桁は result.json) |
| `pipeline.py` sha256 | `472cc7a2…` (数え直し loop と witness 解析の正本) |
| verifier の既定 worker | `_effective_worker_count(48, None)` = **16** (parse の並列。`min(48 file, affinity 48, 16)`) |
| probe | `verifier_cli_timing_probe.py` 544 行、sha256 `03a1efbc832329982b1a947d21adefaced2fdb0356ab6462d462ee8f8b3d52f8` (smoke と本走で同じ版)。login (pegasus02) の `selftest` 25/25 PASS |

---

## 3. 計時範囲の定義 (結果を見る前に固定、段 4 裁定 §1)

| 記号 | 何を計るか | 主値 | 副値 |
|---|---|---|---|
| T_trace | trace 有効 bench process (records 読込 + 3 秒走 + trace 書出し/flush + 終了) | `subprocess.Popen` 直前〜`os.wait4` 復帰の `monotonic` 差 (親視点の wall) | Popen 復帰後〜wait4 復帰 (pipeline の timeout が計る `communicate()` 窓の近似)、`wait4` の rusage (user / sys / maxrss) |
| T_count | C 行数え直し (pipeline `_run_trace` と同じ純 Python loop を probe 内に写したもの) | 関数の wall | — |
| T_verify | `python3.10 -B -m orchestrator.verifier <dir> --json --expected-commits N --protocol silo --ccbench-root <src>` を別 process で (cwd = wave worktree) | 同上 | 同上 |

- T_trace は pipeline の `timeout=120` で打ち切らず (probe 側 900 秒)、120 秒超過の有無を別に記録した。
- verifier の内部段 (parse / DSG / cycle) は測っていない。CLI に引数の追加も変更もしていない。T_verify には interpreter の起動・import・引数解析・JSON の生成と出力・process 終了までが含まれる。
- stdout / stderr は pipe でなく file へ直結した (pipeline は `capture_output=True`)。file の open は計時の外。`start_new_session=True` の起動費用と watchdog thread の起動は wall に含まれる。probe の wall 観測としては成立するが、pipeline の I/O 経路の厳密な再現ではない。
- file 別の bytes / 行数 / sha256 の一覧は別 pass・別計時 (pipeline には無い処理)。ただしこの pass は **verifier の直前に trace 全体をもう 1 度読む**ので、T_verify は「数え直しと inventory の追加読出しの後の入力に対する CLI 時間」である。cache の常駐状態と効果量は測っていない (pipeline にも数え直しはある)。

---

## 4. 結果 (本走、`run/main/result.json`)

### 4.1 計時

| 区間 | wall (秒) | 副値 |
|---|---:|---|
| T_trace (bench process) | **3.344** | Popen 復帰 0.0002 秒後、`communicate()` 窓 3.344 秒、rc 0、user 143.193 秒 / sys 5.214 秒、maxrss 529,672 KiB (517 MiB)、120 秒超過 なし、timeout なし |
| T_count (C 行数え直し) | **16.858** | 17,128,612 行 (= commit witness)。換算 0.984 μs/commit、82.6 ns/行 (204,048,743 行) |
| (参考) file 一覧 pass | 16.676 | 行数・bytes・sha256。pipeline に無い |
| T_verify (verifier CLI) | **421.707** | Popen 復帰 0.0003 秒後、`communicate()` 窓 421.706 秒、rc 0、user 1812.169 秒 / sys 88.976 秒 (CPU 合計 1901.146 秒 = 原本の和 1901.145549、CPU/wall = 4.51 — 並列実行が起きたことと整合するが、16 worker 全てが正常完走したことの直接記録ではない。`parse.py` `_parallel_file_outcomes` には失敗時の fallback 経路がある)、`wait4` の `ru_maxrss` 46,084,868 KiB (43.95 GiB。待たれた子孫 = parse worker の最大 RSS が反映され得る値で、process tree の同時合計 RSS や cgroup peak ではない)、timeout なし |
| (参考) trace 複製 (node local → Lustre) | 3.979 | 6,520,332,111 bytes、pipeline に無い |

3 区間の和 = 3.344 + 16.858 + 421.707 = **441.909 秒**。割合は bench 0.76%、数え直し 3.81%、verifier 95.43%。maxrss は KiB (Linux)。

### 4.2 検証結果 (現行 verifier の出力をそのまま転記)

| 項目 | 値 |
|---|---|
| rc / verdict / certified | 0 / `serializable` / **true** |
| txns / edges | 17,128,612 (= `--expected-commits` = commit witness = C 行数) / 296,980,787 |
| anomaly_count / total_cycles | 0 / 0 (`verifier.json` の `"total_cycles": 0`、`anomalies` は空) |
| integrity | `clean` true、orphan_reads 0、version_dups 0、dup_txids 0、genesis_commits 0、missing_txids 0、write_version_mismatch 0、malformed_keys 0、framing_violations 0、lock_coverage_violations 0、write_intent_violations 0、permutation_violations 0、notes 空 |
| proof surfaces | CLI の JSON (`report.result_to_dict`) には `proof_surfaces` が無い (`proof_surfaces_present=false`)。`certified=true` は `Integrity.clean()` が `proof_surfaces.certification_gate_satisfied()` (X と P の `evidence-present`) を要求するので、X / P の text evidence は `--ccbench-root` の compiled source に在った (stock silo: `izanagi_trace::emit_lock_violation` ×3、`"P "` emitter L432) |
| 出力 | `verifier.json` 1,237 bytes、`verifier.stderr` 0 bytes、`bench.stdout` 21 行 (`commit_counts_: 17128612`、`batch_commit_counts_: 0`、`abort_counts_: 3066603`)、`bench.stderr` 0 bytes |

換算 (算術のみ): verifier は 421.707 秒 / 17,128,612 txn = **24.62 μs/txn**、/ 296,980,787 edge = 1.42 μs/edge。

### 4.3 既往の数値との位置関係 (比較ではない)

以下は**異なる時点・code・node・計時範囲の数値の併記**であり、速度向上や当時の内訳を推定しない (規律 7)。本観測の 3 区間の和 (bench + 数え直し + verifier CLI) と当時の WAL 反復区間は含む処理も一致しない (§3、§5)。

- D2144 の当時の反復 (並列化前 verifier、bnode022、`ed8a676b`) の中央値は 1408.8 秒 (高 commit 3 変種・13 反復の中央値で、欠測 attempt `292d58f1dad8` の 3 反復を含む。除いた 10 反復では 1398.7 秒 — t2229 README §2、D1529 の但し書き)。本観測の 3 区間の和は 441.909 秒 (現行 verifier、bnode041、1 回)。
- t2229 README §4 (D2144 本文にも同旨) の「bench process ≤ 約 120 秒 (条件付き)」は `subprocess.run(timeout=120)` の契約から置いた上限で、実時間の記録ではない。本観測の bench process は 3.344 秒 (1 回)。同 §4 の「Python 側 ≈ 91%」は当時の反復についての条件付き帰属で、本観測の内訳 (数え直し + verifier = 99.24%) で置き換えない。
- t2229 README §4 の数え直し換算「約 17〜19 秒 (1.0〜1.1 μs/commit、合成 trace の単価)」に対し、本観測の実 trace での数え直しは 16.858 秒 (0.984 μs/commit)。
- 並列化後の検査器で完走した `acf840c8` の反復帯は 595.5〜626.9 秒 (t2229 README §5.2 の高 commit 3 変種、bnode088、2026-09-05 の code)。本観測とは code 状態と node が違う。

### 4.4 smoke (code path の実走確認のみ、値は使わない)

10,000 records / extime 1 / 48 thread、同じ node・同じ job・同じ probe 版: T_trace 1.048 秒 (commit 4,933,099、abort 3,330,543)、T_count 4.741 秒、file 一覧 4.601 秒 (57,674,153 行、1,812,744,103 bytes)、T_verify **92.806 秒** (rc 0 `serializable` / `certified`、edge 92,352,511、user 413.954 / sys 22.207 秒、maxrss 13,585,176 KiB)、複製 1.228 秒。binary sha256 `258440e6…` (本走と別 build)。

---

## 5. 本書が保証しないこと

- 1 条件・1 反復・1 node の観測であり、代表値・帯・分散・node 間差を言わない。同じ条件で 2 回目を走らせれば別の値が出る。
- `ed8a676b` 当時の verifier (並列化前) の所要ではない。当時の反復の内訳 (t2229 README §4、D2144) は本書で変わらない。
- binary の bytes は campaign の `none` と同一と主張しない (§2.1)。
- trace 有効 build の throughput・commit 数は性能主張に使わない (規律 1)。本書の commit 数は verifier の入力規模の記述である。
- verifier の内部段別 (parse / DSG / cycle) の所要と、`workers` を変えたときの所要は測っていない。`ru_maxrss` は `wait4` が返す子孫込みの最大値で、CLI 本体だけの RSS ではない。
- pipeline の `verify_trace_dir_with_capability` は build admission・genome・source evidence の束縛を検査し、保存された source snapshot を渡し、capability receipt を生成し、`proof_surfaces` を WAL へ出す (`core.py`)。CLI は渡された checkout をその場で読み、それらを行わない。検証本体 (`verify_trace_dir`) は共通だが、**pipeline の検証段全体と同じ意味・同じ費用ではない**。逆に T_verify には CLI 固有の費用 (interpreter 起動・import・引数解析・JSON 出力) が入る。
- T_verify の直前に inventory pass が trace 全体を読んでいる (§3)。page cache の状態が pipeline の反復と同じとは言えず、その効果量は測っていない。
- §4.2 の X / P emitter の個数・行番号 (`emit_lock_violation` ×3、`"P "` L432) は親が stock source を grep した値で、`certified=true` が個数・行番号まで証明するわけではない。
- 単独性検査 (`_assert_single_tenant`) は bench 直前に 1 回だけ行い、verifier 実行中の外乱は測っていない (dispatch は node 1 本の専有割当て)。

---

## 6. 一次資料と再現手順

- job dir: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-cli-timing-probe/`
  - `run/main/result.json` (本走の全記録、file 別 sha256 を含む)、`run/main/summary.md` (`summarize` の射影)、`run/main/trace/` (trace 原本 48 file + `log/`)、`run/main/bench.stdout` / `bench.stderr`、`run/main/verifier.json` / `verifier.stderr`
  - `run/smoke/` (同構成、小規模)
  - `dispatch-run.log` (generic dispatch の log、request ID・Elapse)、dispatch receipt は `recovery-original-dispatch/receipt.json` (旧 wave worktree `output/pegasus-dispatch/ffe13d094bd3bef4523148ef4e7c3774/` の原資料一式を清掃前に保全)
  - `probe/verifier_cli_timing_probe.py` (probe 本体、sha256 は §2.2)、`probe/run-both.sh` (親の運転 script。smoke → rc=0 なら本走)、`selftest-login-1.log`
  - `s4-ruling.md` (段 4 裁定 = 設計正本)、`codex/prompt-author.md` / `codex/s5-author.md` (author の prompt と報告)、段 6 review の prompt と逐語は `codex/`
- repo 内の逐語: `verbatim/probe-source.md` (probe と運転 script の全文)、`verbatim/s6-review-A.md` / `verbatim/s6-review-B.md` (段 6 レビュー)、`verbatim/s6-focus.md` (焦点再レビュー)。`s6-review-B.md` は原文 (job dir `codex/s6-review-B.md`、sha256 `06f3e0a9b8474448bfc012828aa640d6d0e70c69ff623e7aeb93ae14af1a5a24`、13,257 bytes) の 149 行目と 150 行目の行末空白 2 個ずつを除いた可逆正規化 (13,253 bytes、可視文字不変。復元は両行の末尾に空白 2 個を戻す)
- 起動形 (login、wave worktree から): `python3.10 tools/pegasus/dispatch_compute.py --task generic --walltime 01:50:00 --queue-wait-timeout 14400 --overall-grace 14400 -- bash <job dir>/probe/run-both.sh`
- 一次資料の既往: D2144、`output/insights/2026-09-18/t2229-verify-cost-decomposition/README.md` §3〜§4、campaign.lock `izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-read-heavy-formal-ed8a676b/campaign.lock`

## 7. 段 6 レビューの所見と対応

read-only codex 2 本 (`gpt-6-astra` / medium)。A = 過剰・削除・測定妥当性 (`verbatim/s6-review-A.md`)、B = 整合・数値検算 (`verbatim/s6-review-B.md`)。A は **NO-GO** (must-fix 1、should 5、nit 1、観測値の棄却・再測定を要する所見なし)、B は **GO** (must-fix 0、should 4、nit 3。§4.1・§4.2・識別・時刻・smoke の主要値は原本と一致、派生値も独立再計算で一致し、CPU 合計の丸め差 0.001 秒だけを訂正)。修正提案は全件採用した (A3 と B8〜B10 は疑義の棄却 = refuted、他は real)。fix はすべて本 README の文言 (親が直接編集、実装面ゼロ)。

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| A1 | must-fix: (P1) の根拠「`backoff.hh` はコンパイル対象外・patch の差は cache 変数のみ」が誤り (`transaction.hh` L9 が無条件 include、patch は `BACKOFF_FIXED` / `BACKOFF_NOINLINE` の定義と backoff.hh の変更を含む) | real | §2.1 を「backoff 動作の対応まで。コンパイル入力・bytes の同一性は主張しない」へ書き直し、段 4 裁定 (job dir) と HANDOFF にも同じ訂正を追記 |
| A2 | should: buildcache の `-fmacro-prefix-map` / `-fdebug-prefix-map` / `CMAKE_SKIP_RPATH` と probe の `CCACHE=OFF` / launcher 空 / `CXX_FLAGS` 空を列挙し「compile 面の同一性」の結びを弱める | real | §2.1 に列挙、結びを「一致を確認したのは workload argv と defines」へ |
| A3 | refuted: 主計時・argv・数え直しに観測を無効にする不一致は無い (`timed_process` の計時位置、wait4 唯一の reaper、file open 計時外) | refuted (疑義棄却) | 変更なし。§3 に「pipeline の I/O 経路の厳密な再現ではない」を明記 |
| A4 | should: CLI と pipeline の差は capability と WAL だけでない (admission / genome / source evidence の束縛、snapshot、CLI 固有の起動費用)。worker 16 は選択値で fallback 経路がある | real | §3・§4.1・§5 に追記 |
| A5 / B3 | should: verifier 直前の inventory pass が trace 全体を読む → page cache の条件を明記 | real | §3・§5 に追記 |
| A6 / B4 | should: `ru_maxrss` は process tree の同時合計 RSS ではない | real | §4.1・§5 の文言を訂正 |
| A7 / B7 | should / nit: 31.4%・1/36 を否定文付きで併記するのは紛らわしい | real | §4.3 から比を削り「異なる時点・code・node・計時範囲の併記」へ |
| A8 | nit: `total_cycles` は原値 0 を転記できる | real | §4.2 を `0 / 0` へ |
| B1 | nit: CPU 合計は原本の和 1901.145549 → 3 桁丸めなら 1901.146 | real | §4.1 を訂正 |
| B2 | should: 1408.8 秒は高 commit 3 変種・13 反復の中央値で欠測 3 反復を含む | real | §4.3 に母集団と D1529 但し書きを併記 |
| B5 | should: `run/smoke/summary.md` と repo の `verbatim/s6-review-*.md` が未作成 | real | 両方作成 (§6 の参照先が実在) |
| B6 | nit: 「D2144 §4 / §5.2」は D2144 本文の節番号でない | real | t2229 README の節番号へ |
| B8〜B10 | refuted: 転記誤り・`proof_surfaces` 不在と certified の矛盾・D2144 置換の主張は無い | refuted (疑義棄却) | 変更なし |

焦点再レビュー (1 本、`verbatim/s6-focus.md`): **GO、closed 15 / partial 0 / regressed 0**。訂正文 (§2.1 の backoff の説明、§4.3 の併記) を source と当時の patch で裏取りし、全数値を原本と再照合して一致。新規 nit 3 件 (§3 の page cache の表現、§5 の参照先 §4.2、§7 の「全件 real」の整理) を反映した。
