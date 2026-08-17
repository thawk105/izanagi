# D498 実装プラン

結論は GO。親案 P1 は実時間依存を残すため、論理時計で preflight を固定する判別テストへ置き換える。P2 は help 文言だけの変更で正しい。

以下の行番号は編集前の現行行。

## 1. 編集の完全な閉包

| file:line | 編集内容 |
|---|---|
| `tools/codex_worker_launch.py:1793-1800` | `spawn_completed_ns` を診断条件の外で 1 回取得し、診断境界と evidence deadline の双方へ渡す。唯一の本体ロジック変更。 |
| `orchestrator/tests/test_codex_worker_launch.py:1542-1561,1629-1635` | `_base_command` に `evidence_grace: str = "1.0"` を追加し、固定文字列 `"1.0"` を `evidence_grace` に置換する。既存 caller は無変更。 |
| `orchestrator/tests/test_codex_worker_launch.py:4098-4166` 周辺 | `diagnostics=None` でも spawn 起点になる直接 `_attempt_loop` テストを追加する。 |
| `orchestrator/tests/test_codex_worker_launch.py:5926-5950` 周辺 | 旧起点を殺す sidecar ベースの判別テストを追加する。 |
| `tools/dev_wave_codex.py:94-105` | help に「子の起動完了時を起点とする猶予」と明記する。 |
| `orchestrator/tests/test_dev_wave_codex.py:579-602` | help block に新しい起点文言の assertion を追加する。 |

`rg -n "state\.started_ns" tools/codex_worker_launch.py` で得られる consumer は現在 2 箇所だけである。

- `tools/codex_worker_launch.py:1797-1800`: evidence deadline。ここだけ新しい `spawn_completed_ns` へ切り替える。
- `tools/codex_worker_launch.py:2003-2006`: attempt の `wall_clock_s`。変更しない。値は `:2018-2024` から `_seal_attempt` に渡り、`:1631-1638` で receipt attempt に出力される。

同じ初期サンプル `attempt_started_ns` の他の consumer も変更しない。

- `tools/codex_worker_launch.py:1698-1705`: `AttemptState.started_ns` への保存。
- `tools/codex_worker_launch.py:1706-1712,514-523`: 診断の `attempt_started_ns` と `attempt_state_created` 境界。
- `tools/codex_worker_launch.py:391-399`: signal の `attempt_elapsed_s_at`。
- `tools/codex_worker_launch.py:461-467`: sidecar の各 attempt elapsed。
- `tools/codex_worker_launch.py:3348-3354`: offline metering 再計算用の `AttemptState(started_ns=0)`。deadline を計算しないため無関係で、constructor も変えない。

したがって `AttemptState` や `AttemptDiagnosticsState` に field を追加せず、receipt、sidecar の schema と field 集合も変えない。

## 2. 時刻サンプルの単一性

現行:

```python
if attempt_diagnostics is not None:
    attempt_diagnostics.note_boundary(
        "spawn_completed", _monotonic_ns()
    )
evidence_deadline_ns = (
    state.started_ns
    + decimal_seconds_to_nanoseconds(args.evidence_grace_s)
)
```

変更後:

```python
spawn_completed_ns = _monotonic_ns()
if attempt_diagnostics is not None:
    attempt_diagnostics.note_boundary(
        "spawn_completed", spawn_completed_ns
    )
evidence_deadline_ns = (
    spawn_completed_ns
    + decimal_seconds_to_nanoseconds(args.evidence_grace_s)
)
```

サンプル位置は `Popen` と `read_pid_identity` が完了した後の既存 `spawn_completed` 境界、すなわち `tools/codex_worker_launch.py:1778-1795` の末尾に保つ。

これにより:

- `attempt_diagnostics is None` でも `spawn_completed_ns` は必ず定義される。
- 診断境界と deadline は同じ整数値を使う。
- `_monotonic_ns()` の呼び出し回数は、通常の診断あり経路では変更されない。
- attempt wall clock の起点は従来どおり `state.started_ns` である。

## 3. 判別テスト

### 推奨 fixture と値

新 node ID:

`orchestrator/tests/test_codex_worker_launch.py::test_evidence_grace_starts_at_spawn_completed`

使用条件:

- fixture mode: `no_rollout`
- `--evidence-grace-s`: `"0.05"`
- `--max-wall-clock-s`: `"3"`
- poll interval: `_base_command` の既存 `"0.01"`
- termination grace: `_base_command` の既存 `"0.05"`

