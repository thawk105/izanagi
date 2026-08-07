---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t625-waiter-dispatch
seq: 1
title: [T-625] 待ち手規約を条件 dispatch へ載せた — 裁定の 4 要素目は本文にしかなく実装せず返す (コード + docs、受入 7174 passed / 20 skipped、変異 5/5 KILLED、branch worktree-dev-wave-t625-waiter-dispatch)
---

## 本文

- **裁定どおり 3 要素で land した。** 入口の条件 dispatch 表へ key `24` を 1 行足し、
  `tools/check_docs.py` の `CONDITION_DISPATCH_CONTRACT` へ `24 → DW-C00` を追加した。
  `DW-C00` 本文と既存 22 条件は 1 byte も変えていない。入口は 9035 bytes (上限 9500)、
  最長 137 文字 (上限 140) で、予算は引き上げていない。
- **親が裁定を 1 件撤回した。これが本 wave で最も重い出来事である。** 第 3 案の出所
  (T-597 wave 段 6c の焦点再レビュー) には「待ち条件作成」という **4 要素目**があり、
  裁定要約 (裁定 inbox §39、worklog の起票と裁定記録) はいずれもこれを落としていた。
  親は F31 (裁定要約と本文の食い違いは本文を優先) を根拠に 4 要素で実装したが、
  **段 6 のレンズ D が「F31 の射程は既に成立した decision 本文であって、裁定前のレビュー案では
  ない」と反証した。** ユーザーの発話は「推奨通りで」だけで、提示されたのが全文案か要約かは
  資料から判別できない。記録された 3 要素へ戻し、4 要素目は {{T:waiter-rule-fourth-element}} と
  して裁定へ返す。詳細は {{F:pre-ruling-proposal-as-decision}}。
- **親の変異事前登録が 3 件とも誤っていた。** 段 6 のレンズ C が指摘した — (i) M1/M2 の期待 kill
  node に guard case を入れていたが、guard は実入口を読まず契約から合成入口を作るため依存経路が
  ない、(ii) M3 (契約 entry 削除) は実 repo 検査・新 pin・fixture 構築失敗の三重に過剰決定される、
  (iii) M4 を「新 pin だけが殺す」と登録したが、契約だけを変える片側変異では実 repo の
  契約不一致検査も同時に赤くなる。**3 件とも本走前に訂正した** — M1〜M3 を
  `test_real_repo_clean` へ再帰属し、M3 は行重複 (rows=2) へ差し替え、M4 は入口と契約を同時に
  `DW-CTX` へ倒す**二層変異**にした。訂正後は 5/5 が事前登録どおりの node で KILLED になった。
- **M4 と M5 は新テストだけが殺した。** M4 の失敗 node は
  `test_condition_24_contract_pins_exact_target` の 1 件だけで、入口と契約が一致するため既存の
  構造検査は素通りする。M5 も `test_command_guard_case_registration_is_complete` の 1 件だけ。
  ただし `DW-M08` の「新旧両走」は本 wave では**定義できない** — M4/M5 の anchor は変更前の
  木に存在しないため、旧テストへ同じ変異を注入できない。純増検出力の根拠は
  「失敗 node が新テスト 1 件に限られたこと」であり、両走の実測ではない。
- **機械が検査するのは構造だけである。** 条件行の key・行数・参照 pair は `check_docs` が拒否するが、
  **発火条件セルの文言は checker が保持も比較もしない。** 段 3 と段 6 の 2 レンズが独立に
  この穴を must-fix で挙げたが、`docs/skill-self-improvement.md` の「義務本文の文言と意味の保存は
  lint に固定せず、敵対監査と人間レビューで担保する」という明文方針に反するため採らず、
  方針の是非自体を {{T:dispatch-condition-literal-pin-policy}} として返す。
  記録上「発火条件が守られる」とは書かない。
- **効果を後から確認する field がない。** 条件 24 が読まれ 3 条が守られたことを、worklog・handoff・
  task-run・supervisor receipt のどの field からも確認できない。段 6 のレンズ B が指摘した。
  恒久義務化は本 wave の 3 ファイル外なので {{T:waiter-dispatch-observability}} として返す。
