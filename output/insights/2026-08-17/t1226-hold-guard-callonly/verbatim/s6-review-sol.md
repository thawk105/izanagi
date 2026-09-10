## 所見

1. **主張:** `__wrapped__` 保持と「exact token だけが解除口」は両立しておらず、call-only の held 本体へ無条件到達できる。  
   **根拠:** `orchestrator/tests/growth_test_holds.py:602-609`, `orchestrator/tests/growth_test_holds.py:673-681`, `orchestrator/tests/test_growth_test_holds_contract.py:1390-1406`。  
   **具体的な失敗シナリオ:** plain import 後に `inspect.unwrap(module.test_x)()`、`test_x.__wrapped__()`、または `inspect.getclosurevars(test_x).nonlocals["function"]()` を呼ぶと、環境 token なしで原関数が実行される。純 Python probe で `BODY_RAN` を確認した。canonical 名と guard 後の alias は拒否されるが、この経路は拒否されない。  
   **重大度:** blocker

2. **主張:** pre-guard alias 禁止は単純な代入しか扱わず、複数の原関数退避経路を受理する。  
   **根拠:** `orchestrator/tests/test_growth_test_holds_contract.py:933-973`, `orchestrator/tests/test_growth_test_holds_contract.py:1251-1263`。  
   **具体的な失敗シナリオ:** `def escape(fn=test_held)`, `setattr(Escape, "held", test_held)`, `holders.append(functools.partial(test_held))` は binding error にならず、いずれも本体へ到達した。fixture も `@pytest.fixture; def escaped(fn=test_held): return fn` が受理され、fixture wrapper の `__wrapped__` から原関数を取得できた。直接代入、class body の直接代入、直接代入された `partial` は検出され、guard 後の alias は wrapper を指すため拒否される。  
   **重大度:** blocker

3. **主張:** M3 の pytest 判定除去は新テストを落とさず、裁定された費用層を検査していない。  
   **根拠:** `orchestrator/tests/growth_test_holds.py:673-675`, `orchestrator/tests/test_growth_test_holds_contract.py:1568-1587`。  
   **具体的な失敗シナリオ:** `_pytest_drives_current_import()` の拒否を削除しても、pytest は module を収集後に wrapped test を呼び、同じ拒否 marker、非ゼロ rc、`BODY_RAN` 不在を生成する。全 assert がそのまま成立するため、fixture setup が先払いされる退行を黙って通す。  
   **重大度:** blocker

4. **主張:** self-load 判定は最終 loader identity ではなく、shadow された API 名や到達不能コードでも call-only 適格と誤認する。  
   **根拠:** `orchestrator/tests/test_growth_test_holds_contract.py:591-605`, `orchestrator/tests/test_growth_test_holds_contract.py:816-872`。  
   **具体的な失敗シナリオ:** local `class runpy` の `run_path` を `if False:` 内で `runpy.run_path(__file__)` と書くだけで `_guard_binding_errors == ()`、`self_load is True` になった。実際の自己読込がない file でも import 拒否を解除できる。  
   **重大度:** must-fix

5. **主張:** stack の module 名だけによる pytest 判定には具体的な誤検出・誤不検出境界がある。  
   **根拠:** `orchestrator/tests/growth_test_holds.py:612-626`。  
   **具体的な失敗シナリオ:** plain Python でも `__name__="_pytest.fake"` の frame から loader を呼べば誤拒否する。一方、pytest test/plugin が別 thread から import すると、その thread の stack に `_pytest.*` frame がなく、enforcement config もない `--confcutdir` sessionでは import を許す。後者は fixture setup 後の call-time 拒否へ退行し得る。  
   **重大度:** must-fix

6. **主張:** 裁定 1 の runner 境界がテストで完結していない。  
   **根拠:** `orchestrator/tests/test_growth_test_holds_contract.py:1548-1587`。  
   **具体的な失敗シナリオ:** plain `spec_from_file_location` の正例と `--noconftest` だけがあり、plain package import と `--confcutdir` の node がない。現実装では純 Python の spec/package import は成功し canonical call は拒否されたが、package 側または confcutdir 側だけを壊す変異は受入を通る。  
   **重大度:** must-fix

## 変異の帰属

| 変異 | 落とす nodeid / 結論 |
|---|---|
| M1 | `test_enforcement_signature_pins_independent_guard_mode_default` と `test_import_guard_rejects_nonempty_nonexact_release_token[explicit-typo]`、`[explicit-user-command-extra]`。既存 test だけという事前帰属ではなく、新 signature pin も落ちる。 |
| M2 | `test_call_only_mode_allows_import_but_refuses_held_call`。wrap 前 return では `BODY_RAN` が出て rc=0 になる。default mode なら import 前拒否となり `IMPORT_OK` が消えるため、この正例は mode 分岐を区別している。 |
| M3 | **落とせない。** `test_call_only_mode_still_rejects_noconftest_pytest_import` は collection-time 拒否と call-time wrapper 拒否を区別しない。 |
| M4 | `test_call_only_mode_still_rejects_non_delegating_main`。拒否除去後は module が何も実行せず rc=0 になる。 |
| M5 | `test_self_load_detection_handles_real_nested_consumers`。`test_s8b_floor_campaign.py` の nested f-string 内 spec loader で落ちる。 |
| M6 | exact anchor がなく完全集合を一意化できない。少なくとも `test_self_load_detection_compares_full_path_not_only_basename`、`test_guard_binding_requires_call_only_exactly_for_canonical_self_load` の runner 3 node、foreign controls が候補。現状の事前登録は完全集合要件を満たさない。 |
| M7 | `test_guard_binding_requires_call_only_exactly_for_canonical_self_load[none]`、`[manual]`、`[pytest-delegating]`。未知 kwarg、重複、逆順のいずれかで落ちる。 |
| M8 | `test_call_only_binding_rejects_pre_guard_alias_with_post_guard_control`。ただし単純代入だけを KILL し、所見 2 の alias 変異は生存する。 |
| M9 | `test_guard_mode_rejects_unknown_literal[unknown]`、`[True]`、`[None]`。 |
| M10 | `test_self_load_detection_handles_real_nested_consumers`。`test_dev_waves_integration.py` の nested package import で落ちる。M5 と同じ nodeid で、失敗 subcase は nodeid だけでは識別できない。 |

## 総括

blocker は exact-token 不変条件の自己矛盾、alias 漏れ、M3 生存の 3 件。  
registry は count 59、指定 SHA、held file 13、現行 13 binding の無指定受理を静的確認した。  
`@wraps` と `__wrapped__` は保持されているが、それ自体が call-only の解除口になる。  
差分は既存 assert の反転・緩和・skip・削除を含まず、置換された binding assert は強化されている。  
pytest は実走せず、ファイル編集・commit も行っていない。