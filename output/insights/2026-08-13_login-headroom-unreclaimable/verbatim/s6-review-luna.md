pytest・mutation は未実走であり、緑とは判定していない。以下は実コードからの静的 KILL 予測である。

## M1〜M7 + P1 判定表

| 変異 | 殺す node | 落ちる assert | 単一理由か | 見かけの kill か |
|---|---|---|---|---|
| M1 | `test_admit_and_reserve_use_unreclaimable_bytes_at_exact_boundary` | `test_login_headroom.py:724`。`reservation[0]`: `LOCAL` 期待に対し `DISPATCH`。`required` は基準 `RESERVE+200`、変異後 `RESERVE+1000`。 | はい | いいえ。前段拒否なし。 |
| M2 | `test_grant_budget_uses_unreclaimable_bytes_for_available` | `test_login_headroom.py:758`。`budget_bytes`: `900` 期待に対し `100`。 | はい | いいえ。`grant_budget` 本体へ到達する。 |
| M3 | `test_calculates_unreclaimable_from_clean_file_and_reclaimable_slab`; `test_snapshot_inconsistency_degrades_conservatively`; `test_admit_and_reserve_use_unreclaimable_bytes_at_exact_boundary`; `test_grant_budget_uses_unreclaimable_bytes_for_available`; `test_dirty_bytes_cross_admission_boundary[clean-file-reclaimable]` | `:323` は `680` 対 `950`; `:392` は `None` 対 `100`; `:719` と `:748` は `100` 対 `900`; `:791` は `LOCAL` 対 `DISPATCH`。 | **いいえ**。算出、snapshot degrade、seam 前提、dirty 正例の5理由へ波及。 | **一部あり**。`:719`、`:748` は seam 呼出前の property assert で落ち、admission seam の検出には帰属できない。 |
| M4 | `test_calculates_unreclaimable_from_clean_file_and_reclaimable_slab`; `test_dirty_bytes_cross_admission_boundary[dirty-unreclaimable]` | `:323` は `680` 対 `580`; `:791` は `DISPATCH` 対 `LOCAL`。 | **いいえ**。算術 oracle と admission 反転の2理由。 | いいえ。dirty 境界 node は本来の分岐まで到達する。 |
| M5 | `test_every_observation_failure_is_none_and_dispatch[stat_missing]` | `test_login_headroom.py:662`。`None` 期待に対し `LoginHeadroom`。 | はい | いいえ。fixture は `anon` を含み、残る値も構文上正常。別要因による観測失敗はない。 |
| M6 | `test_snapshot_inconsistency_degrades_conservatively` | `test_login_headroom.py:392`。`None` 期待に対し `0`。続行すれば `:393` も判定占有量 `100` 対 `0`。 | はい | いいえ。snapshot 不整合分岐を直接通る。 |
| M7 | `test_calculates_unreclaimable_from_clean_file_and_reclaimable_slab` | `test_login_headroom.py:323`。`680` 期待に対し `650`。 | はい。M3 と同じ assert だが、M7 単独では一つの算術差。 | いいえ。 |
| P1 | `test_admit_and_reserve_use_unreclaimable_bytes_at_exact_boundary`; `test_grant_budget_uses_unreclaimable_bytes_for_available` | 正例は実在。`:724`、`:727` が `LOCAL`、`:757` が `LOCAL`、`:758` が予算 `900` を固定。 | はい。2 seam は別 node。 | いいえ。未登録ではない。 |

## 所見

### 1. M3 の自己申告は完全集合でなく、単一帰属も成立しない

- 深刻度: **高・must-fix**
- file:line: `plan-v2.md:118`、`author-out.md:55`、`orchestrator/tests/test_login_headroom.py:323,392,719,748,791`
- 再現条件: `reclaimable = slab` にすると、算出 node だけでなく snapshot node、2 seam node の前提 assert、dirty 正例も落ちる。特に seam 2 node は実装分岐へ到達する前に赤になる。
- 判定: M3 と M7 が共有する `:323` 自体は、それぞれ `950` と `650` という一つの値差なので単独では過剰決定ではない。しかし M3 全体は5 node・複数理由であり、自己申告の単一 node 帰属は誤り。
- 修正要求: DW-M08 の期待 node を完全集合へ直し、`:719`/`:748` は巻き添えと明記する。単一理由を維持するなら seam fixture を clean file ではなく slab で差を作るなどして分離する必要がある。
- 成果物影響: このままでは mutation ledger の期待完全集合照合が不一致となり、M3 の検出力を証明できないため、certified 選択の proof chain を閉じられない。

