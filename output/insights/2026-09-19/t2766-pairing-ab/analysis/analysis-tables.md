## T-2766 A/B analysis

逐次の隣接対比較。別 job/allocation 間の比較である。
F = W - O は同じ shard の残差。固定費とは実証していない。
中央値率 10% は本 wave 独自の保守基準。3/3 は有意差判定ではない。
worker item 列は JUnit 出現順。全 worker の2個目を保証しない。
測定 tip は必須 CLI 引数で固定し、前後 SHA と clean を照合する。

## 走表

| ID | 条件 | tip | 投入 / 完了 | W_max | argmax | rc | session_dir_origin (参照しない) | 有効 / 理由 | 対の採否 / 理由 |
|---|---|---|---|---|---|---|---|---|---|
| 01-A | A | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T02:03:24+0900 / 2026-09-20T02:08:24+0900 | None | [] | 16 | /work/1/SFC/tanab/.izanagi-acceptance-shards/bf4b7a4c04956c1390eed7400953e76e | ['run rc != 0', 'copy_ok is not true', "session_dir must be relative path 'session'", 'shard-0: invalid copied session path', 'shard-1: invalid copied session path', 'shard-2: invalid copied session path', 'missing/nonpositive W_max'] | ['invalid run in pair'] |
| 02-B | B | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T02:11:16+0900 / 2026-09-20T02:18:10+0900 | 362.281 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/1fd875bff48001ea1fffd871fb4e6553 | valid | ['invalid run in pair'] |
| 03-A | A | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T03:04:47+0900 / 2026-09-20T03:13:10+0900 | 454.716 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/76a850a65ac3e8aa358edd87e19d1654 | valid | valid |
| 04-B | B | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T03:15:17+0900 / 2026-09-20T03:36:02+0900 | 353.01 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/613639689b85c5feea811b96bd4b1af9 | valid | valid |
| 05-B | B | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T03:38:32+0900 / 2026-09-20T03:50:58+0900 | 352.669 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/697b220bca6d0702267d627d1f45a0c5 | valid | valid |
| 06-A | A | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T03:53:27+0900 / 2026-09-20T04:17:33+0900 | 465.54 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/00bfe11a4834fe75ae6cc7be09eb97ab | valid | valid |
| 07-A | A | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T04:20:10+0900 / 2026-09-20T04:45:18+0900 | 480.574 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/0025e566ccbc528ed8a46c6416760ef4 | valid | valid |
| 08-B | B | 0eabe67bad429403a2eadfddcac4c1252d55dda3 | 2026-09-20T04:48:01+0900 / 2026-09-20T05:10:53+0900 | 336.25 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/7f6380e032f66f8530dd9c79a0ec6aea | valid | valid |

## Shard / witness

| 走 | shard | W | O | F (残差) | 最忙 worker / items / duration | witness | partner cost |
|---|---|---|---|---|---|---|---|
| 01-A | 0 | None | None | None | None | False | None |
| 01-A | 1 | None | None | None | None | False | None |
| 01-A | 2 | None | None | None | None | False | None |
| 02-B | 0 | 362.281 | 292.021836957 | 70.259163043 | {'id': 'gw35', 'duration_s': 292.021836957, 'items': 4} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 02-B | 1 | 258.847 | 195.933701018 | 62.913298981999986 | {'id': 'gw2', 'duration_s': 195.933701018, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 02-B | 2 | 205.937 | 141.271068899 | 64.66593110100001 | {'id': 'gw31', 'duration_s': 141.271068899, 'items': 125} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 03-A | 0 | 454.716 | 385.576948805 | 69.13905119500004 | {'id': 'gw46', 'duration_s': 385.576948805, 'items': 34} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 03-A | 1 | 232.251 | 168.815858629 | 63.435141371000014 | {'id': 'gw0', 'duration_s': 168.815858629, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 03-A | 2 | 173.024 | 107.624602505 | 65.399397495 | {'id': 'gw23', 'duration_s': 107.624602505, 'items': 130} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 04-B | 0 | 353.01 | 282.988270874 | 70.02172912599997 | {'id': 'gw40', 'duration_s': 282.988270874, 'items': 15} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 04-B | 1 | 230.621 | 167.174540565 | 63.44645943500001 | {'id': 'gw0', 'duration_s': 167.174540565, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 04-B | 2 | 174.426 | 108.318666741 | 66.10733325899999 | {'id': 'gw39', 'duration_s': 108.318666741, 'items': 146} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 05-B | 0 | 352.669 | 282.314029063 | 70.35497093699996 | {'id': 'gw40', 'duration_s': 282.314029063, 'items': 68} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 05-B | 1 | 231.829 | 169.097084671 | 62.731915329 | {'id': 'gw0', 'duration_s': 169.097084671, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 05-B | 2 | 171.746 | 106.569620345 | 65.176379655 | {'id': 'gw33', 'duration_s': 106.569620345, 'items': 139} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 06-A | 0 | 465.54 | 395.867514041 | 69.67248595900003 | {'id': 'gw1', 'duration_s': 395.867514041, 'items': 13} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 06-A | 1 | 233.172 | 169.620790485 | 63.55120951500001 | {'id': 'gw0', 'duration_s': 169.620790485, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 06-A | 2 | 171.044 | 105.68621035 | 65.35778965000002 | {'id': 'gw26', 'duration_s': 105.68621035, 'items': 159} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 07-A | 0 | 480.574 | 410.779587619 | 69.79441238100003 | {'id': 'gw1', 'duration_s': 410.779587619, 'items': 24} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 07-A | 1 | 233.817 | 170.078666999 | 63.738333001 | {'id': 'gw0', 'duration_s': 170.078666999, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 07-A | 2 | 170.415 | 106.575363411 | 63.839636588999994 | {'id': 'gw9', 'duration_s': 106.575363411, 'items': 134} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 08-B | 0 | 336.25 | 265.910588679 | 70.339411321 | {'id': 'gw14', 'duration_s': 265.910588679, 'items': 116} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 08-B | 1 | 232.475 | 169.287072965 | 63.187927035 | {'id': 'gw0', 'duration_s': 169.287072965, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 08-B | 2 | 171.382 | 105.200967748 | 66.18103225200001 | {'id': 'gw4', 'duration_s': 105.200967748, 'items': 135} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |

## 対表

| 対 | 期待 slot / 順序 | 走順 | 有効 / 理由 | ΔW | r | D357 |
|---|---|---|---|---|---|---|
| 1 | 1 / ['A', 'B'] | ['01-A', '02-B'] | ['invalid run in pair'] | None | None | None |
| 2 | 1 / ['A', 'B'] | ['03-A', '04-B'] | valid | 101.70600000000002 | 0.22366927928641178 | \|r\| >= 10% |
| 3 | 2 / ['B', 'A'] | ['05-B', '06-A'] | valid | 112.87100000000004 | 0.24245177643167082 | \|r\| >= 10% |
| 4 | 3 / ['A', 'B'] | ['07-A', '08-B'] | valid | 144.324 | 0.3003158722694112 | \|r\| >= 10% |

## 中央値と事前登録判定

```json
{
  "class": "i",
  "label": "方向一致・閾値以上",
  "subclasses": [],
  "valid_pairs": 3,
  "medians": {
    "paired_delta_W": 112.87100000000004,
    "paired_r": 0.24245177643167082,
    "condition_W_difference": 112.87100000000004
  }
}
```
