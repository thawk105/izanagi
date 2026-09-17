# 段 4 裁定 — [T-2654] t316 の hydrate + prepare 合流 (plan v2 と変異事前登録)

日時: 2026-09-17 22:10 JST / 親 (Claude) / 入力: `s1-brief.md`、`s2-plan-out.md`、`s3-lensA-out.md`、`s3-lensB-out.md`
裁定 inbox 再走査: main は 05eca6af4 (D2116〜D2120) へ前進、T-2654 / t316 / 対象 file に触れる項は無し。

## 所見の裁定 (real / refuted、採否、scope)

| 所見 | 判定 | 採否 | 扱い |
|---|---|---|---|
| A-1 (prepare は供給側の正常化、受理集合は不変) | refuted (親支持) | — | 記録: 「cache 直指しと受理集合が同じ」とは書かず、「関門の判定規則は同じ、到達集合は変わる」と記す |
| A-2 (hydrate 失敗 → `S6_SOURCE_IDENTITY_INVALID`、prepare 失敗 → `S6_CONDITION_GATE_UNPROVEN`) | refuted (規律 2 の穴なし) | 採用 (test 要件) | 失敗系 test は `failure_stage` に加え `verdict_s6` の理由コードを上表どおり assert する |
| A-3 (host 関門と sandbox の S 同一性) | refuted | — | 配置と bind の実検査を test に置く (M4/M5) |
| A-4 (D2085 の射程拡大) | **real** | 採用 (brief 文言) | (P2) の理由を「hydrate 自身が生成時に pristine を検証済み・A-2 の複製経路を導入しない・追加 gate は scope 外」に置き換える。D2085 は先例に留める |
| A-5 (D2032 却下欄は禁止でない) | refuted | — | 「同じ準備済み source を供給する合流」と記述し、先例の緑を本構成の証拠に転用しない |
| A-6 (変異 (a) の killer 実在) | refuted | — | fixture は cache に実 git repo 5 本 |
| A-7 (変異 (g) は JSON 解読失敗が遮る) | **real** | 採用 (事前登録) | (g) は 2 置換 (rc 検査 + JSON 失敗処理の両方を外す) で 1 理由に絞る。rc 検査だけ外す変異は冗長 gate 対照 (SURVIVED 期待) として別登録 |
| A-8 (d/e/i の assertion 発火時点) | **real** | 採用 (test 設計) | observer は `_execute_ccbench_build` の call 境界と configure argv の command 境界で **inline に assert** し、build 失敗より前に狙った理由で赤にする |
| A-9 (b/c/f/h の帰属) | refuted (条件付き) | 採用 | call 数等は記録して `except Exception` の外で検査する |
| A-10 (時間予算の外挿) | **real** | 採用 (brief 文言) | (P6) は見積りに降格。実証は計算ノード実走 1 回 |
| A-11 (親の事実の未検算一般化) | **real** | 採用 (記録) | insight に「一次記録未検算」の区別を書く。network 不在の一般化と時刻の出所を削る |
| A-12 (規律 7) | refuted | — | 束縛拡張は新実行の記録拡張。旧受領証への遡及なし |
| A-13 (brief 不変条件 5 と P4 の字義) | **real** | 採用 (brief 文言) | 「S6 観測 2 key + runtime 束縛 map の 2 件拡張。旧受領証への遡及要求なし」と明記 |
| A-14 (新設なし) | refuted | — | 実装項目はすべて合流 |
| A-15 (sink 不検出は安全性の証明でない) | refuted (親の書き方) | 採用 (文言) | prepare を使う理由は「必要な依存準備を既存 helper で行う」に置く |
| B-1〜B-3, B-5, B-6, B-8, B-9, B-11 | refuted (実効性あり) | — | plan どおり |
| B-4 (prepare の固定 configure は ccache/launcher 抑制を持たない) | **real** | 採用 (既知の差) | `buildcache.py` は変えない。差を insight の限界に書き、実走の `masstree_prepare.configure_argv` と成功で確認 |
| B-7 (所要は見積り、受領証の elapsed は 93.3 秒) | **real** | 採用 (文言) | 「93 秒 + hydrate 15.75 秒 (Lustre 実測) + prepare 13 秒 (別 runner 実測) 前後」を見積りとし上限を主張しない |
| B-10 (fixture が dependency_prefix 欠落と archive 欠落を見逃す) | **real** | 採用 (fixture) | fixture 依存 2 本に package config を install させ fixture CCBench で `find_package(... REQUIRED)`; masstree custom command は OUTPUT 2 本 (config.h + archive 相当) |
| B-12 (spawn-site / build-sink 登録は不要) | real (親 brief の誤り) | 採用 | 焦点走の consumer から `test_ccbench_spawn_sites.py` の**登録**要求を外す (走らせるのは可) |
| B-13 (束縛 fixture bytes と投入直前の clean) | **real** | 採用 | `bound_bytes` +2、shell param +2、投入前に 9 path の HEAD blob 一致を確認 |
| B-14 / B-15 (timeout は子孫停止・撤去を保証しない、manifest は timeout なし) | **real** | 採用 (限界明記) | 共有 helper は変えない。insight の「保証しないこと」に書く。test は `failure_stage` と S 撤去まで確認する |
| B-16 (P1〜P5 の条件) | 条件付き支持 | 採用 | 下記 plan v2 |

