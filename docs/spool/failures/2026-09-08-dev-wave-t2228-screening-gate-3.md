---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2228-screening-gate
seq: 3
---

## 再発

### F855

- **再発: 2026-09-08** — 向きが逆の同型。screening 関門へ `-DFETCHCONTENT_BASE_DIR` を渡す
  実装を入れたところ、それを参照しない共有 fixture `condition_meaning_gate/effectuation-ignored`
  に対して CMake が「Manually-specified variables were not used by the project」を stderr へ出し、
  gate が `configure-failed` で赤になった。既存の `preprocess-bytes-identical` 判定に届く前に
  止まるため、負例 test が別の理由で赤になっていた。D1666 は同じ理由で共有 fixture
  `condition_meaning_gate/supplied` へ無害な参照 1 行を入れており、本 wave はそれを
  `effectuation-ignored` へも入れて閉じた。**gate 側は fail-closed で正しく、直すのは
  変数を渡す側か受ける側である**という F855 の恒久対応がそのまま当てはまる。

### F817

- **再発: 2026-09-08** — 段 6 レビュー B の待ち手が producer 生存中に rc=0 で戻り、
  `.done` も成果物も存在しなかった。`DW-C00` どおり `.done` 非空で判定していたので誤判定はせず、
  until ループへ張り替えて正しく待てた。恒久対応は未実施のままでよい。
