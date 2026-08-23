---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1376-receipt-ledger-scope
seq: 2
---

## 新規

### {{F:preacceptance-resume-gate-livelock}}. acceptance 直前に session-start resume gate を再実行し、既存の main 取り込み経路を使わず停止した [手順漏れ] [コンテキスト浪費]

- 事象: [T-1376] の stale-main 再開で固定 main を取り込んだ後、acceptance 直前に local main が
  8 commit 進んだ。親は `check_wave_startup.py --mode resume` を再実行して NG を得ると waiter を
  中断し、fresh context へ戻した。この運用を繰り返せば、高頻度 land 下で受入実走 0 のまま
  再開を反復する。さらに同じ shell の gate 非 0 で後続を止めず、起動した waiter を手動中断した。
- 根本原因: `DW-O20` の resume gate を session 開始時の検査でなく acceptance 直前の gate として
  再適用した。一方 `tools/dev_wave_wait.py` の `_run_acceptance_attempt()` は claim 後の behind を
  検出し、`--merge-message-file` の provenance 検査、`merge --no-ff --no-commit`、commit、behind と
  clean-tree の再検査を行ってから acceptance command を起動する。既存の活性経路と外側の運用を
  食い違わせた。
- 恒久対応: 現行の実行面は `tools/dev_wave_wait.py::_run_acceptance_attempt()` と D731/D732 の
  前方 main 取り込み検証を使う。契約の曖昧さは {{T:preacceptance-resume-gate-liveness}} で
  `DW-O20`、checker、subprocess E2E を同期し、同じ誤適用を機械検出する。
- 再発検知: session-start resume gate の成功後に main を前進させ、単一の acceptance waiter が
  fixed message の merge commit を作り、behind=0 と clean tree を再確認して child command を
  1 回だけ起動する subprocess test。fresh-context 停止や child 起動 0 回なら再発とする。
