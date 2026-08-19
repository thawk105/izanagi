---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1115-env-bytecode-check
seq: 1
title: '[T-1115] orchestrator/・tools/ 配下の env= 起動で PYTHONDONTWRITEBYTECODE 抑止が欠けている箇所を検出する checker (`tools/check_subprocess_bytecode_guard.py`) を新設した (コード+テスト+記録、branch worktree-dev-wave-t1115-env-bytecode-check、変異matrix = 6/6 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=non-attributable-only)'
---

## 本文

- command 引数は「裁定は不要」と明記していたため、段1〜4 は親裁定 (real/refuted) だけで
  ユーザー裁定へ戻していない。段3 敵対相談2レンズ (`--stage consult --lane luna` 固定、
  prompt本文だけで攻撃角度を分ける既定を継承) が独立に P1 の argv[0] 起点化・`-B` guard 認定・
  real-repo テスト欠落を real 所見として一致させた。
- 段5 実装後、親の焦点走 (consumer test 含む36 file) で2件の real 回帰を発見した。
  `tools/pegasus/dispatch_compute.py` の無条件 env 上書きが既存 passthrough テストを壊した件と、
  新設テストの自走 harness 欠如。段6 敵対レビュー2本がこれを検算しつつ、
  `tools/dev_wave_land.py` の同型パターン・sys.path bootstrap 欠如・アサーション粒度・
  分岐カバレッジ不足を追加で発見し、fix で解消した。
- 受入直前の local main 取り込みで `merge-message-provenance` (rc=70) に2回遭遇した
  (1回目は role=author trailer 欠如、pegasus-runbook.md §7.3 と同日の archive worklog
  entry 690・backlog [T-1399] に既知の同型事例あり、対処法も同じ = merge message へ
  Codex `role=author` trailer 追加)。2回目は受入待ち手 (`tools/dev_wave_wait.py`) 自身が
  待機中の main 前進で自己の bytes 束縛が陳腐化する `restart-required` (pegasus-runbook.md
  §7.3 記載の既知挙動、`receipt-waiter-sha256-mismatch`) で、新しい tip から再起動する以外の
  対処が無かった。さらに1回、`preclaim-history-provenance` が `TimeoutExpired` で落ちたが
  単独実行では43秒で正常終了し、一時的な輻輳と判断してそのまま再投入した。
- 受入 attempt4 (merge成功後) で pytest 自体が2件赤になった。1件は
  `test_check_subprocess_bytecode_guard.py::test_real_repo_clean` — **自分のwaveに帰属する
  実違反**で、local main 取り込みで他wave (詳細未特定、`test_dev_wave_wait.py` の
  `_real_waiter_repo`/`_run_real_self_report_merge_case` 周辺への並行追加) が
  checker 検出対象の新規箇所を持ち込んでいた。修正2巡を要した理由は checker の 1-hop
  関数解決が `repo, lease, env = _real_waiter_repo(...)` という **tuple-unpack 代入**を
  索引しない (checker の `_FileIndex.visit_Assign` は single-Name ターゲットしか見ない) ため、
  呼び出し先関数だけを guard しても届かず、呼び出し元関数自身の scope で guard する必要が
  あったこと。もう1件 `test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`
  は `docs/archive/worklog-phase3-0813-537.md` の固定バイト範囲 sha256 を比較するテストで、
  archived worklog への他wave由来の内容drift。自分のwaveと無関係と判断し、受入は
  `tools/check_acceptance_reds.py` 経由で `verdict=non-attributable-only` として正しく
  受理された (`red_nodeids=["orchestrator/tests/test_spool_fold.py::..."]`)。
- fix子 (`--stage fix`) の完了報告が2回、`tools/dev_wave_codex.py` の `-o` 出力が空 (rc=1) に
  なった。原因は `attempt-0001.output.md` (494 bytes) が `tools/check_codex_output.py` の
  `--min-bytes 500` を僅かに下回り不採用になったため (`accepted: false`, `validator_rc: 1`、
  `codex_exit_code` 自体は 0)。実際の成果物は `attempt-0001.output.md` に正しく書かれており
  fallback で読めた。親の fix prompt が「変更した file:line を明記するだけでよい」と
  簡潔な報告を求めたことが直接の原因。段8へ改善候補として記録する。
- checker の shallow 判定の既知限界 (tuple-unpack 代入を1-hop解決が追跡しない) は、
  `tools/check_subprocess_bytecode_guard.py` 冒頭 docstring の「deeper data-flow は
  analyse しない」という一般的な開示に含まれるが、tuple-unpack という具体形は明記していない。
  {{F:checker-shallow-tuple-unpack}} で構造化した。
- 新設テスト `test_real_repo_clean` は `orchestrator/`・`tools/` の全 `.py` を AST 走査し
  実測 8.3 秒を要する。既存の `orchestrator/tests/growth_test_holds.py` の登録機構
  (`_HOLD_ROWS`) は `_hold()` 内で単一の過去裁定定数 `RULING_2026_08_12_BUNDLE_3` にしか
  紐付かない設計であり、新規裁定なしに登録すると裁定引用を捏造することになるため、
  本 wave では登録せず現状 (既定走行に残す) を維持した。growth-hold 登録の要否は
  ユーザー裁定候補として次の一手へ新規計上する。

## 次の一手差分

### 完了

- [T-1115] `tools/check_subprocess_bytecode_guard.py` を新設し、22 既存 test file +
  2 production file (`tools/dev_wave_land.py`, `tools/pegasus/dispatch_compute.py`) への
  最小修正 (env dict への `PYTHONDONTWRITEBYTECODE` 追加) を実施、受入まで完了した
  (verdict=non-attributable-only)。
  remaining: none
  base: d939504ad1269622413cbcf5a032e8b66a2422a730abfc66b7dae6774d645673

### 新規

- {{T:subprocess-guard-growth-hold-ruling}} **P3・新規**: 新設した
  `test_check_subprocess_bytecode_guard.py::test_real_repo_clean` (実測8.3秒、
  `orchestrator/`・`tools/` 全 `.py` を AST 走査) を
  `orchestrator/tests/growth_test_holds.py` の growth-hold registry へ登録すべきか
  ユーザー裁定が必要。登録すると checker が既定走行から外れ将来の新規違反を受入で
  自動検出できなくなる一方、未登録のままだとコードベース成長に比例してこのテストの
  コストが伸び続ける。registry の `_hold()` は単一の過去裁定定数
  (`RULING_2026_08_12_BUNDLE_3`, 2026-08-12 rulings 第3束) にしか紐付かない設計で、
  新規裁定なしに登録すると裁定引用の捏造になるため見送った。
