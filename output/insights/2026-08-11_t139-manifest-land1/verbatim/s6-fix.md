指定された [receipt-schema-v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json) だけを repo 内で編集しました。commit/add/checkout、pytest は実行していません。

## 変更内容

1. `#/definitions/plannedExecution/properties/runs`
   - `minItems: 36` を維持し、`maxItems: 36` を削除。

2. `#/definitions/plannedExecution/{required,properties}`
   - `pilot_cluster_slots` を `consumed_cluster_slots` に改名。
   - 通常形を 1〜13 の整数配列に変更。
   - `#/allOf` に pilot 条件を追加し、`study_stage == "pilot"` では exact `[1,2,3,4,5,6,7,8]` を要求。

3. `#/definitions/effectiveFlags/properties/*`
   - `clocks_per_us`、`epoch_time`、`extime`、`ycsb_zipf_skew`: `number`
   - `thread_num`、`ycsb_max_ope`、`ycsb_rmw`、`ycsb_rratio`、`ycsb_tuple_num`: `integer`

4. `#/definitions/plannedExecution/properties/cluster_slots`
   - `minItems: 156`、`maxItems: 156` を追加。

5. `block_index`
   - `#/definitions/plannedRun/properties/block_index`
   - `#/definitions/actualRun/properties/block_index`
   - `#/definitions/clusterSlot/properties/block_index`
   - すべて 1〜6 に変更。

6. `#/definitions/allocation/properties/binary_rehash`
   - `minItems: 0`、`maxItems: 9`、`uniqueItems: true`。
   - 到達 point 条件を schema から除去。

7. allocation phase
   - `#/definitions/phaseCap/properties/phase`
   - `#/definitions/phaseEvent/properties/phase`
   - 共通定義を文字列型とし、`#/definitions/allocation/allOf` の `if/then/else` で role 別 enum を適用。
   - performance: `preflight, observation, decision, marker, run, teardown`
   - verification: `staging, build, build_post, correctness_run, evidence, teardown`
   - phase 件数・cap 値の制約は削除し semantic 側へ移管。

8. `#/properties/correctness_evidence`
   - `minItems: 0`、`maxItems: 6`。
   - 6 組の `contains` 条件を削除。
   - `#/properties/liveness` から件数・組合せ条件を削除。

9. `#/definitions/correctnessEvidence/properties/outputs`
   - `minItems: 1` を追加。

10. environment observation
    - `#/definitions/environmentObservation/properties/stat_before`
    - `#/definitions/environmentObservation/properties/stat_after`
    - 両方に `minItems: 1`、`maxItems: 8` を追加。

11. `#/definitions/attempt/allOf`
    - completed 性能 attempt: marker 非 null、failure null。
    - completed 検証 attempt: marker null、failure null。
    - pre-performance infra failure: marker null、failure 非 null。
    - post-performance failure: failure 非 null。
    - correctness anomaly: replacement null、failure 非 null。既存の `kind == correctness` も維持。

12. `#/definitions/preregistration/properties/errata`
    - `minItems: 1` と `uniqueItems: true` が残っていることを確認。変更なし。

## 検査結果

JSON parse:

```text
python3 -c "import json;json.load(open('/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json'))"
rc=0
```

Draft-07 schema 検査:

```text
python3 -c "import json,jsonschema;jsonschema.Draft7Validator.check_schema(json.load(open('/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json')))"
rc=0
```

Object schema 閉包検査:

```text
python3 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/check_receipt_object_schemas.py
rc=0
object_schema_count=51
missing_additionalProperties_false=0
missing_required=0
```

正負例の静的検査:

```text
python3 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/check_receipt_schema_examples.py
rc=0
pilot [1..8], runs=288 against root pilot projection + #/definitions/plannedExecution: ACCEPT (expected ACCEPT)
pilot [1..8], runs=36 against root pilot projection + #/definitions/plannedExecution: ACCEPT (expected ACCEPT)
pilot [6..13] against root pilot projection + #/definitions/plannedExecution: REJECT (expected REJECT)
stat_before=9 items against #/definitions/environmentObservation: REJECT (expected REJECT)
outputs=[] against #/definitions/correctnessEvidence: REJECT (expected REJECT)
correctness_anomaly with non-null replaces_attempt_id against #/definitions/attempt: REJECT (expected REJECT)
all_static_cases_passed=6
```

最初の 3 ケースは root の pilot 条件と `#/definitions/plannedExecution` の射影 schema、残りはそれぞれ `environmentObservation`、`correctnessEvidence`、`attempt` 定義を検査しています。

追加の差分検査:

```text
git diff --check -- output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json
rc=0
```

最終 status:

```text
git -C /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1 status --short
rc=0
 M output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md
 M output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json
 M output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md
```

開始時点ですでに `erratum-core-s7-stresscheck-v2.md` と `record-items-v2.md` が変更済みでした。開始時 status との差分として今回 repo 内で増えた変更は `receipt-schema-v1.json` 1 件だけです。既存 2 ファイルには触れていません。

## 要件文書の不整合・semantic 側の責務

文書内に次の不整合があります。指示どおり文書自体は編集していません。

- §7.1 (6) は role 別 phase 切替を draft-07 では表現できないとしていますが、§4.7および今回の指示は `if/then/else` による実装を要求しています。enum 切替だけを schema 化し、件数・cap 値は semantic 側に残しました。
- §7.1 (8) は marker 条件を含む reason-code 分岐全体を表現不能としていますが、今回の指示は表現可能な null/type 条件の実装を要求しています。指定された条件だけを schema 化しました。

semantic validator 側に残した制約は次のとおりです。

1. 種別ごとの exact 件数と組合せ被覆。
2. ordinal の連番性。
3. field 単位・複合 key 単位の一意性。
4. dependency、flags、schedule 値の逐語一致。
5. runs 件数の `36 × |consumed_cluster_slots|` と schedule 表との対応。
6. phase 件数、cap 値、時間予算。
7. binary rehash の `(point, arm)` 一意性と到達条件。
8. actual run 件数、a03 導出、36 run 双射、置換可能性。
9. attempt/allocation role と slot の整合。
10. stat 実列数と malformed reason の再計算。
11. TU path 正規化と base-tree SHA の再導出。
12. argv、compile commands、CMake cache の三者一致。
13. actual argv と計画 argv、run-log flags の照合。
14. pointer の実在、size/hash、単一 snapshot、symlink 拒否。
15. monotonic ordering。
16. intent/marker の create-only 性。
17. a13 台帳の append-only 全履歴検査。
18. phase elapsed と cap の算術検査。
19. schema digest と approval-manifest pin の一致。
20. duplicate JSON key の parser 前段での拒否。

## 総括

変更後の行数: 1326  
object schema の総数: 51  
`additionalProperties: false` を持たない object schema の件数: 0  
直せなかった項目の件数: 0