---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-t2288-floor-spec-freeze
seq: 2
---

## 再発

### F864

- **再発: 2026-09-15** — 親が段 1 brief で、凍結 spec と build receipt の実 instance が
  「0 件」であることを `git ls-files | grep -i floor.pair` という **file 名検索**で断定した。
  loader (`floor_pair_driver.load_frozen_spec`) は spec の命名を一切要求しないので、
  この検索では任意の名前で保存された instance を除外できない。段 2 plan と段 3 レンズ A が
  独立に指摘し、親が内容検索 (`git grep` + JSON parse) と tracked `.gz` 1767 件の展開走査で
  取り直した。件数は変わらなかったが、根拠は不十分だった。
  **不在を主張するときは、consumer が実際に要求する識別子 (ここでは top-level の `schema` 値) で
  内容を引く。** file 名は consumer の要求ではない。
