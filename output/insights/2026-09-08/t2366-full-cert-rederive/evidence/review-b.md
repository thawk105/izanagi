## 所見

1. **主張:** full 側は、再読した acquisition が本当に full の receipt chain かを確認していない。partial 側には canonical evidence の `acquisition_schema` / `completion_schema` 検査があるが、full 側は再読前の可変な `evidence` だけを検査している。具体的には、有効な partial evidence を複製し、渡す側だけ `acquisition_schema=ACQUISITION_SCHEMA`、`completion_schema=COMPLETION_SCHEMA`、`raw_manifest_valid=False`、`raw_manifest_schema=None` と偽装する。その partial evidence から `_canonical_full_report` で作った indeterminate report は既存検査を通り、再読後も同じ report が導出されるため受理される。

   **file:line:** `orchestrator/campaign/paper_story_a2_certification.py:4390`（partial の canonical chain 検査）、`:4469`（full は渡された evidence のみ検査）、`:4531`（再読後に同検査なし）、`:4567`（返された partial evidence の receipt bytes を成果物化）。既存 cross-chain test は `orchestrator/tests/test_paper_story_a2_certification.py:2950` だが、schema field を偽装しない入力だけを扱う。

   **成果物への影響:** intended contraction が一部成立せず、full v4 の indeterminate `certification.json` と partial acquisition/completion receipts を同居させた certified 成果物が、`materialize` 直接呼出しで生成できる。旧実装から受理集合が広がるのではなく、本変更が閉じるはずの受理集合が閉じ切らない。

   **提案する対処:** 再読直後に partial 側と同型の full acquisition/completion schema 検査を置く。既存 `test_materializer_rejects_v3_v4_result_receipt_cross_chain` に上記の forged wrapper ケースを追加すれば、新規 node や台帳項目を増やさず帰属を固定できる。partial の raw-manifest schema-chain 全拒否まで写すのは、full の manifest 無効を indeterminate にする裁定と衝突するため提案しない。

   **自己判定:** real

2. **主張:** M04 の裁定上の old 逐語 `report == expected` は一意でない。partial と full に一箇所ずつ存在する。ただし full 側の代入文全体を old にすれば一意になり、交換は現行の exact-dict report domain で等価である。

   **file:line:** `orchestrator/campaign/paper_story_a2_certification.py:4431`、`:4537`。裁定の短縮表現は `ruling.md:51`。

   **成果物への影響:** 等価交換なので certified 成果物・受理集合は変わらない。一方、裸の式を mutation old にすると、full 比較を変異したという証拠が partial 側との間で一意に帰属しない。

   **提案する対処:** DW-M07 の最終 old を、下記の代入文全体に固定する。実装コードの変更は不要。

   **自己判定:** real

## 変異の逐語 old と期待 node

M01-rederive-removed — old は一箇所だけで、partial 側との重複なし。

```python
        expected = _canonical_full_report(
            policy, canonical_full_evidence,
            attempt_id=canonical_full_evidence["attempt_id"],
            current_pin=report["current_pin"])
```

期待 node の完全集合:

- `test_full_materializer_rejects_forged_status_from_positive_evidence`
- `test_full_materializer_rejects_forged_effects_from_positive_evidence`
- `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition`

M02-reread-removed — old は一箇所だけで、partial 側との重複なし。

```python
        canonical_full_evidence = validate_acquisition_bundle(
            policy, acquisition_path, current_pin=report["current_pin"])
```

期待 node の完全集合:

- `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition`

これだけである。status/effects 負例は未改竄の evidence から再導出するため引き続き拒否される。既存 full 正例は渡された evidence 自体が canonical なので変化しない。

M03-always-reject — old は一箇所だけで、partial 側との重複なし。

```python
        if not full_report_matches_rederived_evidence:
```

期待 node の完全集合（現物の node 名）:

- `test_p2_a6_full_v3_path_collects_and_materializes`
- `test_synthetic_pbs_free_preregister_through_analyze_positive`
- `test_m11_materializer_stages_marker_before_single_noreplace_rename`
- `test_materialize_einval_uses_exclusive_claim_and_flags_zero_rename`
- `test_materialize_einval_refuses_destination_created_before_recheck`
- `test_materialize_einval_fails_closed_on_publish_claim_collision`
- `test_materialize_non_einval_publish_error_does_not_enter_fallback`
- `test_materialize_noreplace_success_does_not_enter_fallback`

M04-equivalent-swap — 裁定の裸の式は二箇所にあるため、最終 old は次の一意な代入文全体にする必要がある。

```python
        full_report_matches_rederived_evidence = report == expected
```

期待 node の完全集合: 空。`expected == report` への交換は等価で SURVIVED が正しい。

## 破れなかった箇所

- `_canonical_full_report` は authority gate、driver failure、manifest failure、`collect_results`、例外 tuple、`source_commit` 付与まで旧 full collector 分岐を忠実に移している。余計な正規化・分岐はない。
- full にだけ残る structural / identity / schema / request-ID 正規化 / fixed-field / cells / historical 検査は partial への射影にはない「余計な検査」だが、裁定が渡された evidence に対して据え置くよう明示した既存検査である。再読位置もその全検査後で、legacy v3 の `return evidence` は維持されている。
- 新規3負例は単一理由性を満たす。偽 status は許容 vocabulary、偽 effect は finite float、indeterminate は forged evidence と identity・shape が整合するため、いずれも既存検査を抜けて再導出差だけで拒否される。
- 変更前相当では3件とも `materialize` が publish まで到達する。したがって実装子の「再導出条件だけを無効化すると DID NOT RAISE」という probe は妥当であり、`pytest.raises` の終了時点で失敗するため後続の成果物不存在 assert が未実行でも materialization 成功を示す。
- 既存 test の変更は `test_p2_a6_full_v3_path_collects_and_materializes` の canonicalizer 同一性 assert だけで裁定内。synthetic 正例の構築は差分上変更されておらず、実装子報告と一致する。
- 新規 node はすべて `test_` 命名で、同ファイルの `_run()` → `pytest.main([__file__, "-q"])`（test file `:5376`）に自動包含される。実装子が挙げた allowlist/self-runnable meta-test は file 単位である。
- acceptance duration ledger の3 node 登録は未了だが、裁定どおり親の段7作業であり実装子報告もそのように記している。報告された `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` の成功は個別3 node の登録証拠にはならない。meta-test 定義と台帳現物は射影外なので未読である。
- 実走 rc の主張は静的レビューでは再検証していないが、実装子の完了報告と指定差分・現物の間に、それ以外の食い違いは見つからなかった。

## 総括

full report の再導出、検査順、新規3負例、M01〜M03 の kill set は裁定どおりである。  
ただし、再読後の full receipt-family 確認が欠け、full result と partial receipts の cross-chain 受理が残る。  
M04 は等価だが、裸の old 逐語は partial と重複するため代入文全体への固定が必要である。  
実装・test 実行・編集は行っていない。