`no_rollout` は `orchestrator/tests/test_codex_worker_launch.py:1403-1407` で thread は出すが rollout を作らず 30 秒待つため、deadline まで evidence 不足が安定して継続する。`no_thread` は TERM 無視の子孫も作る `:1381-1385` ため、今回不要な process-group 終了経路を混ぜる利点がない。

`_base_command` は次の形にする。

```python
def _base_command(
    ...,
    max_wall: str = "3",
    evidence_grace: str = "1.0",
    ...
):
    ...
    "--evidence-grace-s",
    evidence_grace,
```

### 実時間に依存しない preflight 差

親案の「実機 preflight が 0.05 秒以上」を前提にせず、既存の in-process 実行 seam を使う。

1. 実際の `_hook_checker.validate_installation` を呼ぶ wrapper を monkeypatch し、検査結果を改変せず、完了時に論理時計だけを 0.10 秒進める。
2. `_monotonic_ns` は spawn 境界まではその 0.10 秒を保持し、以後のサンプルごとに poll interval と同じ 0.01 秒進める。
3. `FAKE_MODE=no_rollout` で `LAUNCHER.main` を in-process 実行する。
4. sidecar を `_read_launcher_diagnostics` で読む。

検証値は次のとおり。

```python
grace = Decimal("0.05")
phases = diagnostics["attempts"][0]["phase_duration_s"]
preflight = Decimal(str(phases["attempt_preflight"]))
drain = Decimal(str(phases["supervision_drain"]))

assert preflight == Decimal("0.10")
assert preflight >= grace
assert drain == grace
```

正しい実装では spawn 後の 0.01、0.02、…、0.05 秒目の poll で発火する。旧実装では attempt 起点の deadline が spawn 時点ですでに満了しているため、最初の poll で発火し、`supervision_drain` は 0.01 秒となって最後の assertion が落ちる。

### sidecar field の実在根拠

推測 field は使わない。

- `tools/codex_worker_launch.py:418-429`: `attempt_preflight` と `supervision_drain` の境界対を定義。
- `tools/codex_worker_launch.py:468-474`: 各差分を `phase_duration` に計算。
- `tools/codex_worker_launch.py:475-489`: `as_document()` が `"phase_duration_s": phase_duration` を実際に出力。
- `tools/codex_worker_launch.py:2792-2797`: launcher sidecar の `attempts` に `item.as_document()` を格納。

### poll と termination grace

`tools/codex_worker_launch.py:1882-1892` では deadline を poll ごとに検査するため、実時間なら発火には最大で poll 1 周分程度の overshoot がある。したがって実時間の厳密な上限比較は置かない。推奨テストでは論理時計を 0.01 秒刻みにするため `drain == 0.05` を決定的に検査できる。

`supervision_drain_completed` は `tools/codex_worker_launch.py:1894-1897` で `_terminate` より前に、発火判定に使った同じ `now_ns` を記録する。従って `:1898-1903` の termination grace 0.05 秒は `supervision_drain` に混入しない。

親 P1 のままなら、正しい実装でも実機 preflight が 0.05 秒未満の環境で前提 assertion が偽の赤になる。推奨案では 0.10 秒を論理的に注入するため環境速度に依存しない。wrapper が実際に適用されなければ `attempt_preflight == 0.10` が明示的に落ち、黙って旧実装を通さない。

### 診断なし経路

追加 node ID:

`orchestrator/tests/test_codex_worker_launch.py::test_evidence_deadline_origin_is_diagnostics_independent`

`_diagnostic_attempt_loop_args` (`orchestrator/tests/test_codex_worker_launch.py:4080-4095`) と、既存 direct `_attempt_loop` の stub 群 (`:4098-4161`)を再利用する。`diagnostics=None`、grace 0.05 秒、preflight 0.10 秒、spawn 後 0.01 秒刻みの時計にし、process の `poll_count == 5` と `state.evidence_forced_stop` を確認する。

旧起点または診断なし時だけ `state.started_ns` へ fallback する変異は最初の poll、すなわち `poll_count == 1` で停止する。診断条件内でしか `spawn_completed_ns` を定義しない変異は未束縛エラーになる。

## 4. 既存テストへの影響

observable な待機時間が延びる既存 node は次の 4 本。assertion は origin や厳密な所要を固定していないため、期待値更新は不要で緑のままを期待する。

| node | 根拠 |
|---|---|
| `test_launcher_failure_diagnostic_reports_incomplete_evidence` | `orchestrator/tests/test_codex_worker_launch.py:2623-2635`。missing evidence の表示だけを検査。 |
| `test_evidence_forced_stop_propagates_unknown_residual_to_sidecar` | `:4169-4193`。強制停止、signal、residual の形だけを検査。 |
| `test_rollout_missing_after_grace_is_stopped_and_not_accepted` | `:5926-5950`。終端理由、evidence 状態、signal の有無を検査。 |
| `test_thread_missing_after_grace_kills_process_group` | `:5953-5984`。signal 種別と elapsed の非負性だけを検査。 |

