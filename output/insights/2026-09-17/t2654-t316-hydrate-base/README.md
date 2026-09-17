# t316 の条件関門と両 build を hydrate 済み staging + prepare_masstree_fetchcontent の準備済み base へ合流させた

日付: 2026-09-17 / wave: `dev-wave-t2654-t316-hydrate-base` / branch: `worktree-dev-wave-t2654-t316-hydrate-base`
対象: [T-2654] (D2044 項 27 の実装手番) / 実装 commit `f296e42bc` (Codex author)

## 一行で言うと

t316 probe は永続 third-party cache を `FETCHCONTENT_SOURCE_DIR_*` で直指しし、cache に残る masstree の
生成物 (`config.h` / archive) があるから関門の preprocess が通っていた。job 内で cache から pristine な staging を
hydrate し、緑の 2 例と同じ `prepare_masstree_fetchcontent` で masstree を 1 回 build してから関門と両 build に
渡す形へ揃え、計算ノードの実経路で S6 go に到達した (request `0:4163.nqsv`)。関門の受理集合は変えていない。

## 何を変えたか (`tools/pegasus/probes/t316_sandbox_backend_probe.py`、同 `.pbs`、`orchestrator/tests/test_t316_sandbox_probe.py`)

1. **hydrate (job 内、実 CLI)。** `observe_s6` が scratch の兄弟に staging S (`TemporaryDirectory`、prefix
   `t316-s6-thirdparty-`) を作り、`python3 -I -B tools/pegasus/fetch_third_party.py hydrate --repo-root <repo>
   --cache-root <cache> --staging-root <S>` を `_run_command` で 1 回走らせる。cache は hydrate の**入力にだけ**使う。
   失敗 (rc≠0 / timeout / JSON 解読不能) は `failure_stage="third-party-hydrate"` で fail-closed にし、identity を採らずに
   返す (verdict は `S6_SOURCE_IDENTITY_INVALID`)。timeout は `min(ccbench_build_cap_s, 残時間-1)`。
2. **identity は S 側。** third-party 3 本の `source_heads` / `source_identities` は hydrate 後・prepare 前に S から採る
   (gflags / glog は T139 root、ccbench は submodule のまま)。
3. **prepare は outside で 1 回、関門の前。** `_execute_ccbench_build(inside=False)` の gflags / glog install 後に
   `buildcache.prepare_masstree_fetchcontent(ccbench_dir=<patch 済み requested 木>, fetchcontent_base_dir=<scratch>/fetchcontent,
   masstree_source_dir=<S>/masstree, …, expected_toolchain_manifest=observed_toolchain_manifest(cc, cxx),
   dependency_prefix=<scratch>/s6-outside/install, configure_timeout_s ≤ 300, target_timeout_s ≤ 1200)` を呼ぶ。失敗は
   `masstree-prepare` / `masstree-prepare-configure` / `masstree-prepare-build` で fail-closed にし、**prepare の後に改めて
   `if failure_stage is None:` で関門へ入る** (verdict は `S6_CONDITION_GATE_UNPROVEN`)。inside では prepare しない。
4. **関門・outside・inside の configure は `-DFETCHCONTENT_SOURCE_DIR_*=<S>/<name>` だけ。** `-DFETCHCONTENT_BASE_DIR` は
   渡さない (各 build root の `_deps` 既定)。masstree の custom command は OUTPUT (`config.h` と archive) が source dir に
   実在すれば再実行しないので、host の prepare 1 回で sandbox 内 (S は ro-bind) の build も通る。
5. **S6 profile の `readonly_roots` に S を足す。** S1〜S5 の profile (cache と T139 root の ro-bind) は変えない。
6. **受領証の S6 に 2 key を足す。** `third_party_staging` (`source_root`、hydrate の `command` 記録、`payload` = CLI の JSON) と
   `masstree_prepare` (`ccbench_dir` / `dependency_prefix` / `source_dirs` (呼び出し前に記録)、base / build dir、timeout、
   成功時の `configure_argv` / `build_argv`、`elapsed_ns`、失敗時の `failure_stage` / `error`)。既存 field と schema
   `t316-sandbox-backend-probe/v1` は変えない。
