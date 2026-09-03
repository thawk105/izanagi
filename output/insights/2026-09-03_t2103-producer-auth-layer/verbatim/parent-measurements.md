# 親の実測記録 (T-2103)

すべて wave base commit `4ec3eba04354f9ba86117a2dd488c72d007045e6` の checkout で測った。

## M1. producer の現行 bytes

```
sha256sum orchestrator/campaign/p3_b4_raw_record_producer.py
55e264f05eef48e466a1ab20c97d9a7d30acba0afe3e76937e58411e17b1c790
```

段 2 plan が静的に読み取った値と一致する。

## M2. T-2049 の変異 matrix 18/18 KILLED は成果物 field で確認できる

`output/insights/2026-08-29_t2049-b4-raw-record-producer/mutation-registered-report.json` の
`summary` field:

```
{"KILLED": 18, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0,
 "completed": 18, "matching": 18, "recorded": 18, "registered": 18}
```

同 report の `repo_head` は `c576b6e8108017f49f34f96e9cb4057fa1291032`、`date` は
`2026-08-29T07:38:22Z`。

**束縛の範囲:** producer 本体の blob は当時と現 HEAD で同一である。

```
git rev-parse c576b6e81:orchestrator/campaign/p3_b4_raw_record_producer.py -> 9d3864ca01e09871f18755aa464f0ae51aa95630
git rev-parse HEAD:orchestrator/campaign/p3_b4_raw_record_producer.py       -> 9d3864ca01e09871f18755aa464f0ae51aa95630
```

一方 test 側の blob は変わっている。

```
git rev-parse c576b6e81:orchestrator/tests/test_p3_b4_raw_record_producer.py -> 3fab44773476bfe2061e0e2b6f777d0b8cb99877
git rev-parse HEAD:orchestrator/tests/test_p3_b4_raw_record_producer.py     -> 29e3978cdb80b18e23e8f9670e331480d6b7f254
```

したがって「現行 producer bytes に対し、当時の test 版が 18/18 を殺した」と書く。
現行 test 版での再走は本 wave では行わない (M01-M18 は比較の分子ではない)。

## M3. closure receipt は verdict 経路へ配線されていない

段 2 plan の指摘は正しい。`generate_verified_analysis_source_closure_receipt` の
呼び手は test だけである。

```
git grep -n "generate_verified_analysis_source_closure_receipt" -- '*.py'
orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1092  (定義)
orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1113  (__all__)
orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py:17,109  (test のみ)
```

`p3_b4_material_report.py:224` の `evaluate_b4_artifacts` 呼び出しは receipt を渡さない
(`floor` / `contract_binding` / `scheduled_registry_bytes` / `analysis_manifest_bytes` /
`raw_analysis_records_bytes` / `source_artifact_bytes` の 6 引数のみ)。

**含意:** frozen consumer 候補は「closure tuple に producer path を足す」だけでは成立せず、
receipt を verdict 経路へ配線する変更を伴う。変更閉包の事前見積り (production file 3) は
この配線を含めて数え直す必要がある。
