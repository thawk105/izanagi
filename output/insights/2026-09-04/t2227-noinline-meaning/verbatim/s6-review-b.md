## must-fix

無し。

## nit

- 対象: `orchestrator/tests/test_condition_meaning_gate.py:724-730`。既存 8 macro について、fixture 内の全 `#if` を拾う検査から宣言行だけを拾う検査へ狭まり、余分な条件分岐を見逃す方向に弱化している。ただし registry、patch の追加行、factory の 1/0 契約は別 assert で維持され、現成果物への影響は示せない。
- 対象: `orchestrator/tests/test_paper_story_a2_certification.py:529-573`。sentinel を evaluator まで渡す検査は有効だが、`:573` の undeclared message 不在は evaluator stub が常に green を返すため、M7 に対して独立の検査にならない。`:71` の source 文字列検査も同じ node 内で先に赤になる冗長 gate。
- 対象: `orchestrator/tests/test_s1_direct_comparison.py:54-89`。実 noinline 検査は `certified-selection` だけで、`develop` の `raw` と `floor` を実 factory 宣言で直接通していない。production helper 内では `use_class` より前に同じ factory を呼ぶため配線自体は共通だが、role test は autouse stub に置換される。
- 対象: `orchestrator/tests/test_pegasus_calibration_workload.py:104-136`。新規 workload は `BACKOFF_NOINLINE=0` だけで、値 1 を明示的に pin しない。また factory 返値との等値比較は、同値 object の直接構築を factory 由来と区別しない。production のループは値 0/1 とも同じ factory 呼出しへ到達する。
- 対象: `orchestrator/tests/fixtures/condition_meaning_gate/supplied/include/backoff.hh:1`。fixture 全体は 3 行、54 bytes 増えて full-file hash と既存行番号が変わる。一方、追加は EVOLVE block より前なので `test_condition_meaning_gate.py:2140-2151` の conditional、hole、期待行 bytes は不変。射影内の `condition_gate_test_support`、`test_build_site_gate`、`test_t316_sandbox_probe` に full-file bytes、固定 hash、固定行数の assert はない。
- CMake configure の増分は condition suite の 8 回に加え、s1 の新規実 factory test が supply 2 回と meaning 2 回を行うため、合計 12 回。裁定の「+8〜10回」より 2 回多く、静的見積りは約 +2〜3 秒。
- A-2 の undeclared-message assert、s1 の独立 factory 型 assert、t1683 の legacy assert は、対象 driver の新配線を空にしても単独では緑になる。各 test 全体としては別 assert が M7、M8、M9 を殺す。
- 配線しない driver の理由は ruling と author report の間では一致する。指定された実コード 5 file と repo 全体の artifact 検索は読取り射影に含まれないため、コードおよび凍結成果物の独立照合はできていない。author report の主張は repo `output/` 内が空集合、repo 外は未走査。

## 変異 M1〜M10 と test の対応の検証

- M1: `test_condition_meaning_gate.py::test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one` は declaration 型 assert、`::test_backoff_noinline_factory_accepts_only_default_zero_binary_requests[0-0-True]` は declared assert で赤。さらに s1 の noinline test と t1683 の factory test も同じ「0/0 宣言が None」で赤になるため、report より冗長。
- M2: `test_condition_meaning_gate.py::test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one` は meaning が非識別 red となり status assert で赤。schema test の初期 green assert と s1 noinline test も同じ理由で赤になる。
- M3: `test_condition_meaning_gate.py::test_header_shadow_preserves_directory_symlinks_and_git_link` の shadow topology assert と inert test の owner-TU operand/status assert が殺す。旧 helper を文字どおり戻して計装 header 自体を operand にすると requested-one test は green の可能性があり、author report の「要求 1 正例も必ず殺す」は静的には確定しない。
- M4: `test_condition_meaning_gate.py::test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one` の「`request.owner_tu` で終わる operand がちょうど 1 個」assert が赤。requested-one test には同 assert がない。
- M5: `test_condition_meaning_gate.py::test_backoff_noinline_requested_one_supply_and_meaning_are_green` が、旧挙動なら configured command 不在、単純な条件削除なら build root 同一の assert で赤になる。
- M6: `test_condition_meaning_gate.py::test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one` の `_validate_arm_record_integrity(meaning)` が逆順 0/1 evidence を拒否して赤になる。
- M7: `test_paper_story_a2_certification.py::test_paper_condition_gate_is_p_strict_and_precedes_campaign` が source 文字列 assert と sentinel identity assert で赤。undeclared message 不在 assert は独立には殺さない。
- M8: `test_s1_direct_comparison.py::test_prepare_cell_condition_family_uses_real_two_arm_api` の source 文字列 assert と `::test_noinline_inert_meaning_record_comes_from_registry_factory` の green/unestablished assert がともに赤になる。
- M9: `test_pegasus_calibration_workload.py::test_cost_probe_uses_factory_noinline_and_legacy_backoff_declarations` の noinline declaration exact-type assert が None を拒否して赤になる。既存の every-genome test は declaration を検査せず、単独では殺さない。
- M10: `test_condition_meaning_gate.py::test_compile_time_factory_rejects_nonpaired_values[0-0]` が、既存 macro の 0/0 を None とする assert で赤になる。既存 8 macro の 1/0 正例と `MEANING_SUPPORTED_MACROS` の完全集合 pin、`SUPPLY_DOMAIN_MACROS - {"BACKOFF_FIXED"}` の旧宣言拒否 pin も維持されている。

## 総括

- 静的検査では、A-2、s1、t1683 の factory 返値は evaluator まで到達し、`BACKOFF_FIXED` の既存 override/fallback も保持されている。
- s1 helper は `use_class` に依存せず宣言を決め、t1683 の値 1 もコード上は factory 宣言になる。
- A-2 receipt、s1 WAL、t1683 JSON は noinline meaning record、record digest、admission digestと参照、未確立一覧の bytes が変わる。
- 成果物を誤って変える must-fix は見つからなかったが、M3 の report 対応、role/value coverage、configure 数には上記のずれがある。
- pytest、実 compiler、repo 全体検索は実行していない。