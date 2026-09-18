単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (自分が推測して探した path の不在は停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s4-ruling.md` — **親の段 4 裁定 = plan v2 (この prompt の正本)**。試作 patch の変更一覧、shadow 登録簿、45 cell と条件付き予測、実行順、(iii) の helper 呼び出し形
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s2-plan.md` — 段 2 plan (file:line の詳細。裁定と食い違う箇所は裁定が勝つ)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s1-brief.md` — 段 1 brief (背景。登録簿の行番号 184-199 は誤りで正しくは 160-176)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s3-a.md` と `s3-b.md` — 段 3 の所見 (裁定で採用済みの是正の出所)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/verbatim-d2120-item12.md`、`verbatim-t2644-s5.md` — ユーザー裁定と一次資料の逐語
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/orchestrator/campaign/condition_meaning_gate.py` — gate (読むだけ。**編集禁止**)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/tools/pegasus/run_ss2pl_lock_study.py` — runner (読むだけ。**編集禁止**)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/patches/ss2pl-lock-protocol-study.patch` — 現行 patch (読むだけ。**編集禁止**。試作はこれの派生を別 file に書く)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/output/insights/2026-09-17/t2644-ss2pl-wfg-connect/verbatim/probe.md` — 前 wave の probe 逐語 (runner の production 関数を import する形、`discover_pbs_jobid`、atomic write の手本)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/tools/pegasus/probes/t316_sandbox_backend_probe.py` — 1905-1945 (`buildcache.observed_toolchain_manifest` → `prepare_masstree_fetchcontent` の呼び方の現物)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/orchestrator/campaign/buildcache.py` — 2034-2110 (`prepare_masstree_fetchcontent` の signature)、`observed_toolchain_manifest` の定義 (`grep -n "def observed_toolchain_manifest"`)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/external/ccbench/cc/ss2pl/transaction.cc`、`include/*.hh`、`/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/external/ccbench/include/rwlock.hh`、`/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/external/ccbench/cc/ss2pl/CMakeLists.txt` — stock (読むだけ)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe` (branch `probe-dev-wave-t2737-gate-controls`、base `d2ebef7a4`)。上記以外も repo 内を読んでよい。**大きい file を全文 `cat` しない** (`grep -n` → `sed -n` で 200 行以内ずつ)。

## 成果物 (すべて `<repo root>/probe-t2737/` 配下の新規 untracked file。tracked file は 1 byte も編集しない。commit しない。`git add` / `git stash` / branch 操作をしない)

1. `probe-t2737/patches/ss2pl-lock-protocol-study-define-only.patch` — **revS**。裁定「試作 patch」項 1 のとおり。現行 patch (2,766 行) を出発点に `git apply` 可能な unified diff として書く (stock の submodule `external/ccbench` を `git clone` した作業木に現行 patch を当て、編集し、`git diff` で出力する形が確実。作業木は `probe-t2737/work/` 配下に置き、成果物には含めない旨を README に書く)。
2. `probe-t2737/patches/ss2pl-lock-protocol-study-define-only-abort-unconditional.patch` — revS との差が abort 増分ブロック (裁定 #8) だけの版。
3. `probe-t2737/t2737_gate_probe.py` — 裁定「shadow 登録簿」「cell (45)」「実行順」「(iii) warm-up の形」を実装する probe。詳細は plan §6〜§7 + 裁定の B4〜B8。
4. `probe-t2737/README-probe.md` — 使い方 (login の selftest / precheck / 計算ノード投入 argv)、**login で自分が実走した結果** (下記)、実走していないこと (plain build、trial、計算ノード cell)、既知の限界。

## 試作 patch の契約 (裁定の逐語を優先)

- 新しい lock 意味論を足さない。KIND を IMPL=0 で人工的に効かせない。stock 経路の「復元」は stock の本文・配置を戻す作業であって再実装ではない。
- `wfg.cc` は CMake で `if(CCBENCH_SS2PL_WFG_DIAG EQUAL 1)` の条件付きのまま (無条件にしない。runner の `validate_wfg_absence` が source 名の `wfg` を拒否する)。owner TU 側は `ss2pl_wfg.hh` の include を無条件にし、中身を `#if SS2PL_WFG_DIAG` で囲む。
- CMake の DLR marker は stock どおり `DLR1` 固定。`SS2PL_DLR` は純 define。stock transaction.cc の `#ifdef DLR0 / #elif defined(DLR1)` 5 組 (stock 172/178、263/269、309/314、411/413、436/438) は `#if SS2PL_DLR == 0 / #elif SS2PL_DLR == 1` へ。IMPL=0 && DLR=2 は `#error`。`ss2pl_lock.hh` の `#error "SS2PL_DLR=n requires DLRn"` は撤去。
- 新規 header 3 本は `#pragma once` をやめ include guard (`#ifndef … #define … #endif`) にする (親の実測: `g++ -E -P` で `#pragma once` は 7 空白 + 改行の残渣を残す)。`rwlock.hh` の既存 `#pragma once` は保持。
- `ss2pl_lock.hh`: `rwlock.hh` と `ss2pl_study_lock.hh` を無条件 include、alias `using ReaderWriteLock = SS2PLStudyLockT<…>` だけ `#if SS2PL_LOCK_IMPL == 1`。`include/rwlock.hh` には `class ReaderWriteLock` だけを `#if !defined(SS2PL_LOCK_IMPL) || SS2PL_LOCK_IMPL == 0` で囲む hunk を足す (include 群と `using namespace std;` は無条件のまま)。study header の依存 include (`<array>` 等) は無条件、宣言・定義は全部 `#if SS2PL_LOCK_IMPL == 1` 内。
- abort 増分 (現行 patch が `TxExecutor::abort()` から除去した `++result_->local_abort_counts_`): revS では `#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB` / `#else` 増分 / `#endif` の形で非 YCSB に戻す。abort-unconditional 版は現行どおり無条件除去。**2 版の差分はこのブロックだけ**。
- S 復元 (plan §2 末尾の表): common.hh の legacy `DEFINE_*/DECLARE_*` 削除、transaction.hh の include 位置・constructor の出力形、`begin()`、`update()`、`delete_record()` の `break`、既取得ロック検査、`unlockList()` の brace。目標は「S (IMPL=0, KIND=1, DLR=1, WFG=0) かつ `SS2PL_WORKLOAD_YCSB` 未定義 (tpcc target) のとき、`transaction.cc` の `-E -P` 出力が stock と byte 一致」。YCSB target で必要な変更は `SS2PL_WORKLOAD_YCSB` で囲む。**固定した範囲で復元し、届かなければ残差を README に書く** (隠さない)。phase1 (IMPL=1, KIND=0, DLR=0, WFG=1) の study 経路と WFG 計器の挙動は変えない (diff で確認し README に書く)。

## probe の契約

- 引数: `--repo-root --patch-current --patch-redesigned --patch-abort-unconditional --shadow-root --scratch-root --gflags-prefix --glog-prefix --thirdparty-root --jobs --output --cells {recommended|login-precheck|<ID…>} --selftest`。`--thirdparty-root` は**保存用 pristine staging** で、probe は attempt ごとに `cp -a` で `<scratch>/<attempt>/staging/` へ複製してから使う (原本を書かない。複製後に `masstree/config.h` 不在を確認し記録)。scratch・shadow・staging の親 dir 名に `wfg` を含めない。
- runner の production 関数 (`validate_required_commands`、`verify_canonical_submodule`、`clone_network_free`、`_apply_patch`、`_expected_cache`、`_condition_request_inputs`、`_target_compile_entries`、`_validate_compile_definitions`、`_wfg_absence_evidence`、`validate_abort_counter_ownership`、`_study_lock_header_declarations`) を import して使う。runner は `ROOT` を `sys.path` に入れる。
- gate 呼び出しは runner の `_require_condition_gates` (R:1980-2045) と同じ 3 呼び出し (`capture_define_inputs` → `make_define_request` → `evaluate_define_supply_effectuation` / `evaluate_define_runtime_meaning(declaration=None)` → 4 軸そろったら `require_condition_gate_family(use_class="raw-measurement")`) を **shadow module ごとに同じ module instance で**行い、record の `canonical_json()` を全部保存する。`configure_args` は R:1988-2003 と同じ組み方 (軸 cache key は除外、`-DFETCHCONTENT_BASE_DIR` は渡さない)。
- shadow 登録簿: `<shadow-root>/<patch-id>/<registry-id>/orchestrator/campaign/condition_meaning_gate.py` + `patches/ss2pl-lock-protocol-study.patch` を probe 開始時に生成 (既存なら中身一致を検査、不一致は停止)。生成は SS2PL 4 entry の完全一致 block 置換 (`target` 4 行を `tpcc_ss2pl.exe`、T− は `SS2PL_LOCK_KIND` の companion を空 tuple)。受理条件 = 生成 bytes が repo gate bytes に許可置換だけを施した期待 bytes と一致 (O は byte 同一)。`importlib.util.spec_from_file_location("orchestrator.campaign._t2737_gate_<id>", path)` → `sys.modules` 登録 → exec。`__package__`、`source_digest.__file__`、`_patch_changed_paths(spec)` の結果、正準 `orchestrator.campaign.condition_meaning_gate` の `id()` / `__file__` の前後不変を receipt に残す。
- (iii) warm-up: `buildcache.observed_toolchain_manifest("cc", "c++")` → `buildcache.prepare_masstree_fetchcontent(ccbench_dir=<revS clone>, fetchcontent_base_dir=<attempt scratch>/fetchcontent, expected_toolchain_manifest=manifest, configure_timeout_s=300, target_timeout_s=600, dependency_prefix="<gflags>;<glog>", masstree_source_dir=<attempt staging>/masstree, mimalloc_source_dir=…, googletest_source_dir=…)` を 1 回。生 `cmake --build --target masstree_build` は書かない。前後の `config.h` 有無・sha256・所要・argv を保存。
- 実行順・cell ID・条件付き予測 (`expected_reason`) は裁定の表どおり。cell ごとに try/except/finally + atomic 保存 (前 wave の `write_result` の形)。予算未実施・probe 内部例外・gate red を別 field で区別。configure-failed の cell では同じ引数の診断 configure を別 build dir で 1 回走らせ stdout/stderr 全文を保存 (原判定は置換しない)。
- receipt 先頭に `tempfile.gettempdir()`、空き容量、`c++` / `cmake` / `cc` の realpath と `--version`、hostname、`PBS_JOBID` 候補 (env → `compute-visible.json` 最新 → unknown、**候補として**記録)、probe / patch 3 本 / runner / gate の sha256 と byte 数。
- plain build (計算ノードのみ): revS を S と phase1 で `ycsb_ss2pl.exe` を build (`_configure` + `cmake --build`、timeout 1800)、`_target_compile_entries` + `_validate_compile_definitions`、S build に `_wfg_absence_evidence`。build 成功と gate admission は別欄。trial は走らせない。
- `--selftest`: tmp 不要の合成入力で (a) shadow 生成の受理/拒否 (許可置換だけ受理、`inert_values` / `owner_tus` / 式の混入を拒否、非 SS2PL entry の変更を拒否)、(b) cell 表の ID 一意性・件数 45・予測語彙・実行順 (pristine が warm-up より前)、(c) 2 版 patch の差分が abort ブロックだけであることの検算関数、(d) 合成 source の `#if 0` 内増分も `validate_abort_counter_ownership` の token 走査に数えられること。rc=0/1 で結果を返す。
- `--cells login-precheck`: clone / apply / 2 版差分検算 / runner 静的契約 (abort 所有権を 2 版で、`_study_lock_header_declarations`) / shadow 生成 / stock と revS を同じ configure_args で configure し **tpcc target の transaction.cc entry** を `-E -P` で前処理して `cmp` (S の一致診断) / revS×T−×S の IMPL 1 cell を実 gate で評価。warm-up・build・trial は呼ばない。`--thirdparty-root` には login では前 wave の warm 済み staging `/work/1/SFC/tanab/dev-wave-jobs/t2644-deps/thirdparty-src` (config.h あり、`staging_state=preexisting` と記録、pristine の証拠に数えない) を渡す。
- 起動形: `python3 -B <絶対 path>/t2737_gate_probe.py …` (clean env・cwd = 投入 worktree を前提に、path は全部絶対で受ける)。

## login で自分が実走して README に書くこと (実走 nodeid / command と rc を併記。走らせていないものは「未実走」)

1. `python3 -B probe-t2737/t2737_gate_probe.py --repo-root <repo root> --selftest` → rc と各項目の PASS/FAIL。
2. `--cells login-precheck` (scratch は `probe-t2737/work/scratch`、shadow は `probe-t2737/work/shadow`、gflags/glog prefix は `/work/1/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install`、thirdparty は上記 warm 済み staging) → S の `cmp` 結果 (一致 / 不一致なら最初の差分 20 行と、path 差以外の差分行数)、abort 所有権検査の 2 版の結果、IMPL cell の `reason_code`。**一致に届かなければそう書く。**
3. `git status --porcelain` が `?? probe-t2737/` だけであること (tracked file 無変更)。
4. 所有外 caller・共有 fixture・consumer test への波及可能性の静的列挙 (成果物は repo 外へ退避されるので通常ゼロのはず。ゼロならゼロと書く)。

`cmake --build` (masstree の warm-up、`ycsb_ss2pl.exe` の build) と trial は login で走らせない。configure と `-E -P` 前処理は走らせてよい。

## 禁止

- tracked file の編集、commit、`git add`、stash、branch 操作。`patches/`・`orchestrator/`・`tools/` の既存 file を変えない。
- gate の判定 logic・runner・登録簿 (repo 側) を変えない。テストを足さない・変えない。
- 実走していない結果を緑と書かない。予算が尽きそうなら成果物を書けたところまで保存し、README と `## 総括` に途中状態を書いて終わる (無出力が最悪)。

## 出力形式

最終メッセージに `## 総括` (必須): (1) 成果物 4 点の path・byte 数・sha256、(2) revS の S 一致診断の結果 (一致 / 残差 N 行)、(3) selftest と login-precheck の rc、(4) 裁定と違えた点・できなかった点、(5) 計算ノード投入 argv の推奨形、を 15 行以内。
