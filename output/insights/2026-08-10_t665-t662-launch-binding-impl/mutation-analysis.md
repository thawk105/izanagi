# 変異 matrix の結果と親の判定 — [T-665] + [T-662]

2 走した。1 走目 = 事前登録 9 件 (`mutation-spec.json` / `mutation-ledger.json`)、
2 走目 = 訂正再走 5 件 (`mutation-spec-correction.json` / `mutation-ledger-correction.json`)。
**baseline は両走とも PASSED。** runner は `python3 tools/run_tests.py --force-dispatch -rf` で、
変異ごとに全 suite を走らせている。

| ID | 1 走目 | 2 走目 | 親の判定 |
|---|---|---|---|
| M01 規範行の `fullmatch` → `search` | MISMATCH | MISMATCH (M01c) | **KILLED 相当**。期待 7 node がすべて赤。超過分は同一理由の consumer |
| M02 規範行の件数検査 `!= 1` → `< 1` | KILLED | — | KILLED |
| M03 U+2028/U+2029 拒否を `pass` へ | SURVIVED | SURVIVED (M03b 二層) | **冗長分岐**。下記 |
| M04 authority-bound で `--reasoning` を受理 | KILLED | — | KILLED |
| M05 top-level fallback を復活 (**wave 前の形**) | MISMATCH | **KILLED** (M05c) | KILLED |
| M06 `attempts[-1]` だけで accepted (**wave 前の形**) | MISMATCH | MISMATCH (M06c) | **KILLED 相当**。下記 |
| M07 working tree と authority commit の比較を無効化 | KILLED | — | KILLED |
| M08 `effort = snapshot.review_effort` → `"low"` | **SURVIVED** | **KILLED** (M08c) | 検出力の穴を塞いだ後に KILLED |
| M09 dispatcher の argv から `--stage` を落とす | KILLED | — | KILLED |

## M08 — 本 wave で最も重要な発見

**対象テスト 623 全緑、段 3 と段 6 の敵対レビュー計 4 本を通過した状態で、この変異は生存した。**

原因は循環である。`test_docs_authority_alone_rejects_consistent_effort_mutation` と
`test_authority_bound_launch_uses_derived_model_and_effort` は期待値を
`derive_launch(snapshot_authority(_ROOT), ...)` から取っていた。派生関数そのものを変異させると
期待値も一緒に動くため赤にならない。
**すなわち「段 6 の effort が `DW-S06-A` の記載と一致する」という [T-665] の中核主張が、
テストで証明されていなかった。**

docs を独立に読む cross-check を 3 本足して塞いだ (production は 1 byte も変えていない)。
`test_review_effort_matches_independent_docs_cross_check` /
`test_focus_effort_matches_independent_docs_cross_check` /
`test_all_stage_models_match_independent_docs_cross_check`。
再走で M08c は KILLED になった。期待値の literal はテストへ書いていない
([T-667] の見送り裁定の実質的な再提案を避けるため)。

## M03 — 単層でも二層でも生存した。kill として数えない

`DW-M02` に従い、まず mask を疑って**二層変異 M03b** を登録した。
M03b は sentinel を除去した候補をそのまま規範行として採用する形で、成功すれば
受理集合が変わる (偽装行が権威として通る)。**これも rc=0 で生存し、赤は 0 件だった。**

親が機序を実測した。**Python の `str.splitlines()` は U+2028 と U+2029 で行を分割する**
(`"abc def".splitlines()` → `['abc', 'def']`)。したがって偽装された規範行は
上流の可視行分解で 2 行に割れ、どちらも `fullmatch` に当たらず「規範行が 0 件」で拒否される。

- **性質は守られている** — 偽装行は受理されない。decoy テスト `[u2028]` / `[u2029]` は
  baseline でも両 mutant でも緑である。
- **しかし当該分岐が独立に効いていることは示せなかった。**
  `DW-M03` に従い kill として数えず、**冗長な防御分岐**として記録する。
  診断文字列の一致だけを assert して kill を作ることはしていない (同節の禁止)。
- 残る疑問 (sentinel 置換経路で二層変異がなぜ受理へ倒れないか) は本 wave では閉じていない。

## M01 / M06 の MISMATCH は親の登録漏れ

- **M01c**: 期待 7 node が**すべて**赤 (`missing` は 0 件)。超過は
  `test_launcher_failure_diagnostic_reports_failed_predicates` 1 件で、同一理由の consumer である。
- **M06c**: 期待 5 のうち 4 が赤。落ちなかった
  `test_dev_waves_integration.py::test_malformed_child_output_is_output_invalid[oversize]` は
  **1 走目で赤・2 走目で緑**であり、F57 族のフレークとして変異へ帰属しない。

いずれも検出漏れではなく、親が事前登録した node 集合が実際の閉包より狭かった / 広かったことによる。
`DW-M08` の照合は exact 集合一致を要求するため MISMATCH と記録される。**この記録は消さない。**
