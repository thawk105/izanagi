# 2026-09-08 [T-2380] 軸 B5 の後継凍結物 — 3 点 (候補主キー / catalog の seal / 引用・著者経路の起点) を閉じた記録と生証拠

- wave: `dev-wave-t2380-b5-successor-freeze` (branch `worktree-dev-wave-t2380-b5-successor-freeze`、base main `34af5a571`)
- 凍結物: `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md` (1/2、commit `caae3b683`)、
  `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json` + `orchestrator/axis_b5_search/catalog.py` (commit `64681dda7`)、
  `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md` (2/2、本 README と同じ commit)
- 判定値の正本は 2/2 であり、本 README は生証拠の所在と、凍結物に入らない経過だけを持つ。

## 生証拠の所在

| dir | 内容 |
|---|---|
| `probe/` | 1/2 §6 の非 anchor による応答形の観測 (OpenAlex / arXiv / doi.org / Crossref / DBLP の header・body。request の URL は 1/2 §6 に逐語)。`dblp_*.body` は Anubis の challenge HTML そのもの |
| `resolve/` | anchor 16 件の書誌解決と ID lookup の 1 回目 (OpenAlex の `select` に `referenced_works_count` を含まない request 形)。`summary.json` が要約 |
| `resolve2/` | 同 2 回目 (1/2 §2.4 の登録 request 形)。**2/2 の値はこちらから取った。** `*.meta.json` に URL・method・HTTP status・全 response header・body SHA-256・request 時刻 (UTC) |
| `codex/` | 段 2 plan、段 3 相談 A / B、段 5 author、段 6 レビュー A / B、fix、焦点再レビューの逐語と receipt |
| `mutation/` | 変異 spec (probe / final)、台帳 (probe / final)、attempt 記録。runner argv は台帳の `runner_identity` |
| `brief.md`、`rulings-stage4.md`、`rulings-stage6.md` | 親の brief と裁定 |

## 変異 matrix (commit `64681dda7` の HEAD、`tools/mutation_harness.py --runner-mode dispatch`、runner = `tools/run_tests.py --force-dispatch orchestrator/tests/test_axis_b5_search_catalog.py -q -rf`)

- probe (13 件すべて SURVIVED 期待で観測 node を収集): baseline 17 passed、MISMATCH 12 / SURVIVED 1 (等価変異 `m13`)。観測した赤 node 集合は焦点再レビューの静的見積りと 13/13 で一致した。
- 本走 (観測 node を期待に写し、`m01`〜`m12` KILLED / `m13` SURVIVED 期待): baseline 17 passed、**KILLED 12 / SURVIVED 1 (m13、等価) / MISMATCH 0**、完全集合の期待 node と 13/13 一致 (台帳 `mutation/final-ledger-1.json`、spec sha256 `fa43ff2ed4e0f72d4c092d6e58492c515f374a4c9aeb522b93994de1750df769`)。

| id | 変異 | 赤 node 数 (観測) |
|---|---|---:|
| m01 | `from urllib.parse import quote_plus as quote` (空白が `+`) | 9 |
| m02 | OpenAlex の safe から `,` を外す | 6 |
| m03 | OpenAlex の複数語を `"` で囲む | 6 |
| m04 | arXiv の `abs:"..."` の引用符を落とす | 6 |
| m05 | block 内の語順を sort | 10 |
| m06 | DBLP 直積 `product` → `zip` | 7 |
| m07 | DBLP 対象枝から `B5-Q10` を落とす | 8 |
| m08 | 語 ID の 2 桁 0 埋めを外す | 11 |
| m09 | `B5-CTL-AND2023@dblp` の `shares_request_with` を `null` | 5 |
| m10 | venue の年範囲から 2026 を落とす | 6 |
| m11 | render の末尾 newline を落とす | 4 |
| m12 | `--verify` を bytes 比較から JSON 意味比較へ | 1 |
| m13 | `list(group)` → `[*group]` (等価、SURVIVED 期待) | 0 |

## 経過 (凍結物に入らないもの)

- 段 3 レンズ A が親 brief の erratum 案 (`非収録` を見てから control から外す) を倒した。裁定は「索引別 member 集合を lookup 前に固定」。
- 段 3 レンズ A-3: `G2-SA` の包含枝がすべて C を要求する構造的懸念 → ユーザーへの裁定パッケージ。
- 段 6 RA-04 / RA-05: `index` の表記と `year` の型は凍結文から一意に読めない → 実装のとおり (小文字 token、number) に親裁定、bytes 不変、2/2 の E-4。
- 段 6 RA-08 / RB-01: test の自己参照と受理集合の穴 → fix 子が test だけを直した。焦点再レビューで全所見 closed。
- DBLP: 3 入口・4 UA・2 Accept で anti-bot challenge。1 回目の応答には meta refresh があり 2 秒後に追従したが、2 回目以降は JS 駆動の challenge で、以後は模倣しない裁定。
- OpenAlex の lookup を 2 回行った (1 回目は登録 request 形と `select` が 1 field 違った)。値は 16 件とも同一。
