---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t870-dispatch-grace
seq: 1
title: '[T-870] 受入・焦点走dispatchのqueue-wait/overall-grace既定値是正を調査し、自動選択は不採用、opt-in環境変数機構を実装した (コード+テスト、branch worktree-dev-wave-t870-dispatch-grace、変異matrix=baseline PASSED・4/4 KILLED・SURVIVED0・MISMATCH0)'
---

## 本文

- 前 wave `accept-bottleneck-chain` (worklog archive entry733) が Unit B としてこの論点を段2プラン
  →段3敵対相談まで進めたが、BLOCKER 1件・MUST-FIX 3件を検出し未実装のまま見送っていた。本 wave は
  その続きとして着手した。
- 段2 codex プランの結論: brief の (P1)「lease TTL (2400秒) を超えない bounded 値」は、実測すると
  ほぼ改善余地が無い (`Q+G<=770〜1070秒`、現行900秒からの伸びしろが乏しい)。加えて既定 walltime
  (3600秒) 自体が既に lease TTL を超えている latent gap を新たに発見した。
- 親が段2完了後に `tools/run_tests.py:528` の `_is_acceptance_run(args)` という既存の正規注入
  seam を見つけ、「受入形かどうかで timeout 値を分岐する」新方針を立てたが、**段3敵対相談2レンズが
  独立に BLOCKER と判定し却下した**。lensA (sol) が具体的反例を提示: 受入lease保持中
  (land/release前) に同一operatorが targeted な `python3 tools/run_tests.py --force-dispatch
  <target>` を実行すると `is_acceptance=False` になり、大きい timeout を選べてしまう。
  `docs/decisions.md` D299 が「lease自己保持はwave slug digestだけでinvocationを識別しない」
  ことを既に文書化・裁定パッケージへ送る対象と明記しており、この設計はその既存裁定の射程を
  無断で侵すと判断した。lensB (luna) は独立に mutation harness (個別runnerに900〜5400秒の
  timeoutを課す、collectionは`_default_dispatch`を経由せず`dispatch_compute.py`を直接呼ぶ) との
  衝突を検出した。
- 段3は同時に、前wave由来の「55分・2.5時間」という queue 滞留時間の数字が本 repo のどこにも
  一次資料を持たないことを確認する一方、`docs/archive/worklog-phase3-0816-566-567.md`
  (83分間 gen_S が待機列のみで queue-wait-timeout を3回返した実例)・
  `docs/archive/worklog-phase3-0804-187.md` (保守明けQUE 227滞留で`--overall-grace 21600`
  =6時間が要った実例) という未引用の一次資料を発見した。実際の congestion は数十分〜時間
  オーダーで現実に起きており、lease TTL 内に収まる値では原票の症状を解消できない。
- 段4裁定 (詳細は {{D:t870-opt-in-dispatch-override-scope}}): 自動分岐・新既定値のどちらも
  選ばず、`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/`IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE`
  という2つの opt-in 環境変数上書きだけを実装した (未設定なら現行既定900秒/300秒を完全維持)。
- 段5実装 (Codex role=author) は親が実測 (`test_run_tests_preflight.py -k default_dispatch`
  =14 passed、既存consumer `test_pegasus_dispatch_compute.py` 2件も非退行)。段6敵対レビュー2本
  はレンズB (scope遵守) 所見ゼロ、レンズA (正しさ) が MUST-FIX 1件 (`float("-1e-324")` が
  IEEE754 underflow で `-0.0` になり負数判定をすり抜ける境界値バグ)・NIT 1件
  (`dispatch.assert_not_called()` 未固定) を検出、fix で両方対応し焦点再レビュー1本で
  closed 確認。統合commit `dd29fd9c`。変異matrix (4件事前登録) は baseline PASSED (16 passed)・
  4/4 KILLED (node集合完全一致)・SURVIVED 0・MISMATCH 0。
- 棄却した所見: 前wave由来の bounded 数値案 (段2算術で不成立と判明)、親が新規提案した
  is_acceptance ベース自動分岐案 (段3両レンズが BLOCKER)。いずれも実装せず記録に留める。

## 次の一手差分

### 更新

- [T-870] **P2・opt-in機構は実装済み、自動選択は未解決**: `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE` (`tools/run_tests.py`、commit `dd29fd9c`) により
  operator が自身の文脈を把握した上で明示的に上書きできるようになったが、既定挙動 (900秒/300秒)
  は変わらないため、通常の受入・焦点走は queue 混雑時に引き続き rc=16 で落ちる。次回試行が設計に
  含めるべき点: (a) 受入lease claim〜launcher-start〜postrun〜receipt-publish〜land-lock〜release
  の各時刻を実測し、claim/land保守予算 H を確定する。(b) 既定walltime(3600秒)がlease TTL(2400秒)
  を超える latent gap を是正する (D133時代は30分だった形跡があり、いつ60分へ引き上げられたか
  未追跡)。(c) `dev_wave_wait.py` の `--max-wait-seconds` が起動済みlauncherのdispatch待ちを
  中断できない構造的欠陥 (`_LauncherSession.wait()`が`timeout=none`) を、待ち手コアの書き起こし
  ではなく既存claim/renew/release関数の呼出しで閉じる設計を検討する。(d) mutation harness
  自身へcaller-budget-awareな値を明示的に渡す設計 (harnessの`timeout_seconds`/
  `hang_timeout_seconds`を読み、本waveが追加したenv var経由で安全な値をopt-inする)。
  (e) 「queue混雑時は待つのでなく並列度を下げる」という別解 (`IZANAGI_TEST_NPROC=4`が実例で
  有効だった) も選択肢に含める。(f) D299が既に裁定パッケージへ送っているlease invocation
  識別・fencing機構は、T-870固有の課題ではなくプロジェクトレベルで別途解決すべき前提条件として
  扱い、T-870側で先回りして解こうとしない。
  base: d0b9cb2ff0eddd9a2ea010297c4a4045fc06e53416cb7678a015c4ebfb417552
