---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1372-oracle-perf-binding
seq: 2
title: [T-1372] oracle の _perf_for_holdout へ HOLDOUTS 束縛検証を追加した (コード+テスト、branch worktree-dev-wave-t1372-oracle-perf-binding、変異matrix = baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 設計判断の詳細は {{D:oracle-holdout-perf-binding}} を参照。
- **一次資料の訂正:** command 引数は「発見元は[T-540]」としていたが、実際の discovery は
  entry 658 ([T-1333]/[T-1310]、2026-08-18) であり、[T-540] (2026-08-20 land、`a7f57886`) は
  同ファイルを別件 (完走予約式) で触れただけだった。両裁定文 (entry 658 発見・
  `worklog-phase3-0820-750.md` の再確認) とも [T-540] に言及せず内容は一致しており、実害はない。
- 段2 codex plan (rc=0) は P1 択(a) (`_perf_for_holdout` 内の自己完結検証) を採用し、
  既存 `_canonical_bytes` (s8b_oracle_driver.py:276-283) を再利用する具体案を起草した。
- 段3敵対相談2レンズ (rc=0×2、正しさ境界/整合実効性) とも must-fix なし。real 所見は
  「未知 holdout_id の例外順序が変わる」(裏取り済み: `s8b_oracle_manifest.py` の schedule/freeze
  holdout 集合完全一致検査により実運用では到達不能、defense-in-depth として妥当) と
  「DW-G03 の『同型』主張は文言の精度が要る」({{D:oracle-holdout-perf-binding}} で反映) のみ。
- 段5実装子はテスト実走不能 (dispatch preflight rc=16、既知の codex sandbox 制約) だったため、
  親が直接 `tools/run_tests.py` で実走し 94 passed・17 skipped・0 failed を確認、さらに
  production 側だけ一時的に `git checkout --` で退避し負例2本が実際に失敗する (fixture が
  無条件緑でない) ことを確認してから `git apply` で復元した。
- 段6敵対レビュー2レンズ (rc=0×2) とも must-fix ゼロ。P2/P3 nit 2件 (負例テストの match 正規表現が
  ID・終端を固定しない、"rr20" 側の直接テストがない) は軽微 edge case のため親が追加対応なしで
  受け入れ裁定。
- **変異 spec の見積り訂正:** M2 (canonical bytes 比較の演算子反転 `!=`→`==`) を当初
  「新設2テストのみ」で登録したが、`_perf_for_holdout` は既存の多数の `run_block` 系テストが
  共有する helper であるため、実測すると `run_block` 成功系テスト群を含む28 node が MISMATCH で
  落ちた ([T-540] の M4 実測訂正と同型)。expected_nodes を実測値28件へ訂正し spec v2 で再実行して
  KILLED を確認した。単一原因 (演算子反転) のカスケードであり DW-M01 の単一理由性は保たれている。
- 工数実績 (job dir: `dev-wave-jobs/dev-wave-t1372-oracle-perf-binding/`): 段2 codex plan 1本
  (1回目 not_accepted、commit hash 転記誤りで prompt 修正後2回目 accepted)、段3敵対相談2レンズ、
  段5実装子1本 (accepted)、段6敵対レビュー2本、変異harness実行2回 (1回目 M2 MISMATCH で
  spec訂正、2回目で全2変異 KILLED)。

## 次の一手差分

### 完了

- [T-1372] `s8b_oracle_driver._perf_for_holdout` へ `s8b_holdout_freeze.HOLDOUTS` との
  canonical bytes 束縛検証を追加し、未検証のまま schema-valid な records/threads/ycsb を
  受理していた穴を閉じた。新設ユニットテスト3本 (正例・records 改変拒否・未知 ID 拒否)、
  変異2件事前登録・実行 (baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0)。
  remaining: none
  base: 10b9d68aff85fcaa76e67221db5a7d2538655519ace74786443a684b17fe152c
