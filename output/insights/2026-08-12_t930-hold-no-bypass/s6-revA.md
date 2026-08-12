## 所見 1

BLOCKER - call-time wrapper より先に pytest fixture と plain runner helper が実行されるため, 保留 workload は実際には封鎖されていない.

根拠:

- 台帳自身が `repository_scan` fixture の実行コストを保留理由としている. `orchestrator/tests/growth_test_holds.py:140-145`
- fixture は real repository scan を実行する. `orchestrator/tests/test_campaign_import_invariant.py:1073-1075`
- 6 held node がこの fixture を要求する. `orchestrator/tests/test_campaign_import_invariant.py:1078`, `:1218-1235`
- wrapper の拒否は test function が呼ばれた時点でしか発火しない. `orchestrator/tests/growth_test_holds.py:216-234`
- pytest は test function 呼出し前に fixture を解決する. 従って `--noconftest` でも `repository_scan` 完了後に wrapper が拒否する.
- plain runner はさらに明白で, held function を呼ぶ前に `scan_repository(REPOSITORY)` を無条件実行する. `orchestrator/tests/test_campaign_import_invariant.py:1654-1664`, `:1687-1692`

失敗シナリオ:

```text
python3 -m pytest --noconftest -q \
  orchestrator/tests/test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels
```

token 未設定でも real repository scan が先に完走し, その後 wrapper が prefix 付きで失敗する. 同様に次の E 経路も scan を先払いする.

```text
python3 orchestrator/tests/test_campaign_import_invariant.py
```

rc != 0 と拒否 prefix は得られるが, 保留理由である成長比例処理は既に実行済みである.

成果物影響:

`growth_test_hold_inventory()` は該当 6 node を保留済みとして提示する一方, B と E では保留 workload が実行される. 台帳の受理集合と実行事実が食い違い, 成長比例コストの床が runner 依存のまま残る.

提案:

- pytest 経路では function call より前, かつ高コスト fixture より前に拒否する層を追加する.
- `test_campaign_import_invariant.py::_run()` の scan を遅延し, token 無しでは scan に到達させない.
- token 無しの synthetic fixture に side effect counter を置き, fixture 到達が 0 であることを検査する.
- plain runner では `scan_repository` を fail-fast stub に置換した負例を追加する.

## 所見 2

MAJOR - subprocess matrix は fixtureless node だけを攻撃しており, 上の実在する封鎖漏れでも全検査が緑になり得る.

根拠:

- B 検査の対象は引数も fixture も持たない repo scan node である. `orchestrator/tests/test_growth_test_holds_contract.py:549-564`
- E 検査も同じ fixtureless file だけである. `orchestrator/tests/test_growth_test_holds_contract.py:567-575`
- fixture 検査は `opt_in=True` の許可経路しか試さない. `orchestrator/tests/test_growth_test_holds_contract.py:516-546`
- `test_campaign_import_invariant.py` の B/E 経路は検査されていない.
- 差分に追加された `test_` 関数は 14 個ではなく 12 個である. 実在する 12 個を全査した.

1 行破壊に対する監査結果:

| test | 判定 |
|---|---|
| `test_every_held_module_has_exact_top_level_guard_binding` | binding 1 行削除で RED |
| `test_guard_binding_negative_control_detects_removed_call` | repo scan binding 削除で RED. 他 7 file は対象外 |
| `test_all_registered_nodes_are_call_time_wrapped` | binding または wrapper no-op で RED |
| `test_enforcement_rejects_misplacement_and_missing_functions` | 0 件と missing の拒否削除で RED. noncallable 検査削除は GREEN |
| `test_exact_token_is_the_only_release_for_lightweight_body` | token 比較, body 前拒否, `wraps` 破壊で RED |
| `test_opt_in_runs_held_fixture_and_parametrize_shape` | opt-in と metadata 破壊で RED. token 無しの fixture 先行実行は GREEN |
| `test_noconftest_bypass_is_refused_before_held_body` | fixtureless 対象の binding 破壊で RED. fixture 先行実行は GREEN |
| `test_plain_runner_bypass_is_refused_before_held_body` | repo scan file の binding 破壊で RED. campaign runner の helper 先行実行は GREEN |
| `test_imported_conftest_does_not_enable_runpy_bypass` | 対象 binding または拒否削除で RED |
| `test_direct_import_and_call_bypass_is_refused` | 対象 binding または拒否削除で RED |
| `test_regular_pytest_path_keeps_single_hold_skip` | 新 binding 1 行を削除しても GREEN. A の positive control としては正常 |
| `test_plain_pytest_delegating_runner_is_not_over_rejected` | env file の新 binding 1 行を削除しても GREEN. 過剰拒否 positive control としては正常 |

