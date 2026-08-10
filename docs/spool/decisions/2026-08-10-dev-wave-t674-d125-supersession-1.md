---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t674-d125-supersession
seq: 1
---

## {{D:d125-campaign-id-invariance-superseded}}. D125 決定 (2) のうち「OTHER の campaign_id は 1 bit も変えない」だけを前向きに失効させ、env による identity 分離は残す

**背景:** D125 決定 (2) は独立した 2 つの内容を 1 項に束ねている。(i) Pegasus 契約のときだけ
`search_config` へ `measurement_env` を足し campaign identity を env で分離する、
(ii) OTHER の campaign_id は 1 bit も変えない (既存 campaign の再開互換)。
**(ii) は既に破れており、破ったのは本 D ではない。** ユーザー裁定は、この失効を遡及改変ではなく
前向き supersession の新 D として記録することを求めた。

**実測 (一次資料):**

- (i) の実装は実在する。`orchestrator/campaign/p3_s4_loop_trigger_gating.py` の
  `_CAMPAIGN_ENV_KEY = "measurement_env"` と、`PEGASUS_COMPUTE` 側だけへ足す site 射影である。
  OTHER の `search_config` には入らず、同 module の test が両方向 (compute にある / OTHER にない) を
  pin している。
- (ii) は 3 世代で 3 回破られた。`orchestrator/tests/test_p3_s4_loop_trigger_gating.py` が
  pre-T343 / T343 / T530 の OTHER・COMPUTE 計 6 値を定数として並べ、**現行の OTHER id は T343 値**で
  あることを等号で、T530 値でないことを非等号で pin する。D259 決定 1 が契約 hash を identity
  pre-image から外した結果、現行値は T530 値ではなく T343 値へ戻っている。
- 既存成果物との対応: `output/campaigns/` は 30 campaign・30 lock。pre-T343 値を名に持つ dir は 1、
  現行値 (T343 値) を持つ dir は 0、T530 値を持つ dir は 0。
  **再計算した campaign_id は既存 dir を 1 本も指さない。**
- 既存成果物の到達性を担保しているのは id ではなく dir 名 prefix である。
  `orchestrator/campaign/replay.py` の `discover_campaign_dir` は `<slug>-<search_tag>-*` の glob で
  discover し、docstring が「id の pre-image に依存しない (C1 回避)」と明記する。

**決定 (1): D125 決定 (2) のうち (i) env による identity 分離は存続する。** 正本は D259 決定 7
(「契約 hash は id に入れないが env tag は入る」という非対称の明文化) であり、本 D はこれを覆さない。

**決定 (2): D125 決定 (2) のうち (ii)「OTHER の campaign_id は 1 bit も変えない」は本 D の日付を
もって失効する。** 以後この文を有効な不変条件として引いてはならない。失効の理由は方針変更ではなく
**事実の追認**である — 上記のとおり land 済み production が既に 3 回破っており、不変を保つ機構は
存在しない。

**決定 (3): 失効は前向きのみとし、遡及改変をしない。** D125 の本文、当該変更以降の worklog、
既存 campaign directory と lock の bytes は 1 byte も書き換えない。歴史記録の改竄を避けるためであり、
dev-wave 契約の受入免除証拠を巡る裁定で採った「旧射程を precedent として引く canonical decisions は
遡及改変せず前向き supersession だけで足りる」と同じ扱いである。

**決定 (4): campaign_id の pre-image を変える変更で「既存成果物が到達不能になる」を blocker と
しない。** 根拠は決定 (2) の実測 — discover が id 非依存であり、再計算 id は現時点で既に既存 dir を
1 本も指していない。これは本 D が新設する緩和ではなく status quo の明文化であり、契約 hash 束縛の
実装 wave が同じ実測で blocker から外した判断と同一である。
**ただし id を literal 固定するテストは同じ変更単位で更新する義務を残す** — 現に 6 定数がその履歴を
保持しており、この pin が無ければ 3 回の変化はいずれも沈黙していた。

**名乗ってよい範囲 (これを超えて書いてはならない):**

本 D は**記録であって機構ではない**。

- 「今後 campaign_id が安定する」とは名乗らない。安定させる仕組みは無く、pre-image を変える
  変更は今後も id を変える。
- 「既存成果物が引ける」ことを保証しているのは prefix discover の 1 点だけである。
  dir 名 prefix (`<slug>-<search_tag>-`) を変える変更は依然として到達性を壊す。
- 本 D はコードを 1 byte も変えないので、受理集合・certified 選択・レポートの値・proof 参照は
  いずれも変わらない。変わるのは**今後の wave が blocker と判定する集合**だけである。

**却下した選択肢:**

- **D125 決定 (2) 全体を失効させる案。** (i) の env 分離は現に実装されて動いており、
  D259 決定 7 が identity に残すと明示裁定している。全体失効は生きている裁定を巻き込む。
- **D125 本文へ取り消し線・注記を入れる案。** 遡及改変であり、裁定時点の記録を読めなくする。
  ユーザー裁定も「遡及改変なし」を明示している。
- **id 不変を回復する実装 (pre-image を pre-T343 形式へ戻す) を作る案。** identity と受理集合を
  再び動かす変更であり、裁定が求めているのは失効の記録だけである。実装は裁定範囲外。
