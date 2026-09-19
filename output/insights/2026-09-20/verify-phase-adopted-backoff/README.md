# 検証相 (独立 8 反復 × 3 workload、trace-enabled、extime 3 s) — 採用候補 fixed-5 / fixed-10 を Pegasus 計算ノードで通し、両候補とも 24 枠すべて serializable・certified・anomaly 0 (S-1 (iv 付属) 規則の準用、台帳 ID 未起票)

- wave: `worktree-dev-wave-verify-phase-adopted-backoff` (背景 job fa9409aa、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/`)
- 起点 local main: `657e1e5a7` (着手時 `a99425b66` から ff)。**実装面 (repo 内) の差分 0** (insight・results 系列稿・paper-story README 表 1 行・worklog / decisions fragment のみ)。runner (Codex `role=author` 作) は repo へ入れず job dir に保全 (§9)。変異 matrix は `DW-S04` により免除、受入全走は免除しない
- **新規の測定投入は計算ノード job 18 本** (段 A 校正 6 本 `10868〜10873.nqsv`、段 B 本走 12 本 `11268〜11279.nqsv`、gen_S、2026-09-19 22:46 (段 A 投入) 〜 2026-09-20 00:43 (段 B 最終 job 終了) JST)。記録は校正 18 + 本走 48 = 66 件、うち実走は 64 (校正 16 + 本走 48、read-heavy 10 s の 2 件は規則により未実走)。性能値は取らない (規律 1: trace-enabled build の throughput は診断生値として記録するだけで、性能主張・比較に使わない)
- ユーザー裁定 (2026-09-19) の逐語と wave 側の解釈は `rulings-inbox/2026-09-19-verify-phase-adopted-backoff-authorization.md` と段 4 裁定 (`verbatim/s4-ruling.md`)。設計判断は `{{D:verify-phase-adopted-backoff-authorization}}` (fold 後の D 番号は decisions を見る)
- 段 6 の独立レビューの所見と対応は §10

---

## 1. 一行で

採用候補 2 genome — **fixed-5** (`silo`、`BACK_OFF=1, BACKOFF_FIXED=5`、= T-1998 事前登録 v1 の target = A-2 rr50 採用値) と **fixed-10** (`BACKOFF_FIXED=10`、A-2 rr5 採用値) — について、trace-enabled build で write-heavy / balanced / read-heavy 各 8 独立反復 (extime 3 s、計 24 verify) の trace を `python3 -m orchestrator.verifier` に掛けた結果、**両候補とも 24 枠すべてが `serializable`・certified・anomaly 0** だった。校正 (段 A) で完走した各 6 verdict も anomaly 0。判定は runner の `summarize` が §4.1 の規則を機械適用して **fixed-5 = pass、fixed-10 = pass** を返した (判定集合 = 本走 24 + 校正完走 6 = 30 件 / 候補、anomaly 0、未完走 = 校正 10 s の 2 件 / 候補を開示)。

これは「独立反復 n=8 × 3 workload で anomaly ゼロ」という**操作的事実**であり、形式的信頼度 1−εⁿ は主張しない (§7)。S-1 事前登録 (iv 付属) の充足ではなく、2026-09-19 のユーザー裁定で対象を採用候補へ変え、同節の規則を**準用**した追加検証である (§2)。

---

## 2. 位置づけ — S-1 (iv 付属) の準用

`docs/phase3-main-experiment.md` 層 1 (iv 付属)「検証相の拘束数値」の対象は系側 gate 構成 (g_rl / g_rt) である。本 wave はそれを充足したのではなく、ユーザー裁定により対象を採用候補 2 genome へ変え、同節の規則を準用した。対応表:

| 項目 | S-1 (iv 付属)・2026-07-16 校正 | 本 wave |
|---|---|---|
| 対象 | headline 最終候補 = 系側 gate 構成 (g_rl / g_rt) | fixed-5 / fixed-10 (固定 backoff、silo) |
| 環境 | cygnus `linux-baremetal` | Pegasus gen_S 計算ノード (node-local build・trace、Lustre へ保全) |
| 反復数 | N_verify = 8 独立反復 / workload、3 workload、計 24 | 同じ (候補ごとに 24) |
| 校正 | read-heavy × g_rl 1 本、extime {3, 6, 10} 昇順各 1 回、verifier wall ≤ 600 s の最大値、600 s 超で残候補打ち切り、hard timeout 1200 s、timeout は校正全体の失敗 | 2 候補 × 3 workload の 6 本、同じ選択関数 (`s1_verify_extime_calibration.choose_extime` を流用)、候補ごとに 1 値 = 3 workload の適格集合の共通部分の最大、hard timeout 3600 s、未完走は `indeterminate` として開示し完走 prefix から選ぶ (§5.3) |
| 判定 | 24 verify 全て anomaly ゼロで pass、1 件でも anomaly で失格 | 同じ。判定集合 = 本走 24 枠 ∪ 校正で完走した verdict。未完走 (校正) は pass を妨げないが件数・保全先を必ず開示 |
| 1−εⁿ | 主張しない (同節の限定表現) | 主張しない |
| 記録先 | 同節へ日付付き追記 (2026-07-16 に実施) | 同節へは追記できない (凍結束縛、§8)。D fragment・本 README・results 系列稿に日付付きで記録 |

---

## 3. 対象候補と identity

| 候補 | genome (silo) | 実測 identity (`src_token` = `source_bytes_sha256`、build 前後で期待値と一致、候補ごとの 9 job 全部) | 既存記録との関係 |
|---|---|---|---|
| fixed-5 | `BACK_OFF=1, BACKOFF_FIXED=5` + `NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0` | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` | **T-1998 事前登録 v1 §5 target の `source_bytes_sha256` と bytes 一致**。A-2 attempt `t2364-20260907b` rr50-fixed5 の `src_token` `21def77c944b1b855ea2da5516a7280858957888ec1b0644b80d9ae51e73c98a` とは不一致 |
| fixed-10 | `BACK_OFF=1, BACKOFF_FIXED=10` + 同上 | `16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d` | A-2 同 attempt rr5-fixed10 の `src_token` `955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9` とは不一致 |

- 導出: pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` の使い捨て checkout (`patchharness.checkout`) → `assert_pinned_clean` → `patchharness.applied("patches/silo-backoff-fixed.patch")` (現行 sha256 `a5e0710c3f767447…`) の内側で `source_digest.resolve_evidence(genome, pin, cxx="g++")`。tracked_paths = `cmake/Options.cmake`, `include/backoff.hh`。runner は build 前と build 後の両方で期待値と一致しなければ fail-closed (18 job すべて一致)。
- **A-2 と不一致の理由 (git で実測):** A-2 の izanagi source commit `31ec382a7` は patch の改訂 `91a5bfca3` (2026-09-07 23:39 JST「静的 backoff の表現可能上限を 999 から 9999 マイクロ秒へ広げる」) を含まない (`git merge-base --is-ancestor` 偽)。改訂の差分は `now_backoff` 三項式の**最終 else 分岐 (生値 ≥ 3000 の復号)** の 1 行だけで、`BACKOFF_FIXED / 1000 == 0` (5・10 µs) が選ぶ最初の分岐 `static_cast<double>(BACKOFF_FIXED)` は不変。commit message は「生値 0〜2999 の 3 領域の復号結果は数値的に不変であり、stock 枝・骨格・マーカー・待機ループは 1 byte も変えていない」と書く。
- 限定: 本検証は、A-2 rr5-fixed10 で採用された固定 10 µs という設定を、**現行 patch の trace-enabled build で**検証した。A-2 当時とは source bytes が異なり、当時のソース・バイナリの再検証や過去の certified 判定の昇格を意味しない (規律 7: A-2 / T-1998 の記録はそのまま保持し、本検証は現行 source の新しい事実として併記する)。fixed-5 は T-1998 v1 target と source bytes まで同一である。
- patch 無しの対照 (login、build 無し): fixed-5 の `src_token` = `stock`、`source_bytes_sha256` = `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` = T-1998 §4.2 が「受理しない」と書いた値。導出手順の再現性の確認。

---

## 4. 条件と識別

### 4.1 build と bench

| 項目 | 値 |
|---|---|
| protocol / target | silo / `ycsb_silo.exe` (`<scratch>/build/cc/silo/ycsb_silo.exe`、node-local `/scr`) |
| configure defines | `-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_BACKOFF_FIXED=<5|10> -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` (+ Release、sanitizer OFF、ccache OFF、launcher 空、FetchContent 3 本と gflags/glog の prefix は hydrate 済み依存へ) |
| toolchain | `/usr/bin/x86_64-linux-gnu-gcc-11` / `g++-11` (`x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`、version body sha256 `b713e6ab…`、policy `tools/pegasus/mocc_trace_v1_policy.json` sha256 `66ea7135…`)。digest 用の `cxx="g++"` の実体と build compiler の実体が同一であることを job 内で照合 |
| workload argv | `-ycsb_tuple_num=1000000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=<5|50|95> -ycsb_rmw=0 -ycsb_max_ope=10 -extime=<E> -clocks_per_us=2100` (A-2 policy v2 `performance_common`・entry 1681 と同じ動作点、numactl なし) |
| env / cwd | `IZANAGI_TRACE_DIR=<trace_dir>`、cwd=`<trace_dir>`、`<trace_dir>/log/` を先に作る (pipeline `_run_trace` と同形)、bench timeout 120 s |
| 「seed×N」 | ycsb は CLI seed を持たず run ごとに自己シードする。N = bench process が生成した trace の数。記録できるのは rep-id・PID・開始時刻・argv であり、数値 seed・seed の相異・乱数列の独立性は記録できない (`seed_mode=self-seeded`、`seed=null`) |
| 単独性 | `p2_2._assert_single_tenant()` を毎 bench・毎 verifier の直前に実行 (全走 通過) |

### 4.2 verifier と保全

| 項目 | 値 |
|---|---|
| verifier | `/usr/bin/python3.10 -B -m orchestrator.verifier <trace_dir> --json --expected-commits <commit witness> --protocol silo --ccbench-root <checkout>`、cwd = submit-tree (repo HEAD `657e1e5a7860a0ff77fd02ab37a6cb58b64cc78c`)、別 process、`--max-report` は既定 20 |
| verifier module (file 別 sha256、18 job 同一) | `__init__.py 56c7fb4c…`、`__main__.py 9a06c813…`、`cli.py 68e690c6…`、`commit_receipt.py 106e0dcc…`、`core.py 4d70c244…`、`dsg.py e77eaabd…`、`model.py 59136847…`、`parse.py 1aedb77a…`、`report.py e68e31a0…`。`orchestrator/campaign/pipeline.py` `472cc7a2…` (数え直し loop と witness 解析の正本) |
| verifier の既定 worker | `_effective_worker_count(48, None)` = 16 |
| hard timeout | 校正 3600 s、本走 1800 s (§5.3 の規則) |
| 計時範囲 | 各 process = `Popen` 直前〜`os.wait4` 復帰の monotonic 差 (entry 1681 と同形)、数え直し・保全は関数の wall、job = setup 開始〜cleanup 終了 |
| 保全 | **verifier 起動前に**全 trace file を inventory (file 別 sha256 / bytes / 行数) → `zstd -T0 -3` で job dir へ (圧縮後 sha256 / bytes を記録) → 保全完了 flag → verifier。全 64 走 × 48 file = **3072 file、原本 213,338,672,445 bytes (213.3 GB) → 保存 48,928,578,277 bytes (48.9 GB)、圧縮率 4.36**。保全先 `run/calib/<c>-<w>/extime-<e>/trace/`、`run/verify/<c>-<w>-<k>/rep-<i>/attempt-<a>/trace/` |
| 実行場所 | 各 job 1 node (site `PEGASUS_COMPUTE`)、投入元は job ごとに別の detached submit-tree (`submit-tree-a1〜a6`、`b1〜b6`、HEAD `657e1e5a7`)、generic dispatch (`--task generic`) |

### 4.3 runner

`verify_phase_runner.py` (Codex `role=author` 作、repo へは入れない、原本は job dir `probe/`)。**走行に使った版 = v1、1301 行、sha256 `91bbf85d594085a4900bb2e9272bd455cef18e83c258ccfe5828594c0afd82a7`** (全 66 記録 (実走 64 + 未実走 2) の `result.json` の `runner_sha256` がこの値)。段 6 fix 1 で `summarize` の ruling sha 検査に許可集合を足した **v2、1384 行、sha256 `c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5`** で最終集計 (§6.3)。login の `selftest` は v1 42/42、v2 49/49 PASS。逐語は `verbatim/runner-source.md`。

---

## 5. 校正 (段 A、投入 2026-09-19 22:46 JST、最初の job 開始 22:49:38、最後の job 終了 2026-09-20 00:01:24 JST、集計 `summary-A.json` 00:02:02 JST)

### 5.1 全 18 記録 = 実走 16 + 未実走 2 (`run/calib/<c>-<w>/extime-<e>/result.json`)

| 候補 | workload | extime | node | commit | bench s | count s | 保全 s | verifier 完走 | rc | verdict | certified | anomaly | verifier wall s | maxrss GiB | eligible | stop | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed-5 | write-heavy | 3 | bnode125 | 2530609 | 3.340 | 2.487 | 5.293 | True | 0 | serializable | True | 0 | 115.676 | 9.7 | True | — | completed |
| fixed-5 | write-heavy | 6 | bnode125 | 5017504 | 6.343 | 4.934 | 8.071 | True | 0 | serializable | True | 0 | 247.475 | 18.8 | True | — | completed |
| fixed-5 | write-heavy | 10 | bnode125 | 8323838 | 10.325 | 8.229 | 12.362 | False | -9 | — | — | — | 3601.454 | 17.9 | False | verifier timeout | indeterminate |
| fixed-5 | balanced | 3 | bnode132 | 4450058 | 3.332 | 4.431 | 8.273 | True | 0 | serializable | True | 0 | 166.645 | 14.0 | True | — | completed |
| fixed-5 | balanced | 6 | bnode132 | 8855503 | 6.350 | 8.856 | 14.285 | True | 0 | serializable | True | 0 | 357.002 | 27.8 | True | — | completed |
| fixed-5 | balanced | 10 | bnode132 | 14748197 | 10.353 | 14.669 | 21.612 | False | -9 | — | — | — | 303.093 | 21.2 | False | killed_unknown | indeterminate |
| fixed-5 | read-heavy | 3 | bnode139 | 16819316 | 3.341 | 16.658 | 24.375 | True | 0 | serializable | True | 0 | 416.111 | 43.2 | True | — | completed |
| fixed-5 | read-heavy | 6 | bnode139 | 32754846 | 6.347 | 32.196 | 45.510 | True | 0 | serializable | True | 0 | 864.291 | 85.6 | False | verifier wall > 600 s | completed |
| fixed-5 | read-heavy | 10 | bnode139 | — | — | — | — | False | — | — | — | — | — | — | False | verifier wall > 600 s | not_run |
| fixed-10 | write-heavy | 3 | bnode051 | 2532560 | 3.330 | 2.474 | 5.056 | True | 0 | serializable | True | 0 | 114.098 | 9.7 | True | — | completed |
| fixed-10 | write-heavy | 6 | bnode051 | 5018742 | 6.316 | 4.921 | 8.155 | True | 0 | serializable | True | 0 | 250.556 | 18.8 | True | — | completed |
| fixed-10 | write-heavy | 10 | bnode051 | 8348584 | 10.323 | 8.204 | 12.197 | False | -9 | — | — | — | 3601.485 | 17.9 | False | verifier timeout | indeterminate |
| fixed-10 | balanced | 3 | bnode055 | 4286776 | 3.338 | 4.274 | 8.125 | True | 0 | serializable | True | 0 | 159.191 | 13.5 | True | — | completed |
| fixed-10 | balanced | 6 | bnode055 | 8604257 | 6.363 | 8.521 | 14.316 | True | 0 | serializable | True | 0 | 344.028 | 26.9 | True | — | completed |
| fixed-10 | balanced | 10 | bnode055 | 14230861 | 10.354 | 14.172 | 21.396 | False | -9 | — | — | — | 294.880 | 20.5 | False | killed_unknown | indeterminate |
| fixed-10 | read-heavy | 3 | bnode119 | 15437721 | 3.334 | 15.336 | 23.022 | True | 0 | serializable | True | 0 | 384.936 | 39.6 | True | — | completed |
| fixed-10 | read-heavy | 6 | bnode119 | 30656095 | 6.336 | 30.468 | 42.890 | True | 0 | serializable | True | 0 | 807.805 | 80.2 | False | verifier wall > 600 s | completed |
| fixed-10 | read-heavy | 10 | bnode119 | — | — | — | — | False | — | — | — | — | — | — | False | verifier wall > 600 s | not_run |

commit = bench の commit witness (C 行数え直しと一致)。maxrss = verifier 主 process の `ru_maxrss` (parse worker 16 本の合計ではない)。校正で完走した 12 verdict はすべて `serializable`・certified・anomaly 0。

### 5.2 適格集合と確定 extime (規則は段 4 裁定 §3.2〜3.3、結果を見る前に固定)

- 適格 = bench 完走 ∧ verifier 完走 ∧ `serializable` ∧ certified ∧ anomaly 0 ∧ verifier wall ≤ 600 s。両候補とも **E = {write-heavy {3, 6}、balanced {3, 6}、read-heavy {3}} → 共通部分 {3} → extime = 3 s**。`choose_extime` (07-16 校正器の純関数) に正常完了の昇順 prefix を渡した結果と一致。
- 本走の見込み B̂(3) = Σ_w 8 × (bench + 数え直し + verifier) + Σ_w 8 × 保全 + 6 × F̂ (F̂ = 31.140 s = 段 A の setup+hydrate+build の最大) = **fixed-5 6346.534 s、fixed-10 5998.965 s**、いずれも ≤ 14400 s で段下げなし。
- extime の決定は `summary-A.json` の生成時点 (2026-09-20 00:02:02 JST) で機械的に定まった。段 4 裁定 §7 (追補) はその記録で、file の mtime は 00:04:05 JST、段 B の投入 (request Created) は 00:04:14 JST。**§7 の見出しに書いた「00:05 JST」は親の推定で誤り** (正しくは 00:04:05 の書込み)。§7 追補版は段 B の記録が `ruling_sha256` で束縛しているため本文は訂正せず、ここに erratum として残す。
- 校正の実消費 (別欄、§3.1): dispatch Elapse の和 = fixed-5 6462 S (10868 = 1445 S read-heavy、10870 = 955 S balanced、10871 = 4062 S write-heavy)、fixed-10 6339 S (10873 = 1351 S、10872 = 925 S、10869 = 4063 S)。runner の job wall 和 = 6447.5 / 6324.9 s。校正 + 本走の合計 (dispatch Elapse) = fixed-5 12,778 S (3.55 h)、fixed-10 12,473 S (3.46 h)。

### 5.3 未完走 (indeterminate) — 候補あたり 2 件、trace は保全済み

- **balanced 10 s (両候補、bnode132 / bnode055 の 2 node で再現):** verifier が SIGKILL (rc −9、timeout ではない、wall 303.1 / 294.9 s)。主 process の maxrss は 21.2 / 20.5 GiB、stderr 空。Pegasus gen_S に per-job cgroup は無い (runbook §1) ので node memory (128 GiB) の枯渇と整合するが、証拠は signal と rusage だけなので `killed_unknown` と記録した。read-heavy 6 s (32.8M / 30.7M commit、主 process 85.6 / 80.2 GiB) は完走しているので、commit 数だけでは説明できない (balanced は書込 50% で依存辺が多い可能性があるが、本 wave は原因を確定しない)。
- **write-heavy 10 s (両候補、bnode125 / bnode051):** hard timeout 3600 s で打ち切り。主 process の user CPU 時間 (`ru_utime`) は 520.180 / 522.415 s (user+sys 546.951 / 549.039 s) と、完走した 6 s 走の 816.687 / 824.115 s (user+sys 884.364 / 892.184 s) より少なく、maxrss 17.9 GiB で頭打ち、stderr 空 → 主 process は大半の時間を待っていた (並列 parse の worker 側の停滞が疑われる)。正しさシグナルではなく運用上の未完走。
- read-heavy 10 s は規則により未実走 (6 s が 600 s 超)。
- 07-16 校正器の規則 (timeout = 校正全体の失敗) からの意図的変更: 資源上限は正しさシグナルでないため、未完走を開示付きで記録し完走 prefix から extime を決めた (段 4 裁定 §4.2、D fragment 項 5)。

---

## 6. 本走 (段 B、2026-09-20 00:04 〜 00:43 JST)

### 6.1 job (各 4 反復直列、walltime 03:30:00、extime 3)

| 候補 | workload | job-index | reps | request | node | Started (JST) | Ended (JST) | Elapse S | runner job wall s | setup+hydrate+build s |
|---|---|---|---|---|---|---|---|---|---|---|
| fixed-5 | write-heavy | 1 | 1-4 | 11275.nqsv | bnode001 | 00:04:36 | 00:13:31 | 539 | 534.0 | 30.5 |
| fixed-5 | write-heavy | 2 | 5-8 | 11276.nqsv | bnode017 | 00:06:08 | 00:15:04 | 540 | 535.1 | 30.2 |
| fixed-5 | balanced | 1 | 1-4 | 11268.nqsv | bnode055 | 00:20:40 | 00:33:02 | 746 | 741.6 | 30.6 |
| fixed-5 | balanced | 2 | 5-8 | 11272.nqsv | bnode128 | 00:10:12 | 00:22:46 | 758 | 753.7 | 30.6 |
| fixed-5 | read-heavy | 1 | 1-4 | 11270.nqsv | bnode125 | 00:04:23 | 00:35:13 | 1855 | 1849.6 | 31.1 |
| fixed-5 | read-heavy | 2 | 5-8 | 11274.nqsv | bnode130 | 00:09:56 | 00:41:10 | 1878 | 1874.1 | 31.3 |
| **fixed-5 合計** | | | | | | | | **6316** | **6288.1** | |
| fixed-10 | write-heavy | 1 | 1-4 | 11273.nqsv | bnode129 | 00:04:24 | 00:13:24 | 545 | 540.3 | 30.9 |
| fixed-10 | write-heavy | 2 | 5-8 | 11277.nqsv | bnode132 | 00:11:37 | 00:20:38 | 545 | 540.2 | 30.5 |
| fixed-10 | balanced | 1 | 1-4 | 11271.nqsv | bnode126 | 00:20:33 | 00:32:48 | 739 | 734.3 | 30.4 |
| fixed-10 | balanced | 2 | 5-8 | 11278.nqsv | bnode113 | 00:12:37 | 00:24:47 | 734 | 729.3 | 30.5 |
| fixed-10 | read-heavy | 1 | 1-4 | 11269.nqsv | bnode122 | 00:10:10 | 00:40:05 | 1799 | 1794.5 | 30.9 |
| fixed-10 | read-heavy | 2 | 5-8 | 11279.nqsv | bnode115 | 00:13:36 | 00:43:04 | 1772 | 1767.0 | 30.6 |
| **fixed-10 合計** | | | | | | | | **6134** | **6105.7** | |

「≤ 4 時間/候補」(段 4 裁定 §3.1 = 本走 job の dispatch Elapse の和) は **fixed-5 6316 S (1.75 h)、fixed-10 6134 S (1.70 h)** で充足。校正を足した合計は 12,778 / 12,473 S (別欄、§5.2)。bench 失敗 (attempt-2) は 0 件、verifier 未完走 (`reverify`) は 0 件、単独性検査の拒否は 0 件。

### 6.2 24 枠 (候補 × workload × rep。全 48 行は `verbatim/table-B.md`)

| 候補 | workload | 枠 | commit の範囲 | verifier wall s (最小〜最大、中央値) | maxrss GiB | Σ(bench+count+verifier) s | Σ 保全 s | 判定 |
|---|---|---|---|---|---|---|---|---|
| fixed-5 | write-heavy | 8 | 2,471,532〜2,517,433 | 113.5〜117.3 (114.6) | 9.5〜9.6 | 965.1 | 41.5 | 8/8 serializable・certified・anomaly 0 |
| fixed-5 | balanced | 8 | 4,365,454〜4,464,643 | 160.7〜165.3 (162.9) | 13.7〜14.0 | 1366.3 | 65.8 | 8/8 serializable・certified・anomaly 0 |
| fixed-5 | read-heavy | 8 | 16,456,248〜16,860,602 | 405.6〜416.3 (412.2) | 42.2〜43.3 | 3458.6 | 198.5 | 8/8 serializable・certified・anomaly 0 |
| fixed-10 | write-heavy | 8 | 2,516,870〜2,533,193 | 113.8〜118.4 (115.7) | 9.6〜9.7 | 974.5 | 42.4 | 8/8 serializable・certified・anomaly 0 |
| fixed-10 | balanced | 8 | 4,300,911〜4,345,781 | 157.8〜161.7 (159.3) | 13.5〜13.6 | 1335.5 | 65.0 | 8/8 serializable・certified・anomaly 0 |
| fixed-10 | read-heavy | 8 | 15,688,765〜16,078,316 | 386.5〜398.3 (396.1) | 40.3〜41.3 | 3306.7 | 189.2 | 8/8 serializable・certified・anomaly 0 |

全 48 枠: `bench_attempt_id = 1`、`verify_attempt_id = 1`、rc 0、`verdict = serializable`、`certified = true`、`anomaly_count = 0`、integrity clean (orphan_reads / version_dups / dup_txids / missing_txids / write_version_mismatch / lock_coverage_violations / write_intent_violations / permutation_violations すべて 0)、保全完了、identity 一致。

### 6.3 判定 (段 4 裁定 §4.1 を `summarize` が機械適用)

| 候補 | 判定 | 判定集合 | anomaly | 未完走 (校正、開示) | 未実走 (校正) | extime | 本走実消費 |
|---|---|---|---|---|---|---|---|
| fixed-5 | **pass** | 30 件 (本走 24 + 校正完走 6) | 0 | 2 件 (balanced 10 s、write-heavy 10 s) | 1 (read-heavy 10 s) | 3 s | 6316 S ≤ 14400 S |
| fixed-10 | **pass** | 30 件 | 0 | 2 件 (同上) | 1 | 3 s | 6134 S ≤ 14400 S |

- 最終集計 = runner v2 の `summarize --accept-ruling-sha 2f9d8eb1… --accept-ruling-sha 1ddd2386…` (`run/summary-B-fix1.json`、sha256 `f7248a7f1de6e41d2e7e4a5a9753d6752fc79fc41ae0ba4104a34f1cf9246e37`、generated 2026-09-19T15:51:41Z)。
- **ruling sha の開示 (段 6 fix 1 の理由):** 段 4 裁定 `s4-ruling.md` は「規則 (§1〜§6、§8、§9)」と「段 A 後に親が書く計算結果の追補 (§7)」を 1 file に持つ。段 A の 18 記録は §7 未記入版 (sha256 `2f9d8eb1e6520bb45cbb2eff76ede4286a23b39c29463cc50b18019ae97610cd`) を、段 B の 48 記録は §7 追補版 (`1ddd2386ef1f4558077fffbef4bcab882205f955a5e4c8f9375d01b64cfd9201`) を `ruling_sha256` に持つ。v1 の `summarize` は全記録が 1 値でないと構造誤り (`ruling sha mismatch`) として `undetermined` を返した (`run/summary-B.json`、sha256 `723d8112…`)。親は段 A 版を復元して sha が一致すること (`s4-ruling.stageA.md`)、差分が §7 の 48 行だけであることを実測し、段 6 fix 1 (Codex) で `summarize` に許可 sha の明示 (`--accept-ruling-sha`、repeatable) と段別 sha の開示 (`ruling_sha_by_phase`) を足した。無指定時の挙動と判定規則 (§4.1) は不変、selftest は 42 → 49 件 (混入・許可集合・部分許可の各正例・負例)。判定を親が手で書き換えてはいない。

---

## 7. 限定

1. **1−εⁿ は主張しない。** 「独立反復 n=8 × 3 workload で anomaly ゼロ」は操作的事実であり、ε の定義・数値 seed・乱数列の独立性は記録できない (§4.1)。同じ trace の verifier 再実行は N を増やさない (本 wave では 0 回)。
2. **性能値ではない。** trace-enabled build の commit 数・throughput は診断生値として `result.json` に残るだけで、性能主張・A-2 / T-1998 / A-6 の性能値との比較・候補の優劣に使わない (規律 1)。
3. **判定集合は 30 件 / 候補で、「全走 anomaly ゼロ」ではない。** 校正 10 s の未完走 2 件 (§5.3) は verdict を持たない (anomaly でも pass でもない)。trace は保全済みで、より大きい記憶容量の場があれば後日検証できる。
4. **identity は現行 source に束縛。** fixed-10 は A-2 rr5-fixed10 と同 genome・同数値挙動 (10 µs が選ぶ復号分岐は不変) だが source bytes は改訂 `91a5bfca3` 分だけ異なる (§3)。A-2 / T-1998 / A-6 の certified 記録を昇格も降格もしない (規律 7)。
5. **binary は job (node) ごとに別 build。** 18 job の `binary_sha256` は互いに異なる (node-local build、debug 情報の path 等)。正しさ検証は量を比べないので判定に影響しないが、「同一 binary で 24 反復した」とは書けない。source identity (§3) は候補ごとの 9 job で一致 (候補間では当然異なる)、toolchain (§4.1) は 18 job で同一。
6. **verifier は現行版 (2026-09-02 の並列化後、module sha は §4.2)。** 07-16 の cygnus 校正 (verifier 433.3 / 974.7 s) とは code も環境も違う。数値は併記であって置き換えではない (規律 7)。
7. **未完走の原因は確定していない。** `killed_unknown` は SIGKILL と rusage からの推定であり、OOM の直接証拠 (dmesg 等) は取れていない。write-heavy 10 s の停滞も verifier 内部の段別計時を持たないため機序は特定していない。
8. **S-1 (iv 付属) の「本節へ日付付き追記」は未履行の繰延べ** (§8)。本 wave は S-1 の充足ではない (§2)。
9. **job の予約 walltime に上限保証は無かった。** 段 4 裁定 §8 の予約 (段 A 02:00:00、段 B 03:30:00) は段 3 レンズ B の上限式 (校正 verifier の hard timeout を 1800 s と置いた 6960 s) から採ったが、裁定 §3.2 は校正の hard timeout を 3600 s に変えており、同じ式で再計算すると最悪 8760 s (> 7200 s) になる。runner 内の setup+build 2400 s は build 後の事後検査で、保全に timeout は無い。実測の最大は dispatch Elapse 4063 S / runner の job wall 4057.876 s (いずれも校正 fixed-10 write-heavy、request 10869) で予約内に収まったが、これは結果であって保証ではない。段 3 B2 は「会計範囲」だけが処置済みで「上限式」は未処置 (§10 A7)。

---

## 8. 記録先と繰延べ

`docs/phase3-main-experiment.md` は編集していない。同文書は `output/s1-freeze/known_axes_freeze.json` の source sha256 として凍結され、`s1_known_axes_freeze.verify_document` が現物と照合する — 親が 1 行追記を `source_resolver` で模擬したところ historical の両モードで `FreezeError: source sha256 不一致` になった (2026-09-19)。凍結文書の raw sha は `t080_freeze_migration.KNOWN_AXES_RAW_SHA256` に pin され、`IZANAGI_FREEZE_HOLD` の解除はユーザー明示命令だけである。したがって (iv 付属) の「確定値は本節へ日付付き追記」は本 wave では**未履行の繰延べ**とし、校正確定値 (両候補 extime 3 s、2026-09-19〜20、§5) は `{{D:verify-phase-adopted-backoff-authorization}}`、本 README、results 系列稿 `docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md` に日付付きで置く。phase doc への追記は凍結束縛の解除 (ユーザー明示命令) または source 束縛の移設の裁定の後に別 wave で行う。

---

## 9. 一次資料

すべて job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/` 配下 (repo には本 README と `verbatim/` の逐語だけを入れる)。

| 物 | path | 同定 |
|---|---|---|
| runner v1 (走行) | `probe/verify_phase_runner.v1-run.py` | 1301 行、sha256 `91bbf85d594085a4900bb2e9272bd455cef18e83c258ccfe5828594c0afd82a7` |
| runner v2 (最終集計) | `probe/verify_phase_runner.py` | 1384 行、sha256 `c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5` |
| 段 4 裁定 (段 A 版 / 追補版) | `s4-ruling.stageA.md` / `s4-ruling.md` | sha256 `2f9d8eb1e6520bb45cbb2eff76ede4286a23b39c29463cc50b18019ae97610cd` / `1ddd2386ef1f4558077fffbef4bcab882205f955a5e4c8f9375d01b64cfd9201` |
| 校正の記録 | `run/calib/<c>-<w>/{job.json,calib.json,extime-<e>/{result.json,bench.stdout,bench.stderr,verifier.json,verifier.stderr,preservation.json,trace/}}` | 6 job、18 記録 (実走 16、未実走 2 は result.json のみ) |
| 本走の記録 | `run/verify/<c>-<w>-<k>/{job.json,rep-<i>/attempt-1/{同上}}` | 12 job、48 走 |
| dispatch log / receipt | `run/A-<c>-<w>.log`、`run/B-<c>-<w>-<k>.log`、`run/*.wait-receipt.json`、各 submit-tree の `output/pegasus-dispatch/` | request 10868〜10873、11268〜11279 |
| 集計 | `run/summary-A.json` (sha256 `0ed068a6…`)、`run/summary-B.json` (`723d8112…`、v1、undetermined)、`run/summary-B-fix1.json` (`f7248a7f…`、v2、pass) と各 `.md`、`run/table-B.md` | |
| 子の逐語 | `codex/s2-plan.md`、`codex/s3-consult-A.md`、`codex/s3-consult-B.md`、`codex/s5-author.md`、`codex/s6-fix-1.md`、`codex/prompt-*.md` | repo 内は `verbatim/` |
| 裁定控え | `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-19-verify-phase-adopted-backoff-authorization.md` | land 後に消してよい |

`verbatim/` の逐語は `git diff --check` の行末空白抵触を避けるため、**行末の空白 (空白・タブ) だけを除去する可逆最小正規化** (可視文字不変) を掛けた。原本は job dir (`codex/*.md`、`s1-brief.md`、`s4-ruling*.md`、`refs/identity-precheck.md`、`run/table-B.md`、runner は `probe/`) にそのまま残り、復元は原本の再複写。`runner-source.md` は job dir の `probe/verify_phase_runner.py` (v2) と v1→v2 の unified diff を fenced block に入れた生成物で、除去した 6 行は v2 source の空白行の行末空白 (v2 の sha256 `c960093d…` は `probe/` の原本で照合)。

| file | 原文 bytes | 原文 sha256 | 正規化後 bytes | 正規化後 sha256 | 除去した行数 |
|---|---|---|---|---|---|
| `identity-precheck.md` | 3943 | `f931ccb3e17f9223…` | 3943 | 同左 | 0 |
| `runner-source.md` | 86097 | `2cd4050f9e675b18…` | 86091 | `167d113a8a4b5be7…` | 6 |
| `s1-brief.md` | 9442 | `b3b571d7084016eb…` | 9442 | 同左 | 0 |
| `s2-plan.md` | 24422 | `6662c1b7252459dc…` | 24414 | `2cfb6036fd35769d…` | 4 |
| `s3-consult-A.md` | 13413 | `120ffef78ad7d780…` | 13269 | `843fcf483e22748f…` | 49 |
| `s3-consult-B.md` | 15933 | `989a109c8ee37e42…` | 15793 | `3f12004876dba5ff…` | 56 |
| `s4-ruling.md` | 23707 | `1ddd2386ef1f4558…` | 23707 | 同左 | 0 |
| `s4-ruling.stageA.md` | 17926 | `2f9d8eb1e6520bb4…` | 17926 | 同左 | 0 |
| `s5-author.md` | 1265 | `8f56e4b645e40ae9…` | 1265 | 同左 | 0 |
| `s6-fix-1.md` | 2213 | `482214748c6112e7…` | 2213 | 同左 | 0 |
| `s6-focus.md` | 5926 | `41d7ba6f8b7880b8…` | 5920 | `22c5896d2be18ef9…` | 3 |
| `s6-focus-2.md` | 4801 | `e772b79e3ec5a52f…` | 4795 | `e53d2b92d2cd6b01…` | 3 |
| `s6-review-A.md` | 11392 | `2cf40b733bc6c632…` | 11370 | `279b7f553e646d99…` | 11 |
| `s6-review-B.md` | 7277 | `ce0f1ab7d0505615…` | 7261 | `5546772b3a6dcf20…` | 8 |
| `table-B.md` | 8660 | `5de5d069fd4de757…` | 8660 | 同左 | 0 |

---

## 10. 段 6 の独立レビュー

段 6 は read-only codex (`gpt-6-astra` / medium) の 2 本 — A = 過剰・削除・測定妥当性・fix の正当性、B = 整合・数値の独立検算 — を並列に行った (逐語は `verbatim/s6-review-A.md`、`verbatim/s6-review-B.md`)。両方 **NO-GO** (A: must-fix 1、should 2、nit 3。B: must-fix 3、should 2)。観測値の訂正・再測定・判定の変更を要する所見は 0 件で、両レビューとも校正 18 記録・本走 48 枠・判定集合 30 件・pass・hash・保全量が原記録と一致することを独立に確認した。親は全所見を real と裁定し (refuted 0)、docs を直接 fix した。段 4 裁定 `s4-ruling.md` は段 A / 段 B の記録が `ruling_sha256` で束縛しているため本文を訂正せず、本節に erratum として書く。

| # | 所見 (出所) | 重み | 裁定 | 対応 |
|---|---|---|---|---|
| A1 | 段 6 fix 1 (ruling sha 許可集合) は結果を見た判定器の緩和ではない — `decide` の変更は sha 検査行のみ、判定条件 (重複・欠番・identity・判定集合・anomaly・24 枠) は不変、2 版の差分は §7 だけ | 攻撃不成立 | — | 変更なし (§6.3 の記述を維持) |
| A2 | 24 枠・判定集合 30・未完走 2・未実走 1 の独立照合で不整合なし | 攻撃不成立 | — | 変更なし |
| A3 | 校正規則 (適格集合・prefix・not_run・timeout / kill の区別・見込み) は規則どおり | 攻撃不成立 | — | 変更なし |
| A4 | D fragment・worklog の「資源上限で検証相が恒久に止まる」は `killed_unknown`・原因未確定の記録を超える過大。B-8 注記の見出しは「関連する追加検証が得られた」が本文の留保と整合 | should | real | D fragment 項 5 の理由・却下案と worklog fragment を「旧規則では今回の校正は未確定になり本走を投入できない」へ訂正。paper-story README の B-8 注記の見出しを訂正 |
| A5 | 「source identity と toolchain は 18 job で同一」は文字どおりには誤り (候補間で digest は異なる) | should | real | §7 項 5 を「source identity は候補ごとの 9 job で一致、toolchain は 18 job で同一」へ訂正 |
| A6 | results §0.3 と §4 の限定列挙の重複、D fragment の「唯一の形」、§5.3 の worker 停滞仮説は短縮可。必須項目の欠落は無し (ただし事前登録 §8 全項目との完全照合は未実施) | nit | real (nit、部分適用) | D fragment の「唯一の形」を削除。results §0.3 (書かないもの) と §4 (限定) の二段構成は同系列の先例 (T-1998 稿 §0.3 / §4) と同形式なので**意図的に維持**し、§5.3 の停滞仮説も 1 文で原因未確定と明記しているので維持。削減提案は部分適用に留めた (親裁定) |
| A7 | **段 3 B2 (walltime 上限式) は処置済みと言えない** — 予約 7200 s は hard timeout 1800 s 前提の上限式から採られ、裁定 §3.2 の 3600 s で再計算すると最悪 8760 s。runner 内の 2400 s は事後検査、保全に timeout なし。今回の実測 (最大 dispatch Elapse 4063 S、runner job wall 4057.876 s) は予約内 | **must-fix** | real | §7 に限定 9 を追加、§10 本表と worklog fragment に「上限保証は未実装、実測は予約内、B2 は会計範囲のみ処置」と記録。裁定 §0 の「B2 採用・反映済み」は erratum (本文は sha 束縛のため不変)。pass の取消し・再測定は不要 (所見自身の結論) |
| A8 | 規律 6 / 1 / 7 違反は指定範囲で確認できない | 攻撃不成立 | — | 変更なし |
| B1 | **CPU 時間の転記誤り**: §5.3 の 6 s 走「822 s」は `ru_utime` 816.687 s が正。定義 (user CPU) を明記 | **must-fix** | real | §5.3 を `ru_utime` 520.180 / 522.415 s (10 s) と 816.687 / 824.115 s (6 s)、user+sys 546.951 / 549.039 s と 884.364 / 892.184 s に訂正 |
| B2 | **時刻の精度と時系列**: results の「裁定 22:20」は原文「22:2x」から確定できない。「00:05 確定」は段 B 投入 00:04:14 より後。計算結果は `summary-A.json` 生成 00:02:02 に存在。段 A の「00:02」は job 終了 (00:01:24) でなく集計時刻 | **must-fix** | real | README §5 見出し・§5.2 に投入 22:46 / 最初の開始 22:49:38 / 最後の終了 00:01:24 / 集計 00:02:02 / §7 追補の mtime 00:04:05 / 段 B 投入 00:04:14 を明記し、§7 見出しの「00:05」を erratum として記録。results 稿 §2・§3.1 も同様に訂正 (裁定の作成時刻は裁定文書の自己記載「22:2x JST」だけを書き、段 A 版 file の mtime は追補で上書きされて一次資料に残っていないので書かない) |
| B3 | **18 / 66 を実走数として扱わない**: 校正 18 記録 = 実走 16 + 未実走 2、全 66 記録 = 実走 64 | **must-fix** | real | README 冒頭・§4.3・§5.1・§9、results §0.1、paper-story README 行を「記録 / 実走」の区別で訂正 |
| B4 | 校正 + 本走の合計消費 (12,778 / 12,473 S) を追記 (裁定 §3.1 が和も報告と定める) | should | real | README §5.2・§6.1、results §3.1・§3.3 に追記 |
| B5 | selftest の PASS 件数・07-16 の 433.3 / 974.7 s・起点 `a99425b66`・背景 job 識別子は指定一次資料だけでは独立確認できない | should | real (出所の限定) | **独立照合されていない事項として残す**: (a) 親の login selftest (v1 42/42、v2 49/49) の stdout は file に保存しておらず、再現は job dir で `python3.10 -B probe/verify_phase_runner.py selftest` (author / fix 子の実走は `codex/artifacts/**/attempt-0001.output.md` の報告文のみ)。(b) 07-16 の 433.3 / 974.7 s は `docs/phase3-main-experiment.md` (iv 付属の校正確定追記) からの転記で本 wave では再測していない。(c) 起点 `a99425b66` は wave worktree の作成時 HEAD (handoff の記録)、`657e1e5a7` は commit 履歴で照合可。(d) 背景 job 識別子 fa9409aa は session の job dir 名 (`/home/SFC/tanab/.claude/jobs/fa9409aa/`) が出所。数値自体は変えない |

焦点再レビュー 1 巡目 (`verbatim/s6-focus.md`) は NO-GO (closed 7 / partial 5 / regressed 1): paper-story README への訂正が未反映 (親の編集 script が途中停止)、「最大 job wall 4063 S」は dispatch Elapse で runner の job wall は 4057.876 s (計時範囲の混同)、「file の mtime 22:20」は一次資料に無い、B5 の未照合事項の明記不足、A6 の部分適用。いずれも本表の対応欄のとおり訂正した。2 巡目 (`verbatim/s6-focus-2.md`) は **GO** (残件 6 件 closed、1 巡目 closed 7 件に退行なし、計 13 件 closed、文書間の不整合なし。A7 の runner job wall 4057.876 s は `job_wall_s` = 終了〜開始の monotonic 差で、`stage_wall_s` の和 4057.564 s とは 0.312 s 異なる、と 2 巡目が補足)。
