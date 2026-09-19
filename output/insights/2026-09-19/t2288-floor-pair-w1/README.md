# [T-2288] (b) B-4 床値 (floor-pair) の w1 を凍結 spec 3 本 (rr95 / rr50 / rr5) で同一 HEAD から実投入し、初回実配送の証拠を記録した

`authority: none`
`default_effect: no-state-change`

2026-09-19。wave `dev-wave-t2288-floor-pair-w1`、branch `worktree-dev-wave-t2288-floor-pair-w1`。着手直前の local main
`2ba4000870c63254132410b3002b5298c0c6a210` (21:27 JST に再読) をそのまま実行 HEAD `H` とした。可変状態の正本は worklog 末尾と
現行 phase doc であり、本書ではない。時刻は特記なき限り UTC (`date -u`、receipt の epoch、`qstat -f` の表示から採り、推定していない)。

## 依頼と答え

依頼は「[T-2288] (b) B-4 床値 (floor-pair) の w1 実投入。carry (docs/archive/worklog-phase3-0918-1661.md の [T-2288]) どおり、着手直前の
local main から実行 HEAD H を 1 つ決めて detached checkout で place (D2069 項 7) し、凍結 spec 3 本 (rr95 / rr50 / rr5) の w1
(now + 24h <= 2026-09-27T00:00Z) を同じ H から tools/pegasus/submit_floor_pair.sh で投入する。手順は docs/pegasus-runbook.md §7.8、
計算ノード側は tools/pegasus/floor_pair_campaign.sh、契約は D2145 / D2146。終了条件 = 初回実配送の証拠 (8 変数・walltime・signal・到達段・
receipt) の確認と記録。w2 (09-29 以降) と finalize は後続 wave。窓を使えずに終わったら延長・差替えをせず記録して終端。凍結 spec・事前登録の
bytes は変えない。scope 外 = 集約発行・採用裁定・§5 記入・追加 gate」だった。

**答え: 3 spec の w1 を同じ `H` から投入し、3 job とも投入 8 秒後に計算ノードで起動、69〜77 分で terminal `complete` (124 / 124 session、
62 / 62 標本、drop 0、trap による signal 観測なし、job_rc 0) で終わった。** 8 変数のうち 6 個は受領証の値で、evidence dir は出力先で、
walltime 変数は job body の形式検査の通過で配送を確認し、walltime・到達段・receipt は下記の証拠 file で確認した (「初回実配送の証拠」と
「完走の記録」)。signal は配送の有無を判定できる証拠が無い (走が walltime 前に終わり、trap の観測記録が無い)。実装面の差分はゼロ (資材は T-2288 (a) のまま、変異 matrix 免除)。凍結 spec・事前登録・既存出力の
bytes は変えていない。

## 実行 HEAD と投入元 checkout (D2069 項 7、申し送り 2・3)

