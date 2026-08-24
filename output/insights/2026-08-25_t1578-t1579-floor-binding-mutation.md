# [T-1578][T-1579] floor 依存束縛の変異 matrix — 事前登録と実測

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は測定記録であり裁定台帳ではない。

- 測った checkout: branch `worktree-dev-wave-t1578-t1579-t1431-floor-restart`。
- 変異を注入した commit: `22fa18902608950deb237469d72601974008c8fa`。
- spec: `mutation-final.json` (sha256 `0c77e41396ced728b692c5f511a99f3a6803f08b4e866ca44ef39fdc56d19bda`)。
- harness: `tools/mutation_worktree.py`、`--runner-mode dispatch`、使い捨て worktree。
- runner: `python3 tools/run_tests.py orchestrator/tests/test_s8b_floor_campaign.py
  orchestrator/tests/test_buildcache_v2.py orchestrator/tests/test_pegasus_floor_tools.py
  -q -rf --force-dispatch`。
- 実行環境: Pegasus 計算ノード。

---

## 1. 何を確かめたかったか

この wave は archive bytes の静的 pin をやめ、run-local な観測値 + source identity +
toolchain manifest へ束縛を張り替えた。**束縛を弱めずに照準だけ変えた**と主張するには、
新しい各 gate が実際に発火することと、承認した受理形を過剰に拒否しないことの両方が要る。
所見ゼロや受入緑は、その証拠にならない。

登録は 10 本の負例と 1 本の正例統制である。正例統制は「受理集合を縮小する wave では
承認外の過剰拒否を検出する正例も登録する」(`DW-M01`) に対応する。

## 2. 手順 — probe を先に走らせた

期待 node の完全集合を机上で書けなかったため、まず全件 `SURVIVED` 期待の probe を走らせて
観測 node を集め、それを期待集合として登録し直してから本走した。

probe (spec sha `f702786f...`, commit `d7ecb118...`): baseline `PASSED`、11 件すべてが
失敗 node を出した (全件 `MISMATCH` = 期待した `SURVIVED` にならなかった = 検出できている)。

本走 (fix 4 巡目まで反映した `22fa1890...`): baseline `PASSED`、
`KILLED 11 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / matching 11`。
期待 node は完全一致した。fix で実装を動かした後も 11 本の anchor は全て逐語一意のままだった。

## 3. 結果

| ID | 変異 | 殺した node |
|---|---|---|
| m01 | payload policy loader の exact key 検査を superset 許容へ緩める | `test_floor_masstree_payload_policy_loader_rejects_unknown_key` |
| m02 | 独立 expected config hash の比較を落とす | `test_floor_postflight_staged_source_set_and_expected_hash_are_enforced` |
| m03 | prebuild 前の ignored source 検査を落とす | `test_floor_pristine_staged_preflight_verifies_three_pins_and_clean_status` |
| m04 | postflight の tracked source drift 検査を落とす | `test_build_cells_production_postflight_rejects_dependency_drift[tracked-...]` |
| m05 | buildcache dependency receipt の exact key 検査を落とす | `test_v2_fetchcontent_dependency_receipt_requires_exact_head_config_schema` |
| m06 | BuildResult toolchain manifest の object 一致比較を落とす | 同 mismatch test の fresh / cache-hit 2 件 |
| m07 | canonical / result / binding の toolchain hash 一致を落とす | 同 mismatch test の fresh / cache-hit 2 件 |
| m08 | build 例外を failure record へ載せない | `test_sort_best_build_failure_persists_bounded_exception_diagnostic` 2 件 |
| m09 | `message_truncated` を常に false にする | 同 test の `[long-surrogate]` |
| m10 | generator の一時 clone で `make` を先に走らせる | `test_floor_masstree_policy_generator_is_independent_and_has_both_cli_inputs` |
| pos | run-local archive 観測値を静的期待値と比較して拒否する | `..._allow_distinct_build_bytes_across_runs` ほか 2 件 |

## 4. 何が言えて、何が言えないか

言えること。10 本の負例 gate はいずれも単一理由で発火し、消せば必ず対応する test が赤くなる。
正例統制は、承認した受理形 (別 run では archive bytes が異なってよい) を静的期待値で
締め直すと、それを許す test が即座に赤くなることを示した。**束縛の照準替えは、
締め方を弱めた結果ではない。**

言えないこと。変異は登録した 11 本の位置についてだけ検出力を主張する。
`DW-M08` の「テスト強化だけの wave は新旧両走を登録する」には該当しないため、
新テストだけが検出する差分は測っていない。実 build を伴う経路 (実際の masstree build、
cache hit の実体) は unit 境界の外にあり、この matrix は触れていない。
