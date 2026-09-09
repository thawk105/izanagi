---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2051-b4-prerun-entry
seq: 1
title: [T-2051] 依頼 4 項目のうち 3 項目は着地済みで、実際に空いていたのは裁定済み未実装の D1880 だった — formal bootstrap の manifest membership を閉じた (コード + テスト + insight、branch worktree-dev-wave-t2051-b4-prerun-entry、変異 4 KILLED + 登録 SURVIVED 1・期待 node 完全一致)
---

## 本文

- 一次資料は `output/insights/2026-09-10_t2051-b4-prerun-entry/`。逐語 10 本と変異 spec / report を
  probe / 本走の 2 組ずつ置いた。
- **依頼の前提が着手前に覆っていた。** 4 項目のうち「正式起動口」「不変な writer」
  「§7.1 の全件 report generator」は 2026-08-29 と 2026-09-01 に着地済みで、残るのは
  certified 選択への必須配線 1 項目だった。それは [T-2139] が「現 checkout では完成できない」と
  裁定し、再開条件 4 項目 (無条件 3 + 順方向の場合 1) を残している。今日も 1 件も成立していない。
- **ただし「3 項目着地」という集計は段 3 のレンズ B が refuted にした。** 着地しているのは
  `p3_b4_analysis_path.py` の docstring が持つ 5 語台帳の中での話で、依頼の文言に照らすと
  3 項目とも部分的である。writer は create-only であって不変ではなく、report 生成器は
  成果物自身が `section_7_1_four_classifications_operationalized: false` と宣言し、
  launcher が覆うのは単一 arm の driver 起動までである。
- **実際に空いていたのは裁定済みで未実装の決定だった。** D1880 (2026-09-09) は
  「formal B-4 の母集合を analysis manifest の 201 行に固定する。manifest 外の registry 行は
  hash が一致しても実行しない」と決めているが実装が無く、production コード自身が非保証 tuple で
  `manifest membership は検査しない (裁定パッケージ 3)。` と宣言していた。これを閉じた。
  同じ /rulings 回の D1881 (事前登録が publication root を 1 つ名指しする) も未実装のまま残る。
- **段 3 の 2 レンズが割れ、台帳が決着させた。** レンズ B は manifest membership を実装候補に
  挙げ、レンズ A は「母集合を manifest 201 行にするか registry 全行にするかが未裁定だから
  実装へ送るな」と保留を求めた。親が `docs/decisions.md` を引いたところ D1880 が現に存在し、
  レンズ A の保留理由は refuted だった。**peer の「未裁定」判断も台帳で裏を取る。**
- **停止地点は 6 層 × 3 状態で書いた。** 両レンズが独立に「段 2 plan の L2 は実測でなく静的予測」と
  指摘したので、`observed stop` / `unreached` / `static expected rejection` を区別した。
  実測した停止点は層 1 だけで、`p3_b4_launcher.py bootstrap` の実走が
  `[admission-record] record is unavailable` rc=1 を返す。層 2〜6 は入力を作っていないので
  `unreached` であり、拒否実績として記録しない。
- **母集合の実数を測った。** 3 driver の loop campaign の whiteboard は success 7 / rejected 0。
  別 campaign の rejections digest に赤が 3 件あるが whiteboard を持たず適格性を満たさない。
  したがって赤 precursor は「0 件」ではなく「最大 3 件、適格確認 0 件」で、要求は 201 件である。
  `campaign.lock` の `b4_reflux_ablation` marker は 0 件。
- **親 brief の 12 項目を訂正した。** 主なものは、最初の停止点は publication ではなく
  admission record であること、`EXPECTED_BLOCK_COUNT == 201` の機械条件は型付き行であって
  実 precursor file ではないこと、§5 の `未記入` を含む値セルは 6 行でなく 7 行であること。
- **段 6 の敵対レビューが test の実体性を 1 件潰した。** production 実装への must-fix は 2 レンズとも
  0 件。一方、段 5 の負例が loader を monkeypatch していたため「実 loader が受理した publication で
  受理集合が狭まった」証拠になっていなかった。レンズ A が実 issuer で 202 件発行すれば 202 番目が
  manifest 外になると構成を示し、fix で差し替えを撤去した。
