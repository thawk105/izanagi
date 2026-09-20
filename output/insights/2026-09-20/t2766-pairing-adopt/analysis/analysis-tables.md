## T-2766 A/B analysis

逐次の隣接対比較。別 job/allocation 間の比較である。
F = W - O は同じ shard の残差。固定費とは実証していない。
中央値率 10% は本 wave 独自の保守基準。3/3 は有意差判定ではない。
worker item 列は JUnit 出現順。全 worker の2個目を保証しない。
各 arm の許容 tip 集合・tested tip と終了後 HEAD の一致・clean を照合する。

## 走表

| ID | 条件 | tip | tested_main | other_leaders | load1 | 投入 / 完了 | W_max | argmax | rc | session_dir_origin (参照しない) | 有効 / 理由 | 対の採否 / 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01-A | A | a465c29c201e4a7d008c32d1294365e4c20d9d3c | 4726b649390a71555e0f189e9cfed0746ca2d4f7 | 1 | 19.71 | 2026-09-20T14:47:42+0900 / 2026-09-20T15:11:33+0900 | 500.96 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/c42607982511e6313d3374e19fafaf50 | valid | valid |
| 02-B | B | a4c30d6c6333ccc622b4f7c479d7bb9eb32588aa | 4fe49200e11726e27defbeae843e72cf79ffdab3 | 0 | 8.16 | 2026-09-20T15:14:17+0900 / 2026-09-20T15:23:37+0900 | 355.134 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/8e174826650e3e19a94c2812533b9126 | valid | valid |
| 03-B | B | 8cdd7bf54e821cfb9cef10303215da3b790e76eb | c6bacf505e43e611a49d105b09f62dfe2af9427c | 1 | 4.28 | 2026-09-20T15:44:02+0900 / 2026-09-20T16:07:25+0900 | 353.767 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/29a2409306864e1f1f5064b78615b19b | valid | valid |
| 04-A | A | 5fb5a37f13237ace6334cd47e9cb7b8111fc47b8 | 182cdb8d625b440726b5bfde5cddc741ddb237a1 | 1 | 3.34 | 2026-09-20T17:09:47+0900 / 2026-09-20T17:35:29+0900 | 440.036 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/cacaef3fbf01f0c00267df1eb03fb876 | valid | valid |
| 05-A | A | 94368ff7539d863bdcb7b8dea540f65a18981cd3 | 82d7206d60cd0ca12a9be7a363ae01475343943a | 0 | 5.72 | 2026-09-20T17:43:37+0900 / 2026-09-20T17:54:41+0900 | 455.936 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/1f7e0511623cb9761f0122e1ce60fe0a | valid | valid |
| 06-B | B | cfb217cdb9b3eb9ddf6ce521cfac041ac5effc67 | fec4a818741e5464fffcd11e4b094c125dfe5280 | 0 | 3.66 | 2026-09-20T17:57:13+0900 / 2026-09-20T18:10:52+0900 | 398.629 | [0] | 0 | /work/1/SFC/tanab/.izanagi-acceptance-shards/fd6825ad8c2922d12c36623a52bdc211 | valid | valid |

## Shard / witness

