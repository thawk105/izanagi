## 総括

最も重い所見は、current profile の正例が呼び手計算の hash seam を常用しており、production CLI の pin 強制を current 入力で検証していないことです。current 限定の自己 hash 化を混入しても全追加テストが通ります。  
現物の pin 実装、legacy 分岐、caption、Lustre EINVAL 退避自体には静的な契約違反を見つけませんでした。CLI から `main(expected_hashes=...)` へ到達する現行経路もありません。  
ただし複数の重要な拒否検査に、削除を赤にする node がないため、この差分は現状では採らない判断です。  
read-only 指示に従い pytest は実行しておらず、以下は静的検査結果です。

## 所見

1. **current CLI の pin 強制が mutation-pinned ではない**

   - 主張: current の全正例は fixture と同じ呼び手が計算した hash を `expected_hashes` に渡しており、repo 所有 pin 表を経由していません。
   - file:line の根拠: `orchestrator/tests/test_plot_a2_certification.py:322-327,392-404,732-734`。現行実装は `tools/plotting/plot_a2_certification.py:106-125,811-828,841-842` で正しく CLI と kwargs を分離していますが、CLI テスト `:567-582` は legacy bytes だけです。
   - 最小変異と期待 node: `main()` に「current schema のときだけ入力 2 file の実 hash を期待値にする」分岐を足す。`test_cli_has_no_caller_selected_hash_options` は parser 不変なので緑、legacy を使う `test_cli_rejects_exact_bytes_at_certification_path_missing_from_pin_table` も緑です。赤になる既存 node はありません。
   - 放置時の成果物への影響: current の改変 certification/status/effects と自己計算 hash の組を同じ呼び手が publish できる退行を、テストが検出しません。
   - **must-fix**

2. **WAL の 2 token authority を同時に壊しているため、各比較を単独では pin できていない**

   - 主張: 実装は `build_start.payload.src_token` と `build_admission.source.src_token` を別々に比較しますが、テスト helper は両方を同時に変更します。
   - file:line の根拠: 実装 `tools/plotting/plot_a2_certification.py:393-401`、同時変更 helper `orchestrator/tests/test_plot_a2_certification.py:353-360`、期待 node `:498-511`。
   - 最小変異と期待 node: token tuple から `start_payload.get("src_token")` だけ、または `admission_source.get("src_token")` だけを削除する。期待される `[wal]` case は、もう一方の不一致で引き続き緑になります。
   - 放置時の成果物への影響: manifest-bound WAL 内で片方だけ異なる source identity を current-full 図の根拠として受理する退行が検出されません。
   - **must-fix**

3. **current-full 受理集合の複数の重要な拒否枝に負例がない**

   - 主張: raw schema、embedded-policy identity、WAL build-start 一意性、policy-bound workload 条件、symlink/claim path に対応する mutation node がありません。
   - file:line の根拠:
     - embedded policy identity/cell identity: `tools/plotting/plot_a2_certification.py:190-205`
     - claim path / symlink: `:273-291,318-321`
     - current raw schema: `:373-375`
     - build-start mapping: `:385-391`
     - workload condition: `:437-444`
     - schema テストが変更するのは cert/manifest のみ: `orchestrator/tests/test_plot_a2_certification.py:430-446`
   - 最小変異と期待 node: v2 raw を current でも許可する、policy protocol equality を削除する、build-start 一意性を削除する、`condition != expected` を削除する、symlink 拒否を削除する、の各変異。いずれも対応する既存 node がありません。
   - 放置時の成果物への影響: current-full provenance が legacy raw、異なる protocol、曖昧な WAL、policy と異なる測定条件、または measurement root 外の参照を受理する退行を検出できません。
   - **must-fix**

4. **caption テストが同義の D1198 過剰主張を許す**

   - 主張: 現行 caption は証拠範囲内ですが、テストは `"gate passed"` という一表現しか禁止しません。
   - file:line の根拠: 正しい本文は `tools/plotting/plot_a2_certification.py:549-552,589-606`。テストは `orchestrator/tests/test_plot_a2_certification.py:556-564`。
   - 最小変異と期待 node: current gate note に `D1198 was executed successfully.` を追加し、既存の必須部分は残す。`test_current_gate_copy_is_receipt_observation_not_legacy_fixed_copy` は全 assert を満たして緑です。
   - 放置時の成果物への影響: 保存されていない supply/meaning evidence に基づき「D1198 を実施・成功した」と caption が主張しても検出されません。
   - **must-fix**

5. **新しい landed bundle closure は helper を置いただけで発火しない**

   - 主張: 新図用と読める closure helper は定義されるだけで、test node から呼ばれていません。
   - file:line の根拠: `orchestrator/tests/test_plot_a2_certification.py:585-591`。同名参照はこの定義 1 件だけです。既存 landed test `:828-839` は旧 prefix を直接検査します。
   - 最小変異と期待 node: `_assert_named_landed_bundle` を丸ごと削除する。赤になる node はありません。
   - 放置時の成果物への影響: 新しい PNG/PDF/provenance の欠落、closure 不一致、README caption 未登録がテスト成功と両立します。
   - **must-fix**