- **焦点走の対象集合を親が取り違えた。** 変更 production file の module 名で grep して 28 file を
  得たが、レンズ B が projection closure 経由の間接 consumer 2 件と collection meta-test 1 件の
  漏れを名指しした。`projection_closure_manifest` が `p3_s4_loop.py` の bytes を読むためである。
  31 file へ広げて 3187 passed / 17 skipped / rc=0。
- **セッション異常: 変異 harness の起動で 3 回はじかれた。** (a) runner argv の `-rf` 必須、
  (b) category 語彙に `equivalent` は無い、(c) spec の `timeout_seconds` が dispatch 待機契約
  (queue_wait 3600 + grace 600) より短いと拒否。(c) は D612 の上書きを使うと必ず当たる。
  1 投入で 1 件しか出ないため 3 回投げ直した。
- **焦点走を 1 回取り下げた。** レビュー前に投入した 28 file の走行は、fix 子が worktree を編集すると
  計測が汚染される。対象集合も作り直しになるため `qdel` し、orphan hold の残留が無いことを確認した。
- **エージェント工数:** codex 子 7 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1)。
  全件 `tools/check_codex_output.py` rc=0。read-only の子は pytest を実走していない。

## 次の一手差分

### 更新

- [T-2051] **P2・更新**: 依頼 4 項目のうち「正式起動口」「不変な writer」「§7.1 の全件 report
  generator」は着地済みで、残るのは certified 選択への必須配線だけである。これは [T-2139] が
  所有し、無条件の再開条件 3 件が未成立のため着手できない。本項に残るのは、着地済み 3 項目が
  依頼の文言に対して部分的である点 (writer は create-only、report 生成器は §7.1 の 4 分類を
  実効化しない、起動口は単一 arm の driver 起動までを覆う) をどう扱うかの判断である。
  base: a432d4483a07b08d49dd2557afca6906ebcbf00fecb4ecd19561f4e177065a4f

### 新規

- {{T:b4-publication-root-authority}} **P2・新規**: D1881 (2026-09-09 裁定) を実装する。
  事前登録が publication root を 1 つ名指しし、発行器がそれ以外での発行を拒否する。
  裁定は下りているが実装が無く、現在は呼び手が実行時に root を選べるため、任意の提案に対し
  その hash を持つ registry を別 root へ発行すれば bootstrap 束縛が通る。凍結事前登録へ 1 行
  足す必要があるため、erratum の手順に従う。
- {{T:b4-stale-non-guarantees}} **P2・新規**: 陳腐化した非保証 2 件の扱いを決める。
  `p3_b4_prerun_issuer.py` の `formal_launcher_not_wired_to_require_this_receipt` は、launcher が
  `cd47c4651` (2026-09-09) 以降 publication を必須にしたので偽である。
  `p3_b4_raw_record_producer.py` の「`initial_proposal_sha256` を計算・記録する経路が repo に
  無い」も [T-2101] の再導出実装で前段が偽になった。後段 (束縛は転記に留まる) はなお真で
  ありうる。**後者は材料レポートへ射影される**ため独立の裁定が要る。凍結 receipt field と
  凍結文面なので黙って直さない。事前登録 §7.2 / §10 の「正式 launcher への必須配線も無く」も
  同じ理由で陳腐化している。
- {{T:b4-precursor-population-supply}} **P1・ユーザー裁定待ち**: B-4 の母集合 201 件をどう作るか。
  適格な赤 precursor は現在 0 件で、3 driver の loop 履歴は success 7 件である。事前登録 §5.1 は
  「予算上 n を確保できないなら『記述統計に留め有意性を主張しない』と本書に先に宣言してから
  実走する」という逃げ道を先に用意している。n を下げるのか、precursor の供給源を変えるのかは
  実験設計の判断であり AI が単独で決めない。
