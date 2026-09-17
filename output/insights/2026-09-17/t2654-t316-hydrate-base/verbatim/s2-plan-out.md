## 変更面 (observe_s6 / _execute_ccbench_build)

行番号は現状のもの。以下では編集対象を次の略称で記す。

- `probe.py` = `tools/pegasus/probes/t316_sandbox_backend_probe.py`
- `probe.pbs` = 同ディレクトリの `t316_sandbox_backend_probe.pbs`
- `test.py` = `orchestrator/tests/test_t316_sandbox_probe.py`

**hydrate → S 側 identity → requested 基底 identity → patch → outside 依存 install → prepare → 関門 → outside build → inside 関門・build** の順にする。関門の実装・受理集合は変更しない。

1. **staging の寿命と位置 — `probe.py:1985` 付近**

   `_s6_requested_checkout` の隣に `_s6_third_party_staging(scratch)` contextmanager を置く。既存 requested checkout helper は変更しない。

   `tempfile.TemporaryDirectory(prefix="t316-s6-thirdparty-", dir=scratch.resolve(strict=True).parent)` で空 directory S を作り、canonical `Path` を yield する。空の既存 directory は hydrate が受理するので、そのまま S にできる。環境変数 `TMPDIR` の変更は不要。

   S は scratch 外に置く。既存 requested 木と同様、後続の writable scratch bind に覆われない配置を守る。S の context は hydrate、identity、両 build 全体を囲み、早期 return・関門例外でも撤去する。

2. **hydrate — `probe.py:2024` 以降、third-party の HEAD 観測前**

   既存 interpreter と実 CLI を用いる。

   ```python
   [
       str(Path(sys.executable).resolve(strict=True)), "-I", "-B",
       str(repo_root / "tools/pegasus/fetch_third_party.py"),
       "hydrate",
       "--repo-root", str(repo_root),
       "--cache-root", str(cache_root),
       "--staging-root", str(staging_root),
   ]
   ```

   `_run_command` で host 上から一度だけ実行する。新しい submit 入力・環境変数・probe CLI option は不要。

   timeout は直前の残時間から次のように導出する。

   ```python
   remaining_s = (deadline_ns - time.monotonic_ns()) // 1_000_000_000
   # remaining_s < 30 なら既存と同じ walltime 扱い
   timeout_s = min(
       int(policy["stage_budgets_s"]["ccbench_build_cap_s"]),
       int(remaining_s - 1),
   )
   ```

   本番通常値では最大 1200 秒となり、既知の NFS 85 秒を固定 20 秒で切る問題を避ける。1200 秒は S6 全体の保証ではなく、この subprocess の上限である。

   非 0 rc、`timed_out=True`、起動例外、JSON 解読失敗は `failure_stage="third-party-hydrate"`、`success=False`、outside/inside 成功とも false にして返す。以後の identity・prepare・関門へ進まない。残時間不足は `"walltime"`。CLI payload の読み取りに加え、hydrate 同等の source 再検証は追加しない。

3. **S6 profile と build 引数 — `probe.py:2100` 付近**

   ```python
   readonly_roots=(*profile.readonly_roots, requested_root, staging_root)
   ```

   とする。`run_probe:2545` 以降が作る S1〜S5 用 profile は変更しない。

   `_execute_ccbench_build:1826` の第 3 引数を `cache_root` から `staging_root` に改名し、outside/inside の両呼び出しへ同じ S を渡す。`configure:1859` の 3 行をそれぞれ `S/masstree`、`S/mimalloc`、`S/googletest` に変える。関門には従来どおり、この共有 list の `configure[5:]` を渡す。

