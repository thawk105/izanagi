---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t329-nextstep-conservation
seq: 3
---

## 新規

### {{F:codex-evidence-nfc-echo}}. repo 内の非 NFC 行を子が raw 表示すると evidence が全損する [コンテキスト浪費] [手順漏れ]

- 事象: 2026-08-16、段 2 のプラン子が
  `nl -ba orchestrator/tests/test_check_docs.py | sed -n '4540,4885p'` で編集対象ファイルの範囲を
  raw 表示した。その範囲の 2 行に**意図的な分解形 `プ` (フ + U+309A COMBINING KATAKANA-HIRAGANA
  SEMI-VOICED SOUND MARK)** が置かれており、echo された内容が event 行に載って
  `evidence_status=invalid` → `outcome=not_accepted` になった。子は codex_exit_code=0 で
  19,127 bytes の完成したプランを書いていたが、930 秒の走行ごと全損した。
- 根本原因: 既知の「codex 出力は NFC でないと全損」は**子が書く出力**についての規律で、
  **子が読んで echo する repo の内容**は別経路である。子 prompt にも入口にも、編集対象ファイルが
  非 NFC 行を含みうるという前提が無かった。当該 2 行はプレースホルダ検査が正規化形の違いを
  digest で区別できるかを確かめる test data であり、**合成形へ直してはならない**。
- 恒久対応: memory `codex-child-must-not-echo-non-nfc-repo-lines` — 子を起動する前に編集対象
  ファイルの非 NFC 行を機械走査し、該当があれば prompt に「その行番号を含む範囲を
  `sed -n 'A,Bp'` / `nl` / `cat` / `head` / `tail` で raw 表示するな」と具体的な行範囲つきで書く。
  本 wave の段 5・6 の全子 prompt はこの形で運用し、以後 1 件も再発しなかった。
- 再発検知: 走査は 1 command で足りる — repo 全体で非 NFC の tracked file は 3 件だけである
  (`orchestrator/tests/test_check_docs.py` と
  `output/insights/2026-08-12_t886-rollout-fastpath/mutation-round1.json` /
  `mutation-round2.json`。後 2 者は同じ test の診断記録)。
  `evidence_status=invalid` かつ `codex_exit_code=0` の receipt が出たら、まず
  attempt の events.jsonl を NFC 検査に掛けて該当行を特定する。
