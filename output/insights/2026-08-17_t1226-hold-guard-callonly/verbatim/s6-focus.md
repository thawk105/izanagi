## 対応表

| 所見 ID | 判定 | 根拠 file:line |
|---|---|---|
| A-1 | closed — `by-ruling-recorded` | `growth_test_holds.py:602-609` は `@wraps` を維持し、`s6-fix2.md:21` が `__wrapped__`・closure 経由を記録処理と明記。 |
| A-2 | **partial** | 通常の `Name` load は `test_growth_test_holds_contract.py:1060-1078,1359-1379` で拒否された。しかし `globals()["test_held"]` は検出されず、guard 前に原関数を保存できる。 |
| A-3 | closed | module・fixture marker は `test_growth_test_holds_contract.py:1735-1763`、拒否検査は同 `:1811-1857`。pytest 判定を外すと guard 後 marker が出るため M3 を検出する。 |
| A-4 | closed | module import alias、shadow、定数到達不能判定は `test_growth_test_holds_contract.py:530-620,866-885`。元の偽陽性二例は同 `:1442-1457` で固定。新しい局所 import の偽陰性は後述。 |
| A-5 | closed — `by-ruling-recorded` | stack 判定は `growth_test_holds.py:612-628` のまま。別 thread import と `_pytest` 名偽装は `s6-fix2.md:21` に記録済み。 |
| A-6 | closed | package import 正例は `test_growth_test_holds_contract.py:1788-1808`、`--confcutdir` 拒否は同 `:1835-1857`。 |
| B-1 | closed | 注釈付き spec と loader alias の逆引きは `test_growth_test_holds_contract.py:910-943,1419-1439`。解決不能な `exec_module` は同 `:1512-1521` で fail-closed。 |
| B-2 | closed | `inspect.currentframe() is None` は拒否側へ倒れる (`growth_test_holds.py:612-616`)、専用検査は `test_growth_test_holds_contract.py:1631-1635`。 |
| B-3 | closed | 固定 synthetic は `test_growth_test_holds_contract.py:1386-1416`。floor の spec/load/exec 形は `test_s8b_floor_campaign.py:7896-7900`、integration の package import/Popen 形は `test_dev_waves_integration.py:2050-2057` と一致し、全量 parse はない。 |

## 新規所見

1. **主張:** F1 は動的 namespace lookup による原関数退避を閉じていない。  
   **根拠:** 検査対象は `ast.Name` の `Load` だけ (`test_growth_test_holds_contract.py:1070-1076`)。一方、wrapper は canonical global だけを置換する (`growth_test_holds.py:665-669`)。静的 probe では `saved = globals()["test_real_repository_scan_matches_known_hits_and_has_positive_control"]` が `errors=(), self_load=True` で受理され、token なしの `saved()` が本体へ到達した。  
   **失敗シナリオ:** call-only file が guard 前に文字列 lookup で原関数を保存し、guard 後にそれを呼ぶ。  
   **重大度:** blocker。

2. **主張:** F1 の全面 `Load` 禁止は、現行 13 file の将来 call-only 化を実際に過剰拒否する。  
   **根拠:** `test_s8b_repo_scan_invariant.py:38-40` の `_run()` は held 名を参照し、guard は同 `:54-55`。この参照は `__main__` から guard 後にだけ実行される (`:58-59`) が、行番号だけを見る `test_growth_test_holds_contract.py:1070-1076` は拒否する。現行 13 file の静的列挙では、この file だけが該当した。  
   **失敗シナリオ:** 同 file に正当な self-load を追加して `guard_mode="call-only"` にすると、manual runner の安全な wrapper 呼出まで binding error になる。  
   **重大度:** must-fix。

3. **主張:** F2 は関数内の正規 `import runpy` を自己読込として認識せず、判定不能エラーにも倒さない。  
   **根拠:** module 直下以外の import 名は無条件に不明扱いになる (`test_growth_test_holds_contract.py:593-607`)。その結果 `_qualified_name` は `None` を返し (`:657-674`)、`runpy.run_path` 分岐 (`:974-975`) に入らない。probe `def consumer(): import runpy; runpy.run_path(__file__)` は `(False, ())` だった。  
   **失敗シナリオ:** 実 consumer が局所 import を使うと self-load を黙って見逃し、call-only 宣言を過剰拒否する。  
   **重大度:** must-fix。

4. **主張:** 現行 mutation builder は段 4 の M1〜M10 を表現していない。  
   **根拠:** `s4-adjudication.md:81-92` は 10 変異だが、`build_spec.py:10-42` は 9 件だけで、M5 以降の意味が入れ替わり M10 がない。  
   **失敗シナリオ:** 現行 builder で本走すると、段 4 の nested parse・package import などを未変異のまま「matrix 完了」と誤認する。  
   **重大度:** blocker。

## 変異の生存判定

以下は段 4 定義そのものに対する静的 kill 判定。今回は pytest・mutation harness を実走していない。

| 変異 | 落とす nodeid / 生存判定 |
|---|---|
| M1 | `test_growth_test_holds_contract.py::test_enforcement_signature_pins_independent_guard_mode_default`。加えて `test_import_guard_rejects_nonempty_nonexact_release_token[explicit-typo]` と `[explicit-user-command-extra]`。KILLED。 |
| M2 | `test_call_only_mode_allows_import_but_refuses_held_call`、`test_call_only_mode_allows_package_import_but_refuses_held_call`。wrap 前 return なら原 body が動く。KILLED。 |
| M3 | `test_call_only_mode_still_rejects_noconftest_pytest_import` と `test_call_only_mode_still_rejects_confcutdir_pytest_import`。判定除去後は `MODULE_AFTER_GUARD_RAN` が出る。**KILLED。** |
| M4 | `test_call_only_mode_still_rejects_non_delegating_main`。KILLED。 |
| M5 | `test_self_load_detection_handles_real_nested_consumers` の floor synthetic。二段 parse を外すと self-load が消える。KILLED。 |
| M6 | `test_self_load_detection_compares_full_path_not_only_basename`。foreign path を self と誤認して落ちる。KILLED。 |
| M7 | `test_guard_binding_requires_call_only_exactly_for_canonical_self_load[none]`、`[manual]`、`[pytest-delegating]`。逆順 keyword が受理されて落ちる。KILLED。 |
| M8 | `test_call_only_binding_rejects_pre_guard_alias_with_post_guard_control`。登録された検査除去変異は KILLED。ただし `globals()[name]` という同根の未登録変異は生存。 |
| M9 | `test_guard_mode_rejects_unknown_literal[unknown]`、`[True]`、`[None]`。KILLED。 |
| M10 | `test_self_load_detection_handles_real_nested_consumers` の integration synthetic。package self-import 検出除去で落ちる。KILLED。 |

## 総括

- 判定は **NO-GO**。A-2 は partial で、token 不要の動的 alias 経路が残る。
- F1 は現行 `test_s8b_repo_scan_invariant.py` の安全な manual runner 参照を将来過剰拒否する。
- F2 には局所 `runpy` import の無診断偽陰性がある。
- M3 は二つの pytest node が確実に落とす形へ閉じた。
- 段 4 の exact M1〜M10 は静的には kill 可能だが、現行 mutation builder の drift を直さない限り本走証拠にはならない。