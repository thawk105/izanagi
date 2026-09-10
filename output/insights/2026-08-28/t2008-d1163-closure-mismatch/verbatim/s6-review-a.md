## 所見

### A-01 — P2-2 サマリから historical marker が脱落する

- 判定: **real / scope 内 / must-fix**
- file:line:
  - [p2_2_report.py:249](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/campaign/p2_2_report.py:249)
  - [test_bench_first_real_wal.py:358](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_bench_first_real_wal.py:358)
- 具体的反例: `report_workload()` の戻り値には `verifier_assessment_basis` が入るが、`write_summary()` は `campaign_verifier_epoch` だけを表へ出し、marker を一度も直列化しない。したがって新規生成される `output/campaigns/p2-2-summary.md` は、特に historical E1 を「現行 verifier で再検証済み」と区別できない。
- test の問題: 新規テストは `_epoch_provenance(view)` の戻り値だけを検査する。`write_summary()` を通らないため、現在の脱落も検出しない。
- 成果物影響: D1163 が要求する「当時の verifier での判定」という表示が、P2-2 の横断サマリ成果物に届かない。個別 workload の Markdown/.dat provenance には届いている。
- 推奨 fix: `write_summary()` で各行の `read_purpose` と `verifier_assessment_basis` を exact に要求し、marker を列または provenance 節へ出す。実際に一時 summary を生成し、literal の存在と欠落時の拒否を検査するテストを追加する。

## 不変条件照合

- 撤去された production 条件は、`recorded.blob_sha256s` と current map の比較だけ。`recorded-current-closure-mismatch` は dataclass、Layer3 schema、oracle legacy reader の3面だけに残っている。
- `current-closure-unavailable` は [artifact_admission.py:855](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/campaign/artifact_admission.py:855) で維持され、current closure の clean/available 検査も残る。
- 記録 commit blob/digest は `_recorded_campaign_verifier_epoch()` から `_verify_committed_loader_binding()` を通るため維持されている。
- `purpose` は keyword-only・既定値なしで、exact enum 検査も維持。
- `CertifiedCampaignView` と `HistoricalCampaignView` は分離されたまま。marker は historical view のみにあり、certified view の exact 型検査も不変。
- blob map の exact 24-path 集合、reason enum、oracle legacy 受理はいずれも残る。
- D1163 の撤去対象外5束縛について、preregistration、freeze、trace/receipt、operation binding、fresh live semantic resolver の production 経路に差分はない。
- live anomaly 即 reject の verifier/WAL 経路にも変更はない。persisted WAL を全 consumer が再検査しない既存限界は別問題であり、本差分起因の回帰としては扱っていない。
- committed drift 正例は独立 fixture repo で closure A を記録後、closure B を commit している。uncommitted 負例は同じ経路で dirty bytes を作り、理由を `current-closure-unavailable` まで固定している。無関係な層だけで成立する反例は静的には見つからなかった。

## 変異の検出力

- M1: 有効。旧 map 比較を戻すと、pipeline 1 node と verifier 7 parameter の committed 正例が成功地点で失敗する。uncommitted 負例は引き続き拒否側に留まる。
- M2: 有効。literal 変更は historical view、Layer3、critic、backoff、S1 の exact 検査で検出される。
- M3: **部分的**。Layer3、critic/online、backoff、S1 の変更箇所は対応テストが直接通る。P2-2 は helper の検査に留まり、最終 summary の脱落を検出しない（A-01）。
- M4: 有効。schema conditional を外すと、他の receipt/admission 前提を満たした marker 混入負例が受理されるため、対象条件に限定して失敗する。
- M5: 有効。24-path parameter test は exact error reason/path も要求するため、後段の空 WAL 拒否による偽検出にならない。
- M6: 有効。freeze closure SHA 負例は exact `closure-sha-mismatch` を要求し、生成 commit 自体は整合する。
- M7: 有効。operation-only mismatch が独立ケースに含まれ、他の binding は一致したまま。
- M8: 有効。fresh launch は current resolver の呼出しと historical resolver 非呼出しを同時に固定する。
- frozen artifact hashや fixture hashの置換は差分にない。backoff の手製 marker fixtureだけに依存せず、別途 production `load_campaign()` の検査もある。
- repo 内テストと gate の協調改変を防げないというD387/D1163の限界は残る。今回の静的評価は単独変異に対する検出力までである。

## 総括

must-fix は1件。certified 受理境界の撤去範囲は指定された map mismatch 1条件に収まり、規律2および撤去対象外の束縛は弱体化していない。一方、P2-2 の最終サマリ成果物には historical marker が出ず、新規テストもその経路を検査していないため修正が必要。

read-only のため書き込み・テスト実走は行っておらず、緑とは判定していない。
