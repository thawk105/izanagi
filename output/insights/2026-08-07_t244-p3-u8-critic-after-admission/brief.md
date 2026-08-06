# [T-244] P3 critic 後置 (U-8) — 段 1 brief

**scope.** 8c 自律 trial (`orchestrator/campaign/p3_autonomous_workload_trial.py`) の critic 呼び出しを、
cell の Layer 3 admission (`_finalize_build_cell_admission`) より**後**へ移す。付随して完了性検査
(`orchestrator/campaign/autonomous_trial_completeness.py`) の受理集合を追随させ、D96 に従い
新しい D と境界テストを同一変更単位に含める。

**確定済みユーザー裁定.** U-8 = 「移す」(2026-08-05 /rulings、正本 =
`output/insights/2026-08-05_t244-p3-design/README.md` §9 表 U-8 行および §5.4)。
理由は「移さないと commit-reveal が名乗りだけになる」。

**不変条件.**
- ledger seal と proof 書き込み (origin-proofs sidecar / report v3) の後置は **scope 外** — D201 が
  8c への origin ledger 結線を「実装しない」と裁定し、sidecar / report v3 は前 wave が却下済み。
  本 wave で ledger を結線しない。
- D114 の承認上限 `MAX_APPROVED_GENERATIONS = 1`、D114 の cap=1、trial registry の
  `certifying=False` / `arm_binding="declared-only"` を変えない。
- 規律 2 / 3: critic へ渡る情報を減らすことを口実に、machine preview・auditor gate・WAL admission・
  完了性検査のいずれも緩めない。緩める方向の変異は採用しない。

**成果物影響 (DW-G05).** certified 選択・材料レポート・試行台帳の現在値と参照は**不変** (P3 は依然 FAIL、
閉じた成果層は 0/11 のまま)。変わるのは 8c 非認定 pilot の `report.json` / `attempts.jsonl` における
critic event の到達時点と、完了性検査の受理集合である。実装しない場合、設計 §5.4 の漏洩経路 (ii)
「critic payload が seal 前に連続値 metrics を受け取る」が残り、8c の commit-reveal は名乗りだけのままになる。

**発火経路 (DW-G04).** 既存 artifact path = `orchestrator/tests/test_p3_autonomous_workload_trial.py` が
`FixtureRoleProvider` 経由で `run_trial` を実走し `report.json` / `attempts.jsonl` を実生成する経路。
新しい計測 ID も本番 provisioning も要らない。

**成果物の形.** (1) driver の critic 後置、(2) 完了性検査の状態機械追随、(3) 境界テスト更新
(`test_state_machine_rejects_nonprefix_roles` ほか) と後置を pin する新テスト、(4) 新しい D、
(5) insights + spool fragment。

**親の provisional 裁定 (攻撃対象).**
- **(P1)** scope を「Layer 3 admission 後置のみ」に限る。3 anchor のうち 8c に実在するのはこれだけ。
- **(P2)** 移動粒度は **cell 単位** — `_finish_trial` が cell ごとに admission を確定した直後に、
  その cell の全 generation の critic をまとめて呼ぶ。admission は cell 単位にしか存在しない。
- **(P3)** critic invalid は後置後も cell の `stop_reason` を `role-invalid` にする意味を保つ。
  admission_decision は確定済みのまま残し、report に両方載る。
- **(P4)** `generations >= 2` では critic → `prior_critic_reverse` の還流が構造的に成立しなくなる。
  承認上限 1 (D114) のため承認運転では挙動不変 (実測: `prior_reverse` は cell ごとに `None` 初期化、
  consumer は次 generation だけ) だが、実装上限 10 の経路では意味が変わる。fail-closed にするか
  還流断を明示記録するかは段 4 で裁定する。

**新規検出力 (性質での既存被覆検索).** 「critic 呼び出しが cell admission より後に起きる」を pin する
性質は現状どのテストにも無い (既存は generation 内 role presence の prefix 検査と
`test_critic_relation_oracle_detects_candidate_derived_evidence_leak` の leak oracle のみ)。
純増は「順序の反転を検出する」1 点。

**並列分割方針.** 編集面は driver と完了性検査 + テストの 2 面だが、状態機械の意味が一体なので
段 5 は Codex `role=author` 1 単位とし、段 6 の敵対レビューを 2 レンズ並列にする。

**受入・実測環境.** 本 worktree の repo root で `python3 tools/run_tests.py` 全走 (Pegasus login node)。
変異 matrix は `tools/mutation_harness.py`。
