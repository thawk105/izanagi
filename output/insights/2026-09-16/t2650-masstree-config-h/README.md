# [T-2650] condition gate へ prebuild 済み masstree を供給する

- wave branch: `worktree-dev-wave-t2650-masstree-config-h`
- 着手時 local main: `262c2993e`
- 実装 commit: `16e7a055e`、段 6 fix commit: `45cedc8cb`、main 取り込み: `f28e668c1`

## 1. 何をしたか

official 床値 campaign が 3 走行とも cell build 段の condition gate で
`BACKOFF_FIXED:supply-effectuation:preprocess-failed` を出して止まっていた。
その原因を一次資料で確定し、供給の配線 1 本を入れ、実 compiler の正例・負例で裏を取った。

出発点は [T-1851] の走行証拠
(`output/insights/2026-09-15/t1851-c3c-official-floor-run/README.md` §4) が残した実値である。

## 2. 根本原因 — `BACKOFF_FIXED` の供給失敗ではない

失敗しているのは Masstree の autoconf 生成 header `config.h` の供給である。

1. `external/ccbench/cmake/ThirdParty.cmake:57-78` — masstree は CMake project でないので
   `add_custom_command` が `bootstrap.sh` / `configure` / `make` / `ar` を回し、
   `config.h` と archive を **masstree の source dir の中へ** 書く。同 85 行の
   `target_include_directories` が同じ dir を include path へ足す。
   つまり `config.h` は **configure 時点では存在せず、build して初めて出来る**。
2. `orchestrator/campaign/condition_meaning_gate.py:1868` — gate は
   `tempfile.TemporaryDirectory(prefix="izanagi_condition_supply_")` に build dir を作り、
   cmake configure だけを行って `compile_commands.json` を読み、同 2210 行〜で
   owner TU を **前処理する**。build は一切しない。
3. `orchestrator/campaign/s8b_floor_campaign.py:3426` — 床値 campaign は
   `buildcache.prepare_masstree_fetchcontent` で masstree の prebuild を**既に持っていた**。
4. `floor_prepare` が `prepare_cell` へ `condition_configure_args` を渡しておらず、
   既定の空 tuple (`s1_direct_comparison.py:836`) が gate まで届いていた。

**同型の欠陥は段 4 loop 経路で既に解決済みだった。** `p3_s4_loop.py:346` の
`_condition_gate_offline_configure_args` と、`test_p3_s4_loop.py:8296` の
`test_prebuild_offline_tokens_reach_real_condition_gate_configure_argv` がその形である。
D1495 が「job script 側で解けたが、condition gate の supply arm は preprocess で
止まったまま」と記録していた残余が、床値経路にだけ残っていた。

## 3. prebuild は sort_best を含む campaign で 1 回走る — 走行時も成立していた

`s8b_floor_campaign.py` の prebuild 発火条件は
`if production_floor_path and any(cell.get("configuration_id") == "sort_best" for cell in cells):`
であり、prebuild は cell ごとではなく **campaign 全体で 1 回**走る。D424 が言う
「sort_best 限定」は `dependency_binding` の **cell build への注入**の射程であって、
prebuild の発火条件ではない。

official 走行の cell 集合を権威 API で実測した。
`enumerate_cells(output/s8b-freeze/holdout_freeze.json, stock_configuration=<floor_protocol.json>)`
= **12 cell**、内訳 `backoff_fixed_best` 2 / `ident_all` 2 / `p2_2_flag_opt` 2 /
`sort_best` 2 / `stock_common` 2 / `system_gate` 2。

段 3 のレンズ A が「現行 worktree の cell 数から過去走行を一般化できない」と反証したので、
走行時 commit と照合した。

- `git diff --stat c185b9fd4 262c2993e -- output/s8b-freeze/holdout_freeze.json output/s8b-freeze/floor_protocol.json`
  は **差分ゼロ**。
- `git show c185b9fd4:orchestrator/campaign/s8b_floor_campaign.py` の該当条件行は現行と同一。

