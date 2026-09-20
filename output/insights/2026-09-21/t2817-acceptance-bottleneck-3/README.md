# [T-2817] 受入律速の再同定 (第 3 回) と collection 差の分解診断 — pairing 後の最遅 shard の wall は「L の worker」でなく「ledger 未収載の active_v2 系 node を後方 rank で直列に抱えた別 worker」で決まり、受入 `pre` 61 秒と温 collection の差 約 45 秒は shard plugin の `pytest_collection_modifyitems` (48 worker 同時の `Path.resolve()`、kernel 時間) で、早期 memo prewarm (44〜54 秒) はその窓に並走して隠れている (2026-09-21)

wave `dev-wave-t2817-acceptance-bottleneck-3`。依頼の逐語は `verbatim/T-2817-origin.md`。対象 = [T-2817] と持ち越し [T-2273] / [T-2444] / [T-2495] / [T-2560] (D2148 項 6、D1936 項 35)。
一言でいうと「pairing 既定 on 後の実受入の最遅 shard が何で決まっているかを、保存済み受入成果物 (21 session) と現行 tip の計算ノード job 2 本 (段階載せ collection 診断 = Job A / A 条件 replica の観測 wrapper = Job B) と同 code の参照受入 1 走で取り直した」診断で、**改善の実装は 1 行もしていない** (D1936 項 35)。probe 7 file は Codex author の子 branch にあり、repo には逐語 `.txt` だけを置く。

## 結論 (最初に読む)

計測 tip `2afb39768` (投入直前の local main、fresh worktree を ff-only で揃えた)。Job A = bnode009、request 14108.nqsv、Elapse 442 秒、9 cell、単独 (`others=0`、`stale_pytest=0`、全 cell)。Job B = bnode008、request 14038.nqsv、Elapse 425 秒 (smoke 57 秒 + A 走 355 秒)、単独。数値は `job-out-aggregate.md` / `.json` (Job A の機械集計)、`job-out-b/analysis-A.md` / `.json` (Job B の機械集計)、`raw/` (生記録) にある。

1. **律速の再同定 (第 3 回、依頼 (1)):** pairing 後の shard-0 の wall は、最長 node L の worker ではなく**別の worker** で決まる。Job B (現行 tip、A 条件 1 走) では W 353.3 = O_max 281.0 (gw40) + F 72.3。gw40 の列は「小 item 26 個 (rank 40〜422、計 54.5 秒) → `test_t080_active_v2_delegation_accepts_full_receipt` (rank 423、180.6 秒。うち共有 base の**構築** 145.8 = copy 配置 64.2 + 直下 git 12.4 + 発行 subprocess 69.1) → `test_t080_failed_launch_preserves_receipt_refusal` (rank 424、46.2 秒)」。L (216.0、gw5、rank 5) の worker は相方 0.0 で、L 自身の内訳は「他 worker の base 構築を flock で待つ 182.0 + base→test copytree 4.6 + verify 5 回 27.1 + その他 2.3」。保存済み受入 21 session (§2b) でも最大占有 worker は 21/21 で L の worker と別、`O_max − L` の中央値 62.7 秒 (Job B は 65.0)。
2. **機構 (仮説から観測へ):** rank 423〜424 の node は ledger (`acceptance_duration_ledger.json`、2026-09-17 再生成) に**未収載** (T-2724 が 2026-09-18 に追加した 8 node) で、conftest の並び替えは未収載 unit に「既知 cost の 96 番目」(Job A の shard-0 選択集合では 9.6〜13 秒) を与えて後方に置く。動的配布でそれらは t ≈ 55 秒に空いた worker へ載り、そこから active_v2 系 key の base を建てる (145.8 秒) ので、L の worker (t = 0 から 216 秒) より遅く終わる。**「未収載 → 後方 rank → 遅い開始 → 別 worker の直列」は Job B の timeline で観測した** (1 走)。ledger の未収載そのものは D2107 が「次の add-only wave が再登録する」と書いた型。
3. **collection 差の分解 (依頼 (2)):** 同 job・同 node・同 checkout で段階載せした結果 (`pre_junit` = worker の `pytest_collection_finish` 出口の最大 − junit timestamp、受入 `pre` と同定義。a / b の 2 走):
   - S0 (独立 48 process `--collect-only`): cohort wall 16.9 / 17.3 秒 (process median 16.7 / 17.1)。
   - S1 (xdist `-n 48 --dist loadgroup --no-loadscope-reorder`、shard plugin なし): **`pre_junit` 15.0 / 14.9 秒** (worker の collect 12.0 / 12.1 + modify 0.43 / 0.44 + spawn 0.25)。controller の同期 memo prewarm (`xdist_node_collection_finished`、43.3 / 30.3 秒) は worker の時刻に入らず、process wall (65.5 / 52.4 秒) にだけ入る。
   - S2 (S1 + `-p tools.acceptance_shards` + shard spec 0/3): **`pre_junit` 60.4 / 61.4 秒**。増分はほぼ全部 **modify 区間 (最後の `pytest_itemcollected` → `pytest_collection_finish` 入口) 44.1〜46.2 秒 (worker median 45.7 / 45.6)** に入り、worker の memo 待ち (`cf_exit − cf_entry`) は 0.02 秒。sys 時間が 80 → 2108 秒 (48 worker × 約 42 秒の kernel 時間)、Lustre `md_stats:intent_lock` が 5.2 M → 60.9 M。shard plugin の `pytest_collection_modifyitems` (trylast) は全 item (26,407) に `Path(item.path).resolve()` を掛けて正規化する (`tools/acceptance_shards.py` `_canonical_item` / `records_from_items`) ので、48 worker 同時の path 解決が Lustre 上で kernel 時間になる、と読める (機構の同定は code 読みと sys 時間・Lustre op 数の対応から。plugin 内の関数別計時はしていない)。早期 memo prewarm (44.4 / 53.9 秒) は controller で並走し、worker が collection_finish に着く前に終わっている。
   - S3 (S2 から `--no-loadscope-reorder` を外す = ledger 読込 24,379 entry + 配送 + 並び替え + pairing、受入 shard の argv 形): **`pre_junit` 61.3 / 61.6 秒**。S2 との差 0.9 / 0.2 秒。
   - 段差 (a / b / 平均): Δ10 = −1.9 / −2.3 / −2.1 秒 (xdist 起動 + 同時 collection + controller 通知; 独立 48 process の cohort より短い)、**Δ21 = +45.4 / +46.4 / +45.9 秒** (shard plugin + memo 同期→早期の切替の複合差、実体は上記の modify 区間)、Δ32 = +0.9 / +0.2 / +0.6 秒。
   - **同 code の実受入との整合:** Job B (replica、同 tip) の `pre` 61.9 秒、参照受入 (§3.3、shard-0 は Job A と同じ bnode009) の shard-0 `pre` 61.8 秒に対し、S3 の `pre_junit` 平均 61.45 秒 (差 −0.31 秒、便宜的閾値 10 秒以内、機械判定 `reproduces_reference=true`) → **S3 は受入 `pre` を同 code・同 node 条件で再現した。** したがって「受入 `pre` 61 秒 = collection 約 12〜15 秒 + shard plugin の modifyitems 約 45 秒 + 起動・通知の数秒」を受入 `pre` の内訳の**候補**として提示する (段 4 §4 の条件を満たす)。T-2243 §5 (d) の「約 43 秒」はこれで閉じる。削減可能量は書かない。
