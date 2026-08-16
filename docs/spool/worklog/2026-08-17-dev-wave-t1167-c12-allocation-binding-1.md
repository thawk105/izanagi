---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1167-c12-allocation-binding
seq: 1
title: 8c 事前登録 C12 の allocation 節を実現可能な予約 binding へ縮小する (コード + docs、branch worktree-dev-wave-t1167-c12-allocation-binding)
---

## 本文

- ユーザー裁定 (2026-08-16 /rulings 全件 第 3 回、択 (c)) を実装した。C12 の allocation 節は
  実装に存在しない `single_process_required` の呼び出しと、8c launcher が single-process 違反と
  resume を launch 前に拒否することの証明を要求しており、充足不能だった (D441)。要求を実在する
  予約 binding — `read_binding` / `check_reservation` と PBS job ID・boot ID・予約期限までの
  残時間 — だけへ縮小した。縮小で保護されなくなった 3 点は事前登録本文 §6 の 衝突 (e) へ逐語で
  名指しした。**旧要求は 1 度も発火していなかったため、新たに拒否されなくなった実行は無い**
  (D441 決定 3)。規律 2 の逸脱ではないが逸脱に見えうるので注記を残した。
- 縮小後の binding が実データで発火することは、実 repository の blob に対して C12 の理由が
  `environment-contract-consumer-absent` (誤診断) から `allocation-enforcement-consumer-absent`
  (実在の欠落) へ変わることで示した。終端は `EVIDENCE_UNDEFINED` のままで `SATISFIED` 経路は
  作らず、受理集合は不変である。判断は {{D:c12-allocation-binding-shrink}} に記録した。
- 段 3 の敵対レンズ 2 本の所見はすべて real、refuted ゼロだった。
- **並行 wave [T-1250] が同じ面へ先に着地した。** 合成で判明した構造事実を 2 つ実測した。
  (1) 凍結世代 record の blob 不変は**全履歴**に及ぶため、同じ世代番号を並行 wave が先に land
  すると自 branch 履歴の旧 record が `generation-mutated` を発火させる。main の merge では
  履歴の旧 blob が消えず解けないので、branch を main 直上の線形形へ組み直した。
  (2) `prepare-revision` は文書と契約を作業木から読み履歴は `--commit` で検証するため、文書変更を
  commit 済みにすると `record-protected-mismatch` で必ず落ちる。記録は {{F:frozen-generation-collision}}。
- 不変条件テストの競合は Codex author の合成監査で解いた。main 側 tip 束縛テストへ本 wave 固有の
  assert (`_load_freeze_record` 経由の世代照合、型付き record の版照合) を統合し、落とした assert
  は 0 件である。監査は allocation gate の判定順序を production snapshot に依存させない fixture も
  足した。
- 変異 matrix は最終 commit で 4/4 KILLED、baseline PASSED。期待 node は全件 SURVIVED 期待の probe
  から実測した完全集合を使った。**runner 範囲を 2 ファイルへ縮小した (silent cap にしない)** —
  不変条件テストの候補 tip テストは `@xdist_group` 付き node ID を持ち、harness の正規化が接尾辞を
  剥がせず停止するため外した。同じ変異は焦点走で不変条件テスト側も検出することを確認済み。
- 段 8 の自己改善候補 3 件はすべて `docs/failures.md` または既存 `DW-M07` で足り、dev-wave 入口・
  reference の編集は不要と裁定した。
- 工数: Codex author 子 (plan 1・敵対相談 2・実装 1・レビュー 2・fix 1・合成監査 1) の計 8 本。

## 次の一手差分

### 完了

- [T-1167] 8c 事前登録 C12 の allocation 節を実現可能な予約 binding へ縮小し、縮小で保護されなく
  なった 3 点を事前登録へ名指しで注記した。縮小後の binding が実 repository の blob に対して発火し
  理由コードを誤診断から実在の欠落へ変えることを 2 経路で pin し、変異 4/4 KILLED で検出力を示した。
  第 5 世代の凍結 record を発行した。
  remaining: none
  base: 95b1860c1da8c88401553882796df893b281d2f5b7511076e7a5207ea03d931d
