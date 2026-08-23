---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t183-codex-failure-recovery
seq: 2
---

## 新規

### {{F:fork-misacts-as-manager}}. read-only 調査目的の fork が会話全体を継承し自分を manager だと誤認して逸脱行動をとった [誤前提]

- 事象: dev-wave T-183 の段1 brief 材料調査のため read-only 調査専任の fork を起動したところ、
  最終メッセージが依頼した調査結果 (file:line 粒度の6項目) ではなく、
  「forkはまだ実行中です、予約済みの起床まで追加のポーリングはせず待機します」という、
  このセッションの dev-wave manager (親) 自身の待機挙動を模倣した無関係な文面を返した。
  fork は 16 回のツール呼び出し・145,019 tokens を消費しており、調査自体は実行した形跡が
  あったが、最終報告が manager の振る舞いへすり替わっていた。
- 根本原因: fork は親の会話全体 (`/dev-wave` command 本文、9段状態機械、待機・裁定の振る舞いを
  含む) を継承する。依頼 prompt に「read-only 調査専任」という役割記述はあったが、
  「あなたは manager ではない」という明示的な役割**否定**文が無かったため、継承した文脈の
  重力に引かれて自分自身を manager だと誤認し、manager の典型行動 (完了待ちの表明) を
  代わりに出力した。同型の事例が 2026-08 中に既に 2 件発生しており独立再現の閾値を満たす
  (DW-G03)。
- 恒久対応: fork へタスクを委任する prompt には、担当範囲の記述だけでなく
  「あなたは manager ではない。dev-wave の状態機械・段階・待機・裁定には一切関与しない」
  という明示的な役割否定文を含める。memory
  `fork-inherits-command-context-can-misact-as-manager` (Claude 側の恒久対応記録) を
  読み込み契機とする。
- 再発検知: fork の最終メッセージが依頼した成果物の形式 (file:line 粒度の回答等) を満たさず、
  代わりに親自身の言い回し・待機文言を模倣していないかを、親が受領直後に目視で確認する
  (機械検査は fork の自由記述出力の意味を判定できないため、当面は行動規律)。
