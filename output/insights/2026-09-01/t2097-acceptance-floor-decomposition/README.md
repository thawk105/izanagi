# [T-2097] 受入 wall の床の分解 — 排他閉包の細分化で取れる量を実測した

authority: none
default_effect: no-state-change

D1035 (ユーザー裁定) が指示した「排他閉包の細分化で受入 wall の床を下げる」を実行するために、
現行の床が何でできているかを実測した記録である。**本 wave は実装を 1 行も入れていない。**
状態の正本は worklog、採用済み判断は decisions とする。

一次資料は `measurements.md` (親が取った生の出力と再現手順)、
`verbatim/` (段 2 プランと段 3 の敵対相談 2 本の逐語) に置く。

## 結論

**排他閉包の細分化で取れるのは、最遅 shard の pytest wall 213.9 秒に対して約 9.5 秒 (4.5%) が上限で、
しかもその 1 手は正しさを弱めるため採れない。**

床は次の 3 つでできており、いずれも排他閉包ではない。

| 成分 | 大きさ (2026-09-01 08:15 の全走、shard-0) | 性質 |
|---|---|---|
| 最長単体 node | 126.13 秒 | 1 個のテストの所要。走ごとに 118.6〜219.3 秒で動く |
| 全 shard 共通の report 外費用 | 約 56.3 秒 | collection・worker 起動・終了処理。排他 group が 1 つも無い shard-2 でも同じ大きさ |
| shard-0 固有の report 外費用 | 約 21.9 秒 (14 走の中央値 20.3 秒、範囲 18.9〜27.9 秒) | **未計測。** lock 待ちか controller prewarm か区別できていない |

## 何が閉じ、何が閉じていないか

**閉じたもの (この artifact で主張してよいこと)**

1. **D1035 が名指した排他鎖はもう存在しない。** D1008 の資源別 reader/writer lock で `real-repo` は
   39 worker へ分散しており、ccbench writer は 4 node・合計 0.19 秒 (うち 3 本は slow 印で
   受入では実走しない)。reader は共有ロックなので相互に待たない。
2. **生きている xdist group の作業単位はどれも最長単体より小さい。** 同一走で
   `s8c-predicate-snapshot` 67.9 秒、`dev-waves-runtime` 15.4 秒、
   `campaign-repository-scan` 0 秒、`s8c-preregistration-candidate` 0 秒。
3. **shard 割付の閉包は file である。** `tools/acceptance_shards.py` の `_components()` が
   file と group の二部グラフを union するため、group を含む file は**その file 全体**が
   1 component になる。実走の最大成分は 23 file・3405 node・4187.6 秒で、
   これは shard-0 の仕事量 5816.6 秒の 72.0% を占める。
   **そのうち `REAL_REPO_ACCESS_BY_NODE` に載るのは 95 node・162.5 秒 (3.9%) だけ**で、
   残りは同じ file に居るというだけで shard-0 に拘束されている。
4. **その拘束を解いても最遅 shard の worker occupancy は下がらない。** node 粒度で 3 shard へ
   完璧に割り直した場合の各 shard の LPT(48 worker) は 126.1 / 122.4 / 118.5 秒で、
   最悪値は現行 shard-0 の理論最適 126.1 秒と一致する。最長単体 node 自身が access map の外に居り、
   どの shard へ移してもその shard の occupancy 下界を 126.1 秒にするためである。
5. **したがって割付・詰め込みで取れるのは、実走の最大 worker occupancy 135.68 秒と
   理論最適 126.13 秒の差 = 9.54 秒だけである。**
6. **床の形は 14 走で再現する。** 各 shard の pytest wall は
   `report 外費用 + 最大 worker occupancy` で分解でき、report 外費用の中央値は
   shard-0 が 77.2 秒、shard-1 が 56.4 秒、shard-2 が 56.6 秒だった。

**閉じていないもの**

1. **shard-0 固有の約 21.9 秒の正体。** 資源 lock の取得は `pytest_runtest_protocol` の wrapper で
   setup report より前に行われ、controller prewarm も test protocol の前に走るため、
   どちらの待ち時間も JUnit にも `report.json` にも現れない。
   「この 21.9 秒は排他待ちではない」とは**実測で言えない**。
