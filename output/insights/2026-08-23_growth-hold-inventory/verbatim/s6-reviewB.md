## 所見

### 1. [real] must-fix: 台帳の独立 golden が旧 59 件のまま

`test_hold_inventory.py` は削除された 14 node と旧 reason を保持しています。[test_hold_inventory.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:51) と [test_hold_inventory.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:75) が旧 16 件を列挙し、[test_hold_inventory.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:359) で現 registry との完全一致を要求します。

この helper は次の2テストから到達します。

- [test_inventory_projects_exact_registered_source_sets:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:534)
- [test_main_dispatches_human_and_json:718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:718)

最初の集合 assertion は stale extra 14 件で失敗します。集合を直しても、残存2件の reason は [test_hold_inventory.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:68) の旧共有 reason と一致せず、exact inventory / human 出力比較が赤になります。

影響: 台帳本体は count `45` と新 digest を正しく出す一方、受入全走は少なくとも上記2 node が静的に赤となり、certified レポートを緑として確定できません。

### 2. [real] corpus 不在時は「再導入14件すべて実行」にはならない

[benchmark_snapshots:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:508) は `_HISTORICAL_SESSIONS.is_dir()` が偽なら fixture setup で skip します。

再導入14 functionの内訳は次のとおりです。

- 12 function、14 items が skip:
  `cleaned_snapshot`、`stale_commit_graph`、M1、M3 4 function、`pos_neg_submodule`、`agent_sandbox`、`verify_replays`、`attempt_four`、`f3_4`。
  M3 focus は [parametrize 3件:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:2040) なので、12 functionから14 itemsになります。
- 2 function、4 items が赤:
  - M2の1 itemは [derive_independent_golden:1988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1988) から空 corpus を検索し、[codex_reasoning_ab.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:488) の `ValidationError` になります。
  - prompt replacementの3 itemsは [parametrize:6099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6099) から固定 file を読み、[codex_reasoning_ab.py:497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:497) で `FileNotFoundError` になります。

現在の作業ホストでは corpus directory、固定 `_REAL_ROLLOUT`、historical controls の実在を確認しました。したがって現在の受入環境ではこの skip 分岐は発火しませんが、host 非依存の実行保証ではありません。

影響: corpus 不在環境では runnable 集合が14 items不足し、さらに4 itemsが赤になります。fixture依存の変異期待 node は実行されず、その nodeだけが殺す変異は SURVIVED になり得ます。

### 3. [refuted] hold 以外の collection quarantine は再導入14件を除外しない

collection hookで skipを付ける経路は、[conftest.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:883) の `GROWTH_TEST_HOLDS` lookupと [conftest.py:891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:891) の marker追加だけです。

- `REAL_REPO_SERIAL_NODES` に12 fixture consumerが残っていますが、[conftest.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:877) から [conftest.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:881) は `xdist_group("real-repo")` を付けるだけで、skip / deselectではありません。
- `flaky_test_holds` または別の pytest hold registry は `orchestrator/` と `tools/` にありません。
- `SANCTIONED_EXCLUSIONS` は [test_selection_contract.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/test_selection_contract.py:39) の `test_sort_swo_oracle.py` 1 fileだけです。[test_selection_contract.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/test_selection_contract.py:48)
- `pytest.ini` は [pytest.ini:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/pytest.ini:13) の `testpaths` と [pytest.ini:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/pytest.ini:14) の一般的な `norecursedirs` のみです。`collect_ignore`、`addopts`、marker filterはありません。
- repository内の `conftest.py` は suite の1 fileだけで、対象 test module自身にも fixtureの [pytest.skip:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:509) 以外の該当 skip markerはありません。

影響: 現在の corpus-present 環境では、削除した14 keyに別の skip / deselectが重ならず、18 itemsが既定 runnable 集合へ入ります。

## 受入集合の増分

変更されるのは collection総数ではなく、skip markerを持たない runnable 集合です。

- function-level node key: `+14`
- parametrize展開後 item: `+18`
  - M3 focus: 3 items
  - prompt replacement: 3 items
  - 残り12 function: 各1 item

したがって親の `11 node / 15 items` ではなく、確定値は `14 function nodes / 18 items` です。

`test_prompt_replacement_count_zero_expected_and_excess[0,9,10]` の実際の合否と所要時間は実走が要ります。固定 rollout fileの実在だけ確認し、pytestは実行していません。

## consumer 全列挙

### `GROWTH_TEST_HOLDS`

- collection / report: [conftest.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:883)、[conftest.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:909)、[conftest.py:1005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:1005)、[conftest.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:1115)。特定 node key集合への動的依存で、件数・digest pinはありません。
- guard実装: [growth_test_holds.py:654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:654)。file名ごとの特定 node集合に依存します。codex moduleには2件残るため、[growth_test_holds.py:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:657) の zero-holdエラーは発火しません。
- contract test: [test_growth_test_holds_contract.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:266) が件数、key digest、row digestをpinします。
- exact台帳 test: [test_hold_inventory.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:359) が特定 nodeとreasonをpinします。ここがstaleです。
- real-repo契約: [test_real_repo_serialization.py:1215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_real_repo_serialization.py:1215) と [test_real_repo_serialization.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_real_repo_serialization.py:1243) は別 fileの特定 payer / memo nodeに依存し、今回の14件を含みません。
- collection unit test: [test_pytest_collection_config.py:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_pytest_collection_config.py:549) はsynthetic registryを注入するだけで、現件数に依存しません。