4. **prepare — `probe.py:1884` の関門呼び出し直前**

   `failure_stage is None and not inside` のときだけ実行する。位置は既存 6 command の成功後なので、outside の gflags/glog install が完了している。

   `probe.py:36` に `buildcache` import を加え、次の引数で呼ぶ。

   | 引数 | 値・由来 |
   |---|---|
   | `ccbench_dir` | patch 適用済み `str(source)` |
   | `fetchcontent_base_dir` | mkdir 済み canonical `<scratch>/fetchcontent` |
   | `masstree_source_dir` | `S/masstree` |
   | `mimalloc_source_dir` | `S/mimalloc` |
   | `googletest_source_dir` | `S/googletest` |
   | `expected_toolchain_manifest` | `buildcache.observed_toolchain_manifest(compiler_c, compiler_cxx)` |
   | `dependency_prefix` | outside の `str(prefix)` |
   | `site` | 省略。既存 site 判定に委ねる |
   | `configure_timeout_s` / `target_timeout_s` | 下記の残時間分割 |

   compiler は **`:1839`〜`:1841` の既存 `shutil.which` 解決を維持**する。`compilers_for_current_site()` へ切り替えない。受領証 `0:999027.nqsv` は既存選択が `/usr/bin/x86_64-linux-gnu-gcc-11` に解決した事実を記録している。manifest は compiler 選択を要求する API ではなく、渡された compiler と PATH 上の cmake の実体・version 全文を取得する API である。`_toolchain_contract` の受領証には manifest が要求する `requested` 等が揃わないので、その dict を流用しない。

   manifest 取得後に残時間 R を再計算する。`R < 30` は `"walltime"`。例えば次の分割なら、prepare の二つの subprocess timeout の合計を残時間内に収められる。

   ```python
   budget = R - 1
   configure_timeout_s = min(300, budget // 2)
   target_timeout_s = min(
       int(policy["stage_budgets_s"]["ccbench_build_cap_s"]),
       budget - configure_timeout_s,
   )
   ```

   `observed_toolchain_manifest` 内の version subprocess 自体には timeout がない。変更禁止の既存 helper を利用する以上、**これで絶対 deadline 全体を厳密に拘束できるとは主張しない**。

5. **prepare 失敗と inside の制御**

   `MasstreeFetchContentError.stage=="configure"` は `"masstree-prepare-configure"`、`"target"` は `"masstree-prepare-build"` とする。manifest・引数・filesystem 等の例外は `"masstree-prepare"`。既存の小文字・ハイフン区切りに揃える。

   prepare 呼び出しに限定した `except Exception` で診断を保存し、`failure_stage` を立てる。`BaseException` は捕捉しない。prepare の非 0 rc は `buildcache._run:3791` が例外へ変換するため、戻り値に rc があるとは仮定しない。

   **prepare の後に改めて `if failure_stage is None:` を置いて関門を呼ぶ。** 同じ if block 内で catch 後にそのまま関門へ落ちる構造にしない。関門自身の例外は従来どおり伝播させる。

   outside が失敗すれば既存の inside `"outside-control"` 分岐を保つ。S6 全体の既存 `failure_stage` 集約規則は変更せず、prepare の詳細原因は `outside_build.failure_stage` と新記録に残す。

## identity と受領証

**third-party の identity は hydrate 後・prepare 前に S へ向ける。** cache 側 identity を build 入力の identity として記録しない。

- `probe.py:2030` 付近の `source_heads`：third-party 3 本だけ S から読む。gflags/glog は既存 dependency root、CCBench は既存 submodule のまま。
- `probe.py:2070` 付近の `identities`：同じ振り分けにする。期待 pin は既存 policy の値を維持。
- requested 基底 identity は現在と同じく patch 適用前に取る。
- S 側 identity を prepare 後に再採取する検査は追加しない。記録の意味は「hydrate 後、prepare 前の source identity」であり、生成物がない状態が使用時まで続くとの主張にはしない。

masstree pin `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` の **tracked `.gitignore` を `git show <pin>:.gitignore` で確認した**。working-tree の `.gitignore` ではない。

| 生成物 | tracked `.gitignore` の該当行 |
|---|---|
| object | 1 行目 `*.o` |
| archive | 3 行目 `*.a` |
| config header | 8 行目 `/config.h` |

`config.h.in`、`configure`、`config.log`、`config.status`、`GNUmakefile` 等も ignore 対象だった。したがって、これらの生成物だけなら prepare 後も `_git_source_identity` の `clean_including_untracked` は true のままになる。一方、**実 prepare 全体が他の非 ignored file を作らないことは未実走**であり、包括的な保証にはしない。

追加する S6 観測 key は次の二つとする。

