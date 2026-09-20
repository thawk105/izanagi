# [T-2802] floor attempt ledger 回復の二乗構造を per-call memo で直す — 受理集合不変の証拠と受入 shard の A/B 隣接対 3 組

- authority: none
- default_effect: no-state-change
- 依頼: `orchestrator/campaign/s8b_holdout_admission.py` の `_floor_attempt_recovery_candidate_locked` が attempt 数に対し二乗になる構造を直し、受入 worker 時間 (`test_s8b_floor_campaign.py` 約 90 node × 5.8 s) を削る。受理集合 (拒否・受理の判定) を変えないことを変異 (正例・負例) で示し、効果は受入 shard の隣接対比較 (T-2766 の型) で実測する。局所修正だけ。起票は worklog 1704 の `[T-2802]`。
- wave: dev-wave-t2802-floor-attempt-recovery (branch `worktree-dev-wave-t2802-floor-attempt-recovery`)。着手時 local main `b7f970dfa`。実装 commit `06d101fee` (production + test)、段 6 fix commit `7adf2eea6` (test のみ) = **測定 tip B**。
- 原ログ: job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/` (brief、裁定と erratum 1〜5、prompt、子の報告、焦点走 log、差分 probe、変異 spec/台帳、A/B `runs/` と `analysis/`、診断走 `diag-t080/`)、claude job dir `/home/SFC/tanab/.claude/jobs/04be94b6/`。逐語は本 dir の `verbatim/`。
- 設計判断: decisions fragment `docs/spool/decisions/2026-09-20-dev-wave-t2802-floor-attempt-recovery-2.md` の 2 件 (slug `floor-attempt-recovery-per-call-memo` = per-call memo の採用と cross-call cache の不採用、`floor-recovery-ab-measurement-contract` = 固定 2 tree の隣接対比較の測定契約。D 番号は land の fold が付ける)。

## 1. 結論 (先に)

1. **修正は狙った費用を消した。** 二乗回復の載る floor node 群 (測定前に凍結した `S_mid` 65 node) の worker 秒は、有効 3 対すべてで A ≈ 400 s → B ≈ 123 s (対差 +276.7 / +275.1 / +276.8 s、65 node 中 64〜65 node が各 ≥ 3 s 短縮)。
2. **事前登録の一次判定は `effect-not-established`。** 一次指標 `F` (凍結 `S_all` 523 node の合計) は 3 対とも B の方が大きい (ΔF = −614 / −1315 / −1335 s、中央値 −1315 s)。判定式は結果を見て変えていない。
3. **B で増えたのは floor の snapshot 系 19〜22 node の実 repo lock 待ち**で、lock 保持者は floor file 外の `test_s8b_oracle_driver` t080 群 (shared base 構築が A 113〜164 s → B 189〜245 s)。走内で複数 node に同じ量 (例 −114.4 s × 5) が乗る = 共有待ち。output/ の残骸差 (25,740 vs 25,762 file) と `git status` 所要 (両 tree 3〜9 s) では説明できず、t080 shared base を単独で走らせる診断走 (§5.4) では A 60〜62 s / B 62〜68 s と tree 差がない。よって B の増分は tree 固有の性質ではなく同居負荷 (配布・node・共有 FS) 依存で、本 wave の資料では node 起因と配布起因を分離できない。
4. 受理集合不変: 差分 probe 40 状態一致 + 正例 2 状態検出、変異 8/8 KILLED (等価 1 SURVIVED)、焦点走 2522 + 293 passed / 0 failed。
5. 採否はユーザー裁定 (§6)。実装は wave branch の tip に含めて land する (production の受理集合は不変、性能は S_mid の実測どおり短縮、一次判定は未確立)。

## 2. 機序と修正

- 二乗の機序: `consume_attempt_ticket` (attempt ごと 1 回) → `_recover_floor_attempt_ledger_locked` → `_floor_attempt_recovery_candidate_locked` が、target + 既存 marker 全件 + attempt ledger 全行を `_canonical_floor_attempt_ledger_row` で完全再導出する。再導出 1 回ごとに claim 文書の読取 + main ledger の全読 (+ v1 経路では main 行ごとの sha256) が走る。第 i 回消費では 1 + 2(i−1) 回 → N 回で N² 回 (98 attempt で 9,604 回、profile 9.9 s 中 9.1 s、`output/insights/2026-09-19/acceptance-worker-time-trim/`)。代表 node は measurement-generation 経路 (v1 の行ごと sha256 は代表 node の直接の律速ではない — 段 2 plan の訂正)。
- 修正 (段 4 裁定 §2、実装 `06d101fee`): 候補関数のローカルに呼び出し内 context (成功済み claim 射影の memo + main ledger 生行列の遅延 slot) を 1 個作り、target / 各 marker / 各 A 行の 3 箇所だけ context 対応 helper を通す。memo に入るのは marker equality まで通った射影だけ。hit でも marker の exact shape・schema・role・digest・attempt_id、attempt coverage、constructor、marker 全体との equality (MUT-A2) を毎回行う。main ledger の生読取は従来の読取位置に初めて到達したときだけ (eager 先読みなし)。既存 signature の 3 関数は context なしの wrapper。走査順・filter・canonical filename・identity 重複・A 行の marker 照合・completed 拒否 (MUT-A6)・error message は不変。production +133/−25 行、新規 helper 7 (`_FloorAttemptClaimProjection`、`_FloorAttemptRecoveryContext`、`*_with_context` ×3、`_derive_*` ×2)。
- 残る費用 (線形化ではない): marker file 読取 k 件/呼、A ledger 全読、constructor・比較 q = 1 + k + a 回、directory sort、claim ごとの projection (c 件)。claim 数が attempt 数と共に増える条件では projection 部分にも二乗性が残る。

## 3. 受理集合不変の証拠

| 証拠 | 結果 |
|---|---|
| 差分 probe (`verbatim/t2802_diff_probe.py`、変更前 module `b7f970dfa` の逐語を `orchestrator.campaign._t2802_base_admission` の別名で load し、同じ root 状態で新旧の候補関数の (戻り値 / 例外型 / message 全文) を両順序で比較) | 40 状態すべて一致 (`diff-probe/run2-40states.json`)。状態: marker 不在 / M+A− / M+A+、同 claim 2〜3 attempt の消費列 (memo hit)、2 件目以降の非 target marker の改竄 4 型、A 行の改竄 3 型、completed、main records 改竄、claim 非 canonical bytes、consumed の symlink、複数 claim、2 claim × 2 attempt (marker・A 行双方の hit)、非 target の coverage 不正、legacy v1/v2、正常→改竄→再呼出し |
| 差分 probe の正例 (DW-O19、M1 形の一時変異 = memo hit で marker の campaign_run_id を信用、`diff-probe/positive-control-M1-*.log`) | 24 状態中 2 状態 (`e-later-nontarget-marker-campaign_run_id`、`f-later-A-campaign_run_id`) で不一致を検出、rc=1。復元後の blob = HEAD |
| 焦点走 0 / 2 (計算ノード、変更 test file 単独) | 282 passed (実装後) / 293 passed (fix 後、110 case) / 0 failed |
| 焦点走 1 (consumer 13 file、計算ノード request 11898、304 s) | 2522 passed / 16 skipped / 0 failed |
| 恒久 test (`test_s8b_holdout_admission.py` +615 行、既存期待値は不変) | 複数 claim・複数 attempt の消費列 (期待文書は 13 key literal + fixture 出所、production の文書 constructor に依存しない)、2 件目以降の marker / A 行の負例 (固定 literal)、claim エラーが main 読取に先行する順序、main 検査の射程 (legacy 読取互換 fixture)、memo の寿命と読取回数 (実物へ委譲する観測 wrapper、claim ごと 1 回・main 1 回・2 回目で再読)、unsafe entry、bytes 検査が filter に先行、projection 入口・attempt_ids・main 行数の負例 |
| 静的到達不能 (負例で埋めない) | A≠marker (H:5296)、target≠canonical_target (H:5304)、marker identity 重複 (H:5276): 同 identity は同じ canonical 文書に再導出される |
| lock 契約の限界 (記録) | advisory lock を無視する書込み・一過性 I/O では実行履歴同値を保証しない。lock なしで候補関数に到達する production 経路はない (validate は H:5082 入口・H:5094 lock)。context は戻り値・closure・module state に公開せず次回呼出しで再利用しない (traceback frame からの参照は対象外) |

## 4. 変異 matrix (DW-M01、独立 clone D1009 `mutation-source` main = `7adf2eea6`、`tools/mutation_worktree.py --runner-mode dispatch`、runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_s8b_holdout_admission.py -q -rf`)

