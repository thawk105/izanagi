## 所見

1. 主張: P2 の検出規則は package self-import と `runpy.run_module` を取りこぼす。  
   根拠: 親 brief:11-19、plan:56-63、`test_dev_waves_integration.py:2050-2055`、`test_s8b_floor_campaign.py:3217-3222`。  
   具体的な失敗シナリオ: integration を将来 hold 登録しても検出器は self-load なしと判定し、既定の import-and-call binding を受理する。subprocess package import 時に `growth_test_holds.py:646-655` が import を拒否し、F351 型の受入赤になる。  
   重大度: blocker

2. 主張: `__file__` の「由来」ではなく、最終 loader path が当該 test file と同一かを比較しなければならない。  
   根拠: `test_check_docs.py:1934-1941,3952-3960,9760-9768`、`test_check_docs.py:6422-6423`、`test_codex_reasoning_ab.py:59-67`、`test_ruleops.py:22-40`、plan:61。  
   具体的な失敗シナリオ: `__file__` から repo root を導出しただけで self-load 扱いすると、foreign tool loader と単なる自己ソース読込まで発火し、現行 `test_check_docs.py` を誤って call-only 必須にする。  
   重大度: must-fix

3. 主張: call-only 候補の「guard 前に元関数の別名を逃がしていない」条件が、実装契約・静的検査・正例に入っていない。  
   根拠: wrapper は `growth_test_holds.py:599-606,640-644` で canonical global だけを差し替える。plan:35-43 の exact 述語に alias 条件がなく、plan:101-103 は記録提案に留まる。既存検査 `test_growth_test_holds_contract.py:683-700` も canonical 名だけを呼ぶ。  
   具体的な失敗シナリオ: `saved = test_held` を guard 前に作り、subprocess が `saved()` を呼ぶと、元関数が実行され body marker が出る。call-only の「呼出拒否」不変条件を破る。import-time の高コスト処理も同様に選別条件から漏れている。  
   重大度: blocker

4. 主張: 検査は既定 pytest 全走には入るが、「lease 消費前の静的 gate」にはなっていない。  
   根拠: `pytest.ini:12-14`、`tools/run_tests.py:53-54,380-399`、`conftest.py:390-435`、contract test の loop `test_growth_test_holds_contract.py:622-641`、plan:8,58-63,87。  
   具体的な失敗シナリオ: 現行 13 file には canonical self-load がなく、実 registry 上の call-only 分岐は一度も実データで発火しない。synthetic control が緑でも、registry から binding 判定へ接続する部分の退行は残る。個別 file 走や `-k` 選択走では contract test 自体が走らない。  
   重大度: must-fix

5. 主張: 母集合は全 repo glob ではないが、held source の総量に比例する費用は残る。  
   根拠: `test_growth_test_holds_contract.py:508-589,638-641`。現行 13 file の静的計測は約 1,382,252 bytes / 36,016 lines。  
   具体的な失敗シナリオ: hold file が増えたり巨大化したりすると、各 contract 走で全 source の読込・AST 化が増え、受入前の焦点走が lease 窓を圧迫する。少なくとも tree と self-load 判定を一回の parse に統合し、別走査を増やさない必要がある。  
   重大度: nit

6. 主張: 変異帰属に重複がある。  
   根拠: plan:71,76-78、既存 `test_growth_test_holds_contract.py:683-700,731-763`。  
   具体的な失敗シナリオ: default を call-only にする変異は既存の `test_noconftest_bypass_is_refused_before_held_body` と `test_import_guard_rejects_nonempty_nonexact_release_token` が先に落とす。wrapper 削除も `test_all_registered_nodes_are_call_time_wrapped` が先に落とすため、新しい call-only 正例の帰属は mode 分岐・import 成功・body 未到達に限定すべきである。  
   重大度: must-fix

## 発火予測表

| 保留登録済み file | 発火予測 | 理由 |
|---|---|---|
| `test_campaign_import_invariant.py` | しない | guard は `:1707-1708`。自己 loader ではなく、fixture 内の文字列・scan 対象。 |
| `test_check_docs.py` | しない | `:1935,3955,9761` は `spool_fold.py` または tmp `check_docs.py`。`__file__` は `:6422-6423` のソース読込だけ。 |
| `test_codex_reasoning_ab.py` | しない | `:61-67` は `tools/codex_reasoning_ab.py` の foreign loader。guard は `:7081-7082`。 |
| `test_env_attestation.py` | しない | guard `:1359-1360`。canonical self-load なし。 |
| `test_real_repo_serialization.py` | しない | `:121-128` は foreign `conftest.py` loader。guard は `:33,1670`。 |
| `test_ruleops.py` | しない | `:27-40` は `tools/ruleops.py` と `tools/run_tests.py`。guard は `:3455-3456`。 |
| `test_s1_known_axes_freeze.py` | しない | guard `:25,678`。自己 loader なし。 |
| `test_s1_measurement_freeze.py` | しない | guard `:23,322`。自己 loader なし。 |
| `test_s8b_binding_driftguards.py` | しない | guard `:536-537`。自己 loader なし。 |
| `test_s8b_holdout_freeze.py` | しない | guard `:1961-1962`。subprocess は production/fixture 対象で自己 loader ではない。 |
| `test_s8b_oracle_driver.py` | しない | `:819-822` は dynamic `source_path` を使う custom loader だが、当該 test file の `__file__` ではない。guard は `:5294-5295`。 |
| `test_s8b_protocol_builder.py` | しない | guard `:41,1865`。自己 loader なし。 |
| `test_s8b_repo_scan_invariant.py` | しない | guard `:54-55`。自己 loader なし。 |

登録外の実測 control では、`test_s8b_floor_campaign.py:7896-7901` は detector 単体なら発火する。一方、`test_dev_waves_integration.py:2050-2055` の package self-import は計画どおりなら発火せず、false negative になる。

## 総括

- P1 の独立 `guard_mode` は、`PlainRunner` の AST 由来意味と衝突しないため支持する。  
- P2 は foreign path を除外する狭い意味では支持するが、package import・`run_module`・path 同一性の明示不足で反証される。  
- P3 の synthetic module は registry 不変条件を守るため支持する。ただし live registry の陽性分岐は別途必要である。  
- scope は runtime mode と選別検査の両方を含み、registry 変更や helper 切出しへの逸脱はない。  
- pytest は依頼どおり実行していない。