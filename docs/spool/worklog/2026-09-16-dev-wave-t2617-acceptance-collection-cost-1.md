---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2617-acceptance-collection-cost
seq: 1
title: [T-2617] 受入の「テスト開始まで」の内訳を確定し、安全に削れる量が 1 秒級であることを実測で示した (docs のみ、branch worktree-dev-wave-t2617-acceptance-collection-cost、実装面の差分 0 なので変異 matrix は DW-S04 により免除)
---

## 本文

- **依頼が挙げた「collection 約 93 秒」は現行の値ではなかった。** 93 秒は 2026-09-14 の
  1 走の値で、しかも直接観測ではなく残差だった。2026-09-16 の 28 走を測り直すと
  **55.4〜59.1 秒**で、33 台の別ノード・wall 296.2〜604.5 秒にまたがって幅 3.7 秒しか動かない。
- **主因を対照実験で 1 つ消した。** 受入だけが載せる分割 plugin の per-item 費用は、
  同じ負荷で連続 2 走した差分で **user CPU +1.74 秒**しかない。
  `_canonical_item` の 2 回呼び出しも `Path.resolve()` も `allocate` も digest も全部この中である。
  **「per-item の正規化を減らせば効く」という見込みは否定された。**
  主因は 48 worker が同じ全 collection を並列に払うこと (計算ノードは 48 core・HT 無効)。
- **短縮の判定は「`pre` は削れない、`disp` の手は別タスクが持っている」。**
  `pre` に残る唯一の安全な候補は `_canonical_item` の重複除去だが、48 worker でも wall 1 秒級で、
  正規化・重複拒否・marker 検査の等価性証明に見合わない。**規律 2 の面に触れる変更を
  1 秒のために入れない。** 詳細は {{D:acceptance-pre-collection-is-parallel-collection}}。
- **段 3 の 2 レンズが親の provisional 裁定 5 件のうち 3 件を覆した。棄却した所見は無い。**
  (a) 「`disp` の 99.995% が receipt prewarm」は `receipt/barrier` の比であって
  `receipt/disp` ではない (barrier 31.32 対 `disp` 28.44、差 2.88 秒)。
  (b) 「56 − 18 = 38 秒」は同条件の差分ではない (host・plugin・commit・集合が違う)。
  (c) 「集合不変だから gate に触れない」は等価性の証明ではない。
  さらに親が数え落としていた事実を 2 件受け取った — `_canonical_item` は item ごとに 2 回
  呼ばれる (親は 1 回と数えていた)、`:917` と `:919` の digest は別入力で重複計算ではない。
- **D1729 の見送りは事後的に正しかったことが確認された。** 実際に内訳を確定してみたが
  次の一手は変わらなかったので、再訪条件「内訳の確定なしには次の一手が決まらない」は
  満たされていない。schema は v1 のまま置く。{{D:d1729-observation-field-deferral-confirmed}}。
- **D1728 の再訪条件も満たされていない。** 独立な全体集合から導いた期待割付の供給設計を
  本 wave は示していない。絞り込みは採らない。両レンズが独立にこれを支持した。
- 実測・逐語・再現手順は `output/insights/2026-09-16_t2617-acceptance-collection-cost/`。
  親の段 1 brief も `verbatim/` に置いたが、その (P1-B) (P1-C) (P1-D) は段 4 で覆っている。
- **[T-2616] の wave が同時に稼働していた。** 編集面は wave slug 入りの新規 path
  (insight dir と spool fragment) だけなので、重複は構造的に生じない。

## 次の一手差分

### 完了

- [T-2617] 2 区間の内訳を確定し、絞り込み以外の手の有無を判定して insight に残した。
  `pre` は 48 重の全 collection が主因で安全に削れる量は 1 秒級、`disp` の手は [T-2616] が所有。
  remaining: none
  base: 7e3a1ad08f95bce1aa058bd86a55d586662d5e332b93fd0f4d14f8a81d2422d7
