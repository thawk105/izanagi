# 受入 worker 時間の削減 — s8b emitter builder の disk memo と preflight test の小 repo 入力

- authority: none
- default_effect: no-state-change
- 依頼: 受入全走の worker 時間を、受理集合・assertion・hold・成分粒度を変えずに削る (対象 6 file、局所修正 4 型だけ、効果は同 job A/B、変異 matrix で kill 集合同一)。逐語は `verbatim/rulings-verbatim.md`。
- wave: dev-wave-acceptance-worker-time-trim (branch worktree-dev-wave-acceptance-worker-time-trim)。着手時 local main `a99425b66`、段 5 前に `657e1e5a7` を ff 取込。実装 commit `ecff42ec6`。
- 原ログ: `/home/SFC/tanab/.claude/jobs/28fa456a/` (brief、prompt、子の報告、焦点走 log/junit、A/B 出力)、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-worker-time-trim/` (独立 clone、変異 spec/results/attempts)。
- 実装: `orchestrator/tests/test_s8b_ratified_freeze.py` (+229/−74)、`orchestrator/tests/test_run_tests_preflight.py` (+30/−8)。production・conftest・登録簿・hold・既存 test の期待値は不変。追加 node は機構の正例 2 本だけ。

## 段 1 の実測 (費用の種別)

計算ノード bnode130 (request 10737) で 6 file を file 単独・`-n 12` で走らせ `--durations` を setup/call で分け、代表 node を bnode020 (request 10741) で cProfile した。login node の `/tmp` は fsync 1 回 30 ms (conftest.py 冒頭の実測) で受入条件と違うため、login の単独走は打ち切って計算ノードで取り直した。

| file | 単独 junit 合計 (12w) | 台帳 (48w 受入) | 費用の種別と所在 |
|---|---:|---:|---|
| test_s8b_floor_campaign.py | 1,320 s (532 node) | 2,368 s | 約 90 node × 5.8 s = production `s8b_holdout_admission._floor_attempt_recovery_candidate_locked` の attempt ledger 回復が attempt 数に対し二乗 (98 attempt × 98 row、json 16 万回、profile 9.9 s 中 9.1 s)。9 組 18 呼出しの `_real_output_snapshot` (実 repo output/ 25,185 file、初回は全 file を sha256 15.6 s、以後 `git status -- output` 3.5 s + rules 1.4 s + walk 1.6 s)。5 node × 30 s の実 repo clone + production clean scan |
| test_s8b_ratified_verify.py | 825 s (189 node) | 945 s | 101 node × 8〜15 s: 各 test が `build_production_emitter_g1` で決定的 git repo fixture を再構築 (git subprocess + 固定 seam の campaign)。82 test は `in_sealed_fixture_process` の fork 子で本体を走らせる |
| test_p3_b4_producer_auth_experiment.py | 398 s (50 node) | 832 s | production `ScratchTree` (`git archive HEAD \| tar -x`、856 MB / 28,158 file、3.9 s/本) × 30 本以上 + wave mutant 8 node の `tools/run_tests.py` subprocess (26 s/本) |
| test_run_tests_preflight.py | 207 s (216 node) | 544 s | 19 node × 7.4 s: `RT.main(site=PEGASUS_LOGIN)` の `_tree_and_submodules_fingerprint(_REPO)` = 実 worktree への git 5 command (status --untracked-files=all 5.0 s、diff HEAD 2.4 s、submodule 3 本 0.7 s) が 100% |
| test_codex_reasoning_ab.py | 346 s (643 node) | 483 s | module fixture `benchmark_snapshots` 10.3 s/worker (実 repo の pack-objects + checkout + submodule) が setup 135 s、call は production `verify_manifest` (46 s/代表 node) が主 |
| test_t1259_qsub_env_delivery_probe.py | 12 s (51 node) | 550 s | module fixture 4.0 s/worker (git 3 回)、本体 0.43 s。既に module memo。受入 48 worker 下の値は単独走で再現しない |

台帳の 6 file 合計 5,722 秒は全体 17,959 秒の 32%。段 1 の要約は `verbatim/stage1-prof-summary.md`。

## 裁定 (段 4) と実装した範囲

plan (1 本) と敵対相談 2 本 (正しさ境界 / 実効性・過剰) を受け、実装は次の 2 単位だけにした。

- **U1 s8b builder の disk memo (型 ii・iv)**: `build_production_emitter_g1` の campaign 完了直後・mutation 適用前の木を pytest の session basetemp 直下 `izanagi-emitter-memo/<key sha256>/` に 1 回構築し、同 key の呼出しは `<key>.lock` の flock 内で copytree + `git update-index --refresh` + `git status --porcelain` の byte 一致検査で複製する。key は worktree root、`now`、`selector_valid_cell`/`selector_payload_hit`/`perf_available`/`compiler_input_rel`/`cert_at_generation`、session (`PYTEST_XDIST_TESTRUNUID`、無ければ process token)。`receipt_root` と selector 系 True は memo を迂回し現行処理。構築元の `tmp_path`/`root`/`out_root` 文字列も needle に加え、artifact への絶対 path 漏洩検出 (M3) を維持する。fork 子でも消えない disk 置き場を pytest の basetemp 規則に委ね、自前の寿命管理は作らない。
- **U3/R preflight の小 repo 入力 (型 i)**: function scope fixture `_small_login_repo` が git init + 1 commit の小 repo を作り `RT._REPO` へ注入。fingerprint 関数と 5 command はそのまま実行される (DW-O14 の外側入力 seam)。9 関数 18 node に適用。`test_nonacceptance_bounded_child_marker_warns_exactly_once_in_parent` (記録開始経路) と `test_previous_full_cap_estimate_dispatches_without_local_scope` (fingerprint 非到達、RuleOps 経路) は除外。
- **実装しなかったもの (残る律速)**: U2 floor の digest 共有 (読取り失敗の fail-closed を共有 hit で隠す + 11 node 同時到着で共有待機と相殺、純利得の符号不明)、`_real_output_snapshot` の before 共用 (先行 test の汚染が後続 test の失敗集合を変える = 受理集合の変更)、floor の production 二乗 ledger 回復 (fixture 費用でない)、U3/A codex_ab (oracle/prompt/receipt の絶対 path と submodule gitdir の再束縛で 120〜200 行、純利得未確認)、U4 p3_b4 (7 tree の共有は配置依存で 0 もあり得る、production ScratchTree と run_tests subprocess は検査対象)、t1259 (既に 1 回構築)。D2068 の 3 案は提示していない。
- brief の誤りを相談で訂正: real-repo 登録 node が 1 worker に直列なのは process-memo 集合 (t1259 30 関数) だけ、floor の snapshot は 9 組 18 回、p3_b4 は 7 tree、12 worker の比は 48 worker へ外挿しない。

## 独立検証と修復

plan 1 本、相談 2 本、author 2 本、レビュー 2 本、fix 3 本 (U1 2 巡、U3R 1 巡)、焦点再レビュー 1 本を隔離 Codex subprocess で実施。逐語は `verbatim/`。

- レビュー 2 本の must-fix: 新正例に `@in_sealed_fixture_process` が無く sealed build session の単一 OS thread 要求で失敗 (親の裁定の指示ミス、focus1 で実測)、memo 置き場の名前探索が外側 custom basetemp で別 session の memo を拾いうる、focus 差の「保守的」断定、A/B script の `--basetemp`。should: 4 象限 test も対象化 (42.7 s → 0.2 s)、正例の 5→4 回構築、metadata の不要 field。
- fix 1 巡目の A2 対応 (相対 path の形で締める) は `tmp_path/"mutation"` 等の下位 dir 配置を memo 迂回にし、V を 224 s → 416 s へ戻す回帰を focus2 で実測。fix 2 巡目で session 境界を key (`PYTEST_XDIST_TESTRUNUID` or process token) へ移して解消 (focus3 で V 223.5 s)。
- 焦点走 (計算ノード、同走 `-n 12`): focus1 1310/1 (赤は新正例のみ)、focus2 1311/0、focus3 1159/0 (oracle_driver 省略)。consumer 5 file (holdout_freeze、oracle_driver、oracle_report、oracle_manifest、verdict、t080_freeze_migration) は緑。

## 効果 (同 job A/B、計算ノード bnode012、request 11248)

A = 修正前 `657e1e5a7` の base worktree、B = 修正後 `ecff42ec6` の wave worktree。同じ job で 6 file を 1 回の `run_tests.py … -n 12 --dist=loadgroup` に渡し、走ごとに新しい `TMPDIR` / `PYTHONPYCACHEPREFIX` (空)、`PYTHONDONTWRITEBYTECODE=1`、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、warmup A→B の後 **AB / BA / BA / AB の 4 対**。全 10 走 rc=0、B 側の memo key は各走 1 (`verbatim/ab-runs-summary.txt`、集計 `verbatim/ab-aggregate.txt`、script `verbatim/ab-compute.sh.txt`)。指標は junit testcase time の合計 (worker 秒)。

| file | A worker 秒 (4 対) | B worker 秒 (4 対) | A−B 中央値 (最小〜最大) |
|---|---:|---:|---:|
| test_s8b_ratified_verify.py | 861〜864 | 239〜254 | **−620.6** (−609.9〜−623.1) |
| test_run_tests_preflight.py | 182〜267 | 18〜20 | **−208.3** (−163.6〜−247.4) |
| test_s8b_floor_campaign.py (無変更) | 1,088〜1,219 | 1,088〜1,194 | −38.4 (+106.1〜−63.2、符号が振れる) |
| test_codex_reasoning_ab.py (無変更) | 416〜456 | 398〜418 | −27.2 (+2.1〜−54.2) |
| test_p3_b4_producer_auth_experiment.py (無変更) | 460〜474 | 445〜459 | −18.0 (−1.5〜−22.4) |
| test_t1259_qsub_env_delivery_probe.py (無変更) | 7.1〜7.6 | 5.7〜6.3 | −1.3 |
| **6 file 合計** | 3,016〜3,244 | 2,195〜2,336 | **−917.1** (−680.8〜−992.5) |
| 6 file 同走の wall (12 worker) | 269〜287 s | 200〜212 s | −27% |

読み方: 修正した 2 file の対差は 4 対とも同符号で幅が小さい (V は ±7 s、R は ±42 s)。無変更 4 file の差は競合緩和の副次効果と走間変動の混合で、floor は符号が振れる (走間変動 ±100 s 級) ので削減として数えない。この A/B は 12 worker・6 file 同走の条件であり、48 worker の受入全走へは比を外挿しない。受入全走はこの記録 commit の後に投入するので本書には書かない (受領証は land の `--acceptance-receipt` と job dir に残る)。修正前後で node 数は V 189 / R 216→217 (正例 +1) / 他は同数、赤 0。

## 変異 matrix (kill 集合の同一性)

production 側の 7 変異 (`verbatim/mutation-spec-new.json`、事前登録は `verbatim/adjudication.md` §3) を、修正前 `657e1e5a7` と修正後 `ecff42ec6` の test file に対して `tools/mutation_worktree.py` (独立 clone、D1009、`--runner-mode dispatch`) で両走した。runner argv は両側 `run_tests.py --force-dispatch test_s8b_ratified_freeze.py test_s8b_ratified_verify.py test_run_tests_preflight.py -q -rf`。
修正前は 3 file の parametrize 展開後の完全集合を静的に確定できないため **probe 走** (全件 SURVIVED 期待・node 空、DW-M08 の「確定できない場合に限り初回を probe」) で観測集合を採り、その集合を修正後の **KILLED 期待** に登録した (M3 は新正例 1 node を加える、事前登録済み)。

| 変異 | production の位置 | 修正前 (probe 観測) | 修正後 (KILLED 期待) | 差 |
|---|---|---:|---:|---|
| M1 frozen-at-head 検査を無効化 | s8b_ratified_freeze.py `parents[0] != frozen` → `False` | 1 | 1 (KILLED) | なし |
| M2 closure sha 検査を無効化 | 同 `_sha256_hex(g_blob) != sha` → `False` | 1 | 1 (KILLED) | なし |
| M3 argv の root 相対化を無効化 (構築側) | s8b_floor_campaign.py `_replace_root_component` 呼出しを恒等に | 130 | 131 (KILLED) | 新正例 1 node のみ |
| M4 launch-start の cert sha を固定値に (構築側) | 同 journal launch-start の `launch_certificate_sha256` → `"0"*64` | 43 | 43 (KILLED) | なし |
| M5 child rc を 0 に | tools/run_tests.py `return scope_result.child_rc` → `return 0` | 2 | 2 (KILLED) | なし |
| M6 fingerprint 前後比較を無効化 | 同 `tree_before != tree_after` → `False` | 1 | 1 (KILLED) | なし |
| P0 等価 (`len(parents) != 1` → `1 != len(parents)`) | s8b_ratified_freeze.py | 0 (SURVIVED) | 0 (SURVIVED) | なし |

修正後の台帳 summary: KILLED 6 / SURVIVED 1 / MISMATCH 0 / PARSE_ERROR 0 / TIMEOUT 0、matching 7/7、baseline PASSED。wrapper receipt は shared_snapshot_matches / terminal_ledger / teardown_completed = true、resolved_commit = ecff42ec6。修正前の probe 台帳 (`verbatim/mutation-old-results.json`) と node 単位で突合した差分は M3 の新正例 1 node だけ。構築側の変異 (M3/M4) が memo 経由の消費 node でも検出されたことは、memo が走ごとに fresh (pytest の session basetemp 下、key に session 成分) であることの正例である。単一理由性は probe の失敗本文 (`test_output_tail`) で確認した: M1/M2 は `_assert_registered_refusal("frozen" / "closure-sha")`、M3 は builder の `_assert_no_root_bytes` (6 excerpt すべて)、M4 は production loader の `RatifiedFreezeError [binding-chain-mismatch] sha256(cert.raw) != journal.launch-start.launch_certificate_sha256`、M5 は R:1851 の rc assertion、M6 は dispatch mock の assertion。

## 残る律速と次の一手

- floor_campaign 約 90 node × 5.8 s: production `s8b_holdout_admission.py` の attempt ledger 回復が attempt 数に対し二乗。局所 fixture では消えない。production 側の改善候補 (別 wave、裁定要)。
- floor の `_real_output_snapshot` 9 組 18 回 (55〜65 s/node 同走時): before/after は失敗集合の意味なので残す。digest の session 共有は純利得の符号が不明で見送り。
- floor の実 repo clone + production clean scan 5 node × 30 s、codex_ab の production verify、p3_b4 の ScratchTree と run_tests subprocess、t1259: 検査対象そのもの。
- V の selector 系 18 node (~7 s) は決定性未確認のため memo 迂回のまま。決定性を実測できれば key に含めて memo 化できる。
