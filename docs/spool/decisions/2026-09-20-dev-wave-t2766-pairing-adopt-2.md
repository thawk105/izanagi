---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2766-pairing-adopt
seq: 2
---

## {{D:pairing-default-on-adopted}}. 受入 shard 内 pairing を既定 on で採用し、property 4 種を残す

**決定:** D2172 項 1 (択 (a)) の実装として、受入の collection hook (`orchestrator/tests/conftest.py`) は cost 順の unit 列に無条件で `_pair_initial_distribution_units` (realized order の 49〜96 位を候補中最小 cost の 48 unit に入れ替える) を適用する。環境変数 `IZANAGI_ACCEPTANCE_PAIRING_V1` の opt-in・token・`tests` task の allowlist 行は撤去し、opt-out も設けない。全 item への property 4 種 (`izanagi_acceptance_pairing_v1_{scope,rank,partner,worker}`、pairing 適用走のみ) は残す。unit < 96 の無変更、cardinality 不成立時の `pytest.UsageError` (fail-closed)、受理集合 (selected / hold / group / unit 境界・marker・既存 property・identity) の不変は保つ。

**理由:**
- 効果の再確認 (待ち手経由 = 本番経路の実受入、A = 採用前 main / B = 採用後の隣接対 3 組) で 3 対とも B が短く、最遅 shard の JUnit wall の対差 145.8 / 86.3 / 57.3 秒、対率中央値 19.6 % で、事前登録した land 条件 (全対 ΔW > 0 かつ対率中央値 ≥ 10 %) を満たした。前 wave (同一 tip の直接投入) の 101.7 / 112.9 / 144.3 秒と同方向。
- property は本番の毎受入に「発火と実配布の witness」(被覆 100 %、rank 48〜95 = partner 集合、多重集合の独立再計算、worker 別 item 列) を残す唯一の手段で、既定 on の正例 test と変異 M5 の帰属もこれに依る。機序が未同定のまま採るので、後から機序を調べる材料を毎走残す価値がある。
- opt-out を足さないのは、裁定が「名指しの変更に限定し付随する gate を足さない」と定めるためと、off の経路を残すと A 不変の負例と変異 M3 を維持し続ける費用が要るため。撤去は並べ替えの呼び出し 1 行と property 付与の削除で戻る。

**却下した選択肢:**
- property を外して順序変更だけ入れる — junit.xml は小さくなる (受入 1 走あたり約 −13 MB) が、本番で pairing が発火した証拠が junit から消え、機序調査の材料も残らない。
- (b) A 側 witness (機序調査) を採用の前提にする — 裁定が「相乗り可、採用を遅らせない」と定め、A の item → worker 対応は A の code を変えないと取れない (A = 採用前 main でなくなる) ため本 wave では取らない。
- (c) 見送り — 効果は本 wave でも 3 対同方向で確認された。

**再訪条件:** property の費用は junit.xml が受入 1 走あたり約 +13 MB (A 0.7 / 1.8 / 1.6 MB → B 2.4 / 6.2 / 6.4 MB、3.4 倍) と実測した。session dir の容量が問題になった時点で、property を rank / partner だけに縮約するか外すかを別裁定にする。効果量は regime 依存 (57〜146 秒の観測) で「毎受入 100 秒」と一般化しない。対 3 (docs fold だけの最もきれいな対) が 12.6 % と閾値に近いため、効果の消失が疑われたら同じ事前登録 (隣接対 3 組、閾値 10 %) で再測する。
