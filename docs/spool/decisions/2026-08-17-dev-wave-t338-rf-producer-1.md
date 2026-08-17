---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t338-rf-producer
seq: 1
---

## {{D:rf-producer-blocked-by-admission-gate}}. RF producer は投入 gate の完成に依存する — 本 wave は実装せず、閂の所在を公表層から gate へ訂正する

**背景:** D481 は RF 発火条件 (ii) の評価領域を D282 pin 済み receipt へ束縛し、pilot を公表層実装と
追補 P 凍結から切り離した。同 D の backlog は「RF producer と attempt registry の実体」を第 1 項に
挙げ、archive worklog はこれを「producer 実装から着手可」と記録した。本 wave はその実装 wave として
起動し、段 2 プラン 1 本と段 3 敵対レンズ 2 本 (総括はいずれも NO-GO) を得た。
一次資料 = `output/insights/2026-08-17_t338-rf-producer/` (裁定パッケージ本体は `package.md`)。

**決定 (1): 本 wave は実装しない。** 実装差分はゼロであり、変異 matrix は `DW-S04` により免除される。
コード・テスト・gate・schema・artifact・凍結 bytes・certified 選択・材料レポート・proof chain・
受理集合はいずれも不変である。

**決定 (2): producer を止めている閂は公表層ではなく投入 gate であると訂正する。** D481 は
producer の閂を公表層実装だと同定し、それを切り離した。切り離し自体は正しく、公表層は
もはや producer を止めていない。**しかし閂はもう 1 つあり、D481 はそれを見ていなかった。**

- record-items-v2 §6.10 は「受領証を永続化する関数自体」が `PreregBinding` を必須 keyword-only で
  受け、三つ組と `measurement_head` を照合してから publish することを要求し、別経路の writer を禁じる。
- `PreregBinding` は D264 が投入 gate の完成まで非 export と定めた 4 名前の 1 つであり、
  D282 の `preserved` がこの非 export を維持している。
- したがって**投入 gate が完成するまで、受領証を書き出す producer は作れない。**

**決定 (3): 残余を「producer 実装済み」として land しない。** 決定 (2) の制約と、投入なしでは
attempt が真正な qsub 事実を持てないという制約を引いた残余は、attempt registry と純粋な組み立て
関数と否定検査である。**これは D264 が名指しで却下した形である** — 同 D は
「台帳だけが『producer 実装済み』へ進む半実装は、直前の wave が blocker と判定した形である」と
書いている。拒否専用 adapter や fixture 限定 leaf を producer 結線として land しない
(D147 決定 (3) / D163 決定 (1) の再適用)。

**決定 (4): `declared_use_class = "dry"` は qsub 事実の免除ではない。** D282 pin 済み schema の
`attempt` は `qsub_result` / `performance_started_marker` / `cluster_slot_or_null` を必須とし、
種別による免除規定を持たない。`declared_use_class` は利用意図であって受理入力にしてはならない
(record-items-v2)。投入せずに値を合成すれば raw 事実でなくなる。`pilot_submission = forbidden` と
D292 の解除権威は本 D でも維持し、解除条件の中身も定めない。

**決定 (5): D229 決定 (8) の必須 kill 3 件は producer 段では達成できないと実測記録する。**
敵対レンズ 2 本が独立に同じ結論へ到達した。「失敗した投入を台帳と raw の双方から落とす」は
producer の外にある durable な intent authority と PBS driver との結線を要し、
「親系列 ID の自己申告による累積有意水準のリセット」は族の根から測定 head までの全履歴 validator を要し、
「anomaly の clean 申告」は raw の正しさ証拠を再計算する独立 semantic validator を要する。
いずれも D229 決定 (6) の順序では producer より後段の機構である。**本 wave はこの 3 件を
「kill 済み」と記録しない。**どの段の受入条件に置くかはユーザー裁定へ返す。

**決定 (6): 起動命令が名指しした既存機構は実在しないと訂正する (実測)。**
`orchestrator/campaign/s8b_floor_stats.py` は自らの保証境界として「raw session 自体の真正性
(append-only journal・attempt registry・schedule 突合) は保証しない」と明記しており、
attempt registry を持たない。`s8b_floor_campaign.py` のそれは私有 runner クラスの私有メソッド群で、
床値 protocol の cell / round / retry 予算に束縛され export されていない。
D229 決定 (7) が名指しする再利用先は `orchestrator/qualification/attempt_ledger.py` である。
ただし再利用先の確定は次 wave の段 1 要件とし、本 D では定めない。

**決定 (7): D496 との相互作用について、承認済み出力契約に床値表への依存は無いと実測記録する。**
D282 pin 済み受領証 schema と record-items-v2 の双方で `floor` / `床値` の出現は 0 件であり、
schema は 3 arm を同一受領証内で必須とする。RF は床値表の引き当てではなく同一 campaign 内の
対測定であって、D496 が求める形と一致する。D162 決定 (9) も層 3 の calibration floor 閉表との
分離を既に命じている。**この結論は承認済み出力契約の範囲に限る。**
文字列の不在から実装依存の不在を導かない — 新規 module の設置先 package は import graph 上
calibrator を引くこと、および D496 の構成集合固定と失敗時の全構成再測定という lifecycle 条件が
attempt registry の identity 設計に効くことを、次 wave の段 1 要件として残す。

**却下した選択肢:**

- attempt registry だけを先に land し producer 実装済みと記録する — D264 が名指しで却下した形であり、
  本 wave の実測では必須 kill を 1 件も達成せず消費者も 0 件である。
- `dry` 受領証で end-to-end を通す — 決定 (4) のとおり免除規定が無く、合成すれば raw 事実でなくなる。
- 恒真 deny stub や拒否専用 adapter を gate の代わりに置く — D264 が明示的に却下している。
- 発火条件が揃わないまま機械化する — `DW-G04` は発火条件を満たす既存 artifact path か計測 ID を
  brief に書けない場合、設計メモに留めると定める。本 wave はどちらも書けない。
- 段 2 プランの総括をそのまま採る — 必須 kill が「後二件」だけ不能という記述は同プラン本文と
  食い違っており、実際は 3 件とも不能である。

**研究状態への影響:** certified 選択の値、材料レポート、proof chain、凍結 bytes、既存 gate、
受理集合はいずれも**不変**である。実装差分はゼロであり、producer・pilot artifact・
validator / consumer のいずれも本 D では生成しない。変わるのは、RF producer を止めている閂の
所在が公表層から投入 gate へ訂正されたことと、必須 kill 3 件の帰属段がユーザー裁定待ちとして
分離されたことの 2 点である。
