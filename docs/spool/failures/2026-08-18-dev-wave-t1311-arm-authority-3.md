---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1311-arm-authority
seq: 3
---

## 新規

### {{F:new-check-preempts-existing-diagnostic}}. 新設 gate が既存診断を奪い、fix が既存テストを壊す方向へ 2 度進んだ [恒真ゲート] [手順漏れ]

- 事象: 新設した digest chain 検査が、wave 前から存在する `[terminal-projection]` /
  `[acceptance-lifecycle]` の診断より先に発火し、それらを pin する既存テストが赤になった。
  fix 子は 2 度、既存テストを通すために誤った方向へ進んだ — 1 度目は同じ検査を新設側へ
  **重複実装**して順序を作り替え (別の既存 key 閉包テストが構造的に必ず赤になった)、
  2 度目は合成 fixture を探索形へ差し替え (`[launch-admission]` の別枝へ落ちて赤のまま)。
  親が 4 巡目に構造を確定し、chain の**呼び出し位置**を既存検査の後段へ移して解いた。
- 根本原因: 新設 gate の「どこで実装するか」と「どこから呼ぶか」を分けて考えていなかった。
  既存検査と同じ変異で同時に成立する gate を、既存検査より前に走る層の内部へ実装した。
  fix 子への指示が「赤を消せ」に寄り、「既存診断の優先順位を保て」を毎回明示していなかった。
- 恒久対応: {{D:new-gate-must-not-preempt-existing-diagnostic}} — 新設 gate は既存診断を奪わない。
  両立しないときは呼び出し位置を移し、**移動後に全呼び出し経路を列挙して被覆を確かめる**。
  既存テストの期待診断の書き換えと、既存検査の新設側への重複実装を禁じる。
- 再発検知: 呼び出し位置を移した gate について、移動前後で「その gate を通る公開経路の集合」が
  縮んでいないことを敵対レビューのレンズに含める (本 wave の段 6 は実際にこれで
  producer 自己検査と CLI からの消失を検出した)。

### {{F:sink-count-taken-from-ledger-not-measured}}. 台帳の「6 sink」を実面数と読み替えた [手順漏れ] [テスト代表性]

- 事象: 台帳項と設計文書がどちらも「descriptor・campaign identity・proposal bytes/path・
  invocation namespace・run-start・terminal report」の 6 面を挙げていたため、親 brief も
  段 2 プランも 6 sink 前提で設計した。段 6 の敵対レビューが、**provider へ実際に送った
  payload / envelope bytes** が 7 番目の面であり未検査だと指摘した。6 面だけを塞いだ状態では
  「台帳・report は off、実 stdin は on」の入力が全検査を通る。
- 根本原因: 列挙が「宣言が現れる面」を数えており、「実行入力が実際に外へ出る面」を数えていなかった。
  親は列挙をそのまま受け取り、実行経路を独立に辿って面を数え直さなかった。
- 恒久対応: 規律 3 (正しさシグナルを後付けにしない) の適用として、
  gate 新設 wave の段 1 で**列挙された面ではなく実行経路から面を導出**する。
  本 wave の insight
  (`output/insights/2026-08-18_t1311-arm-execution-authority/README.md` 2.3 節) が
  7 面の導出手順と、6 面止まりで通るすり抜け入力を逐語で残す。
- 再発検知: 変異 matrix に「各 sink へ digest を流さない producer」を 1 件ずつ登録し、
  面の数だけ KILLED が並ぶことを求める。面が漏れていれば、その面の変異が作れないことで気づく。