### `growth_test_hold_inventory` / `growth_test_hold_key_digest`

- [growth_test_holds.py:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:706) が count、digest、全rowを動的生成します。
- [tools/hold_inventory.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/hold_inventory.py:81) はその結果を読み、[tools/hold_inventory.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/hold_inventory.py:89) で count / digest / holdsをそのまま投影します。hard-code pinはありません。
- contract testのpin値は独立再計算と一致しました: count `45`、key SHA `5a5f7a4f...3429`、row SHA `8cf20b5f...d945`。
- `test_hold_inventory.py` のcount / digest自体は [test_hold_inventory.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:421) で動的計算しますが、node / reasonの完全集合がstaleです。

### `enforce_held_functions`

production test moduleでのconsumerは次の13箇所です。いずれも件数・digestではなく、自 fileに属する特定 node集合へ依存します。

`test_campaign_import_invariant.py:1708`、`test_check_docs.py:10923`、`test_codex_reasoning_ab.py:9157`、`test_env_attestation.py:1360`、`test_real_repo_serialization.py:3947`、`test_ruleops.py:3456`、`test_s1_known_axes_freeze.py:678`、`test_s1_measurement_freeze.py:322`、`test_s8b_binding_driftguards.py:590`、`test_s8b_holdout_freeze.py:2363`、`test_s8b_oracle_driver.py:5824`、`test_s8b_protocol_builder.py:1865`、`test_s8b_repo_scan_invariant.py:55`。

今回変化するのは `test_codex_reasoning_ab.py` のguard対象が16から2になる点だけで、他12 moduleのsubsetは不変です。

影響: 正式台帳は45件へ追従します。壊れるconsumerは動的出力ではなく、旧 node / reasonを独立pinした `test_hold_inventory.py` です。

## contract testの残余 assertion

### [refuted] L43-45以外に今回の削除で赤になる前提はない

- `startswith`: [test_growth_test_holds_contract.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:281) は別module prefixの禁止です。
- `in GROWTH_TEST_HOLDS`: [test_growth_test_holds_contract.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:289) は別 fileの既存 holdです。
- `isdisjoint`: [test_growth_test_holds_contract.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:290) の3 nodeは変更前から未holdで、今回も未holdです。
- contract module自身のprefix禁止は [test_growth_test_holds_contract.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:393)。
- inventory assertionは [test_growth_test_holds_contract.py:405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:405) で更新済み定数を再利用します。

影響: 3 pinの更新以外に、このcontract file自身から旧14件を要求する赤は残りません。

## 変異正本

### [refuted] 変更後にまだ hold されている期待 nodeはゼロ

正本は [test_codex_reasoning_ab.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4) から [test_codex_reasoning_ab.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:19) です。変更後のcodex registry keyは次の無関係な2件だけです。

- [growth_test_holds.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:110) `test_forbidden_commits_are_unreachable_in_both_cases`
- [growth_test_holds.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:125) `test_parent_numstat_controls_remain_pinned`

M1、M2、M3の4件、M5の2件はいずれもhold解除済みです。M4、M6、M7、M8、M9、M10、M11、M12にもhold、skip marker、SANCTIONED exclusionはありません。代表定義は [M4:7494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:7494)、[M6:8933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:8933)、[M12:8370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:8370) です。

ただし所見2のとおり、corpus不在時はM1、M3 4 function、M5 replayがfixture skipします。

影響: 現在の corpus-present hostでは、holdまたは別selection機構によって変異が必ず SURVIVED になる期待 nodeは残りません。

## テスト強度とreason

### [refuted] assertion緩和・skip追加はない

全差分は3 fileだけです。

- `growth_test_holds.py`: 14 row削除、2 reason更新、未参照定数削除。
- `test_codex_reasoning_ab.py`: [6105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6105) のsource解決だけを固定 path + SHA検査へ変更。期待値分岐とassertionは [6121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6121) 以降で不変です。
- `test_growth_test_holds_contract.py`: 3 pin定数だけ変更。

`_validate_hold_rows` は [growth_test_holds.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:542) 以降に差分がなく、reasonの非空string検査も [growth_test_holds.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:551) のままです。

影響: 検出 assertionは反転・緩和されず、固定 rolloutのSHA検査が追加されています。

### [refuted] 長いreasonはvalidator / JSON出力を壊さない

2 reasonはいずれも非空 `str` です。inventoryは [growth_test_holds.py:717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:717) で `asdict` し、値はstring、bool、`None`だけです。[growth_test_holds.py:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:724) と `tools/hold_inventory.py` のJSON serializerが引用符をescapeします。

軽量import probeで、内側inventoryと外側2層inventoryの双方を `json.dumps` でき、2 sentinel substringも `json.loads` で復元できることを確認しました。pytestは実行していません。

影響: 台帳の count、digest、holds rowは有効なJSONのままで、reason内の引用符による破損はありません。

## 総括

must-fixは1件です。

1. `orchestrator/tests/test_hold_inventory.py` の旧16件 exact goldenを、残存2件の新reasonを含む45件契約へ更新する。放置すると少なくとも2テスト nodeが静的に赤となり、受入全走をcertifiedにできません。

corpus不在時の14 skip / 4 redは実在する条件分岐ですが、現在の作業ホストでは必要なcorpusと固定fileが存在します。その他の隠れたskip、残留mutation hold、assertion緩和、JSON破損は確認されませんでした。