- `third_party_staging`
  - `source_root`: S の絶対 path
  - `command`: `_run_command` の記録そのもの。argv、rc、timeout、所要、stdout/stderr、起動失敗を保持
  - `payload`: hydrate の JSON 全体。解読不能時は null と error
- `masstree_prepare`
  - `attempted`、`success`
  - `fetchcontent_base_dir`、`build_dir`
  - `configure_argv`、`build_argv`：成功時は実 helper の戻り値を list 化
  - `configure_timeout_s`、`target_timeout_s`
  - `elapsed_ns`、失敗時の `failure_stage` と error

prepare API は失敗時に argv を返さない。取得できない argv を「実行済み」と捏造せず、失敗時は null とする。成功受領証では両 argv を必ず保存する。

`_execute_ccbench_build` からは private key `_masstree_prepare` で観測を返し、`observe_s6` が pop して S6 の新 key に載せる形にできる。未到達の場合は `attempted=False`。既存 schema・既存 field の意味・関門 record は変更しない。

## 束縛拡張 (.pbs / _BOUND_RELATIVE_PATHS)

`probe.pbs:54` の `BOUND_PATHS` と `probe.py:2356` の `_BOUND_RELATIVE_PATHS` に、同じ二つを追加する。

```text
tools/pegasus/fetch_third_party.py
orchestrator/campaign/buildcache.py
```

既存の dirty 検査、committed blob 比較、runtime SHA 記録をそのまま適用する。

線引きは、**今回 probe が直接利用する実行機構の正本を追加し、推移的 import 全体の閉包は作らない**、である。既存リストも patchharness・condition gate を直接列挙しており、その import 先をすべて束縛してはいない。したがって今回も `site_policy`、`source_digest`、`build_admission` 等、また hydrate が import する `silo_ladder_rung1` を再帰的に追加しない。

これは現行リストから読み取れる粒度の踏襲であり、「全依存コードの bytes を保証する」という意味ではない。

テスト変更は以下。

- `test.py:1541` 付近の `bound_bytes` に二つの独立した fixture bytes を追加。
- `:1630` 付近の `test_execution_binding_shell_dirty_gate` の literal parameter に `hydrate`、`buildcache` を追加。staged/unstaged の両方を拒否させる。
- `test_execution_binding_binds_runtime_spool_to_pbs` の既存 assertions を維持し、新規二つの runtime SHA も照合。
- 新規 `test_execution_binding_bound_paths_match_shell_and_literal`：独立 literal の期待集合を Python tuple と PBS 配列の両方へ照合する。両側から同じ項目を消す変異も検出する。
- 新規 `test_execution_binding_python_rejects_dirty_offline_inputs`：追加二つ × staged/unstaged で `_execution_binding` の dirty 拒否を確認する。

## 配線テスト fixture

### 実 hydrate CLI を成立させる構成

`test.py:1765` の `_s6_live_fixture` を次の順序に組み直す。

1. **cache に実 Git repository を 5 本作る。**

   `masstree`、`mimalloc`、`googletest` に加え、**gflags/glog も必要**。`fetch_third_party.main:728`〜`:729` が 3 本と 2 本を結合し、`_hydrate:629` が全 cache を検証するためである。

   全 repo は通常の非 shallow repository、tracked file を commit 済み、HEAD を fixture pin とする。origin URL は policy と一致する `https://github.com/.../*.git` を設定する。local filesystem URL を policy に書く案は `_build_dependency_sources:84` と `third_party_policy:894` に拒否される。

   clone 元は local cache なので、origin に HTTPS URL があっても実 hydrate はネットワーク取得をしない。gflags/glog の既存 dependency repo を local clone して cache 側へ置く場合は、clone が設定する local origin を policy URL に変更する。

2. **policy を完備する — `test.py:1847`。**

   top-level に次を置く。

   ```text
   gflags_source_url / gflags_expected_head
   glog_source_url / glog_expected_head
   ```

   `silo_ladder_rung1.dependency_pins` はその二つの HEAD と一致させる。`third_party_sources` は順序も含めて `masstree, mimalloc, googletest` の 3 件とし、各件の key は次の exact 集合。

   ```text
   name / source_name / url / pin / fetchcontent_ref
   ```

   `pin=fetchcontent_ref=fixture HEAD` とすれば tag 解決は不要。

