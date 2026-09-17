# 段 1 brief — [T-2654] t316 の条件関門を hydrate 済み staging + `prepare_masstree_fetchcontent` の準備済み base へ合流させる

wave: `dev-wave-t2654-t316-hydrate-base` / branch: `worktree-dev-wave-t2654-t316-hydrate-base`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2654-t316-hydrate-base`
基準: `38353207f719acb0871cfe3d9bbe3a02490282bb` (local main、着手直前)

## 研究前進 (土台)

t316 probe の S6 go (`0:999027.nqsv`、2026-09-15) は、8c 無人ループの sandbox backend を計算ノードで採れるという
go/no-go の唯一の実測証拠である。その関門の緑は永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` に
残る生成物 (`config.h`、`libkohler_masstree_json.a`; 本日も実在、ignored 40 件) に依存しており、cache を掃除した瞬間に
再現できなくなる (t2607 insight「保証しないこと」第 1 項)。最小差分 = t316 の S6 が、緑の 2 例 (A-2、backoff_sweep
driver 段) と同じく **hydrate 済み pristine staging を `prepare_masstree_fetchcontent` で準備してから** 関門と両 build に
渡す形にする。完了判定 = (a) 計算ノードの実経路 1 走で S6 go に到達し、受領証の configure argv の
`FETCHCONTENT_SOURCE_DIR_*` が永続 cache でなく hydrate staging を指し、hydrate と prepare の記録が受領証にある、
(b) login の配線テストが実 hydrate + 実 prepare を fixture で通す。

## 確定済みユーザー裁定 (起動引数 + D2044 項 27)

既存機構への合流であり新しい仕組みは作らない。過去の測定事実 (5 受領証) は無効化しない (規律 7)。実装面は Codex author
(D95)、変異事前登録要。計算ノードでの実走は既存 probe の経路 (同じ `qsub -v … t316_sandbox_backend_probe.pbs`) で 1 回。
規律 2 を緩めない。本題の合流だけ。追加の gate・台帳は scope 外。D1625 (t316 関門は exact 一致のみ、緩和なし) と
D2032 (関門と build は同じ patch 済み使い捨て木) は不変。D2085 (使用直前の hydrate 同等検証は足さない) に従い、
hydrate 自身の `reject_ignored=True` 検証を超える検査は足さない。

## 不変条件

1. 関門が検査する木と build する木は同一 (D2032)。third-party source も関門・outside・inside の 3 者で同一 path。
2. 規律 2 — `condition_meaning_gate` の受理集合、`_INERT_CONDITION_GATE_PAIRS`、`verdict_s6` の拒否枝 4 本、
   `-DCCBENCH_BACKOFF_FIXED=-1` の要求、source_identity / trace-disabled 検査、D1995 の stderr 診断は緩めない。
3. 永続 cache を **読む** (hydrate の入力) のはよいが、関門・build の configure argv から cache 直指しを消す。
4. sandbox 内で source (requested 木・third-party source) が書けない性質を保つ (現行: cache は ro-bind、requested は
   scratch 外の ro-bind)。
5. 受領証 schema `t316-sandbox-backend-probe/v1` の既存 field は変えない。追加は S6 観測内の新 key に限る。
6. `orchestrator/campaign/condition_meaning_gate.py`、`buildcache.py`、`fetch_third_party.py` は 1 byte も変えない。
7. 既存テストの期待値を甘くして緑にしない。赤なら実装側が誤り。

## (P) 親の provisional 裁定 — 段 3 の攻撃対象

- (P1) **hydrate は job 内で Python から行う。** `observe_s6` が `IZANAGI_PEGASUS_THIRDPARTY_CACHE` を入力に
  `python3 tools/pegasus/fetch_third_party.py hydrate --repo-root <repo> --cache-root <cache> --staging-root <S>` を
  subprocess で 1 回起動する (先例: `tools/pegasus/mocc_trace_pilot.sh:1534`、job 内 hydrate)。投入経路 (`.pbs` の env
  4 本、qsub 形) は変えない。採らない案: A-2 / certify 型の「親が login で hydrate → 新 env var で staging を渡す」
  (新しい submit 入力を足す。D2084 も新 env を足さないと定めた)。
