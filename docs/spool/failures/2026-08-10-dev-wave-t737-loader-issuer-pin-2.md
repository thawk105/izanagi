---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t737-loader-issuer-pin
seq: 2
---

## 再発

### F28

- **再発: 2026-08-10 ([T-737] wave)。** 事前登録した 8 変異の kill 意味論が、**上位層の 2 node に
  ついてだけ成立していなかった**。65 env の合成 registry で `[:N]` 縮退を入れると遷移 gate は
  通るが、その直後に `env_contract.py:535` の `_verify_entry_calibration` が存在しない合成
  calibration を検証して**別理由で**拒否するため、`ec.current_activation_state()` を入口にした
  node は赤くなっても受理集合が反転しない (`DW-M03` の semantic kill でない)。
  **今回の新しさは、mask が変異位置の「手前」ではなく「後続」にあったこと**である。
  `DW-M01` の恒久対応は「その位置より手前に同じ入力を落とす検査が無いこと」しか求めておらず、
  親は段 4 でその手前側だけを確認して登録した。段 6 の敵対レビュー 2 本が独立に検出し
  (2026-07-26 / 2026-08-08 の再発と同じ通過経路)、変異実測の前に落ちた。
  恒久対応の追補 = 事前登録の確認項目を「手前」から**「手前と後続の両方」**へ広げ、
  `DW-M01` の本文に後続層の確認を明記する。再照準は、受理集合が実際に反転する下位入口
  (本件では `activation.load_activation_state`) へ semantic kill を移し、上位層の node は
  **到達性 + 診断感度の pin** として `DW-M08` の別枠に記録することで行う。
  本走は最終 commit `f9b44c4c` で 8/8 KILLED + 正例 1/1 KILLED、変更前 HEAD 側 4/4 SURVIVED、
  いずれも事前登録と完全一致した。**総数を 13 kill と書かず、層ごとに何が言えるかを
  `output/insights/2026-08-10_t737-loader-issuer-pin/README.md` の表で書き分けたことが対応の本体である。**
