---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2369-stale-carry
seq: 1
title: [T-2369] B-4 対照対 driver は 2026-09-08 に着地済みだった — 実装 wave が自分の carry stub を 完了 にしなかったため 6 エントリ持ち越された (docs のみ、branch worktree-dev-wave-t2369-stale-carry、実装面の差分 0)
---

## 本文

- 依頼は「D1699 は裁定済みで、残るのは driver の設計と実装である」として実装を求めたが、
  **その作業は既に完了していた。** 段 1 の前提実測で覆ったので実装せず、台帳の訂正だけを行った。
- **済の裏取りは 4 経路で取った。** (1) `orchestrator/campaign/floor_pair_driver.py` の履歴に
  `003ef6173` と `47e14a499` の 2 commit があり、前者の件名は T-2369 の原文と逐語一致する。
  (2) `make_measurement_plan` は 1 pair-sample を 2 つの side session に分け、各 session が
  `candidate` と `reference` の両方を持ち、session 内の測定順を HMAC rank で無作為化する。
  役割ごとの別 session ではない。(3) 凍結も効いている — reference 数と D の式は module 定数で、
  loader が spec の statistics へ exact 一致を要求し、plan 生成側にも同じ検査がある。
  旧 schema 識別子を拒否する負例は後続 commit が足した。(4) 事前登録 §11.2 も
  「2 つの side session を作り、各 session の中で候補と参照を 1 回ずつ測る」へ更新済みで、
  docs 側のずれは無い。commit の件名だけでなく挙動と文書の両方で確かめた。
- **持ち越された原因は実装 wave 自身にある。** エントリ 1327
  (branch `worktree-dev-wave-b4-paired-session-driver`) が D1699 を実装したが、
  同エントリの 次の一手差分 で T-2369 を carry stub のまま残し 完了 にしなかった。
  以後の fold が毎回そのまま持ち越し、1403〜1408 まで運ばれた。
  記憶にある「実装 wave が自分の carry を落とさない」型の 2 例目である。
- **依頼が名指しした稼働 wave も既に終わっていた。** 「稼働中の dev-wave-t2316-b4-base-site が
  `p3_b4_launcher.py` と対応テストを編集している」という前提で重複検査を求められたが、
  同 wave は main HEAD に着地済み (worklog 末尾 1408 が完了記録) で、ListAgents にも存在しない。
  本 wave は同 file を 1 byte も触らず、変更面は wave slug で一意な新規 fragment 1 file だけなので、
  稼働 wave との衝突は構造的に起こらない。全 worktree の未 commit 差分を対象語で走査する
  低速 scan も並行して回した。
- **F35 による依存項目の繰り上げ (報告のみ、本 wave では台帳を触らない)。** T-2369 と並ぶ
  「B-4 の実走前に要る」項目 2 件も実測では済に見える。[T-2368] (n = 59 → 62) は事前登録が
  n = 62 を本文に持つ。ただしエントリ 1318 が「失効値 59 が残る」と書いており残存箇所の確認が要る。
  [T-2367] (D1641 第 4 項の理由文の訂正) は事前登録 §5 と §11.2 に D1694 の erratum が入り
  「§11.2 が名指しした専用 driver は実在する」と明記されているが、`docs/decisions.md` の
  D1641 第 4 項本体には「現行の sanctioned CLI ではこの測定を起動できない」がそのまま残り
  追記が見当たらない。**済と断定しない。** 訂正先が事前登録側だけでよいのかは読み直しが要る。
  どちらも本 wave の task ではないので 完了 化せず、ユーザー裁定へ返す。
- **B-4 実走の本当の残りは spec である。** driver は完成し CLI の 3 mode が通っているが、
  凍結 spec の実体が repo に 1 件も無い。driver は spec が HEAD の tracked blob と byte 一致
  することを要求するので、次の一手は「D1641 決定 3 の 12 項目を埋めた凍結 spec を書いて commit し、
  24 時間以上離した 2 window を計算ノードで走らせ finalize する」である。測定自体は
  D1641 決定 2 で既に認可されている。
- **エージェント工数:** 子ゼロ。実装面の差分が無く docs-only のため、段 2・3・5・6 の
  codex 子を起動していない。段 1 の前提実測だけで依頼の前提が覆った。

## 次の一手差分

### 完了

- [T-2369] D1699 の対照対 driver は 2026-09-08 のエントリ 1327 で着地済みだった。
  candidate と reference の 1 session 形、reference 数と D の式の凍結、事前登録 §11.2 の整合が
  いずれも現物で確認できたので、本項を閉じる。
  remaining: none
  base: 3097791c5c3177797b9df474999f4281dbe0454efc2fbd6a4a85daf9f2bf9a3c