3. **CCBench fixture に literal 6 行を置く。**

   `external/ccbench/cmake/ThirdParty.cmake` に 3 source それぞれの

   ```cmake
   set(CCBENCH_MASSTREE_REPO "https://github.com/…/….git")
   set(CCBENCH_MASSTREE_TAG "<fixture HEAD>")
   ```

   と同型の MIMALLOC / GOOGLETEST 行を置く。各 literal は一度だけ出現させる。**CCBench の stock commit と pin を作る前**に配置する。

4. **fixture repo から実 CLI を起動可能にする。**

   fixture の `tools/pegasus/fetch_third_party.py` を実 `_REPO/tools/pegasus/fetch_third_party.py` への symlink として用意する。CLI の `_CODE_ROOT` は `Path(__file__).resolve()` から求められるため、実 repository の Python module を import しつつ、`--repo-root` で fixture policy を読める。

   script だけをコピーする案では import root も fixture になり、`orchestrator.campaign.silo_ladder_rung1` がないため失敗する。symlink は実 CLI の代替ではなく、同じ実 file の起動口である。stub・monkeypatch による CLI 置換や `_hydrate` 直接 import は不要。

### 実 prepare が必要になる CMake fixture

`test.py:1793` 付近の `project(... LANGUAGES C CXX)` は維持する。cc/cxx/cmake は実 executable を利用し、manifest・prepare・関門を stub 化しない。

fixture の CMake へ以下を追加する。

- `include(FetchContent)` と literal 6 行を持つ `ThirdParty.cmake` の include。
- masstree の `FetchContent_Declare` / `FetchContent_Populate`。
- mimalloc/googletest の `FetchContent_Declare` / `FetchContent_MakeAvailable`。各 source repo の最小 `CMakeLists.txt` は空に近い project でよい。
- masstree の tracked `config-template.h` を `config.h` にコピーする `add_custom_command(OUTPUT ...)`。
- その OUTPUT に依存する `masstree_build` target。
- `ycsb_silo.exe` への masstree include directory と `add_dependencies(... masstree_build)`。
- stock の `transaction.cc` に `#include <config.h>` を追加。

これにより、prepare を飛ばすと **build より前の実関門 preprocess** が欠落 header で失敗する。`config.h` は configure 時には生成しない。fixture masstree の tracked `.gitignore` に `/config.h` を入れる。

FetchContent を実際に使えば `FETCHCONTENT_BASE_DIR` も自然に消費される。未知の configure 変数を一律に読んで警告を抑える変更はしない。既存の未使用 3 変数を拒否する能力を残す。

### 既存 wiring test の維持

現物には `test_observe_s6_*` という名前はない。対応する主な 4 関数は次のとおり。

| 既存 test | 変更後も保つ到達点 |
|---|---|
| `test_s6_live_requested_gate_and_both_build_roots_match` (`:1972`) | 実 hydrate・prepare 後、同じ requested 木で関門 2 回と両 build が成功する |
| `test_s6_requested_base_identity_rejects_real_wrong_head_and_dirty` (`:2014`) | hydrate は先行するが、requested identity 拒否で patch・prepare・関門・build は未到達 |
| `test_s6_requested_wrong_head_rejected_without_harness_mask` (`:2033`) | 観測後に HEAD を戻す既存仕掛けを維持し、probe 自身の identity 拒否へ帰属させる |
| `test_s6_live_patch_cleanup_on_short_circuit_and_gate_exception` (`:2048`) | outside parameter は `ccbench-build` 失敗、gate parameter は実関門例外。どちらも patch 撤去を維持 |

**gate parameter の fixture は必須修正。** 現在の `:1810` は無条件 `message(FATAL_ERROR ...)` なので、prepare 導入後は prebuild configure で先に落ちる。`CMAKE_BINARY_DIR` が `/izanagi-masstree-prebuild$` に一致する場合だけこのエラーを出さない形にする。関門 configure では従来の fatal error を出し、既存 `pytest.raises(... "condition gate rejected")` を維持する。

`_observe_s6_wiring:1888` の profile observer に、実 `prepare_masstree_fetchcontent` の call/return 観測を追加する。置換はせず、次を assertions に使う。