- `H` = `2ba4000870c63254132410b3002b5298c0c6a210` (local main tip。`git rev-parse main` を 12:27:09Z に再読し、wave worktree の HEAD と一致)。
- 投入元 checkout = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/submit-tree` (`git worktree add --detach … H`、28140 file、
  detached、tracked clean、欠落 0、untracked 0、`git worktree lock` 済み。lock 理由 = 3 段 (w1 / w2 / finalize) が終わるまで HEAD を進めない・
  削除しない)。submodule は未初期化のまま (driver・job body は `external/ccbench` を参照しない。`git status --porcelain --untracked-files=no`
  は未初期化 submodule を差分に数えない — submitter の tracked clean 検査 (`checkout tracked_dirty`) は通った)。
- checkout 時に `warning: unable to access 'output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/.gitattributes': システムコール割り込み`
  が 1 件出た。同 path は tracked file ではなく (同 dir の tracked は `campaign.lock` と `runs/wal.jsonl` の 2 本)、git の属性探索の stat が
  EINTR に当たっただけで、`git ls-files --deleted` = 0、tracked 28140 = checkout 報告値と一致。
- `place` (login node、12:30:31Z〜12:30:42Z、rc=0): `python3 -B -m orchestrator.campaign.b4_binary_record place --record
  output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json --source-root /work/1/SFC/tanab/izanagi-b4-floor-binaries
  --env-tag pegasus --repo-root <submit-tree>` → `output/env/pegasus/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4`
  (701760 bytes、sha256 一致、`-rwxr--r--`)。ignored path なので木は tracked clean のまま。**`place_record` は site 検査を持たず login node で
  完了する** (site を要求するのは `produce_record` だけ)。receipt の policy (`contract_sha256 e576e9cd…`、ccbench pin `511c9538`) と現行
  protocol の一致検査は `floor.store_binaries` が行い、通った。3 spec の `artifacts` はいずれも同じ binary (reference / candidate とも
  `7cdf0dc3…`、対は byte 同一の候補対) なので place は 1 回で足りる。

## dry-run と実投入 (runbook §7.8、D2145 項 3)

submitter は submit-tree の root で `bash tools/pegasus/submit_floor_pair.sh --workload <wl> --window w1 [--dry-run]` を起動した
(起動 script は job dir の `run-submit.sh`、stdout / stderr は job dir に `submit-<wl>-w1[-dry].{stdout,stderr,rc}` として残る)。

| 段 | rr95 | rr50 | rr5 |
|---|---|---|---|
| dry-run (rc、所要) | rc=0、12:31:02Z〜12:31:05Z、nonce `879a8ef9966c1e604dab3bd9d338b488` | rc=0、12:31:20Z〜12:31:24Z、nonce `d451d1d2b0b9a26048a4bdd97dba20f0` | rc=0、12:31:24Z〜12:31:27Z、nonce `0c1d69d137d3e6ba3d11a4602a738212` |
| 実投入 (rc、所要) | rc=0、12:32:09Z〜12:32:11Z | rc=0、12:32:19Z〜12:32:20Z | rc=0、12:32:20Z〜12:32:22Z |
| nonce (evidence dir) | `3fb5c77cc501ee3f7917becd093dfe39` | `8b8dc69bffae50e5e14d574ea3e99153` | `91c65a96c0d2dcfd5869acc63e60b0e9` |
| qsub | rc=0、`Request 10711.nqsv submitted to queue: gen_S.` | rc=0、`Request 10712.nqsv submitted to queue: gen_S.` | rc=0、`Request 10713.nqsv submitted to queue: gen_S.` |
| submit-receipt.json `status` | `submitted`、`pbs_jobid` `10711.nqsv` | `submitted`、`pbs_jobid` `10712.nqsv` | `submitted`、`pbs_jobid` `10713.nqsv` |
| 起動 (`qstat -f`、JST) | Created 21:32:11 → Started 21:32:19 (8 秒)、`bnode022` | Created 21:32:20 → Started 21:32:28 (8 秒)、`bnode080` | Created 21:32:22 → Started 21:32:30 (8 秒)、`bnode081` |

- dry-run と実投入で submitter が通した gate は同一 (引数 → 環境消去 → interpreter → pin → walltime → checkout (root 一致・detached・
  tracked clean・HEAD) → spec (file sha・HEAD blob sha) → binary → 窓 (`now >= not_before && now + 86400 <= not_after`) → outputs (対象窓
  JSONL 不在、他窓なし) → evidence dir → pre-submit.json)。dry-run は qsub だけを省く。stdout / stderr は 6 回ともに空。
- qsub argv (pre-submit.json / submit-receipt.json の `qsub_argv` に逐語): `qsub -l elapstim_req=24:00:00 -N fp-<wl>-w1 -v FP_NONCE=…,
  FP_EXPECTED_HEAD=H,FP_SPEC_RELPATH=…,FP_SPEC_SHA256=…,FP_MODE=window,FP_WINDOW_ID=<wl>-w1,FP_EVIDENCE_DIR=…,FP_ELAPSTIM_REQ=24:00:00
  -o <evidence>/scheduler.stdout -e <evidence>/scheduler.stderr tools/pegasus/floor_pair_campaign.sh`。`request` = {project SFC、queue gen_S、
  nodes 1、elapstim_req 24:00:00 = 86400 s}。
- 3 本は順次 qsub したが (12:32:09Z〜12:32:22Z の 13 秒)、job は 3 node で並走した (§7.5)。`qstat -f` の Entered Queue Time から
  Started Request Time までは 3 job とも 8 秒 (gen_S は投入時 26 走行 / 20 待ち / 25 hold)。この 8 秒の内訳 (queue 待ちと起動準備) は分離
  できない。

## 初回実配送の証拠 (F660 で未観測だった 5 項目)

1. **8 変数の伝播:** job body の `bootstrap` は `PBS_JOBID` `PBS_O_WORKDIR` + `FP_NONCE` `FP_EXPECTED_HEAD` `FP_SPEC_RELPATH` `FP_SPEC_SHA256`
   `FP_MODE` `FP_WINDOW_ID` `FP_EVIDENCE_DIR` `FP_ELAPSTIM_REQ` の 10 個が空なら `missing_binding` (rc=2) で止まる。3 job とも evidence dir に
   `driver.stdout` / `driver.stderr` (job body が `set -o noclobber` で開く) が 12:32Z に作られ、submit-tree の窓 JSONL に driver が header を
   書いたので、bootstrap → commands (`git nm pgrep sha256sum hostname date realpath mkdir env`) → checkout (`PBS_O_WORKDIR` == submit-tree、
   HEAD == `FP_EXPECTED_HEAD`) → spec (sha == `FP_SPEC_SHA256`) → binary → site (hostname `bnodeNNN`) → window → scratch (`/scr/<jobid>`) →
   window 再検査 → driver の全段を通った。値の一致は終端の `job-result.json` (job body の `write_result` が env のうち `FP_NONCE` /
   `FP_EXPECTED_HEAD` / `FP_SPEC_RELPATH` / `FP_SPEC_SHA256` / `FP_MODE` / `FP_WINDOW_ID` の 6 個を写す) で「完走の記録」に確認する。
   `FP_EVIDENCE_DIR` は同 file の出力先として、`FP_ELAPSTIM_REQ` は `walltime_seconds` の形式・正値検査の通過としてだけ確認でき、受信値
   そのものは記録されない。
2. **walltime:** `qstat -f` の `(Per-Req) Elapse Time Limit = Max: 86400S Warn: 86400S` (3 job とも、`observations/qstat-f-<id>-initial.txt`
   に保存) = scheduler 側が受けた要求の確認。submitter の `-l elapstim_req=24:00:00` と env `FP_ELAPSTIM_REQ=24:00:00` は同じ 1 箇所
   (`select_walltime`) から出ているが、job body が受け取った `FP_ELAPSTIM_REQ` の値は上記のとおり直接には記録されない。
3. **signal:** `qstat -f` の `Accept Sigterm = Yes` (job body の `#PBS --accept-sigterm=yes`)。job body の trap (TERM / HUP / INT →
   `record_signal`) が観測したかは終端の `job-result.json` の `reason` (`completed` | `signal_observed`) で「完走の記録」に書く。trap の
   観測記録が無いことは配送が無かったことの証明にはならない (F1012 の SIG_IGN 継承が否定できない限り、配送されても観測されない場合を
   排除できない)。
