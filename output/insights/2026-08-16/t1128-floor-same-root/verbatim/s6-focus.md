## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| A-1 | **regressed** | 正当な別 base の cache hit は通るが、`cached=True` なら completion に記録された実効 root を無条件に無視する。このため fresh postflight で拒否済みの wrong-root entry も次回 hit で通る。[根拠 `orchestrator/campaign/s8b_floor_campaign.py:2092`] [根拠 `orchestrator/campaign/s8b_floor_campaign.py:2096`] |
| A-2 | **partial** | expected base の内容 drift は publish 前に検査する一方、検査対象は実効 root ではなく `canonical_fetchcontent_base`。wrong-root binary は completion へ publish される。[根拠 `orchestrator/campaign/buildcache.py:1719`] [根拠 `orchestrator/campaign/buildcache.py:1723`] [根拠 `orchestrator/campaign/buildcache.py:1786`] |
| A-3 | **closed** | field が存在する非 `sort_best` record は store/project の双方で拒否し、base 無し `sort_best` は受理する片方向規則になった。[根拠 `orchestrator/campaign/s8b_floor_campaign.py:2762`] [根拠 `orchestrator/campaign/s8b_floor_campaign.py:3456`] |
| B-2 | **closed** | base/source の対象 `stat` は seam 経由でも実際に実行され、`OSError` は閉じた detail code へ変換される。通常時の seam は単なる `path.stat()` である。[根拠 `orchestrator/campaign/s8b_floor_campaign.py:1501`] [根拠 `orchestrator/campaign/s8b_floor_campaign.py:1656`] [根拠 `orchestrator/campaign/s8b_floor_campaign.py:1751`] |
| B-3 | **closed** | 本物の `_prepare_floor_oracle_dependency` を通し、configure/target だけを失敗させる。oracle/build 未到達も固定されている。[根拠 `orchestrator/tests/test_s8b_floor_campaign.py:2312`] [根拠 `orchestrator/tests/test_s8b_floor_campaign.py:2321`] [根拠 `orchestrator/tests/test_s8b_floor_campaign.py:2393`] |
| B-4 | **closed** | archive receipt は独立した 3-key literal に固定され、fake は完全一致を要求する。fresh/cache-hit の両経路も存在する。[根拠 `orchestrator/tests/test_s8b_floor_campaign.py:298`] [根拠 `orchestrator/tests/test_s8b_floor_campaign.py:336`] [根拠 `orchestrator/tests/test_s8b_floor_campaign.py:2546`] |

## 新規所見

### [severity: must-fix] fresh で拒否した wrong-root completion が次回 cache hit で admission される

攻撃シナリオ:

1. ambient `CMAKE_TOOLCHAIN_FILE` などにより、build の `masstree_SOURCE_DIR` を期待 base 外の root E にする。argv には `FETCHCONTENT_SOURCE_DIR_*` を残さない。
2. buildcache は CMakeCache から E を観測するが、publish 前の receipt 再照合は E ではなく期待 base B に対して行う。B が元 receipt と同じなら completion を publish する。
3. campaign の fresh postflight は E と B の root mismatch を検出して拒否するが、完成 cache entry は残る。
4. 次回は同じ receipt でその entry を hitする。`cached=True` は root 照合を無条件に迂回し、B の内容再照合だけで通るため、E 由来 binary に admission receipt が発行される。

[根拠 `orchestrator/campaign/buildcache.py:1719`]  
[根拠 `orchestrator/campaign/buildcache.py:1723`]  
[根拠 `orchestrator/campaign/buildcache.py:1728`]  
[根拠 `orchestrator/campaign/buildcache.py:1768`]  
[根拠 `orchestrator/campaign/buildcache.py:1786`]  
[根拠 `orchestrator/campaign/s8b_floor_campaign.py:2096`]  
[根拠 `orchestrator/campaign/s8b_floor_campaign.py:2104`]  
[根拠 `orchestrator/campaign/s8b_floor_campaign.py:2545`]

提案: fresh publish 前に、実効 root が現在の `<base>/masstree-src` と一致することを buildcache 内で必須化し、HEAD/config/archive もその実効 root から再取得して入力 receipt と比較する。wrong CMakeCache root → completion 0 件 → 次回も `cached=False` を固定する lifecycle test を追加する。

**成果物影響:** oracle が検証した root と異なる依存で作られた binary が certified 選択へ入り、レポートと台帳の依存 identity・binary 参照が偽になる。

### [severity: nit] M1 用に見える root 負例の一部が別 gate に過剰決定されている

攻撃シナリオ: `test_floor_postflight_gate_rejects_effective_root_and_content_drift` の wrong-root fixture は `masstree-src` 自体を作っていない。root gate を削ると後段の source-missing gateが拒否し、テストは受理集合の変化ではなく診断文の不一致で赤になる。

[根拠 `orchestrator/tests/test_s8b_floor_campaign.py:2045`]  
[根拠 `orchestrator/tests/test_s8b_floor_campaign.py:2051`]  
[根拠 `orchestrator/campaign/s8b_floor_campaign.py:2104`]

