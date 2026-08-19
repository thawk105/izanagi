---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: worktree-t699-cell-parser
seq: 2
---

## 再発

### F223

- **再発: 2026-08-19** — [T-699] の段3敵対相談で、`orchestrator/tests/test_check_docs.py`
  4965〜4976行の `test_placeholder_guard_digest_line_boundary_contract` (非NFC/BOM/制御文字
  fixture、F223が指す4442/4465行とは同ファイル内の別位置) を子が自発的に読み、
  `evidence_status=invalid` で2回連続不採用になった (48/41 model call・625/770秒を浪費)。
  [T-855] の恒久対応 (repo全体の非NFC機械検査) が未実装のため、同ファイルの成長で
  非NFC混入箇所が増える限り同型が再発しうる。今回は prompt へ「この行範囲は絶対に読むな」
  という明示制約を追加する運用回避で凌いだ (3回目で解消)。

### F224

- **再発: 2026-08-19** — [T-699] の変異matrix登録で、`test_dev_wave_dispatch_rejects_...`
  (parametrize 第1引数に日本語`line_prefix`を含む) の期待nodeを `--collect-only` の
  実出力どおりに書いたが、**dispatch relay 経由の実 stdout は非ASCII文字を `\uXXXX` の
  逐語エスケープ文字列として出力する** (F224が指す `unicode_escape` と類似だが、今回は
  collection段階でも実行段階でも一貫して同じ逐語エスケープ形式であり、
  「実ID を collect-only の出力から採る」だけでは解決しなかった —
  Read ツールで読んだ内容が既にエスケープ済み文字列であり、それを spec.json へ転記する際に
  Python の unicode escape として解釈させず**逐語の6/12文字**として書く必要があった)。
  実際の dispatch stdout ファイルを直接読んで文字列一致を確認してから解決した。
