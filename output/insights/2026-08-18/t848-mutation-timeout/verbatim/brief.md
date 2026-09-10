# 段 1 brief — [T-848] 変異 TIMEOUT の意味を実行 timeout に限定する

wave: dev-wave-t848-mutation-timeout / branch: worktree-dev-wave-t848-mutation-timeout
base: 2a3b505516071992a9d9cf34479383d7178e23b3 (local main と同一, clean)
repo (worktree): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout

## 直したい欠陥 (親が実測で確認した事実のみ)

- `tools/mutation_harness.py:1646` (`_observed_status`): `result["timed_out"]` が真なら無条件で
  `"TIMEOUT"` を返す。計算ノードで実行が始まったかを一切見ていない。
- `tools/mutation_harness.py:1558` (`_run_tests`) / `:1618` の `process.communicate(timeout=timeout_s)` は
  **dispatch subprocess 全体**に掛かる。`timeout_s` は呼び出し側で `spec.timeout_seconds`
  (baseline: `:1309`, `:1693`) または `spec.hang_timeout_seconds` (`:1811`, hang_risk 変異のみ)。
  したがって request が `QUE` のまま超過した場合も `timed_out=True` になる。
- `tools/mutation_harness.py:40`: `TERMINAL_STATUSES` が `TIMEOUT` を含む。結果:
  - `_summary` (`:1924`) が `completed` に数える。
  - `_summary` の `recorded` は record 数なので、**一度も走っていない変異でも
    `registered == recorded` かつ `completed == registered` が成立する。**
  - resume 経路 (`:2346-2352`) が terminal として `kept` に入れ、再実行しない。
- 判定に使える証拠は実在する (DW-O13 の実在確認 — 実 artifact で確認済み):
  `output/insights/2026-08-03_t357-mutation-transport-smoke/evidence/leg1-dispatch-submissions/e1589343194f51df2fc28103718c1d54/receipt.json`
  は `schema_version = "pegasus-dispatch-receipt/v2"` で、`queue_wait_observed: true`、
  `queue_wait_s: 5.223764462978579`、`state_history: [{"state":"QUE",...},{"state":"RUN",...}, ...]` を持つ。
  producer 側は `tools/pegasus/dispatch_compute.py:1825-1837` (RUN 初観測時に `run_seen=True` と
  `queue_wait_observed=True` を receipt へ固定) と `:1862-1865` (RUN 未観測終端では
  `queue_wait_observed=False`)。
- harness は timeout 時に既に receipt を回収している: `tools/mutation_harness.py:1633`
  (`result["request"] = _recover_dispatch_request(repo, dispatch_before)`) と `:1495-1537`。
  ただし現状は `request_id` / path / `outcome_rc` しか取り出さず、RUN 有無を読んでいない。

## 既存被覆 (純増検出力を測るための先行検索)

「走っていない変異が terminal 扱いされる」性質を止める既存機構は 1 つだけ実在する:
`tools/mutation_fanout_contract.py:1043-1046` が併合時に `TIMEOUT: 0` を要求し、TIMEOUT を含む
shard を丸ごと拒否する (D289 決定 (3))。**これは fan-out 併合経路にしか無い。**
本 wave の純増検出力は「逐次経路 (`mutation_harness` 単体走) と
`tools/mutation_worktree.py` wrapper 経路で、queue 側 timeout が terminal に数えられない」ことである。

## 不変条件 (緩めてはいけない)

1. 規律 2/3: 判定が付かない場合は必ず **非 terminal 側へ倒す** (fail-closed)。
   receipt 不在・読取不能・state 不明を「実行 timeout」に分類してはならない。
2. 実行 timeout の記録能力を失わせない。DW-M06 は hang 変異の timeout を
   「fail-open へ倒れた証拠」として使う。RUN が確認できた timeout は従来どおり terminal な `TIMEOUT`。
3. 既存テストの期待値を緩めない・反転させない。
4. 台帳 summary の欄集合は 3 箇所で exact に固定されている (`tools/mutation_harness.py:1924-1934`,
   `tools/mutation_fanout_contract.py:119-122`, `tools/mutation_worktree.py:841-850`)。
   欄を増やすならこの 3 箇所すべてを同時に動かす。`TERMINAL_STATUSES` の複製は
   `tools/mutation_harness.py:40` と `tools/mutation_worktree.py:35` の 2 箇所。