変更経路を通るが挙動が変わらない回帰 anchor:

- `test_forced_stop_without_signal_is_not_launcher_initiated` (`:4098-4166`): 1 秒刻み時計では旧・新とも spawn 後最初の sample が新 deadline と等しく、同じ poll で停止する。
- `test_launcher_diagnostics_phase_durations_use_distinct_boundaries` (`:4196-4240`): `as_document` の field と境界対は不変。
- `test_launcher_diagnostics_production_phase_wiring_has_exact_durations` (`:4243-4307`): 既存の診断用 spawn sample を再利用するので期待値更新不要。別 sample を追加する誤実装なら `supervision_drain` が 2 から 3 へずれて落ちる。
- `test_positive_p3_exact_limit_natural_exit_is_accepted` (`:3732-3769`): evidence が deadline 前に完成するため不変。
- unsafe grace の parser test (`:3070-3098`) は spawn 前拒否なので不変。

`_base_command` の新 kwarg は既定 `"1.0"` のため、既存 caller と `:2593-2594` の診断文字列に更新は不要。

## 5. `tools/dev_wave_codex.py` の要否

P2 は正しい。

変更するのは `tools/dev_wave_codex.py:98-104` の help だけで、例えば「子の起動完了時を起点とする evidence 待機猶予」とする。

変更しない箇所:

- `tools/dev_wave_codex.py:150-157`: `min(90, max_wall_clock_s)` と `grace <= max_wall` の検証。起点と独立した値域規則であり、D498 は値を変更していない。
- `tools/dev_wave_codex.py:237-240`: launcher への argv 転送。値はそのまま渡せばよい。
- `orchestrator/tests/test_dev_wave_codex.py:208-235`: 既定値、小数 override、低い wall 上限への切り下げは不変。
- `:238-330`: unsafe 値と上限検証は不変。
- `:579-602`: 既存 help assertion は維持し、「子の起動完了時を起点」の assertion だけ追加する。

grace と max wall が等しい場合、launcher start 起点の max wall が evidence deadline より先に発火し得るが、これは `tools/codex_worker_launch.py:1765-1772,1819-1881` の既存かつ意図された全体上限である。

## 6. 変異事前登録

| 対 | (a) 変異内容 | (b) 殺す node ID | (c) 根拠 |
|---|---|---|---|
| M1 | 正: `spawn_completed_ns + grace`。変異: `state.started_ns + grace`。 | `test_evidence_grace_starts_at_spawn_completed` | preflight 0.10、grace 0.05。正は drain 0.05、旧起点は最初の poll の 0.01。 |
| M2 | 正: spawn sample を診断条件外で取得。変異: 診断あり時だけ取得し、なし時は未束縛または旧起点へ fallback。 | `test_evidence_deadline_origin_is_diagnostics_independent` | `diagnostics=None` で正は 5 poll、fallback は 1 poll、未束縛は例外。 |
| M3 | 正: 診断境界と deadline に同じ sample。変異: deadline 用に `_monotonic_ns()` をもう一度呼ぶ。 | `test_launcher_diagnostics_production_phase_wiring_has_exact_durations` | `:4260-4265` の時計は呼び出しごとに 1 秒進み、余分な sample で `:4298-4307` の exact duration がずれる。 |
| M4 | 正: `_base_command(..., evidence_grace="0.05")` を argv へ転送。変異: `"1.0"` を固定したまま。 | `test_evidence_grace_starts_at_spawn_completed` | command option と sidecar の drain 0.05 を検査するため、固定 1.0 は通らない。 |

## 7. やらないこと

起点据え置きと事前検査所要の控除、現状維持、ならびに `max_wall_clock_s` の判定式、起点、既定値、検証、テスト期待値への変更はすべて scope 外とする。

DW-S02 / DW-O05 に従う静的プランであり、read-only sandbox では pytest を実走していない。上記を緑とは報告しない。

## 総括

- 本体変更は `codex_worker_launch.py:1793-1800` の 1 ブロックだけで、attempt wall clock は維持する。
- 旧起点は論理時計付き `no_rollout` sidecar テストで決定的に殺す。
- 診断なし経路と単一サンプル性も別 node と既存 exact-duration node で固定する。
- 最大の不確実性は、親の実走時に既存 3 秒 fixture が極端な負荷で max wall を先に踏む可能性である。