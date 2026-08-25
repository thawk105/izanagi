---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1675-official-floor-path
seq: 1
title: [T-1675] 床値 official 経路の閉塞を実測で 4 つまで数え上げ、§8 承認束縛を裁定した (docs のみ、branch worktree-dev-wave-t1675-official-floor-path、実装差分ゼロ)
---

## 本文

**D811 の着手条件は実測で不成立だった。** 「official 走行が同じ cell を claim できることを確かめ、
塞がっていれば着手前に報告する」に対する答えは**塞がっている**である。

入場鍵の identity は 6 項目 (freeze sha256 / holdout key / configuration / CCBench pin /
env tag / observation role) だけで、**mode も source commit も script blob hash も入らない**。
隔離 fixture で本番と同じ機構を走らせた実測 — official を新規で入れると
`holdout cell key was already consumed by another fresh run`、resume で入れると
`resume cell claim does not match the same run identity`、対照の pilot resume (同一 identity) は
通る。したがって **D323 が指示する再投入 (別 source commit・別 script blob hash) を完全に
実行しても、入場鍵の identity は 1 bit も変わらない。** D323 の手順と入場鍵の定義は直交している。

試験走行が焼いた使い捨てファイルは claim 12 + 消費 marker 96 = **108 枚** (走行
`20260824T205358Z-2c8cf9be`)。D811 本文の「118 件」は再現しなかった。導出の記録が無く、
どちらが正しいかは判断できない。

**閉塞は 2 つでなく 4 つあった。** 段 3 の敵対相談 2 本が独立に残り 2 つを指摘し、親が一次資料で
確認した。(3) `_assert_official_permitted` が official を core で無条件拒否している。拒否理由は
コード内に「§8 (承認束縛方式) 未裁定」と書かれており、決定台帳を検索しても「承認束縛方式」に
触れる決定は 1 件も無く、今も未裁定だった。(4) v2 freeze が要求する budget 承認の成果物
`output/s8b-freeze-budget-approvals/g1.json` が不在かつ未追跡で、人間が書く承認文書である。
落とした経緯は {{F:brief-missed-guard-in-read-docstring}}。

**親の説明の誤りを 2 件訂正した。** (i) 単位 B (依存物の運搬を staged 既定にする) を
「緩和ではない」とユーザーへ説明したが誤りで、判定式を編集せずに同じ構成の
`eligible_for_refreeze` が false から true へ反転する受理集合の拡大である。承認 nonce は
この拡大を検出しない。(ii) 段 1 brief は観測役割を 3 個としたが実際は 4 個で、
official 専用役割を足すなら 4 から 5 への変更になる (段 2 プラン子が指摘)。

**§8 承認束縛方式をユーザーが裁定した ({{D:s8-official-approval-nonce}})。**

**退けた指摘 1 件.** 「[T-1669] が旧役割を固定しているので official の claim は最初の消費で
止まる」は、当該 worktree の追加コードに `observation_role` の参照が 0 件で、
現状の証拠では支持されない。

**段 4 で「実装しない」と裁定した。** 4 つの閉塞のうち 2 つ (§8 の裁定、budget 承認文書) は
人間手番であり、単位 B だけ先に入れても official は core で拒否されたままで床値は動かず、
受理集合だけが広がる。実装差分ゼロで着地する。

**codex 子 5 本** (プラン 1、敵対相談 2、§8 設計相談 1、および認証の一時無効化
`401 token_invalidated` で出力未生成のまま失敗した 1 本)。失敗した 1 本は記録を保全したうえで
別 identity で再投入した。ローカルの `codex login status` は「ログイン済み」と答えるのに
サーバが 401 を返す状態が、走行の途中で発生しうる。

**記録中に dispatch を自分で止めた。** 親が全史 provenance 監査を 2 分のタイムアウトで打ち切り、
計算ノード job の終端を観測し損ねて orphan hold が武装した。監査自体は計算ノードで成功しており
(`child_rc=0`、5858 件・新規違反なし)、実害は復旧作業だけだった。解除の過程で、解除文言が
実際に閉塞している耐久記録を名指ししないことが分かった
({{F:orphan-hold-message-names-only-summary-path}})。

## 次の一手差分

### 更新

- [T-1675] **P1・一部裁定済み・人間手番待ち**: 床値 official 経路の閉塞は 4 つ。
  §8 承認束縛は {{D:s8-official-approval-nonce}} で裁定済み。残るユーザー手番は
  (a) budget 承認文書 `output/s8b-freeze-budget-approvals/g1.json` の作成、
  (b) {{T:floor-staged-transport-eligibility}} の裁定、
  (c) {{T:cross-role-observation-budget}} の裁定。3 つが揃えば実装 wave を起こせる。
  実装は入場鍵へ official 専用の閉じた役割リテラルを 1 個足す形 (claim key の 6 項目は変えない)。
  base: ae5df0d65a1aa36f7bc8e79ece5417e8fbe304e1339e4a61a146f9fe26623b0b

### 新規

- {{T:floor-staged-transport-eligibility}} **P1・ユーザー裁定待ち**: 依存物の staged 運搬を
  driver の既定にすると、明示引数のとき不適格だった同じ構成が `eligible_for_refreeze` で
  適格へ反転する。D446 の「受理集合は縮む方向にしか動かさない」と衝突するため、
  整合する変更として承認するかを裁定する。計算ノードは offline で、既定 (legacy) 経路は
  依存物の所在を渡さず取得するため、承認しない場合は Pegasus で適格な official 走行が
  構造的に作れない。
- {{T:cross-role-observation-budget}} **P2・ユーザー裁定待ち**: official 専用の観測役割を
  足すことに対し、役割横断の生涯観測上限を別途要求するか。承認 nonce は将来の役割追加を
  止めないため、上限を置かないと役割ごとに観測を増やせる形が残る。
- {{T:orphan-hold-message-lists-actual-paths}} **P3・新規**: Pegasus の orphan hold 解除文言に、
  gate を成立させた実 path を列挙させる。現在は要約 marker の path しか出さないため、
  request 別の耐久記録だけが残っている場合、指示どおり削除しても hold が解けず、
  文言は不在の path を指し続ける。
