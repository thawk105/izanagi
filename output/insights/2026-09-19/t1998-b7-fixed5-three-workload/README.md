# 採用候補 fixed 5 µs を 3 workload で同時期に測り、床値超の退行を判定した wave の記録 (2026-09-19)

wave `dev-wave-t1998-three-workload-regression` (背景 job f6bf33bb、branch `worktree-dev-wave-t1998-three-workload-regression`)。
**結果の正本は results 系列稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` と、
権威 bytes `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/` である。** 本 README は wave の工程・裁定・検査の記録であり、
数値の出所ではない。

## 0. 何をしたか (1 段落)

ユーザー裁定 (2026-09-19) に従い、T-1998 事前登録の採用 arm (静的 backoff fixed 5 µs) を stock (backoff 無し) と対にして
rr5 / rr50 / rr95 の 3 workload で同一 attempt・同時期に測り、D1639 の between-run 床値と対差を比べた。機構は A-2 / A-6 の
certification 経路を descriptive に使い、新 study `paper-story-b7-fixed5-regression` を closed set へ 1 path 足した
(A-6 追加 60605bec3 と同形、実装 commit `c18a80967`)。結果: write-heavy +67.8968% / balanced +12.6717% は退行なし、
**read-heavy −11.3787% は床値超の退行**。6 cell とも certified・anomaly 0。B-7 の要件充足は判定しない (D2044 項 3)。

## 1. 工程

| 段 | 内容 | 所在 |
|---|---|---|
| 1 brief | 純増 = 同一候補の 3 workload 同時期測定 + 床値判定。(P1)〜(P7) を攻撃対象として提示。床値 3 値を JSON 全桁で固定 | `verbatim/brief.md` |
| 2 plan | codex read-only。module 5 箇所 + submitter **2 箇所** (:273 と receipt 再構成 :365) + tests。3 workload の finish→collect→materialize が既存経路で通ることを行番号で確認 | `verbatim/plan-out.md` |
| 3 consult ×2 | レンズ A (受理集合・pin・正しさ境界): real 3 (P1 の argv 一致は不成立、prereg digest 一致は機構が保証しない、A-6 73 分は nodes=1)。レンズ B (実効性・過剰): real 5 (同一 build の読み替え、同時期性の過大主張、判定不能行の未固定、partial 時の完了扱い、fp-* lock 前提)。純増あり・裁定パッケージ候補なし | `verbatim/consult-{a,b}-out.md` |
| 4 裁定 | 所見 7 件採用・2 件 refuted (plan / brief 支持)。判定規則 v2・再投入規則を結果前に固定。変異 M1〜M8 登録 | `verbatim/ruling-s4.md` |
| 5 author | codex workspace-write、別 worktree `.codex/worktrees/t1998-author`。sandbox で qstat 不在のため pytest 未実走と申告。親が所有 patch を展開し実走: 対象 2 file **307 passed** (login bounded local)、meta 5 file **1071 passed / 6 skipped** (計算ノード dispatch) | `verbatim/author-out.md`、`evidence/tests-{focus,meta}-1.log` |
| 実装 commit | `c18a80967` (policy + module + submitter + tests、5 file、376+/12−)。message-file 検査 rc=0、全史 provenance 監査 11631 件・新規違反なし | git |
| 計測 | submit-tree (detached branch `submit-t1998-b7-fixed5`、HEAD c18a80967、hydrate rc=0) から attempt `b7f5-20260919a` を 22:32 JST 投入。3 request 各 5 node。rr5 386 s / rr50 841 s / rr95 1218 s、driver_rc 0 × 3。finish-group rc=0 | `evidence/submit.log`、`evidence/finish-group.log` |
| collect | 1 回目 (wave worktree の module から) は rc=2 `qsub -v is not bound to workload and current pin` — submission receipt が **submit-tree の policy 絶対 path** を束縛するため。2 回目は submit-tree の module で `--repo-root` だけ wave worktree にして rc=0 | `evidence/collect-attempt{1,2}.log` |
| 6 review ×2 | must-fix 0 / should-fix 1 (変異台帳の期待集合の訂正のみ)。レビュー A が M1〜M8 の静的期待集合を導出 | `verbatim/review-{a,b}-out.md` |
| 変異 | probe (全件 SURVIVED 期待) で観測集合を採取 → 静的導出と完全一致 → 本走 (KILLED 期待) | §3 |
| 7 記録 | results 稿、README 行、spool fragment (worklog 更新 [T-2610]、decisions 1 件)、本 README | 記録 commit |

## 2. 裁定で訂正した親の前提 (段 3 → 段 4)

- 「同一 build」→「同一候補・同一ソース条件 (genome・define・toolchain・patch 適用下の source bytes digest) から workload ごとに
  別 build」。稿は binary digest を列挙し「同一 binary」を書かない。
- 「A-6 は nodes=5 で 73 分」→ 誤り。A-6 attempt の receipt は `-b 1`。nodes=5 の根拠は t2489 probe (rr5/rr50 で 4.17 倍短縮) と D2148 項 5。
  実測: 本 attempt は nodes=5 で rr95 1218 s (A-6 nodes=1 の 4382 s より短いが、候補も日付も違うので倍率の主張はしない)。
- 「fp-* 3 request が bench.lock を共有する」→ 現 checkout の floor_pair 経路は bench_lock を取らない。前提を撤回。
- 「同一 attempt なら対照は数分差」→ rr95 は stock → adopted が 11 分 4 秒。稿は bench 時刻を載せ、文字どおりの同時性を主張しない。

## 3. 変異 matrix

spec `evidence/mutations-probe.json` (probe、全件 SURVIVED 期待) と `evidence/mutations-real.json` (本走、KILLED 期待)。
runner: `tools/mutation_worktree.py --source-repo <独立 clone、main=c18a80967> --runner-mode dispatch` +
`python3 tools/run_tests.py --force-dispatch -q -rf <対象 2 file>`。probe の観測集合 (job dir `mutation-probe-results.json`) は
レビュー A の静的導出と完全一致した。

| id | 置換 | probe 観測 (赤 node 数) | 本走の期待 | 本走の結果 |
|---|---|---|---|---|
| M1 新 policy の rr50-fixed5 `BACKOFF_FIXED` 5→10 | policy JSON | 14 | KILLED | **KILLED** (14 node 完全一致) |
| M2 `policy_shapes` (3,6)→(2,4) | module | 14 | KILLED | **KILLED** (14 node 完全一致) |
| M3 closed set から B7 path を外す | module | 7 | KILLED | **KILLED** (7 node 完全一致) |
| M4 `_qsub_job_name` の B7 entry を外す | module | 10 | KILLED | **KILLED** (10 node 完全一致) |
| M5 `_qsub_environment_keys` で B7 を POLICY_PATH 不要側へ | module | 6 | KILLED | **KILLED** (6 node 完全一致) |
| M6 submitter :273 の条件から B7 を外す | submitter (shell) | 1 (`test_b7_submitter_three_requests`、実 argv 比較) | KILLED | **KILLED** (1 node 完全一致) |
| M7 submitter :365 の receipt 再構成から B7 を外す | submitter (埋込 python) | 1 (同上、env 集合検証) | KILLED | **KILLED** (1 node 完全一致) |
| M8 help 文言 three→two | module | 0 | SURVIVED (等価、harness の SURVIVED 検出の正例) | **SURVIVED** (期待どおり、赤 0) |

単一理由性: M1 は 14 node が赤になるが、機構側の拒否層は `M:609-616` の adopted 整合検査 1 つ (bytes pin test は別層 = literal pin。
レビュー A が「全 node が単一の検査で落ちるという意味ではない」と注記)。M2 の `[genome]` 負例は期待例外文言が変わるための赤。
M6 は receipt の env が正常なままなので `J:1372` の実 argv 比較だけが検出する。

本走 (`evidence/mutation-real-results.json`、wrapper receipt `evidence/mutation-real-wrapper-receipt.json`): baseline PASSED、
8/8 期待一致 (7 KILLED、等価 1 SURVIVED)、MISMATCH / PARSE_ERROR / TIMEOUT 0、`shared_snapshot_matches = true`、
`terminal_ledger = true`。probe (`evidence/mutation-probe-results.json`) は 7 MISMATCH + 1 SURVIVED で、その観測 node が
本走の期待集合である。数値契約 (閉集合の 1 path 追加) の検出であり、任意 policy の拒否を主張しない。

## 4. 受入

受入全走は本 README を含む記録 commit の後に `tools/dev_wave_wait.py acceptance` で 1 回だけ投入する
(land は tested tip をそのまま取り込むため、記録 commit を受入より前に置く)。結果は land 受領証 (`docs/spool/FOLDED.md` の
`tested_tip`) と job dir `acceptance-receipt-*.json` に残り、本 README には書けない。受入前に緑を確認した安い関門:
全史 provenance 監査 (実装 commit 時点 11631 件・新規違反なし、記録 commit 後に再走)、`check_docs.py` 違反なし、
`spool_fold.py --dry-run` planned、対象 2 test file 307 passed、meta 5 file 1071 passed / 6 skipped。

## 5. 主張の上限

- 1 attempt。反復・有意差・機序・他 workload 点への転移は無い。
- 「同一候補」は source bytes・define・toolchain・pin まで。binary は別 build。
- 同時期性は「同 attempt・33 分 38 秒の窓・各 workload で stock 直後に adopted」まで。
- 床値判定は記述的 (1 arm の CV と 2 arm の比を直接比較、ユーザー裁定どおり)。
- B-7 充足・certification 昇格は判定しない。

## 6. 再現条件

| 項目 | 値 |
|---|---|
| 実装 commit | `c18a80967ed3d9a901b395116c23f90d6a554b36` (local main 657e1e5a7 の上) |
| policy | `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` (sha256 `c6b24050d17c4bc552d254ce65e328b3a6edca919387b5720b4e025ea78b0df1`、protocol `5653d439714e11df9de8f2bd3e697c038d0cfbb538c5f703e0749facbfe2998c`) |
| 投入 | `tools/pegasus/submit_paper_story_a2_certification.sh --policy orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json --attempt-id b7f5-20260919a --ccbench-root <tree>/external/ccbench --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps --third-party-source-root <tree>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` (submit-tree = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1998-b7-fixed5/submit-tree`) |
| collect | submit-tree で `python3 -B -m orchestrator.campaign.paper_story_a2_certification --policy <相対 path> collect --attempt-root <root> --current-pin 511c953 --acquisition-receipt <root>/receipts/acquisition.json --repo-root <wave worktree>` |
| durable root | `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/` |
| 外からの採取 | job dir の `qstat-samples.log` (60 秒間隔の `qstat -f`、3 request) |
| 子の成果物 | `verbatim/` (prompt と出力の逐語)、job dir `/home/SFC/tanab/.claude/jobs/f6bf33bb/artifacts/` (receipt) |
