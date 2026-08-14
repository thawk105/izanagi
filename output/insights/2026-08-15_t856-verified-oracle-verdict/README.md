# [T-856] VerifiedOracleVerdict — 変異台帳

`judge_combined` を封印 token 専用にした wave の変異検査記録。
対象 commit は `e8e817bab2b19dad0ea782a3095a6b0cf767acd7`、
runner は `tools/mutation_worktree.py --runner-mode dispatch --detached`、
test runner argv は `python3 tools/run_tests.py orchestrator/tests/test_s8b_verdict.py -q -rf --force-dispatch`。

## ファイル

| file | 位置づけ |
|---|---|
| `mutation-spec.json` | 本走の spec (期待 node = 完全集合)。sha256 `c12ebd403ae4c74b767ebb58a49ba3abe68ac2d819481b599936dfe8f8a7f468` |
| `mutation-ledger.json` | 本走の台帳。**5/5 KILLED・SURVIVED 0・MISMATCH 0** |
| `mutation-spec-probe.json` | probe 走の spec (期待 node = 親の候補)。sha256 `d90c19c2523ae59d0ba323351206af2591fc7072ca45bde84db7a5a7babc4ca4` |
| `mutation-ledger-probe.json` | probe 走の台帳 (erratum 証拠)。4 KILLED + 1 MISMATCH |

## 事前登録した 5 変異と結果

| ID | 種別 | 無効化する検査 | 実測で落ちたテスト (完全集合) | 本走 |
|---|---|---|---|---|
| M01 | negative | `judge_combined` の封印 token 型判定 (取り出し側も条件化) | `test_judge_combined_rejects_unverified_official_oracle_verdict` | KILLED |
| M02 | negative | 再導出結果との canonical JSON 文字列比較 (dict 等値へ後退) | `test_verify_oracle_verdict_rejects_boolean_median_type_confusion` | KILLED |
| M03 | negative | oracle の `manifest_sha256` と検証済み manifest の束縛 | `test_verify_oracle_verdict_rejects_wrong_authority_observations` | KILLED |
| M04 | positive | canonical 比較を常時不一致へ (過剰拒否の検出力) | `test_verify_oracle_verdict_accepts_rederived_exact_match`、`test_judge_combined_rejects_post_issuance_oracle_document_tampering` | KILLED |
| M05 | negative | 封印判定を `.document` 属性の有無で代用 | `test_judge_combined_rejects_duck_typed_oracle_wrapper` | KILLED |

M01〜M03 と M05 はそれぞれ**ちょうど 1 本**のテストだけを落とした。単一理由性が実測で成立している。

## probe 走の erratum

初回 (probe) では M04 の期待 node を正例テスト 1 本として登録したが、実測では 2 本落ちた。
`test_judge_combined_rejects_post_issuance_oracle_document_tampering` も正当な token の発行を
前提とするため、verifier を常時拒否へ倒すと同時に落ちる。完全集合で再登録して本走した
(D303 / `DW-M08` の「期待 node は完全集合」)。probe 台帳を消さずに残すのは `DW-M02` に従う。

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
