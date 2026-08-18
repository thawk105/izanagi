# 親の実測 (すべて計算ノードまたは library 経路。時刻は JST)

## 判定器 (library 経路)

`orchestrator.campaign.s8c_preregistration_evidence.get_registry().evaluate_all(head, repo_root=root)`
を直接呼んだ。CLI は全条件を `evaluator-exception` へ潰すため一次資料にしない。

- 起点 `38f173cb` (18:05): C04 = UNSATISFIED / crash-policy-cell-partial、
  C11 = EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable、
  C12 = UNSATISFIED / allocation-enforcement-consumer-absent。
- main ff 取り込み `54baeb86` (19:45): 3 条件とも同じ値 (t1333 の land は 3 条件を動かさない)。
- 実装 commit `ce8c2f50` (20:45): C04 / C11 / C12 の 3 条件とも
  EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable。

## C11 が既に成立していたことの実測 (18:10)

`orchestrator/campaign/p3_autonomous_workload_trial.py` (起点 `38f173cb` 時点の行番号):
`MAX_APPROVED_GENERATIONS = 2` (:126)、`_validate_generation_budget` 定義 (:395)、
呼び出し 3 件を AST で関数へ帰属させた結果 — :2801 → `_run_workload`、:3296 → `run_trial`、
:3772 → `main`。`apply_critic_feedback` は :2906 = `_run_workload`。
runtime の被覆も既にあり (`test_two_generation_critic_feedback_precedes_next_planner`)、
production 変更もテスト追加も不要と裁定した。

## 焦点走 (計算ノード dispatch、10 test file)

| 時刻 | 対象 tip | 結果 |
|---|---|---|
| 19:44 | 実装 (未 commit) | 8 failed / 900 passed |
| 20:50 | `ce8c2f50` | 4 failed / 1206 passed |
| 21:40 | `80a785f2` | 0 failed / 1210 passed |
| 22:16 | `a026cc37` | 0 failed / 1214 passed |

19:44 の 8 件のうち 4 件は判定器が commit を読むことによる commit 待ちの赤で、
`ce8c2f50` を作った時点で消えた。残る 4 件が本物の赤だった。

対象 file: `test_p3_autonomous_workload_trial.py`, `test_trial_registry.py`,
`test_s8c_preregistration_predicates.py`, `test_s8c_preregistration_invariant.py`,
`test_s8c_preregistration_core.py`, `test_claude_transport.py`, `test_reservation.py`,
`test_autonomous_trial_completeness.py`, `test_layer3_report.py`,
`test_reflux_origin_binding.py`。

## 変異 matrix

- probe (21:58 投入、22:07 完了): baseline PASSED、KILLED 2 / MISMATCH 9 / SURVIVED 1。
  MISMATCH 9 件はすべて「実際に落ちる node 集合が親の予測より広い」型で、
  期待 node 集合の導出に使った。SURVIVED 1 件が本物の検出穴 (README 参照)。
- 本走 (22:19 投入、22:38 完了、tip `a026cc37`): **baseline PASSED・12/12 KILLED・
  SURVIVED 0・MISMATCH 0**。

## 実行環境

- Python 3.10.12。`BaseException.add_note` は 3.11 以降の API であり**存在しない**。
  これが恒真な握り潰しの原因だった。
- テストは Pegasus の計算ノードへ dispatch して実行した。login では
  `qstat -Q` の preflight が rc=1 になり、codex の子は pytest を実走できなかった
  (子の報告はすべて「実装済み・未実走」)。実測は毎巡 親が引き受けた。
