---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-8c-formal-consumer-wiring
seq: 1
---

## 新規

### {{F:background-completion-notification-without-output}}. 背景 job の完了通知が出力ゼロのまま「完了 exit 0」で返る [偽完了] [手順漏れ]

- 事象: dev-wave の待ち手を背景 Bash (`run_in_background`) で起動すると、**待たずに
  「完了・exit code 0」の通知が出力ファイル空のまま返る**事例を 1 セッション中に 5 回超観測した。
  `Monitor` へ切り替えても、`.done` も成果物も存在しないのに
  `SETTLED rc=0 bytes=2637` のような**実測値らしき数値を含む早すぎるイベント**が混じった。
  偽完了を信じた結果、子が編集中の tree を 2 回測って「まだ赤」と誤読しかけた。
- 根本原因: 背景実行の通知経路が producer の実状態と束縛されていない。
  待ち手自体は健全である — 同じ呼び出しを**前景**で走らせると
  `timeout 70 python3 tools/dev_wave_wait.py producer ... --max-wait-seconds 60` が
  60 秒待って `rc=70` (timeout) を正しく返した。
- 恒久対応: 完了判定を **3 点照合**に固定する — (1) `.done` が存在し exit code を持つ、
  (2) 成果物が存在し**非空**、(3) producer が **pid file の pid** で死亡している。
  長時間の待ちは**前景の bounded wait** を既定とし、
  `timeout 560 python3 tools/dev_wave_wait.py producer --done-file ... --artifact-file ...
  --pid-file ... --max-wait-seconds 540` を Bash の 10 分上限内で区切って繰り返す。
  背景通知は「見に行く契機」にはしてよいが**判定の根拠にしてはならない**。
  実体は `tools/dev_wave_wait.py` の producer 待ちと `DW-O01` の
  「完了は `.done` と exit code だけで判定し、grep も通知も判定にしない」である。
- 再発検知: 待ち手が返った直後に 3 点照合を行い、`.done` 不在または成果物が空または
  producer 生存のいずれかなら**何もせず待ち直す**。本 wave では毎回これで弾き実害ゼロだった。
