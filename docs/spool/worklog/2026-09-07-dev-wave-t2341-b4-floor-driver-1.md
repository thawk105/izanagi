---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2341-b4-floor-driver
seq: 1
title: [T-2341] B-4 事前登録 §5.1 (i)(ii)(iii) を履行し、対照対 driver の欠測規則を D1641 第 3 項へ適合させた — 依頼の前提「専用 driver を作る」は既に着地済みで偽だった (コード + docs、branch worktree-dev-wave-t2341-b4-floor-driver、実装面の差分 2 file)
---

## 本文

- **依頼の前提が古かった。** 依頼は D1641 第 4 項を引いて「B-4 床値を測る専用 driver / adapter を作る」
  と命じていたが、その driver は裁定の 3 日前 (2026-09-02) に [T-2166] / D1453 で main へ着地していた。
  第 4 項の理由文「現行の sanctioned CLI ではこの測定を起動できない」は D1453 の理由文の写しで、
  裁定日に既に偽だった。本 wave は「新設」ではなく「欠測規則の適合」として進めた。
  **D1641 へ追記で前提を訂正することを裁定パッケージ 1 として返す** (決定そのものは維持でよい)。
- **D1641 第 3 項との実差は欠測規則の 1 点だけだった。** 既存 driver は 1 件でも欠測があれば不生成で、
  5% の許容へ到達できなかった。実装は {{D:floor-pair-drop-and-count}} と
  {{D:floor-pair-campaign-threshold-locality}}、{{D:floor-pair-record-closure-is-part-of-status-rederivation}}。
- **§5.1 (i) を別 commit で凍結し、(ii) を実測して (iii) を記入した。** 候補 3 driver を Pegasus 計算
  ノードへ直列投入し 3 件とも合格。凍結済みの決定規則 (列挙順の最初) により **base
  (silo-backoff-magnitude)** を採用した。§5 の残る 8 欄は sentinel のままで、本書はまだ発効しない。
- **段 6 の敵対レビュー 2 本が実欠陥を 2 件見つけた。** どちらも「有限な入力から不当に不生成になる」型で、
  受理集合を**狭める**向きだった。(a) 偶数 rep の median が `(a+b)/2` で overflow し、各 rep が有限でも
  最大有限 float 2 件で `inf` になっていた。(b) exact int の float 変換が total でなく `10**400` で
  例外が漏れていた。レビューは pytest を実走できない読取専用の子で、静的検査だけでこれを出した。
- **段 3 のレンズ A 1 回目は出力を失った。** read-only sandbox では file を書けないため、
  子が用意した本文が保存されず 2.5 KB の要約しか残らなかった。「出力は最終メッセージ本文に全文を書け」
  と明記して投げ直し、2 回目は成功した。read-only の子には毎回この指示が要る。
- **変異は probe → 再照準 → 本走の 3 段で回した。** 本走は 22 件 KILLED、等価変異 1 件 SURVIVED、
  期待 node 完全一致、MISMATCH と TIMEOUT は 0。probe で生存した 1 件は照準の誤りで、落ちた標本では
  droppable な record が原因の 1 件しかなく下流も集合で畳むため、集合を列へ変えても挙動が変わらなかった。
  分子を record 数で数える位置へ再照準して 15 node を落とした。この erratum は insight に残した。
  drift mask は 0 件だった。
- **計算ノードが混雑していた。** 焦点走を 3 回投入し、うち 2 回が queue-wait-timeout (rc=16) で子が
  起動しなかった。D612 の待ち時間上書き (3600/600) を付けた回はいずれも走り切った。
- **ユーザー裁定へ 6 件返す。** 前提訂正 (上記)、driver が検査しない機械保証の扱い、**n = 59 と 5%
  許容の非両立** (2 件落ちると残り 57 で被覆 94.6%、推奨は n = 62)、pair ごとの閾値を足すか、
  環境不一致の記録の形、「参照点は対ごとに同一セッション内で測る」の解釈。**前提訂正と n の 2 件は
  B-4 の実走を始める前に決める必要がある。** 詳細は
  `output/insights/2026-09-05_t2341-b4-floor-driver-d1641/README.md`。

## 次の一手差分

### 完了

- [T-2341] 専用 driver は既に存在したため、D1641 第 3 項への適合として実装した。§5.1 (i) を §5.1.0 と
  して凍結し、(ii) を 3 driver 分実測して (iii) の「対象 driver と軸」に base を記入した。変異本走は
  22 KILLED / 期待不一致 0。
  remaining: none
  base: aa7fa6c06a46144d4385a94025455b8db95a668c87803b55baa87e5605cca263

### 更新

- [T-2140] **P1・裁定済み (2026-09-05、AI 委任) → 実装待ち**: 担当 3 者は thawk105 名義で AI が操作、
  測定は認可済み、12 行は §11.2 の案で確定 (D1641)。**起動側の前提は満たした** — driver は D1641 第 3 項へ
  適合済みで、§5 の「対象 driver と軸」は base (silo-backoff-magnitude) で記入済み。
  **実走の前に裁定 2 件が要る**: D1641 第 4 項の前提訂正と、n = 59 と 5% 許容の非両立 (推奨 n = 62)。
  残る §5 の 8 欄と §11 の凍結 commit → 測定 → 採用裁定 → floor 行の記入は未着手。
  base: 1dc92305fd83974999648397c595e2b7bd10548f68414af8430e957215b68de5