### 2. M4 の境界は正しく反転するが、自己申告から算出 node が漏れている

- 深刻度: **高・must-fix**
- file:line: `plan-v2.md:119`、`author-out.md:56`、`orchestrator/tests/test_login_headroom.py:311-323,766-791`
- 再現条件: dirty case は基準式で `clean=75424`、`unreclaimable=24576`、`required=RESERVE+24577 > ceiling=RESERVE+24576` なので `DISPATCH`。M4 では `clean=100000`、`unreclaimable=0`、`required=RESERVE+1` となり `LOCAL`。境界は1 byte確実にまたぐ。
- 追加赤: 算出 vector でも M4 により `clean=270→370`、`reclaimable=320→420`、`unreclaimable=680→580` となり `:323` が落ちる。
- 修正要求: mutation matrix の期待完全集合を2 nodeへ訂正し、dirty nodeを本来の検出、算出 nodeを冗長 gateとして区別する。
- 成果物影響: 現行の単一 node 登録では実走時の余分な失敗 node により M4 を KILLED と認定できず、変異台帳とレポートが不一致になる。

### 3. 既定 fixture は実機と異なり clean file が常に0になる

- 深刻度: **nit**
- file:line: `orchestrator/tests/test_login_headroom.py:34-48,90-119`
- 再現条件: `_memory_stat()` は `max(0,202-303-404-505)=0`、`_observation()` は `max(0,2-3-4-5)=0`。一方、実機の対になった読取りでは `current=13,537,415,168→13,537,923,072`、`file=3,679,072,256`、`shmem=466,944`、`dirty=462,848`、`writeback=0`、`unevictable=4,472,832`、`slab_reclaimable=1,469,858,664` で、`clean_file=3,673,669,632` と明確に正。
- 評価: 専用算出 node と admission seam は正の clean file を明示しているため、登録変異の検出自体は失われていない。実機の dirty は直前の別読取りでは `1,220,608` でもあり、揮発している。
- 成果物影響: 現行成果物値は変わらないが、今後 default helper だけで追加された consumer test は clean-file 回帰を検出できない。

### 4. M1 の「判定が緩み」は方向が逆

- 深刻度: **nit**
- file:line: `plan-v2.md:116`
- 再現条件: `admission_bytes=100` を raw current `900` へ戻すと必要量が増え、`LOCAL→DISPATCH` となるため、これは過剰拒否側への厳格化。
- 成果物影響: certified 選択値は変わらないが、レポートに変異方向を逆向きで記録する。

## 併合判定

- テスト弱体化: 既存 assert の削除、期待値反転、skip、xfail はない。既存 dataclass 期待値へ新 field が追加され、peak 診断 assert が2本追加されている。
- 揮発値の焼き込み: なし。`24576` は実機値のコピーではなく境界 fixture であり、実機 current、dirty、hash は期待値に入っていない。
- seam 独立性: 満たす。`admit`/`reserve` は `:705`、`grant_budget` は `:734` の別 node。
- M5: genuine kill。`_stat_missing` は縮小後 required の `anon` を含み、optional 欠落は base への degrade となるため、別要因による先行拒否はない。
- 静的検査のみ実施。pytest、collection、mutation harness は実走しておらず、緑の申告はない。

## 総括

- M1、M2、M5、M6、M7 は登録どおり静的に KILL 見込みで、P1 も実在する。
- M4 は境界を確実にまたぐため SURVIVE しないが、実際は2 nodeを落とす。
- M3 も SURVIVE しないが、5 nodeへ波及し、うち2 nodeは seam 前の見かけの kill。
- must-fix は M3・M4 の期待失敗 node 完全集合と、本来検出／巻き添え帰属の訂正。