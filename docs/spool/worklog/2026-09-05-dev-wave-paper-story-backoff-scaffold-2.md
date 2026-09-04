---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-paper-story-backoff-scaffold
seq: 2
title: adaptive backoff 単独論文の枠を docs だけで新設した — 診断 (律速は更新間隔) を柱に、動的化は未取得証拠として A/B/C へ置き、不在主張は RW0 で軸登録した (docs のみ、branch worktree-dev-wave-paper-story-backoff-scaffold、実装面ゼロ・変異 matrix 免除)
---

## 本文

- ユーザー依頼は「`docs/paper-story-backoff/` を `docs/paper-story/README.md` と同じ凍結契約で新設し、README と
  初版スナップショットを一次資料 (3 定数の insight、D1475 / D1505 / D1506、本体論文 README の stale 注記 1) だけから
  書く。主張は診断 (窓あたり commit 数が勾配推定を壊す) を柱、動的化は未取得証拠として A/B/C 表へ。不在主張
  『更新間隔を動的に決める backoff の先行は無い』は related-work 7.7 の手続きで軸登録し、候補文献 3 群で内部の不在と
  世界の不在を分ける。docs/README.md へ 1 行、check_docs を通す。複数論文を持つ判断は decisions fragment。
  `docs/paper-story/` 配下は編集しない。実装面ゼロ、Codex 子なし、変異 matrix 免除」。
- **段 1 で依頼の前提を覆す一次資料を見つけ、段 4 で親が裁定した。** 依頼の括弧内「窓あたり commit 数が勾配推定を
  壊す」は D1505 が**候補**として記録した機序であり、D1576 (2026-09-03) が「窓幅一定」の前提を崩し、
  `2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` は逐語の歩行 model が谷を再現しないことを
  記録している。柱は D1505 の実測支持部分「律速は更新間隔、刻みは従属変数、上限は他 2 定数の後では効かない」とし、
  依頼の括弧内は候補機序 (前提修正つき) として §4.3 に置いた。**依頼の語「診断」は保った。**
- **導出に含めた一次資料は依頼の 4 資料 + 同日時点の正典 6 件** (D1576、D1515、t2216、t2189 の正しさ認証、
  t2266 の静的 tail 既測、tuned-adaptive-control-paper-reference)。凍結契約「新しい日付の版はその日付時点の正典全体
  からの導出」に従った。除外すると初版が着地時点で腐る。
- 成果物: `docs/paper-story-backoff/README.md` と `2026-09-05.md` (§0〜§10、主張軸 B1〜B6、A/B/C 表、過大主張
  チェックリスト 12 項、本体論文との境界)、`docs/related-work/claim-survey/2026-09-05-backoff-axis-registration.md`
  (軸 B5 を 4 条件へ分解、`docs/related-work/` 配下を 11 語で走査した内部の不在 = 直接接地 0 / 近傍 1、候補 3 群は
  `要裁定`、成熟度 `RW0`)、claim-survey README の一覧 +1 行、docs/README.md の地図 +1 行、
  decisions fragment {{D:repo-holds-multiple-paper-story-series}}。
- 稼働中の別 wave (3 定数の動的化 + Pegasus 実測) と scope が隣接するが編集面は重ならない。動的化の証拠は
  本版では 0 件と書き、進行状況は worklog を正本にした。
- 軽量版 (DW-C00): docs-only のため段 2・3・5・6 の子ゼロ。Codex 起動 0 回、新規計測 0 件。
  段 8 の改善候補: なし。

## 次の一手差分

### 新規

- {{T:backoff-paper-axis-b5-search-prereg}} **P2・新規**: backoff 単独論文の軸 B5 (更新間隔を動的に決める backoff)
  について、`docs/related-work/README.md` 7.7.4 の事前登録 (索引 3 つ・検索式・母集合の外・候補 3 群の positive
  control) を `claim-survey/` の新しい日付版として書く。登録であって実行ではない。
- {{T:backoff-paper-next-version-trigger}} **P3・新規**: `docs/paper-story-backoff/` の次版は、A-4 (機序の直接観測) か
  B-1 (動的化の実測) のどちらかが一次資料になった時点で、その日付時点の正典全体から全面再導出する。
  一項目の決着は版を足さず README の stale 注記で指す。
