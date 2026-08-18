# 段 1 brief — 8c 条件 C12 / C04 (+ C11 実測) の production consumer 配線

wave branch: `worktree-dev-wave-s8c-c12-c04-c11`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11`
起点 main: `38f173cb` (2026-08-18 18:00 JST 時点、乖離 0)

## 親の起動時実測 (子はこれを疑ってよい。全部 attack 対象)

判定器は `orchestrator/campaign/s8c_preregistration_evidence.py`。library 経路
(`get_registry().evaluate_all(head, repo_root=root)`) で HEAD を評価した実測値:

| 条件 | 現状 status | reason |
|---|---|---|
| C04 | UNSATISFIED | crash-policy-cell-partial |
| C11 | EVIDENCE_UNDEFINED | completion-proof-not-machine-checkable |
| C12 | UNSATISFIED | allocation-enforcement-consumer-absent |

**(M1) `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` は機械検査を全通過した
合格終端である。** `SATISFIABLE_CONDITION_IDS = frozenset()` であり、機械検査可能条件が
`SATISFIED` を返すと `evaluate_all` がそれを `ERROR / evaluator-internal-error` へ潰す
(`s8c_preregistration_evidence.py` の `evaluate_all` 内)。したがって到達可能な最良状態は
`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` である。

**(M2) C11 は既に合格終端に到達している。** `_evaluate_c11` が要求する形は
`orchestrator/campaign/p3_autonomous_workload_trial.py` に全部実在する:
- `MAX_APPROVED_GENERATIONS = 2` (:126、`cap >= 2` を満たす)
- `_validate_generation_budget` の定義 (:395) と 3 境界からの直接 call —
  `_run_workload` (:2801)、`run_trial` (:3296)、`main` (:3772、`args.max_generations` を渡す)
- `_run_workload` 内の `apply_critic_feedback` (:2906)
- `s8c_generation_projection.py` 側の `_CRITIC_KEYS` / `_DIAGNOSTIC_METRICS` 代入と
  `apply_critic_feedback` / `_validate_critic_projection` / `validate_planner_payload` 定義
関数帰属は AST で照合済み (2801→`_run_workload`, 2906→`_run_workload`, 3296→`run_trial`,
3772→`main`)。**よって C11 に production 変更は要らない。** 引数の「3 境界すべてで要求せよ」は
既に成立している。

**(M3) C12 が止まっているのは allocation gate だけ。** `_c12_allocation_binding_verdict` は
`reservation.py` に `read_binding` / `check_reservation` が定義され、かつ **`run_trial` の
module 内 reachable call 集合**に両名が入ることを要求する。`reservation.py` 側は実装済み
(:159 `read_binding`, :218 `check_reservation`, :27 `ReservationBinding`, :273
`is_reservation_required`)。欠けているのは p3 側の消費だけ。
gate 通過後に `env_contract.lookup` と `execution_guard.attest_and_build_receipt` が
`main` からの跨 module 到達 (`_ReachabilityExplorer`) で見えることも要る。現状 p3 は
`attest_and_build_receipt` を 0 回呼んでおらず、env は `trigger._admit_env_contract(site)`
経由 (:987, :1082, :2811) である。**到達成立の可否は未実測。段 2 で file:line で確定させる。**

**(M4) C04 の 2 つの consumer は repo に 1 件も存在しない。**
`mark_experiment_indeterminate` (p3 側) と `forbid_trial_restart` (trial_registry 側) は
判定器と契約 JSON 以外に出現しない。`_evaluate_c04` は `main` からの到達 graph で
両名の `_declared_call` を要求し、さらに `trial_registry` に `forbid_trial_restart` の
**定義**を要求する。crash 捕捉点は既存: `run_trial` の `except BaseException as exc` (:3524)、
`_run_workload` 系の `except BaseException as terminal_error` (:3235)。

**(M5) 凍結 bytes の pin 閉包は 0 件 (DW-O09/O10 不成立)。**
`grep -rn "p3_autonomous_workload_trial" --include=*.py` と同 `trial_registry.py` の全件を
見た結果、この 2 module の bytes を pin する台帳・test・trust root は無い。存在するのは
(a) 記号レベルの不変検査 `test_s8c_preregistration_invariant.py`、(b) 実 repo の status
snapshot (下記 M6)、(c) 過去 wave の変異台帳 (歴史記録)。
凍結世代 `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g7.json` が pin して
いるのは preregistration markdown と契約 JSON の hash (`evidence_contract_sha256`,
`section6_condition_hashes`) であって production コードではない。契約 JSON を触らない本 wave では
**再凍結は要らない**。scope 外指定と整合する。

**(M6) 反転させねばならない consumer 検査 (実測で列挙)。**
- `orchestrator/tests/test_s8c_preregistration_predicates.py:157,165` — 実 repo の全 12 条件
  status/reason を exact dict で pin する gap ledger。C04 と C12 が反転する。
- 同 `:2029` 付近 `test_current_repository_c12_registry_reports_unwired_allocation_consumer` —
  本文コメントに「production が正しく配線されたら反転させる snapshot tripwire である」と
  明記された tripwire。**削除でなく、配線済みを pin する向きへ反転**させる。
- `orchestrator/tests/test_s8c_preregistration_invariant.py` の
  `MACHINE_CONTRACT_FUNCTION_CHECKS` / `MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` は
  `assert checked == ...` / `assert excluded == excluded_pin` の exact 集合比較である。
  C04 の 3 件 —
  `("C04", p3, "mark_experiment_indeterminate", "declared-unimplemented-token")`,
  `("C04", trial_registry, "forbid_trial_restart", "declared-unimplemented-token")`,
  `("C04", trial_registry, "reject_started_trial", "declared-unimplemented-token")` —
  は実装した瞬間 excluded から checked へ移る。**両集合を同時に直さないと必ず赤。**
  C12 側の `"reservation.read_binding"` 等は非 identifier token なので分類は変わらない (要再確認)。

## scope

**実装する。**

1. **C12**: `run_trial` が campaign launch の**前に**、登録済み環境 attestation
   (`env_contract.lookup`) と calibration attestation
   (`execution_guard.attest_and_build_receipt`) に加えて予約束縛
   (`reservation.read_binding` → `reservation.check_reservation`) を消費し、
   (a) PBS job 不一致、(b) boot 不一致、(c) 予約期限までの残時間不足 を launch 前に拒否する。
   判定器が要求する到達形 (`run_trial` の module 内 reachable calls に `read_binding` と
   `check_reservation`、`main` からの跨 module 到達に `lookup` と
   `attest_and_build_receipt`) を満たすこと。
2. **C04**: production の crash 捕捉経路が、戻る前に (a) 実験全体を indeterminate と記録し
   (`mark_experiment_indeterminate`)、(b) registry の no-restart consumer
   (`forbid_trial_restart`) を呼ぶ。契約 JSON の `reachable_from` が挙げる
   `run_trial preflight -> reject_started_trial` と `trial_lifecycle.started_once` /
   `trial_lifecycle.restart_forbidden` も同じ land に含める (invariant 表の
   declared-unimplemented 3 件を全部閉じるため)。
3. **M6 の consumer 検査 3 箇所**を、緩めずに反転側へ更新する。

**実装しない (scope 外)。**
- 契約 JSON `s8c_preregistration_evidence_contract.v1.json` の `machine_checkable` 反転
  (3 条件とも既に `true`。触らない)。
- 凍結 record (`condition-freeze.v1.g*.json`) の更新・再発行。
- **C11 の production 変更** — (M2) より既に成立。

## 不変条件 (規律 2 を緩める方向は不採用)

- crash を成功扱いにしない。indeterminate は成功でも失敗でもない第三の値として記録する。
- 世代上限の検査を 1 箇所に減らさない。3 境界の `_validate_generation_budget` call は現状維持。
- 新設 gate は恒真にしない。拒否が実際に発火する負の対照を、3 拒否理由
  (job 不一致 / boot 不一致 / 残時間不足) それぞれに付ける。
- 既存の受理挙動を黙って狭めない。予約束縛が要らない実行形 (`is_reservation_required`
  が False を返す isolation policy) を壊さないこと。ここは段 2 で現行の受理集合を先に書き出す。
- tripwire test を削除しない。反転させる。

## 成果物影響 (DW-G05)

- C12 未実装のままだと、8c 本走が予約の切れたノード・別 job・reboot 後のノードで起動でき、
  そこで採った測定値が certified 選択の材料に入る。実装後は launch 前に拒否されるので、
  台帳へ入る試行が「予約束縛と一致した割当上で走った」ものだけになる。
- C04 未実装のままだと、crash した実験が部分セルのまま台帳に残り、再起動で
  「2 回目の初回試行」が混入しうる。実装後は experiment 単位で indeterminate が記録され、
  再起動が registry 側で禁止される。
- M6 の 3 検査を直さないと受入全走が赤になり land できない (成果物ゼロ)。

## 判断が割れうる前提 (親の provisional 裁定。攻撃対象)

- **(P1)** C11 は no-op で正しい。「引数が C11 の実装を求めているのだから何か足すべき」
  ではなく、実測 (M2) が既に成立を示しているので production は触らない。
  ただし *runtime* の「適用された critic 射影が次世代で実際に消費される」ことを固定する
  test は存在するか未確認。**無ければ test だけ追加する**のは規律 3 に沿う純増であり採る。
  段 2 で既存被覆を性質で検索して純増検出力を出すこと。
- **(P2)** C12 の 3 拒否は `reservation.check_reservation` に既にある判定を p3 が消費する形で
  足りる。p3 側で判定ロジックを再実装しない (二重権威を作らない)。
- **(P3)** C04 の indeterminate 記録先は既存の experiment 単位の記録経路を使い、新しい
  台帳形式を作らない。段 2 で既存の記録先を file:line で特定すること。
- **(P4)** C12 の gate は `run_trial` の既存 preflight 群 (:3280 以降の引数検証帯) と
  同じ帯に置き、campaign launch を行う地点より前に支配的に置く。
- **(P5)** 予約束縛の消費は環境変数 (`reservation.read_binding(environ)`) 由来なので、
  既存テストの多くが環境変数を持たない。**既定を「予約不要なら読まない」にするか
  「常に読んで不在なら拒否」にするかで受理集合が変わる。** 現行の
  `is_reservation_required(isolation_policy)` の意味論を段 2 で確定し、
  既存の受理集合を壊さない側を選ぶ。

## 分割方針

編集面が 2 module + 3 test file に集中し、C04 と C12 は同じ `run_trial` 本体を触るため
**単一実装子**とする (所有が素集合にならない)。段 6 のレビューは 2 レンズ並列。

## 変更面アンカー表 (段 2 はここから file:line を確定する)

| path | anchor |
|---|---|
| orchestrator/campaign/p3_autonomous_workload_trial.py | `MAX_APPROVED_GENERATIONS` :126 / `_validate_generation_budget` :395 / `_run_workload` :2747 / `run_trial` :3244 / preflight 帯 :3280- / crash 捕捉 :3524 `except BaseException as exc` / `main` :3732 / 世代 gate :3772 |
| orchestrator/campaign/reservation.py | `ReservationBinding` :27 / `ReservationCheck` :59 / `read_binding` :159 / `check_reservation` :218 / `is_reservation_required` :273 |
| orchestrator/campaign/env_contract.py | `lookup` :820 |
| orchestrator/campaign/execution_guard.py | `attest_and_build_receipt` :576 |
| orchestrator/campaign/trial_registry.py | 3008 行。`forbid_trial_restart` / `reject_started_trial` は不在 |
| orchestrator/campaign/s8c_preregistration_evidence.py | `_evaluate_c04` :1601 / `_c12_allocation_binding_verdict` :1747 / `_evaluate_c12` :1766 / `_evaluate_c11` :1700 (**判定器は読むだけ。触らない**) |
| orchestrator/tests/test_s8c_preregistration_predicates.py | 実 repo snapshot :157,165 / C12 tripwire :2029 付近 |
| orchestrator/tests/test_s8c_preregistration_invariant.py | `MACHINE_CONTRACT_FUNCTION_CHECKS` :44- / `MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` :86- / `_assert_machine_contract_function_pins` :321 |
| orchestrator/tests/test_p3_autonomous_workload_trial.py | production 側の主 test file |

## 環境

受入・実測は本 worktree の親 (Pegasus login) で `python3 tools/run_tests.py` を相対・素の名前
ちょうどで走らせる。計測 (性能) は本 wave に無い。

## 並行 wave (段 4 と受入直前に再確認する)

- `worktree-dev-wave-t1333-t1310-workload-profile`: 同じ p3 file を +237 行編集。**未 land**
  (main に commit 無しを実測)。→ main の形の上に実装する。受入直前に main を再取り込み。
- `worktree-dev-wave-t1348-c09-c10-consumer` (C09/C10)、`worktree-dev-wave-t1353-c03-c08`
  (C03/C08): commit 0 件の起動直後。同じ判定器・同じ snapshot test を触る可能性が高い。
  先に land された側の形へ合わせる。
