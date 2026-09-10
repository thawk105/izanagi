# [T-2097] 受入 1 shard の残差 約 58 秒の内訳 — ほぼ全量が「テストを走らせなくても払う起動費用」

authority: none
default_effect: no-state-change

D1384 (ユーザー裁定) が「次に調べるのは全 shard 共通の report 外費用 (約 56 秒、wall の 26%)」と
定めたのを受け、その量を測点付きで分解した記録である。**本 wave は実装を 1 行も入れていない。**
状態の正本は worklog、採用済み判断は decisions とする。

一次資料は `measurements.md` (親が取った生の値と再現手順)、`verbatim/` (段 2 プラン、段 3 の
敵対相談 2 本、段 4 裁定、probe 逐語)。

## 呼称と定義 (D1298 / F755 に従い「固定費」と呼ばない)

測った量は **`残差 = pytest wall − その走の実測最大 worker report duration 合計`** である。
これは上界であって原因別の費用ではない。worker の idle、lock 待ち、scheduler、session の前後が
混ざりうる (D1298)。したがって内訳は**最繁 worker w* から見た wall 露出区間**として書く。

```
残差 = A + B + D + C
A = session 開始 → w* の最初の report 開始
B = (w* の最後の report 終了 − 最初の report 開始) − w* の report 合計
D = 全 worker の最後の report 終了 − w* の最後の report 終了
C = 全 worker の最後の report 終了 → terminal が wall を測る時点
```

前 wave の親は 3 項 (A / B / C) で足りると考えたが、段 2 の codex がこれを**否定した**。
最繁 worker が最後に終わるとは限らないため D が抜ける。実測では D = 0.000 秒だった。

## 結論

**残差のほぼ全量 (58.16 秒中 55.21 秒、95%) は A である。そして A の大半は
「48 個の worker が各自で全テストを collection する」時間である。**

| 区間 | R2-B1 (shard-2) | R1-B1 (shard-1) |
|---|---:|---:|
| A | 55.209 秒 | 相当区間 55.1 秒級 |
| B | 0.035 秒 | 同程度 |
| D | 0.000 秒 | 0.000 秒 |
| C | 2.913 秒 | 同程度 |
| 残差 合計 | 58.156 秒 | 57.939 秒 |

A の内訳 (controller の event 時刻。session 開始を 0 とする)

| 到達点 | shard-2 (R2-B1 / R2-B2) | shard-1 (R1-B1 / R1-B2) |
|---|---:|---:|
| 48 worker の gateway 生成完了 | 3.13 / 3.17 秒 | 3.17 / 3.23 秒 |
| 48 worker の ready 完了 | 3.47 / 3.59 秒 | 3.53 / 3.70 秒 |
| 48 worker の collection 完了 (最初〜最後) | 51.01〜55.18 / 50.55〜55.52 秒 | 50.23〜55.09 / 51.00〜55.31 秒 |

**worker 起動は約 3.2 秒、collection は約 51.7 秒**である。C (終端) は約 2.9 秒で、その内訳は
最後の report から worker 終了通知まで 0.22 秒、そこから wall 終点まで 2.69 秒だった。

## 独立の裏づけ — テスト 0 件の較正走

production の shard plugin に全 collection と割付を行わせた後で実行 item を空にした走 (Z-S1) の
pytest wall は **55.73 秒**だった (選択 6524 / 完走 0 / universe 19572)。
テストを 1 件も走らせない走が 55.73 秒かかるという事実が、A をほぼ独立に裏づける。

**この走は受入判定ではない。** 較正 (`instrumented zero-selected calibration`) であり、
受入の gate・selection・排他・判定はいっさい変更していない。

## D711 との比較 — 同型の量が 4.3 倍になっている

D711 (2026-08-23) は同型の測定を **12.86 秒 (48 worker 起動 + 全 collection + 集約、テスト 0 件)**
と記録し、その小ささを根拠に「全 collection を K 回払っても費用はほぼ増えない」と結論した。
今回の同型の値は **55.73 秒**である。

