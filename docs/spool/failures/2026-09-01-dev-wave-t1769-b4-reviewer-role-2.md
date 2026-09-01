---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1769-b4-reviewer-role
seq: 2
---

## 新規

### {{F:consult-heading-depth}}. prompt が出力形式に深い見出しを混ぜ、完成した子出力が採用 gate で落ちた [手順漏れ]

- 事象: [T-1769] の段 3 敵対相談 A で、子は所見 8 件と対案を含む完成した本文 10727 bytes を
  返したが、最終節を `### 総括` と書いたため `tools/check_codex_output.py` の
  `^## 総括` 要求に掛かり `failure_class=f43_fragment` で不採用になった。子の再投入 1 本
  (初回 wall 289 秒) が無駄になった。
- 根本原因: 親の prompt が出力形式の節を `### 所見` `### 文面の対案` と深い階層で書き、
  最後だけ `## 総括` にしていた。子は見出し階層を全体で揃えて出力するため、深い側へ引かれて
  `## 総括` が出なかった。`DW-O01` の既存規則「prompt に `## 総括` 必須」は満たしており、
  規則を守っても落ちる形だった。
- 恒久対応: memory `codex-child-levels-prompt-heading-depth` — codex 子の prompt では出力形式の
  見出しを全部 `## 総括` と同じ階層で書く。`docs/dev-wave/operations.md` の `DW-O02` へ足す案は
  採らなかった — dev-wave docs の L1.5 byte 予算 9696 を 188 bytes 超過し、空けるには他の
  安全義務を削ることになるためである (超過は実測、`tools/check_docs.py`)。
- 再発検知: 同 gate (`tools/check_codex_output.py` の `--require-heading`) が引き続き
  fails-closed で落とす。検知はもともと効いており、欠けていたのは親側の prompt 規律である。
