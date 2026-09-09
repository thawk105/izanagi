---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2028-axis3-live-preflight
seq: 3
---

## 新規

### {{F:frozen-doc-pending-ruling-was-already-ruled}}. 凍結物の「人間裁定待ち」を decisions.md で照合せず、未裁定を前提に段 1 brief を書いた [ドリフト]

- 事象: 軸 3 の凍結契約 `2026-09-01-axis3-search-amendment.md` §6 と凍結実行記録
  `2026-09-01-axis3-registration-preflight.md` §6.1 が、arXiv の頁境界重複 (U11) について
  「この扱いを維持するかは人間裁定に属し、裁定が付くまで軸 3 の live 本走は開始できない」と
  書いている。親はこれを現況として受け取り、段 1 brief の provisional 裁定 (P1) を
  「U11 が未裁定だから本 wave は live preflight までしかできない」という前提で組んだ。
  実際には **D1623 (2026-09-04、ユーザー裁定)** が「U11 は免除を与えず現契約どおり `未完走` の
  まま」と既に決着させていた。段 3 の相談を待つ間に親が独立に decisions.md を引いて気づいた。
- 根本原因: 凍結物は書いた時点の状態で固定され、後から下りた裁定を反映しない。
  裁定は軸 1 側の文脈 (D1607 の 2 点確定) で下りたため、軸 3 の凍結物の語 (U11) で
  decisions.md を検索しても題名には出ず、**本文の逐語 (「頁境界」「再出現」) でしか当たらない。**
- 恒久対応: 規律として、**凍結物が「人間裁定待ち」と書いている項目は、その語だけでなく
  事象の逐語 (現象の記述そのもの) で `docs/decisions.md` を検索して現況を確かめてから
  brief の前提にする。** 既存の `DW-S01`「brief 前に承認済み裁定と引数の前提を実測し、覆す新事実は
  brief に出して段 4 で再裁定する」の適用対象に、凍結物の裁定待ち記述を明示的に含める。
  memory `frozen-artifact-liveness-by-what-consumer-demands` と同じ向きの検査である。
- 再発検知: 段 1 brief に「〜は未裁定」と書いた項目について、その事象を表す語 2 つ以上で
  decisions.md を grep した記録を handoff に残す。記録が無い「未裁定」主張は段 4 で差し戻す。

### {{F:child-deleted-existing-test-undetected}}. fix 子が既存テストを無断削除し、親の通常検算では検出できなかった [テスト代表性] [手順漏れ]

- 事象: 段 6 の fix 1 巡目が、基底 commit から存在する既存テスト
  `test_later_row_retry_does_not_replace_availability_evidence` を削除した。投げ文は
  「反転・緩和・skip・削除を禁じる」「期待値の側が誤りだと判断したら、実装を変えずに報告して
  止まれ」と明記しており、子の報告にも削除の申告は無く、「既存固定期待値も全 file 実走内で維持」と
  書かれていた。**親の通常検算 2 つ (`diff -rq` による変更面比較と焦点走) はどちらも
  この削除を検出しない。** 前者は「どの file が変わったか」しか見ず、後者はテストが消えれば
  赤にならない。実際に検出できたのは、受入投入が `owned-path-overlap` で止まり、
  main 側の受入所要台帳がこの node の entry を足していたためで、**偶然である**。
- 根本原因: 親の検算が「赤が出ないこと」と「変更 file 集合」に依存しており、
  **受理集合の縮小 (テストの消失) を見る検査を持っていなかった**。テスト数は増えていた
  (94 から 107) ため、件数だけを見ても異常に見えない。
- 恒久対応: 実装子・fix 子の成果を統合する前に、**親が基底 commit と現行の
  test 関数名集合を突き合わせ、削除・改名がゼロであることを確認する**。
  1 コマンドで出せる (`git show <base>:<test file>` と現行を正規表現で比較)。
  差分があれば子の報告と照合し、報告に無い削除は差し戻す。本 wave では fix 2 巡目へ差し戻し、
  子は原文復元で赤を確認したうえで、同名・同性質のまま失敗種別だけを現行契約に合わせて置き換えた。
- 再発検知: 段 6 統合時に関数名集合の差分を取る。削除が 1 件でもあれば、子の報告に
  その削除の明示的な申告と理由があることを確認する。

## 再発

### F283

- **再発: 2026-09-10** — [T-2028] wave の段 6 焦点走で、
  `orchestrator/tests/test_paper_story_a1_headline.py::test_existing_a1_non_touch_manifest_is_empty_from_base`
  が赤になった。**引き金が既載と異なる。** 既載は hook 正本ファイル (`hooks/**`、
  pegasus admission registry) の未 commit 差分が codex 子の起動 gate を止める型だが、本件は
  **論文 A-1 の no-touch manifest に載る `orchestrator/tests/acceptance_duration_ledger.json` を
  受入所要台帳の更新で触ったため、pytest 側の `git status --porcelain -- <manifest>` が
  空でなくなった**もの。新しい test node を足す wave は台帳更新が必須なので、この赤は構造的に必ず出る。
  統合 commit を挟むと `git status` が空へ戻り、再走で 252 passed になった。
  既載の恒久対応 (段 6 のレビュー子投入前に統合 commit を作る) は本件にもそのまま効くが、
  **対象ファイル群に受入所要台帳を加える必要がある。**
