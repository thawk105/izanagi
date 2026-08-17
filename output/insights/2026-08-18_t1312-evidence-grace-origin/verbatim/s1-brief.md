# 段 1 brief — [T-1312] D498: `--evidence-grace-s` の deadline 起点を子の起動完了時へ移す

## scope

`--evidence-grace-s` が定める evidence deadline の起点を、attempt 記録の作成時
(`AttemptState.started_ns`) から**子の起動完了時** (`spawn_completed` 境界) へ移す。
編集面は `tools/codex_worker_launch.py`、`tools/dev_wave_codex.py`、
`orchestrator/tests/test_codex_worker_launch.py`、`orchestrator/tests/test_dev_wave_codex.py`。

## 確定済みユーザー裁定 (D498、覆さない)

- 起点は子の起動完了時へ移す。
- 総所要の有界化は `max_wall_clock_s` が引き続き担う。**触らない。**
- 受理集合が形式的に広がるのは、関門が宣言していた集合への是正として受諾済み。
  **それ以上広げない。**
- 却下済み: 起点据え置き + 起動側の事前検査所要の控除。現状維持。

## 不変条件

1. `max_wall_clock_s` の判定式・起点・発火箇所を一切変えない
   (`codex_worker_launch.py:1767` の preflight 検査、:1819/:1841 の elapsed、
   `_record_limit_conditions` の `limits`)。
2. `AttemptState.started_ns` は attempt wall clock (:2004
   `wall_clock_s = attempt_wall_now_ns - state.started_ns`) の起点として不変。
   evidence deadline だけを切り離す。
3. `attempt_diagnostics is None` でも新起点は成立しなければならない。現行 :1795 の
   `spawn_completed` 記録は `attempt_diagnostics is not None` の中にあり、
   時刻取得が診断の有無に依存してはならない。
4. 診断が記録する `spawn_completed` 境界と、関門が使う起点は**同一の 1 サンプル**とする
   (2 度 `_monotonic_ns()` を呼んで別値にしない)。
5. receipt / sidecar の schema version と field 集合を増やさない (T-1083 の封印は見送り済み)。
6. `--evidence-grace-s <= --max-wall-clock-s` の既存検証 (`dev_wave_codex.py:154`) を緩めない。
7. `docs/dev-wave/**` は予算満杯。そこへ書く必要が出たら `DW-S08` に従い止めて裁定へ返す。

## 成果物影響 (DW-G05)

実装しない場合: launcher の evidence 関門は「公称猶予 − preflight 所要」で発火し続ける。
F57 の実測 (2026-08-17、受入全走 request 914871) では attempt 2 の preflight が 1.04〜1.11 秒に
膨らみ、fixture の猶予 1.0 秒を食い切って `evidence_forced_stop=true` が立ち、
`limit_trigger` が立たないまま `_writer_truth` が `max_attempts` へ落ちた。
結果として**受入全走の台帳へ非帰属の赤が 3 件混入し、緑 1 回 = land 1 回分の窓を消費する**。
実装すれば、この赤の機序 (F57 の確定した機序) が消える。

## 成果物の形

- `codex_worker_launch.py` の deadline 計算 1 箇所の起点差し替え + 時刻サンプルの
  診断非依存化。
- 「起点が旧位置のまま」を殺す判別テスト (下記 P1)。
- 既存 evidence 系テストの緑維持。
- 変異 matrix で旧起点の変異体が殺されることの実測。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 判別テストの設計。** 猶予を preflight より小さく取る
  (例 `--evidence-grace-s 0.05`) と、旧起点では spawn 完了時点で deadline が既に満了しており
  最初の poll で即殺されるのに対し、新起点では spawn 後ちょうど猶予だけ生存する。
  sidecar の `phase_duration` から
  (a) 前提として `attempt_preflight >= 猶予` を assert し、
  (b) `supervision_drain >= 猶予` を assert する。
  (a) を assert することで、preflight が想定より速い環境では黙って通らず声を上げる。
  `_base_command` に `evidence_grace` kwarg を足す (現行は `1.0` 固定、
  `test_codex_worker_launch.py:1629`)。
  *攻撃してほしい点:* 時間比較テストの脆さ、poll interval 0.01 秒との干渉、
  `no_rollout` fixture 以外に適した mode があるか、(a) が偽の赤を生む確率。
