## 所見

1. **対象:** `s4-ruling.md:75-85` の変異 9 件  
   **何が起きるか:** 6 件 (`m01/m02/m03/m04/m06/m09`) は期待 node が完全集合ではない。同じ変異で複数の新規 node が赤になる。詳細は後節。遮蔽ではなく、事前登録の列挙不足である。  
   **成果物影響:** 変異を特定の機構・node に単一帰属したという mutation ledger を作れない。  
   **重大度:** **must-fix**

2. **対象:** `orchestrator/tests/test_knowledge_manifest.py:298`、`s4-ruling.md:46-48`  
   **何が起きるか:** `test_receipt_version_is_v1_for_legacy_and_v2_for_extended` は、戻り値を同じ production module の `KM.RECEIPT_SCHEMA_VERSION` と比較しているだけで、literal `"knowledge-manifest-receipt/v1"`、既存 manifest digest `6d8674...406`、receipt 全 bytes のいずれも固定していない。定数と producer を同時に変える、または version 以外の legacy receipt bytes を変える実装でも緑になる。既存の `test_receipt_is_canonical_create_only_and_claims_are_caller_inputs` も「現在生成した bytes が canonical か」を見るだけで、変更前 bytes の golden ではない。  
   **成果物影響:** 「legacy v1 bytes と digest を 1 byte も変えない」という replay 互換性の中心主張がテストで証明されない。  
   **重大度:** **must-fix**

3. **対象:** `orchestrator/tests/test_p3_s4_loop.py:5780-5822`  
   **何が起きるか:** `test_main_passes_resolved_knowledge_projection_to_proposal_loader` は、検査対象の `load_proposal_file` 自体を `load_spy` に差し替え (`5813`)、期待値も `KM.planner_projection(resolved)` を再呼出しして作る (`5821`)。例えば production projection が `data_boundary`、`knowledge_level`、`knowledge_manifest_sha256` を落としても、main と期待値が同じ誤った producer を使うため緑になる。K2 loader の semantic 検査も `sources` しか読まない (`policy.py:521-547`) 一方、role input schema の正例テストは手組み payload なので、この producer/consumer 間の欠落を補足しない。  
   **成果物影響:** main が role schema を満たす campaign-bound projection を実 consumer へ渡すという配線証拠にならない。  
   **重大度:** **must-fix**

4. **対象:** 新規テストの「Rejects」主張全般  
   **何が起きるか:** 実際の拒否点は次のとおり。末尾の「assertion only」は production の fail-closed 経路ではない。

   | node | 実際の拒否元 |
   |---|---|
   | `test_completed_empty_retrieval_is_accepted_and_recorded` | legacy 空入力は `knowledge_manifest.py:320-325` |
   | `test_empty_sources_require_declared_scope_and_completed_empty_result[...]` | scope 欠落 `320-325`、空 scope `235-237`、status 閉集合 `279-282`、status/count 矛盾 `287-290`、空 source/nonempty status `326-333` |
   | `test_extended_empty_receipt_binds_lock_wal_and_material_projection` | tampered receipt は `wal.py:996-999` から `wal.py:797-800` に到達して拒否 |
   | `test_k2_load_proposal_accepts_declared_role_output_with_empty_sources` | marker 無し wrapper は `p3_s4_loop.py:1808-1811` → `projection_guard.py:339-350` / `281-287` |
   | `test_k2_load_proposal_rejects_out_of_range_knowledge_use` | `p3_s4_loop.py:1744-1746` → `policy.py:535-542` |
   | `test_k2_load_proposal_rejects_knowledge_use_item_without_use_field` | `p3_s4_loop.py:1732-1734` → `events.py:170-186`。必須 `use` は `manifest.json:916-934` |
   | `test_k2_load_proposal_rejects_declared_instruction_like_content` | `p3_s4_loop.py:1740-1743` |
   | `test_k2_load_proposal_requires_role_and_knowledge_marker_together[...]` | `p3_s4_loop.py:1792-1797` |
   | `test_knowledge_report_projects_completed_empty_retrieval` | 手動削除後は `layer3_report.py:293-295`、条件は `layer3_schema.json:62-97` |
   | `test_schema_accepts_completed_empty_knowledge_provenance_specimen` | private `_validate_schema` の直接呼出し。legacy `minItems` は `layer3_schema.json:38-48`、extended tag は `56-59` |
   | `test_extended_schema_rejects_empty_sources_without_completed_empty_result[...]` | private `_validate_schema` の直接呼出し。`layer3_schema.json:62-97`、status/count は `392-412` |
   | `test_extended_manifest_digest_binds_scope_and_retrieval_result` | production 拒否なし。テスト自身の assertion `test_knowledge_manifest.py:278-282` |
   | `test_receipt_version_is_v1_for_legacy_and_v2_for_extended` | production 拒否なし。assertion `318-324` |
   | `test_nonempty_extended_manifest_fields_are_independently_optional` | production 拒否なし。assertion `352-355` |
   | `test_main_passes_resolved_knowledge_projection_to_proposal_loader` | production 拒否なし。spy assertion `test_p3_s4_loop.py:5821-5822` |
   | `test_coder_v4_k2_input_schema_accepts_empty_sources` | production input consumer を通らず、live spec を直接 `jsonschema` に渡す `test_codex_agents.py:1024-1046` |

   K2 の 4 loader test は public production reader を実際に通り、schema・anomaly・semantic を stub していない。standalone Layer 3 schema test と role input schema test は契約単体テストとしては有効だが、production 経路の証拠として数えてはならない。  
   **成果物影響:** assertion-only test を「production が拒否した証拠」と記録すると、fail-closed 主張が過大になる。  
   **重大度:** **should-fix**

