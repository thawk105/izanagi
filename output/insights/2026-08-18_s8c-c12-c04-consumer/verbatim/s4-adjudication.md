# 段 4 裁定 + プラン v2 + 変異事前登録

親裁定。段 3 レンズ A (7 件) / レンズ B (8 件) を real/refuted、採用/不採用、scope 内/外で裁く。

裁定 inbox 再走査 (19:30 JST): `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` の最新
`2026-08-18-rulings-full8-19rulings.md` に「UNSATISFIED 5 件の consumer を実装する」が
**裁定不要・実装のみ**として置かれている。本 wave はその C04 / C12 分に一致する。
同文書冒頭のユーザー指示「研究を速く進める。無駄なことをしない。」を scope 判断の重みとする。

## 裁定表

| # | 判定 | 採否 | scope | 理由 |
|---|---|---|---|---|
| A-1 | **real** | 不採用 | **外** | `p3_s4_loop_trigger_gating` の CLI / `loop.run_campaign` 直呼びは 8c launcher ではなく s4 探索層の入口である。C12 の `consumer_requirement` は path=p3、entrypoints=main/run_trial と明示。全 launch へ gate を広げるのは別 module への新設 gate であり、本 wave の変更面外。**裁定パッケージへ返す。** |
| A-2 | **real** | 採用 | 内 | `reject_started_trial` を定義するだけにしない。`run_trial` preflight から実際に呼ぶ。 |
| A-3 | **real** | 採用 | 内 | forbid と terminal 記録を failure-atomic にする。片方の失敗で他方を落とさない。 |
| A-4 | **real** | 部分採用 | 内 (限定) | `mark_experiment_indeterminate` は `experiment_status` と `remaining_cells` を引数に取り、既存 lifecycle row の**既存 field** へ載る形でだけ記録する。**新 JSON key を作らない** (B-7 と整合)。載せられる既存 field が無ければ helper 引数として保持し、その事実を記録に書く。 |
| A-5 | **real** | 不採用 | **外** | `_finish_trial` の `Exception -> partial` は着地済みの設計 (cell 単位の部分失敗を正当に扱う) で、専用テストが複数 pin している。これを反転させると report の受理集合が広範に変わる。本 wave の依頼は consumer 配線であって crash 方針の再設計ではない。**裁定パッケージへ返す** (reason code 名 `crash-policy-cell-partial` が指す意味的な穴が残ることを記録に明記する)。 |
| A-6 | **real** | 部分採用 | 内 (限定) | 予約検査は preflight 帯の**最後**、lifecycle start の直前に置く (preflight→launch の時間差を最小化)。campaign launch ごとの再検査は不採用・**裁定パッケージへ返す**。 |
| A-7 | **real** | 不採用 | **外** | 予約事実を report / lifecycle へ永続束縛するのは新しい証拠面の新設。**裁定パッケージへ返す。** |
| B-1 | **real** | 採用 | 内 | 反転面は 5 つ目 (`test_s8c_preregistration_predicates.py:607-650` の overlay) がある。反転する (削除しない)。 |
| B-2 | **real** | 採用 (前半のみ) | 内 / 外 | production から呼ぶ (A-2 と同じ、採用)。**判定器 `s8c_preregistration_evidence.py` への reachability target 追加は不採用・裁定パッケージへ返す** — 自分が実装するものを判定する門を同じ wave で書き換えない。 |
| B-3 | **real** | 採用 (回避の形で) | 内 | sealed admission への refactor を**やめる**。`_finish_trial` / `_run_workload` の signature を変えず、`:986,:1081,:2804,:2811` の既存 site/env 解決を一切触らない。これで B-3 と B-8 の risk が消える。 |
| B-4 | **real** | 採用 | 内 | single-process contract で `run_trial` を通る既存テストを**全件**列挙し、共有の valid reservation fixture を足す。1 件で足りると仮定しない。 |
| B-5 | **real** | 採用 | 内 | 3 拒否テストは「provider / campaign が起動していない」ことを必ず assert する。late-call 変異が殺せる形にする。 |
| B-6 | **real** | 不採用 | **外** | 上位 PBS dispatch 経路は未実装。A-1 と同じ裁定パッケージへ束ねる。 |
| B-7 | **real** | 採用 | 内 (運用) | 受入直前に main を再取り込みし、status dict と `MACHINE_CONTRACT_FUNCTION_*` は**現行 contract から再導出**する。行番号で合流しない。 |
| B-8 | nit | 不採用 | — | B-3 の裁定で signature を変えないため前提が消える。 |