4. **到達段:** driver 起動段 (上記 1)。driver 内では `_assert_live_environment` (site PEGASUS_COMPUTE + 証拠、env_tag pegasus) と
   `runtime_head == loaded_head` を通って header を書いた: `schema floor-pair-window/v3`、`loaded_head` = `runtime_head` = `H`、
   `session_count 124`、`planned_measurement_count 248`、`pair_sample_count 62`、`measurements_per_session 2`、`plan_sha256` =
   rr95 `9c7838cc1d501595e690c4f868dbd36a32acdb1e54372b5a15585ac9305c3860` / rr50 `b4da73d253e55851c2752cbe821b8deebc2c49269c0bb0022a1ce2c1b09a05b8`
   / rr5 `cc45797ad26eb1a50d658126ac594277523e04b9fd102727807f38cd42e738b7`。
5. **receipt:** submitter の `pre-submit.json` → `submit-receipt.json` (`status submitted`、`qsub_rc 0`、`pbs_jobid`)、`qsub.rc` = `0`、
   `qsub.stdout` に request 行。job body の `job-result.json` は終端で書かれる (「完走の記録」)。

session record の形 (rr95 の 2 行目、sample 35 `candidate_1`、schedule 順は seed で無作為化): `pre_probe.status clear` → reference
(5 rep、throughputs `[2326626, 2357701, 2341281, 2331727, 2303422]`、rc 全 0、16.8 秒) → candidate (5 rep、rc 全 0、16.9 秒) →
`post_probe.status clear`、session 33.7 秒、`status complete`。両測定の `binary_sha256` は `7cdf0dc3…` (同一 bytes の対)。**この値は床値の
集約に使う生データであって、本書で throughput を比較・解釈しない。**