probe 走 (全件 SURVIVED 期待・node 空、spec sha `42bfbd40…`、裁定 erratum 2 の理由) で観測集合を採り、final 走 (spec sha `d5021149…`、`mutation-final-results.json`) で KILLED 期待の完全集合と照合した。**final: KILLED 8 / SURVIVED 1 / MISMATCH 0、matching 9/9、baseline PASSED**、wrapper receipt は `shared_snapshot_matches` / `terminal_ledger` / `teardown_completed` = true、resolved_commit `7adf2eea6`。

| ID | 変異 | 観測 = 期待 node | 最初の拒否位置 | 新規検出力 |
|---|---|---|---|---|
| M1 | memo hit 時に marker の `campaign_run_id` で期待文書を上書き (generation) | 3: 既存 `test_cut6_recovery_requires_exact_marker_rederived_from_claim[claim-mismatch]` + 新規 `test_cut6_later_marker_rejected[claim-mismatch]`、`test_cut6_later_attempt_row_rejected[claim-mismatch]` | marker ≠ expected (MUT-A2) | 新規 2 node は専有だが既存 test も別 message で赤 → 専有に数えない |
| M3 | hit 時の coverage 検査を省く | 1: 新規 `test_cut6_later_marker_rejected[attempt-not-covered]` | coverage | 新規 |
| M4 | canonical filename 比較を省く | 1: 新規 `test_cut6_later_marker_rejected[noncanonical-filename]` | filename | 新規 |
| M5 | A identity 重複検査を省く | 1: 新規 `test_cut6_later_attempt_row_rejected[duplicate]` | A duplicate identity | 新規 |
| M6g | generation の `main != expected_main` を省く | 3: 既存 `test_floor_marker_capability_requires_exactly_one_matching_main_row[mismatch]` + 新規 `test_cut6_main_validation_scope[records-generation]`、`test_cut6_projection_once_per_claim_per_call[main]` | main ≠ expected_main | 新規 2 + 既存 1 |
| M6v | v1 の `main != expected_main` を省く | 3: 新規 `test_cut6_legacy_projection_once_per_claim_per_call[main]`、`test_cut6_main_validation_scope[records-v1]`、`[records-v2]` | 同上 (v1) | 新規 |
| M7 | completed 拒否 (MUT-A6) を省く | 1: 既存 `test_cut6_completed_session_forbids_reissue_of_same_attempt` | MUT-A6 | 既存 |
| M8 | memo を root key の module dict へ昇格 (呼び出し跨ぎ保持) | 4: 新規 `test_cut6_projection_once_per_claim_per_call[claim]`/`[main]`、`test_cut6_legacy_projection_once_per_claim_per_call[claim]`/`[main]` | 読取回数 (改竄拒否には帰属させない、レビュー B-S2) | 新規 |
| P0 | A 行 identity の `str(...)` を外す (等価) | SURVIVED (両走) | — | — |