7. **runtime 束縛の拡張。** `.pbs` の `BOUND_PATHS` と `_BOUND_RELATIVE_PATHS` に `orchestrator/campaign/buildcache.py` と
   `tools/pegasus/fetch_third_party.py` を足した (9 path)。推移的 import は束縛しない (patchharness / gate を足したときと
   同じ粒度)。旧 5 受領証の 7 path 記録には遡及しない (規律 7)。
8. **配線テスト。** fixture は cache に実 git repo 5 本 (origin は policy と同じ HTTPS URL、HEAD = fixture pin)、fixture policy に
   5 source、fixture `ThirdParty.cmake` に literal 6 行 + 実 FetchContent、実 CLI への symlink、masstree fixture は build 時に
   `config.h` と archive 相当の OUTPUT 2 本を source dir に生む `masstree_build`、依存 2 本に package config を install させ
   `find_package(… REQUIRED)` + marker 必須。cache には毒入りの stale `config.h` (`#error`) と archive を残し、build が
   それを include しないことと cache が不変であることを検査する。observer は build / command / gate の call 境界で inline に
   assert する (S は scratch 外・ro-bind・SOURCE_DIR は S・BASE_DIR 不在・関門前に prepare return 1 回)。新規 test:
   `test_s6_live_offline_source_paths_and_prepare_order`、`test_s6_live_staging_is_readonly_outside_scratch` (sandbox 内で
   読めて `EROFS` で書けないことを実測)、`test_s6_hydrate_failure_stops_before_identity_and_gate` (glog の origin 不一致で
   rc=1)、`test_s6_prepare_failure_stops_before_gate[configure|target]`、`test_execution_binding_bound_paths_match_shell_and_literal`、
   `test_execution_binding_python_rejects_dirty_offline_inputs[…]`。

変えていないもの: `condition_meaning_gate.py`、`buildcache.py`、`fetch_third_party.py`、`silo_ladder_rung1.py`、policy JSON、
`_INERT_CONDITION_GATE_PAIRS`、`verdict_s6`、`_require_condition_gate`、D1995 の stderr 診断、投入経路 (`qsub -v` の env 4 本)。

## 実測

### 計算ノード実走 (t316 実経路、request `0:4163.nqsv`、bnode064、gen_S)

Started 23:05:37 / Ended 23:07:21 JST、Elapse 108 秒、probe `elapsed_ns` 102.5 秒 (修正前 `0:999027.nqsv` は 93.3 秒)。
受領証 `output/env/pegasus/t316-sandbox-backend/0:4163.nqsv/receipt.json` (execution_binding: commit `f296e42bc`、
`bound_paths_clean=true`、runtime_sha256 は 9 path + PBS spool)。

| 項目 | 値 |
|---|---|
| S6 | go (`S6_SANDBOX_BUILD_SUCCEEDED`)、`outside_success` / `inside_success` / `trace_disabled` / `source_identity_valid` すべて true、`failure_stage` null |
| supply-effectuation | green / `stock-inert-preprocess-root-location-only` / comparison `stock-inert-root-location-only` |
| runtime-meaning | unestablished / `meaning-witness-undeclared` (現行契約どおり) |
| family-admission | admitted / `raw-measurement` |
| `third_party_staging` | root `/scr/t316-s6-thirdparty-5w3ib2yi`、rc 0、**1.37 秒**、payload 5 source (masstree b3c5d054 / mimalloc 02a2f5df / googletest f8d7d77c / gflags e171aa2d / glog 8f9ccfe7) |
| `masstree_prepare` | attempted / success、**11.39 秒**、timeout 300 / 1200、base `/scr/t316-0_4163.nqsv-twt3er1t/fetchcontent`、build `cmake --build … --target masstree_build -j 48` |
| identity (masstree / mimalloc / googletest) | path は S 配下、valid、`clean_including_untracked` true |
| outside / inside の ccbench-configure | rc 0、0.69 / 0.64 秒、`-DFETCHCONTENT_SOURCE_DIR_*` は 3 本とも S、`-DFETCHCONTENT_BASE_DIR` なし |
| outside / inside の ccbench-build | rc 0、3.94 / 3.96 秒 |
| S7 | go |
| overall | no-go (S3 inconclusive / S5 `S5_BUILD_SYSTEM_COMMAND_SIDE_EFFECT_OBSERVED`; 修正前の 3 走と同じで本 wave の変更面と無関係) |

