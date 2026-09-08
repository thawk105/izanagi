---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2314-inert-reason-pair
seq: 1
---

## 再発

### F67

- **再発: 2026-09-09 (3 件目)** — 親が段 4 で、敵対相談の所見「新規 5 nodeid を
  受入所要台帳へ足せ」を**採用**と裁定したあと、段 7 で D1152 (定期更新の担い手は land 側) を
  引き当てて**不採用へ倒した**。この撤回が誤りだった。D1152 の言う land 側の実装は
  `tools/dev_wave_land.py` に存在せず、被覆の閾値を割った wave が直すほかない。
  過去 2 件が「前提を supersede する後発裁定を探さなかった」「別裁定の理由文を後発裁定より
  強い根拠にした」であるのに対し、本件の新しい角度は **所見が新しい作業を wave へ割り当てるとき、
  その作業の担い手の既裁定を引かなかった**ことである。段 1 の前提実測ではなく段 4 の所見裁定で
  起きたため、F67 の既存 2 件が指す発火点 (`DW-S01` の brief 前実測) の外にある。
  **実害あり** — 受入全走が `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  を 89.991874% (19935/22152) で赤にし、受入 1 巡と Codex 子 1 本を余分に費やした。
  撤回の根拠にした「追加後の被覆 20042/20047 = 99.98%」は**分母を取り違えた計算**で、被覆の分母は
  台帳 entry 数ではなく collection の node 数である。5 件を除けば 90.0122% なので赤は本 wave に
  帰属する。是正は正本 producer (`tools/update_acceptance_duration_ledger.py --add-only` +
  本走の JUnit) による commit `d44bc8a01` で、更新後の被覆は 99.363489%。
  恒久対応は未実施 — 「所見が担い手を割り当てるときは採用前に decisions を主題で検索し、
  引き当てた decision が指す担い手の実装が現に在るかを確かめる」義務を `DW-S04` へ足す案を
  検討したが、`docs/dev-wave/**` の L1 予算は 2 件目の記録時点で空き 0 bytes と実測されており、
  同じ理由でユーザー裁定へ返す。一次資料は
  `output/insights/2026-09-09_t2314-inert-reason-pair/README.md`。