3 走行の traceback は `_build_cells_impl` の `_prepared_binding` 行に到達しているので、
prebuild ブロックは例外なく通過していた。
**ただし prebuild が完走したことの直接の受領証は job 終了で消えており、未照合である。**

## 4. 実装

prebuild の入力から既存生成器で configure 引数を作り、`_FloorOracleDependencyBinding` の
内部搬送 field で持ち回して `floor_prepare` から**全 cell へ**渡す。
`cache_receipt()` / `private_dict()` には入れない。sort 限定の build 注入は変更しない。

**床値経路の offline token は 4 本**である (`FETCHCONTENT_BASE_DIR` と
`FETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}`)。
段 4 loop の先例が pin する「ちょうど 5 本」は明示 `dependency_prefix` を持つ regime の値で、
床値には `prepare_kwargs` へ prefix を入れる経路が無いため転用できない。
実機の gflags/glog は `tools/pegasus/floor_campaign.sh:1148` が
`CMAKE_PREFIX_PATH` を **環境変数で** export しており、gate の subprocess はそれを継承する。

## 5. 生死確認 — 実 compiler・実 CMake の正例と負例

段 3 の両レンズが親 brief の (P1-d)「生死確認は既存実測を継承する」を **refuted** した。
配線が繋がったことを示す argv 一致テストは、`config.h` が実際に読めることを何も証明しない。

`orchestrator/tests/condition_gate_test_support.py` の
`condition_gate_compilers()` / `install_condition_gate_build_fixture()` を使い、
gflags/glog を要さない最小 project で対照を取った
(`test_floor_condition_gate_config_header_supply`、3 source_mode x 2 payload)。

| source_mode | 期待 | 実測 |
|---|---|---|
| `supplied` | green / `requested-default-preprocess-different` | 一致 |
| `omitted` (SOURCE_DIR を落とす) | red / `preprocess-failed` | 一致 |
| `empty` (`config.h` の無い dir) | red / `preprocess-failed` | 一致 |
| `empty` + `config.h` を置き直す (configure 引数不変) | green | 一致 |

**base dir と source dir は別 path に置いた。** 一致させると CMake の既定命名
`<BASE_DIR>/<name>-src` が複製を拾い、`FETCHCONTENT_SOURCE_DIR_*` を 1 本落としても
configure が通るため、**負例が baseline から恒真に緑になる** (D1920 の罠)。

最後の行は段 6 のレビュー所見への是正である。当初の負例は `preprocess-failed` と detail の
`"config.h"` 部分一致しか見ておらず、テスト自身が owner TU へ挿入する `#error wrong config.h`
も同じ条件を満たすため、**原因が `config.h` の不在であることを特定できていなかった**。
同じ `capture_define_inputs` の結果を再利用して configure 引数を 1 bit も変えずに
`config.h` だけを置き直し、green へ戻ることを示した。

## 6. 段 6 で閉じた所見

| ID | 所見 | 出所 | 対応 |
|---|---|---|---|
| F1 | 12 行挿入で `test_ccbench_spawn_sites.py` の行番号 pin がずれ 4 件赤 | 親の焦点走 | closed。4708→4720、8661→8673 |
| F2 | 負例の単一理由性が弱い | レビュー A | closed。§5 の最終行 |
| F3 | commit message の「受理集合は変えない」が裁定と食い違う | レビュー B | closed。amend で訂正 |

不採用: `prepare_kwargs.get("dependency_prefix", "")` を固定値へ明記する案 (レビュー B、低)。
成果物影響が無く、将来 prefix が実在したとき黙って落とす向きの危険と引き換えになる。

F1 は F39 の **4 度目の再発**である。詳細と、今回が足した事実 (検索鍵の不足) は
`docs/failures.md` の F39 へ追記した。

## 7. 変異事前登録と matrix