6. **一部の検査は重複しており、個別削除に帰属できない**

   - 主張: `source_binding_status` は二層で同じ入力を拒否し、12-file closure も件数と key set の二層です。
   - file:line の根拠: `tools/plotting/plot_a2_certification.py:204-205,403-404,244-246,284-285`。テストは `orchestrator/tests/test_plot_a2_certification.py:449-457,514-518`。
   - 最小変異と期待 node: いずれか片方だけ削除する。対応 node は残った層で拒否され、緑のままです。
   - 放置時の成果物への影響: 現時点の値・受理集合・参照は変わりませんが、DW-M01 の単一理由性を個別層へ帰属できません。
   - **nit**

## 発火しない保証の一覧

`PLOT::` は `orchestrator/tests/test_plot_a2_certification.py::`、`A2::` は `orchestrator/tests/test_paper_story_a2_certification.py::` の略です。

| 追加された検査 | 最小変異 | 期待 node | 静的判定 |
|---|---|---|---|
| EINVAL fallback | EINVAL を再送出 | `A2::test_atomic_write_bytes_noreplace_einval_uses_create_only_hard_link` | 発火 |
| create-only hard link | 既存 destination を消してから link | `A2::test_atomic_write_bytes_noreplace_einval_hard_link_refuses_existing_name` | 発火 |
| 非 EINVAL 非退避 | EIO も fallback へ流す | `A2::test_atomic_write_bytes_noreplace_non_einval_is_not_fallback` | 発火 |
| current-full 正例/12 members | current plan から追加 members を外す | `PLOT::test_current_full_profile_uses_producer_policy_and_exact_twelve_file_closure` | 発火。ただし pin 表は通らない |
| embedded policy hash | SHA 比較を削除 | `PLOT::test_current_rejects_embedded_policy_hash_mismatch` | 発火 |
| top-level status vocabulary | `"bound"` を許可 | `PLOT::test_current_top_level_status_uses_verdict_vocabulary_not_bound` | 発火 |
| artifact-derived order | legacy orderを固定 | `PLOT::test_current_full_policy_order_is_artifact_derived` | 発火 |
| cert/manifest schema pair | crossed pair を current として許可 | `PLOT::test_current_rejects_schema_crosses_and_partial_families` | 発火 |
| 12-file count/key set | 片方だけ削除 | `PLOT::test_current_rejects_twelve_file_closure_underflow_and_overflow` | **個別には不発火** |
| receipt existence | missing-file 分岐を削除 | `PLOT::test_current_rejects_missing_manifest_bound_condition_receipt` | 発火 |
| receipt hash | receipt の hash 比較を飛ばす | `PLOT::test_current_rejects_condition_receipt_hash_mismatch` | 発火 |
| passive member hash | campaign-lock の hash を飛ばす | `PLOT::test_current_hash_checks_passive_campaign_closure_members` | 発火 |
| receipt canonicality | canonical JSON equality を削除 | `PLOT::test_current_rejects_noncanonical_condition_receipt` | 発火 |
| `admitted=true` | admitted 検査を削除 | `PLOT::test_current_rejects_condition_receipt_admitted_false` | 発火 |
| receipt/raw/cert token | 各 authority 比較を削除 | `PLOT::test_current_rejects_each_src_token_authority_mismatch` | 発火 |
| WAL の 2 token | どちらか一方だけ比較から削除 | 同 `[wal]` case | **不発火** |
| `source_binding_status=bound` | 二層の片方だけ削除 | `PLOT::test_current_rejects_nonbound_source_binding_status` | **不発火** |
| role/token compatibility | stock/adopted 制約を削除 | `PLOT::test_current_rejects_role_wrong_tokens_even_when_all_four_authorities_agree` | 発火 |
| median/effect recomputation | 各 crosscheck を削除 | `PLOT::test_current_recomputes_certification_medians_and_effects` | 発火 |
| receipt由来 caption | legacy 固定文へ戻す | `PLOT::test_current_gate_copy_is_receipt_observation_not_legacy_fixed_copy` | 発火 |
| caption の過剰主張禁止 | `"gate passed"` 以外の同義表現を追加 | 同 node | **不発火** |
| CLI hash option 禁止 | 別名 `--hash-pair` を追加して forward | `PLOT::test_cli_has_no_caller_selected_hash_options` | **不発火** |
| unpinned path 拒否 | current 限定で自己 hash 化 | current 正例群・CLI 2 node | **不発火** |
| current raw v3 固定 | current で raw v2 も許可 | 該当なし | **不発火** |
| embedded policy identity/cells | protocol または cell equality を削除 | 該当なし | **不発火** |
| symlink/claim canonical path | 拒否を削除 | 該当なし | **不発火** |
| unique WAL build-start | 一意性検査を削除 | 該当なし | **不発火** |
| policy-bound workload 条件 | `condition != expected` を削除 | 該当なし | **不発火** |
| named landed closure | helper を削除 | 該当なし | **発火しない helper** |
| policy bytes golden | tracked destination を戻す | `A2::test_p1_a2_default_policy_bytes_and_protocol_are_unchanged` | 発火 |

legacy 経路については、schema pair が exact、compatibility constants/defaults が legacy のまま、current-only 検査も profile 分岐内であるため、静的には受理集合の拡大を認めませんでした。

## 凍結境界の確認

統合 patch に `diff --git a/output/...` はありません。凍結 file の path は fixture・pin 表・既存テストの参照として現れるだけです。

`output/insights/2026-08-24_paper-story-a2-certification/certification.json` の現物 SHA-256 は引き続き `f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40` であり、凍結成果物への byte 差分はありません。