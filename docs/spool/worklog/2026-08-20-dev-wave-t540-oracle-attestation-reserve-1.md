---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t540-oracle-attestation-reserve
seq: 1
title: '[T-540] oracle の完走予約式へ attestation probe 所要時間項を追加した (コード+テスト、branch worktree-dev-wave-t540-oracle-attestation-reserve、変異matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 設計判断の詳細は {{D:oracle-reservation-probe-term-no-plus-one}} を参照。
- **セッション異常:** 段6 fix (NaN/Inf 回帰テスト追加、3回目の fix 試行) が
  `codex_worker_launch.py` の出力下限 (500 bytes) を1バイトも余裕なく下回り
  (`output_bytes=492`) `not_accepted` (validator_rc=1) になった。sandbox=workspace-write
  での実ファイル書き込み自体は正しい内容 (NaN/Inf 拒否テスト2件) で成功していたが、正式な
  採用記録がないため、4回目の fix へ「現状確認し、既にあれば重複させない」という指示で
  再投入し、正式な accepted 記録を得た (作業ツリーへの重複書き込みはなし)。教訓は memory
  `codex-output-min-500-bytes.md` の既存知見どおりだが、今回は「短い診断報告で済むタスク」で
  実際に踏んだ実例として記録する。
- **変異 spec の見積り訂正:** `reservation.py` の NaN/Inf 拒否ロジック
  (`_validate_duration`) を削除する変異を事前登録した際、当初 NaN・Inf 両方が
  `_validate_duration` 層だけで拒否されると見積もったが、実測すると Inf 側は別層
  (`_require_capacity` の `required_s + safety_margin_s > remaining_s` 比較、
  `inf > 有限remaining_s` は常に True) が自然に拒否し続けており、`_validate_duration` 層の
  変異だけでは Inf を kill できなかった (`MISMATCH`、失敗 node が `[nan]` のみ)。
  `expected_nodes` を `[nan]` のみへ訂正し spec v2 で再実行して KILLED を確認した
  (`DW-M02` の「他層の mask を疑い実効 gate へ再照準する」の実例)。これは実装のバグではなく
  NaN と Inf で拒否層が異なるという二重防御の発見であり、規律2 の観点ではむしろ安心材料。
- **工数実績 (job dir: `dev-wave-jobs/dev-wave-t540-oracle-attestation-reserve/`)**:
  段2 codex plan 1本、段3 敵対相談2レンズ、段5 実装子1本 (accepted)、段6 敵対レビュー2本、
  段6 fix 4本 (1本 not_accepted・3本 accepted)、変異 harness 実行2回 (1回目 M4 MISMATCH で
  spec 訂正、2回目で全4変異 KILLED)。

## 次の一手差分

### 完了

- [T-540] oracle の完走予約式へ attestation probe 所要時間項を追加した。
  `orchestrator/campaign/s8b_oracle_driver.py` の `_reservation_required_s`/
  `_recheck_required_execution` へ `ORACLE_ATTESTATION_PROBE_S` (0.2秒) を掛けた項を追加、
  `reservation.py` を int|float 対応 + NaN/Inf 拒否へ拡張。実装 commit `a7f57886`。
  remaining: none
  base: e5af28608fcfa7da154aa2a26d6b953405d0499157192f0c291a8baaebe6a46d