5. **対象:** `orchestrator/codex_roles/review_ledger.py:28,61,84,124`、`orchestrator/tests/test_codex_agents.py:134-157`  
   **何が起きるか:** K2 source・description・manifest・input schema の現行 hash は同じ変更で ledger に登録され、テストは current bytes との一致を検査する。runtime に hash を自動注入する恒真 fixture ではなく、将来 drift を止める hard-coded pin ではあるが、この wave の意味的正しさは証明しない。  
   **成果物影響:** checker 緑は adapter/ledger の整合証拠に限定され、K2 consumer の実効性証拠には使えない。  
   **重大度:** **nit**

6. **対象:** `orchestrator/tests/acceptance_duration_ledger.json`  
   **何が起きるか:** 新規 16 test function、parametrize 展開後 27 nodeid はすべて未登録。collection 自体は `pytest.ini` の `testpaths=orchestrator/tests` と既存 file 内への追加なので漏れない。ledger consumer は未登録 node を unknown-cost として扱う (`conftest.py:1524-1544,1584-1613`)。coverage meta-test は 90% 閾値 (`test_acceptance_schedule_order.py:704-713`) なので、この 27 件だけでは登録漏れを赤にしない。  
   **成果物影響:** テストは実行対象から落ちないが、受入走の shard 所要時間モデルが新規 27 node を正しく扱えない。  
   **重大度:** **nit**

## 変異登録の再評価

1. **`t2246.m01` — 期待 node が誤り。**  
   期待 node は確かに kill するが、空 manifest を production parser へ通す次の 6 node がすべて赤になる。

   - `test_completed_empty_retrieval_is_accepted_and_recorded`
   - `test_extended_empty_receipt_binds_lock_wal_and_material_projection`
   - `test_main_passes_resolved_knowledge_projection_to_proposal_loader`
   - `test_k2_load_proposal_accepts_declared_role_output_with_empty_sources`
   - `test_k2_load_proposal_rejects_declared_instruction_like_content`
   - `test_knowledge_report_projects_completed_empty_retrieval`

   再登録候補はこの 6 node の完全集合。

2. **`t2246.m02` — 期待 node が誤り。**  
   `canonical_value` から scope を落とすと hash test だけでなく、receipt の直接 assertion と空 receipt の WAL 検証も赤になる。完全集合候補は次の 5 node。

   - `test_completed_empty_retrieval_is_accepted_and_recorded`
   - `test_extended_manifest_digest_binds_scope_and_retrieval_result`
   - `test_nonempty_extended_manifest_fields_are_independently_optional`
   - `test_extended_empty_receipt_binds_lock_wal_and_material_projection`
   - `test_knowledge_report_projects_completed_empty_retrieval`

3. **`t2246.m03` — 期待 node が誤り。**  
   「最初の拒否は WAL consumer だけ」は誤り。`receipt_value` の戻り値を直接見るテストが先に赤になり得る。完全集合候補は次の 4 node。

   - `test_completed_empty_retrieval_is_accepted_and_recorded`
   - `test_nonempty_extended_manifest_fields_are_independently_optional`
   - `test_extended_empty_receipt_binds_lock_wal_and_material_projection`
   - `test_knowledge_report_projects_completed_empty_retrieval`

4. **`t2246.m04` — 期待 node が誤り。**  
   K2 wrapper を legacy branch へ送ると、正例 node だけでなく、各拒否 test の invalid input が目標層より前の projection guard で止まり、また各 positive control も失敗する。完全集合候補は次の 4 node。

   - `test_k2_load_proposal_accepts_declared_role_output_with_empty_sources`
   - `test_k2_load_proposal_rejects_out_of_range_knowledge_use`
   - `test_k2_load_proposal_rejects_knowledge_use_item_without_use_field`
   - `test_k2_load_proposal_rejects_declared_instruction_like_content`

