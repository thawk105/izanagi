---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t139-producer
seq: 1
title: [T-139] producer は実装せず裁定 4 問へ返した — 凍結事前登録 core の内部矛盾と追補 A 不在で入力が揃わない (docs のみ、実装差分なし、受入 7229 passed / 20 skipped、branch worktree-dev-wave-t139-producer)
---

## 本文

- **producer は実装しなかった。コードとテストは 1 行も land していない。**
  段 2 の起草子と段 3 の敵対レンズ 2 本が独立に NO-GO を返し (blocker 計 15 件、重複統合後 11 件)、
  親は全件 real と裁定した (refuted 0 件)。段 4 で `4→7→8→9` へ分岐した。
- **決め手は入力の不在。** PBS 測定本体は追補 A の `a01`〜`a09` (時間予算・待機・driver 引数・
  arm identity・schedule seed) に依存する。これ無しに前置・sink・registry だけを land すると、
  台帳だけが「producer 実装済み」へ進む。両レンズが独立にこれを blocker と判定し、
  worklog (305) の [T-139] 次の一手が記録する順序 (追補 A → producer 実装 → pilot) とも一致する。
- **凍結事前登録 core に内部矛盾を発見した (新事実)。** §14 の閉集合の表は追補 A を `a01`〜`a13` と
  列挙するのに、§15 の投入 gate の要件 5 と「通る正例」は `a01`〜`a12` を基準にする。
  exact-key は欠落も余剰も解決失敗なので 2 つの集合は**互いに素**であり、どちらを実装しても
  他方を満たす追補 A が拒否される。`a13` は **primary 系列の有意水準**であり、`a12` 読みを採ると
  pilot の後に有意水準を選べる状態が残る (絶対規律 3 に抵触)。2026-08-07 の裁定時点で未見であり、
  親が片方を選ぶと受理集合が動くため、`DW-S04` に従いユーザー再裁定へ返した。
- **段 2 案の認可 sink の位置が誤っていた (レンズ B が検出)。** `qsub` を行う関数にだけ binding を
  必須化し、**受領証を実際に書く関数は無認可**のままだった。T-609 が否定した「呼び手側の認可」の
  再現であり、T-643 (i) の「認可の第一境界は producer 側」に照らすと必須引数は永続化する関数に要る。
- **親の誤りが 3 件あった。** (1) brief の「実装被覆 0」は誤り — **D229 決定 (7) が既に「0/9 は過大」と
  訂正済み**の見積りを親が再導入した。正しくは「T-139 固有の public API が 0 件」。
  (2) 成果物影響表の 6 行は追補 A・PBS 本体・publisher 結線・validator caller が揃った後の
  条件付き効果である。(3) `verify_receipt` が検出できるのは producer が書いた 2 文書の食い違いであり、
  実測 checkout の混入ではない。両レンズが (1)(2) を独立に指摘した。
  **親の一般化が段 3 で覆るのはこれで 6 wave 連続**である。詳細は {{F:corrected-estimate-reintroduced}}
- **納品物は裁定 gate への提出物である。** 段 A の記録項目 (受領証 closed schema) の案を、
  敵対検証の指摘 5 系統 (絶対規律 1 の trace/perf 分離、条件付き制約と参照整合性、evidence-only の明示、
  失敗投入を raw に残す authority、認可を実 writer へ) を反映した形で作った。
  記録項目の確定は D229 決定 (7) と事前登録 §11 段 A が定める**単独の裁定 gate** であり、
  2026-08-08 の [T-643] はこれを裁定していない。
- **実装差分がゼロのため変異 matrix は射程外。** 受入全走は [T-642] の裁定 (実装差分ゼロでも
  実 repo を読むテストがあるなら走らせる) に従い実施し、**7229 passed / 20 skipped** (19 分 12 秒、
  計算ノード) で緑だった。走らせた時点では `DW-S04` 本文の射程改訂が未 land だったので裁定の実質に
  従ったが、land 直前の取り込みで [T-642] の改訂本文 (受入全走は免除しない) が入り、結果的に一致した。
  **測った checkout は local main を取り込んだ最終 tree** (docs commit + merge commit) であり、
  同じ値を fragment 追加前の tree でも得ている。