受領証の build step argv に `izanagi-thirdparty-cache` が現れるのは inside の bwrap `--ro-bind` (S1〜S5 profile の継承) だけで、
configure の参照ではない。prepare の configure argv は `-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCMAKE_C_COMPILER=…gcc-11
-DCMAKE_CXX_COMPILER=…g++-11 -DFETCHCONTENT_BASE_DIR=<base> -DCMAKE_PREFIX_PATH=<outside install> -DFETCHCONTENT_SOURCE_DIR_*=<S>/…`
で、共有 configure が持つ ccache / launcher / toolchain file / CXX flags の空指定を持たない (既知の差、下記)。

### テスト (login node、load 16〜24)

- `test_t316_sandbox_probe.py` 単独: **180 passed / 271 秒** (変更前の基準 commit で同じ login: 166 passed / 112 秒)。
- t316 + consumer 6 file (`test_official_perf_closure.py`、`test_hooks.py`、`test_acceptance_schedule_order.py`、
  `test_real_repo_serialization.py`、`test_ccbench_spawn_sites.py`、`test_plain_runner_coverage.py`): 897 passed / 2 skipped
  (既存の growth hold) / 711 秒。
- 段 6 fix 後の再走 (fix 対象 3 node + 束縛 test): 33 passed。
- 計算ノードでは同 file の baseline (変異 harness) が 48.9 秒。

**テストコストの増分 (login)**: +159 秒/file。単独計測では fixture の git repo 5 本 + clone 2 本の構築が 2.8 秒、実 hydrate CLI が
3.3 秒 (合計 約 6 秒/live test)。live test は 12 本 (既存 8 + 新規 4)。seed を session で共有しても削れるのは 2.8 秒/本で、
hydrate CLI の分は実 CLI を使う限り残る。直近受入では t316 file は shard-2 (175 秒) に入り、壁を決める shard-0 は 336 秒。
本 wave では fixture の共有化を実装せず backlog に置く。

### 変異 matrix — baseline PASSED、13/13 KILLED、期待 node 完全一致、対照 2 件 SURVIVED

台帳は `mutation/mutation-final-ledger.json` (spec `mutation/mutation-spec-final.json`、sha256 `aa604b9d…`)。container worktree
(`.codex/worktrees/t2654-mutcontainer`、HEAD `f296e42bc`) で `run_tests.py orchestrator/tests/test_t316_sandbox_probe.py -q -rf
--force-dispatch` を計算ノードへ dispatch、probe 走 (全件 SURVIVED 登録で観測 node を集める、`mutation/mutation-probe-ledger.json`)
の後に本走。summary は `KILLED=13 / SURVIVED=2 / MISMATCH=0 / TIMEOUT=0 / matching=15`、baseline 52.7 秒、全 anchor 1 箇所
(M7 は 2 置換とも 1 箇所)。