- (P2) **staging root S は requested 木と同じ置き方** (`scratch.parent` 配下、`_s6_requested_checkout` と同じ理由で
  scratch の writable bind に覆われない) にし、S6 profile の `readonly_roots` に足す。hydrate 出力の layout
  `<S>/{masstree,mimalloc,googletest,gflags,glog}` をそのまま使い、A-2 の `<base>/<name>-src` への `cp -a` 並べ替えと
  `_verify_pristine_floor_dependency_sources` は使わない (hydrate が `reject_ignored=True` で pristine を検証済み。
  二重検査は D2085 の射程)。gflags / glog は `IZANAGI_T139_DEPENDENCY_SOURCE_ROOT` のまま (本題外)。
- (P3) **prepare は host で 1 回、outside の gflags/glog install 後・関門の前。** `buildcache.prepare_masstree_fetchcontent(
  ccbench_dir=requested_root, fetchcontent_base_dir=<scratch>/fetchcontent, masstree_source_dir=<S>/masstree, mimalloc…,
  googletest…, expected_toolchain_manifest=buildcache.observed_toolchain_manifest(cc, cxx), configure_timeout_s,
  target_timeout_s, dependency_prefix=<outside prefix>)`。site は未指定 (計算ノードで PEGASUS_COMPUTE に解決、
  テストは conftest が OTHER に中和)。関門・outside・inside の configure には `-DFETCHCONTENT_SOURCE_DIR_*=<S>/<name>`
  だけを渡し `-DFETCHCONTENT_BASE_DIR` は渡さない (masstree の custom command は OUTPUT が source dir に実在すれば
  再実行しないので、各 build root の `_deps` 既定で通る; `<base>/mimalloc-build` を outside/inside で共有しない)。
  inside は prepare を繰り返さない (S は sandbox 内 ro)。masstree の warm-up を probe 内の生 `cmake --build --target
  masstree_build` で書くと `test_ccbench_spawn_sites.py` の `direct-cmake-target` sink が 1 つ増え define × sink の
  gate 被覆登録が要る — `prepare_masstree_fetchcontent` 経由なら sink にならない (`.build`/`.build_v2` 名でも
  `--build`/`--target` literal でもない)。これも prepare を使う理由。
- (P4) **runtime 入力の束縛は既存規約どおり広げる。** `fetch_third_party.py` と `buildcache.py` が S6 の実行入力になるので、
  `.pbs` の `BOUND_PATHS` と `_BOUND_RELATIVE_PATHS` (runtime_sha256) に足す (t2607 が patchharness / gate を足した
  のと同じ規約)。新しい gate ではない。
- (P5) **受領証への記録** は S6 観測に `third_party_staging` (hydrate CLI の JSON payload と argv/rc) と
  `masstree_prepare` (prepare の configure_argv / build_argv / 所要) を足す。`source_heads` / `source_identities` の
  third-party 3 本は build に使う S 側を見る (cache 側でなく)。`identities` の期待 pin は policy のまま。
- (P6) **時間予算**: 前回実走 98 秒 + hydrate (5 source、/scr、数秒〜十数秒) + prepare (configure + masstree 13 秒) で
  `ccbench_build_cap_s=1200` / `s6_minimum_remaining_s=3600` の内側。policy JSON は変えない。hydrate の timeout は
  mocc_trace_pilot の 20 秒でなく NFS 実測 (85 秒) を超える値を deadline 残から与える。

## 成果物の形

Codex author による `t316_sandbox_backend_probe.py` / `.pbs` / `test_t316_sandbox_probe.py` の変更。配線テストの
fixture (`_s6_live_fixture`) は実 hydrate + 実 prepare を通す (fixture repo に policy.json の 5 source と
`external/ccbench/cmake/ThirdParty.cmake` の literal、fixture cache の git repo 3 本 (pin = fixture HEAD)、
`masstree_build` target)。計算ノード実走 1 回の受領証 (`output/env/pegasus/t316-sandbox-backend/<request>/`)。
insight (逐語 + 変異台帳)、worklog / decisions / failures の spool fragment。

