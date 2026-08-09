---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t673-transition-pbt-package
seq: 1
title: [T-673] 量化縮退への検査方式を実測して裁定へ返した — PBT は依存ゼロの stdlib 生成と frontier が完全一致し、hypothesis 固有の追加検出力は観測されなかった (docs のみ、変異 distinct 14 種 / ledger 92 件・事前登録不一致 0、branch worktree-dev-wave-t673-transition-pbt-package)
---

## 本文

- **ユーザー指示どおり本番コードを 1 byte も編集していない。候補テストも land していない。**
  land したのは docs fragment と insights だけである。候補テスト 5 本 (562 行) は
  probe commit `3912c7fc` (side branch `worktree-dev-wave-t673-probe`) にあり、
  **land 対象 branch の祖先ではない** (`git merge-base --is-ancestor` で機械確認)。
- **測定の中心的な結果は「hypothesis を入れても、依存ゼロの stdlib 生成テストと frontier が
  1 マスも変わらなかった」ことである。** ともに N ≤ 63 を検出し N = 64 を見逃す。
  ただし B2 の frontier は `@example(env_count=64)` が単独で決めており、
  shrinking や多軸探索を含む **PBT 一般の効用を測ったわけではない**。この限定を落とすと
  「PBT に価値がない」という誤った一般化になる。
- **段 6 の焦点再レビューが裁定パッケージへ NO-GO を出し、親は推奨を後退させた。**
  前版は「現状維持 + trigger」を推奨していたが、依存ゼロで frontier を広げる A′ / B1 と、
  本番編集禁止で未測定の D を比較せずに現状維持へ誘導していた。
  改訂版が断定するのは **「B2 を今 land する根拠は無い」まで**で、A / A′ / B1 / D の優劣は
  親が決めずユーザー裁定へ回した。
- **親自身の誤りを 4 件、子が反証して是正した。** (i)「dispatch は tracked 限定コピーだから
  probe は commit が要る」は誤りで、非変異のコスト測定なら repo 外 probe を絶対 path で走らせられる
  (段 3 レンズ A)。(ii)「現行本番では遷移検査が一度も呼ばれない」は言い過ぎで、
  発行 tool の publish 経路は今日でも発火し、実 serial 2 が commit `677d0952` に存在して
  land 待ちである (段 6 レンズ C / D)。(iii) C1 負制御の事前予測 3 件 (事前 slice・`del`・decoy) が
  誤りで、実際は C1 が検出する。(iv) C1 の「変数 rename」負制御が定義側を残した壊れた変更だった
  (段 6 焦点再レビュー)。**(iv) は測り直したが結論は変わらず、意味保存 3/3 で C1 は赤のままだった。**
- **`[T-627]` の記録に erratum がある。** worklog 2026-08-08 (318) は `changed[:1]` の 10 node を
  「semantic 3 / diagnostic 7」と記録したが、**正しくは semantic 5 / diagnostic 5** である。
  後段の非 bool と例外の 2 件も受理集合を変える意味的検出であり、診断 pin ではない。
  根拠は同 wave 台帳 `mutation-ledger-v3.json` の M4 の `failed_nodes` の実読。
- **事前登録は全 92 件が実測と一致した (MISMATCH 0)。** 親が probe 本文と production を読んで
  導出した期待 node 集合が、G 側の切り詰めが P 系 node の witness も消すという因果を含めて
  全件当たった。distinct な変異は 14 種類で、それを 7 つの scope / 候補へ適用した結果が 92 件である。
  **「92 種類の変異を試した」ではない** (段 6 焦点再レビューの指摘で表記を是正)。
- **実行時間はどの候補でも順位が付かなかった。** pytest 報告 session 時間は候補すべて
  2.37〜2.45 秒 (単発)。ただし反復も分散も取っておらず、end-to-end は 21.8〜26.9 秒である。
  「差が無い」とは書けない。少なくとも「M を 64 まで掃くと重い」という懸念を支持する兆候は無かった。
- **段 3・段 6 の敵対レンズ 4 本 + 焦点再レビュー 1 本が、いずれも実質的な所見を出した。**
  レンズを model 混成 (sol / luna) にしたことが段 3 で効き、段 6 は同一 model 2 本でも
  測定器の欠陥 (C3 の恒真化条件、B2 の collection 汚染、sibling import の誤束縛リスク) を出した。
- 上記 (iv) は新しい F を採らず **F29 の再発**として記録した
  (「正しく測ったが測定対象が命題と違っていた」型の 3 度目)。
- 一次資料 = `output/insights/2026-08-09_t673-transition-quantifier-ruling/`
  (裁定パッケージ、段 1〜6 の全子出力、変異 spec 7 本と台帳 7 本、親測定器の逐語出力、
  候補テストと測定器の逐語 + SHA-256)。

## 次の一手差分

### 更新

- [T-673] **P2・ユーザー裁定待ち**: 遷移述語の量化縮退に対する検査方式の裁定パッケージを
  実測付きで返した (`output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md`)。
  実測が断定するのは「B2 (hypothesis) を今 land する根拠は無い」までで、
  A (現状維持) / A′ (fixture 8 env 増量) / B1 (stdlib 生成) / D (本番側の走査完全性 guard) の
  優劣は未決。裁定していただきたいのは (1) A / A′ / B1 / B2 のどれを採るか、
  (2) A を採る場合の再裁定 trigger と所有者・機械的発火面、(3) D を別 wave で測ってよいか
  (本番編集禁止は今回限りか恒久か)、(4) E (変異 spec の恒久登録) の採否、
  (5) G (loader / issuer への integration pin) の起票可否、(6) 候補テスト 5 本の保存方式
  (再生成でよいか side branch を保持するか)。
  base: 4d42f4c43fe3879f1b33814f1694f8f426be90297cc31afcf0d6de06bd74d18b
