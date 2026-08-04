---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: wave-t409-impl-trigger-grammar
seq: 2
---

## 新規

### {{F:parallel-wave-premise-supersession}}. 並行 wave の land が実装 wave の裁定前提を覆し、完成した実装を捨てた [手順漏れ] [ドリフト]

- 事象: [T-409] の実装 wave が全緑まで到達した後、走行中に main へ着地していた並行 wave [T-428] が
  同じ攻撃面 (trigger 軸の hole 受理) を、より強い閉集合検査へ置き換えていたと判明した。
  裁定 5 件すべての前提が消え、49 ファイル・1170 行の実装を land せず裁定へ返した。
- 根本原因: 既存の規律は「着手前に main を確認する」「wave 中は main を定期確認して都度マージ」だが、
  どちらも**テキスト衝突**の予防を目的としている。今回の衝突は意味的で、
  `git log` の subject を読んでも「T-428 = reflux wiring」からは同じ攻撃面とは読めなかった。
  マージを試みて 14 conflict が出るまで検知できなかった。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O23` に、land 直前の main 監査で
  「本 wave の攻撃面・受理集合・裁定前提を変える commit が入っていないか」を、
  subject でなく**変更 path の交差**で判定する義務を追加した (本 wave で同節を是正)。
  交差があれば land せず前提を再評価する。
- 再発検知: 段 9 の land 前に、wave の変更 path 集合と `HEAD..main` の変更 path 集合の交差を
  列挙する。交差が空でなければ停止して前提を再評価する (`DW-O23` の手順)。