## plan v2 (確定)

段 2 plan の「実装子への指示」14 項を基本とし、次を上書き・追加する。

1. **(P1) 採用。** hydrate は `observe_s6` 内で `_run_command([sys.executable, "-I", "-B", <repo>/tools/pegasus/fetch_third_party.py, "hydrate", "--repo-root", <repo>, "--cache-root", <cache>, "--staging-root", <S>])` を 1 回。timeout = `min(ccbench_build_cap_s, remaining_s - 1)`、`remaining_s < 30` は `walltime`。
2. **(P2) 採用。** S = `tempfile.TemporaryDirectory(prefix="t316-s6-thirdparty-", dir=scratch.resolve(strict=True).parent)` の contextmanager `_s6_third_party_staging(scratch)`。hydrate〜両 build を囲み、早期 return・例外でも撤去。S6 profile の `readonly_roots` に `staging_root` を足す。`_verify_pristine_floor_dependency_sources` と `<name>-src` 複製は導入しない (理由は A-4 の是正どおり)。
3. **(P3) 採用 (条件付き解消)。** prepare は `_execute_ccbench_build(inside=False)` の依存 6 command 成功後・関門前に 1 回。引数は plan の表どおり (compiler は既存 `shutil.which` 解決、manifest は `buildcache.observed_toolchain_manifest(compiler_c, compiler_cxx)`、`fetchcontent_base_dir=<scratch>/fetchcontent` (mkdir 済み canonical)、`dependency_prefix=str(prefix)`、site 省略)。関門・outside・inside の configure は `-DFETCHCONTENT_SOURCE_DIR_*=<S>/<name>` だけ (BASE_DIR は渡さない)。prepare 後に改めて `if failure_stage is None:` で関門へ入る。inside は prepare しない。**既知の差 (B-4):** prepare の configure は ccache / launcher / toolchain file / CXX flags の空指定を持たない — 記録し実走で確認。
4. **(P4) 採用。** `.pbs` `BOUND_PATHS` と `_BOUND_RELATIVE_PATHS` に `tools/pegasus/fetch_third_party.py`、`orchestrator/campaign/buildcache.py` を同期追加。推移的 import は束縛しない (現行粒度の踏襲)。brief 不変条件 5 は A-13 どおり改める。
5. **(P5) 採用。** third-party 3 本の `source_heads` / `identities` は hydrate 後・prepare 前に S から採る (gflags/glog は T139 root、ccbench は submodule のまま)。S6 観測に `third_party_staging` (`source_root`、`command` = `_run_command` 記録、`payload` = hydrate JSON or null+error) と `masstree_prepare` (`attempted`、`success`、`fetchcontent_base_dir`、`build_dir`、`configure_argv`、`build_argv`、`configure_timeout_s`、`target_timeout_s`、`elapsed_ns`、失敗時 `failure_stage` と error) を足す。既存 field は不変。
6. **(P6) 見積りに降格。** 実証は計算ノード実走 1 回。
7. **failure_stage 名:** `third-party-hydrate` / `masstree-prepare` / `masstree-prepare-configure` / `masstree-prepare-build` / `walltime`。hydrate 失敗は identity 未採取のまま `success=False` (verdict は `S6_SOURCE_IDENTITY_INVALID`)、prepare 失敗は identity=true・関門 family 空 (verdict は `S6_CONDITION_GATE_UNPROVEN`)。verdict の規則は変えない。
8. **fixture (`_s6_live_fixture`):** plan §「配線テスト fixture」に B-10 を加える — (i) cache に git repo 5 本 (masstree / mimalloc / googletest / gflags / glog、origin は policy と一致する HTTPS URL、HEAD = fixture pin)、(ii) fixture `tools/pegasus/policy.json` に 5 source (`third_party_sources` 3 件 exact key + `gflags_source_url` / `gflags_expected_head` / `glog_*`)、(iii) fixture `external/ccbench/cmake/ThirdParty.cmake` に literal 6 行 + 実 FetchContent (masstree Populate、mimalloc / googletest MakeAvailable)、(iv) fixture `tools/pegasus/fetch_third_party.py` は実 file への symlink、(v) masstree fixture: tracked `config-template.h` → `${masstree_SOURCE_DIR}/config.h` と archive 相当の第 2 OUTPUT を build 時に生む `add_custom_command` + `masstree_build` target、tracked `.gitignore` に `/config.h` と第 2 OUTPUT、(vi) stock `transaction.cc` に `#include <config.h>`、ycsb target に masstree include dir と `add_dependencies`、(vii) 依存 fixture 2 本に最小 package config を install させ、fixture CCBench で `find_package(gflags REQUIRED)` / `find_package(glog REQUIRED)`、(viii) gate failure fixture は `CMAKE_BINARY_DIR` が `/izanagi-masstree-prebuild$` のとき fatal error を出さない。
9. **observer (`_observe_s6_wiring`):** 実 `prepare_masstree_fetchcontent` の call/return を watched に追加。**inline assert** を (a) `build` call 境界で「S は scratch 外」「S ∈ profile.readonly_roots」、(b) configure argv を持つ command 境界で「SOURCE_DIR_* == S/<name>」「`-DFETCHCONTENT_BASE_DIR` 不在」、(c) `gate` call 境界で「prepare return を 1 回観測済み」に置く。call 数・path の集合は記録して `observe_s6` の外で検査する。
10. **変更禁止:** `condition_meaning_gate.py` / `buildcache.py` / `fetch_third_party.py` / `silo_ladder_rung1.py` / policy JSON / docs。