提案: この parameterized node を M1 の kill 証拠に数えず、後段 verifier を正常終了させている `test_floor_postflight_cache_hit_uses_content_receipt_not_prior_absolute_root` の fresh 部分を M1 の単一理由 node とする。

**成果物影響:** 現時点の受理集合への直接影響はないが、誤った node を変異 kill 証拠として記録すると mutation 台帳が偽の緑になる。

### [severity: nit] generator 内の SOURCE_DIR・BASE_DIR 数検査は入力から発火不能

`_v2_commands` と `prepare_masstree_fetchcontent` は argv を固定要素から構成する。公開引数や `Genome.cmake_defines()` から `FETCHCONTENT_SOURCE_DIR_*` や二つ目の `FETCHCONTENT_BASE_DIR` を作る経路がなく、内部の拒否 branch を発火させる具体的入力はない。

[根拠 `orchestrator/campaign/buildcache.py:1266`]  
[根拠 `orchestrator/campaign/buildcache.py:1270`]  
[根拠 `orchestrator/campaign/buildcache.py:1280`]  
[根拠 `orchestrator/campaign/buildcache.py:1327`]  
[根拠 `orchestrator/campaign/buildcache.py:1340`]

提案: generator 側は構成不変条件と明記するか、argv validator を独立関数へ分け、SOURCE_DIR 1 個・BASE_DIR 0/2 個の具体入力で発火させる。campaign postflight の SOURCE_DIR 負例は実在する。

**成果物影響:** 現行受理集合への直接影響はないが、generator 内防壁を外部入力に対する実効 gate と記録すると保証範囲を過大表示する。

Scope は `330f67d0..5fcad04e` で段 4 §2.1 の7ファイルだけだった。base/receipt の build 引数と runtime field は `sort_best` にだけ付与され、既定 caller の preimage は receipt が `None` なら不変である。[根拠 `orchestrator/campaign/buildcache.py:933`] [根拠 `orchestrator/campaign/s8b_floor_campaign.py:2489`] 非 sort の binary 参照変更、`FETCHCONTENT_FULLY_DISCONNECTED`、pinned-clean・全 floor・全 node・全 profile への一般化主張は認めなかった。

## 変異予測

- **M1:** 赤 — `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_postflight_cache_hit_uses_content_receipt_not_prior_absolute_root`。fresh 部分で後段 verifier は正常終了するため、root gate 削除だけで `pytest.raises` が失敗する。なお `test_floor_postflight_gate_rejects_effective_root_and_content_drift` は別 gate に過剰決定されており、単一理由証拠にはしない。
- **M2:** 赤 — `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_postflight_gate_rejects_effective_root_and_content_drift[config_sha256-config.h が変化]`。
- **M3:** 赤 — `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_receipt_change_misses_and_empty_default_preserves_identity`。
- **M4:** 赤 — `orchestrator/tests/test_s8b_floor_campaign.py::test_production_floor_dependency_preflight_failure_persists_private_attempt[configure]` と `[target]`。握り潰すと oracle 用 fixture へ進み、単一理由で失敗する。
- **M5:** 赤 — `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_base_is_canonical_single_define_and_receipt_in_preimage`。
- **M6:** 赤 — `orchestrator/tests/test_s8b_floor_campaign.py::test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`。
- **M7:** 赤 — semantic な旧共有-cache復元なら `test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle`、`test_production_floor_preflight_marker_precedes_toolchain_and_dependency_probes`、`test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`。削除済み helper 名だけを戻して `NameError` にする変異は注入不成立として数えない。
- **M8:** 赤 — cache receipt から archive key を外す元所見の変異は `orchestrator/tests/test_s8b_floor_campaign.py::test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`。fake が独立 3-key literal を要求するため単一理由で赤になる。buildcache の preimage 記録側を外す変異は `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_base_is_canonical_single_define_and_receipt_in_preimage` が赤になる。

## 判定

**NO-GO** — fresh postflight で拒否した wrong-root completion が cache に残り、次回 hit の root 免除によって admission される lifecycle 欠陥がある。

## 総括

- 変更 scope は裁定どおり7ファイルに限定されている。
- A-3、B-2、B-3、B-4 は静的には閉じた。
- G1 の片方向化は非 sort field の拒否を緩めていない。
- H2 seam は production の `Path.stat()` を省略せず、通常挙動も変えていない。
- H1 の `buildcache` は production と同一 module object へ束縛された。
- ただし A-1 の cache-hit root 免除と A-2 の publish 順序が危険に合成される。
- publish 前 receipt は実効 root ではなく期待 base を観測している。
- そのため fresh で拒否した binary が次回 cache hit で受理されうる。
- M1〜M8 は赤になる node があるが、この二段 lifecycle 攻撃は事前登録変異に含まれない。
- generator 内には具体的入力から発火不能な補助 gate が残る。
- 同型の偽の緑として、M1候補 node の後段 source-missing mask を確認した。
- pytest は実行しておらず、緑の数値は親の実測値としてのみ扱った。