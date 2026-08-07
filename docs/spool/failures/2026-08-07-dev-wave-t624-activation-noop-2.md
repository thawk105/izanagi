---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t624-activation-noop
seq: 2
---

## 再発

### F30

- **再発: 2026-08-07** — 四度目。前回 (三度目) と同じ role 名 key の pin を、同じ module
  (`orchestrator/campaign/env_contract.py`) について再び数え落とした。今回は原因が 2 つ重なる。
  (i) 段 1 で `grep -rln "env_contract" --include=*.json output/` を走らせたが、**出力を `| head` で
  10 件に切って**全件を見なかった。silo evidence の
  `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` は path 文字列を持つので
  検索自体には掛かっていたが、切られた側にいた。(ii) t419 probe manifest の
  `env_contract_sha256` は role 名 key であり path 検索に掛からない — `DW-O09` が三度目の
  恒久対応として明記した経路をそのまま踏んだ。結果、brief へ「bytes を literal で pin する
  台帳・test は 0 件」と誤って記録した (正しくは歴史 pin 2 件・live pin 0 件)。
  段 3 の 2 レンズが独立に検出し、親が実測で裏を取った。本 wave は当該 module を変更せず
  終端したため実害はない。恒久対応は `DW-O09` から変更せず、**検索出力を件数で切らない**ことを
  同節の既存義務の運用として守る (新しい節は作らない)。
