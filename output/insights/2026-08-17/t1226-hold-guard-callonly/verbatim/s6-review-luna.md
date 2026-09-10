## 所見

1. **主張:** `spec_from_file_location` 系の自己読込検出には偽陰性がある。  
   **根拠:** `orchestrator/tests/test_growth_test_holds_contract.py:826-845` は、`spec.loader.exec_module(...)` の変数名と、単純な `ast.Assign` の代入先だけを照合する。  
   **具体的な失敗シナリオ:** `loader = spec.loader; loader.exec_module(module)` または `spec: object = spec_from_file_location(..., __file__)` は、実際には自己読込するのに静的確認結果が `(False, ())` になった。binding error にもならず、裁定の「解決不能なら fail-closed」を破る。現行 F351 の二例は検出できるが、同じ loader 族を閉じ切れていない。  
   **重大度:** must-fix

2. **主張:** pytest 駆動判定は frame 取得不能時に fail-open になる。  
   **根拠:** `orchestrator/tests/growth_test_holds.py:614-624` は `inspect.currentframe()` が `None` の場合も `False` を返し、同ファイル `:673-681` が call-only import を許可する。  
   **具体的な失敗シナリオ:** frame introspection 非対応環境では `pytest --noconftest` の import を普通の loader と誤認する。held 本体の wrapper は残るが、fixture 先払いを collection 時点で止める費用層が失われる。判定不能は拒否へ倒す必要がある。  
   **重大度:** must-fix

3. **主張:** 新しい実 consumer 回帰検査は、開発に伴って増える source bytes を毎回追加 parse する。  
   **根拠:** `orchestrator/tests/test_growth_test_holds_contract.py:1135-1160,1266-1275`。13 held file の外側 source は合計 1,382,252 bytes、nested source を含む総 parse 入力は 1,391,119 bytesだった。外側 parse は既存検査との統合だが、nested parse 8,867 bytesは増分である。さらに実 consumer 二本の新規検査は外側 545,446 bytes、nested 込み 548,386 bytesを別途 parseする。  
   **具体的な失敗シナリオ:** `test_s8b_floor_campaign.py` と `test_dev_waves_integration.py` が成長するたび、全受入の当該 node が線形に遅くなる。新設 detector の実 file 部分だけで現在約 557 KB の増分であり、段 4 の「単一 parse へ統合」と「開発するほど遅くしない」に反する。  
   **重大度:** must-fix

## 発火予測表

| 登録済み held file | 予測 | 理由 |
|---|---|---|
| `test_campaign_import_invariant.py` | しない | 自 file を実行する loader はなく、検出結果は `(False, ())`。 |
| `test_check_docs.py` | しない | `:1935` と `:9761` は一時 repo の `tools/spool_fold.py`、`:3955` は一時 repo の `tools/check_docs.py`。いずれも full path が foreign。 |
| `test_codex_reasoning_ab.py` | しない | `:61-67` は `tools/codex_reasoning_ab.py` の読込で foreign。 |
| `test_env_attestation.py` | しない | nested source 124 bytesも parseされるが自己読込なし。 |
| `test_real_repo_serialization.py` | しない | `:121-128` は `conftest.py`、`:1048-1049,1130-1131` は別 test module。自 module ではない。 |
| `test_ruleops.py` | しない | `:27-40` は `tools/ruleops.py` と `tools/run_tests.py` の foreign loader。 |
| `test_s1_known_axes_freeze.py` | しない | 認識対象の自己 loader なし。 |
| `test_s1_measurement_freeze.py` | しない | module source の読取りはあるが、自 file の実行ではない。 |
| `test_s8b_binding_driftguards.py` | しない | 認識対象の自己 loader なし。 |
| `test_s8b_holdout_freeze.py` | しない | nested source 二本も含めて自己 import・自己 path 実行なし。 |
| `test_s8b_oracle_driver.py` | しない | nested source 二本を parseするが自己読込なし。自 source の `ast.parse` は実行 loader ではない。 |
| `test_s8b_protocol_builder.py` | しない | 多数の subprocess 呼出はあるが、自己 module を読む認識対象 loader はない。 |
| `test_s8b_repo_scan_invariant.py` | しない | loader 自体がなく、検出結果は `(False, ())`。 |

偽陰性指定の二例は、`test_s8b_floor_campaign.py:7896-7912` が `(True, ())`、`test_dev_waves_integration.py:2050-2058` も `(True, ())` となり、現行形の F351 は検出する。

## 受入で赤になりうる node

なし。

静的確認では13 fileすべて `errors=(), self_load=False` だった。registry 59件と held file 13件は不変で、`conftest.py:391-435` の collection、`test_hold_inventory.py:524`、`test_real_repo_serialization.py:1122-1171` の `inspect.unwrap`、`test_plain_runner_coverage.py:60-86` を赤くする差分も見つからない。新設 test file はなく、既存 contract file の `__main__` harness も `:1731-1732` に残る。禁止された `docs/`、`conftest.py`、13 held file、registry の編集も差分にない。

## 総括

現行13 fileには偽陽性がなく、指定された F351 二例は両方検出する。  
ただし loader alias と注釈代入で自己読込を見逃すため、検出器は最終仕様を満たしていない。  
pytest stack の判定不能も許可へ倒れており、費用層が fail-open になる。  
実 consumer 二本の追加全量 parse は成長比例なので、着地前の修正対象と判断する。