5. **`t2246.m05` — 帰属できる。**  
   入力は `use` を持つため output schema を通り、`source_index=1` は source 数 1 に対する範囲外なので `policy.py:535-542` だけが拒否する。semantic call を除去すると期待 node の `pytest.raises` が失敗する。他の新規 node に同じ不正入力はない。

6. **`t2246.m06` — 期待 node が誤り。**  
   standalone 正例だけでなく、実 report producer と parameterized test 内の completed-empty positive control も赤になる。完全集合候補は次の 7 node。

   - `test_schema_accepts_completed_empty_knowledge_provenance_specimen`
   - `test_knowledge_report_projects_completed_empty_retrieval`
   - `test_extended_schema_rejects_empty_sources_without_completed_empty_result[...]` の 5 展開すべて

7. **`t2246.m07` — 帰属できる。**  
   projection guard は `knowledge_use` item の内部を見ない。schema call を除去しても semantic validator は `source_index` だけを読み、`use` 欠落を拒否しない (`policy.py:533-547`)。したがって期待 node だけが赤になる。

   `m05` と `m07` が互いに遮蔽しないという親判断は正しい。`m05` の入力は schema-valid な範囲外 index、`m07` の入力は semantic-valid な範囲内 indexかつ `use` 欠落で、拒否層は排他的である。

8. **`t2246.m08` — 帰属できる。**  
   `instruction_like_content_detected=true` は schema-valid で、semantic policy はこの flag を判定しない。`p3_s4_loop.py:1740-1743` を除去すれば期待 node だけが赤になる。

9. **`t2246.m09` — 期待 node が誤り。KILLED 自体は成立する。**  
   正例 node の `false` 申告は確実に過剰拒否される。ただし同じ `false` を既定とする他の K2 test も赤になる。完全集合候補は次の 4 node。

   - `test_k2_load_proposal_accepts_declared_role_output_with_empty_sources`
   - `test_k2_load_proposal_rejects_out_of_range_knowledge_use`
   - `test_k2_load_proposal_rejects_knowledge_use_item_without_use_field`
   - `test_k2_load_proposal_rejects_declared_instruction_like_content`

## 焦点走に含めるべき file

変更 symbol とその参照先から引くと、最低限次を含めるべきである。

- `orchestrator/tests/test_knowledge_manifest.py`
- `orchestrator/tests/test_p3_s4_loop.py`
- `orchestrator/tests/test_layer3_report.py`
- `orchestrator/tests/test_codex_agents.py`
- `orchestrator/tests/test_p3_b4_closed_critic.py` — `L.load_proposal_file` の既存 B4 caller (`:2901`)
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py` — 共有 `assert_closed_proposal_schema` の legacy/trigger consumer (`:54`, `:2106` 以降)
- `orchestrator/tests/test_p3_b4_launcher.py` — `L.main` の driver registry (`:322,326`)
- `orchestrator/tests/test_p3_build_authority_cli.py` — `p3_s4_loop.main` を CLI entrypoint として列挙 (`:74`)
- `orchestrator/tests/test_p3_exploration_namespace.py` — 同 main の coder entrypoint 契約 (`:418`)
- `orchestrator/tests/test_campaign_import_invariant.py` — `p3_s4_loop.py` に追加された cross-package import の repository-wide consumer
- `orchestrator/tests/test_ccbench_spawn_sites.py` — `knowledge_manifest.py::_git` の process-spawn inventory (`:117`)
- `orchestrator/tests/test_acceptance_schedule_order.py` — duration ledger の実 collection coverage consumer
- `orchestrator/tests/test_pytest_collection_config.py` — test file 集合を動的 tree discovery に束縛する meta-test (`:1105-1109`)

実装子が明示したのは変更した 4 test file で、`test_p3_b4_closed_critic.py` は波及例として言及したものの、焦点 argv は提示していない。上記の追加 consumer 群は焦点走から漏らさない方がよい。

## 総括

最も実効性が低いのは `test_main_passes_resolved_knowledge_projection_to_proposal_loader` で、callee を stub し、期待 projection も同じ production producer から再生成している。  
加えて legacy v1 の exact bytes/digest 維持には独立 golden がなく、中心的な互換性主張が未証明である。  
`m05` と `m07` の非遮蔽判断、および `m08` の単一帰属は静的には正しい。`m09` も KILLED だが期待 node 集合は誤っている。  
pytest・変異は実走していない。少なくとも mutation expected sets と legacy golden、main projection の独立検査を直すまでは段 7 へ進めない。