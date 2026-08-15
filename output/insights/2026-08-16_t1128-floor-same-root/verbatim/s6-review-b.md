## 所見

1. [severity: must-fix] oracle 前後の同値検査は ABA 型の差替えを検出できない。oracle 後に archive を別内容へ交換し、その archive で binary をリンクした後、postflight 前に元の bytes へ戻せば、実効 root、HEAD、`config.h`、archive の前後値がすべて一致して admission が通る。cache preimage も交換前 receipt のままであり、実際の linker input と binary を結ぶ証拠がない。F60 の swap→restore と F130 `[恒真ゲート]` の観測窓が再発している。[根拠 orchestrator/campaign/s8b_floor_campaign.py:1645] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2445] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2455] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2500] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2521]

   提案: oracle から link 完了まで依存を実効的に書換不能にするか、実際に linker が読んだ archive の identity を binary completion receipt へ束縛する。少なくとも「build 中だけ archive を交換し、終了前に復元する」負例を追加する。

   **成果物影響:** oracle が検証していない archive 由来の binary が admission され、certified 選択とレポートの依存証明が偽になる。

2. [severity: must-fix] base/source 消失の競合で、閉じた detail code と永続化を通らず素の例外が抜ける。base は `resolve()` 後の `stat()` が `ValueError` しか捕捉されず、source は hash 後の `stat()` が無保護である。これらが `FileNotFoundError` になれば、`build_cells` の `_FloorOraclePreflightError` 捕捉へ入らない。また prebuild helper 内の `BuildCacheError` は configure/base 失敗でも広い `except Exception` により checkout failure へ誤分類される。F309 `[恒真ゲート]` `[防壁の射程誤認]` の「新設前段だけ構造化診断を外れる」再発である。[根拠 orchestrator/campaign/s8b_floor_campaign.py:1645] [根拠 orchestrator/campaign/s8b_floor_campaign.py:1649] [根拠 orchestrator/campaign/s8b_floor_campaign.py:1735] [根拠 orchestrator/campaign/s8b_floor_campaign.py:1771] [根拠 orchestrator/campaign/s8b_floor_campaign.py:1794] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2358]

   提案: 各 filesystem probe を段階別 `_FloorOraclePreflightError` へ変換し、prebuild の checkout/configure/target/base を別々に捕捉する。消失競合を注入し、private failure JSON の exact code と oracle・`build_fn` 呼出し回数 0 を検査する。

   **成果物影響:** fail-closed 停止自体はするが、台帳と診断 artifact から失敗理由が消え、次の variant 判断に必要な正しさシグナルが欠落する。

3. [severity: must-fix] M4 を落とすテストがない。`test_production_floor_dependency_preflight_failure_persists_private_attempt` は実際の `_prepare_floor_oracle_dependency` 内で configure/target が失敗する経路を使わず、その helper 全体を例外送出 fake に置換している。このため `MasstreeFetchContentError` を握り潰す変異はテスト対象行を通らず生存する。F127 の委譲辺未固定、F150 の下流呼出し 0 不足、F15 `[テスト代表性]` の型である。[根拠 orchestrator/campaign/s8b_floor_campaign.py:1771] [根拠 orchestrator/campaign/s8b_floor_campaign.py:1781] [根拠 orchestrator/tests/test_s8b_floor_campaign.py:2239] [根拠 orchestrator/tests/test_s8b_floor_campaign.py:2248]

   提案: checkout は成功させたまま本物の `_prepare_floor_oracle_dependency` を通し、`buildcache.prepare_masstree_fetchcontent` だけを configure/target 別に失敗させる。既存 source artifact を残した target-failure fixtureも用意し、握り潰すと oracle へ進む単一理由の負例にする。

   **成果物影響:** prebuild 失敗後に oracle・build が進む退行を検出できず、不完全な依存物による床値 binary が成果物候補へ入る。

4. [severity: must-fix] cache-hit と archive receipt の検出力が固定されていない。campaign の fake build は常に `cached=False` なので、postflight を fresh build 限定にする変異が全テストを通る。また archive receipt の期待値を production の `dependency.cache_receipt()` 自身から導出しており、同メソッドから archive key を削る M8 は期待値も一緒に動く。fake も receipt が非 `None` としか検査しない。F207 `[検出力]` の循環期待値と F60 `[テスト代表性]` が該当する。現実装では postflight は cache hit/fresh 共通かつ admission 前で、F61 `[順序]` 型の逆転は見当たらないが、その性質をテストが固定していない。[根拠 orchestrator/campaign/s8b_floor_campaign.py:2497] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2520] [根拠 orchestrator/tests/test_s8b_floor_campaign.py:327] [根拠 orchestrator/tests/test_s8b_floor_campaign.py:338] [根拠 orchestrator/tests/test_s8b_floor_campaign.py:1888]

   提案: receipt の期待値を独立 literal 3-key dict にし、fake でも exact key/hash を検証する。postflight→永続化→admission 未実行の通しテストを `cached=False/True` の両方で走らせる。

   **成果物影響:** archive identity が cache key から脱落する、または cache hit だけ postflight を迂回する退行が緑となり、別 masstree 由来 binary の受理を許しうる。

## 変異予測

- M1: `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_postflight_gate_rejects_effective_root_and_content_drift` の両 parameter が赤。
- M2: 同 node の `config_sha256` parameter が赤。
- M3: `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_receipt_change_misses_and_empty_default_preserves_identity` が赤。
- M4: なし。実際の `MasstreeFetchContentError` 握り潰し経路を通る test がない。
- M5: `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_base_is_canonical_single_define_and_receipt_in_preimage` が赤。
- M6: `orchestrator/tests/test_s8b_floor_campaign.py::test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort` が赤。
- M7: `test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`、`test_production_floor_preflight_marker_precedes_toolchain_and_dependency_probes`、`test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle` が赤。
- M8: なし。cache identity の実 consumer である `_FloorOracleDependencyBinding.cache_receipt()` から archive key だけを削る変異は、自己導出期待値と寛い fake により生存する。phase marker の記録行だけを削る別変異なら `test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle` と `test_phase_marker_is_create_only_fsynced_private_and_carries_dependency_hash` が赤になるが、cache identity の検出証拠にはならない。

## 判定

**NO-GO** — oracle と実リンク入力の ABA 窓が残り、さらに事前登録 M4・M8 に赤となる test node がない。

## 総括

- fresh build と cache hit は、現実装上は共通の postflight を通る。
- postflight は binary admission より前に配置され、通常の早期 return による迂回は見当たらない。
- receipt は v2 preimage に入り、空の既定 callerでは旧 identityを保つ。
- archive hash の計算時点も prebuild 後・cell build 前である。
- ただし前後 snapshot だけなので、build 中の差替えと復元を検出できない。
- base/source の消失競合には、永続化前に素の例外が抜ける経路がある。
- positive/negative control は root・config・archive driftにはあるが、cache hit と実 prebuild failureにはない。
- M4 と cache-receipt 位置の M8 は静的予測で生存する。
- pytest は実行しておらず、上記は指定どおり差分と周辺コードによる静的判定である。