- **(P2) `dev_wave_codex.py` の編集は help 文言のみ**と見る。argv 生成・既定値
  `min(90, max_wall_clock_s)`・上限検証は起点移動の影響を受けない。
  *攻撃してほしい点:* 既定値 90 秒の妥当性が起点移動で変わるか (D498 は値に触れていない)。
- **(P3) 凍結露出なし**と判定した。`FROZEN_MANIFEST` (`test_frozen_artifacts.py:41`) の
  entry はすべて `output/` 配下で、launcher 系の pin は無い。よって `DW-O08`/`DW-O09`/`DW-O10`
  は不発火。
  *攻撃してほしい点:* path を key にしない pin (role 名 key、generator source hash) の見落とし。

## 実アンカー表

| path:line | 内容 |
|---|---|
| `tools/codex_worker_launch.py:1698` | `attempt_started_ns = _monotonic_ns()` (現行起点の源) |
| `tools/codex_worker_launch.py:1701-1708` | `AttemptState(started_ns=...)` と `new_attempt` |
| `tools/codex_worker_launch.py:1762-1777` | preflight (`_require_attempt_hook_installation`)、`max_wall_clock_s` 検査、`attempt_preflight_completed` |
| `tools/codex_worker_launch.py:1778-1796` | `Popen`、`read_pid_identity`、`spawn_completed` 記録 |
| `tools/codex_worker_launch.py:1797-1799` | `evidence_deadline_ns = state.started_ns + grace` (**変更対象**) |
| `tools/codex_worker_launch.py:1882-1890` | 関門の発火 (`evidence_forced_stop`) |
| `tools/codex_worker_launch.py:2004` | attempt wall clock (`state.started_ns` の別用途、不変) |
| `tools/codex_worker_launch.py:343,365,505-522` | `AttemptState.started_ns`、`job_started_ns`/`attempt_started_ns`、`new_attempt` |
| `tools/codex_worker_launch.py:406-470` | 境界順序・phase 対・elapsed 算出 |
| `tools/codex_worker_launch.py:3753-3757` | `--evidence-grace-s` の argparse (既定 5) |
| `tools/dev_wave_codex.py:94-105` | `--evidence-grace-s` の help |
| `tools/dev_wave_codex.py:150-157` | 既定値導出と上限検証 |
| `tools/dev_wave_codex.py:239-240` | argv への転送 |
| `orchestrator/tests/test_codex_worker_launch.py:1560-1648` | `_base_command` (猶予 `1.0` 固定) |
| `orchestrator/tests/test_codex_worker_launch.py:1650-1690` | `_run_case`、`_read_launcher_diagnostics` |
| `orchestrator/tests/test_codex_worker_launch.py:3082-3090` | 不正猶予値の起動前拒否 |
| `orchestrator/tests/test_codex_worker_launch.py:5926-5975` | `no_rollout` / `no_thread` の evidence 強制停止 |
| `orchestrator/tests/test_dev_wave_codex.py:208-330` | 既定値・小数・上限検証 |
| `orchestrator/tests/test_dev_wave_codex.py:588-600` | help block |

## 並列分割方針

段 2 plan 1 本 → 段 3 敵対 2 本 (sol/luna) → 段 5 実装 1 本 (編集面が
launcher 1 file に集中し所有を割れない) → 段 6 敵対レビュー 2 本 + fix。

## 環境

受入・実測はこの worktree
(`/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin`) で親が行う。
