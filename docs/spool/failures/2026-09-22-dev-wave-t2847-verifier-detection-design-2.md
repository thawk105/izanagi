---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2847-verifier-detection-design
seq: 2
---

## 再発

### F473

- **再発: 2026-09-22** — [T-2847] の設計 insight で、親が「どの test も被覆していない」案を、`_tmp_trace(...)` の直接の文字列引数だけを拾う自作走査と、読み取り子の「G0 / G1c の巡回は fixture に無い」という報告から書いた。走査は helper で組み立てる trace 文字列を構造的に拾わず、`test_verifier.py` の `_ordinal_witness_trace()` が既に wr だけの巡回を trace 入力で使っていた (呼び出し数も関数定義を含めて 1 件多く数えていた)。段 6 の焦点再レビュー 1 巡目が既存 test を示して訂正し、親は走査を verifier を使う test file 13 本の全文字列リテラルへ広げて再集計した (未被覆 3 → 2)。記録前に閉じ、成果物への波及はない。不在を書く前に、走査が拾わない形 (helper・実行時生成) を 1 行で言う。F473 の恒久対応 (memory `tool-filtered-view-is-not-the-total`) は変更しない。
