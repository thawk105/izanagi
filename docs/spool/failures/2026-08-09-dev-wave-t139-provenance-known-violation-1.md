---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t139-provenance-known-violation
seq: 1
---

## 再発

### F37

- **再発: 2026-08-09 (3 例が同日・独立)** — [T-139] R4 probe wave の親が
  `check_ai_provenance.py 2>&1 | tail -5; echo "rc=$?"` で `tail` の rc を読み、
  **22 commit を形式違反のまま main へ land**した。[T-659] の親は `| tail -2` で末尾 2 行だけを
  見て緑と誤判定し 1 件 land。t316 design の親は `| grep -E … | head -1` で、grep がたまたま
  件数行に当たって検出した (rc では捕まえていない)。`DW-O17` は既に単独 rc を要求しており
  規約の不足ではなく遵守漏れだが、**文章による注意喚起は 3 例とも防げていない**。
  ユーザー裁定 (2026-08-09、rulings-inbox `2026-08-09-t659-provenance-and-f37-rulings.md`) により
  **機械強制へ移した** — `tools/dev_wave_land.py` が ff-only を行う land でだけ全史 provenance 監査を
  自ら走らせ、赤なら `RC_PROVENANCE = 29` で拒否する ({{D:land-ff-only-provenance-gate}})。
  逃がし道は作らない。**設計は敵対検証 4 本 (段 3 の 2 レンズ、段 6 の 2 レビュー) が全部 NO-GO を
  返したため 2 度組み直した。**親の当初案は (i) 監査を lock 内に置き `lock-busy` の即時性を壊す、
  (ii) 38.3 秒という単発観測を lock 予算の根拠にする (実際は dispatch 経路で queue 900s +
  walltime 2400s + grace 300s を含みうる)、(iii)「active fold recovery は新規 commit を 1 つも
  admit しない」という**偽の署名**を書く、の 3 点で誤っていた。逐語は
  `output/insights/2026-08-09_t139-f37-land-gate/`。
