# 段 4 追補裁定 1 — 新 macro 登録に従属する件数の固定値 (2026-09-30)

発端: author-b-1 が報告した `test_condition_meaning_gate.py::test_v1_domain_and_claim_boundaries_are_exact` の赤 (`len(_COMPILE_TIME_BRANCH_MACROS) == 57`、実数 58)。段 4 の不変条件は「固定表への新 entry の追記だけ」を許したが、同じ登録に従属する件数の直書きを列挙し漏れていた。

裁定: real (SILO_ORDER_VARIANT を supply domain と compile-time witness の両方へ 1 つ足したことの直接の帰結で、実装の誤りではない)。次の **件数だけ** を +1 することを許可する。他の期待値・文言・test 名は変えない。

| file | 箇所 (現物の文字列) | 変更 |
|---|---|---|
| orchestrator/tests/test_condition_meaning_gate.py | `assert len(_COMPILE_TIME_BRANCH_MACROS) == 57` | 57 → 58 |
| 同 | `assert len(G.MEANING_SUPPORTED_MACROS) == 58` | 58 → 59 |
| 同 | `assert "supply domain contains the 75 patch-derived defines" in G.__doc__` | 75 → 76 |
| 同 | `"Fifty-seven\nregistered macros additionally have a bounded compile-time witness"` | Fifty-seven → Fifty-eight |
| orchestrator/campaign/condition_meaning_gate.py | module docstring の `the 75 patch-derived defines` と `Fifty-seven` | 75 → 76、Fifty-seven → Fifty-eight (改行位置は test の照合文字列と一致させる) |
| 同 | `independently declared 75-macro supply domain`、`outside the 75-macro domain` (2 か所) | 75 → 76 |

test 関数名 `test_module_claim_names_the_exact_75_define_supply_domain` は nodeid を変えないため据え置く (名前の数字が古くなることは一次資料に記す)。

受理・拒否の含意: 受理集合は SILO_ORDER_VARIANT を supply domain に 1 つ足した分だけ広がる (段 4 で許可済み)。件数の変更はその事実の記述の追随で、他の macro の受理・拒否を変えない。通る正例: `SILO_ORDER_VARIANT=0` の Silo build 要求が supply domain の検査を通る。

並行 wave の注意 (親の統合時に検査): 他の wave も同じ件数を +1 していれば、git は同値の書き換えを 1 回分に畳む。main 取り込み時に両側の数値 literal を突き合わせ、実数と一致させる。
