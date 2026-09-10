# [T-625] 待ち手規約を条件 dispatch へ載せた — 材料と逐語

日付 2026-08-07。branch `worktree-dev-wave-t625-waiter-dispatch`。
起点 main `bb824d8b`、実装 commit `8fc73188`、main 取り込み merge `50cc3db6`。
実測環境は Pegasus (テスト・監査はすべて計算ノードへ dispatch。login node の bounded local は
rc=16 で使えなかった)。

## 何をしたか

ユーザー裁定 (2026-08-07 /rulings、第 3 案) に従い、`DW-C00` の待ち手規約 3 条の**文面を変えずに**、
入口 `.claude/commands/dev-wave.md` の条件 dispatch 表へ key `24` を 1 行追加した。
`DW-C00` はそれまで段 dispatch の「wave 開始」でしか読まれず、事故が起きる瞬間 —
背景 producer や待ち手を作る時点 — には届いていなかった。

同時に `tools/check_docs.py` の `CONDITION_DISPATCH_CONTRACT` へ `24 → DW-C00` を追加し、
入口と契約の不一致を機械が拒否するようにした。テストは 3 つ足した。

| 追加物 | 何を殺すか |
|---|---|
| guard mutation case `condition_waiter_deleted` | 入口から条件 24 の行が消えること |
| `test_condition_24_contract_pins_exact_target` | 契約の 24 が `DW-C00` 以外を指すこと (誤配線) |
| `test_command_guard_case_registration_is_complete` | guard case の登録漏れが無検査で通ること |

## 射程 — 機械が保証するのは構造だけである

`check_docs` が検査するのは条件行の **key・行数・参照 pair** である。
**発火条件セルの文言は parser が保持も比較もしない。** 「通知処理」を「常に」へ書き換えても
機械は通す。段 3 のレンズ A と段 6 のレンズ B が独立にこの穴を must-fix で挙げたが、
`docs/skill-self-improvement.md` は「義務本文の文言と意味の保存は lint に固定せず、
敵対監査と人間レビューで担保する」と明文で定めており、方針に反するため採らなかった。
方針の是非自体は裁定へ返した。

**「条件 24 を入れたので待ち手規約が守られる」とは書けない。** 書けるのは
「条件 24 の行が存在し、`DW-C00` を指し、消せば `check_docs` が赤くなる」までである。

## 親が撤回した裁定 (本 wave で最も重い出来事)

第 3 案の出所は T-597 wave 段 6c の焦点再レビューで、そこには発火条件が **4 要素**で書かれていた。

> 背景 producer／待ち手の生成・再利用・停止、通知処理、**待ち条件作成**の直前に `DW-C00` を再読する。

一方、ユーザーが承認した記録 — 裁定 inbox §39、worklog の起票、worklog の裁定記録 — は
いずれも「待ち条件作成」を落とした **3 要素**だった。

親は段 4 で F31 (裁定要約と本文が食い違う場合は本文を優先) を根拠に 4 要素で実装した。
段 6 のレンズ D がこれを blocker として反証した — **F31 が言う「本文」は D71 のように
既に成立した decision であり、裁定前のレビュー案ではない。** ユーザーの発話は「推奨通りで」だけで、
提示されたのが全文案か要約かは資料から判別できない。少数側 (案本文 1 点) を「本文」と呼んで、
一致する 2 点 (裁定 inbox・worklog) より優先したのが誤りだった。

記録された 3 要素へ戻し、4 要素目は独立タスクとして裁定へ返した。失敗台帳へ新規 F として記録した。

## 親が撤回した変異事前登録 (3 件)

段 4 で登録した変異表は 3 箇所とも誤っており、段 6 のレンズ C が本走前に全部指摘した。

| 誤り | 内容 | 訂正 |
|---|---|---|
| 期待 node の誤帰属 | M1/M2 の kill node に guard case を入れた | guard は実入口を読まず契約から合成入口を作るため依存経路がない。`test_real_repo_clean` へ再帰属 |
| 過剰決定 | M3 (契約 entry 削除) が実 repo 検査・新 pin・fixture 構築失敗の三重に当たる | 入口の行重複 (rows=2) へ差し替え、単一理由化 |
| 純増検出力の誤主張 | M4 を「新 pin だけが殺す」と登録 | 契約だけを変える片側変異では構造検査も同時に赤くなる。入口と契約を同時に倒す**二層変異**へ変更 |

**訂正後の本走は 5/5 が事前登録どおりの node で KILLED**、SURVIVED 0、MISMATCH 0。
台帳は `mutation-ledger.json` (repo_head `50cc3db6`、runner-mode dispatch)。

M4 と M5 の失敗 node はそれぞれ新テスト 1 件だけで、既存テストは 1 件も鳴っていない。
ただし `DW-M08` が求める**新旧両走は本 wave では定義できない** — M4/M5 の anchor は
変更前の木に存在しないため、旧テストへ同じ変異を注入する経路がない。
純増検出力の根拠は「失敗 node が新テスト 1 件に限られたこと」であって、両走の実測ではない。

## 受入・検査

- 受入全走: **7180 passed / 20 skipped** (計算ノード、17 分 06 秒、受入形の警告なし)。
  最終 tip での再走値である。記録用の 1 走目 (main 取り込み前、tip `50cc3db6`) は
  7174 passed / 20 skipped だった。
- 焦点走行: `orchestrator/tests/test_check_docs.py` 307 passed。
- `python3 tools/check_docs.py`: 違反なし。
- 変異 matrix: 5/5 KILLED、SURVIVED 0。
- provenance: 本 wave の commit 範囲 (`7d705709..HEAD`) は 1 件・違反なし。
  全履歴監査は wave 途中では rc=1 だったが、新規違反は既存 commit `3f2c43d7` の 1 件だけで
  本 wave 由来ではない。land 直前に [T-618] (同 SHA の既知違反台帳追加) を取り込んだ結果、
  最終 tip では 1720 件・新規違反なし (rc=0) になった。
- 入口予算: 9035 bytes / 上限 9500、最長 137 文字 / 上限 140。引き上げなし。

## 段構成

`check_docs` の受理集合が変わるため `DW-C00` の軽量版に該当しない。
子は 8 本 — 段 2 プラン 1、段 3 敵対 2、段 5 実装 1、段 6 敵対レビュー 2 + fix 1 + 焦点再レビュー 1。
段 5 / 段 6 fix の子は sandbox で pytest を走らせられず (dispatch preflight が rc=16)、
「実装済み・未実走」と正しく申告した。実走はすべて親が行った。

## 逐語

`verbatim/` に段 1〜6 の全成果物を置いた。特に読む価値があるのは次の 2 本である。

- `verbatim/s6-lensD.md` — 親の裁定を blocker で覆したレビュー。
- `verbatim/s6-lensC.md` — 変異事前登録の 3 件の誤りを本走前に潰したレビュー。