段 4 で位置を事前登録し、実装後に単一理由性を確認した。期待 node は probe 走で観測して
完全集合を確定し、本走で完全一致を要求した (`DW-M08`)。

- probe: `mutation-spec-probe.json` / `mutation-probe-out.json` — 全件 SURVIVED 登録で
  観測 node を収集。結果は 4 件とも MISMATCH (= 実際には検出された)、**各 1 node だけが赤**。
- 本走: `mutation-spec-final.json` / `mutation-final-out.json` — `repo_head=45cedc8cb`、
  **baseline PASSED・KILLED 4 / 4・SURVIVED 0・MISMATCH 0・TIMEOUT 0・期待 node 完全一致**。

| ID | 変異 | 期待 node | 結果 |
|---|---|---|---|
| M1 | `floor_prepare` が空 tuple を渡す | `test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort` | KILLED |
| M2 | masstree と googletest の source dir を入替え | `test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once` | KILLED |
| M3 | binding へ搬送値を格納しない | `test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once` | KILLED |
| M4 | 搬送を `sort_best` 限定へ退行させる | `test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort` | KILLED |

runner は `python3 tools/run_tests.py orchestrator/tests/test_s8b_floor_campaign.py -k
"config_header_supply or prebuild_uses_pinned_checkout or prebuilds_one_shared_dependency"
-q -rf --force-dispatch`、`--runner-mode dispatch`、`--detached`。

## 8. 検査

親が実走した値だけを書く。

| 検査 | 範囲 | 結果 |
|---|---|---|
| 焦点走 1 | `test_s8b_floor_campaign.py` の新規・変更 3 test | 8 passed / 0 skipped |
| 焦点走 2 | consumer 7 file (`DW-O26` の参照関係で列挙) | 1275 passed / **4 failed** (F1 を検出) |
| 焦点走 3 | `test_ccbench_spawn_sites.py` 単独 (fix 前) | 4 failed |
| 焦点走 4 | `test_ccbench_spawn_sites.py` 単独 (fix 後) | 47 passed |
| 焦点走 5 | 焦点走 1 と同じ範囲 (fix 後、F2 の対照込み) | 8 passed / 0 skipped |
| provenance | `check_ai_provenance.py` full | rc=0 (impl / fix / merge の各 commit 後) |
| 変異 matrix | §7 | baseline PASSED・4/4 KILLED |

**受入全走は本 commit の時点で未実施である。** 実走後にこの表へ amend する。

## 9. 到達範囲と非保証

- **official 床値 campaign が実機で cell build 段を越えたことは、本 wave では確認していない。**
  それは実機再投入を要する別タスクである。本 wave の緑を実機通過と読み替えてはならない。
- prebuild が完走したことの直接の受領証 (`sort-swo-oracle-dependency.json` 等) は未照合。
- 判定規則・reason code の定義・sort 限定の build 注入は変えていない。
  ただし「受理結果まで不変」ではない — 依存欠落による**検査不能**を解消したので、
  従来得られなかった green が新しい走行の台帳に載りうる。
- **非 sort 単独 campaign には同じ `config.h` 欠落が残る。** prebuild も binding も作られない。
  本 wave の scope 外とし、次の一手へ送った。
- 生死確認は最小 project の実 compiler 対照であり、実機 CCBench の `FetchContent_Populate`
  経路そのものを再現したものではない (段 6 レビュー A の射程指摘)。

## 10. 収録物

- `verbatim/s1-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-consult-{sol,luna}.md`、
  `verbatim/s4-ruling.md`、`verbatim/s6-review-{sol,luna}.md`
- `mutation-spec-probe.json`、`mutation-probe-out.json`、
  `mutation-spec-final.json`、`mutation-final-out.json`

段 5 の実装子と段 6 の fix 子は、いずれも上限で SIGTERM を受け**報告を書けずに落ちた**
(`f45_missing_output`)。編集は両方とも完了しており、親が現物を検収して受理した。
子の報告 artifact は存在しないので収録していない。
