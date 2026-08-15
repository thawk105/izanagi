---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t244-8c-multigen
seq: 1
title: 8c の多世代を人間ループ同等の射影に限って開放する — 承認上限 1→2、還流を白名単で機械的に閉じ、正直な計数を出す (コード + テスト、branch worktree-dev-wave-t244-8c-multigen)
---

## 本文

- 2026-08-13 18:00 JST のユーザー裁定 (控え =
  `dev-wave-jobs/rulings-inbox/2026-08-13-t244-8c-multigeneration-human-loop-parity.md`) に従い、
  8c の承認上限を 1 から 2 へ上げ、世代間で運んでよいものを
  descriptor + abstract whiteboard + critic 二層射影に機械的に閉じた。設計判断は {{D:multigeneration-whitelist}}。
- **段 1 前提実測で裁定控えを超える事実が 5 件出た。** (a) `apply_critic_feedback` は
  production に存在せず、名前だけ s8c 契約が固定していた。(b) critic は世代ループ内で走っておらず、
  critic 出力が次世代へ届く経路は 1 本も無かった。(c) 既存テストは cap を monkeypatch して
  2〜3 世代を回しており、**多世代ループ自体は動いていた**。(d) s8c C11 は 12 条件すべて
  `machine_checkable: false` で dormant。(e) 本 wave は `FROZEN_MANIFEST` 対象 bytes を変えない。
- **(c)(d) の親の記述は敵対レビューが 2 件とも訂正した。** 既存の多世代テストは注入 drive を
  使っており標準 `trigger.drive_iteration` を通っていない (F15 型)。dormant な C11 は
  `EVIDENCE_UNDEFINED` = **未充足**であって緑ではなく、cap 引き上げの権威根拠に使えない。
- **`test_multi_generation_deferred_critic_fails_closed` が「cap=2 の 2 世代運転は
  `RuntimeError` で止まる」を既にテストで固定していた。** つまり cap だけ上げても report は
  1 件も発行できず、critic の実行位置の決定はユーザー裁定を実行するための不可欠な構成要素だった。
  D217 / U-8 との関係と親の限定 supersede は {{D:intermediate-critic-position}}。
- **段 3・段 6 の敵対レビュー計 4 本が親の誤りを 6 回止めた。** 内訳は段 3 で裁定 1 件
  (性能値 3 欄の扱い)、段 6 で親の誤指示 2 件 (digest の扱い・検査の適用範囲)、
  親の見落とし 1 件 (budget==1 の受理集合変更)、恒真 validator 1 件 (両レンズ独立)、
  凍結 golden の再生成 1 件。**焦点走が全緑 (508 passed) になった後に、
  敵対レビューが中心的保証の恒真性を暴いた**のが本 wave 最大の収穫である。詳細は {{F:tautological-external-expectation}}。
- **wave 前テストの期待値改変が 1 件あった。** `test_cli_default_is_literal_one_by_ast` の
  `assert len(calls) == 1` が `== 2` へ書き換えられていた。F72 の恒久対応そのものである。
  production の `add_argument` は元から 1 個で**防壁の実装は無傷**、変えられたのはテストだけだった。
  base へ復元し、`git diff 43ac2d67 -- orchestrator/tests/` の全数走査で
  **親の明示裁定が無い期待値変更は他に 0 件**と確認した。
- **変異 spec を書いた子が親の登録 3 件を差し戻して再照準した (F28 型)。** 親が fix 報告から採った
  MUT-6/7/8 の kill 予定 node は対象 helper を monkeypatch するため、production anchor の変異では
  赤にならない。そのまま走らせれば偽の KILLED で検出力を過大証明していた。
- **変異 matrix 第 1 走は SURVIVED 0 / MISMATCH 9。** 9 件は「意図した gate は発火したが
  期待 node 集合が完全でない」もので、本 wave が新設した横断検査により同じ分岐に依存する
  テストが増えたことが原因。実測から完全集合を再導出して再走し、**18/18 KILLED・MISMATCH 0**
  (baseline PASSED、TIMEOUT 0、PARSE_ERROR 0)。生台帳 =
  `dev-wave-jobs/2026-08-14_t244-8c-multigen/mutation/ledger-v2.json`。