## 実測環境

login node: 焦点走 (`test_t316_sandbox_probe.py` + consumer `test_official_perf_closure.py`、`test_hooks.py`、
`test_acceptance_schedule_order.py`、`test_real_repo_serialization.py`、`test_ccbench_spawn_sites.py` (spawn site が
増える)、`test_plain_runner_coverage`)。計算ノード: t316 実経路 1 走 (gen_S、既存 admission 登録済み、新規実行体なし)、
変異 matrix は dispatch。永続 cache は本日 `config.h` 実在 → 実走の緑が cache 残留由来でないことは configure argv が
cache を指さないことで示す (cache を掃除して示すのは scope 外・他 wave に影響)。

## 分割方針

実装面あり → 軽量版にしない。段 2 plan 1 本、段 3 敵対 2 レンズ並列、段 5 実装子 1 本 (所有: probe.py / .pbs / test)、
段 6 レビュー 2 本 + fix、変異 matrix 免除なし。

## 変更面の実アンカー表

| path | anchor | 役割 |
|---|---|---|
| `tools/pegasus/probes/t316_sandbox_backend_probe.py` | `_execute_ccbench_build` の `configure` list (`-DFETCHCONTENT_SOURCE_DIR_*={cache_root / …}`) | cache 直指しの本体。関門 (`configure[5:]`) と両 build が共有 |
| 同上 | `observe_s6` (`cache_root = Path(os.environ["IZANAGI_PEGASUS_THIRDPARTY_CACHE"])`、`source_heads`、`identities`、`_s6_requested_checkout` の with、`s6_profile = SandboxProfile(... readonly_roots + requested_root)`) | hydrate / prepare を差し込む位置、identity と ro-bind の対象 |
| 同上 | `_s6_requested_checkout` | staging root の置き方の先例 (scratch.parent、TMPDIR 退避) |
| 同上 | `_BOUND_RELATIVE_PATHS` / `_execution_binding` | runtime_sha256 の束縛一覧 |
| 同上 | `run_probe` の `readonly_roots = [cache, deps]` | S1〜S5 の profile (変えない) |
| `tools/pegasus/probes/t316_sandbox_backend_probe.pbs` | `BOUND_PATHS=(` … `)` | commit 束縛一覧 (py 側と同期 test あり) |
| `orchestrator/tests/test_t316_sandbox_probe.py` | `_s6_live_fixture` (`third_party_sources: []`、`cache = tmp_path/"cache"` 空)、`_observe_s6_wiring`、`test_execution_binding_*`、`_BOUND_RELATIVE_PATHS` の pin | 配線テストと束縛 pin |
| `orchestrator/campaign/buildcache.py` | `prepare_masstree_fetchcontent` (:2034)、`observed_toolchain_manifest` (:1276) | 呼ぶだけ。変えない |
| `tools/pegasus/fetch_third_party.py` | `main` / `_hydrate` (`--staging-root`、`reject_ignored=True`) | 呼ぶだけ。変えない。`_load_policy` が `policy.json` 5 source + `ThirdParty.cmake` literal を要求 |
| `orchestrator/campaign/paper_story_a2_certification.py` | `_condition_gate_family_context` (:679-720) | 緑の先例 1 (prepare → capture) |
| `orchestrator/campaign/backoff_sweep.py` | :437-465 | 緑の先例 2 (一時 base で prepare → 関門) |

## 模擬 / 実の差

- 段 1 で実測したのは: 永続 cache の生成物実在、hydrate CLI の契約 (`_load_policy` / `_hydrate`)、prepare の契約と
  site 拒否、sandbox bind 構成、受領証の現行 argv。**hydrate + prepare を t316 の requested 木に対して通した実測はまだ無い**
  (段 5 の login 配線テストと段 6 の計算ノード実走で得る)。
- 変異事前登録は段 4 で確定する (候補: cache 直指しへ戻す / prepare を飛ばす / 関門だけ staging・build は cache /
  staging を scratch 内へ置く / readonly_roots から S を落とす / BOUND_PATHS から 1 件落とす / hydrate の rc 無視)。
