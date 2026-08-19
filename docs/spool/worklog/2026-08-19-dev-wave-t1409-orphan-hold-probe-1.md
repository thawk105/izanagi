---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1409-orphan-hold-probe
seq: 1
title: '[T-1409] の orphan-hold 再発を、check_acceptance_reds.py 固有の欠陥ではなく共有 dispatch の非決定的 timing 事象と切り分けた (docs のみ、branch worktree-dev-wave-t1409-orphan-hold-probe)'
---

## 本文

- [T-1409] の依頼は「dispatch/qstat 応答性の環境要因か `check_acceptance_reds.py` 自身の
  qstat 判定条件の欠陥か」の切り分けだった。`tools/check_acceptance_reds.py` を全文 grep した結果
  `qstat` への参照が 0 件であることを確認した — 同ファイルは `tools/run_tests.py --force-dispatch`
  経由で `tools/pegasus/dispatch_compute.py` の共有 dispatch/orphan-hold 機構を呼ぶだけで、
  独自の qstat 判定ロジックを一切持たない。**したがって「check_acceptance_reds.py 自身の
  qstat 判定条件の欠陥」という仮説は構造的に成立しない (そのようなコードが存在しない) と判断した。**
  同じ結論に達するため mutation_worktree.py / mutation_harness.py / run_tests.py も grep し、
  `--accounting-grace` を上書きする呼び出しが repo 内に 1 件もないことも確認した (既定の
  `DEFAULT_ACCOUNTING_GRACE_S = 60.0` が全 caller 共通で適用される)。
- T-1362 land 時 (worklog 旧 entry 689) に実際に発生した orphan-hold の一次証拠を、
  repo 外に保全済みの
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1362-reasoning-pin/` 配下のログ・receipt から
  読み直した。`waiter.stdout.log`/`waiter.stderr.log`/
  `acceptance-receipt-1.json.acceptance-red-check.json` は、**同一 wave・同一 nodeid・同一
  probe worktree パターンへの反復投入のうち先行する複数回が orphan-hold で終わり、直後の
  試行が同一コード・同一入力のまま `status=attributable-red` で正常完了した**ことを示していた
  (最終的に `request_id 924102.nqsv`/`924113.nqsv` の dispatch receipt が両方とも正常取得され、
  probe worktree もクリーンアップ済みで残骸なし)。**同一コードが同一条件で失敗と成功の両方を
  返した事実そのものが、決定論的なロジック欠陥ではなく非決定的な timing 事象であることの
  直接証拠である。**
- コード読解で特定したトリガー経路 (1 本): `tools/pegasus/dispatch_compute.py:1948` の
  `DispatchError("result/log/accounting-grace-expired")` — scheduler が `END` を報告してから
  `accounting_grace_s` (既定 60 秒) 以内に `result.json`・stdout/stderr ログ・NQSV 会計サマリ
  (`_accounting_present`)・compute marker の**全て**が揃わないと発火する。この例外は `finally`
  節の `_fresh_qstat_gated_qdel` (同ファイル 1195 行台) に落ち、そこで打つ**新規** `qstat -f`
  が既に scheduler から消えたジョブを `success-request-absent` と分類し、`denied("request-absent")`
  → `job_may_remain=True` → `_latch_orphan_hold` (1072 行) が `gate.reason=request-absent` を
  持つ `orphan-hold.json` を作る。実測の hold evidence (`gate.reason=request-absent`) と完全に一致する。
- `check_acceptance_reds.py` の probe 利用パターン (`--collect-only` 1 件 + 各 nodeid の
  main/wave 再走を短時間に連続投入) は、受入全走や変異 matrix のような単発長時間 dispatch と異なり
  **小さく短い job を複数バースト投入する**。60 秒という固定の accounting-grace 窓が、この
  バースト投入パターンで相対的に厳しくなる (scheduler 側の epilogue/会計書き込みが競合しうる、
  または新規作成した probe worktree の共有 FS 上の可視性伝播が遅れうる) という仮説を持つが、
  これは未実測であり本 wave では確認していない。実測せずに恒久対応へは進まず、
  本 wave は依頼どおり診断と構造化報告だけで打ち切る。
- F383 の原記録 (変異走行中の docs 編集による共有木 byte 変化検出、`rc=125`) とは無関係な
  トリガー経路であることを確認した。ただし latch 自体・復旧手順 (`qstat` 出力内容で不在確認 →
  worktree の clean/HEAD 確認 → 手動 `qdel` を使わず hold を削除) は共通の `_latch_orphan_hold`
  機構であり、F383 への「再発」追記で記録する (F 番号は新設しない、同台帳の運用規則どおり)。

## 次の一手差分

### 完了

- [T-1409] `check_acceptance_reds.py` 自身の qstat 判定条件の欠陥ではなく、
  `tools/pegasus/dispatch_compute.py` 共有の `accounting_grace_s` (既定 60 秒) 満了 →
  `_fresh_qstat_gated_qdel` の fresh qstat が `request-absent` を返す、という単一の非決定的
  timing 経路であると切り分けた。恒久対応 (grace 窓拡張・probe 投入間隔の調整・
  `request-absent` の latch 条件見直し等) は未実施でユーザー裁定へ返す
  ({{T:orphan-hold-accounting-grace-margin}} を新規発行)。
  remaining: none
  base: 6a6314b0ccfd7628d32907a4f3fbcf82b74c082cc925017839874d2e1c9c00da

### 新規

- {{T:orphan-hold-accounting-grace-margin}} **P1・新規・ユーザー裁定待ち**: [T-1409] の診断結果、
  `check_acceptance_reds.py` の probe worktree dispatch が非決定的に orphan-hold へ到達する原因は
  `tools/pegasus/dispatch_compute.py` の `DEFAULT_ACCOUNTING_GRACE_S=60.0`
  (`result/log/accounting-grace-expired` → `_fresh_qstat_gated_qdel` の fresh qstat が
  `request-absent` を返し保守的に latch する) にある。恒久対応の候補は (a) grace 窓を広げる、
  (b) probe の複数 dispatch 投入間隔を空ける、(c) scheduler `END` 観測後の `request-absent` latch
  条件を緩める、のいずれかだが、(c) は latch の保守性 (F383 の教訓) を弱める可能性があるため
  正しさゲート (規律2) に触れない範囲でも設計判断としてユーザー裁定が必要。恒久対応は別 wave。
