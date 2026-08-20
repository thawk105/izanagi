---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t870-congestion-nproc
seq: 1
title: '[T-870] 受入全走のボトルネック分析 — item (e) 並列度低減は不成立と実測、opt-in recovery機構を次候補として記録した (docsのみ、branch worktree-dev-wave-t870-congestion-nproc)'
---

## 本文

- 依頼「受入全走のボトルネック分析・改善。リワードハック禁止」を受け、T-870系列
  (entry 769 commit `dd29fd9c`) が未着手のまま残していた (e) 「queue混雑時は待つのでなく並列度を
  下げる」(`IZANAGI_TEST_NPROC`) を、受入全走 (`orchestrator/tests` フルスイート) に適用できるかへ
  絞って着手した。着手前に `dev-wave-t870-lease-timing` (T-870の(a)(b)(c)実測、受入lease保持中)
  が同時に稼働中であることを確認し、その未land spool fragmentを読んで作業範囲が重複しないことを
  確認した。
- 段2 codex プラン (read-only) は、受入全走が `login_headroom.grant_budget()` を通ること・
  `IZANAGI_TEST_NPROC` が予算計算の入力に含まれないことを file:line で確認し、4GiB以内に収まる
  実測が無いため P1 (nprocを下げれば受入全走もlocalへ倒せる) は未立証と結論した。
- 親が既存 `login_headroom` モジュールを直接呼ぶ最小実測 (新規 driver 不要、DW-G01) を行い、
  `tests-full` の peak 台帳に 2026-08-06 付で 4GiB 上限ちょうどの記録が残っていること、
  `grant_budget()` の見積り計算が現行 peak がある限り nproc の値に関わらず恒常的に DISPATCH を
  選ぶこと、実際に `grant_budget(operation="tests-full")` を呼ぶと今日時点でも DISPATCH になる
  ことを確認した (ledger変更なし)。
- 段3 敵対相談2レンズ (sol=正しさ・一般化境界、luna=scope・reward-hack回避) が独立に、
  親の結論の核 (「現evidenceは(e)の受入全走実装を支持しない」) を支持しつつ、2つの過大な補助主張
  (「local実行は永久不可能」「実測空き容量が典型値」) を是正した。luna は独立に、D612の射程を
  超えない明示opt-inのpeak履歴無視recovery機構という安全な改善候補を提示した。
- 段4裁定: 実装しない (4→7→8→9)。理由は `output/insights/2026-08-20_t870-congestion-nproc/README.md`
  および同 wave の decisions fragment ({{D:t870-congestion-nproc-scope}}) に記載。
  新規発見 (peak履歴の内部回復機構欠如) は次の一手 (h) として本項目へ記録する。
- 段9受入全走投入時、queue congestionを実地に観測した (1回目: main前進後の全史provenance再監査が
  480秒枠でTimeoutExpired。2回目: merge・全史監査は通過したがdispatch自体がqueue-wait-timeout
  (900秒既定) で失敗、`ps`で少なくとも15以上の別waveが同じ受入lease/dispatch queueを同時に
  奪い合っていることを確認)。この際、T-870のopt-in override環境変数が受入形launcherの環境射影
  (`_acceptance_environment_preflight`が`pytest_addopts`/`pytest_plugins`/`task_run_id`/
  `task_runs_root`の4 field固定) に含まれず、受入・焦点走自体には構造的に届かないことをコードと
  実観測 (`--env-projection-json`の4キーのみ) で確認した。次の一手 (i) として本項目へ記録する。

## 次の一手差分

### 更新

- [T-870] **P2・(a)(b)(c)は別wave実測中・(e)は受入全走で不成立**:
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/`IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE`
  (`tools/run_tests.py`、commit `dd29fd9c`) により operator が自身の文脈を把握した上で明示的に
  上書きできるようになったが、既定挙動 (900秒/300秒) は変わらないため、通常の受入・焦点走は
  queue 混雑時に引き続き rc=16 で落ちる。(a) 受入lease claim〜land/release実時間の実測、
  (b) 既定walltime(3600秒)とlease TTL(2400秒)の関係、(c) `dev_wave_wait.py`の
  `--max-wait-seconds`不介入は、別wave (`dev-wave-t870-lease-timing`) が実測中/実測済み — 同wave
  の記録を正とする。(d) mutation harness自身へcaller-budget-awareな値を明示的に渡す設計
  (harnessの`timeout_seconds`/`hang_timeout_seconds`を読み、opt-in環境変数経由で安全な値を渡す)
  は未着手のまま持ち越す。(e) 「queue混雑時は待つのでなく並列度を下げる」
  (`IZANAGI_TEST_NPROC=4`が単独file実行 (`test_s8b_verdict.py`) では実例で有効だった) は、
  **受入全走 (フルスイート) には現evidenceでは不成立と確認した**: `login_headroom.grant_budget()`
  の admission 判定は `IZANAGI_TEST_NPROC` を入力に含まず、`tests-full` operation key の
  peak履歴 (2026-08-06付、4GiB上限相当の値が残存) の1.25倍見積りだけで判定するため、既定の
  呼出し経路ではnprocの値や現在の空き容量に関わらず恒常的にDISPATCHになる (実測含め詳細は
  `output/insights/2026-08-20_t870-congestion-nproc/README.md`)。この経路には
  staleness/expiry/decayによる自然回復が無い。(f) D299が既に裁定パッケージへ送っている
  lease invocation識別・fencing機構は、T-870固有の課題ではなくプロジェクトレベルで別途解決すべき
  前提条件として扱い、T-870側で先回りして解こうとしない。次回試行が設計に含めるべき新規の点
  (h): peak履歴を無視して一回限りlocal admissionを再試行できる明示opt-in機構。既存safety機構
  (lock・atomic write・`MIN_LOCAL_BUDGET_BYTES`・`MemoryMax`・CAP_OOM時のdispatch fallback) は
  すべて維持し、D612 (`docs/decisions.md:24540`) が禁止した既定値自動選択・`is_acceptance`分岐の
  いずれにも該当しない設計に限る。実装するなら専用のbrief→plan→consultを経ること。nproc実測は
  このrecovery機構と併せて次waveで行う (recoveryが無いとlocal試行自体が起こらないため、nproc単独
  の実測は今のままでは意味を持たない)。次回試行が設計に含めるべきもう1点 (i):
  opt-in override (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/`_OVERALL_GRACE_OVERRIDE`) を
  受入・焦点走launcherの環境射影 (`tools/dev_wave_wait.py`の`_acceptance_environment_preflight`)
  へ、既定不変・自動選択なしのまま到達させる設計を検討する。現状はad hocな手動dispatchにしか効かず、
  `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`拒否 (再現性保証) と衝突しない形が要る。専用のbrief→plan→consult
  を要する。
  base: 427d55c749e3af25a62be5618ea67bb81e0e5b22e6485171d84c8162835fa1ef