4. **固定費 F の構造 (依頼 (1) の「固定費」):** Job B で F = 72.3 = pre 61.9 + 終了後 10.0 + 残差 0.3。21 session の中央値も F 77.3 = pre 67.0 + post 10.0 + 残差 0.1〜4.5 (§2b)。`post` 10.0 秒は shard-0 だけに一定で現れる (shard-1/2 は 3〜4 秒)。原因は同定していない (候補は §8)。
5. **効果量の見込み (§5、実装しない):** (a) ledger 未収載 8 node への実測中央値付与を固定所要 list-scheduling で model 化すると O_max_model は 253.3 → 233.7 (= L)、差 19.5 秒。**model 値であり実 wall の予測ではない** (junit 中央値は builder / waiter の二峰を潰すので観測の `O_max − L` 62.7〜65.0 より小さく出る)。(b) `pre` は「worker 側 = collection 12 + plugin modify 45」と「controller 側 = 早期 memo 44〜54」の**ほぼ同じ長さの 2 本の並走**で決まるので、片方だけを縮めても `pre` はもう片方の長さで止まる (構造の記述であり数値の見込みではない)。memo prewarm は D2185 で現行維持。

## 1. 何を測ったか

### 1.1 Job A — 段階載せ collection 診断 (`raw/job-out/`)

- 投入: `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:40:00 --queue-wait-timeout 5400 --overall-grace 5400 -- bash <wave dir>/probe/t2817_collection_stage_probe.sh` (launcher `verbatim/run-probe-a.sh.txt`、dispatch log `verbatim/run-probe-a.log`)。**投入元は同 SHA (`2afb39768`) の別 worktree `dev-wave-t2817-joba`** — 同一 worktree からの dispatch は直列で、Job B の pending orphan hold に当たり最初の投入が `orphan-hold` (rc=16、子は起動せず、`verbatim/run-probe-a.attempt0-orphanhold.log`) になったため。cwd は dispatcher が投入元 worktree に固定 (`WAVE_ROOT=$(pwd -P)`)。01:53 投入、02:00:01 RUN、02:07:19 終了 (JST)。
- 共通環境: `PYTHONDONTWRITEBYTECODE=1`、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、`PYTHONPATH=<probe dir>`、`LC_ALL=C` + `PYTHONUTF8=1`、`TMPDIR` は cell ごとに node-local (`/scr`)、`unset PYTEST_ADDOPTS PYTEST_XDIST_TESTRUNUID IZANAGI_TASK_RUN_SIDECAR PYTHONPYCACHEPREFIX IZANAGI_TEST_RUNNER_EXCLUSIONS_V1 IZANAGI_ACCEPTANCE_SHARDS ...`。python は `python3.10`、pytest 9.1.1、xdist 3.8.0。pyc は投入前に login で `python3 tools/run_tests.py orchestrator/tests --collect-only -q -p no:cacheprovider` を 1 回走らせて温めた (778 pyc、pytest rewrite 367〜369、`verbatim/pyc-warm-joba.times`)。job 前後で pyc 数は不変 (778 / 778)。
- cell と argv (順序どおり。`<abs>` = 投入元 worktree):
  - `warm`: 1 process `python3.10 -m pytest <abs>/orchestrator/tests --collect-only -q -p no:cacheprovider` (page cache の温め、参照列)。
  - `S0-{a,b}`: 上と同じ command を 48 本同時。共通起点 `cohort_start` と各 process の start / end epoch。
  - `S1-{a,b}`: `python3.10 -m pytest <abs>/orchestrator/tests -n 48 --dist loadgroup --no-loadscope-reorder --junitxml=<cell>/junit.xml -p t2817_probe_plugin -p no:cacheprovider -q`、env `T2817_PROBE_COLLECT_ONLY=1`。
  - `S2-{a,b}`: S1 + `-p tools.acceptance_shards -p no:cacheprovider -p t2817_probe_plugin` (受入と同じ順) + env `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1={"session_root":"<cell>/session","shard_count":3,"shard_index":0}`。
  - `S3-{a,b}`: S2 から `--no-loadscope-reorder` を外す (受入 shard 子の argv 形 `python3.10 -m pytest <abs>/orchestrator/tests -n 48 --dist loadgroup --junitxml=… -p tools.acceptance_shards -p no:cacheprovider` に probe plugin を足しただけ。恒久除外は現在 0 件)。
