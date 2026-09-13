---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: t1912-pair-completeness
seq: 3
---

## 再発

### F35

- **再発: 2026-09-14** — 「機構が存在しない」と主張する carry item が、別 ID の実装 wave に
  よって 2 日後に事実でなくなり、そのまま 40 エントリ運ばれた。従来の 7 形態と違う新しい角度は
  **反証が台帳の中に一切現れない**ことである。carry 本文は否定命題 (「precursor hash・
  on/off receipt・proposal・block id を束縛する manifest と完全性 consumer が要る」) を運ぶが、
  それを崩す実装は別 ID の wave が自分の次の一手だけを書いて着地させたため、carry 側の本文は
  無傷で残った。段 1 で初出エントリ (`docs/archive/worklog-phase3-0827-1008.md:901`) の逐語まで
  当たっても検出できず、崩れたのは段 3 の敵対相談 2 本が実装コードを読んだ後である。
  被害はユーザーの依頼そのものに及んだ — 依頼は「実装する」ことを前提に立ったが、
  `orchestrator/campaign/p3_b4_raw_record_producer.py:2322-2333` の `expected_binding` 完全一致
  要求と `:2366` の照合済み binding からの代入により 4 者の束縛は既に存在し、正例・負例
  (`orchestrator/tests/test_p3_b4_raw_record_producer.py:2063` ほか) も同じ commit
  `227ec68923c8a489be28861c4b2566effe140626` (2026-08-29) に着地していた。
  恒久対応は {{D:stale-carry-falsified-only-by-code}} — 持ち越し項目を対象とする wave の段 1
  前提実測に「その項目が無いと主張する機構の名前で実装側を検索し、着地 commit を
  `git log -S` で確かめる」を含める。**機械防壁は無いままである** — 否定命題の陳腐化を
  検出する検査は台帳側に置けない。
