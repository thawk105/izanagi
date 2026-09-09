# 変異台帳 — [T-2154] n-pilot 条件関門の配線と後継事前登録

本走 (2 巡目): `mutation-spec.json` / `mutation-out.json`。
**baseline PASSED / KILLED 6 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、期待 node 完全一致 6/6。**
runner argv は `python3 tools/run_tests.py --force-dispatch -q -rf
orchestrator/tests/test_s8b_oracle_n_pilot.py orchestrator/tests/test_ccbench_spawn_sites.py`、
`--runner-mode dispatch --detached`。

## 事前登録の時点

変異は段 4 の裁定で実装前に登録した。段 5 / 段 6 の実装が終わり、driver への修正が
すべて完了した最終 commit の bytes に対して本走した (行番号 pin と digest pin は最後に 1 回だけ
当てるという手順に従った)。

## 結果

| ID | 変異 | 結果 | 赤くなった node |
|---|---|---|---|
| m01 | 返却物検査の文を丸ごと削除 | KILLED | 閉包 2 件 + 負例 2 件 + 冗長 gate 1 件 |
| m02 | 期待 digest の出所を freeze から `prepared.genome.flags` へ差し替え (恒真化) | KILLED | 出所独立の正例 + 冗長 gate |
| m03 | adapter が record を運ばず delegate の戻り値をそのまま返す | KILLED | 本番経路の正例 + 冗長 gate |
| m04 | 検査の拒否を `except: pass` で握り潰す | KILLED | 負例 2 件 + 冗長 gate。**閉包検査は緑のまま** |
| m05 | 後継事前登録の `source.commit` を実在しない値へ | KILLED | 後継テスト |
| m06 | 2 つの sha 定数を 1 つに潰す | KILLED | 後継テスト |

## 冗長 gate の宣言 (単独変異の帰属証拠から外す)

`orchestrator/tests/test_s8b_oracle_n_pilot.py::test_r33_successor_protocol_document_loads_from_repository`
は、後継事前登録が記録する digest と**現行 driver bytes の digest** の一致を検査する。
そのため **driver をどう変異させても必ず赤くなる。** m01〜m04 ではこの node を
帰属の証拠に数えない。m05 / m06 ではこの node が変異の直接の標的なので、証拠として数える。

冗長 gate を除いた帰属は次のとおりで、いずれも空ではない。

- m01 → 閉包 2 件 + 負例 2 件
- m02 → `test_build_binaries_uses_binding_flags_and_prepared_records_independently`
- m03 → `test_default_build_fn_wraps_build_v2_with_prepared_records`
- m04 → 負例 2 件

## m04 の観測 — 閉包検査の盲点 (kill には数えない診断 pin)

m04 は受理集合を変えるので KILLED に数える。それとは別に、**同じ走行で
`test_define_sink_cross_product_has_no_unreviewed_ungated_member` が緑のままだった**ことを
診断 pin として記録する。

拒否を握り潰しても閉包検査が緑のままだということは、この検査が当該 member について
「呼出しが所定の位置にある」以上のことを保証していないという意味である。
配線側はこの弱い経路に依存しないよう、呼出しを module scope の実体・無条件の文・
例外の再送出という署名で固定してある。検査本体の強化は族全体に効く共有機構の変更なので、
本 wave では scope 外としてユーザー裁定へ返した。

## 初回走行 (probe) と erratum

初回は期待 node 集合が不完全で MISMATCH 4 件になった。**期待した node は 6 変異すべてで
漏れなく発火しており、不一致はすべて「余分に赤くなった」側**である。余分の内訳は
(a) 上記の冗長 gate、(b) 親の登録漏れ (`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
— 閉包の分類件数を固定する別テストで、m01 では正当に赤くなる) の 2 種だった。
初回結果は消さず `evidence/mutation-probe1-summary.json` と
`evidence/mutation-spec-probe1.json` に保存し、観測した完全集合で再登録して 2 巡目を走らせた。
