# 段 1 brief — [T-1912] 対の完全性と receipt shopping の遮断

## 研究前進

B-4 還流 ablation 事前登録 §7.2 / §10 が「閉じない」と列挙する項のうち **「pair の完全性と receipt
shopping の遮断」1 項**を閉じる。止めている研究は B-4 正式標本 (§7.1 の全件報告規則が機械強制されず、
同一 block を複数回走らせて都合のよい pair を提出する経路が開いている)。最小差分は、block id・
precursor hash・proposal hash・on/off receipt の 4 者を束縛する canonical な pair binding と、それを
厳密再生成して照合する完全性 consumer を、既存 production 消費点の手前に置くことである。完了判定は
「負例 (pair をすり替えた bytes) が reject され、正例 (整合した bytes) が通る」ことを実テストで示すこと。

## 確定済みユーザー裁定・上位規範

- 本 wave の依頼 (ユーザー直接発話): 束縛の実装だけを行う。B-4 本走は分離する ([T-2464] 裁定待ち)。
  同一 receipt の再消費は既に閉じているので重複して作らない。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外。Codex author = D95。
- D1936 項 8: B-4 は記述統計へ限定して進める。母集合を作るための追加基盤は採らない。
- D1936 項 9: B-4 の部分実装を完成と呼ばない。完成主張のための不変 writer・全 arm 運営機構を増設しない。
- D1812 (a): 事前登録 §5「primary outcome の演算定義」欄に記入した 5 値が**記入時点の bytes と一致する
  ことを引き続き要求する**。
- 絶対規律 2: 正しさゲートを緩める変異を採らない。本 wave は受理集合を**狭める**方向のみ。

## 不変条件

1. **分析閉包 5 module (`p3_b4_analysis_contract.py` / `_adapter.py` / `_ledgers.py` / `_path.py` /
   `_prereg_consumer.py`) の bytes を 1 byte も変えない。** 変えると §5 の記入値が黙って偽になる
   (照合する機械検査が無いので test は赤にならない。だからこそ人が守る)。
2. 事前登録 doc (`docs/phase3-b4-reflux-ablation-preregistration.md`) を編集しない。並行 wave
   ([T-2547]、[T-1875]) が同 doc を所有しうる。閉じた事実の追補は別 wave・別裁定に委ねる。
3. 新しい検査は受理集合を狭めるだけにする。既存の正例が落ちてはならない。
4. 主張を広げない。「pair が同一 campaign から来た」ことの証明は作れない
   (`B4_RAW_RECORD_NON_GUARANTEES` に既述のとおり `initial_proposal_sha256` の権威 producer が無く、
   束縛は転記に留まる)。閉じるのは**転記の一貫性と対の一意性**までであり、そう明記する。
5. 実 campaign 成果物は 0 件。値域は issuer / producer の実 API が生む bytes で実測する。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** 実装は閉包 5 module の**外**へ置く。新 module + 既存 production 消費点
  (`p3_b4_material_report.py:267` の `evaluate_b4_artifacts` 呼び出し周辺) への配線で閉じられる。
  閉包内へ入れる案は §5 記入値の差し戻しを要し、受理集合を変えるのでユーザー裁定が要る。
- **(P1-b)** pair binding は**新しい writer を増やさず**、既に create-only で公開済みの artifact
  (封印 registry の `initial_proposal_sha256`、凍結 manifest の block id / attempt id、issuer 計画 path に
  公開された attempt artifact の arm ごと `precursor_hash` と `source_artifact_sha256`) から
  **決定的に再生成**する。`assert_analysis_manifest_complete` と同じ「厳密再生成して照合」の型を踏襲する。
- **(P1-c)** 遮断する性質は 4 つ。(i) manifest の 201 block と pair 行が過不足なく 1 対 1、
  (ii) 各行の proposal hash が封印 registry の同 attempt の `initial_proposal_sha256` と exact 一致、
  (iii) 両 arm の観測 `precursor_hash` が (ii) の値と exact 一致 (現状は on==off しか見ていない)、
  (iv) on/off receipt (`source_artifact_sha256`) が提出全体で大域一意かつ arm slot の取り違えが無い。
- **(P1-d)** (iv) の「1 回の提出内の重複禁止」は `p3_b4_analysis_path._source_artifacts_match` が既に
  持つ。**重複実装しない。** 新規に足すのは「registry / manifest の値との突き合わせ」だけである。

## 成果物の形

- 新 module 1 本 (閉包外)。純関数 + fail-closed。closed schema・closed 理由語彙。
- 新 test file 1 本。**負例を性質ごとに 1 つ以上**持ち、通る正例を 1 つ添える。
  新規 test file なので自走 harness の file 集合列挙と `acceptance_duration_ledger.json` の両方を同じ
  変更単位で満たす。
- production 消費点 (`p3_b4_material_report.py`) への必須配線と、その負例テスト。
- 変異 matrix で (P1-c) の 4 性質それぞれが kill されることを示す。
- worklog / decisions / failures は spool fragment として書く。insights は逐語を直接書く。

## 分割方針

受理集合を変え正しさ防壁に触るので**軽量版にしない**。段 2 plan 1 本、段 3 敵対相談 2 本
(lane=sol / luna、レンズを変える)、段 5 実装子 1 本 (所有 path: 新 module + 新 test + material_report +
duration ledger)、段 6 レビュー 2 本 + fix。実装面は全て Codex `role=author` が書く。親は直接編集しない。

## DW-G04 / G05

- **G04 (発火 gate):** 本 gate は条件付きではなく、material report 生成のたびに無条件に発火する。
  発火点は `p3_b4_material_report._load_and_evaluate`。実 campaign 成果物は 0 件だが、この関数は
  `test_p3_b4_material_report.py` が issuer と producer の実 API で作った実 bytes で通す経路である。
- **G05 (成果物影響):** 放置すると材料レポートと分析 verdict が、同一 block を複数回走らせて選んだ
  pair、および registry の proposal と無関係な precursor を持つ pair を受理しうる。受理集合が変わる。

## 受入・実測環境

Pegasus login node 上の python テストのみ。build・benchmark・計算ノード投入は行わない。
