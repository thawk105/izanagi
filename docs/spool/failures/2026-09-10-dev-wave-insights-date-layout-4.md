---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-insights-date-layout
seq: 4
---

## 新規

### {{F:premature-recoverable-stop}}. 修正可能な検査失敗で作業を終了し、ユーザーへ再開を要求した [手順漏れ] [誤前提]

- 事象: insights整理のauthorが実行ログ検査で未受理になり、親は原因の切り分けや安全な再試行をせず正式停止した。
  自分の途中差分による文書検査の赤も残したまま、ユーザーへ新しい再開コマンドを要求した。
- 根本原因: 「赤のまま次段へ進まない」を「赤が出たら作業を終了する」と混同した。
  F728の既知事象を調査すれば、検査器を緩めずASCII表示で再実行できた。子sandboxのqstat不能も親環境で再確認できた。
- 恒久対応: ユーザー指示を {{D:recoverable-failures}} とし、DW-STOPの自律復旧と正式停止を分離、DW-O01の未受理差分監査を明示。
- 再発検知: 終了判断時に、原因調査・許可範囲の修正・再検証で進める状況でないかを確認する。
  人間の裁定/権限や新しい外部状態が必要という具体的根拠がなければ、再開要求へ逃がさない。

## 再発

### F728

- **再発: 2026-09-10** — fixture読取stdoutが非NFCになりauthorが未受理。receiptのevent_invalidを調べ、
  strict_json_loadsのNFC拒否を再現した。原記録を保持し、ASCII escapeで読む新authorを正常受理した。
  DW-O02へ読取ログを含むNFC義務と原文保持を明記した。原fixtureとログ検査器は変更していない。
