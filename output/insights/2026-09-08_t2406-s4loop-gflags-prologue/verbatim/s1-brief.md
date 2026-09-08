# [T-2406] 段 1 brief — p3_s4_loop_pegasus.sh へ gflags/glog 供給経路を移植する

- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags` (branch `worktree-dev-wave-t2406-s4loop-gflags`、base = local main `34af5a571`、clean、submodule 初期化済み)
- 確定済みユーザー裁定 D1773 (2026-09-08): 兄弟 job body `tools/pegasus/floor_scoping.sh` の gflags/glog prologue を `tools/pegasus/p3_s4_loop_pegasus.sh` へ**そのまま移植**する。(a) policy (`tools/pegasus/policy.json` の `gflags_source_path` / `gflags_expected_head` / `glog_source_path` / `glog_expected_head`) 依存の新設を認める、(b) provenance file は作らない、(c) 契約テスト (`orchestrator/tests/test_p3_s4_loop_job_contract.py`) の期待 node と admission registry は同じ commit で更新する、(d) `CMAKE_PREFIX_PATH` は driver 本走まで持たせる。帰属は D1737。
- 実測済み前提 (本 wave、2026-09-08): 両 source は detached HEAD で policy pin と exact 一致 (`e171aa2d…`、`8f9ccfe7…`)。`policy.json` は whole-file sha256 golden で pin されている (`orchestrator/tests/pegasus_policy_expected_goldens.py`) ので **policy.json は変更しない**。job body / 契約テスト / registry / README の whole-file hash pin は無い。driver は `buildcache.build_v2` で ambient `CMAKE_PREFIX_PATH` を identity へ束縛する (`buildcache.py:2476,2531`)。`prepare_masstree_fetchcontent` の `_run` は env を継承する (`buildcache.py:2069`)。driver CLI に dependency-prefix flag は無いので env が唯一の経路。
- scope (実装面、Codex author): (1) job body へ prologue を移植 — policy 4 key の読取と検証、gflags/glog の HEAD exact 一致・clean 検査、`$TMPDIR` (= `$scratch`) 配下への configure/build/install (argv・timeout・`-j 48` は移植元どおり)、`export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` を masstree 事前構築より前に置き driver 本走まで unset しない。既存の sanitize 段 `unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE` は残す。(2) 契約テスト: required fragment・stage-order marker・refusal 一覧・fragment mutant の追加と、`_assert_forbidden_job_constructs` の `forbidden-cmake-environment-injection` を「上記 exact 1 行だけを 1 回、install 2 本の後かつ prebuild 呼出しの前で受理し、それ以外の `CMAKE_PREFIX_PATH` 代入は従来どおり拒否」へ改訂する。(3) admission registry は分類不変なら変更なしを確認し、変更が要るなら同 commit。
- scope (docs、親): `tools/pegasus/README.md` §7 の「`CMAKE_PREFIX_PATH` は置かない (F813、D1517)」を D1773 の形へ訂正し、prologue の 1 項を足す。
- 不変条件: 規律 2 — 受理形の追加は上記 exact 1 行のみで、他の `CMAKE_PREFIX_PATH` / launcher / include 注入・shim 追加・`--no-build` の拒否は不変。gate・検査・台帳・一般化の新設はしない (D1773 の範囲外)。provenance file (`cmake-prefix-path.json` 等) と evidence root への新規 file は作らない。policy.json / hooks / buildcache / driver は触らない。push 禁止。
- 成果物: 統合 commit 1 本 (job body + 契約テスト [+ registry] + README)。段 6 で変異 matrix と受入全走。段 7 で insight dir `output/insights/2026-09-08_t2406-s4loop-gflags-prologue/`。
- 分割方針: 実装単位 1 (author 子 1 本、3 file は密結合)。段 6 レビュー 2 本 (A: 受理集合・規律 2、B: 移植の忠実さ・実効性)。
- 提案 (provisional、攻撃対象):
  - (P1) 失敗は移植元の `fail 2 "<msg>"` でなく本 job body の `refuse "<msg>"` に写す (rc=2 の境界は同じ、message は移植元と同文)。
  - (P2) gflags/glog の dirty 検査は移植元どおり `--untracked-files=all` を保つ (既存 third-party 検査の `no` へ揃えない)。
  - (P3) compiler は移植元どおり `command -v gcc` / `g++` の realpath (sanitized PATH 下で `/usr/bin/gcc`) とし、`buildcache.compilers_for_current_site()` との一致は前提として検証対象にする。
  - (P4) configure/build/install の stdout/stderr は provenance file へ落とさず、job 標準出力・標準エラーへそのまま流す (evidence root の file 集合を変えない)。
  - (P5) prebuild receipt の schema (`p3-s4-loop-masstree-prebuild/v1`) は変えない。(d) の identity 束縛は build_v2 の ambient 経路に依る。/scr の job 別 path が identity に入り job 間で build cache が再利用されなくなるのは受け入れる (現状も cache 再利用の実測は無い)。
  - (P6) prologue の位置は `claim_root` provisioning の後・`prebuild_source_root=` の前 (third-party 複製と prebuild を連続に保つ)。
  - (P7) 実装後の生死確認 (固定 SHA detached checkout から 1 本 qsub) は段 4 で queue 状態を見て決める。land の条件にはしない。
- 実測環境: テスト・変異・受入は login node の自動判定 / dispatch (`tools/run_tests.py`)。計算ノード実走は (P7)。