## 完走の記録 (3 job とも terminal `complete`、trap による signal 観測なし)

watcher (`run-watch.sh`、5 分周期) は 13:49:40Z に pending=0 で終了し、待ち手 (`dev_wave_wait.py producer`) は rc=0 で戻った。
以下は `job-result.json` (job body が env の値をそのまま書く受領証)、`scheduler.stderr` (NQSV accounting)、`driver.stdout`、窓 JSONL から
`jq` / `cat` で読んだ値である。

| 項目 | rr95 (`10711.nqsv`) | rr50 (`10712.nqsv`) | rr5 (`10713.nqsv`) |
|---|---|---|---|
| `job-result.json` `job_rc` / `gate` / `reason` / `driver_rc` | 0 / `driver` / `completed` / 0 | 0 / `driver` / `completed` / 0 | 0 / `driver` / `completed` / 0 |
| 同 `hostname` / `pbs_jobid` | `bnode022` / `0:10711.nqsv` | `bnode080` / `0:10712.nqsv` | `bnode081` / `0:10713.nqsv` |
| 同 `expected_head` / `spec_sha256` / `window_id` / `nonce` | H / `990e3a6f…` / `rr95-w1` / `3fb5c77c…` | H / `b582d20c…` / `rr50-w1` / `8b8dc69b…` | H / `d13c3844…` / `rr5-w1` / `91c65a96…` |
| 同 `started_epoch` → `completed_epoch` (差) | 1789821139 → 1789825317 (4178 s) | 1789821148 → 1789825289 (4141 s) | 1789821150 → 1789825752 (4602 s) |
| NQSV accounting (`scheduler.stderr`、JST) | Ended 22:41:57、Elapse 4182S、Remaining 82218S | Ended 22:41:29、Elapse 4145S、Remaining 82255S | Ended 22:49:12、Elapse 4607S、Remaining 81793S |
| `driver.stdout` (window result JSON) | `status complete`、`session_count 124`、`artifact_sha256 fa06e213…` | `status complete`、`session_count 124`、`artifact_sha256 8bdd9093…` | `status complete`、`session_count 124`、`artifact_sha256 12fbe874…` |
| `driver.stderr` | 0 byte | 0 byte | 0 byte |
| 窓 JSONL (行数 / sha256 先頭 / mode) | 126 / `fa06e2130b0d15cd` / 0600 | 126 / `8bdd909394fa2bce` / 0600 | 126 / `12fbe874c2899de9` / 0600 |
| terminal | `complete`、session 124 / 124、measurement 248 / 248、sample 62 / 62、dropped 0 | 同左 | 同左 |
| session `status` の内訳 | 124 `complete` | 124 `complete` | 124 `complete` |
| probe (pre / mid / post) | 124 とも `clear` / `clear` / `clear` | 同左 | 同左 |
| 測定の rep rc | 248 測定とも `[0,0,0,0,0]` | 同左 | 同左 |
| side の内訳 / cell | `candidate_1` 62、`candidate_2` 62 / `rr95-t48-s0.9-rmw0` | 62 / 62 / `rr50-t48-s0.9-rmw0` | 62 / 62 / `rr5-t48-s0.9-rmw0` |
| session の実時刻 (最初の `started_at` 〜 最後の `finished_at`) | 12:32:19.9Z 〜 13:41:57.3Z | 12:32:29.3Z 〜 13:41:29.2Z | 12:32:34.4Z 〜 13:49:12.9Z |