**refuted は 0 件。** 全所見が real である (A-5 / A-1 / A-6 / A-7 / B-6 は real だが scope 外)。

## プラン v2 (段 5 実装子への確定指示)

### V2-1 `orchestrator/campaign/trial_registry.py`

- 既存 lifecycle capability state に `started_once` / `restart_forbidden` を持たせる。
  **`output/s8c-trial-registry/lifecycle.jsonl` の JSON key 集合を変えない。**
- `reject_started_trial(...)`: 既存 start row があれば `TrialRegistryError`。row を書かない。
  既存 `_locked_lifecycle_update` / `_load_lifecycle_rows` を再利用する。
- `forbid_trial_restart(token)`: capability state の `restart_forbidden` を立てる。
  永続的な拒否の実体は既存 start row + `terminal_status="indeterminate"` row である。
  **この 2 つを実際に読んで拒否する consumer が誰かを実装報告に file:line で書く**
  (読み手が居なければ恒真な保証である。A-4/B-2 の指摘)。

### V2-2 `orchestrator/campaign/p3_autonomous_workload_trial.py` — C12 gate

- `run_trial` の preflight 帯の**最後**、`run_root.mkdir` と `record_trial_start_once` の直前に
  予約 gate を置く。
- gate は `_admit_env_contract(site)` で得た contract の isolation policy を
  `reservation.is_reservation_required` に掛け、**True のときだけ**
  `reservation.read_binding(os.environ)` → `reservation.check_reservation(binding,
  required_s=max_wall_s, safety_margin_s=0, environ=os.environ)` を呼ぶ。
- 判定 (job 不一致 / boot 不一致 / 残時間不足) を p3 側で再実装しない。`ReservationError` を
  そのまま、または最小の文脈付きで送出する。
- **`ReservationError` が `run_trial` の `except BaseException` (:3524, :3630) に捕まって
  indeterminate 化されない位置**に置くこと (レンズ A の実測どおり outer `try` :3444 より前)。
  この順序をテストで固定する。
- **site 解決の回数と順序を変えない。** 既存の `trigger._current_site()` 呼び出しは
  preflight 帯では `_assert_build_site_opted_in` の中の 1 回 (`:1997`、`do_build` が真のときだけ)
  である。`test_p3_autonomous_workload_trial.py:1799-1830` が
  `iter((OTHER, PEGASUS_COMPUTE))` で呼び出し列を pin している。
  **実装前にこの pin を読み、呼び出し列を変えない形を選べ。** 許される形は
  (i) preflight で一度解決した site を build opt-in と予約 gate で共有する、
  (ii) 内部 helper の signature を変えて解決済み site を渡す、のいずれか。
  **どちらも既存の着地済みテストを反転させずには実現できないと判明したら、実装せず停止して
  親へ報告せよ** (勝手にテスト側を書き換えない)。

### V2-3 同 file — C04 crash helper

- `mark_experiment_indeterminate(token, *, cause, experiment_status, remaining_cells, ...)` を
  追加し、`run_trial:3524-3535` と `:3630-3641` の `_record_indeterminate_terminal` 直呼びを
  置換する。
- **failure-atomic**: `forbid_trial_restart` と terminal 記録を独立に試行し、両方の失敗を
  集約したうえで**元の例外を再送出**する。どちらか一方の失敗で他方を落とさない。
- `_finish_trial` の `Exception -> partial` は**変更しない** (A-5 裁定)。
- `reject_started_trial` を `run_trial` preflight (lifecycle start より前) から呼ぶ。

### V2-4 検査の反転 (5 面。緩めず反転させる。削除しない)

1. `test_s8c_preregistration_predicates.py:151,157,165` — C04/C12 を
   `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` へ。
2. 同 `:169,176-177` — C12 tripwire を配線済み側へ反転。
3. 同 `:196,217-220` — `_c12_allocation_binding_verdict(...) is None` へ反転。
4. 同 `:607,623-650` — overlay を「現行 HEAD の reachable call 集合に `read_binding` と
   `check_reservation` が実在する」正例へ反転。synthetic absence test は維持。