5. 台帳 schema 文字列 `izanagi-dev-wave-mutation/v4` は 4 箇所に固定されている
   (`tools/mutation_harness.py:30`, `tools/mutation_worktree.py:31`,
   `tools/mutation_fanout_contract.py:19`, `orchestrator/tests/test_mutation_worktree.py:137`)。
   さらに `docs/pegasus-runbook.md:1362` が同文字列を本文で参照している。
   schema を上げるか据え置くかは段 2 で file:line 単位に決めること。
6. 凍結側の確認結果: 変異台帳を bytes で pin する `FROZEN_MANIFEST` / generator hash pin は
   検索して **0 件**だった。よって DW-O08 / O09 / O10 は本 wave では成立しないと親は判断している
   (この判断自体も攻撃対象)。

## 親の provisional 裁定 (すべて攻撃対象)

- **(P1) 新 status は非 terminal とする。** `QUEUE_TIMEOUT` を新設し `TERMINAL_STATUSES` に入れない。
  `completed` に数えず、resume では `PARSE_ERROR` と同じく `nonterminal_history` へ送って再実行する。
  成果物影響: これを入れないと変異台帳の `completed == registered` が偽の緑を出し続け、
  worklog へ書く「N/M KILLED」という検出力の主張そのものが汚染される。
- **(P2) 分類は receipt の肯定的証拠だけで行う。** `queue_wait_observed is True` (または
  `state_history` に `RUN` が現れる) のときだけ `TIMEOUT`、`queue_wait_observed is False` かつ
  `state_history` の最終 state が `QUE` のときだけ `QUEUE_TIMEOUT`。それ以外
  (receipt 不在 / 壊れている / state 不明) も `QUEUE_TIMEOUT` へ倒すが、record に
  「どちらの証拠で分類したか」を構造化して残す (規律 3)。
  成果物影響: 証拠欄が無いと、後から台帳を読んだ人が「本当に queue で止まった」のか
  「証拠が取れなかった」のかを区別できず、再解釈が再び不能になる。
- **(P3) `runner_mode` が dispatch でない (local) 経路の timeout は従来どおり `TIMEOUT`。**
  queue が存在しないため。
- **(P4) 既存台帳の再解釈は「対象ゼロ」である。** 親が repo 全体の台帳型 JSON 762 件を
  全件走査した結果、`summary.TIMEOUT > 0`・`status == "TIMEOUT"` の record・
  baseline TIMEOUT はいずれも **0 件**だった (probe は repo 外:
  `/home/SFC/tanab/.claude/jobs/83ce835f/tmp/dev-wave-t848/scan_timeout.py`)。
  よって成果物は「過去記録の書き換え」ではなく「不在の実測 + 今後の記録の読み方」とする。
- **(P5) spec の `expected_status` に `QUEUE_TIMEOUT` を追加しない。**
  `EXPECTED_STATUSES` (`:41`) は `KILLED/SURVIVED/TIMEOUT` のままとする。
  queue 待ちは変異の性質ではないので事前登録できてはならない。
- **(P6) fan-out 併合器 (D289 決定 (3)) の TIMEOUT 全面拒否は本 wave では緩めない。**
  ただし `QUEUE_TIMEOUT` が未知 status として素通りしないことは確認する。

## 成果物

1. `tools/mutation_harness.py` / `tools/mutation_worktree.py` の実装 (Codex author, D95)。
2. `orchestrator/tests/test_mutation_harness.py` ほか必要なテスト。
3. 変異 matrix (新設分類が実際に検出力を持つことの裏取り)。
4. worklog / decisions fragment (P4 の不在実測と、今後 `QUEUE_TIMEOUT` を見たときの扱い)。

## 分割方針

編集面が `tools/` 2 file + テストで一枚岩に近い。段 5 は 1 単位で投入する。

## 受入・実測の環境

acceptance は worktree 内で `python3 tools/run_tests.py` (相対・素の argv ちょうど)。
変異本走は `--runner-mode dispatch` + runner argv に `--force-dispatch` (DW-M07)。
主戦場は Pegasus login node、計算は dispatch 経由。