| 変異 | 受理集合・fail-closed への影響 | 期待 node 数 | 専属 killer |
|---|---|---:|---|
| M0 | comment だけの等価変更 (harness の SURVIVED 検出の正例) | 0 (SURVIVED) | — |
| M1 | `SOURCE_DIR_MASSTREE` を cache 直指しへ戻す | 7 | 関門 call 境界の inline assert (source override は S) |
| M2 | prepare を飛ばす | 10 | 関門 call 境界の「prepare return 1 回」+ 失敗系 2 本。うち `test_condition_gate_dominates_ccbench_configure` は変異文字列 `and not inside` に当たる既存の静的 pin で付随的 (機構の kill は 9 本) |
| M3 | 関門は S、build の configure は cache | 6 | configure command 境界の inline assert |
| M4 | S を scratch 内に作る | 9 | build call 境界の「S は scratch 外」 |
| M5 | S6 profile の `readonly_roots` から S を落とす | 9 | build call 境界の「S は ro-bind」 |
| M6 | `_BOUND_RELATIVE_PATHS` から `fetch_third_party.py` を落とす | 4 | 独立 literal 同期 test + Python dirty 拒否 2 node + runtime spool の SHA 照合 |
| M6b | `.pbs` `BOUND_PATHS` から `buildcache.py` を落とす | 3 | 独立 literal 同期 test + shell dirty gate 2 node |
| M7 | hydrate の rc/timeout 検査と JSON 失敗処理の両方を外す (2 置換) | 1 | `test_s6_hydrate_failure_stops_before_identity_and_gate` (`failure_stage` が `dependency-pins` になる) |
| M7b | hydrate の rc 検査だけ外す (JSON 層が遮る冗長 gate 対照) | 0 (SURVIVED) | — |
| M8 | inside でも prepare を呼ぶ | 1 | `test_s6_live_offline_source_paths_and_prepare_order` (prepare call 数 exact 1) |
| M9 | 関門・両 build の configure に `-DFETCHCONTENT_BASE_DIR=<S>` を足す | 7 | 関門 call 境界の inline assert (BASE_DIR 不在) |
| M10 | prepare 失敗後も関門へ進む | 2 | `test_s6_prepare_failure_stops_before_gate[configure|target]` |
| M11 | prepare の `dependency_prefix` を落とす | 8 | prebuild configure が `find_package(… REQUIRED)` で失敗 → outside 失敗 (fixture の package config 必須化が効く) |
| M12 | third-party の identity を S でなく cache から採る | 1 | `test_s6_live_offline_source_paths_and_prepare_order` (identity path 集合) |

M1 / M2 / M9 / M11 の最初の赤理由は段 4 の事前登録 (command 境界・preprocess・`outside_success`) でなく、共有 observer の
gate call 境界の assert が先に発火する (段 6 レビュー RA-3 の指摘どおり、台帳の説明を上表に合わせた)。M4 / M5 / M9 は build 失敗より
前に inline assert で赤になる (段 3 A-8)。M7 の 2 置換は JSON 解読失敗の層が rc 検査を隠す (A-7) ため。

## 保証しないこと・既知の限界

- **prepare の configure は共有 configure と同じ抑制条件を持たない。** `prepare_masstree_fetchcontent` の argv は固定で、
  `-DCCBENCH_CCACHE=OFF` / `-DCMAKE_*_COMPILER_LAUNCHER=` / `-DCMAKE_TOOLCHAIN_FILE=` / `-DCMAKE_CXX_FLAGS=` を渡せない。
  masstree の実体は autotools + make なので CMake launcher は効かないが、prebuild 側の mimalloc / googletest の configure 条件は
  本走 build と同一ではない (共有 helper は変えない裁定)。
- **timeout は子孫停止・撤去まで保証しない。** hydrate は `_run_command` の kill 後 `communicate()` と S の撤去が無制限、prepare は
  `buildcache._run` の `subprocess.run(timeout=)` だけで子孫 (make / compiler) を止めず、`observed_toolchain_manifest` の version
  取得には timeout が無い。walltime 直前の受領証終端は保証しない (段 4 で受容)。SIGKILL / walltime 強制終了では S も requested 木も
  contextmanager の撤去が走らない。
- **関門例外時は新観測 2 key も消える。** `_require_condition_gate` の例外は `observe_s6` を抜け、`run_probe` が `attempted=False`
  の汎用観測に置き換える既存設計 (D1995 の stderr 診断は残る)。本 wave は変えていない。
- **prepare のトップレベル `failure_stage` は `outside-control`。** prepare の具体的 stage 名は `outside_build.failure_stage` と
  `masstree_prepare.failure_stage` に残る (既存の集約規則)。
- **hydrate の payload は `_run_command` の stdout tail (16 KiB) から読む。** 現行 CLI の出力 (約 1.5 KB) は収まる。超えると
  JSON 解読失敗で fail-closed になる (fail-open ではない)。
