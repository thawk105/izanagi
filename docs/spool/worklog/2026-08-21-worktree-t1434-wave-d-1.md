---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: worktree-t1434-wave-d
seq: 1
title: '[T-1434] (4) codex_reasoning_ab.py Wave D (schedule/oracle/aggregate/replay/packets層) を model 軸拡張向けに一般化した (コード+テスト、branch worktree-t1434-wave-d、変異matrix = baseline PASSED・5/6 KILLED (1件は既知node ID登録制約でMISMATCH確定)、受入 verdict=child-green)'
---

## 本文

- 段2 codex plan・段3 敵対相談2レンズ (正しさ境界・scope境界) が、当初 plan の block 検査
  (「2つの arm」への一般化) が T-189 の正しい pair (同一 arm・異なる model) を誤って拒否する
  blocker を独立発見し、段4 裁定 ({{D:t1434-4-wave-d-apparatus}}) で是正した。
- 段6 敵対レビュー2レンズが独立に、`make_packets` の schedule 記述子なし経路でカーディナリティ
  検査が消失している実害と、schedule 記述子ありでも schema_version 欠落の legacy schedule で
  クラッシュする実害を発見。fix 1巡で解消 (307→310 passed)。
- 受入全走2回目が attributable red (`test_real_repo_group_collection_exactly_matches_canonical_nodes`、
  `main_rerun_rc=0`/`wave_rerun_rc=1`) を検出。段5新設テストが `REAL_REPO_SERIAL_NODES`/
  独立golden双方への登録漏れ (F42 型) だったため fix 2件で解消 (310→340 passed)。
  F42・F425 (fork誤動作、本waveでも段1で11件目相当を実測) へ再発を記録した。
- 受入全走3回目は main 側の別 wave (T-1438) と `conftest.py`/`test_real_repo_serialization.py`
  を独立に触っており `merge-message-provenance` で停止。手動 merge 再現→hunk 範囲の非重複を
  file:line で確認→read-only codex に独立検証させ (`safe-union`)、その検証を根拠に
  `--merge-message-file` を付けて4回目で `verdict=child-green` を得た。
- 変異事前登録6件 (t1434d.m01〜m06)。baseline PASSED、5/6 KILLED。m01 のみ既知の node ID
  登録不能制約 (`@real-repo` suffix が pytest collection に現れない) で MISMATCH 確定
  (4/4 予測 node は一致、残り1件は生ログの `nodeid=` で直接確認済み、erratum として本文に残す)。
- T-1434(4) の Wave A/B/C/D が全て完了。他6論点 (独立custodian・cache制御実測・power
  simulation・stage2/5 downstream replayer・task catalog+独立分類者・price snapshot) は
  引き続き未着手 — T-189 の `routing_evidence_status` は本 wave 完了後も `inconclusive` のまま。
- 一次資料: `output/insights/2026-08-21_t1434-wave-d/` (brief・plan・段3/段6レビュー・段4裁定・
  merge監査の verbatim、変異ledger、受入receipt)。

## 次の一手差分

### 更新

- [T-1434] **P1・(4)完了 (Wave A/B/C/D全て land済み)、他6論点は引き続き未着手**:
  `tools/codex_reasoning_ab.py` の model 軸拡張のうち (4) (schedule/oracle/adjudication/
  aggregate/verify/replay/packets 層の model-aware 化) を Wave D で完了した。7 未解決点の
  うち残る6点 (power simulation・独立 custodian 実現方式・provider cache 制御実測・
  stage2/5 downstream replayer 実装・task catalog 実データ+独立分類者確保・price snapshot
  実データ取得) はいずれも実データ・独立第三者・実測を要し未着手のまま。T-189 の
  `routing_evidence_status` (preregistration §12.1) はこの6点が埋まるまで `inconclusive`
  で確定する。**次の一手はユーザー裁定を要する**: 6点の着手要否・優先度・担当 wave を
  ユーザーへ確認する ({{D:t1434-4-wave-d-apparatus}} 参照)。
  base: bd03a4b8028b3a5c0b93bb7434c73550860d80d047307384b7a76fd1b415e060
