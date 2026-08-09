---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t313-read-budget-gate
seq: 3
---

## 新規

### {{F:range-marker-over-expansion}}. dispatch の範囲記法が注記・URL の `~` でも展開し、読了 edge を捏造していた [恒真ゲート]

- 事象: `tools/check_docs.py` の dispatch 表 parser は、隣接する 2 つの節 token の間に
  `〜` または `~` が**一文字でも**あれば範囲記法とみなして中間の節をすべて展開していた。
  そのため `` `DW-G01`（説明〜補足）, `DW-G05` `` や `` `DW-G01`（https://x/~u）, `DW-G05` `` のように、
  人間には 2 節の列挙にしか見えない表記でも、checker は `DW-G02`〜`DW-G04` を
  **読了済み edge として生成**した。必須参照集合の充足検査はその捏造された edge で緑になる。
- 根本原因: 範囲判定が `re.search(r"[〜~]", between)` の部分一致で、
  token 間文字列全体に対する完全一致でなかった。範囲記法は「区切り」であって
  「どこかに現れる文字」ではない、という区別が実装に落ちていなかった。
- 恒久対応: 範囲 delimiter を `re.fullmatch(r"[ \t]*〜[ \t]*", between)` 相当の完全一致に限定した
  ({{D:dev-wave-layer-read-budget}} の両方向照合の一部)。
  `docs/dev-wave/**` の層予算はこの edge 集合から導出されるため、捏造は予算値も歪めていた。
- 再発検知: `orchestrator/tests/test_check_docs.py` の負例
  `test_dev_wave_dispatch_rejects_range_marker_inside_annotation` と
  `test_dev_wave_dispatch_rejects_ascii_tilde_inside_url`、および正規の
  `` `DW-O01`〜`DW-O06` `` が引き続き展開されることを固定する正例。
  いずれも fails-closed のテストで、変異 matrix の M04 が同 node を KILL する。
