## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| レビューA 所見6 | `partial` | `tools/codex_reasoning_ab.py:6855-6859` は `grouped` が空の場合 בלבדを拒否する。`len(grouped) == 10` などの非ゼロslot数検査はない。新規テスト `orchestrator/tests/test_codex_reasoning_ab.py:7767-7780` も空manifestだけを検証している。 |
| レビューA 所見7 | `closed` | `tools/codex_reasoning_ab.py:5146-5150` の `_legacy_schedule_view` を `_validate_schedule` と `make_packets` が共有し、`make_packets` では `:6860-6875` で検証前に補完する。schema_versionなしを検証するテストは `orchestrator/tests/test_codex_reasoning_ab.py:7783-7833`。 |
| レビューA 所見8 | `closed` | `tools/codex_reasoning_ab.py:5636-5650` の共通条件を、token observation (`:5757-5758`) と aggregate (`:5925`) が使用する。複数modelで `by_arm_case` を出さないテストも `orchestrator/tests/test_codex_reasoning_ab.py:6981-6992` にある。 |
| レビューB 所見B-1 | `partial` | A6と同じく、空slot経路は拒否するが、1、9、11など任意の非ゼロslot数は拒否しない。該当差分は `tools/codex_reasoning_ab.py:6855-6859`。 |

## 新規regression所見

なし。

`_legacy_schedule_view` は従来の `dict(schedule)` と `setdefault` をそのまま抽出しており、非破壊性も維持している。`_is_legacy_projection` も従来のaggregate側条件と同値である。

新しい空manifest検査はslot grouping後、かつ `schedule_descriptor is None` の場合だけ発火するため、scheduleなし・`grouped`非空の既存経路は壊していない。既存の10 slotテストは `orchestrator/tests/test_codex_reasoning_ab.py:7602-7624` にある。

## 総括

fix2とfix3は所見を閉じている。  
fix1は空のlegacy packet経路だけを閉じた。  
非ゼロslotのcardinality欠陥は未解決で、A6/B-1はpartialである。  
helper抽出による別の挙動変更は確認できない。  
指定された新規テストの内容は読んだが、実行はしていない。