2. **最長単体 126.13 秒が今後も床であること。** 14 走で 118.6〜219.3 秒に動いており、固定値ではない。
3. **各 node の所要が割付から独立であること。** 走ごとに shard-0 の総仕事量と最長単体が
   一緒に動くが、これは「その日の機械が遅い」という共通原因でも説明でき、
   負荷を減らせば最長単体が縮むという主張の根拠にはならない。
4. **細分化後の効果量。** B arm を 1 度も走らせていない。

## 採らなかった 1 手と、その理由

段 2 は `test_s8b_floor_campaign.py` の `xdist_group` を持たない 462 node だけを file component から
外す案を出した。**採らない。**

- **その無印 node が実 repo を読んでいる。** 段 3 のレンズ A が file:line で示した
  (同 file の 1588 / 6364 行が実 source を全走査し、2423 / 5075 行が実 calibration・policy・freeze を読む)。
  これらは `REAL_REPO_ACCESS_BY_NODE` の外にあり、`conftest.py` の hook では access が `None` になって
  protocol lock を無取得で通過する。
- **D1008 の lock 保証は同一 host・同一 filesystem までである** と同決定が明記している。
  shard は別 job・別計算ノードで走るので、これらの node を別 shard へ移すと排他が届かなくなる。
  速度のために正しさの射程を縮める変更であり、絶対規律 2 に反する。
- **D1103 の却下理由がそのまま当たる。** 同決定は「排他閉包が今も閉じていない (登録外の実 repo writer と
  collection 窓が残る) ため、閉包が確定していない排他を差し替えない」として同型の案を却下している。
  本 wave のレンズ A は登録外の writer は新たに見つけなかったが、**登録外の reader と、
  shard 間に collection 完了の barrier が無いこと**を確認した。
- **仮に安全でも、効果量 9.54 秒は現行の A/B 設計で判定できない。** 段 2 が置いた
  「走間差 32 秒より小さい差では採らない」という規則では、8〜32 秒の仮説は原理的に採れない。

## 副産物 — access map の外に実 repo を読む node がある

段 3 のレンズ A が、`REAL_REPO_ACCESS_BY_NODE` に載っていないのに実 repo・共有 ccbench を読む経路を
複数の producer で独立に見つけた。

- `orchestrator/tests/test_b10_backoff_shape_sweep.py:1096` — 実 submodule に対して `git archive` を行う。
- `orchestrator/tests/test_s8b_approved.py:34` — 実 gitlink と freeze を読む。
- `orchestrator/tests/conftest.py:576` と `orchestrator/tests/test_sort_swo_oracle.py:206` —
  oracle environment の 25 node が compiler の include root として共有 ccbench を読む。
- `orchestrator/tests/test_mocc_trace_pair.py:121` / `:154` — session fixture が実 production source を読み、
  autouse 経由で同 file の全 node が消費する。

**これは本 wave の scope 外なので直していない。** 閉包を広げる作業は既に見送り台帳の [T-2019] が
持っており、そこへ本 wave の file:line 証拠を追記した。現に走る writer は 1 本・0.19 秒なので
競合窓は小さいが、**小さいことと無いことは別である。**

## 親自身の誤り (段 3 が訂正したもの)

- **(P2) 「残差は排他待ちではない」は棄却された。** 親は「排他 group の無い shard-2 にも残差があるから
  shard-0 の残差も排他待ちではない」と書いたが、これは論理として成立しない。
  shard-0 には全 14 走で 18.9〜27.9 秒の追加分があり、その中身は未計測である。
- **(P3) 「排他閉包の列挙は完全」は棄却された。** shard 配置閉包、`certified_evidence` の
  cross-worker flock (17 node)、controller prewarm の memo cache flock、
  access map 外の実 repo reader が抜けていた。
- **台帳と実走の混用が 1 件あった。** 親は容量の床を台帳合計から `9610.0/(48x3)=66.7 秒` と書いたが、
  同じ走で言うなら `12548.9/(48x3)=87.15 秒` である。台帳の exact-key 被覆は選択 19215 node のうち
  17571 node (91.4%) で、代表例では台帳 55.0 秒の node が実走 126.13 秒 (2.29 倍) だった。
  最長単体が容量の床を上回るという結論自体は変わらない。
- **(P1) は下界の主張としては残るが、「makespan は 1 秒も動かない」は強すぎた。**
  詰め込みの余地が 9.54 秒ある。