5. `test_s8c_preregistration_invariant.py:43-96` — C04 の 3 tuple を EXCLUSIONS から CHECKS へ。
   **exact 集合は現行 contract から再導出**して差分を確認する (行番号で合わせない)。

### V2-5 fixture

single-process (`is_reservation_required` が True) の contract で `run_trial` を通る既存テストを
**全件**洗い出し、共有の valid reservation fixture (`IZANAGI_RESERVATION_*` 8 key +
`PBS_JOBID` + boot + deadline の整合) を足す。Linux / OTHER は予約不要のまま。

## 変異事前登録 (DW-M01。実装前に登録)

各変異は「無効化すると赤くなる理由が一つに絞れる」ことを実装後に確認する。前後に同じ入力を
拒否する層があれば登録から外し実効 gate へ再照準する。

| ID | 変異 | 期待 kill (受理集合 or fail-closed 挙動の変化) |
|---|---|---|
| M1 | 予約 gate の `check_reservation` 呼び出しを削除 | job/boot/deadline の 3 拒否テストが全て通ってしまう → 赤 |
| M2 | 予約要否判定を常に False (常に読まない) にする | Pegasus 経路の 3 拒否テストが赤 |
| M3 | 予約要否判定を常に True (常に読む) にする | **正例**: Linux/OTHER の既存完走テストが `ReservationError` で赤 (過剰拒否の検出) |
| M4 | 予約 gate を campaign launch より後ろへ移す | B-5 の「provider/campaign 未起動」assertion が赤 |
| M5 | `mark_experiment_indeterminate` から `forbid_trial_restart` 呼び出しを削除 | 再起動拒否テストが赤 |
| M6 | 同 helper から terminal 記録呼び出しを削除 | indeterminate row テストが赤 |
| M7 | `reject_started_trial` を no-op (raise しない) にする | preflight 重複起動拒否テストが赤 |
| M8 | 同 helper で元例外を再送出せず正常 return する | crash 伝播テストが赤 (crash を成功扱いにする方向の変異) |
| M9 | forbid を先に投げる (失敗注入) | failure-atomic テストが赤 (terminal 記録が落ちる) |
| M10 | `required_s` を 0 に落とす | 残時間不足テストが赤 |
| M11 | job 照合だけを見て boot 照合を捨てる (p3 側で再実装した場合のみ) | boot 不一致テストが赤。**p3 側に判定を書かない裁定なので、この変異が置けない = 正しい実装** |

M11 は「置けなければ設計が正しい」型の登録である。M3 は受理集合を縮小する wave の
過剰拒否検出 (正例) として必須。

## 成果物影響 (DW-G05)

- C12 未実装: 予約の切れたノード・別 job・reboot 後のノードで 8c 本走が起動でき、その測定値が
  台帳と certified 選択の材料に入る。実装後は launch 前に拒否される。
- C04 未実装: crash した実験が部分セルのまま残り、再起動で「2 回目の初回試行」が混入しうる。
- V2-4 の 5 面を直さない: 受入全走が赤で land できず、成果物ゼロ。

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **A-1 / B-6 — 予約 gate の支配性が 8c launcher に限られる。** `p3_s4_loop_trigger_gating`
   の CLI と将来の PBS dispatch は `run_trial` を経ずに `loop.run_campaign` へ到達できる。
   択: (a) 共通 launch 点へ admission を強制する、(b) 直接 driver を正式に禁止して経路テストを
   置く、(c) 保証範囲を「8c CLI / `run_trial` public boundary のみ」と明記する。
2. **A-5 — `Exception -> partial` が C04 の意味的要求を骨抜きにしている。** reason code
   `crash-policy-cell-partial` が指す穴はここである。着地済みの設計テストを反転させる変更に
   なるため、ユーザー裁定に返す。
3. **A-6 — campaign launch 直前の予約再検査。** preflight 一回では preflight→launch の
   時間差ぶん deadline 余裕が目減りする。`reservation.py:74-117` に再検査 API が既にある。
4. **A-7 — 予約事実の永続束縛。** どの予約の上で走ったかを report / lifecycle から
   再検証できない。
5. **B-2 後半 — 判定器に `reject_started_trial` の reachability を追加するか。**
   契約は 3 consumer を要求するが判定器は 2 つしか見ない。門の強化であり、自分の実装を
   判定する門を同じ wave で書き換えないという理由で見送った。