## 変異事前登録 (意図と killer。`old`/`new` の anchor は実装後・段 6 fix 前に確定 — DW-M01/M07)

| id | category | 変異 | 期待 | killer (test node、prefix `orchestrator/tests/test_t316_sandbox_probe.py::`) |
|---|---|---|---|---|
| M0 | positive | comment だけの等価変更 | SURVIVED | — (harness の SURVIVED 検出の正例) |
| M1 | negative | `configure` の SOURCE_DIR_MASSTREE を `cache_root / 'masstree'` 直指しへ戻す | KILLED | `test_s6_live_offline_source_paths_and_prepare_order` (command 境界の inline assert) |
| M2 | negative | prepare 呼び出しを外す | KILLED | 同上 (gate 境界の「prepare 1 回観測済み」) + `test_s6_live_requested_gate_and_both_build_roots_match` (関門 preprocess の `config.h` 欠落) |
| M3 | negative | 関門には S、build の configure は cache | KILLED | `test_s6_live_offline_source_paths_and_prepare_order` |
| M4 | negative | S を `scratch` 内に作る | KILLED | `test_s6_live_staging_is_readonly_outside_scratch` (build 境界の inline assert) |
| M5 | negative | S6 profile の `readonly_roots` に S を足さない | KILLED | 同上 |
| M6 | negative | `_BOUND_RELATIVE_PATHS` から `fetch_third_party.py` を落とす | KILLED | `test_execution_binding_bound_paths_match_shell_and_literal` + `test_execution_binding_python_rejects_dirty_offline_inputs` |
| M6b | negative | `.pbs` `BOUND_PATHS` から `buildcache.py` を落とす | KILLED | `test_execution_binding_bound_paths_match_shell_and_literal` + `test_execution_binding_shell_dirty_gate[buildcache-*]` |
| M7 | negative (2 置換) | hydrate の rc/timeout 検査と JSON 失敗処理の両方を外す | KILLED | `test_s6_hydrate_failure_stops_before_identity_and_gate` (実 CLI、glog origin 不一致で rc=1 → `failure_stage == "third-party-hydrate"`、identity 未採取、verdict `S6_SOURCE_IDENTITY_INVALID`) |
| M7b | positive | hydrate の rc 検査だけ外す (JSON 層が遮る冗長 gate 対照) | SURVIVED | — |
| M8 | negative | inside でも prepare を呼ぶ | KILLED | `test_s6_live_offline_source_paths_and_prepare_order` (prepare call 数 exact 1) |
| M9 | negative | 関門・両 build の configure に `-DFETCHCONTENT_BASE_DIR=<S>` を足す | KILLED | 同上 (command 境界の inline assert) |
| M10 | negative | prepare 失敗後も関門へ進む (`if failure_stage is None` を外す) | KILLED | `test_s6_prepare_failure_stops_before_gate[configure]` / `[target]` |
| M11 | negative | prepare の `dependency_prefix` を落とす | KILLED | `test_s6_live_requested_gate_and_both_build_roots_match` (prebuild configure が `find_package REQUIRED` で失敗 → `outside_success False`) |
| M12 | negative | third-party の identity を S でなく cache から採る | KILLED | `test_s6_live_offline_source_paths_and_prepare_order` (identity 境界の path 集合) |

probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本走 (前 wave と同手順)。runner は `run_tests.py` で `test_t316_sandbox_probe.py` 1 file、dispatch。

## brief の訂正 (A-4 / A-10 / A-13 / B-12 / A-15)

- 不変条件 5: 「受領証の既存 field は変えない。追加は S6 観測の 2 key と、runtime 束縛 map (`runtime_sha256`) の対象 2 件の拡張に限る。旧受領証への遡及要求はしない」。
- (P2) の理由: 「hydrate 自身が生成時に `reject_ignored=True` で pristine を検証する。A-2 の複製経路 (`<name>-src` + `_verify_pristine_floor_dependency_sources`) は本経路に無いので導入しない。追加 gate は依頼で scope 外」。D2085 は同種の scope 判断の先例。
- (P3) の理由: 「必要な依存準備を既存 helper で行う」。sink scanner の不検出は根拠にしない。
- (P6): 見積り。上限を主張しない。
- 実測環境: `test_ccbench_spawn_sites.py` の台帳登録は不要 (`_PRODUCTION_DIRS` は orchestrator 配下のみ、prepare は sink でない)。焦点走には含めてよい。

## 段 5 の分割

実装子 1 本 (Codex author、workspace-write)。所有: `tools/pegasus/probes/t316_sandbox_backend_probe.py`、
`tools/pegasus/probes/t316_sandbox_backend_probe.pbs`、`orchestrator/tests/test_t316_sandbox_probe.py`。
子は login で焦点走 (`python3 -m pytest orchestrator/tests/test_t316_sandbox_probe.py -x -q` 相当) を走らせてよい
(bwrap 要の node は子の sandbox で `NETLINK_ROUTE` 不可のため赤になりうる — 前 wave の実測。その赤は「実走不能」と申告し、親が login で実走する)。