- prepare は一度だけ、outside install 後・最初の関門前。
- prepare、関門 2 回、configure 2 回の source override は同じ S。
- S は scratch 外、両 build profile の ro-bind に含まれる。
- prepare 前の S に `config.h` がなく、prepare 後にはある。
- 終了・例外後に S が撤去される。

## (P1)〜(P6) への判定

| 裁定 | 判定 | 根拠・条件 |
|---|---|---|
| P1 | **支持** | job 内実 CLI 一回で足り、既存投入入力を維持できる。fixture でも実 CLI を通せる |
| P2 | **支持** | S を scratch の兄弟に置く必要がある。`SandboxProfile.argv:849` の ro-bind より後に `:851` の scratch rw-bind が来るため、S を scratch 内に置くと保護が覆われる |
| P3 | **条件付き支持** | prepare は outside install 後に一回でよい。ただし「緑の 2 例と argv まで同一」ではない。下記の source/base 分離を親が承認する必要がある |
| P4 | **支持** | 新たな直接実行入力二つを現行の束縛粒度で追加する。推移的 import 全体の保証はしない |
| P5 | **支持** | build が使う S の identity を hydrate 後・prepare 前に記録する。cache identity では build 入力の記録にならない |
| P6 | **条件付き支持** | 98 秒＋追加処理という見積りは合理的だが未実走。残時間で timeout を拘束し、予算内完了の証明は親の実経路一走で得る |

P2/P3 では **source root S と FetchContent binary 用 base B を分けて説明する必要がある**。

- S：hydrate した source と、host prepare が作る masstree 生成物を持つ。inside では read-only。
- prepare の B：`<scratch>/fetchcontent`。prebuild configure と mimalloc/googletest の binary directory はここへ置く。
- 関門・outside・inside：`FETCHCONTENT_BASE_DIR` を渡さなければ、それぞれの CMake binary root の `_deps` に mimalloc/googletest の binary directory ができる。source override は引き続き S を指す。

masstree の custom command は source 内の `config.h` と archive を OUTPUT に持ち、DEPENDS はない。prepare が同じ S に生成した OUTPUT を後続 build が利用する構造であり、**後続が prepare の B を共有する必要は、この実装からは導かれない**。

A-2 は base と source override の双方を渡し、backoff_sweep は source override なしで base を共有する。P3 は両者の argv をそのまま踏襲してはいないが、準備した masstree source を関門へ供給する目的は満たせる見込みである。inside で必要な binary directory を ro の S に向ける `-DFETCHCONTENT_BASE_DIR=S` は採らない。

## 変異事前登録の候補と killer

以下は **KILL の事前予測**であり、実測済みの結果ではない。test node の prefix はすべて `orchestrator/tests/test_t316_sandbox_probe.py::`。

| 候補 | killer と必要な assertion |
|---|---|
| (a) source override を cache 直指しへ戻す | 新規 `test_s6_live_offline_source_paths_and_prepare_order`。prepare・関門・両 configure の 3 path を S と exact 比較。cache に ignored な `config.h` を残した fixture でも検出する |
| (b) prepare を飛ばす | 同新規 test の「関門到達時に実 prepare return を一度観測済み」assertion。加えて既存 `test_s6_live_requested_gate_and_both_build_roots_match` が実 preprocess の header 欠落で失敗する |
| (c) 関門だけ S、build は cache | 同新規 test。関門 event と実 command argv の双方を比較する。関門成功だけでは KILL としない |
| (d) S を scratch 内へ置く | 新規 `test_s6_live_staging_is_readonly_outside_scratch`。`not S.is_relative_to(scratch)` を検査し、inside から S への書込みが拒否されることも実確認 |
| (e) readonly_roots から S を落とす | 同新規 test。両 profile の集合・実 bwrap argv の `--ro-bind S S` を確認。実 sandbox で S の既存 file が読めることも確認し、不可視を read-only 成功と混同しない |
| (f) 束縛一覧から一件落とす | 新規 `test_execution_binding_bound_paths_match_shell_and_literal`。PBS 片側は既存 `test_execution_binding_shell_dirty_gate` の新 parameter も検出。Python 片側は新規 `test_execution_binding_python_rejects_dirty_offline_inputs` |
| (g) hydrate rc を無視する | 新規 `test_s6_hydrate_failure_stops_before_identity_and_gate`。5 本目 glog の origin を実際に不一致にして CLI rc=1 を得る。third-party `_git_head` 等の次段へ入った瞬間に assertion で失敗させ、後段の missing path 例外による mask を防ぐ |
| (h) inside でも prepare する | 新規 `test_s6_live_offline_source_paths_and_prepare_order` の実 prepare call 数 exact 1。inside の prepare は host helper なので、S が sandbox 内 ro でも host からは成功し得る。単なる両 build 成功判定では検出できない |
| (i) BASE_DIR を ro の S に向ける | 同新規 test で関門・両 configure に `FETCHCONTENT_BASE_DIR` がないことを確認。実 FetchContent fixture では inside の binary directory 作成も失敗する見込み |

