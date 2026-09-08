# 段 6 裁定 — レビュー C / D の所見と fix 指示

親の焦点走 (計算ノード job 982981.nqsv): issuer / driver / ccbench_spawn_sites / official_perf_closure / material_report の 5 file **320 passed、rc=0**。

| 出所 | 所見 | 判定 | 処分 |
|---|---|---|---|
| C§1,§3 | `mocc\|A\|B=1` が helper を通り発行できる (must-fix 主張) | **refuted** | 親が実測: `Genome(protocol="mocc", flags={"A\|B": 1}).canonical()` は `"mocc\|A\|B=1"` そのもの。helper は canonical 形を正しく受理し、導出 protocol `mocc` は genome の protocol 欄と一致する。issuer だけ厳しくすると共有 helper の目的 (consumer 間で解釈を揃える、`genome.py:223-227`) に反する。Genome の flag 名文法を上流で締めるかは**裁定パッケージ候補** |
| C§1 表 | その他の malformed 経路は fail-closed、`protocol_failed` は sticky | refuted (問題なし) | 維持 |
| C§2 | issuer は validator を直接呼ばないが、public 経路では loader が同 path・同 sha を strict 検証済み | refuted (問題なし) | 維持。重複呼出しは足さない |
| C§4 | テスト弱体化なし、期待値変更は裁定 §3 の名指し範囲内 | refuted (問題なし) | 維持 |
| C§5 M8 / D§4 M8 | 「`missing.append` 削除」型は StopIteration で赤になり帰属が壊れる | real | 採用: M8 は親の probe spec どおり **`if protocol_failed or len(protocols) != 1:` → `if len(protocols) != 1:`** (protocol_failed を無視) とする。これを殺す「部分失敗」負例 (1 receipt canonical + 1 receipt 非 canonical) が現行 test に無い → **fix1 で追加** |
| C§6 | 非保証の記述は妥当。「CCBench source の protocol を再検査しない」を足すなら docstring 1 文 | nit | fix1 で 1 文追加 (受理集合・文言は不変) |
| D§1 | 所有 3 file のみ、既定 receipt bytes 不変 (sha 一致)、HMAC golden 入力不変 | refuted (問題なし) | 維持 |
| D§2 | 新 5 nodeid が台帳未登録、旧 2 nodeid が残る。90% gate は 99.97% で割らない | nit | 裁定どおり台帳は触らない (F903)。受入で実測 |
| D§3 | t2412 との隣接衝突 0 件、意味的衝突なし | refuted (問題なし) | 統合後に同検査を再実行 |
| D§4 M6 | 期待 node は filename test + 正例の 2 node | real | probe で完全集合を実測して本走 spec へ |
| D§4 M5 | producer loader が先に拒否、登録不可 | 同意 | 未登録維持 |
| D§5 | 完了報告の M6/M8 期待集合が不完全、到達性説明が広い | real (記録上) | 段 7 の記録で訂正して書く |
| D§6 | 循環 import なし、CLI/package import ともに解決 | refuted (問題なし) | 維持 |

## fix1 への指示 (所有: issuer と issuer test の 2 file)

1. `test_identity_is_not_a_caller_surface_and_noncanonical_genomes_are_rejected` へ parametrize case `partial-noncanonical` を追加
   (candidate = `Genome(protocol="mocc", flags={"FIXTURE": 1}).canonical()`、reference = `"mocc|B=1,A=2"`)。期待は既存 case と同一。実装は変えない。
2. `_derive_identity` の docstring に「protocol は accepted build receipt の canonical genome の protocol 部であり、CCBench source の protocol を再検査しない」旨を 1 文追加。

## 変異 (probe spec のまま。fix1 後に anchor を再検証)

M1, M2, M3, M4, M6, M7, M8 の 7 件。期待 node は probe (全 SURVIVED 登録) で実測した完全集合を本走 spec へ写す (DW-M07/M08)。
M8 の kill は fix1 の `partial-noncanonical` node が担う。

## 裁定パッケージ候補 (実装しない)
- protocol の許可リスト / CCBench source 束縛 (D1696 再訪条件未成立)。
- `Genome` の flag 名文法 (`|` `,` `=` を含む名前) を model 側で締めるか。