失敗シナリオ:

現実装のまま campaign held node の fixture が実行されても, 選ばれた B/E 検査は別 file のため緑になる. rc と prefix だけでは workload 未到達を証明しない.

成果物影響:

受入結果が封鎖の実効性を過大申告し, BLOCKER の状態を検出できない.

提案:

B と E の双方へ campaign module の負例を追加し, rc/prefix に加えて helper/fixture side effect が 0 であることを直接 pin する.

## 所見 3

MINOR - noncallable 拒否と診断 JSON の一部は mutation されても追加検査が緑のままになる.

根拠:

- noncallable 拒否は `orchestrator/tests/growth_test_holds.py:258-264`.
- 対応 test は 0 件と missing しか検査しない. `orchestrator/tests/test_growth_test_holds_contract.py:477-481`
- `ensure_ascii=True`, `separators`, `sort_keys` は `orchestrator/tests/growth_test_holds.py:227-232`.
- test は JSON を parse して dict 比較するため, これらの出力指定を削除しても緑になる. `orchestrator/tests/test_growth_test_holds_contract.py:467-474`

失敗シナリオ:

noncallable branch を除去すると token 有りで不明瞭な `TypeError` へ変わる. JSON canonicalization 行を除去しても raw 診断形式の退行は検出されない.

成果物影響:

現行 30 node は全て callable かつ payload は ASCII なので, 現時点の封鎖自体は開かない. 影響は opt-in 診断と将来の誤配線検出に限られる.

提案:

synthetic noncallable namespace を追加する. raw JSON bytes を契約にするなら文字列を直接 pin し, 不要なら canonicalization の保証を仕様から外す.

## 所見 4

MINOR - 過剰拒否 positive control は file 全体を再実行し, 厳密には O(1) ではない.

根拠:

- `test_plain_pytest_delegating_runner_is_not_over_rejected` は file を plain Python で起動する. `orchestrator/tests/test_growth_test_holds_contract.py:627-634`
- 起動先は `pytest.main([__file__, "-q"])` で file 内全 node を収集実行する. `orchestrator/tests/test_env_attestation.py:1363-1364`
- `"103 passed, 1 skipped"` の literal は file への test 追加でも赤になる.

失敗シナリオ:

`test_env_attestation.py` の非 held test が増えるたびに subprocess の件数と実行時間が増え, literal 更新も必要になる.

成果物影響:

repo 全体 collection には拡大しないため現時点の影響は限定的だが, 新検査のコストと保守量は対象 file の成長に比例する.

提案:

固定サイズの synthetic delegating runner または既知の軽量 non-held function の直接 call で node 単位性を証明する. 段 4 の exact `103 passed` 要件は O(1) 要件と再裁定する.

## 確認済み

- registry は 30 row, 8 basename.
- 30 node 全てに同名の top-level `def` が厳密に 1 件存在する.
- registry の 8 file と binding の 8 file は一致する.
- 現行 key は全て `basename.py::function` 形で, class method と parameter suffix は無い.
- basename, `::` 分割, 現行 parametrize base name の解決に wrapper 漏れは無い.
- import 失敗, 0 件, missing namespace は成功へ流れず fail-closed になる.
- conftest の `ModuleNotFoundError` fallback は module 側 guard を解除しない.
- `__wrapped__` と `inspect.unwrap` は公開されるが, repo 内に held body を実行する現実的 runner 接続は見つからなかった. 段 4 の受容済み同一 process 任意コードとして BLOCKER にはしていない.
- 静的検査のみで, test は実行していない.

## 総括

NO-GO.

最も危険な 1 件は, pytest fixture と `test_campaign_import_invariant.py::_run()` の real-repo scan が wrapper より前に実行されることである. 拒否 prefix と rc != 0 は出るため封鎖済みに見えるが, 保留対象の成長比例 workload は実際には走る.