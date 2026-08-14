# [T-856] VerifiedOracleVerdict — 変異台帳

`judge_combined` を封印 token 専用にした wave の変異検査記録。
runner は `tools/mutation_worktree.py --runner-mode dispatch --detached`、
test runner argv は `python3 tools/run_tests.py orchestrator/tests/test_s8b_verdict.py -q -rf --force-dispatch`。

**最終結果は `mutation-ledger-final2.json` の 6/6 KILLED・SURVIVED 0・MISMATCH 0**
(対象 commit `e418f9c10116a383ab8ba3117a5ff00a73cef9cc`)。

## ファイル

| file | 対象 commit | 位置づけ |
|---|---|---|
| `mutation-spec-final2.json` / `mutation-ledger-final2.json` | `e418f9c1` | **本走 (権威)**。6 変異、全 KILLED。spec sha256 `79b11bb8247ef0d7edf4598b2c5581eadfaf8e251fc44c37d2034ca2a3c61bbd` |
| `mutation-spec-m06.json` / `mutation-ledger-m06.json` | `b486eaf2` | M06 単独走。**SURVIVED** — 検出力の穴を実測で確定した回 |
| `mutation-spec.json` / `mutation-ledger.json` | `e8e817ba` | 5 変異の中間走。全 KILLED (M06 追加前) |
| `mutation-spec-probe.json` / `mutation-ledger-probe.json` | `e8e817ba` | probe 走。期待 node を完全集合へ再登録するための erratum 証拠 |

## 事前登録した 6 変異と結果 (本走)

| ID | 種別 | 無効化する検査 | KILL したテスト (完全集合) |
|---|---|---|---|
| M01 | negative | `judge_combined` の封印 token 型判定 (取り出し側も条件化) | `test_judge_combined_rejects_unverified_official_oracle_verdict` |
| M02 | negative | 再導出結果との canonical JSON 文字列比較 (dict 等値へ後退) | `test_verify_oracle_verdict_rejects_boolean_median_type_confusion` |
| M03 | negative | oracle の `manifest_sha256` と検証済み manifest の束縛 | `test_verify_oracle_verdict_rejects_wrong_authority_observations` |
| M04 | positive | canonical 比較を常時不一致へ (過剰拒否の検出力) | 正例テストと、token 発行を前処理に含む 2 本 (計 3 本) |
| M05 | negative | 封印判定を `.document` 属性の有無で代用 | `test_judge_combined_rejects_duck_typed_oracle_wrapper` |
| M06 | negative | `judge_combined` 側の plain JSON 型再検査 | `test_judge_combined_rejects_nested_semantic_subclass_in_sealed_document` |

M01〜M03・M05・M06 はそれぞれ**ちょうど 1 本**のテストだけを落とした。単一理由性が実測で成立している。

## M06 — 変異が生存して検出力の穴を見つけた回

最終レビューが「`judge_combined` の plain JSON 型再検査には専用の実効性テストがない」と指摘した。
親はこれを断定せず、M06 を `expected_status=SURVIVED` で走らせて実測した。**結果は SURVIVED**
(落ちたテスト 0 件) で、指摘は real と確定した。

この防壁が守るのは次である。封印 token の `document` の nested 値を、`items()` の結果は元のまま
返すが `__getitem__` / `get` だけ別値を返す `dict` subclass に置き換えると、`json.dumps` は
`items()` を使うため **canonical hash は発行時と一致したまま**、判定本体が読む中央値だけが変わる。
plain 型検査はこれを拒否するが、それを固定する回帰テストが無かった。

追加したテストは、正規に発行した token の nested configuration cell をその subclass へ置き換え、
**canonical hash が `document_sha256` と一致すること自体も assert** したうえで、
`judge_combined` 経由で plain 型検査の例外メッセージを `match` で固定する。
hash 一致を assert するのは、測っている対象が hash 検査ではなく型検査であることを固定するためである。
production は変更していない — 欠けていたのは検査ではなく検出力だった。

## probe 走の erratum (期待 node の再登録)

期待 node は 2 度再登録した。いずれも `DW-M08` の「期待 node は完全集合」に従い、
実測した失敗 node 集合へ合わせたものである。台帳は消さずに残す (`DW-M02`)。

1. probe 走 (`mutation-ledger-probe.json`): M04 の期待を正例テスト 1 本で登録したが、実測では 2 本
   落ちた。`test_judge_combined_rejects_post_issuance_oracle_document_tampering` も正当な token の
   発行を前提とするため、verifier を常時拒否へ倒すと同時に落ちる。
2. 6 変異の初回走 (`mutation-ledger-final.json` 相当): M06 用テストを足したことで、M04 の期待が
   さらに 1 本増えて 3 本になった。同じ理由 (新テストも token 発行を前処理に含む)。

## M01 の再照準 (段 6 の 2 レンズが独立に指摘)

当初の M01 は `judge_combined` の型判定だけを除去する 1 置換だった。しかしそれだけでは
直後の `oracle.document` が `AttributeError` になり、**受理集合は広がらない**。
テストは赤くなるが「封印を外した」ことの実証にはならず、偽の KILLED になる。
型判定の緩和と取り出しの条件化を**累積 2 置換**にして初めて、生の `OfficialVerdict` が
判定関数を通り抜ける。親は登録前に in-memory probe で次を実測した。

| 変異 | 生 `OfficialVerdict` | `.document` を持つ別 object |
|---|---|---|
| M01 適用 | **受理される (fail-open)** | 拒否 |
| M05 適用 | 拒否 | **受理される (fail-open)** |

2 つの経路が 1 対 1 に分離しているため、それぞれの検出力を別々のテストで固定できる。