不採用: plan の M2 (exact-key 省略 + extra key 破棄、複合変異で既存 test が検出)。

## 5. A/B 対比較 (段 4 裁定 §6 + erratum 1・3・4・5、事前登録)

### 5.1 測定手順 (実際に実行した手順)

- **条件:** A = `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-base-a` (HEAD `b7f970dfa`、着手時 local main、clean)。B = wave worktree (HEAD `7adf2eea6` = 実装 commit + test fix commit、docs なし、clean)。tracked 差分は 2 file (+748/−25、`runs-tracked-diff-stat.txt`)。`measurement-tips.json` で系列開始前に固定。**同一 SHA 比較ではなく固定した 2 tree の比較**であり、D2068 の「同一 tree 内で方式を交互」条件は満たさない (path・pyc・page cache・node の差は残る)。
- **投入形:** 各 worktree から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入 (待ち手・lease・merge・receipt なし)。`PYTHONDONTWRITEBYTECODE` unset。門番 = 他 session の受入待ち手 ≤ 1 かつ load1 < 30 を 100〜140 秒周期で 2 回連続 + 0〜45 秒乱数 → 再判定 (erratum 3 以後は RUN dir 作成の直前にもう一度判定)。job dir の flock で直列化。投入前後に HEAD == 条件別 SHA と clean を照合。launcher / 系列 / 集計器は `verbatim/` (Codex author + fix 4 本、`probe/SHA256SUMS.txt`)。
- **warm-up:** 系列開始前に両 tree で計算ノード collect-only 1 走 (`PYTHONDONTWRITEBYTECODE=` を空で export、A: request 11950、B: request 11949、pyc 0/1 → 394、HEAD/clean 前後一致、`warm-A.json` / `warm-B.json`)。page cache・fixture の warm は主張しない。
- **順序:** slot 1 = A,B / slot 2 = B,A / slot 3 = A,B。無効対は同順序で対全体を取り直す。有効 3 対で固定終了、全投入 12 走上限。
- **無効条件・赤の扱い:** 走 = rc≠0 / failed・error > 0 / 成果物欠落・sha 不一致 / `S_all` 不一致 (各 node 1 件・有限非負 time) / HEAD・clean 不一致 / 投入時の門番条件違反 (`gate metadata`)。対 = 走の無効・skipped 集合の対内不一致・系列文法違反。赤は親が本文で分類 (`classification.json`: infra / impl / unclassified)、`impl` / `unclassified` は系列無効。
- **一次指標:** `F` = 3 shard の junit `testcase` のうち `S_all` (凍結 523 nodeid、`floor-subset-frozen.json` sha256 `2bc360b9…`、うち 3 node は常時 skipped で time ≈ 0、対内で集合一致を要求) の `time` 合計。`ΔF = F_A − F_B`。判定 (i) 3 対とも ΔF > 0 かつ中央値 ≥ 200 s → 方向一致・実用閾値以上、(ii) 3 対とも > 0 だが < 200 → 方向一致・閾値未満、(iii) それ以外 → 効果未確立。200 s は実用値でありノイズ由来でない (T-2766 の同一 code の floor 対差は 22 / −211 / 60 s)。
- **補助指標:** `ΔF_mid` (`S_mid` 65 node = T-2766 の 6 走の中央値が 4〜12 s の node、`sum_mid_median` 400.6 s)、`ΔF_long` (`S_long` 22 node、中央値 > 12 s)、nodeid 対差の分布 (中央値、`Δ_n ≥ 3 s` の件数と合計)、`W_max = max(W_0, W_1, W_2)`、`W_0`、最忙 worker。補助は一次の代替にしない。