- 「collection だけで test を実行しない」形: probe plugin が `pytest_xdist_make_scheduler` (tryfirst) で実 `LoadGroupScheduling` instance を作り、その `schedule` だけを差し替える。差し替え先は元の前段 (collection 完了の assert → 再呼出しなら return → `_check_nodes_have_same_collection()` と失敗通知 → `collection` 設定) を保ち、workqueue の構築と初期配布だけを省く。deselect しないので conftest の hold 完全性検査 (worker 側・controller 側) は完全 collection のまま通り、`type(sched) is LoadGroupScheduling` も保たれる (`IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"loadgroup"}` が全 xdist cell で出た)。全 xdist cell で `no tests ran`、rc 0、`collection_mismatch=false`、`complete=true` (48 worker 全部の payload を回収)。
- 計時点 (probe plugin、`raw/job-out/<cell>/probe.json`): worker = `t_import` / `pytest_configure` / `pytest_sessionstart` / `pytest_collection` wrapper の入口・出口 / 最初と最後の `pytest_itemcollected` / `pytest_collection_finish` wrapper の入口 (`cf_entry`、conftest の memo 待ちの前) と出口 (`cf_exit`) / `pytest_sessionfinish`、shard plugin の `collection_finished_epoch_s` (S2/S3)、`workerinput` の key 名と ledger payload の有無。controller = `pytest_sessionstart` / `pytest_configure_node` / `pytest_xdist_node_collection_finished` の入口・出口 (node ごと) / 全 node 登録完了 / 最初の `pytest_testnodedown` / `pytest_sessionfinish`、config 事実 (`ledger_should_load`、`ledger_entries`、shard spec・早期 memo 属性の有無)。JUnit の起点は `--junitxml` の testsuite `timestamp`。
- lever の検証: S1/S2 (`--no-loadscope-reorder`) は controller `ledger_should_load=false`・`ledger_entries=0`・worker に ledger payload なし、S3 は `true`・`24379`・payload あり (`raw/job-out/S*/probe.json` の `config`)。login の生死確認 (narrowed 1 file、`-n 2`) でも同じ (`verbatim/smoke-a2/`)。
- 各 cell の前後に単独性 (`others=0`、`stale_pytest=0`)、loadavg、MemAvailable、Lustre client stats (`/proc/fs/lustre/llite/*/stats`、`mdc/*/md_stats`)。全 cell で `others=0`、`stale_pytest=0`。

### 1.2 Job B — 現行 tip の A 条件 replica 1 走 + 観測 wrapper (`raw/job-out-b/`)

- 投入: 同 dispatcher (`--walltime 00:50:00`) で `python3.10 <probe>/t2817_replica_runner.py run --repo-root <wave 木> --probe-dir <probe> --out-root <job-out-b> --job-tag t2817-b1` (launcher `verbatim/run-probe-b.sh.txt`、dispatch log `verbatim/run-probe-b.log`)。01:40 投入、01:57:18 RUN (PRR 17 分)、02:04:19 終了。runner は hostname `bnode` 防壁、clean 検査 (`git status --porcelain` 0 行)、TMPDIR node-local。
- smoke (先に): `python3.10 tools/run_tests.py orchestrator/tests/test_s8b_oracle_driver.py -k shared_base_builds_real_builder_once_across_processes -n 2 --dist loadgroup -p no:cacheprovider -p t2817_replica_plugin` → rc 0、57 秒、build span 1 件 (`raw/job-out-b/smoke/`)。
- A 走 (1 回): `python3.10 tools/run_tests.py orchestrator/tests -n 48 --dist loadgroup --junitxml=<session>/shard-0/junit.xml -p tools.acceptance_shards -p no:cacheprovider -p t2817_replica_plugin`、SPEC env = shard 0/3、session = `acceptance_shards.create_session(repo, 3)` (受入共有 root `/work/1/SFC/tanab/.izanagi-acceptance-shards/69dcbd57434a3a0c176c98f0f222a969`、**replica であり受入ではない。受入成果物の読み取りではこの session を除外する**)。4063 passed / 53 skipped / 0 failed、W (JUnit) 353.3 秒、rc 0。conftest・shard plugin・pairing はそのまま (受理集合・順序に触れない)。
- 観測 wrapper (DW-O14 の「実物へ委譲する観測 wrapper」): 対象 module が sys.modules に現れた後に、`_T080SharedBases.get`、`_t080_stub_free_e2e_repo` (helper)、`_build_t080_stub_free_e2e_repo` (builder)、`_copy_git_visible_output` / `_copy_t080_migration_basis_file` / `_copy_t080_basis_file` (copy)、`shutil.copytree` (builder 直下 = copy、helper 直下 = base_copy)、`_run_git` (git)、`migration.inspect_receipt_history` (history)、発行子 `subprocess.run([sys.executable, "-I", "-B", "-c", …])` (issue)、`fcntl.flock(LOCK_EX)` (key_wait)、`migration.verify_receipt` (verify) を、同じ引数を 1 回渡し返り値と例外を保存する wrapper で包む。key は wrapper が受け取る引数の 5 要素 tuple を観測値として記録 (KEYS を固定しない)。T-2786 前提との対応表は `verbatim/s5-author-b-out.md`。record-error 0 件、span 例外 5 件 (test 本体が意図的に投げる例外の透過、`analysis-A.json` の `span_exceptions`)。

### 1.3 参照受入 — 同 code の実受入 1 走

`tools/dev_wave_wait.py acceptance` (門番: 他 wave の受入 leader ≤ 1 ∧ 1 分 load ≤ 60、`verbatim/run-acceptance-gated.sh.txt`、chain log `verbatim/acceptance-ref.chain.log`) で、README commit の前に 1 走 (02:12〜02:23 JST、child-green、受領証は job dir)。tested tip = `9ad14946e` (post-claim merge で main `b880449bb` を取り込んだ merge commit。`2afb39768` との差は docs のみ、`orchestrator/` `tools/` の diff 0 行)。結果は §3.3。

## 2. 単独性と環境の記録

- Job A: `raw/job-out/env.txt` の逐語 (要点): bnode009、kernel 5.15.0-173-generic、nproc 48、Mem 124 GiB (available 118)、`/scr` は `/dev/md0` xfs 5.4 TB、投入元 worktree は Lustre、python 3.10.12、pytest 9.1.1、xdist 3.8.0、HEAD `2afb3976822dc0e3d8591c139f6ab607278b9276`、`git status --porcelain` 0 行、cpuset `0-47`、job 前 loadavg 0.55。各 cell の直前に `others=0`、`stale_pytest=0` (`raw/job-out/<cell>/cell.txt`)。job 中の loadavg (1 分) は自分の走行で最大 50.96 (S2-b 後)。
- Job B: `raw/job-out-b/env-before.json`: bnode008、HEAD 同上、clean、`others=0`、`stale_pytest=0`、TMPDIR 残骸 0、loadavg 0.44。A 走の前後も `others=0`。
- Job A と Job B は別 node で並行 (runbook §7.5。共有する path・lock・観測対象なし: Job A は投入元 worktree を読むだけ、Job B は replica session を受入共有 root に作る)。

