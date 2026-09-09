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