### 5.2 走表 (10 走、有効 6 走。時刻 JST、W = shard の JUnit testsuite time、F = S_all 523 node の worker 秒)

| 走 | 条件 | 投入 → 完了 | shard-0 node | 有効 | F | F_mid | F_long | W_0 | W_1 | W_2 | 最忙 worker (item) | 他 leader / load1 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 01-A | A | 09:46 → 10:11 | bnode010 | 有効 (対 1 は 02-B 無効で不採用) | 2664.0 | 403.7 | 2219.8 | 498.3 | 230.5 | 201.2 | gw40 (79) | 1 / 7.08 |
| 02-B | B | 10:35 → 11:00 | — | **無効** `gate metadata` (投入時 leaders 2 > 1、erratum 3、infra) | — | — | — | — | — | — | — | 2 / 10.75 |
| 03-A | A | 11:25 → 11:34 | — | **無効** rc=16 `dispatch-infrastructure` (shard-2 の xdist INTERNALERROR `KeyError: <WorkerController gw30>` + timing test 1 件、A 側、erratum 4、infra) | — | — | — | — | — | — | — | 1 / 5.22 |
| 04-A | A | 11:49 → 11:50 | — | **無効** rc=16 orphan-hold latch 残存で未投入 (親の解除漏れ、erratum 5、infra) | — | — | — | — | — | — | — | 0 / 2.40 |
| 05-A | A | 11:53 → 12:06 | bnode025 | 有効 | 1853.0 | 399.4 | 1413.1 | 488.0 | 244.0 | 199.9 | gw1 (13) | 0 / 4.30 |
| 06-B | B | 12:11 → 12:32 | bnode028 | 有効 | 2467.2 | 122.6 | 2282.7 | 547.9 | 244.1 | 199.7 | gw2 (75) | 0 / 3.40 |
| 07-B | B | 12:44 → 12:52 | bnode002 | 有効 | 3014.8 | 125.6 | 2813.1 | 455.5 | 240.3 | 223.4 | gw40 (43) | 1 / 10.62 |
| 08-A | A | 12:58 → 13:09 | bnode011 | 有効 | 1699.6 | 400.7 | 1267.7 | 480.5 | 237.3 | 199.8 | gw1 (13) | 0 / 5.56 |
| 09-A | A | 13:16 → 13:37 | bnode024 | 有効 | 1987.3 | 400.8 | 1548.9 | 455.8 | 236.7 | 199.9 | gw40 (8) | 0 / 10.36 |
| 10-B | B | 13:40 → 13:50 | bnode001 | 有効 | 3322.4 | 124.0 | 3116.0 | 563.7 | 242.2 | 239.0 | gw40 (33) | 1 / 11.55 |

