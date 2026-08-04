---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: wave-t244-p1-ir-emitter
seq: 3
---

## 新規

### {{F:dev-wave-child-dies-with-tool-call}}. 背景 job の codex 子を detach せずに起動し、tool call の終了に巻き込まれて消えた [手順漏れ]

- 事象: 段 2 の plan 子を `bash run-stage2.sh` として背景 Bash tool で起動したところ、
  log が 09:41 で伸びを止め、`.done` を残さないまま process が消えた。異常終了の痕跡は
  ログに残らない (SIGKILL されるため)。約 25 分の走行を失って再投入した。
- 根本原因: `DW-O01` は起動形 (`codex exec ...; echo $? > <log>.done` を `bash -c` で包む) を
  規定するが **detach を要求していない**。他の稼働 wave はいずれも `nohup ... &` で detach
  していたが、その差は入口の契約に書かれていない。
- 恒久対応: 背景 job から codex 子を起動する経路を `nohup setsid` で detach する
  (本 wave の `run-stage2.sh` / `run-stage3.sh` / `run-stage5.sh` / `run-stage6.sh` は
  すべて detach 済み)。`docs/dev-wave/operations.md` の `DW-O01` へ背景 job 向けの
  但し書きを足すことを {{T:dev-wave-detach-contract}} で起票する。
- 再発検知: `.done` の不在と process の消滅が同時に起きたら detach の有無を最初に疑う。
  完了判定は `DW-O01` どおり `.done` と exit code だけで行い、process の存在で代用しない。

### {{F:pgrep-matches-parallel-wave-child}}. 生存確認の pgrep が並行 wave の子に一致し、死んだ子を「実行中」と 45 分誤読した [観測]

- 事象: 上記の子が死んだ後、`pgrep -f "codex exec -m gpt-5.6-sol" | head -1` で経過時間を
  測り続けたが、一致していたのは**並行 wave (`wave-t409-evolve-hole-allowlist`) の codex** で
  あった。自分の子は存在しないのに「22 分経過、走行中」と報告し続け、約 45 分を空の待機に
  費やした。`pgrep -af` で全文を表示し `-C` の worktree path を確認して初めて気づいた。
- 根本原因: 同一ホストで複数 wave が同時に走る運用では、model 名や command 名だけの照合は
  一意でない。`DW-M05` は「照合語が待ち手自身に一致しないように」とだけ書き、
  **並行 wave の子に一致しないこと**を要求していない。
- 恒久対応: 子の生存確認は自分の worktree path で一意化する
  (`pgrep -af "codex exec" | grep "<自分の worktree 名>"`)。
  `DW-M05` の照合規則へ「並行 wave の子に一致しないこと」を足すことを
  {{T:dev-wave-detach-contract}} に含めて起票する。
- 再発検知: 経過時間だけを根拠に「走行中」と報告しない。`.done` の不在と、
  **自分の worktree path で一意化した** process の存在の両方を確認する。