## 2b. brief 前の前提実測 — 保存済み受入成果物 (pairing property あり 21 session) の shard 層 (login の read-only 観測、2026-09-21 00:5x JST)

一次資料は repo 外の受入成果物 `/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/` の直近 60 session (読み取り script は `verbatim/read_shards_v1.py.txt` / `read_shards_v2.py.txt` / `read_shards_v3.py.txt`、出力は `verbatim/shards-recent-v1.json` / `shard0-pairing-v2.json` / `t2724-nodes-v3.json`。Job B の replica session `69dcbd57…` はこの観測の後に作られたので含まれない)。**母集団は「保存資料中で junit に pairing property (`izanagi_acceptance_pairing_v1_*`) がある 21 session」であり、T-2766 の opt-in 期間 (2026-09-20 14:47〜18:11) の B 走を含み、tip は同一でなく、投入元 worktree と SHA は照合していない** (段 3 所見 8)。「既定 on 後の同条件群」とは言わない。量の定義: W = junit testsuite `time`、`pre` = shard plugin の `collection_finished_epoch_s` − junit `timestamp`、O = `worker_occupancy.duration_s` (**report duration の和**であり worker の実時間ではない)、L = 最長 testcase の `time`、`P_L = O_L − L` (L の worker の相方)、`post` = (timestamp + W) − 最後の test 終了、memo = stderr の `IZANAGI_MEMO_PREWARM_V1` の `receipt_memo_s`。

- N1. 最遅 shard は 21/21 で shard-0。shard-0 の W は中央値 398.6 秒 (349.6〜648.2)。最長 node L は 21/21 で `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[...]` (中央値 233.7 秒、215.3〜405.6)。
- N2. **L の worker の相方 `P_L` は 21/21 で 0.0 秒。最大占有 worker は 21/21 で L の worker と別**で、その item 列は session ごとに異なる (例: `b292af15` = active_v2_delegation 184.1 + floor preflight 50.2 + failed_launch 45.8; `e637a58c` = failed_launch 194.8 + floor preflight 48.2 + delegated_campaign 36.9; `29430742` = v1_gate 324.6 + active_v2_preserves 153.1 + codex_ab 40.5)。各走の `O_max − L` の中央値は 62.7 秒 (55.0〜170.0)、中央値どうしの差 (327.3 − 233.7) は 93.5 秒 (段 3 所見 7)。
- N3. 最大占有 worker に乗る `test_s8b_oracle_driver.py` の node (`test_t080_active_v2_delegation_accepts_full_receipt`、`test_t080_active_v2_preserves_nonlayer2_receipt_refusal`、`test_t080_delegated_campaign_start_*` 3 node、`test_t080_failed_launch_preserves_receipt_refusal`、`test_v1_gate_does_not_delegate_with_active_v2`、`test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity`) は、junit の pairing rank property が 21 session 中 19 で 422〜430 (2 session で 374〜379)。これらは ledger `orchestrator/tests/acceptance_duration_ledger.json` (最終再生成 2026-09-17 `363e79b10`、[T-2236] / D2107) に**未収載**で (T-2724 で 2026-09-18 に追加)、conftest `_reorder_acceptance_items_by_duration` は未収載 unit に「既知 cost の `_ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS` (= 96) 番目」を既定 cost として与える。shard-0 の選択集合と ledger で cost 順だけを再現する (`verbatim/rank_replay_v1.py.txt`) と 4116 unit 中 334 unit が未収載。**この再現は cardinality 順・partner 挿入・real-repo suffix・動的配布を再現しておらず、rank の説明にはならない** (段 3 所見 6。Job B の timeline が実配置を観測した)。実所要 (`verbatim/t2724-nodes-v3.json`、21 session の中央値 / 最小 / 最大): active_v2_delegation 193.5 / 179.9 / 333.3、active_v2_preserves 185.9 / 144.4 / 334.4、delegated_campaign[missing] 182.0 / 36.2 / 319.2、rejects_late_hit 188.3 / 40.1 / 337.8、delegated_campaign[changed] 36.9 / 34.8 / 331.3、failed_launch 46.2 / 45.2 / 278.8、v1_gate 39.2 / 38.0 / 337.6 — session ごとに二峰で、active_v2 系 key の base を建てる側が 180〜335 秒、後から使う側が 37〜46 秒 (Job B で builder = `active_v2_delegation` 180.6 秒、後続 `failed_launch` 46.2 秒を観測)。
- N4. shard-0 の固定費 `F = W − O_max` は中央値 77.3 秒 (70.7〜134.3)。各走で `F = pre + post + 残差` と閉じると `pre` は中央値 67.0 (59.9〜123.9)、`post` は 21/21 で 10.0〜10.1 秒 (shard-1/2 は約 3〜4 秒)、残差 0.1〜4.5 秒。`pre` のうち早期 receipt memo prewarm (`receipt_memo_s`) は中央値 58.2 秒 (45.5〜89.5)、`pre − receipt_memo_s` は shard-0 21 件で中央値 4.6 秒 (0.7〜83.1) — **重複実行 (worker の collection と controller の memo 解決が並走) を含む差であり、独立成分でも削減可能量でもない**。Job A の S2/S3 が示したとおり、`pre` の worker 側の実体は modifyitems (§結論 3) であって memo 待ちではない。
- N5. shard-1 / shard-2 (pairing 群): W 中央値 248.4 / 187.5、pre 63.5 / 62.6、`O_max − L` 24.3 / 0.0、F 67.2 / 65.9、memo 57.7 / 58.0 (`verbatim/shards-recent-v1.json`)。

## 3. 数表

### 3.1 Job A (機械集計 `job-out-aggregate.md`。秒。a / b の順)

