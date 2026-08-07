---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t597-budget
seq: 1
title: [T-597] dev-wave 4 文書の予算を重複一本化で 404 bytes 捻出し、[T-592] の裁定済み 4 候補を全件終端した — 「機械が強制するから prose を削る」は 5 blocker で棄却 (コード + docs、受入 7101 passed / 20 skipped、変異 3/3 KILLED (旧テストでは 3/3 素通り)、branch worktree-dev-wave-t597-budget)
---

## 本文

- **主経路 (`DW-M08` の tool pointer 化、−259 bytes) は段 3 の 2 レンズが独立に棄却した。**
  決め手は F95 が「`DW-M08` は正規化を定めるが **harness 自身が持っていない**」と明記し、
  修正 [T-417] が未了であること。実装が満たしていない義務を「実装が担う」として削るところだった。
  F71 の恒久対応欄も、当該 parenthetical が [T-247] wave で「本 F の (a)(b)(c) を指す形」へ
  **意図的に整形されたもの**と記録していた。重複ではなく設計された再掲である。
  `mutation.md` は本 wave で 1 byte も変更していない。
- **差し替えた捻出は「同じ瞬間に必ず読まれる上位互換節との重複」3 件で 404 bytes。**
  ただし `DW-S09` の削除は行き過ぎで、段 6 の 2 レンズが独立に catch-all (成功以外は全て停止) と
  報告項目の「既存 branch」の欠落を指摘した。helper は `not-landed` / `fold-failed` /
  `fold-recovery-failed` / `fold-rollback-failed` / `rejected` も返すのに `DW-O23` は 2 種しか
  規定していない。1 文で復元したところ、今度は成功 status 集合の二重管理という**新しい退行**を作り、
  焦点再レビューが検出した。`DW-O23` 参照へ変えて解消。**規範記述の fix が新しい不整合を生む
  F146 の再発 2 例目・3 例目である。**
- **[T-592] の 4 候補は全件終端した。** 未採録は 2 件だけで、残る 2 件は実測で既に閉じていた —
  pgrep 自己一致は commit `a62be201` で採録済み、期待 node の完全一致は `_observed_status` の
  `failed_keys == expected_keys` で機械化済み (本 wave で pin test を追加)。
- **段 3 の B-1 は「T-597 の起動で T-592 を閉じるな」と主張し、親は線を
  「2026-08-06 裁定束の内か外か」で引いた。** 束内 2 件は採録、束外 (機構名検索・解除条件棚卸し) は
  見送り。前者は出所自身が「新しい T / F を作らない」と書き、後者は発生元 [T-529] wave が
  段 3 進行中の live candidate だった。この線引き自体を裁定パッケージへ返す。
- **焦点再レビューは待ち手規約の dispatch 強度 1 点を理由に NO-GO を出したが、親は land した。**
  段 3 のレンズは「`DW-O01` では land ループで読まれない」、段 6 のレンズは
  「`DW-C00` は wave 開始でしか読まれない」と、**2 つのレンズが別の場所を否定している**。
  親は採録内容自体は裁定どおり完全で、争点は dispatch 強化という増分だと判断した。
  逆の判断もありうるため {{T:waiter-rule-dispatch-strength}} として裁定へ返す。
- **変異 M2 の初回 `PARSE_ERROR` / rc=16 を、最初は共有ノードの外乱と誤判定した。**
  静穏窓 (生存中の予約 0) でも再現し、harness を介さず手で変異を当てても再現した。
  真因は自己参照 — 変異対象が変異 harness 自身なので、fail-closed 分岐を消すと harness が
  abort せず入れ子実行が増え、外側 bounded scope が倒れる。全ファイル走行の赤は
  「検出した赤」と「枠が倒れた赤」の混合で単一理由性を満たさない。初回結果は消さず
  erratum として残し、narrow 走行へ再照準した ({{F:mutation-harness-self-reference}})。
- **待ち合わせの取り違えを 3 回踏んだ。** 残留 `.done` を完了と誤読、起動ラッパーの PID を
  生産者と誤認、を繰り返した。いずれも本 wave が採録した規約 (`DW-O01` の残留 `.done`、
  `DW-C00` の待ち手 3 条) が狙っている失敗そのもので、規約の実効性を書いた本人が実演した形になる。
- **予算の最終値は 25,134 / 25,200 bytes (余白 66)。** 開始時 13 から 66 へ増え、
  その上で裁定済み規約 249 bytes を採録した。上限は変更していない。
- エージェント工数: codex 7 本 (プラン起草 1 + 敵対相談 2 + 実装 1 + 敵対レビュー 2 + 焦点再レビュー 1)。
  実装子は共有計算資源へ届かず rc=16 で未実走を正しく申告し、緑判定は親の実走に置き換えた。
- **段 8 の参照文書への統合はゼロ。** 候補 3 件はすべて既存規則が覆っていた —
  待ち合わせの取り違えは本 wave が採録した `DW-C00` の 3 条が、実装子の rc=16 未実走申告は
  `DW-S05-C` の既存文が、harness 自己参照の過剰決定は `DW-M03` の「過剰決定なら単一理由へ
  差し替える」が既に担っている。新しい知見は routing どおり failures と decisions へ送り、
  dispatch 強度の設計択一だけを裁定パッケージへ返した。予算を新規追記へ使っていない。
- 一次資料 = `output/insights/2026-08-07_t597-dev-wave-budget/README.md`

## 次の一手差分

### 完了

- [T-597] dev-wave 4 文書から 404 bytes を捻出し、裁定済み規約 249 bytes を採録した。
  上限は不変で、余白は 13 → 66 bytes。捻出の根拠は {{D:budget-reduction-by-duplication}}。
  remaining: none
  base: aae696c2b13e36cb2838fe436ae1da227bd5011f959ed455de89f31d3dff1761
- [T-592] 4 候補すべて終端。待ち手 3 条と残留 `.done` を採録、pgrep 自己一致は採録済みと実測、
  期待 node 完全一致は機械化済みと実測し pin test を追加した。見送りゼロ。
  remaining: none
  base: bc536c0ded0ce81d6be0ebf3d52ad08e18816314f5a451d9eddd06e51ebcb5fd

### 新規

- {{T:waiter-rule-dispatch-strength}} **P2・新規 (裁定待ち)**: 待ち手規約 3 条を
  `DW-C00` に置いたが、wave 開始時にしか dispatch されない。段 3 は `DW-O01` を、
  段 6 は `DW-C00` を否定しており、**2 レンズが別の場所を否定している**。
  焦点再レビューの第 3 案は「文は `DW-C00` に残し、条件 dispatch へ『背景 producer・待ち手の
  生成/再利用/停止、通知処理の直前に `DW-C00` を再読する』を足す」。入口の条件表と
  `check_docs.py` のハードコード表・対応テストの同時変更を要する契約変更のため実装せず返した。
- {{T:mutation-rf-effective-option}} **P3・新規**: `tools/mutation_harness.py` の `-rf` 検査は
  token の存在しか見ず、後勝ちの `-rs` で FAILED summary が消える経路を防がない。
  prose 保持でも塞がらず、実効 option 解析が要る。塞ぐか否かを決める。