- **provenance 全履歴監査は rc=1 だが本 wave 由来ではない。** 新規違反 1 件は既存 commit
  `3f2c43d7` (main の祖先、[T-618] で台帳追加が裁定済み) で、本 wave の commit 範囲
  (`7d705709..HEAD`) は 1 件・違反なしだった。
- **段 5 / 段 6 fix の子は sandbox で pytest を走らせられず (dispatch preflight が rc=16)、
  実走はすべて親が計算ノードで行った。** 子は「実装済み・未実走」と正しく申告した。
- **軽量版を採らなかった。** `check_docs` の受理集合が変わるため `DW-C00` の除外条件に当たる。
  段 2 プラン 1 本、段 3 敵対 2 レンズ、段 5 実装子 1 本、段 6 敵対レビュー 2 本 + fix 1 本 +
  焦点再レビュー 1 本の計 8 子を起動した。

## 次の一手差分

### 完了

- [T-625] 条件 dispatch へ key 24 を追加し、契約とテストを同時変更して land した。
  裁定の 4 要素目は {{T:waiter-rule-fourth-element}} へ分離した。
  remaining: none
  base: aa261be4480315edc7753cb0bfa8347303bf4b44b897e4a7f59911cda156844f

### 新規

- {{T:waiter-rule-fourth-element}} **P2・新規 (ユーザー裁定待ち)**: 条件 24 の発火条件に
  「待ち条件作成」を含めるか。第 3 案の**本文**には 4 要素目としてあるが、裁定 inbox §39 と
  worklog の要約はいずれも落としており、ユーザーの発話「推奨通りで」がどちらを指すか資料から
  判別できない。含める場合は入口の 1 行を差し替えるだけ (byte 増は +21、9056 bytes で予算内)。
  含めないなら、待ち条件を先に確定してから待ち手を作る経路には規約が届かない。
- {{T:waiter-dispatch-observability}} **P3・新規**: 条件 24 が読まれ待ち手 3 条が守られたことを
  後から確認できる field が worklog・handoff・task-run・supervisor receipt のどこにもない。
  最小案は生産者 id・待ち手 id・生成回数・生産者死亡束縛・停止後の孤児数を 1 行で残すこと。
  恒久義務化は複数 producer と consumer に跨るため独立 wave が要る。
- {{T:dispatch-condition-literal-pin-policy}} **P3・新規**: dev-wave 入口の条件 dispatch 表は
  発火条件セルの文言を機械検査しない (parser が保持しない) 一方、`docs/ai-provenance.md` の
  条件表は逐語比較を持つ。段 3 と段 6 の 2 レンズが独立に「文言を変えても通る」を must-fix で
  挙げた。`docs/skill-self-improvement.md` の「文言は lint に固定しない」方針を dev-wave 側にも
  維持するか、provenance 側に揃えるかを決める。
- {{T:s01-ruling-source-scope}} **P3・新規 (段 8 自己改善から)**: `DW-S01` は
  「裁定要約が指す decision 本文を開き、食い違いは本文を優先する（F31）」とだけ書いており、
  「本文」が成立済み decision に限るのか、裁定前の提案文書も含むのかを区別していない。
  本 wave の親はこの曖昧さで 4 要素版を実装し、1 巡の手戻りになった
  ({{F:pre-ruling-proposal-as-decision}})。同節へ「成立済み台帳に限る」を明記するか、
  F の恒久対応だけで足りるとするかを決める。裁定境界に触るため自動是正しなかった。
- {{T:m08-old-run-undefined}} **P3・新規 (段 8 自己改善から)**: `DW-M08` は「テスト強化だけの
  wave は、新テストと変更前 HEAD 版テストの双方へ変異を走らせ、新テストだけが検出する差分を示す」
  と求めるが、**新テストが新設された契約 entry を pin する場合、変異の anchor が変更前の木に
  存在せず両走を定義できない** (本 wave の M4/M5 が該当)。代替の証拠形式
  (失敗 node が新テストに限られたことの記録) を同節へ足すかを決める。
  変異の証拠規律に触るため自動是正しなかった。
- {{T:condition-table-unparsable-row}} **P3・新規**: 条件 dispatch の parser は 3 列未満または
  backtick path 不一致の行を黙って無視するため、人間には key が二義的に見える入口を
  `check_docs` が受理できる。既存 23 key すべてに成立する性質で、本 wave の差分ではない。
  塞ぐか否かを決める。
