# 段 1 brief — [{{T:acceptance-worker-time-trim}}] 受入全走の worker 時間を受理集合不変で削る

wave: `dev-wave-acceptance-worker-time-trim` / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim` (branch `worktree-dev-wave-acceptance-worker-time-trim`、起点 main `a99425b66`、段 5 前に main `657e1e5a7` を ff 取込予定)。
ユーザー依頼文と拘束裁定の逐語は `/home/SFC/tanab/.claude/jobs/28fa456a/rulings-verbatim.md`。

## 研究前進
受入全走は全 wave の land を直列に gate する共有資源で、ユーザー裁定は「全体 5 分が絶対上限」。対象 6 file は台帳 (48 worker) で 5,722 worker 秒 = 全 17,959 秒の 32% を占める。ここを削ることが Phase 3 の全研究 wave の cycle を短くする土台であり、完了判定は「同 job A/B 3 対以上で削れた worker 秒 + 変異 kill 集合の同一性 + 受入全走緑」。

## scope (依頼文の逐語が正本)
- 対象 6 file と、その fixture を所有する helper module (test_s8b_ratified_freeze.py の builder、output_snapshot_ignores.py) だけを編集する。production module (orchestrator/campaign/*.py、tools/run_tests.py、tools/pegasus/probes/*.py、tools/codex_reasoning_ab.py) は編集しない。
- 許す修正は 4 型だけ: (i) function → module/session scope 化、(ii) 同一入力の 1 回構築 + deepcopy/copytree、(iii) subprocess を in-process 呼出しへ、(iv) 実 repo 読取りは shared base 1 回。
- 提示しない: 検査の省略・stub 化・hold 変更・古い判定の再利用・parametrize 縮約・D2068 却下 3 案 (whitelist / alternates / index 移送)。新 gate・framework・並列度変更・launcher 改修は scope 外。
- 受理集合・assertion・hold・成分粒度 (node 数・nodeid・xdist group・real-repo 登録簿) は不変。nodeid を変えない。

## 確定済みユーザー裁定
依頼文 §1 全文。D2068。D95 (実装は Codex author)。DW-O14 (monkeypatch は最後の手段、検査対象の機構を構成する呼び出しの差し替えは禁止、実物へ委譲する観測 wrapper は差し替えでない)。

## 不変条件
1. 各 test が観測する値 (artifact bytes、git SHA、拒否理由、report) は修正前後で同一。複製で作った fixture は再構築で作った fixture と bytes・git object 一致 (build 2 回の同一性を実測してから採る)。
2. 実 repo (worktree) へは 1 byte も書かない。tmp は `/tmp` (計算ノード xfs) のまま。tmpfs を選ばない。
3. 複製した git repo は index の stat が変わるので、copy 直後に `git update-index --refresh`/`git status` で racy index を解消してから test に渡す (racy 判定で production の `diff-index` が偽陽性にならないことを確認)。
4. real-repo reader 登録簿 (conftest.py:453-664) の nodeid 集合は不変。shared base の実 repo 読取りは既存先例 `_T080SharedBases` (test_s8b_oracle_driver.py:900-990) と同型 (flock、`PYTEST_XDIST_TESTRUNUID` で session 同一性、最後の退出者が削除) に限る。
5. 変異 matrix: production module への変異を修正前 (main) と修正後 (wave tip) の test file 双方へ走らせ、失敗 node 集合の完全一致を KILLED 同一性とする (DW-M08 の新旧両走)。

## 成果物
- 実装 commit (Codex author)、A/B job の junit 6 対以上、変異 matrix 台帳、insight README (`output/insights/2026-09-19/acceptance-worker-time-trim/`)、worklog fragment、受入全走 receipt。
- 報告は「file 別に削れた worker 秒 (A/B 3 対の中央値と幅)」「残る律速 (何が・なぜ局所修正で消えないか)」。目標値は置かない。

## 並列分割方針 (段 5)
- U1: s8b 族 (test_s8b_ratified_freeze.py の builder と test_s8b_ratified_verify.py) — 1 回構築 + 複製。
- U2: test_s8b_floor_campaign.py — `_real_output_snapshot` の 1 回化と `_run_campaign` 系の同一入力再構築。
- U3: test_run_tests_preflight.py + test_codex_reasoning_ab.py — 実 repo 読取りの shared base 化 / module scope 化。
- U4 (候補、plan で採否): test_p3_b4_producer_auth_experiment.py の 3 test × 3 tree の module scope 化。t1259 は診断結果から局所修正候補なし (残る律速として報告)。
所有 file が重ならないよう U1〜U4 は file 単位で分ける。conftest.py と production は誰も触らない。

## 段 1 実測 (計算ノード bnode130、request 10737、`-n 12`、file 単独、junit time の合計; 台帳は 48 worker 受入)
| file | 単独 junit 合計 | 台帳 (48w) | 費用の種別と場所 |
|---|---|---|---|
| test_s8b_floor_campaign.py | 1,320 s (532 node) | 2,368 | (a) 11 node × 55〜65 s: `_real_output_snapshot()` (:1780) を before/after で 2 回 = 実 repo `output/` 25,185 file (733 MB) の走査 (`output_snapshot_ignores.py:564` の index cache 付き walk + `git ls-files -s` + `git status -- output`) → **実 repo 走査**。(b) 6 node × 30 s: public official preflight / real seal e2e。(c) 約 90 node × 5.8〜6.2 s (ほぼ同値): `_run_campaign` (:815) の in-process campaign core + `_test_holdout_authority` (:759) の git repo 構築 → **同一入力の再構築** (profile で内訳確定中) |
| test_s8b_ratified_verify.py | 825 s (189 node) | 945 | 101 node × 8〜15 s: 各 test が `B.build_production_emitter_g1` (test_s8b_ratified_freeze.py:1001、`_prepare_emitter_base` :641 + `_run_official_fixture_campaign` :935 + C/G/A/X commit) で決定的 git repo を再構築、9 node は `_assert_emitter_baseline` (:215) で baseline も再構築 → **同一入力の再構築** (git subprocess 多数 + fsync) |
| test_p3_b4_producer_auth_experiment.py | 398 s (50 node) | 832 | 8 node × 31 s: production `E.ScratchTree` (orchestrator/campaign/p3_b4_producer_auth_experiment.py:1869、`git archive HEAD \| tar -x` = 856 MB/28,158 file、4〜5 s) + `tools/run_tests.py` subprocess (約 26 s)。`test_case_failure…` (:1469) 67 s = 13 tree。:759/:791/:821 の 3 test × 3 tree ≈ 20 s → **fixture の複製 (production 側) + python subprocess** |
| test_run_tests_preflight.py | 207 s (216 node) | 544 | 19 node × 8〜12 s (同時走で同値): `RT.main(site=PEGASUS_LOGIN)` が `_tree_and_submodules_fingerprint(_REPO)` (tools/run_tests.py:2201、git status/diff/submodule recursive の 5 command) を実 worktree で実行 → **実 repo 走査** |
| test_codex_reasoning_ab.py | 346 s (643 node) | 483 | setup 135 s = module fixture `benchmark_snapshots` (:860) が worker ごとに 11 s (`TOOL._build_snapshot_base` tools/codex_reasoning_ab.py:3292 = 実 repo の pack-objects + checkout + submodule)。call 198 s のうち `_full_manifest` (:1678) 6 呼出しで 115 s → **実 repo 走査 (worker 数倍) + 同一入力の再構築** |
| test_t1259_qsub_env_delivery_probe.py | 12 s (51 node) | 550 | setup 10 s = module fixture `_repo_snapshot(REPO_ROOT)` (:73) を worker ごと。call は 0.5 s (実 driver subprocess)。台帳の 10〜23 s/node は受入 48 worker 下の効果 (real-repo group の単一 worker 直列 + 飽和) で、単独走では再現しない → **局所修正候補なし** |

補足: login node の `/tmp` は fsync 1 回 30 ms (conftest.py 冒頭の実測) で、計算ノード xfs の 100 倍遅い。login の単独走 (`-n 8`) は 4 分で 10 node しか進まず打ち切った。A/B は計算ノード同 job で行う。

## 段 1 profile (計算ノード bnode020、request 10741、代表 node の cProfile 単独走; 要約と所在は `/home/SFC/tanab/.claude/jobs/28fa456a/tmp/stage1c/prof_summary_pointer.md`)
- floor 5.8 s 級 (約 90 node): 9.1/9.9 s が production `s8b_holdout_admission._floor_attempt_recovery_candidate_locked` (:5230) の attempt ledger 回復 (98 attempt × 98 row = 9,604 row 正規化、json 16 万回)。**fixture 費用でなく production の二乗**。本 wave の対象外 = 残る律速 (裁定パッケージ候補)。
- floor 55〜65 s 級 (10 node): 29.5/39 s が `_real_output_snapshot` 2 回。初回は `_digest` 25,185 回 = 15.6 s (process 内 cache が空)、以後は `git status -- output` 3.5 s + ignore rules 1.4 s + walk 1.6 s / 回。
- floor 30 s 級 (5 node): 実 repo を `git clone --no-hardlinks` (本体 + ccbench) して production `clean_scan_digest` を 4 回 (26.8 s)。scan は test の主題。
- ratified_verify: **82 test が `in_sealed_fixture_process` の fork 子で本体を走らせる** (seal issuance record は PID 束縛)。memo は process 内では消えるので disk 置き (session 共有 + flock) が要る。
- preflight: 7.4/7.4 s が `_tree_and_submodules_fingerprint` (git 5 command、単独で `status --untracked-files=all` 5.0 s + `diff HEAD` 2.4 s)。
- codex_ab: 46/47 s が production `verify_manifest` (test の主題)。module fixture `benchmark_snapshots` は 10.3 s/worker (`_build_snapshot_base` 3.4 + `_derive_snapshot_from_base` 5.8)。
- p3_b4: 8.8/10.2 s が production `ScratchTree.__enter__` 3 回 (856 MB tar 展開) + rmtree 2.8 s。
- t1259: module fixture 4.0 s/worker (`_repo_snapshot` git 3 回)、本体 0.43 s。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) 「同一入力の 1 回構築 + 複製」で作った git repo fixture は、再構築版と test の観測 (SHA・bytes・拒否理由) が一致する。copy 後の index refresh を入れれば production の git 呼出し (`diff-index`、`status`、`ls-tree`) は同じ答えを返す。fork 子 (`in_sealed_fixture_process`) で走る test でも、disk 上の memo (session 共有 dir + flock) を copy すれば、issuance record を持たない process から後続 (G/A/X commit、`load_ratified_freeze`、`launch_validate`) を通せる。
- (P1') floor の 5.8 s 級 90 node は production の二乗 ledger 回復であり、本 wave の 4 型では消えない。同じく floor 30 s 級の clone + scan、codex_ab の verify、p3_b4 の ScratchTree/run_tests subprocess も test の主題で消えない。これらは「残る律速」として報告し、production 側の改善は裁定パッケージ候補に分ける。
- (P2) `_real_output_snapshot()` の before を module scope で 1 回取り、after だけを test ごとに取っても、「test が実 output/ を変えていない」という検査は弱まらない (検出は残り、帰属だけが粗くなる)。
- (P3) test_run_tests_preflight.py の 19 node で fingerprint は検査対象でなく、`RT._REPO` を小さな tmp git repo へ向ける (実物の関数をそのまま実行) のは DW-O14 の「外側の既存定型 seam」に当たる。monkeypatch で fingerprint 関数自体を差し替える案は最後の手段。
- (P4) codex_ab の `benchmark_snapshots` を `_T080SharedBases` 同型の session 共有 (flock) にしても、snapshot/oracle は絶対 path に依存せず copy で等価。
- (P5) p3_b4 の ScratchTree (production) と run_tests subprocess は test の意味そのもので、局所修正の対象外 = 残る律速。t1259 も同じ。
- (P6) A/B は同 job で base worktree (修正前 tip) と wave worktree を ABABAB で 3 対、6 file を `-n 12` で走らせ junit time の file 合計を比べる。48 worker 受入と絶対値は違うが比は転移する。
