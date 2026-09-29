---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-gen-opt-literature-cards
seq: 2
---

## 新規

### {{F:subagent-source-from-fork}}. 原典読みの子が論文の公開 source を第三者の fork から取った (near miss) [手順漏れ]

- 事象: 2026-09-29 の文献カード wave (gen-opt md_2) で、Polaris (SIGMOD 2023) の本文を取れなかった子が公開 source に切り替え、原典 repo (`chenhao-ye/polaris`) ではなく 2026-09-18 作成の第三者の fork (`ssya23/polaris`) から README と source 2 file を取ってカードを書いた。親が GitHub API の `fork`・`parent` で気づき、原典 repo の同じ 3 file と SHA-256 が一致することを確かめてカードの出典を直した (中身は同一で実害なし)。
- 根本原因: 子への指示が「公開 source を読む」だけで、repo が原典かどうかを確かめる手順を持たなかった。検索で先に現れた repo をそのまま使った。
- 恒久対応: memory `paper-source-must-come-from-upstream-repo` (子の prompt に原典 repo の指定と fork 判定を書く、親が API の `fork`・`parent`・`pushed_at` を見て SHA-256 を照合する)。
- 再発検知: 子の報告に GitHub repo 名が出たら、親が API の `fork` を 1 回確かめる (記録は insight の取得記録)。

## 再発

### F1

- **再発: 2026-09-29** — gen-opt md_2 wave の親が、検索の事前登録 file の改訂 1・2 と handoff に書いた時刻 (09:52・10:40・10:45) を `date` で測らず推定で書き、実時刻 (改訂 1 は 09:49〜09:50、改訂 2 は 10:06、handoff の該当時点は 10:01) と最大 39 分ずれた。file の mtime で気づき、登録 file は本文を書き換えず末尾へ訂正を追記した。恒久対応は既存どおり、時刻を書く 1 回ごとに `date` か mtime を取る。事前登録の改訂のように後から書き換えない記録には、`date` の出力を同じ command で埋め込むのが安い。
