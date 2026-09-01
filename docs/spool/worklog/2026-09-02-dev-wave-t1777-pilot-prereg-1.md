---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t1777-pilot-prereg
seq: 1
title: [T-1777] A-1 pilot の事前登録本文を起草し、人間の発効直前で止めた (docs のみ、branch worktree-dev-wave-t1777-pilot-prereg、変異 matrix = 実装面の差分ゼロにより免除)
---

## 本文

- 関門を実測で確認した。pilot policy の `preregistration` は `{path: null, sha256: null}` で、
  `_require_policy_ready_for_execution` が
  `PaperStoryError("v3 policy preregistration binding is not frozen by the parent")` を投げる。
  submit も measure も必ず拒否される。coordinator の実装は `08a17b3b3` で着地済みのため触っていない。
- 成果物は 2 つ。事前登録本文
  `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
  (SHA-256 = `8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc`) と、
  発効手順を含む wave insight `output/insights/2026-09-01_t1777-pilot-preregistration`。
  **実装面は 1 byte も変えていない。** 発効は D1383 / D1391 に従い人間の手番として残した。
- **依頼と親 brief が数えていた発効の編集箇所は不足していた。** brief は 4 箇所としたが、
  実際は 5 箇所である。5 箇所目は `test_v3_loader_accepts_future_sized_policy_shape` で、
  sized 形状の fixture が pilot policy を実ファイルから複製したうえ `preregistration` だけを
  sized 用へ戻していないため、発効後に sized 側 module pin (`None` のまま) との照合で落ちる。
  段 3 の工程レンズが出し、親が一次資料で検算して確定した。
- 独立レビュー 4 本 (段 2 プラン 1・段 3 相談 2・段 6 レビュー 2) が出した real 所見を、
  親がすべて一次資料で検算してから反映した。反映した主なものは次のとおり。
  `rep_notes` 非空が policy の 16 の無効規則の外にある受理規則として v3 でも発火すること。
  反復数を決める手順の分類語彙 (`bounded-within-floor` / `resolved-beyond-floor`) が
  driver の `CLASSIFICATION_RULES` と別系統であること (親 brief の provisional 裁定を訂正した)。
  alpha の配分が workload ごとに独立で 3 workload 合計は `1/20` ではなく `3/20` であること。
  arm ブロック 24 本と対ブロック 12 本が別物であること。headline のテストが clean worktree を
  要求するため発効の commit より後に走らせる必要があること。
- **不採用にした所見が 1 件ある。** 内容レンズは「Monte Carlo の試行回数を機械可読の正本
  (policy JSON) へ凍結せよ、さもなくば発効不能」と述べたが、policy JSON の編集は発効閉包
  そのもの (人間の手番) であり本 wave の scope 外である。人間可読の事前登録本文で凍結する形は
  v2 の先例と同型で、「データを読む前に決める」という事前登録の意味を満たす。値は同じ A-1 族の
  headline study の凍結値 (探索 20,000 / 認証 100,000) に揃えた。ユーザー裁定では止めていない。
- 恒真な保証を書かないための措置を 2 箇所入れた。16 の無効規則については「登録した判定の規則で
  あって実装の完全性の証明ではない」と明記し、試行回数と候補範囲については「道具が機械的に
  強制する値ではない」と明記した。いずれもレビューが指摘した実装側の裏取り不足に対応する。

## 次の一手差分

### 更新

- [T-1777] **P2・ユーザー手番 (発効)**: A-1 の対の配置。**(1) coordinator 実装は着地済み**
  (`08a17b3b3`)。**(1.5) 事前登録の起草は完了した** (2026-09-02)。本文は
  `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
  (SHA-256 = `8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc`)。
  **残るのは発効だけで、これは人間の手番である** (D1383 / D1391)。編集は 5 箇所 —
  driver の事前登録 pin 2 本、policy JSON の `preregistration`、policy bytes に連動する
  `V3_PILOT_POLICY_SHA256`、未凍結を固定している正例テスト、および sized 形状 fixture の
  `preregistration` 戻し。手順・実行順・commit 前後に分けた検査コマンドは
  `output/insights/2026-09-01_t1777-pilot-preregistration` §4 が正本。
  (2) 発効後に pilot を 60 対/workload 測る (未走)。(3) pilot から対 SD とブロック実効 sigma を
  出し、独立 seed の simulation で反復数を認証する。(4) `paper_story_a1_paired.v3-sized.json` と
  その事前登録を凍結する (未作成)。(5) 本走を投入する。
  凍結済みの現行 study は据え置き、bytes を変えない。
  base: 633d9f08df82445135231a3a98ce939f6e4e15c61e6baf1f7e43c95c921b2eba

### 新規

- {{T:a1-sizing-tool-accepts-wider-range}} **P3・新規**: 反復数を決める道具の受理範囲を
  事前登録と突き合わせるかを判断する。`tools/size_paper_story_a1_balanced.py` の
  `SizingConfig.validate` は試行回数を 1〜1,000,000、候補範囲を
  `28 <= n_min <= n_max <= 4096` の任意値で受理し、下流の sized certificate の照合も
  選ばれた `n` / `df` / `k` / sigma を見るだけで certificate 内の試行回数と候補格子を照合しない。
  事前登録本文は「道具が強制する値ではない」と明記して恒真な保証を避けたが、機械側で閉じるかは
  別判断である。段 6 のレビューが出した real 所見で、docs-only の本 wave では実装していない。
- {{T:a1-invalid-rule-enforcement-evidence}} **P3・新規**: A-1 v3 の 16 の無効規則のうち
  「両 arm の bench 前 build・verify」「ブロックごとの競合テナント検査」「静定がちょうど 1 回」の
  3 つについて、成果物から拒否できることの実装証拠を閉じる。段 3 の内容レンズが
  「射影した driver だけでは確認できない」と述べ、親は事前登録本文で enforcement を主張しない
  書き方にして回避した。実装側の裏取りは未了である。