- **8 変数の配送 (6 個は値で、1 個は出力先で、1 個は形式検査の通過で確認):** `job-result.json` の `nonce` / `expected_head` /
  `spec_relpath` / `spec_sha256` / `mode` / `window_id` (= `FP_NONCE` / `FP_EXPECTED_HEAD` / `FP_SPEC_RELPATH` / `FP_SPEC_SHA256` /
  `FP_MODE` / `FP_WINDOW_ID`) が `submit-receipt.json` の同名 field と 3 job とも一致。`FP_EVIDENCE_DIR` は同 file がその dir に書かれたことで
  確認。`FP_ELAPSTIM_REQ` は job body の `walltime_seconds` (形式 `HH:MM:SS` と正値だけを検査、不正なら rc=2 `invalid_walltime`) を通った
  ことしか分からず、受信値が `24:00:00` だったことは job 側の記録に無い (scheduler 側の 86400S は submitter の `-l` の確認であって env の
  確認ではない)。計算ノード側の `PBS_JOBID` は `0:10711.nqsv` の形 (`0:` 接頭辞) で、job body の `^([0-9]+:)?[A-Za-z0-9._-]+$` に適合した。
- **walltime:** 要求 86400 s に対し実 Elapse 4145〜4607 S (4.8〜5.3%)。walltime 到達なし。
- **signal:** `reason completed` = job body の trap (TERM / HUP / INT) による観測記録なし。walltime 未到達。配送の有無と trap の発火能力
  (F1012 の SIG_IGN 継承) は本走では検証されず、否定もされない。
- **到達段:** `gate driver` / `driver_rc 0`。driver は 124 session をすべて `complete` で記録し terminal を書いた。
- **receipt:** submitter の `submit-receipt.json` と job body の `job-result.json` (`open(..., "x")`) の両方が 3 job 分揃った。
- **accounting の出先:** NQSV の request accounting (`Request ID … Ended Request Time … Elapse`) は `-e` で指定した `scheduler.stderr` に
  出た。`-o` の `scheduler.stdout` は 0 byte。`tools/dev_wave_wait.py compute --accounting-file` をこの job 型に使うなら `scheduler.stderr` を渡す。
- 1 session ≈ 34 秒 (rr95 / rr50)、≈ 37 秒 (rr5)。1 窓 job ≈ 69〜77 分。3 job は 3 node で並走し、最初の qsub から最後の終端まで 77 分。
- `job-result.json` は `FP_EVIDENCE_DIR` と `FP_ELAPSTIM_REQ` の受信値を写さない (上記)。写すよう job body を変えるのは実装面の変更であり
  本 wave の scope 外 — 必要なら別 wave で Codex author が扱う。
- submit-tree は終端後も HEAD = H、detached、tracked clean、untracked 3 (窓 JSONL)。binary は ignored のまま実在。

## 段 6 の敵対レビュー 1 本 (read-only、逐語は `verbatim/s6-review.md`、prompt は `verbatim/s6-review-prompt.md`)

