---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2266-b10-mechanism
seq: 1
title: [T-2266] B-10 の stale 状態を本体論文の入口へ書いた — 機序として書けるのは記述的な会計までで、B-10 は開いたままである (docs のみ、branch worktree-dev-wave-t2266-b10-mechanism、実装面ゼロ・変異 matrix 免除)
---

## 本文

- **成果物の同定を 1 度誤り、段 2 の子を 1 本無駄にした。** 依頼の「材料レポート」を
  `docs/paper-story-backoff/` (backoff 単独論文) と読み、新しい凍結版を全面再導出する計画で
  子を起動した。正解は本体論文 `docs/paper-story/` の見送り台帳 §8 の項目 B-10 で、
  **両系列の文書が「別物であり『backoff の機序』の一語で束ねない」と明示していた** (D1637)。
  曖昧さを解く鍵は依頼文の中の識別子「B-10」だった。詳細は
  {{F:deliverable-identity-not-resolved-before-brief}}。brief を v2 へ書き直して続行した。
- **腐りは延べ 9 箇所・7 命題あり、すべて B-10 一項目に収まった。** 静的 tail の測定完走、
  旧 model の外挿との乖離、待ち方 grid の 3 族 Holm 判定、read-heavy 正式走の完走の 4 系統である。
- **形式の裁定: 新しい日付の版でなく stale 注記を採った。** 段 3 のレンズ B が
  「A-2 も同時に腐っているので 2 項目であり新版が要る」と主張したが refuted とした。
  入口の契約が版に課すのは「版を作るなら全面再導出」であって項目数の条件ではなく、同節は現に
  過去に 2 項目を積んでいる。根拠は {{D:frozen-series-stale-note-holds-multiple-items}}。
  段 6 のレンズ B も独立に closed と判定した。
- **機序の主張上限は D1724 より狭いと裁定した。** 後発の [T-2399] が単一冪則を棄却し
  「『指数関数的な減衰にならない』とは書けない」と明記しているため、D1724 の第 4 項
  (冪則・約 √b・代数減衰) を確定主張として書かない。根拠は
  {{D:static-tail-mechanism-ceiling-narrowed}}。段 3 と段 6 の 4 レンズすべてが独立に同じ点を指した。
- **fix の最中に親が自分で裁定を上書きしかけ、着地前に撤回した。** レビューの是正案をそのまま
  実装して「fig5 の用途制限は新しい attempt があっても変わらない」と書いたが、これは D1645
  (ユーザー裁定) の期限条件つき除外より強い断定である。D1645 の現物を読み直して
  「本節は条件充足を判定していない」へ改めた。詳細は {{F:reviewer-remedy-overrode-a-user-ruling}}。
- **段 8 の自己改善 2 件は共有 docs へ収容できなかった。** `DW-S01` と `DW-S06-C` への追記を
  試したが、L1 が 10,795 bytes (予算 10,625)、L1.5 が 9,941 bytes (予算 9,696) となり弾かれた。
  どちらも単発事故で `DW-G03` (族一般化には独立 2 例) にも掛かるため、恒久対応は memory
  (`deliverable-identity-resolve-before-brief`、`reviewer-remedy-can-override-a-ruling`) へ置いた。
  **上限引き上げは行っていない。**
- **手順のつまずき 1 件。** 段 6 のレビュー子 2 本を `--stage review` に `--reasoning` を付けて
  投入し、argv 検査で即死させた (rc=2)。`DW-C01` が「`--reasoning` は plan / consult で必須。
  他段指定は rc=2」と明記していた既知の罠である。job-id と成果物 path を変えて投入し直した。
- **受入全走は 2 回走らせた。** 1 回目は記録 commit を含む tip (tested main `4dcf07650`、
  tested tip `0c2e84e0c`) で `child-green`、赤 0 件・flake 0 件。その値を insight §7 へ書いた
  commit が 1 回目の tested tip の後に来るため、`DW-O12` に従い land 対象の最終 tip へ
  2 回目を走らせた。受領証はいずれも repo 外の job dir にある。
- 工数: Codex 子 9 本を起動し 7 本が accepted (plan 2 / consult 2 / review 2 / focus 1)。
  model はすべて `gpt-5.6-sol`、effort は全段 `xhigh`。model call は 38 + 28 + 22 + 38 + 27 + 14 + 22
  の計 189。死んだ 2 本の model call は 0。

## 次の一手差分

### 更新

- [T-2266] **P2・機序の記載は着地、残るのは正式な静的 1000 µs 標本 1 点**: 8 点格子の実測、
  13 点較正での歩行 model 再走、旧 model の指数外挿との乖離はいずれも確定済みで、機序の主張と
  限界は本体論文の入口へ書いた (`output/insights/2026-09-09_t2266-b10-mechanism/README.md`)。
  **依頼が挙げた前提 1 件は覆っている** — 「1000 µs は F718 により測定不能」は 2026-09-07 の
  測定時点の事実であり、D1748 が符号化上限を 9999 µs へ広げた後は表現できる。
  ただし**正式標本としての 1000 µs は未取得**で、901〜998 µs の帯も未測である。
  1000 µs を D1813 第 2 段の本格格子の事前登録に含めるかどうかが、この項の残りである。
  base: d418aa4b10a6edf22de418ae6097a24370826171b83141136e196a9e6b1c33c5

### 新規

- {{T:fig5-erratum-expiry-ruling}} **P3・新規・ユーザー裁定待ち**: `figures/fig5_a2_certification_reject`
  の用途制限が D1645 の逐語で「正しい identity で取り直した attempt が出るまで」という**期限つき**に
  なっている。A-2 の新しい attempt の統制稿が repo にある今、この期限が満了したと読める余地がある。
  fig5 は測った対象が違う (`BACK_OFF` の有効/無効) 以上その制限は本来無期限のはずだが、
  **期限条件の書き換えは D1645 の変更**なので AI は行わない。表現は
  `docs/paper-story/README.md` の恒久 erratum 節と `docs/paper-story/figures/README.md` の 2 箇所にある。
- {{T:a2-observed-positive-results-index}} **P3・新規**: A-2 の統制稿
  `docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md` が
  `docs/paper-story/README.md` の results 系列の表に未登録である。2026-09-05 版 §8 A-2
  「採用構成の現行環境での正式判定は無い」の更新も未了。**本 wave は存在ポインタを置いただけで
  結果を評価していない。** main には英語版 `2026-09-09-a2-certification-observed-positive-en.md` も
  着地しており、A-2 側の作業は別途進行している。
