---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1462-t1464-checkpoint-integrity
seq: 1
---

## 新規

### {{F:codex-jsonl-backslash-unterminated-string}}. backslash付き正規表現リテラルを含むtool出力がcodex JSONL strict parserを「Unterminated string」で落とす [手順漏れ]

- 事象: 段5実装子 (`--stage author`) が `codex_exit_code=0`・392秒・21 model call・
  2004 bytes の完全な出力を生成したにもかかわらず、receiptが`evidence_status=invalid`/
  `outcome=not_accepted`/`launcher_rc=1`になり `-o` の最終成果物が書かれなかった。同waveの
  段6敵対レビュー2本・fix1本でも同型が再発した (合計4回)。
- 根本原因: `orchestrator.codex_roles.events.parse_jsonl`を`attempt-0001.events.jsonl`へ
  直接importして実測した結果、子が`sed`/`git diff`で出力した内容 (親のhandoff・段2プラン・
  実装差分) に含まれる`\x00-\x1f`等の正規表現リテラル (backslash付き) が、command_execution
  イベントの`aggregated_output`へ埋め込まれる際にJSON escapeの整合が崩れ、「Unterminated
  string」でJSON parseに失敗する行が生じた。web_searchの重複key (F217) でも非NFC文字
  (F223) でもない別の trigger — backslashを多く含む正規表現/コードスニペットをtool出力
  経由で読ませると再現しうる。
- 恒久対応: 未実施。当面の回避は `attempt-0001.output.md` を`check_codex_output.py`で検収
  (rc=0なら内容は健全) して`-o`の期待パスへ複製するrecover手順 (F223の回避と同型)。
  恒久対応 (parser側でbackslash-escapeを堅牢化する、または子promptで正規表現を含む大きい
  tool出力を避けさせる) は本waveのscope外。
- 再発検知: `evidence_status=invalid`で`codex_exit_code=0`・成果物`check_codex_output.py`
  rc=0のとき、F217 (`web_search`重複key) でもF223 (非NFC行) でもなければ本F。
  `attempt-*.events.jsonl`を`orchestrator.codex_roles.events.parse_jsonl`へ1行ずつ通し
  `EventValidationError`の`"Unterminated string"`メッセージで特定できる。
