# 段 4 裁定の erratum 1 — 差分定義の変異は等価ではない

段 4 裁定「登録しない変異とその理由」で、親は次のように書いた。

> 「旧世代の key 集合を `現行 - {key}` の差分定義へ戻す」変異は、現時点では**両定義が同じ値を返すので
> 等価変異**であり、KILLED を期待できない。

**これは誤りである。** 実装子は
`orchestrator/tests/test_plot_a2_certification.py::test_policy_generation_key_sets_are_independent_exact_literals`
で、値の一致だけでなく **producer source の AST** を検査し、
`_TRACE0_CONFIGURE_ARGV_KEYS_BY_POLICY_GENERATION` の各値が
`frozenset({...})` の呼び出し (`ast.Call` + `ast.Set` 引数、keyword なし) であることを要求している。
差分定義は `ast.BinOp` になるため、この検査は**構文レベルで落ちる**。

したがって当該変異は等価ではなく、変異表へ M9 として追加する。

| ID | 変異 | 位置 | 狙う nodeid | 期待 |
|---|---|---|---|---|
| M9 | 旧世代の key 集合を `_TRACE0_CONFIGURE_ARGV_KEYS - {"fetchcontent_path_argument_prefixes"}` の差分定義へ戻す | producer の世代表 | `test_policy_generation_key_sets_are_independent_exact_literals` | KILLED |

初回の判断は消さずここに残す (DW-M02)。親の見落としは
「守りたい性質が構文的なら、構文を検査すればよい」という一手を検討しなかったことである。
