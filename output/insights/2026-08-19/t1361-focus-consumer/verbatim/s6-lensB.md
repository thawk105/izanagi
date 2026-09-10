## 所見

追加の `real` は1件です。

- **real — 既存の順序検査にも O26 連結の回帰がある。**  
  `orchestrator/tests/test_check_docs.py:8179` の `test_dev_wave_operation_order_rejects_titleless_reorder_and_missing_target` も、O25節を末尾改行ごと削除しています。O26追加後は O26 が前節へ連結され、H2として消えます。純粋なfixture再構成でも O26のH2数は0になりました。  
  checkerは意図した順序違反に加え、O26のH2欠落とexact pin不一致も出します（`tools/check_docs.py:4881`, `tools/check_docs.py:4923`）。しかし `orchestrator/tests/test_check_docs.py:962-967` の `_assert_violation` は needleの存在しか確認しないため、無関係な2 findingを伴ってもテストは通ります。O25除去方法の修正対象にこの箇所も含め、finding集合または件数を固定すべきです。

親が既に確認した次の2件は、再確認でも `real` です。

- `o25_before_o01`: `orchestrator/tests/test_check_docs.py:6222`
- `condition_all_operations_deleted` の期待件数: `orchestrator/tests/test_check_docs.py:6610-6612`

### `_COMMAND_GUARD_CASES` 全件

`orchestrator/tests/test_check_docs.py:6408-6505` の全登録と `:5700-6405` の全mutation分岐を確認しました。

- `dw-o01-wrong-pid-source`、`o23_land_helper_deleted`、`operations_land_helper_outside_o23`、`o25_contract_weakened` は節内部だけを変更し、O26の境界を壊しません（`:5809-5817`, `:6188-6208`, `:6209-6217`）。
- stage dispatch系・既存condition系は `dev-wave.md` の行だけを変更します。
- `condition_18_o18_deleted` は O18 が段5/6の全 operations dispatchにも残るため、閉包findingは増えません（`tools/check_docs.py:704-708`）。
- `registered_reference_deleted` はファイル全体削除であり、O26追加による件数変化はありません（`:6394-6395`）。

したがって、親の2件と上記の順序検査以外に同種の実害はありません。`refuted`。

### 期待件数

`_COMMAND_GUARD_EXPECTED_COUNTS` の既存非1件エントリ（`:6613-6622`）を確認しました。O26により新たに増えるのは、O26を唯一consumerとする `condition_18_o26_deleted` と、親既知の全削除ケースだけです。

- `condition_18_o18_deleted`: 1件のままで妥当。
- `condition_18_o26_deleted`: 2件は、condition不一致とregistry閉包欠落で、同じO26配線欠落に直接由来。
- `condition_26_*`、`dispatch_allowlist`、Codex startup系はO26の影響なし。

その他の件数変更は不要です。`refuted`。

### 新設negative control

次の判定です。

- `condition_18_o18_deleted`: 1件、condition 18の参照集合不一致のみ。`refuted`
- `condition_18_o26_deleted`: 2件だが、配線欠落に直接関係する2面のみ。無関係findingではない。`refuted`
- `condition_18_trigger_broadened`: trigger不一致の1件のみ。`refuted`
- `o26_section_deleted`: H2欠落とexact pin不一致の2件。どちらも同じ節削除に直接関係する。`refuted`
- `o26_heading_only`: exact pin不一致の1件。`refuted`
- `o26_contract_weakened`: exact pin不一致の1件。`refuted`

登録、needle、期待件数の対応も一致しています（`:6443-6446`, `:6476-6478`, `:6543-6546`, `:6576-6578`）。

### meta-test と合成fixture

O26は以下へ漏れなく反映されています。

- production constant / exact-section registry: `tools/check_docs.py:446-475`
- operation registry、condition 18の複数節配線: `tools/check_docs.py:614-617`, `:721-728`
- operation外延と配線meta-test: `orchestrator/tests/test_check_docs.py:6710-6747`
- L2期待集合: `orchestrator/tests/test_check_docs.py:2283-2290`, `:2721-2728`
- exact pinとraw HTML negative control: `orchestrator/tests/test_check_docs.py:8069-8097`, `:8117-8145`
- 合成operations fixtureとcondition 18行: `orchestrator/tests/test_check_docs.py:803-859`, `:694-703`

純粋なfixture構築確認でも、operationsはO26を含む21節、condition 18は `(DW-O18, DW-O26)` の2参照、O26は470 bytesになりました。`refuted`。

pytest全走は、read-only環境で一時ディレクトリを確保できず実行不能でした。緑とは報告していません。

## 総括

親既知2件に加え、O25除去を再利用する順序検査のテストオラクル汚染を1件発見しました。その他のguardケース、期待件数、negative control、meta-test、合成fixtureには追加の実害はありません。