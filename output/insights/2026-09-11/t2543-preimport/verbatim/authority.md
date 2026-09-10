# 必読事項の射影

## D1936項30（逐語）
### 項30 — importより前に条件関門fileを検査する

対象: T-2543。

**決定:** t316のshell側BOUND_PATHSへcondition_meaning_gate.pyを1件足す。

**理由・採らない案:** 既存のdirty検査をPython起動前に効かせる局所修正。汎用import閉包は作らない。

## archive worklog-phase3-0910-1410 T-2543（逐語）
- [T-2543] **P2・新規・ユーザー裁定待ち**:
  `tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54-59` の `BOUND_PATHS` は 4 件で
  `orchestrator/campaign/condition_meaning_gate.py` を含まないが、
  `t316_sandbox_backend_probe.py:36` は module import 時にその file を import し、
  Python 側の dirty 検査はその後に走る。dirty な condition gate は、どちらの束縛関門よりも
  前に import-time のコードを実行しうる。取りうる形は (a) shell の `BOUND_PATHS` へ 5 件目を
  足す、(b) Python の import を dirty 検査の後へ遅らせる、(c) 既知限界として記録する。
  成果物影響 = 放置すると、t316 の receipt が「束縛された 5 path で走った」と記録していても、
  そのうち 1 path については実行より後に検査したことになる。
  [T-2503] の段 3 レンズ A が出し、段 6 の 2 レンズが追認した scope 外の real 所見。

## 今回のユーザー指示
本題の実装だけ。既存dirty検査がPython import前に対象を検査するようにする。対応する既存契約テストと必要な参照を同じ変更で整合する。汎用import閉包や別の防護機構を新設しない。規律2を緩めない。実装は別のD95 Codex author worker。親が検査・受入・統合・記録・landを担当。改善実装・次wave・pushなし。
