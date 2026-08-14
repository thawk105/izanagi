---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-backlog-triage
seq: 2
---

## 新規

### {{F:update-item-carry-stub}}. spool fragment の `更新` 節へ carry stub を本文として書き、元本文を消しかけた [恒真ゲート] [手順漏れ]

- 事象: 「次の一手」658 件の棚卸し wave で 52 件を `更新` する fragment を生成した後、main を取り込んだ。
  取り込み後の worklog では大半の item が `- [T-NNN] (553)` の carry stub になっており、
  生成器がその stub を「item の現本文」として読んで `更新` の本文に据えた。
  そのまま land していれば、52 件の実体本文が 1 行の参照へ置き換わって失われていた。
- 根本原因: `更新` は item を**置換**する操作であるのに、本文の取得元を
  `_extract_latest_active` の `block` (= 末尾エントリの見た目の行) に取っていた。
  carry 鎖を解決した実体本文と、末尾エントリの描画行は別物である。
  `base:` の照合は carry 解決後の digest で行われるため**照合は通り**、
  `tools/check_docs.py` も `tools/spool_fold.py --dry-run` も緑のままだった
  (どちらも「本文が stub であってはならない」を検査しない)。
- 恒久対応: memory `spool-update-body-must-be-carry-resolved` — `更新` / `完了` の本文は
  carry 鎖を解決した実体から作り、末尾エントリの描画行を使わない。
  機械化 ({{T:update-item-stub-lint}}) を起票済みで、そちらが land すれば規律から lint へ移る。
- 再発検知: 現状は目視のみ。{{T:update-item-stub-lint}} が
  「`更新` item の本文が carry stub 形式に一致したら赤」を `check_docs` へ入れる。
  親が本 wave で気づけたのは、生成後に無変更 carry の一覧を出力して目視したためである。