- collection 対象は 14479 node から 19572 node へ **1.35 倍**。
- 費用は 12.86 秒から 55.73 秒へ **4.33 倍**。

**node 数だけでは説明できない。** 本 wave はこの差の原因を分解していない。
測点は「controller が 48 本の collection 完了通知を受け取る時刻」までで、
worker 内部の import・conftest・fixture 収集・deselect の別は測っていない。

D634 は「collection 固定費の削減手段 (controller-only / manifest 共有) はいずれも採用しない」と
決めた一方、「**現在の collection コスト実態の再測定要否 (P2) は未閉**」と明記している。
本 wave はその P2 に対する再測定であり、D634 の却下判断そのものは触っていない。

## 測定の質

- **probe は結果を変えていない。** 計装 arm と対照 arm の赤集合が一致した
  (shard-2 は 3 件同士、shard-1 は 30 件同士)。
- **注入した環境変数は production の姿へ戻している。** controller と 48 worker のすべてで
  `PYTHONPATH` / `PYTEST_PLUGINS` が未設定へ復元され、`env_restore_failed=false`。
  これは 1 回目の計装走で 58 件の赤を出した失敗 (下記) への対応である。
- 全 process の実時計と単調時計の offset drift は 1.5 マイクロ秒未満 (停止閾値 5 ミリ秒)。
- probe が測った report duration は production の `report.json` の値と一致する
  (最大差 2 ナノ秒)。
- 停止条件はすべて充足: affinity 48、`finished == selected`、shard-1 と shard-2 の universe 一致
  (19572、digest 一致)、hook 実行順が想定どおり。

## 主張の射程 (これを超えて使わない)

- **1 PBS job・1 hostname (bnode032)・この checkout (`dd5fddf04e`) 限定。** 実 arm は
  shard ごとに計装 2 走 + 対照 2 走、較正 1 走。
- 2026-09-01 08:15 の走 (別 checkout・別機体) の 56.37 秒**そのもの**を分解したのではない。
  現行 checkout の残差 (57.80〜58.81 秒) を分解した。旧値は文脈として引くだけである。
- pytest wall の層についてだけ述べる。job 層・session 層 (D1320) へ一般化しない。
- D1299 の 5 項を記録した: tested tip `dd5fddf04e`、K=3、worker 48、collection digest
  `814a47b3e4a7...`、growth hold の opt-in = false。

## 途中で分かった別件 (本 wave では直していない)

1. **計算ノードの openssl は機体によって `pkeyutl -rawin` を持たない。**
   bnode011 / bnode013 / bnode032 は OpenSSL 1.1.1q で、
   `test_mocc_trace_pair.py::test_anchor_v3_accepts_external_signed_pin_manifest` などが落ちる。
   基準走の bnode026 では通っていた。テスト側に能力判定が無いため、
   **どの計算ノードに当たるかで受入が赤になりうる。** 本 wave の差分とは無関係である。
2. **shard-1 の赤 30 件**は同じ機体条件で全 arm 共通に出ており、計装の有無で変わらない。
   本 wave は原因を調べていない。

## 親自身の誤りと、それを捕まえたもの

- **前 wave の一次表は下界を引いていた。** `measurements.md` §F の残差は
  `wall − max(最長単体, 総和/48)` で、実測の最大 worker occupancy を引いた値ではない。
  段 3 のレンズ A が指摘し、親が 14 走を実測値で再計算した (`measurements.md` §A)。
- **3 項分解は不成立だった** (段 2 が指摘、D 項が抜ける)。
- **probe を repo 内 (worktree 直下) に置いたことが赤の原因になった。**
  `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`
  が作業ツリー全体を見る。段 2 の「`tools/pegasus/probes/` を避ければ安全」は誤りだった。
- **計測用の注入がテストを 58 件壊した。** `PYTHONPATH` / `PYTEST_PLUGINS` を実行環境として
  検査するテスト群 (`test_run_tests_preflight.py` 47 件ほか) が差分を見て落ちた。
  段 3 のレンズ A が「probe 効果を推定で採用するな」と警告した箇所が、推定ではなく実害として出た。
