---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2097-fixed-cost-decomp
seq: 1
---

## {{D:residual-is-startup-collection}}. 受入 1 shard の残差 約 58 秒はほぼ全量が起動費用であり、その大半は 48 worker の全 collection である

**決定:** D1384 が指した「全 shard 共通の report 外費用 約 56 秒」の内訳を、
`残差 = pytest wall − 実測最大 worker report duration 合計` として次のとおり確定する。
以後この量を「固定費」「report 外費用」と呼ばず**残差**と呼び、内訳は
**最繁 worker から見た wall 露出区間**として書く (D1298 と F755 に従う)。

**実測 (job 966271、bnode032、checkout dd5fddf04e、9 arm):**

- 残差は 9 arm すべてで 57.80〜58.81 秒に収まる。shard-1 と shard-2、計装の有無、
  `__pycache__` の温度のいずれもこの量をほとんど動かさない。
- 4 区間分解 (shard-2 の計装 arm): **A = 55.209 秒**、B = 0.035 秒、D = 0.000 秒、C = 2.913 秒。
  **残差の 95% が A (session 開始から最初のテストが始まるまで) である。**
- A の内訳は controller の event 時刻で、48 worker の gateway 生成完了が 3.13 秒、
  ready 完了が 3.47 秒、**48 worker の collection 完了通知の受信が 51.0〜55.2 秒**。
  つまり **worker 起動 約 3.2 秒、全 collection 約 51.7 秒**である。shard-1 でも同形。
- テストを 1 件も走らせない較正走の wall は **55.73 秒** (選択 6524 / 完走 0 / universe 19572)。
  A をほぼ独立に裏づける。
- **同型の量は D711 (2026-08-23) では 12.86 秒だった。** collection 対象は 14479 node から
  19572 node へ 1.35 倍だが、費用は 4.33 倍になっている。**node 数だけでは説明できない。**

**理由:**

- D1384 は約 56 秒を「どの裁定も触れていない最大の未着手軸」として調査対象に指定した。
  その量が何でできているかは、これまで測点が無く分解されていなかった (D1320 は job 層の残余について
  「分解していないものを分解したと書かない」として推測での内訳記載を却下している)。
- 4 区間の加法分解は代数の恒等式であり検証ではない。独立検査 (report 件数の一致、protocol span の
  被覆、production の `report.json` との duration 一致、terminal 点の上下限、時計 offset drift)
  を別に置き、すべて充足した状態の値である。
- 計測が結果を変えていないことを実測で確かめた。計装 arm と対照 arm の赤 nodeid 集合が一致する。

**この決定が変えないこと:**

- D634 の却下判断 (controller-only collection と manifest 共有はいずれも採用しない) は触らない。
  本決定は D634 が明示的に未閉と書いた「現在の collection コスト実態の再測定」に答えるものである。
- 短縮の実装・提案は行わない。D1384 が採らないと決めた 3 項 (最長単体の短縮解禁、
  最遅 shard 固有 約 21.9 秒の計測、本項の台帳からの削除) にも踏み込まない。

**主張の射程:**

1 PBS job・1 hostname (bnode032)・checkout `dd5fddf04e` 限定。shard ごとに計装 2 走 + 対照 2 走、
較正 1 走。2026-09-01 08:15 の走 (別 checkout・別機体) の 56.37 秒**そのもの**を分解したのではない。
pytest wall の層についてだけ述べ、job 層・session 層へ一般化しない。
D1299 の 5 項 (tested tip `dd5fddf04e`、K=3、worker 48、collection digest `814a47b3e4a7...`、
growth hold の opt-in = false) を artifact に記録した。

**却下した選択肢:**

- **残差を「固定費」と呼び続ける** — D1298 がこの差を上界と規定し、worker の idle・lock 待ち・
  scheduler・session 前後が混ざると明記している。実測では B と D がほぼ 0 だったが、
  それは今回の走でそうだったという事実であって、呼称を変える理由にはならない。
- **3 区間 (開始・窓内・終端) で分解する** — 最繁 worker が最後に終わるとは限らないため、
  その後の他 worker の tail が抜ける。実測では 0.000 秒だったが、成立しない分解を使わない。
- **collection 費用の増加の原因まで本 wave で分解する** — 測点は「controller が collection 完了
  通知を受け取る時刻」までであり、worker 内部の import・conftest・fixture 収集・deselect の別は
  測っていない。測っていないものを分解したと書かない。