追加の失敗系として、`test_s6_prepare_failure_stops_before_gate[configure]` と `[target]` を用意する。prebuild configure の実 fatal error／`masstree_build` の実 failing command を fixture に入れ、`success=False`、上記 failure_stage、関門未到達、inside 未到達、S と requested 木の cleanup を確認する。

timeout・起動例外は小さい局所テストで補えるが、正常系と上記非 0 rc の証拠は実 CLI・実 prepare を使う。

## 実装子への指示 (file:line の編集列)

1. **`probe.py:36`**：`buildcache` import を追加。
2. **`probe.py:1985` の隣**：scratch.parent に S を作る contextmanager を追加。既存 requested checkout helper は維持。
3. **`probe.py:2024`**：S context と hydrate command を導入。rc・timeout・例外時の fail-closed return と新観測を実装。
4. **`probe.py:2030`、`:2070`**：third-party HEAD / identity を S に変更。hydrate より前に third-party identity を採らない。
5. **`probe.py:2100`**：S6 readonly roots に S を追加し、両 build へ同じ S を渡す。
6. **`probe.py:1826`、`:1859`**：引数を `staging_root` に改名し、共有 source override 3 本を差し替える。
7. **`probe.py:1884`**：outside だけ prepare。base mkdir、実 manifest、時間分割、失敗記録を追加。prepare 成功を確認してから既存関門 block に入る。
8. **`probe.py:1915`、`:2119` 以降**：prepare 観測を返し、S6 新 key に集約。既存関門 record、trace-disabled、outside-control、verdict は変更しない。
9. **`probe.py:2356` / `probe.pbs:54`**：束縛二件を同期追加。env・submit・CLI は変更しない。
10. **`test.py:1541`、`:1630`、`:1698`**：束縛 fixture・parameter・SHA assertions を拡張し、独立 literal と Python dirty 拒否テストを追加。
11. **`test.py:1765`〜`:1854`**：5 cache repo、policy、literal 6 行、実 CLI symlink、実 FetchContent と `masstree_build` を持つ fixture にする。stock pin 作成前に必要な tracked file を配置。
12. **`test.py:1810`**：gate failure を prebuild configure だけでは発火させない。既存の関門例外期待を維持。
13. **`test.py:1888`〜`:1969`**：実 prepare の観測、S の寿命・path・順序・cleanup を追加。
14. **`test.py:1972` 以降**：既存 assertions を残して上記 killer を追加。`TMPDIR` 未設定・`/tmp` の既存 test も引き続き実経路を通す。

変更禁止の 4 file、docs、policy JSON は編集しない。生の masstree target subprocess を probe に増設しないため、`test_ccbench_spawn_sites.py:805` の direct-cmake-target sink は追加されない見込みだが、親の焦点検査で確認する。

この段では file 編集・テスト実走・commit・PBS 操作を行っていない。緑の報告はない。親は指定の焦点テスト、変異 matrix、計算ノード実経路一走で検証する。

## 総括

P3 は「同じ準備済み source を共有し、FetchContent binary base は後続ごとに分離」として採るか、段 4 で確定する。
束縛は直接利用する二 file の追加までとし、推移的 import 全体の保証を主張しない線引きを確定する。
P6 は実測前の見積りであり、manifest 内の無 timeout 処理も含め、deadline の厳密保証とは区別する。