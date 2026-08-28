---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t1941-backoff-requested-us
seq: 3
---

## 新規

### {{F:producer-wait-receipt-collision}}. wait receiptがworker launcher receiptを上書きした [手順漏れ]

- 事象: T-1941 author finalの待機で`dev_wave_wait.py producer --receipt-file`へworker receiptと同じpathを渡し、accepted launcher receiptをproducer receiptで上書きした。
- 根本原因: DW-O01がproducer待ちを要求する一方、2種類のreceipt pathを分離する義務を明記していなかった。
- 恒久対応: `docs/dev-wave/operations.md` DW-O01へwait receiptとworker launcher receiptの別path義務を追加した。
- 再発検知: producer wait投入前に2 pathの文字列不一致を確認し、完了後にworker receipt schemaを照合する。

### {{F:compound-preflight-continued-after-red}}. compound shellがpreflight赤の後もcommitへ進んだ [手順漏れ]

- 事象: T-1941 implementation commitで`git diff --cached --check`が赤だったが、同一shellが`set -e`無しで後続provenance/commitを実行した。
- 根本原因: DW-O17の「赤なら止める」を、複数commandを含むshellの終了制御へ写像していなかった。
- 恒久対応: `docs/dev-wave/operations.md` DW-O17へcompound shellの先頭`set -e`、またはtool call分離を追加した。
- 再発検知: commit前tool callの先頭と実行結果を確認し、preflight非0後にHEADが進んでいないことを照合する。
