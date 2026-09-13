# [T-2288] B-4 床値の集約規則 — 実装・相談・検査・生証拠の所在

wave `dev-wave-t2288-b4-floor-aggregate`、branch `worktree-dev-wave-t2288-b4-floor-aggregate`。
起点 local main = `a551cdd3014708993475108f014aacbf32c21137`。
裁定 = D1936 項 7 (= D1855 案 B)。設計判断は本 wave の decisions fragment。

## 何をしたか

D1855 が残した「3 成果物の保守側最大を 1 件へ集約する規則が下流に無い」を閉じた。
事前登録 §5.1 の floor 項目へ集約規則を追補し、既存 issuer に集約発行と v2 受理の経路を足した。
**床値そのものは測っていない。** rr5 / rr95 の較正が 0 件で、workload 別 3 spec を構成できない。

## 生証拠

| path | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親) |
| `verbatim/s2-plan.md` | 段 2 plan (codex, read-only) |
| `verbatim/s3-lens-sol.md` | 段 3 敵対相談 A — 正しさ境界と保守性 |
| `verbatim/s3-lens-luna.md` | 段 3 敵対相談 B — 凍結境界・受理集合・波及 |
| `verbatim/s4-adjudication.md` | 段 4 裁定 (親)。変異事前登録を含む |
| `verbatim/s5-impl.md` | 段 5 実装子の報告 |
| `verbatim/s6-review-a.md` / `s6-review-b.md` | 段 6 敵対レビュー 2 本 |
| `verbatim/s6-fix-brief.md` / `s6-fix.md` | fix 1 巡目の親裁定と子の報告 |
| `verbatim/s6-fix2-brief.md` / `s6-fix2.md` | fix 2 巡目 |
| `verbatim/s6-fix3.md` | fix 3 巡目 (窓数の負例) |
| `mutation-spec-probe2.json` / `mutation-ledger-probe2.json` | 変異 probe (全件 SURVIVED 登録で観測 node を集める) |
| `mutation-spec-final2.json` / `mutation-ledger-final2.json` | 変異本走 (KILLED + 完全 node 集合) |

## 変異検査

probe (`mutation-ledger-probe2.json`) は baseline PASSED、8 変異中 7 件が失敗 node を出し、
**M3 (「各 spec の窓はちょうど 2」を「1 以上」へ緩める) だけが失敗 node 0 件で生き残った。**
追補 (c) が規範として書いた条件に、対応する負例が 1 つも無かった。
fix 3 巡目で窓 1 件・3 件の負例を足し、本走で KILLED になった。

本走は 2 度行っている。1 度目 (`mutation-spec-final.json`、job dir に残す) は M4 の期待 node を
probe 観測の 14 件で登録したが、fix 3 巡目で足した 3 窓負例も M4 で赤になり 15 件だった。
**erratum**: 期待 node を観測の完全集合 15 件へ再登録し (`mutation-spec-final2.json`)、
再走して 8/8 KILLED・MISMATCH 0・baseline PASSED・wrapper rc=0 を得た。
1 度目の結果は消していない (ledger は job dir と本 dir の両方にある final2 が採用版)。

| ID | 変異 | 結果 |
|---|---|---|
| M1 | 保守側の最大を最小へ反転 | KILLED (4 node) |
| M2 | 期待 spec に summary が無い場合の閉包検査を無効化 | KILLED (1 node) |
| M3 | 窓数ちょうど 2 の要求を 1 以上へ緩める | KILLED (2 node) |
| M4 | campaign ごとの期待 strata を当該窓の射影から全窓集合へ替える | KILLED (15 node) |
| M5 | retained と dropped の非交差・完全分割の検査を無効化 | KILLED (3 node) |
| M6 | 窓の artifact 閉包検査を無効化 | KILLED (5 node) |
| M7 | 非最大入力を集約成果物の出所から落とす | KILLED (4 node) |
| M8 | v2 loader の全体再構成比較を無効化 | KILLED (2 node) |

公開経路の正例 `test_aggregate_public_issue_load_and_preregistration_pin` は M1・M4・M7 を
殺している。内部関数だけを組み立てる試験ではないことの証拠である。

## 親が実走した検査

| 対象 | 結果 |
|---|---|
| `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` | 79 passed、rc=0 |
| `orchestrator/tests/test_p3_b4_material_report.py` | 49 passed、rc=0 |
| `orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py` | 33 passed、rc=0 (追補を入れた後) |
| `tools/check_docs.py` | 違反なし、rc=0 |
| `tools/check_ai_provenance.py` (full) | 9713 件、新規違反なし、rc=0 |
| §5.1.1 の raw / semantic 両 hash | 追補の前後で不変 (親が実測) |

受入全走の結果は worklog に書く。

## 本 wave が保証しないこと

- **床値の値を何も出していない。** 較正・凍結 spec・測定はすべて後続である。
- 集約成果物が材料レポートまで届く正例は未作成。合成 repo に prerun publication と raw analysis が
  無く、公開 builder へ渡せない。§5 pin の解決までで止めてある。
- 機械検査は、期待 spec 列が結果を見る前に選ばれたことも、それが事前登録の対象集合と意味的に
  一致することも、n = 62 と 24 時間分離が満たされていることも示さない。追補 (f) に明記した。

## 次 wave の出発点

rr5 / rr95 の較正取得 (D1936 項 6 / [T-2515]) が先行依存である。較正が揃ったら
workload 別 3 spec を凍結し、対照対 driver で 2 窓ずつ測り、本 wave の集約経路で 1 件へまとめて
§5 の floor 欄へ pin する。pin する commit の message に採用裁定の D 番号を書く (§11.1 の案)。