| 走 | shard | W | O | F (残差) | 最忙 worker / items / duration | witness | partner cost |
|---|---|---|---|---|---|---|---|
| 01-A | 0 | 500.96 | 428.609002431 | 72.35099756899996 | {'id': 'gw0', 'duration_s': 428.609002431, 'items': 73} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 01-A | 1 | 276.483 | 199.485592108 | 76.99740789200001 | {'id': 'gw3', 'duration_s': 199.485592108, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 01-A | 2 | 214.54 | 144.821694898 | 69.71830510199999 | {'id': 'gw1', 'duration_s': 144.821694898, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 02-B | 0 | 355.134 | 277.814883026 | 77.319116974 | {'id': 'gw32', 'duration_s': 277.814883026, 'items': 142} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 02-B | 1 | 265.659 | 174.93892912 | 90.72007087999998 | {'id': 'gw0', 'duration_s': 174.93892912, 'items': 50} | True | {'count': 48, 'min': 0.001, 'max': 0.001, 'zero_count': 0} |
| 02-B | 2 | 249.472 | 158.315640774 | 91.156359226 | {'id': 'gw2', 'duration_s': 158.315640774, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 7} |
| 03-B | 0 | 353.767 | 283.065288754 | 70.701711246 | {'id': 'gw47', 'duration_s': 283.065288754, 'items': 8} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 03-B | 1 | 245.048 | 180.318399195 | 64.72960080499999 | {'id': 'gw0', 'duration_s': 180.318399195, 'items': 50} | True | {'count': 48, 'min': 0.001, 'max': 0.001, 'zero_count': 0} |
| 03-B | 2 | 203.872 | 139.852960114 | 64.019039886 | {'id': 'gw2', 'duration_s': 139.852960114, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 7} |
| 04-A | 0 | 440.036 | 369.506144843 | 70.52985515699999 | {'id': 'gw36', 'duration_s': 369.506144843, 'items': 76} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 04-A | 1 | 247.06 | 181.384363427 | 65.67563657299999 | {'id': 'gw0', 'duration_s': 181.384363427, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 04-A | 2 | 165.566 | 100.782230595 | 64.783769405 | {'id': 'gw1', 'duration_s': 100.782230595, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 05-A | 0 | 455.936 | 384.521886675 | 71.41411332499996 | {'id': 'gw47', 'duration_s': 384.521886675, 'items': 25} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 05-A | 1 | 241.995 | 177.378426998 | 64.616573002 | {'id': 'gw0', 'duration_s': 177.378426998, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 05-A | 2 | 165.282 | 100.981184567 | 64.30081543300001 | {'id': 'gw1', 'duration_s': 100.981184567, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |
| 06-B | 0 | 398.629 | 327.285192007 | 71.34380799300004 | {'id': 'gw46', 'duration_s': 327.285192007, 'items': 12} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 29} |
| 06-B | 1 | 245.603 | 179.976077227 | 65.62692277300002 | {'id': 'gw0', 'duration_s': 179.976077227, 'items': 50} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 5} |
| 06-B | 2 | 172.226 | 105.772088869 | 66.453911131 | {'id': 'gw2', 'duration_s': 105.772088869, 'items': 2} | True | {'count': 48, 'min': 0.0, 'max': 0.001, 'zero_count': 2} |

## 対表

| 対 | 期待 slot / 順序 | 走順 | 有効 / 理由 | ΔW | r | D357 | main_moved | tips / tested_main |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 / ['A', 'B'] | ['01-A', '02-B'] | valid | 145.82599999999996 | 0.2910931012456084 | \|r\| >= 10% | True | [{'run': '01-A', 'tip_sha': 'a465c29c201e4a7d008c32d1294365e4c20d9d3c', 'tested_main': '4726b649390a71555e0f189e9cfed0746ca2d4f7'}, {'run': '02-B', 'tip_sha': 'a4c30d6c6333ccc622b4f7c479d7bb9eb32588aa', 'tested_main': '4fe49200e11726e27defbeae843e72cf79ffdab3'}] |
| 2 | 2 / ['B', 'A'] | ['03-B', '04-A'] | valid | 86.269 | 0.19604986864711071 | \|r\| >= 10% | True | [{'run': '03-B', 'tip_sha': '8cdd7bf54e821cfb9cef10303215da3b790e76eb', 'tested_main': 'c6bacf505e43e611a49d105b09f62dfe2af9427c'}, {'run': '04-A', 'tip_sha': '5fb5a37f13237ace6334cd47e9cb7b8111fc47b8', 'tested_main': '182cdb8d625b440726b5bfde5cddc741ddb237a1'}] |
| 3 | 3 / ['A', 'B'] | ['05-A', '06-B'] | valid | 57.30699999999996 | 0.12569088644020204 | \|r\| >= 10% | True | [{'run': '05-A', 'tip_sha': '94368ff7539d863bdcb7b8dea540f65a18981cd3', 'tested_main': '82d7206d60cd0ca12a9be7a363ae01475343943a'}, {'run': '06-B', 'tip_sha': 'cfb217cdb9b3eb9ddf6ce521cfac041ac5effc67', 'tested_main': 'fec4a818741e5464fffcd11e4b094c125dfe5280'}] |

## 中央値と事前登録判定

```json
{
  "class": "i",
  "label": "方向一致・閾値以上",
  "verdict": "land",
  "subclasses": [],
  "valid_pairs": 3,
  "medians": {
    "paired_delta_W": 86.269,
    "paired_r": 0.19604986864711071,
    "condition_W_difference": 100.80199999999996
  }
}
```
