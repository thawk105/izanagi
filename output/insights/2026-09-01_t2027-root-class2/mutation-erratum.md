# 変異事前登録の erratum — [T-2027] 根クラス 2 (2026-09-01)

`DW-M02` は「初回結果は消さず erratum に残す」と定める。本 wave で照準を変えた 2 件を記録する。

## 1. m02 の anchor が一意でなかった

段 4 の事前登録は m02 の逐語 old を `if len(matches) != 1:` の 1 行としていた。
実装後の現物では**同じ file の 2 箇所**に同じ行が存在する
(`s8b_compiler_input.py:189` と `:1137`)。`DW-M04` の「置換対象が一箇所でなければ停止」に
抵触するので、**直後の `raise` 本文まで含めた 4 行へ anchor を広げて一意化した。**
照準そのもの (current 根の一意性検査を潰す) は変えていない。

## 2. m06 は冗長 gate に mask されるので kill 変異から外し、m06b へ再照準した

**初回の照準 (消さずに残す):** `s8b_compiler_input.py` の
`if is_v3 and current_dependency_prefix_roots is None:` ブロックを削除する単層変異。
段 4 の事前登録では「B3 の唯一の拒否点」と書いた。

**実装後の現物で測ると誤りだった。** この条件を無効化しても、直後に呼ばれる
`_canonical_dependency_prefix_roots(None, ...)` が
`if type(value) not in (list, tuple):` で `"current dependency prefix roots is not a
root sequence"` を送出する。**両者の発火条件は `is_v3` で完全に一致しており、受理集合は
1 bit も変わらない。変わるのは診断文言だけである。**
`DW-M03`「診断文字列だけの赤を kill にしない」と `DW-M08`「受理集合を変えず構造化シグナルだけを
pin する変異は kill でなく diagnostic sensitivity pin へ別枠記録する」に該当する。

**再照準した形 (m06b):** 両層同時変異とし、明示条件のブロック削除と、canonical 化関数へ
入る手前で `None` を `()` として扱うことを 1 つの置換で行う。`DW-M04` の要求どおり
**kill 期待を事前に登録した** — 親の probe で「明示的な空 tuple は受理・`None` は拒否」を
実測済みなので、両層を潰すと `None` が受理へ倒れる。

**実測の結果 m06b は KILLED で、期待 node も完全一致した。** 殺した node は
`test_v3_probe_snapshot_only_rejects_none_root_context` と
`test_v3_none_dependency_context_is_rejected_but_explicit_empty_is_accepted` の 2 件。

## diagnostic sensitivity pin (kill として数えない別枠)

- **m06 (単層):** `None` 拒否の明示条件を削除しても、受理集合は変わらず診断文言だけが変わる。
  この条件の価値は「なぜ拒否されたかが読み手に分かる」ことに限られる。
  **段 6 レビュー B の所見 3 の是正は、受理面では純増ゼロである。**
  経緯は failures 台帳の該当エントリに書いた。

## この記録が主張しないこと

- 登録した 6 変異が焦点 4 file の範囲で kill されることだけを示す。
  gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない (D387)。
