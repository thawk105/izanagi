---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t755-mocc-trace-execution
seq: 1
title: '[T-755] mocc trace v2のTRACE=1正しさ検証パイロットを実機実行しserializable・anomaly 0を得た (コード+テスト、branch worktree-dev-wave-t755-mocc-trace-execution、変異matrix = 手動kill-check2件ともKILLED)'
---

## 本文

- 段6まで完了しmain着地済みのmocc trace pilot adapterを実機投入したところ、既存レビュー
  (コードリーディング中心) では検出できなかった実装欠陥2件を発見した。(1) CPU model環境gateの
  厳密文字列比較が実機の商標記号付き表記で偽陽性拒否 (sibling script `t141_region_profile.sh`の
  正規化パターンを移植し解消)。(2) verifier起動が計算ノードのIntel Python 3.9系で
  `orchestrator`パッケージを解決できず失敗 (`floor_campaign.sh`等の既存版数gateパターンを移植)。
  各々段2プラン→段3敵対相談2レンズ→段4裁定→段5実装→段6敵対レビュー2レンズのフルサイクルを
  経て修正し (段6所見: 1件目real0件、2件目real1件でfix)、手動mutation kill-check
  (正規化/fail-closed判定をそれぞれ無効化する単一変異→新設テストKILLED確認→復元) で
  回帰検出力を実測した。設計判断は {{D:t755-cpu-model-normalization}}、
  {{D:t755-verifier-interpreter-gate}} 参照。
- 3件目の障害 (worktree内staging areaの前回attempt build成果物残存によるhydrate拒否) は
  adapterのコード欠陥ではなく環境状態の問題と判明し、staging tree削除で解消 (コード変更なし)。
- 修正後、実機再実行 (request 934607.nqsv) が環境gate・build・751,914txn相当のworkload
  (実測761,914 txn)・trace採取・verifier起動まで完走し、**verifier_rc=0
  (serializable, anomaly_count=0, total_cycles=0, 12種の整合性検査すべてclean)** を得た。
  compute-node上の実行とlogin nodeからの独立再実行でbyte-for-byte一致を確認した
  (規律3、後付けにしない独立確認)。一次資料:
  `output/insights/2026-08-22_t755-mocc-trace-v2-pilot-serializability.md`。
- TRACE=0性能計測はmocc-trace-v2.patchのtrace.hh include行のコメント残存
  (`check_trace0_preprocess_identity.py`がreject) により本waveでも未実施のまま
  (別途人間手番のcommitが要る、worklog entry 812から変わらず)。TRACE=1の本結果はこの
  欠陥の影響を受けない。
- D662 (受入・land運用簡素化) をピア通知経由で把握したが、主checkout `docs/decisions.md`で
  独立に一次資料照合してから採用した (裏付けなしの初報は保留し発信元へ確認を求めた)。

## 次の一手差分

### 更新

- [T-755] Q2(a) mocc trace pilotの実機実行 (TRACE=1) が完了し、serializable・anomaly 0の
  結果を得た。TRACE=0性能計測は人間手番のsource commitが必要なまま未着手 (P1・Q1(a)・
  Q3(a)は既存記述のまま完了)。
  base: f1f86688e961f4fc57944277a8c6c273077f7222309a218695669e71f6087523
