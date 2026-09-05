# [T-2232] 段 1 brief — 段 4 loop 用 Pegasus job body と登録簿の同期 (2026-09-05、base 97ee3cd3a)

## scope (純増だけ)
- 新規 job body `tools/pegasus/p3_s4_loop_pegasus.sh` (compute-only、`#PBS -N izs4loop`)。投入は親が raw `qsub -v ... -o <evidence>/... -e <evidence>/... tools/pegasus/p3_s4_loop_pegasus.sh` で行う (A-1 `paper_story_a1_paired.sh` と同じ「この file は投入器ではない」型)。submitter script は作らない。
- 同じ変更単位で同期: `tools/pegasus/admission_registry.json` (class `dispatch-required` / evidence `static job-body classification`)、`orchestrator/tests/test_hooks.py` の `_PEGASUS_EXPECTED_CLASSES` と entry golden、`docs/pegasus-runbook.md` §7.0 投影表 1 行、`tools/pegasus/README.md` §0 宣言表 1 行 (`qsub-job-body`) + `# admission-site: qsub-job-body` タグ付き qsub block を持つ新節、新規 contract テスト `orchestrator/tests/test_p3_s4_loop_job_contract.py` (A-2 の `_assert_static_job_contract` 型 + 登録簿 exact entry + resolver harness + login 拒否 harness)。
- job body の義務 (引数 + T-2199 §引き継ぎ): (1) PBS envelope と `^bnode[0-9]+` 以外は rc=2 で拒否、(2) `python3.10` resolver + `python3`→3.10 の PATH 先頭 shim (interpreter のみ。PATH は `/usr/bin:/bin` + NQSV dir へ sanitize、`ss2pl_lock_study.sh:105-141` の形)、(3) expected HEAD・tracked clean・CCBench pin 一致、(4) masstree `config.h` の事前構築 = A-2 経路 (`buildcache.prepare_masstree_fetchcontent`、`FETCHCONTENT_SOURCE_DIR_*` を hydrate 済み source root から明示 define で渡す) を `/scr` scratch の base で走らせ、`config.h` の sha256・configure argv・build argv を evidence root の receipt に束縛、(5) `p3_s4_loop` を `"$PY" -B -m orchestrator.campaign.p3_s4_loop --allow-coder-derived-build` + (`--run-iteration <IZANAGI_S4_PROPOSAL_PATH>` | fixture `--value`) で起動、(6) 環境 sanitize (`CMAKE_*` launcher/include、`CXXFLAGS` 等、`GIT_*`、`CCACHE_*`、`PYTHONPATH`) と `IZANAGI_OFFICIAL_OUTPUT_ROOT` の unset。
- 実測しない (F660: 新規 Pegasus 実行体は main 着地後にしか投入できない)。login node での短走 (`bash -n`、compute-only 拒否、resolver harness、focused tests、`check_docs`) までで止める。

## 確定済み裁定 (変えない)
- F813 / D1517: PATH の CMake wrapper・compiler launcher・`CMAKE_PREFIX_PATH` env で third-party を注入しない。判定器 (condition gate) が環境から解決する実体 (cmake / c++) を job 側で差し替えない。
- D59: Pegasus の値を `linux-baremetal` 系列へ混ぜない (site 契約は T-2231 で `PEGASUS_COMPUTE`→`pegasus` に写像済み。job は env_tag を渡さない)。
- D95: 実装面 (job body・tests・registry JSON・test_hooks golden) は Codex author。docs (README/runbook) は親。
- 絶対規律 1・2: job は build flag・trace macro・verifier に触れない。`--no-build` を既定にしない。

## 不変条件
- 登録簿 bytes を pin する golden は無し (blob/sha256 grep 0 件)。`DW-O09` は不成立、`DW-O08/O10` も不成立。凍結 artifact・oracle・proof chain に触れない。
- `DW-O13` 成立 (contract テスト新設): 入力は job body source・registry JSON・README text の実在 file。login 拒否 harness の hostname は stub (`pegasus01`)、compute 側は bnode stub で「拒否前に重い処理へ進まない」だけを見る。
- job body 内で `qsub` しない。`PBS_JOBID` を path 要素にする前に `:` を `_` へ写す。evidence root は repo 外 (repo 内なら rc=2)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) 事前構築した FetchContent base は現行 `p3_s4_loop.py` に消費 seam が無い (`_require_condition_gate` は configure_args 無し、build は base dir 無し)。本 wave は receipt への束縛までとし、消費配線は T-2320 (backoff_sweep 側) と同型の後続 wave に送る。job の loop 本体は proxy 経由の FetchContent clone に依存する。
- (P2) loop の build 用 network は `a5_second_boot_backoff_sweep.sh:32,219-222` と同じ literal proxy を export する (policy.json に proxy key は無い)。
- (P3) walltime は `03:00:00` (loop 上限 3600 s + build + verify ≤ 23 min 実測 + 余裕)。job 名 `izs4loop` (qstat 8 文字切れ回避)。
- (P4) `IZANAGI_S4_REPO_ROOT` は専用 detached checkout (dynamic-backoff wave の `submit-tree` 型) で、campaign 成果物 (`output/exploration/...`) はその checkout 内に落ちてよい。primary worktree からの投入は README で禁じる。

## 成果物影響 (DW-G05)
- 放置時: 段 4 loop は Pegasus へ投入できず (guard が未登録実行体を拒否)、`pegasus` env-tag の certified 選択が 1 件も生成されない。本 wave 後: 登録簿に dispatch-required 1 path が増える (login では引き続き拒否)。certified 値・受理集合・proof 参照は変わらない。

## 分割方針
- 段 2 plan 1 本 (read-only)、段 3 lens 2 本 (A: F813 型の環境注入・受理集合、B: 規律 1/2・登録簿同期の取り残し・contract テストの恒真性)。段 5 author 1 単位 (job body + contract test + registry + test_hooks golden)。段 6 review 2 本 + fix。docs 2 file は親。
- 実測環境: login node の短走のみ。計算ノード投入なし。
