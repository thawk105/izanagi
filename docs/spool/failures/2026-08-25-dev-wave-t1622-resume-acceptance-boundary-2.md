---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1622-resume-acceptance-boundary
seq: 2
---

## 新規

### {{F:mutation-double-launch-nondeterministic}}. 二重起動の変異が非決定的で、期待 node の完全集合を確定できなかった [観測] [手順漏れ]

- 事象: 受入待ち手の launcher 起動行を 2 回に増やす変異 (`launcher_session = launch(...)` の直前へ
  同じ `launch(...)` を挿入) を登録し、probe と本走で観測 node が食い違った。probe では 7 node
  (新設 E2E 1 + 既存待ち手テスト 6) が落ち、同一 spec・同一 HEAD の本走では 2 node しか落ちず、
  **新設 E2E は本走で緑だった。** `DW-M08` の「期待 node は完全集合」に対し MISMATCH となった。
- 根本原因: 二重起動は競走である。1 回目の `launch()` が返す session を捨てて 2 回目を走らせるため、
  1 回目の子 process がまだ生きているかどうかで結果が変わる。launcher は log file を
  `open("xb")` で排他生成するので、2 回目が先に進むか 1 回目の後始末が先かで失敗理由も落ちる node も
  変わる。**変異が単一理由性を持たない** (`DW-M03`)。
- 恒久対応: `DW-M01` の「単一理由へ絞れない変異は登録せず実効 gate へ再照準する」に従い、
  同じ性質 (runner がちょうど 1 回起動される) を決定的に測る形へ差し替えた。
  `tools/acceptance_launcher.py` の `_run_blob()` で、同一の log stream を開いたまま
  runner subprocess を逐次 2 回実行する変異にする。競走が無く、child counter が
  2 行になることで新設 E2E が決定的に落ちる。初回の非決定的な結果は erratum として本項に残す。
- 再発検知: 変異の期待 node が probe と本走で食い違ったら、まずその変異が競走を含むかを疑う。
  同一 spec・同一 HEAD で node 集合が変わる変異は登録し直す。

## 再発

### F24

- **再発 (near-miss): 2026-08-25** — 完了を中間状態から推測する同型が、**監視 harness 自身の
  完了通知**という新しい面で出た。`tools/dev_wave_wait.py producer` を背景 job として起動すると、
  producer が生存し `.done` も未作成の時点で harness が「completed (exit code 0)」の通知を返す
  事象を 1 wave 中に 5 回観測した (段 3 の 1 本、段 6 の fix、変異 probe 2 回、`until [ -f done ]`
  ループ 1 回)。通知の出力 file は空で、`pgrep` では codex / harness の子が生存していた。
  **F24 の恒久対応 (`.done` の存在 + exit code だけで判定) がそのまま効き、実害はゼロ**である。
  通知を完了判定に使っていれば、成果物 0 bytes のまま次段へ進んでいた。
  本追記は、恒久対応の射程が log 本文 grep・`-o` 出力ファイルだけでなく
  **harness の完了通知そのもの**にも及ぶことを記録する。`DW-O01` の
  「完了は `.done` と exit code だけで判定し、grep も通知も判定にしない」は既にこれを禁じており、
  新しい規則は要らない。