赤 (failed / error) は有効 6 走とも 0。skipped の floor node は 6 走とも同じ 3 件。shard-1 / shard-2 の W は A/B で同じ (240 s 級 / 200 s 級)。

### 5.3 対表と判定 (集計器 `verbatim/t2802_ab_analyze.py`、`analysis/analysis.json`)

| 対 | slot / 順序 | 走 | ΔF (A−B) | ΔF_mid | ΔF_long | ΔW_max | Δ_n の中央値 | Δ_n ≥ 3 s の node 数 / 合計 |
|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | 1 / A,B (取り直し 4 回目) | 05-A, 06-B | **−614.2** | **+276.7** | −869.6 | −59.9 | 0.0 | 65 / 291.5 |
| 2 | 2 / B,A | 07-B, 08-A | **−1315.2** | **+275.1** | −1545.4 | +25.0 | 0.0 | 64 / 285.0 |
| 3 | 3 / A,B | 09-A, 10-B | **−1335.0** | **+276.8** | −1567.1 | −107.8 | 0.0 | 64 / 286.2 |

- 判定 (事前登録): 3 対とも ΔF < 0 → **(iii) `effect-not-established`** (対差の中央値 −1315.2 s)。
- 補助: `ΔF_mid` は 3 対とも +275〜277 s (S_mid の 64〜65 node が各 ≥ 3 s 短縮、B の S_mid は 122.6〜125.6 s)。修正の狙いどおり二乗回復の費用は消えた。
- `ΔF_long` が −870〜−1567 s。B が遅い node は 19〜22 件で、`test_official_*` / `test_pilot_resume_*` / `test_real_output_snapshot_*` (いずれも `_real_output_snapshot` を呼び実 repo 読取 lock を取る node) に集中し、走内で同じ量 (例 06-B: −72.4 s × 4 node、10-B: −114.4 s × 5 node) が乗る。