| cell | `pre_junit` | `pre_entry` | `pre_plugin` | worker collect (median) | worker modify (median) | worker wait (median) | spawn | controller all_collected | process wall | user | sys | memo (hook, receipt_memo_s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| warm (1 process) | — | — | — | — | — | — | — | — | 11.0 | 14.6 | 0.8 | — |
| S0 (48 process) | cohort 16.9 / 17.3 | — | — | process median 16.7 / 17.1 | — | — | — | — | — | — | — | — |
| S1 | 14.97 / 14.93 | 14.44 / 14.42 | — | 11.98 / 12.09 | 0.43 / 0.44 | 0.28 / 0.30 | 0.25 / 0.25 | 61.0 / 48.0 | 65.5 / 52.4 | 693 / 693 | 80 / 84 | xdist_node_collection_finished, 43.3 / 30.3 |
| S2 | 60.42 / 61.36 | 60.40 / 61.34 | 60.42 / 61.36 | 12.39 / 13.20 | 45.66 / 45.55 | 0.024 / 0.024 | 0.65 / 0.64 | 60.4 / 61.4 | 65.4 / 66.2 | 834 / 841 | 2108 / 2095 | configure_node, 44.4 / 53.9 |
| S3 | 61.31 / 61.59 | 61.29 / 61.57 | 61.31 / 61.59 | 12.85 / 13.03 | 44.68 / 44.79 | 0.021 / 0.022 | 0.68 / 0.68 | 61.3 / 61.6 | 66.2 / 66.5 | 850 / 861 | 2064 / 2064 | configure_node, 46.1 / 46.0 |

- `pre_junit` = max_w(cf_exit) − junit timestamp、`pre_entry` = max_w(cf_entry) − 同、`pre_plugin` = max_w(shard plugin の `collection_finished_epoch_s`) − 同 (S2/S3 で `pre_junit` と一致 = probe は受入の `pre` の定義を再現している)。collect = 最後の itemcollected − `pytest_collection` 入口、modify = `cf_entry` − 最後の itemcollected (conftest の hold 処理 + shard plugin の modifyitems + 並び替えを含む複合区間)、wait = `cf_exit − cf_entry` (conftest の `pytest_collection_finish` = memo 待ち + prewarm barrier)。spawn = min_w(worker sessionstart) − controller sessionstart。all_collected = controller が最後の node の collection 通知を処理し終えた時刻 − sessionstart。ids: S1 26,407 / worker、S2/S3 4,116 / worker (shard-0 の選択)。
- 段差表 (機械集計、a / b / 平均): Δ10 = `pre_junit`(S1) − cohort(S0) = −1.93 / −2.32 / −2.13; Δ21 = +45.45 / +46.43 / +45.94; Δ32 = +0.89 / +0.24 / +0.56。process wall の段差: Δwall10 = +48.6 / +35.1 (S1 の同期 memo が入る)、Δwall21 = −0.1 / +13.8、Δwall32 = +0.9 / +0.3。前半/後半の差: S0 +0.35、S1 −0.04 (wall −13.1 = 同期 memo の 43.3 → 30.3)、S2 +0.94、S3 +0.29 秒。
- Lustre client stats の差分 (cell 前後、`raw/job-out/<cell>/lustre-*.txt`、`md_stats:intent_lock` の主列): S1-a 5.20 M、S2-a 60.9 M (約 11.7 倍)。`md_stats:close` は S1-a 27.7 k、S2-a 28.1 k (同程度)。

### 3.2 Job B (機械集計 `job-out-b/analysis-A.md`。1 走の観測、中央値ではない)

shard 層: W 353.3、`pre` 61.9 (memo `configure_node` 51.6)、O_max 281.0 (gw40)、L 216.0 (gw5、rank 5、partner rank 49 = 0.0 秒)、`O_max − L` 65.0、`P_L` 0.0、F 72.3、post 10.03、残差 0.33。

共有 base (key = 5 要素 tuple、秒は worker 秒):

| key | builder | build | copy 配置 | 直下 git | 発行 (issue) | その他 | 開始 | 待ち手 (flock) |
|---|---|---|---|---|---|---|---|---|
| `["AI-Agent: codex", F, T, F, F]` | gw11 | 182.0 | 100.4 | 12.1 | 69.4 | 0.09 | t=0 | — |
| `["AI-Agent: none", F, T, F, F]` | gw13 | 182.0 | 100.4 | 12.1 | 69.5 | 0.09 | t=0 | gw10 182.0、gw5 (= L) 182.0 |
| `["AI-Agent: none", F, T, T, F]` | gw4 | 182.4 | 100.4 | 12.1 | 69.9 | 0.09 | t=0 | — |
| `["AI-Agent: none", T, T, F, F]` | gw12 | 181.9 | 100.4 | 12.2 | 69.3 | 0.09 | t=0 | — |
| `["AI-Agent: none", F, F, F, F]` (発行なし) | gw38 | 112.5 | 100.4 | 12.1 | 0 | 0.08 | t=0 | — |
| `["AI-Agent: fixture", F, T, F, T]` (active_v2) | gw29 | 114.0 | 33.0 | 11.8 | 69.1 | 0.05 | 後発 | — |
| `["AI-Agent: none", F, T, F, T]` (active_v2) | gw40 | 145.8 | 64.2 | 12.4 | 69.1 | 0.06 | t ≈ 54.5 | gw14 143.6 |

- 発行 subprocess は 7 key で 69.1〜69.9 秒 (T-2786 §4 の 65.0〜65.9 より約 4 秒長い。tip・node が違う 1 走で、差の帰属はしない)。直下 git は 11.8〜12.4 秒。copy 配置は t=0 の 5 本 (他 test と同時) が 100.4 秒、後発の active_v2 2 本が 33.0 / 64.2 秒 (T-2786 §4 の「session 開始直後は 80〜112、それ以外は 28〜35」と同じ型)。
- L (gw5、216.0) の内訳: key `["AI-Agent: none", F, T, F, F]` の builder gw13 を flock で待つ 182.0 + base→test copytree 4.6 + verify 5 回 (5.26〜5.96) 27.1 + その他 2.3。
- O_max worker (gw40、281.0) の item 列: rank 40〜422 の小 item 26 個 (t=0〜54.5 秒、最長 14.9 秒) → `test_t080_active_v2_delegation_accepts_full_receipt` (rank 423、t=54.5〜235.1、180.6 秒 = base 構築 145.8 (copy 64.2 = 3.6 + 60.4 + 小、git 12.4、issue 69.1) + copytree 3.1 + verify 2 回 5.5 + その他) → `test_t080_failed_launch_preserves_receipt_refusal` (rank 424、t=235.1〜281.3、46.2 秒 = copytree 2.9 + verify 5.4 + その他 37.9)。timeline 全体は `job-out-b/analysis-A.md` の「Timeline gw40 O_max」。
- T-2786 の成分名との対応 (§1.2 の wrapper 対象): build / copy / git / issue / history / key_wait / base_copy / verify を同名で記録。`slot_wait` (L 条件) は本 wave に無い。

### 3.3 参照受入 (同 code、`verbatim/acceptance-ref.chain.log`、受領証は job dir)

session `73684ba638492cc867d64c2295405c9d`、3 shard とも child-green (failed 0)。読み取りは `verbatim/read_shards_v1.py.txt` / `read_shards_v2.py.txt` (出力 `verbatim/acceptance-ref-shards.json` / `acceptance-ref-shard0-v2.json`)。量の定義は §2b と同じ。

| shard | node | 開始 (JST) | W | `pre` | O_max | L | `O_max − L` | F = W − O_max | memo (`receipt_memo_s`) | post | passed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| shard-0 | bnode009 | 02:17:32 | 351.4 | 61.8 | 279.4 | 210.0 | 69.4 | 72.0 | 56.0 | 10.03 | 4063 |
| shard-1 | bnode004 | 02:13:29 | 247.2 | 61.8 | 181.7 | 137.2 | 44.5 | 65.5 | 57.4 | — | 10919 |
| shard-2 | bnode030 | 02:13:31 | 204.7 | 62.4 | 139.0 | 139.0 | 0.0 | 65.7 | 56.6 | — | 11356 |

- shard-0 の最大占有 worker は gw14 で、item 列は `test_t080_active_v2_delegation_accepts_full_receipt` (rank 423) 181.4 + `test_t080_failed_launch_preserves_receipt_refusal` (rank 424) 46.1 + `test_s8c_preregistration_predicates::test_repository_ca…` (rank 14) 16.6 + 小 item。L (210.0) の worker は gw5 (rank 5)、相方 0.0。**Job B の replica (§3.2) と同じ構造** (rank 423 / 424 の 2 node が別 worker に直列、L の worker は相方 0) が実受入でも出た。
- shard-0 の `pre` 61.8 / memo 56.0 / post 10.03 / F 72.0 は Job B (61.9 / 51.6 / 10.03 / 72.3) と S3 (`pre_junit` 61.3 / 61.6) の帯にある。

## 4. 弁別 — 事前に書いた読み方 (段 4 裁定 §4) をそのまま当てる

- **Δ10 (S1 − S0) = −2.1 秒:** xdist で 48 worker を起動して同時に collection させる方が、独立 48 process の cohort より 2 秒短い。「xdist 起動 + 同時 collection + controller 通知」に純増は無い (xdist の純増とは呼ばない)。
- **Δ21 (S2 − S1) = +45.9 秒 (複合差):** 事前登録では「shard plugin + memo の同期→早期並走への切替」の複合差と読むと決めていた。実測では worker の memo 待ち (`wait`) は 0.02 秒で、増分は worker の modify 区間 (45.6 秒) に入った。切替 (同期 43.3 秒が controller 側から消え、早期 44.4 秒が並走に変わった) は process wall の段差 (−0.1 / +13.8) に現れる。したがって Δ21 の実体は「shard plugin の `pytest_collection_modifyitems` が 48 worker 同時に払う path 正規化」で、memo は同じ長さの窓に隠れている。**この帰属は同 job・同 SHA・同 node の段階載せから得た** (T-2243 §7 must-fix 1 が禁じた「異条件の差の成分配分」ではない)。plugin 内のどの行かは関数別計時をしていないので、code 読み (`_canonical_item` の `Path(item.path).resolve()`) と sys 時間 (+2027 秒 / 48 worker ≈ 42 秒) と Lustre `intent_lock` (11.7 倍) の対応からの読みである。
- **Δ32 (S3 − S2) = +0.6 秒 (複合差):** ledger 読込 (24,379 entry、controller の configure 段) + workerinput 配送 + worker 側検証 + 並び替え + pairing property 付与の合計で 1 秒未満。configure 段の費用は junit 起点より前なので `pre_junit` には入らず、process wall の段差 (+0.9 / +0.3) にも 1 秒未満。
- **参照との整合 (§3.3):** S3 の `pre_junit` 平均 61.45 秒と参照受入 shard-0 の `pre` 61.76 秒の差は −0.31 秒 (閾値 10 秒以内、`job-out-aggregate.json` の `reference.reproduces_reference=true`) → 再現。Job B (replica) の 61.9 秒も同じ帯。参照受入の shard-0 は Job A と同じ bnode009 で走った (同 node は偶然で、条件として揃えたのではない)。
- **律速 (Job B):** wall 353.3 = O_max 281.0 + F 72.3。O_max の worker は L の worker ではなく、rank 423〜424 の 2 node を t=54.5 秒から直列に抱えた gw40。L の内訳 (待ち 182 + copy 4.6 + verify 27.1) は 1676 の式の成分 (共有 base 構築・verify・copy) と同じ名で取り直せたが、**wall を決めているのはその式の外にある「後方 rank の base 構築 + 直列」**であり、式は `最遅 shard の wall ≈ max(L の worker, 後方 rank の active_v2 系 key を建てる worker の列) + 固定費 (pre + post)` と書き直す必要がある (本 wave の観測 1 走 + 21 session の N2 から)。

## 5. 短縮策の効果量の見込み (実装しない、D1936 項 35)

| 策 | 本 wave の値からの見込み | 費用・前提 | 見込みの判定 |
|---|---|---|---|
| (a) ledger 未収載 8 node の再登録 (D2107 の refresh mode の運用) | `t2817_ledger_model.py` (固定所要 list-scheduling、48 worker、conftest と同じ並び規則、所要 = 21 session の junit 中央値、共有 base の相互作用なし) で、(a) 現行 ledger のまま O_max_model 253.3 (既定 cost 9.6、最大 worker は 42) → (b) 未収載に junit 中央値を与えると 233.7 (= L)、差 19.5 秒 (`ledger-model.md` / `.json`)。**model 値であり実 wall の予測ではない。D2107 の refresh 入力でも採用案でもない。** 観測の `O_max − L` (62.7〜65.0) より小さいのは、junit 中央値が builder / waiter の二峰 (180〜335 vs 37〜46) を潰すことと、model が動的配布・共有 base の相互作用を持たないため | refresh は D2107 の運用 (1 走の JUnit から非凍結 entry を全再生成)。再登録後に active_v2 系 key の base 構築が t=0 の 5 本と同時に走ると copy 配置が 100 秒級になる (Job B の t=0 の 5 本) 可能性があり、L 自身が伸びうる (未測定) | **model 値のみ。** 実 wall の変化は測っていない |
| (b) `pre` の 2 本の並走 (worker 側 collect 12 + plugin modify 45 ≈ 57〜58、controller 側 早期 memo 44〜54) | `pre` ≈ max(両者) + 数秒。片方だけを縮めても `pre` はもう片方で止まる | memo prewarm は D2185 で現行維持。plugin の modifyitems の内訳 (関数別) は未計測 | **構造の記述のみ。数値の見込みは書かない** |
| (c) 終了後 10.0 秒 (shard-0 のみ) | 観測のみ | 候補は §8 | 見込みを書かない |
| (d) T-2243 §5 (a)(b)(c)(e) | 本 wave の対照の外 | 参照 | 再掲しない |

## 6. 既存被覆との関係 (二重に数えない)

- **T-2710 §4** (固定費 = 開始前 ≈ 60 + 終了後 3〜8、warm/cold): 本 wave の N4 / Job B は同じ量を pairing 群と現行 tip で取り直し `pre` / `post` / 残差に分けたもの。新しい量は `post` の shard-0 10.0 秒の一定性。
- **T-2786 §4** (base 構築の内訳、`7975385b5` の命題): Job B は現行 tip (5 要素 key、7 key) の同成分を 1 走で観測した。値は同型 (copy 100 vs 28〜64、git 12、issue 69 vs 65)。旧値を無効化しない (規律 7)。
- **T-2700 / D2185** (早期 memo prewarm の機序と効果): 本 wave は memo が `pre` の中で worker 側の modify と並走して隠れることを同 job で観測した。効果量の新しい主張ではない。
- **T-2617 §3.2** (plugin +1.74 user CPU 秒 / user+sys +3.46 秒、単一 process、login): 本 wave の Δ21 は 48 worker 同時・Lustre 上での同じ plugin の費用 (worker あたり sys 約 42 秒) で、T-2617 の単一 process 値の並列版にあたる。§3.3 の「残る約 38 秒は 48 重の並列実行そのもの」は本 wave の同条件対照で「plugin の modifyitems の 48 重」に絞れた。
- **T-2243** (独立 process の並列度応答・配置・bytecode): Job A の S0 はその L 腕の再現 (cohort 16.9〜17.3 vs T-2243 L48 process median 18.4、別 node・別 tip)。§5 (d) の「約 43 秒」は Δ21 + Δ32 + Δ10 = +44.4 秒として同 SHA・同 node で閉じた。
- **D2107** (ledger 予測負荷と実測の乖離、refresh mode): N3 の未収載は D2107 が書いた型。本 wave は refresh を実施しない。
- **T-2766 §6 landing 走** (新 pin regime、4 worker が 380〜393 秒): N2 の「最大占有 worker ≠ L の worker」はその観測の 21 session 版 + Job B の timeline。

## 7. 段 3 相談・段 5 実装・段 6 レビューの所見と裁定

- 段 3 (codex gpt-6-astra / medium / read-only、lane sol、`verbatim/s3-consult-out.md`): 所見 11 件 (高 6・中 5)、**全件 real・採用、refuted 0**、判定「修正後 GO」。高 6 件 = (1) scheduler no-op は collection 一致検査を消す → 検査と失敗通知を残し配布だけ省く; (2) S1 でも controller の同期 memo prewarm が発火 → S1 の名と Δ21 の読みを訂正; (3) 計時区間 (ledger 読込は configure 段、wrapper 順序) → 列を分離; (4) S2/S3 の report.json は create-only → 走別 dir; (5) (P1) の全面省略は依頼 (1) を満たさない → Job B (A 条件 1 走) を追加; (6) offline 並びから O_max の変化は導けない → 仮説のまま、model 値に限定。中 5 件 = 加法分解と相方の混同、母集団の限定、`--maxfail` → `--no-loadscope-reorder`、比較単位と反復の限界、読取り専用条件と同 SHA 参照。裁定の逐語は `verbatim/s4-ruling.md`。
- 段 5 (codex author 2 本 + fix 1 本、`verbatim/s5-author-a-out.md` / `s5-author-b-out.md` / `s5-fix1-a-out.md`): A = runner / plugin / 集計 / model の 4 file、B = replica runner / plugin / analyze の 3 file。合成入力の正例・負例は各報告に逐語。親の login 生死確認 (narrowed 1 file、`-n 2`) で A の plugin が「ledger 属性の有無しか記録しない (conftest は読まない場合も空 dict を置く)」欠陥を見つけ fix 1 本で `ledger_entries` / `ledger_should_load` / worker の payload 有無を足した (`verbatim/smoke-a2/` で S1 形 / S3 形の弁別を確認)。B は job 内 smoke で wrapper の配線を確かめてから A 走へ進んだ。
- 段 6 (codex gpt-6-astra / medium / read-only、2 レンズを 1 本、`verbatim/s6-review-prompt.md` / `s6-review-out.md`): 記録 commit 後にレビューし、所見と裁定をここへ追記する (追記前の版はこの行が placeholder のまま)。

## 8. 限界・言わないこと

- **Job A は 1 node (bnode009)・1 job・1 tip・反復 2 (順序反転) の実測、Job B は 1 走の観測で中央値でない。** 21 session (§2b) は tip 非同一・投入元未照合。順序反転は時間変動の記述であり外乱除去の証明ではない。
- **`pre` の成分配分は「S3 が参照受入を再現した」ことを条件に候補として書いた** (§結論 3)。plugin の modifyitems の内訳 (path 解決か allocate か) は関数別に計時しておらず、`Path.resolve()` への帰属は code 読みと sys 時間・Lustre op 数の対応からの読みである。削減可能量は書かない。
- **律速の機構 (未収載 → 後方 rank → 遅い開始 → 別 worker の直列) は Job B 1 走の timeline と 21 session の rank property からの観測で、ledger を直した対照走は無い。** ledger model は固定所要の model で、実 wall の予測ではない。
- 終了後 10.0 秒 (shard-0 のみ一定) の原因は同定していない。候補 (段 3 の見つからなかったこと): xdist の shutdown、shard plugin の `pytest_sessionfinish` の report 作成、conftest の memo session 終了、共有 base の atexit cleanup、JUnit 書出し。原因追跡の追加走はしない。
- Job B の発行 subprocess 69 秒と T-2786 の 65 秒の差、copy 配置の差は tip・node・key 集合が違う 1 走の値で、帰属しない。
- 早期 memo prewarm の値 (44〜54 秒) は D2185 の現行維持の下で観測しただけで、短縮策は提示しない。
- 改善は実装していない。§5 は model 値と構造の記述で、実装した場合の受入 wall の変化は測っていない。
- 事故 (自分起因、実害小): (1) Job A の最初の投入が同一 worktree の orphan hold で rc=16 (子は起動せず) → 同 SHA の別 worktree から再投入 (§1.1)。(2) 段 5 author A の plugin が ledger の読込有無を弁別できない計装だった → 生死確認で見つけ fix 1 本。

## 9. この dir の中身

- `README.md` — 本文。
- `job-out-aggregate.md` / `.json` — Job A の機械集計 (`verbatim/t2817_collection_stage_aggregate.py.txt` の出力)。`ledger-model.md` / `.json` — 固定所要 model (`verbatim/t2817_ledger_model.py.txt`、入力は ledger + 参照 session `b292af15…` の shard-0 report + 21 session の junit)。
- `raw/job-out/` — Job A の生記録 (原本は wave 専用 dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/job-out/`)。`env.txt`、`lustre-initial.txt`、`plugin-import.*`、`probe.done`、`pycache-after.txt`、各 `<cell>/` に `cell.txt`、`time.txt` / `proc-*.time` / `proc-*.rc` / `proc-*.start` / `proc-*.end`、`out` / `err` / `proc-*.err`、`junit.xml`、`probe.json`、`lustre-*.txt`、`loadavg-*.txt`、`mem-*.txt`、`singleton-before.txt`、`process-args-before.txt`。**除外:** `proc-*.out` (S0 の nodeid 出力、各 3 MB × 96)、`session/shard-0/report.json` (S2/S3、各 5.7 MB)。
- `raw/job-out-b/` — Job B の生記録 (原本は同 dir の `job-out-b/`)。`run.json`、`env-before.json`、`probe.done`、`smoke/` (run.json、pytest.log、spans)、`A/` (run.json、env-*.json、pytest.log、controller.json、`spans-*.jsonl` 74 file、`create-session.log`、`session/junit.xml`)、`analysis-A.md` / `.json`。**除外:** `A/session/report.json` (6 MB、原本は replica session `69dcbd57434a3a0c176c98f0f222a969/shard-0/`)。
- `verbatim/` — `T-2817-origin.md` (依頼)、`s1-brief.md`、`s3-consult-prompt.md` / `s3-consult-out.md`、`s4-ruling.md`、`s5-author-a-prompt.md` / `s5-author-a-out.md`、`s5-author-b-prompt.md` / `s5-author-b-out.md`、`s5-fix1-a-prompt.md` / `s5-fix1-a-out.md`、probe 7 file の逐語 `.txt` (sha256 は `probe-sha256.txt`、実体は Codex author の子 branch `author-t2817-probe-a` `f1a1e8eb0` / `author-t2817-probe-a-fix1` `a028857a6` / `author-t2817-probe-b` `ed461aa4f`、land しない)、親の運転 script `run-probe-a.sh.txt` / `run-probe-b.sh.txt` / `run-ledger-model.sh.txt` / `warm-joba.sh.txt` / `run-acceptance-gated.sh.txt`、dispatch log `run-probe-a.log` / `run-probe-a.attempt0-orphanhold.log` / `run-probe-b.log`、`pyc-warm-login.*` / `pyc-warm-joba.*`、前提実測の script と出力 (`read_shards_v{1,2,3}.py.txt`、`rank_replay_v1.py.txt`、`shards-recent-v1.json`、`shard0-pairing-v2.json`、`t2724-nodes-v3.json`、`pairing-shard0-junits.txt`)、login 生死確認 (`smoke-a/`、`smoke-a2/`)、`startup-gate.log`、`acceptance-ref.chain.log`、段 6 のレビュー prompt / out。

## 逐語の行末空白の可逆正規化 (DW-S07)

`git diff --check` に触れる行末空白 (space / tab) を 13 file・60 行から除いた。可視文字は不変。除いた suffix は行番号つきで `verbatim/trailing-whitespace-normalization.json` に残し (原文 sha256・bytes・正規化後 sha256・bytes を併記)、`verbatim/normalize_trailing_ws.py.txt` の逆操作 (各行の末尾へ suffix を戻す) で原文 bytes を復元できる。対象: `verbatim/s3-consult-out.md` (16773 → 16683 bytes、45 行)、`verbatim/s5-fix1-a-out.md` (3928 → 3924、4 行)、`verbatim/run-probe-a.log` / `run-probe-b.log` (各 1 行)、`raw/job-out/{warm,S0-a,S0-b,S1-a,S1-b,S2-a,S2-b,S3-a,S3-b}/cell.txt` (各 1 行 = `argv=` 行の末尾 space)。原文は wave 専用 dir に残っている。

## 10. 再現手順

1. local main から fresh worktree を切り、submodule を初期化し、login で `python3 tools/run_tests.py orchestrator/tests --collect-only -q -p no:cacheprovider` を 1 回走らせて pyc を温める。
2. `verbatim/t2817_*.txt` を repo 外の 1 dir に `.sh` / `.py` として置く (7 file)。
3. Job A: worktree を cwd にして `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:40:00 --queue-wait-timeout 5400 --overall-grace 5400 -- bash <dir>/t2817_collection_stage_probe.sh` (出力先は script 冒頭 `OUT_ROOT` の既定、空 dir が要る)。終了後 `python3.10 <dir>/t2817_collection_stage_aggregate.py <OUT_ROOT> --markdown out.md --json out.json [--reference-pre <秒>]`。
4. Job B: 別 worktree (または Job A 終了後の同 worktree) から `... -- python3.10 <dir>/t2817_replica_runner.py run --repo-root <worktree> --probe-dir <dir> --out-root <out> --job-tag <tag>`。終了後 `python3.10 <dir>/t2817_replica_analyze.py --run-dir <out>/A --markdown out.md --json out.json`。replica session が受入共有 root に残るので、受入成果物の読み取りから除外する。
5. model: `bash verbatim/run-ledger-model.sh.txt` の形 (ledger + shard-0 report + junit 群)。
6. 前提実測: `verbatim/read_shards_v{1,2,3}.py.txt` を `.py` として login で走らせる (read-only)。