- **docs commit 後の閉じ直し (F34)。** commit 後の tree に対し `check_docs.py` rc=0、
  `spool_fold.py --dry-run` rc=0、影響テスト (`test_check_docs` + `test_spool_fold`) が
  **400 passed・rc=0**。取り込み後は base digest を測り直し、[T-139] / [T-643] の対象 item digest が
  不変であることを確認した。
- **受入全走が 1 度 30 分 walltime 上限で SIGKILL された (99% 到達)。** 別セッションの受入と
  2 本並走していたときである。worklog (306) が記録した同型の既知事象であり、
  本 wave の変更由来ではない (単独で再走したときは 19 分で完走した)。
- **受入全走を 1 度失った。** 最初の走行は detach した dispatch クライアントが 134 秒で外部から
  SIGTERM を受け `rc=16` (infra 失敗) となり、その qdel が計算ノード側 job を 98% 付近で打ち切った。
  walltime 30 分 + grace 300 秒に対して早すぎるので deadline ではない (原因は未特定)。
  detach をやめ harness 管理の background task として再走したら完走した。n=1 ずつなので一般則にしない。
- **親が rc を pipe 越しに読みかけた (F152 と同型)。** 影響テストを
  `... | tail -12` の形で走らせ、`tail` の rc を結果として受け取った。気付いて pipe を外し、
  出力を file へ落として rc を別に取り直した。上記 400 passed / rc=0 は測り直した値である。
- 逐語 = `output/insights/2026-08-08_t139-producer-adjudication/`、
  裁定パッケージ = 同 `package.md`、記録項目案 = 同 `record-items.md`

## 次の一手差分

### 完了

- [T-643] producer 実装 wave を起票して実行し、(i) 認可の第一境界と (ii) trust root の最小形の
  裁定を消費した。実装は入力不在で止めたため、残る作業は [T-139] 側で追跡する。
  remaining: none
  base: 9df1771495c84d385645a7092912e56430681ee4365155a2229967191745a905

### 更新

- [T-139] **P1・ユーザー裁定待ち (4 問) → 裁定後に「追補 A → producer 実装 → pilot」**:
  producer 実装 wave を実行したが**実装しないと裁定**した。入力 (追補 A) が無く、
  凍結 core に内部矛盾があるため。裁定パッケージ 4 問 =
  (Q1) 追補 A の閉集合は `a01`〜`a12` か `a01`〜`a13` か (親の推奨は a13 + §15 を erratum として
  明示 supersede。core の bytes は変更しない) /
  (Q2) D234 の実装境界と事前登録 §11 の段順序のどちらの読みを採るか (親の推奨は、D234 の列挙を
  T-139 全段の完了範囲と限定し、段順序は D162 / §11 に従わせる) /
  (Q3) 段 A の記録項目 (受領証 closed schema) を承認するか (親の推奨は追補 A と同時に裁定) /
  (Q4) 次の producer wave の vertical slice をどこで切るか (親の推奨は追補 A 先行 + 1 本の
  vertical slice = PBS 測定本体・qsub 前 durable intent と台帳・job 側 preflight reject の collector・
  binding を必須化した受領証 writer・end-to-end の正例 1 本)。
  **pilot は依然として投入不可** — 追補 A が無く producer も未実装である。
  次 wave が引き継ぐ設計所見 = 認可は受領証の実 writer へ / 追補 A の study-wide な一回限り束縛 /
  失敗投入の collector / trace-perf 分離の schema 制約 / preflight の source authority /
  段 A 変異 6 件のうち 4 系統の単一理由帰属が不成立。
  正本 = `output/insights/2026-08-07_t139-mainrun-design/preregistration.md` (core)、
  本 wave の逐語 = `output/insights/2026-08-08_t139-producer-adjudication/`、設計判断 = D234
  base: 57eaa1e3b84c4289d0ba113063b9253ac6cc6e2e0631ca1618821ac74cf703a3