### 5.4 B が遅い機序の切り分け (事前登録外の診断、判定には使わない)

- `report.json` の `session_timeline.workers[*].real_repo_lock_intervals` (実 repo 読取 lock): shard-0 の総保持 A 908〜982 s (01-A 1217) / B 1121〜1353 s。最長区間は 6 走とも worker gw15 の 1 本目で A 111〜129 s / B 194〜245 s。gw15 の 1 本目は `test_s8b_oracle_driver.py::test_t080_shared_base_builds_real_builder_once_across_processes` (t080 e2e 群の shared base 構築 = 実 repo の複製 + `git add -A`): A 113.4 / 125.4 / 132.6 / 164.1 s、B 188.9 / 237.5 / 244.7 s。t080 e2e の各 node も A 190〜196 → B 253〜282 s。**floor の F 増加は、floor file 外の t080 群が実 repo lock を長く持ち、その後ろで floor の snapshot 系 node が待った時間**である。
- 除外した仮説: output/ の残骸差 (A 25,740 file / 763.5 MB、B 25,762 file / 763.7 MB、`analysis/output-residue-count.txt`)、`git status` の所要差 (両 tree 3.2〜9.4 s、交互 3 回、`analysis/time-git-status.txt`)。
- 未分離: tree (B) 起因か node 起因か。B の 3 走の shard-0 は bnode028 / 002 / 001、A は 025 / 011 / 024 (/ 010)。診断走 (t080 shared base 1 test を両 tree から A,B,A,B の順に単独で計算ノード投入、14:05〜14:11 JST、request 12611 / 12630 / 12636 / 12643、`diag-t080/diag.log`): **A 62.34 / 60.15 s、B 62.29 / 68.18 s** (`1 passed in`) — 単独では tree 差なし。受入同居下の B の 189〜245 s は tree 固有の性質ではなく、同居負荷 (配布・node・共有 FS) に依存する。node 起因と配布起因の分離は本 wave の資料では未達。

## 6. 裁定パッケージ (提案。採用済み判断ではない) と残存限界

前提: production の受理集合は不変 (§3・§4)、狙った二乗費用は消えた (S_mid −276 s/走、3/3 対)、一次指標は方向が逆で未確立 (t080 系の lock 待ちが B で長い、原因未分離)。

| 択 | 内容 | 受理集合 | 費用 | 失う / 残る不確実性 |
|---|---|---|---|---|
| (a) land する (本 wave の既定) | 実装 + test を main に入れる。性能の主張は S_mid の実測 (−276 s/走) に限り、一次判定「未確立」と B の lock 待ち増を併記する | 触れない (差分 probe・変異で固定) | 0 (本 wave 内) | t080 系の B 側の遅れが tree 起因なら、それは本修正とは別の経路 (t080 shared base は admission を通らない) だが、同居時の合計は増えうる。次の受入全走 (待ち手経由、main tip) の floor / t080 の時間で追試できる |
| (b) 同居負荷下の機序調査を先に | t080 群の lock 保持が同居下で伸びる条件 (node・配布) を A 側にも witness を付けて調べる wave を挟み、その後 (a) | 触れない | 調査 wave 1 本 | 採用が 1 wave 遅れる。診断走 (§5.4) は単独では tree 差なしを示しており、機序が分かっても S_mid の削減量は変わらない |
| (c) land を見送る | impl branch に保存し、同一 tree (D2068 適合) の測定設計を作ってから採否 | — | 測定設計 wave 1 本 + 再測定 | 二乗費用の削減 (S_mid −276 s) を使わない |

推奨は **(a)** (受理集合不変の証拠が揃い、狙った費用は 3/3 対で消え、B で増えた費用は本修正が触らない経路の lock 待ちで、単独の診断走では tree 差がない)。

