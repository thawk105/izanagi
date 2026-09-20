# 段 1 brief — dev-wave-paper-story-20260920b (2026-09-20 18:2x JST)

- 研究前進: 論文ストーリーの最新版 (第 3 幕の「あと何が要るか」の地図と §6 / §8 / §9 の状態語) を、現行版 2026-09-20 (起点 `b7f970dfa`、07:04 JST) 以後に着地した entry 1712〜1746 (D2165〜D2183、results 稿 6 本、図 5 本、裁定 2 回 D2172 / D2174、g1 発効 D2180) へ揃え、現行版の執筆時点の事実誤認 2 点を訂正した凍結版を 1 本足す。完了判定 = 新版 `docs/paper-story/2026-09-20b.md` と README 4 節の更新が check_docs 緑・段 6 review GO・受入 child-green で main に着地。
- scope: docs-only。新規 file 1 本 + `docs/paper-story/README.md` の版の履歴表 1 行・「最新 =」・訂正一覧・stale 注記 (3 件を本文へ移管)。既存版 10 本・results 19 稿・figures・claim-evidence は 1 byte も変えない。実装面ゼロ、新規計測ゼロ、gate・検査・台帳の追加なし。英語稿・2 本目論文の版は作らない。
- 確定済みユーザー裁定 (依頼文): 起点 = 着手時 local main `fec4a818741e5464fffcd11e4b094c125dfe5280` (18:01 JST、entry 1746 まで) に固定し p24 (着地済み entry 1743 → 反映する)・A-1 attempt-0002 (稼働 wave、未着地 → 待たない) を待たない。最初に時点語の機械置換。見出し・括弧書きの状態語も D 本文へ再照合。README は受入 owned-path 外、表行は段 7 で main を取り込んでから。§10 は草稿で予定形。
- 反映する着地 (依頼名指し): results 稿 5 本 (mocc-g2 観測条件 1721、mocc-witlight 4 arm 1713、K2 3 巡 1719、S-1a 9 対 1732、B-10 待ち方 grid 正式走 1737) + p24 静的 sweep 稿 (1743)、図 5 本 (fig8b 1728 / D2173、fig10 1729、fig11 1738、fig12 1740、fig3b 1727)。
- 訂正 2 点 (現行版の執筆時点の誤り、依頼名指し): (1) §4「第 2 cohort は fig8 に描かれていない」— fig8b は [T-2793] で 2026-09-20 に着地 (執筆時点 07:04 では未着地 → 段 1 で着地時刻を commit から実測して「執筆時点で偽」か「後続で古くなった」かを判定する)。(2) §8 B-1「非列挙の定義の置き直しは未裁定」— D1441 が裁定済み (実装残件の有無は D1441 本文と現行コードで別に確かめて書く)。
- 状態語の再照合で動く主な項目 (brief 前の実測): A-4 / B-2 (凍結 v2 g1 は D2180 で AI 委任の A/X が発効、批准 loader 成功、P3 gate-check は allowed:false のまま = T-2810、W-4 未)、B-7 (D2174 項 3 で限定付き充足、D2044 項 3 を supersede)、A-1 (D2178 で attempt-0002 の rear gate 解除が着地、投入は未 = 稼働 wave)、B-6 / K2 (D2183 で同 job stock 対照の launcher 着地、pair 投入は未)、B-5 (D2172 項 4 段階裁定、共有部品は 1746 で着地、試走・本走は未)、B-8 (D2175 事前登録 v1、未発効)、B-10 (freeze-tree pin 更新 D2166、fig8b)、mocc (D2172 項 7 追加実験見送り、上流報告案 1739)、受入 pairing (D2172 項 1 採用裁定、採用 wave は稼働中未着地)。
- (P1) 版名: 着手日 2026-09-20 は現行版と衝突するので `2026-09-20b.md` (同日 2 版目) とする。version 表の日付欄は「2026-09-20 (第 2 版)」。親の provisional 裁定・攻撃対象。
- (P2) 訂正 (1) の型判定: fig8b の着地 commit 時刻が 07:04 JST より後なら「執筆時点では真で後続で古くなった」型であり、依頼の「事実誤認」は「現時点で偽」の意味に読み替えて冒頭の訂正一覧でなく本文更新として扱う。実測で決める。
- (P3) 訂正 (2) の型判定: D1441 の日付が現行版起点より前なら執筆時点の誤り (冒頭の訂正一覧に載る)。
- 不変条件: 規律 2 を緩めない。新しい主張を足さない。稼働中で未着地の wave (paper-*-ja 3 本、t2766 採用、t2792 attempt-0002 投入、t2304 pin 前進、t1851 / t2698 official 床値) の内容は書かない。裁定待ちの採否を先取りしない。「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」「床値が有効」「B-8 を取得した」「K2 で改善した」を書かない。
- 成果物の形: 新版 (前版と同じ 10 節構成)、README 更新、insight `output/insights/2026-09-20/paper-story-20260920b/README.md` (brief・review 逐語・検査)、worklog fragment、decisions は不要 (裁定なし)。
- 分割方針: 軽量版 (`DW-C00`)。設計択一なし・正しさ防壁に触れず・受理集合不変 → 段 2・3 省略、段 5 = 親の docs 編集、段 6 = 一次資料から事実を再抽出する docs-only なので独立 read-only review 1 本 + 焦点再レビュー 1 本 (上限 3 巡 DW-O16)、変異 matrix は実装面ゼロで免除、受入は記録 commit 後の tip で 1 走 (README は owned-path 外)。
- 受入・実測環境: 受入 = `tools/dev_wave_wait.py acceptance --lease-optional` (Pegasus 計算ノード、門番 loop)。焦点走 = paper-story を読む test を計算ノードへ dispatch。check_docs / 三軸語走査は login。
- 変更面 (実アンカー): `docs/paper-story/2026-09-20b.md` (新規)、`docs/paper-story/README.md` の「## 版の履歴」表末尾行・「**最新 = `2026-09-20.md`。**」行・「**2026-09-20 版が前版 (2026-09-19 版) を訂正した箇所は 1 件である。**」段落・「## 最新スナップショット以後に確定したこと（stale 注記）」節の 3 項目と移管先一覧。
- 条件 dispatch の再評価: 08 (freeze / oracle / proof chain) 不成立、09 (凍結 bytes) 不成立 (既存版・図・稿は不変、README は凍結物でない)、10 不成立、11 (削除) 不成立、13 (gate 新設) 不成立 (scope 外と依頼が明記)。