軽量版 (実装面差分ゼロ) のため段 2・3・5 を省き、DW-C00 の docs-only 条項に従い一次資料との突合レビューを 1 本だけ投じた
(`gpt-6-astra` / medium、11 call、246 秒、受理)。レビューは「dry-run と実投入」表 18 cell と「完走の記録」表 42 cell、JSONL 3 本 378 行
(372 session・744 測定・1,116 probe・3,720 rep rc)、証拠 file 30 本、meta / rc / stdout / stderr 24 本、初期 qstat 3 本、launcher 6 本を
独立に検算し、値の不一致ゼロで **NO-GO (must-fix 2 = 過大主張の言い切り)** を出した。親の裁定:

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| 1 | 「8 変数を値で確認」は不成立 — `write_result` が写すのは 6 変数、`FP_EVIDENCE_DIR` は出力先、`FP_ELAPSTIM_REQ` は形式検査の通過のみ | real・must-fix・採用 | 「答え」「初回実配送の証拠」1・2、「完走の記録」、「主張しないこと」を 6 / 1 / 1 に分けて書き直した |
| 2 | `reason completed` は signal 配送なしの証明ではない (trap 観測なし + walltime 未到達、F1012 の SIG_IGN 継承を否定できない) | real・must-fix・採用 | 同上の signal の記述を「trap による観測記録なし・配送の有無は未判定」に限定した |
| 3 | handoff の段 1 brief (21:35 JST) と段 4 裁定 (21:36 JST) の時刻が実投入 (21:32 JST) より後 — 事前判断と事後転記を区別できない | real・should・採用 | 親が時刻を `date` で採らず推定して書いた再発 (F1 型、memory 既知)。handoff に erratum。**brief・裁定の本文を書いた時刻は記録されておらず、handoff は版管理されていないので、「brief は `git rev-parse main` の 12:27:09Z より前、裁定は dry-run meta 21:31:27 JST の後・実投入 launcher 開始 21:32:09 JST (`submit-rr95-w1.meta`) の前」という順序は親の操作列の申告であって、証拠から独立には確定できない** (焦点再レビューの指摘)。親は元の時刻を推定で記した誤りと認めて訂正した。一次資料で確認できるのは実投入の時刻であり、brief・裁定の実記載時刻と事前性は独立には確定できない (3 巡目の指摘で「値の誤りは証拠で確定」も撤回)。failures fragment で F1 に再発を追記 |
| 4 | DW-O09 を「凍結 bytes に触れない」だけで不成立とした理由が不十分 (docs-only でも成立しうる) | real・should・採用 | 理由を「変更 file は新規のみ (段 1 時点では README + worklog fragment の 2 本、最終的には verbatim 6 file (レビュー 3 本 + prompt 3 本) と failures fragment を加えた 9 本) で既存 file の bytes を変えない」に改めた。pin 検索: 1 巡目レビューが当初 2 path で `git grep` 0 件、3 巡目の後に親が wave dir 名 `t2288-floor-pair-w1` と fragment 名 `2026-09-19-dev-wave-t2288-floor-pair-w1` で tracked file を `git grep` して 0 件 (9 本すべて未 tracked の新規 path、verbatim は同 dir 配下)。手順は変えない |
| 5 | handoff の rr50 Elapse 4141S は誤り (正 4145S、README は正しい) | real・should・採用 | handoff を訂正 |
| 6 | `run-watch.sh` は JSONL 名の `c1` も `c2` へ要変更 | real・should・採用 | 申し送り 5 に明記 |
| 7 | 「queue 待ちゼロ」は断定できない (証拠は投入→開始 8 秒) | real・should・採用 | 「投入から開始まで 8 秒、内訳は分離できない」に改めた |
| 8 | `qsub-f` は path の誤記 | real・nit・採用 | `qstat-f` に訂正 |
| 9 | dry-run dir は `pre-submit.json` も持つ | real・nit・採用 | 申し送り 4 を訂正 |
| 10 | handoff の「script を書かない」は repo 外 launcher 6 本と食い違う | real・nit・採用 | 「repo 内実装面を書かない、repo 外運用 launcher は作る」に訂正 |
| 11〜15 | place の site 検査、header の書出し順、accounting の出先、fragment 文法、軽量版の妥当性への疑い | refuted (記録のみ) | 変更なし |