残存限界・未実測:

- 別 tree (別 path) 比較で、node も対内で異なる。D2068 の同一 tree 条件・D104 の同一 allocation は満たさない。
- 3/3 は有意差判定ではない。走間ノイズ (T-2766 同一 code の floor 対差 ±200 s 級) と同程度の効果量 (S_mid の −276 s) を対比較で見ている。
- 48w 受入と 12w profile (旧 5.8 s/node) は別条件で、比率換算しない。S_mid の A 側 400 s / 65 node ≈ 6.2 s/node、B 側 123 s / 65 node ≈ 1.9 s/node (受入 48w の同居下)。
- 12 走上限のうち 10 走を使い、無効 3 走 (infra 2 + 親の解除漏れ 1)。launcher の投入直前再判定は 03-A 以後に入れた (erratum 3)。
- 差分 probe は wave 時の資料で、恒久 CI には入れない。base module の逐語は job dir と `verbatim/` にある。

## 7. 再現資料・成果物対応

- **実装:** commit `06d101fee` (production + test) と `7adf2eea6` (test のみ、段 6 fix)。差分 2 file (+748/−25)。`git diff b7f970dfa 7adf2eea6 -- orchestrator/campaign/s8b_holdout_admission.py orchestrator/tests/test_s8b_holdout_admission.py` で再生成できる。
- **凍結 nodeid 集合:** `floor-subset-frozen.json` (sha256 `2bc360b9b1e524506cfa152ec53f2b720df726a6b1a6e9b2f245314e1df4e5d4`、生成器 `freeze_floor_subset.py` = T-2766 の 6 走の中央値)。
- **launcher・系列・warm・集計器・差分 probe:** `verbatim/` の逐語 (`probe/SHA256SUMS.txt`: run-measure.sh `5fd1f27a…`、run-series.sh `686a8bc7…`、run-warm.sh `970f118c…`、t2802_ab_analyze.py `d64b9613…`、t2802_diff_probe.py `57a4b346…`)。再集計: `python3 t2802_ab_analyze.py --runs-root <job dir>/runs --frozen floor-subset-frozen.json --tips measurement-tips.json --out <dir>`。
- **raw 成果物 (job dir):** `runs/<NN>-<X>/{run.json, env.txt, chain.log, gate.log, child.log, classification.json (無効走), session/shard-{0,1,2}/{junit.xml, report.json, dispatch/receipt.json}, session/SHA256SUMS}`、`analysis/{analysis.json, analysis.md, output-residue-count.txt, time-git-status.txt}`、`diag-t080/`、`warm-{A,B}.json`、`mutation-{probe,final}-{results,attempts}.json` と wrapper receipt、`diff-probe/`、`focus/`、`codex/` (prompt・報告・patch)。本 dir の `runs/` は run.json / chain.log / classification.json の写し、`analysis/` は analysis.json の射影 (node 対差を含む) と md。
- **変異:** `mutation-spec-probe.json` (sha `42bfbd40…`)、`mutation-spec-final.json` (sha `d5021149…`)、`mutation-expected-nodes.json`、台帳と receipt。
- **逐語の正規化:** `verbatim/` の 5 file (s2-plan、s3-consult-A/B、s6-review-B、probe-source) は `git diff --check` 抵触の行末空白 (markdown の 2 空白改行) と EOF 空行を可視文字不変で除去した。原文 sha256・byte 数・除去接尾辞・復元法は `verbatim-normalization.json` (DW-S07、D88)。`SHA256SUMS.txt` は正規化後の値。

## 8. レビュー・裁定の逐語

`verbatim/`: s1-brief、s2-plan、s3-consult-A/B、s4-ruling (erratum 1〜5 を含む)、s5-author-impl/probe、s6-review-A/B、s6-review-adjudication、s6-fix-impl1 / fix-probe1〜4、s6-focus、mutation の spec と台帳、probe script、差分 probe の結果。
