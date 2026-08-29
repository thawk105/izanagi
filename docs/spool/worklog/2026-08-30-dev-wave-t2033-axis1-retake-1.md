---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-30
wave: dev-wave-t2033-axis1-retake
seq: 1
title: [T-2033] D1207 に従い軸 1 検索契約を改訂し、追跡された取得器・検査器で取り直した (code + docs + insight、branch worktree-dev-wave-t2033-axis1-retake、変異 12/12 KILLED)
---

## 本文

- D1207 の 4 面をすべて契約の改訂で閉じた。条件 3 は索引ごとの実要素数、条件 4・5 は索引固有
  work ID と work-family の二層、`AX1-Q6@arxiv` と OpenAlex `Q3`/`Q6` は結果を見る前に固定した
  非重複の日付 shard と新しい query ID、中断した取得には D1183 の再開点。**宣言的除外へは
  1 枝も倒していない** (D1155 の `Q6@dblp` だけを維持)。
- 契約は `docs/related-work/claim-survey/2026-08-29-axis1-search-amendment.md`、実行記録は
  `docs/related-work/claim-survey/2026-08-30-axis1-search-execution.md`。旧凍結物の bytes は
  128/128 path で不変 (D1208)。
- 実装は追跡された取得器・検査器・3 schema・生成された query program (267 論理 ID、
  HTTP を出す leaf 263 本)。事前登録した 12 変異は最終 commit で **12/12 KILLED、期待 node 92 件
  完全一致**、baseline PASSED。焦点走は 95 passed。
- **依頼文の前提 1 件が実測と食い違った。** 旧走行で完走した DBLP は 12 本ではなく 10 本で、
  `T05` と `T07` はハイフンの解釈照合で落ちていた。改訂した期待 echo (索引の実測トークン化) で
  2 本とも完走した。**どちらの期待値を正とするかは決めず、実行記録が両方の判定を併記する。**
- 実走で **D1207 が列挙していない面が 2 つ出た。** (1) arXiv が頁境界で同じ work ID を 2 回返し
  つつ総件数では 1 回しか数えないため、条件 5 が落ちる (2 枝)。(2) OpenAlex が `or` グループ内と
  グループ間の順序を正規化して返すため、登録順のままの構造比較が落ちる (78 枝)。
  **(2) は登録した期待値と実応答が 78/78 で順序を除いて完全一致しており、取得自体は成功している。**
  結果を見た後なので**どちらも述語を緩めず未完走として記録した。**
- **親の事前 probe の不備を記録する。** 契約 §4.4 に載せた中立語の複合 filter probe は、
  使った語がたまたまアルファベット順だったため OpenAlex の正規化を露見させなかった。
- **検査器が実機で自分の欠陥を 3 件捕まえた。** 応答保存後に失敗した attempt の evidence 欠落、
  checkpoint prefix 復元の attempt 選択、部分 bundle での検証打ち切り。いずれも検査器を緩めず
  writer / validator を直した。設計判断は {{D:quota-pause-precedes-predicate-failure}} と
  {{D:partial-evidence-bundle-must-verify}}、索引別の照合は {{D:openalex-echo-compared-as-structure}}。
- 段 3 の敵対相談 2 本と段 6 の敵対レビュー 2 本は real 所見 20 件を返し、closed 14 / partial 6 /
  regressed 0。焦点再レビューが残 5 件を出し、それも閉じた。fix は 5 巡 (うち 3 巡は親が実機で
  観測した blocker で、DW-O16 の 3 巡上限とは別枠)。
- 実走は登録 263 leaf 全数を検証し、**arXiv 171 完走・DBLP 12 完走・OpenAlex 0 完走**。
  索引固有 work ID の distinct 数は arXiv 31,500 / DBLP 4,479 / OpenAlex 200、和 36,179
  (work-family 統合前)。**軸 1 は `未完走`、成熟度は `RW1` のまま。**
- OpenAlex の完走には契約上 5 日以上かかる (1 走 431〜519 リクエスト、独立第 2 走を含め
  811〜955、無償枠 100/日)。**本 wave で軸 1 が完走することは初めからない。**
- record の判定、work-family 統合、control、補助探索、感度監査は 1 つも実行していない。
  未実装 schema 層が 5 つある限り、検査器が導出する `axis_complete` は必ず偽になる。
- 一次資料は `output/insights/2026-08-29_t2033-axis1-retake/`。

## 次の一手差分

### 完了

- [T-2033] 完走述語の条件 3 を索引ごとの実要素数の定義へ改め、実データで効くことを確かめた。
  旧契約なら条件 3 が落ちる形 (宣言 64・容量エコー 200・実要素数 64) が 6 条件すべて可で完走した。
  remaining: none
  base: 6ad42e4b023033e55b05944c1016a43402492f10638fb45d147d1332daf966f5
- [T-2034] 取得完全性を索引固有 work ID で数え、正規化主キーの重複を work-family 層へ分けた。
  取得層での family key による先行 dedup を条件 4 が拒否する。変異 M4・M5 で裏打ちした。
  remaining: none
  base: 620dc769a88f84c168e77b1b52cc230e4f2ed7b37fcf23311d3f9c4fe08fb76c

### 更新

- [T-2035] **P2・実装済み・取得継続中**: 結果を見る前に固定した非重複の日付 shard と新しい
  query ID を登録し、`AX1-Q6@arxiv` は 168 shard 中 166 を完走させた。OpenAlex の `Q3`/`Q6` は
  各 37 shard を登録済みだが、無償枠のため取得は数日にまたがる。
  base: 4e8f315bf1101960cc7b95fe88612045fad9713bf775fa0c44752a8f2cc57c88
- [T-2037] **P2・実装済み・取得継続中**: 中断した 2 枝は amendment を先に決めてから新しい
  query ID へ載せ替え、D1183 の機械可読な再開点を発行した。旧 ID は 1 つも継続していない。
  取得の継続は次の無償枠の窓から再開点で継ぐ。
  base: 98b95abb64bb919aeed07027c756f2cd0714923a01274b1574a048d0c82d9975

### 新規

- {{T:axis1-openalex-retrieval-continuation}} **P2・新規**: 軸 1 の OpenAlex 78 leaf を、
  発行済みの再開点から無償枠の窓ごとに継いで取り切る。契約上 5 日以上かかる。
- {{T:axis1-openalex-oqo-order-ruling}} **P2・新規・ユーザー裁定待ち**: OpenAlex の条件 1 を
  `oqo` の順序非依存な比較へ改めるか。索引が順序を正規化する以上、順序つきの比較は構造的に
  充足不能である。改めるなら新しい amendment・新しい epoch・新しい query ID を要する。
- {{T:axis1-arxiv-duplicate-work-id-ruling}} **P2・新規・ユーザー裁定待ち**: 索引が同じ work ID を
  頁境界で 2 回返しつつ総件数では 1 回しか数える場合の条件 5 の扱い。現契約では未完走になる。
- {{T:axis1-verifier-reason-label}} **P3・新規**: 検査器が「完了 pass が無い」leaf へ
  `leaf_page_evidence_missing` という理由ラベルを付ける。evidence は実在するので不正確である。
  状態判定と受理集合には影響しない。
- {{T:axis1-readme-navigation}} **P3・新規**: D1208 の README 導線 (`claim-survey/README.md` と
  `docs/related-work/README.md` 7.7) を、軸 3 の amendment 作業が着地した後に閉じる。
  本 wave は編集面が重なるため触っていない。