- **fixture の忠実度。** fixture の masstree は `config-template.h` の copy と空 archive で、本物の autotools / archive の実体は検証しない。
  package config も marker だけで imported target を再現しない。本物の到達は計算ノード実走 (上表) で示す。
- **hydrate 時の pristine 性が使用時まで続くとは主張しない** (D2085 と同じ限界)。identity は hydrate 後・prepare 前の記録。
- **計算ノードは外部 network 不在、時刻・所要は環境固有。** 段 3 が指摘したとおり、親の事実のうち「network 不在」の一般化と
  login の所要は一次記録の範囲で読む。`/scr` の hydrate 1.37 秒・prepare 11.39 秒は本走 1 回の値。
- S3 / S5 の no-go は別起票のまま。

## 段 3・段 6 が親を訂正した点

- 親 brief は `test_ccbench_spawn_sites.py` の台帳登録が要ると書いたが、`_PRODUCTION_DIRS` は orchestrator 配下だけで、
  `prepare_masstree_fetchcontent` は sink の名前・literal のどちらにも当たらない (段 3 レンズ B、B-12)。
- 親 brief は `_verify_pristine_floor_dependency_sources` を使わない理由に D2085 を引いたが、D2085 は gflags / glog の使用直前
  検査に限った決定で、二重検査一般の禁止ではない (段 3 レンズ A、A-4)。理由は「hydrate 自身が生成時に検証する・A-2 の複製経路を
  導入しない・追加 gate は scope 外」に改めた。
- 親 brief の不変条件「追加は S6 観測内の新 key に限る」は runtime 束縛 map の 2 件拡張と字義で矛盾した (A-13)。
- 時間予算は見積りに降格した (A-10 / B-7)。実測は上表。
- 変異 (g) 「hydrate の rc を無視」は JSON 解読失敗が先に遮るので 2 置換 (rc 検査 + JSON 失敗処理) に再照準し、rc 検査だけの
  変異は冗長 gate 対照 (SURVIVED 期待) として登録した (A-7)。
- 変異 (d)/(e)/(i) は observer の inline assert で build 失敗より前に赤にする形にした (A-8)。
- 段 6 レビュー 2 本は must-fix なし。should-fix (prepare 失敗時に呼び出し入力が受領証に残らない、RA-1 / RB-2) を fix した。

## 逐語

`verbatim/` に段 1 brief、段 2 plan、段 3 の 2 レンズ、段 4 裁定、段 5 実装子報告、段 6 レビュー 2 本と fix 報告、
親の実測事実 (`facts-offline-supply.md`) を置く。変異台帳は `mutation/`。

codex 出力 5 本は markdown の改行 (行末の空白 2 個) が `git diff --check` に当たるため、可視文字を変えない可逆最小正規化
(行末の空白だけを除去) を施した。原文の identity と復元法は次のとおり (復元 = 下記の行数だけ行末に空白 2 個を戻す。
どの行かは job dir の原本 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2654-t316-hydrate-base/<同名>.md` が持つ)。

| file | 原文 sha256 | 原文 bytes | 正規化後 bytes | 行末空白を除いた行数 |
|---|---|---:|---:|---:|
| `s2-plan-out.md` | `accdd2894aa69451b839071e2ea4f6744e0724ecc05eb5bdf3ca6a6484ffb712` | 25426 | 25422 | 2 |
| `s5-author-out.md` | `5d4472124e03859d95743fe4f57a91291b9cce74af21fdd210a45ccfde2efccd` | 6126 | 6122 | 2 |
| `s6-fix1-out.md` | `26c2c553156dbf5f5119219e30c95dda647c596dd1c2cd01f547524d1b824f1b` | 2634 | 2630 | 2 |
| `s6-reviewA-out.md` | `ecc8a04d38c8f2a133e04329792c35d925b7e73bc085d1cb4c93263709b7ff55` | 13825 | 13819 | 3 |
| `s6-reviewB-out.md` | `a09e0477eb7664bec366b7731e7a954e8c3e3f3ae95ac4c71b4c82cbd37a4b8a` | 12191 | 12177 | 7 |