- **ユーザー手番の値を実測根拠つきで用意した。** 8c 経路そのものの bench 実測は存在しない
  (runbook §3.3 が現 Pegasus で実行不能) ため、`output/s1-budget/time_ledger.json` の
  develop phase 実測 (n=33、中央値 166.2 秒、最悪 379.3 秒) を代理に使った。3 workload の trial で
  G=2 は role query 24 回・中央値 ≈997 秒・最悪 ≈2275 秒で既定 `max_wall_s = 3600` に収まる。
  G=3 は最悪 ≈3414 秒で既定に接し、G=4 以上は超える。**既定 wall 予算を動かさずに済む最大は
  G=3、安全側は G=2。** 代理データである点と LLM 応答時間を含まない点は裁定へ明記した。
- **運用の噛み合わせ問題を 3 件実測した。** (i) codex 子の sandbox writable root は repo 内だけで、
  `--spec` / `--out` を repo 外必須とする変異 harness と噛み合わない。
  (ii) `--attempt-out` / `--wrapper-attempt` は `--runner-mode dispatch` 専用。
  (iii) `run_tests.py` の bounded local は前回ピークから次回予算を見積もるが、その小さい予算では
  cgroup attest が落ちて `rc=16` になるため、**同一 target set を 19 回繰り返す変異走行は
  local mode では回せない**。`qstat -Q` は親からは rc=0 (子の rc=1 は sandbox が socket を塞ぐため)。
- 焦点走 = 585 passed / 0 failed / 82.51 秒 (2026-08-15 09:18 JST)。

## 次の一手差分

### 更新

- [T-244] **P3・8c 多世代開放を実装 land (本 wave)。残るユーザー裁定 7 件**:
  承認上限 2、白名単の機械強制、正直な計数、8c 専用 wrapper を land した。
  ユーザー手番は (1) {{D:intermediate-critic-position}} の限定 supersede の追認、
  (2) 開放世代数の上限値と総 query / ベンチ実時間の予算値の確定 (本 wave の実測候補 = 安全側 G=2 /
  既定 wall を動かさない最大 G=3)、(3) P9 の一般閉包の起票順、(4) P1 / P2 残余 / P5 残余 (U-2) の
  充足状態、(5) 注入 seam と `drive_iteration()` 直接反復を保証対象へ入れるか、
  (6) planner→coder 3 field の意味的非干渉を禁止するか、(7) s8c C11 の artifact 2 件を作るか。
  正本 = `dev-wave-jobs/2026-08-14_t244-8c-multigen/s4-ruling.md` §7。
  base: f2e7e2a5a96395870b1e18e48738cab27811d024cea6a75bb14ccf5db1b2f3c2

### 新規

- {{T:p9-whiteboard-closure}} **P3・新規**: P9 (whiteboard 値域と iteration 整合) の一般閉包。
  本 wave は 8c の payload validator で 8c 経路だけを塞いだ。`state_from_dict` の iteration 整合、
  `project_whiteboard` の in-memory 値域、`layer3_report` の独立 reader は未閉包のまま。
- {{T:mutation-spec-offrepo-write}} **P2・新規**: codex 子の sandbox writable root は repo 内だけで、
  `--spec` / `--out` を repo 外必須とする変異 harness と噛み合わない。本 wave は repo root へ
  書かせて親が移す運回避で通したが、dev-wave 側の恒久手当てを決める。
- {{T:bounded-local-peak-budget}} **P2・新規**: `run_tests.py` の bounded local が前回ピークから
  見積もる予算では cgroup attest が落ち `rc=16` になる。同一 target set の 2 回目以降が必ず当たり、
  変異走行を local mode で回せない。
