---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2199-s4-loop-pegasus-build
seq: 3
---

## 新規

### {{F:path-wrapper-changes-acceptance-set}}. code file を 1 byte も変えない PATH wrapper が、判定器の受理集合を変える案として起草された [計測汚染] [恒真ゲート]

- 事象: 段 4 loop のビルドを Pegasus で通すため、段 2 のプランが「job-private な `cmake` wrapper を
  PATH の先頭に置き、configure 時だけ pin 済み `FETCHCONTENT_SOURCE_DIR_*` を注入する」案を出した。
  親 brief 自身も「`condition_meaning_gate.py` を変えずに環境側で解く」を provisional 裁定に
  していた。段 3 のレンズ A が real 所見として反証し、親が段 4 で不採用にした。**実装には至って
  いない (near miss)。**
- 根本原因: condition gate は `cmake` を PATH から解決して実行し、その出力
  (`compile_commands.json`) を受理判定の入力にする。ところが gate の green record は
  **CMake の path も wrapper の hash も実効 configure argv も保存しない**
  (`condition_meaning_gate.py:1402-1415, 1479-1490, 2064-2085`)。したがって wrapper は、
  source-dir・compiler launcher・任意の `-D`・compile entry そのものを差し替えられるのに、
  証拠には現れない。**「code file を変えない」ことを「受理集合を変えない」ことと取り違えた**
  のが誤りの本体である。判定器が環境から実体を解決する設計では、PATH・環境変数・生成された
  入力が受理集合の一部である。
- 恒久対応: 絶対規律 2 (正しさゲートを緩める変異を許さない) をこの型へ適用する
  — 判定器が環境から解決する実体を差し替える案は、差し替えた実体の identity が判定の証拠へ
  束縛されない限り採らない。実行場所の択一としての結論は {{D:s4-loop-stays-on-pegasus}} が持つ。
  **機械的な検出器は無い。** gate 側に wrapper hash と configure argv を束縛する変更が要るが、
  それは本 wave の編集面の外であり、未実装である。この限界は主張せず明記する (規律 7、D387)。
- 再発検知: 「機体 X でビルドを通す」型のタスクで、PATH・`CMAKE_PREFIX_PATH`・compiler launcher・
  interpreter shim を job script 側で差し替える案が出たら、その実体が判定器の入力になるかを先に
  確かめる。入力になるなら、識別子が判定の証拠に残るかを確かめてから採る。
  段 3 の敵対レンズがこの経路を検出した実績がある (本エントリ)。
