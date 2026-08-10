---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t737-rebuild
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
  `DW-M01` は既に「同じ入力を拒否する層が**前後に**無いこと」を求めており契約に穴はない。
  破れたのは適用であって規則ではない — 親は段 4 で手前の層 (schema 検査・catalog 照合・chain 検査) だけを
  読んで登録し、gate の**後続**にある別 module の検証層を見なかった。段 6 の敵対レビュー 2 本が
  独立に検出し (2026-07-26 / 2026-08-08 の再発と同じ通過経路)、変異実測の前に落ちた。
  一方で**本エントリの恒久対応 (i) の文言は `DW-M01` より狭く「その位置より手前」しか書いていない。**
  正本は `DW-M01` の「前後」であり、(i) はそれに合わせて読むこと。
  再照準は、受理集合が実際に反転する下位入口 (本件では `activation.load_activation_state`) へ
  semantic kill を移し、上位層の node は**到達性 + 診断感度の pin** として `DW-M08` の別枠に
  記録することで行った。本走は最終 commit `f9b44c4c` で 8/8 KILLED + 正例 1/1 KILLED、
  変更前 HEAD 側 4/4 SURVIVED、いずれも事前登録と完全一致した。**総数を 13 kill と書かず、
  層ごとに何が言えるかを `output/insights/2026-08-10_t737-loader-issuer-pin/README.md` の表で
  書き分けたことが対応の本体である。**