レビューが独立に確定していないと明記した点 (fragment の base digest と land 先台帳の一致、ff-only の実行、履歴上の事後改変の有無) は
段 9 の land (fold の base 照合) と本 wave の commit 履歴が担う。

**焦点再レビュー (2 巡目、`verbatim/s6-focus.md`、DW-O16 の closed / partial / regressed 表):** 派生値 (6 / 1 / 1、8 秒 ×3、4145S、60 cell、
378 行、372 / 744 / 1,116 / 3,720、30 / 24 本、11 call / 246 秒、mtime 3 点) は原データから再計算して全件一致、「完走の記録」表の 18 cell を
抜き取り再照合して回帰 0。判定は closed 6 (所見 5〜10) / partial 4 (所見 1〜4) / regressed 0 で NO-GO: 所見 1・2 は見出し (`signal なし`) と
handoff の旧断定が残存、所見 3 は「順序を追認」が証拠だけでは成立しない (brief・裁定の記載時刻は記録されていない)、所見 4 は「新規 2 本」が
failures fragment 追加後の現況と不一致。新規 = 所見 16 (should: failures fragment の `prepared_epoch` を 21:32:09 と誤記、正しくは
1789821131 = 21:32:11 JST で 21:32:09 は launcher の meta 開始時刻)、所見 17 (nit: 「新規 2 本」)。親はすべて real・採用で訂正した
(本表の所見 3・4 の反映列も書き直した)。

**焦点再レビュー (3 巡目、`verbatim/s6-focus2.md`、DW-O16 の上限):** 旧断定の全文検索は「現在の事実として肯定する旧断定 0 件」(引用としての
残存 3 箇所は履歴)。所見 1・2・16・17 closed、5〜10 に回帰なし、2 巡目の転記に誤りなし。partial 2 = 所見 3 (「値の誤りは証拠で確定」が
依然過大)・所見 4 (pin 検索の実績は当初 2 path のみ)、新規 18 (should: worklog fragment 稿の「3 巡目で閉じた」が判定の先取り)。
**親の裁定 (DW-O16、3 巡で打切り):** 3 件とも real・採用。所見 3 は本表の反映列を上記の形 (誤りを認めて訂正、実記載時刻と事前性は独立には
確定できない) に改め、所見 4 は親が tracked file への `git grep` を実測して 0 件を記録、所見 18 は fragment を 3 巡の実結果に書き直した。
残る所見なし。実装面ゼロなので変異による裏取りは無い (免除)。

## 主張しないこと

- 床値の生成・採用・§5 記入・集約 (D1974) は行っていない。窓 JSONL の値を比較・解釈していない。
- terminal `complete`・62 / 62・drop 0 は driver が書いた記録であって、n = 62 の充足の確認、欠測率 (campaign 合算 5%) の判定、w2 との
  24 時間以上の分離、環境の一致は証拠確認者 (D1641 項 1、申し送り 6) が実 timestamp で確認する事項である。本 wave は w1 の投入と初回実配送・
  完走の観測までを担い、証拠確認者の判定を代行しない。
- driver の gate の強度、spec の事前性の機械証明、計算ノードの時計の安定、別 node 並走の影響、SIGTERM が配送されたか・SIG_IGN で継承されるか
  否か (F1012) は本走では検証していない (trap の観測記録が無いだけで、配送の有無は判定できない)。
- `FP_ELAPSTIM_REQ` の受信値が `24:00:00` だったこと (job 側に記録が無い)。
- `place` の policy 一致検査が将来の protocol 改訂後も通ることは主張しない (w2 は同じ submit-tree を使うので再 place は不要だが、
  finalize 前に checkout を作り直す場合は再 place と policy 一致が要る)。

## 後続 wave への申し送り

