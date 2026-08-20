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
- **セッション異常:** 段6 fix (3回目) が出力 bytes 下限未達で not_accepted になった件は
  F43 へ再発追記した (実ファイル書き込みは正しく、4回目の fix で現状確認・重複回避のうえ
  accepted 記録を取得)。
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