1. **w2 は 2026-09-29T00:00:00Z 以降、`now + 24h <= 2026-10-07T00:00:00Z` の間に、同じ submit-tree から `bash tools/pegasus/submit_floor_pair.sh
   --workload <wl> --window w2` で投げる。** submit-tree の HEAD (`H`) を進めない・削除しない・`git worktree unlock` しない。submitter は w1 JSONL
   の header `loaded_head` と現 HEAD の一致を qsub 前に検査する。
2. **finalize は w1・w2 両方の terminal の後、同じ submit-tree から `--finalize`。** walltime 30 分。`incomplete` terminal の窓からも
   `not_generated_*` summary が create-only で 1 回だけ作られる (失敗の記録) ので、両窓の terminal を先に読んでから投げる。
3. w1 の窓 JSONL 3 本は submit-tree の `output/env/pegasus/floor-pair/t2288-f1/window__…-c1.jsonl` に untracked のまま残る (mode 0600)。
   3 段が終わるまで commit しない (申し送り 2)。commit は finalize 後の wave が submit-tree 上で行い、main へ merge する。
4. 証拠 dir 6 本 (dry-run 3 + 実投入 3) は `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/<nonce>/`。dry-run の 3 本は
   `pre-submit.json` と `submit-receipt.json` (`status dry_run`) の 2 file だけを持ち、qsub・job body・scheduler の file は無い。削除しない。
5. job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/` に起動 script (`run-verify.sh` / `run-lock.sh` / `run-place.sh` /
   `run-submit.sh` / `run-watch.sh` / `detach.sh`)、submitter の stdout / stderr / rc、`observations/qstat-f-*.txt`、`watch.log` が残る。
   w2 は `run-submit.sh <wl> w2` でそのまま使える。`run-watch.sh` は request ID・nonce に加えて JSONL 名の `-c1.jsonl` を `-c2.jsonl` へ
   書き換えないと w1 の 126 行を報告し続ける。
6. 証拠確認者 (申し送り 6) の 24 時間分離の基準: w1 の最終 session `finished_at` は rr95 13:41:57Z / rr50 13:41:29Z / rr5 13:49:12Z
   (2026-09-19)。w2 の窓は 09-29T00:00Z 以降なので分離は窓の定義で満たされるが、確認は実 timestamp で行う。
7. 所要の実測: 1 窓 job ≈ 69〜77 分 (queue 待ちなしの場合)。w2 の投入は窓の末端 (10-07T00:00Z) から `24 h + queue 待ち` 以上手前に行う
   (submitter の `now + 86400 <= not_after` は job body でも再検査され、外れると rc=4 で create-only path を残して止まる)。

## 生証拠

- submitter receipt: `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/{3fb5c77cc501ee3f7917becd093dfe39,8b8dc69bffae50e5e14d574ea3e99153,91c65a96c0d2dcfd5869acc63e60b0e9}/{pre-submit.json,submit-receipt.json,qsub.rc,qsub.stdout,qsub.stderr}`
- job body の出力: 同 dir の `driver.stdout` / `driver.stderr` / `job-result.json`、scheduler の `scheduler.stdout` / `scheduler.stderr`
- 窓 JSONL: `<submit-tree>/output/env/pegasus/floor-pair/t2288-f1/window__env-pegasus__protocol-silo__threads-48__workload-{rr95,rr50,rr5}-s0.9-rmw0__campaign-t2288-f1-<wl>-c1.jsonl`
- `qstat -f` の初期観測: `<job dir>/observations/qstat-f-{10711,10712,10713}-initial.txt`
- watcher log: `<job dir>/watch.log` (5 分周期、qstat の STT / Elapse と JSONL 行数)
- 段 6 の逐語 (本 dir `verbatim/`): `s6-review.md` / `s6-review-prompt.md` (1 巡目)、`s6-focus.md` / `s6-focus-prompt.md` (2 巡目)、
  `s6-focus2.md` / `s6-focus2-prompt.md` (3 巡目)。receipt は `<job dir>/codex/artifacts/dev-wave-t2288-floor-pair-w1/<job-id>/receipt.json`
