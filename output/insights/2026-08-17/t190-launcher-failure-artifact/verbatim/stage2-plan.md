# 実装プラン v1

行番号は現行 worktree、編集前の行番号である。指定 4 資料はすべて読了した。対象 2 file の全文読みは行っていない。

## P1〜P3 の裁定

| 前提 | 結論 | 理由 |
|---|---|---|
| P1 計装先 | **独立 sidecar を採用。ただし attempt ごとの複数 file ではなく、1 launcher run につき 1 file** | receipt の closed schema、受理述語、checker を一切変更しない。最終 receipt の SHA-256 と attempt index を sidecar に束縛し、食い違いを検出可能にする。 |
| P2 退避の opt-in | **環境変数 opt-in は不採用。未処理の `LauncherReturncodeMismatch` なら常時退避** | 設定漏れがまさに恒真化になる。期待済みの `pytest.raises` は call failure ではないため退避されず、緑走のディスク増分はゼロ。環境変数は有効化条件ではなく、退避 root の上書きだけに使う。 |
| P3 全成立集合 | **親 provisional を採用** | `limit_trigger` の値と優先順位は現状維持し、sidecar にだけ「その判定点で成立していた全条件」を出す。`control_limit_trigger` と `conditions_met` を別名にして意味を混ぜない。 |

P2 への反対案は不変条件 1〜5に触れない。production の値・判定、受理述語、fixture 予算、既存期待値は変更せず、test call がすでに失敗した後の read-only copy だけを追加する。

## 単位 A: launcher 計装

対象: [`tools/codex_worker_launch.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:77)

### A1. 診断状態と sidecar 契約

| 行 | 現状の前後 | 変更後の形 |
|---|---|---|
| `:77-86` | `_LIMIT_REASONS`、`_STOP_REASONS` | 既存 tuple は変更せず、診断 schema literal と residual reason code を直後に追加する。 |
| `:93-179` | `_ATTEMPT_FIELDS`、`_RECEIPT_FIELDS_V1/V2/V3` | **変更しない。** 診断 field を receipt に混ぜない。 |
| `:318-355` | `RolloutState`、`AttemptState` | `AttemptState` に receipt 非公開の in-memory 診断状態を追加し、run 全体用 `LauncherDiagnosticsState` を隣接定義する。 |
| `:604-646` | atomic JSON helper の直後、`_load_json` の前 | sidecar document 生成、receipt hash 束縛、atomic publish helper を追加する。 |

内部状態は次を持つ。

- attempt ごとの phase boundary の monotonic ns
- `evidence_forced_stop`
- residual unknown source の全観測集合と最終 source
- 判定点ごとの `conditions_met`
- 最終 receipt に残った `control_limit_trigger`
- job clock 起点と attempt clock 起点

出力先は次とする。

```text
<artifact_dir>/launcher-diagnostics.<launcher-pid>.<uuid4hex>.json
```

固定名を上書きせず、run ごとに一意にする。document は概ね次の閉じた形にする。

```json
{
  "schema": "codex-worker-launch-diagnostics/v1",
  "job_id": "job-a",
  "receipt_binding": {
    "path": "/abs/receipt.json",
    "sha256": "...",
    "bytes": 1234,
    "status": "sealed"
  },
  "job_elapsed_s_at": {
    "run_preflight_completed": 0.2,
    "receipt_published": 3.1
  },
  "attempts": [
    {
      "attempt_index": 1,
      "evidence_forced_stop": true,
      "control_limit_trigger": null,
      "residual_observation": {
        "final_count": null,
        "final_unknown_source": "pid_identity_unavailable",
        "unknown_sources_seen": ["pid_identity_unavailable"]
      },
      "job_elapsed_s_at": {},
      "attempt_elapsed_s_at": {},
      "phase_duration_s": {},
      "limit_condition_snapshots": [
        {
          "site": "running_poll",
          "comparison": ">=",
          "conditions_met": [
            "max_wall_clock_s",
            "max_model_calls",
            "max_cli_reported_tokens"
          ]
        }
      ]
    }
  ]
}
```

receipt 公開後に exact bytes の SHA-256 を取って束縛する。これにより sidecar と receipt の組み違いは検出できる。sidecar は checker authority にはしない。

### A2. `residual=None` の 4 経路

編集位置は `tools/codex_worker_launch.py:1141-1216`。

`_group_member_count` の数値戻り値 `int | None` は維持する。代わりに optional keyword callback を追加する。

```python
def _group_member_count(
    identity: PidIdentity | None,
    *,
    on_unknown: Callable[[str], None] | None = None,
) -> int | None:
```

各現行 `return None` の直前で以下を通知する。

| 現行行 | 経路 | reason code |
|---|---|---|
| `:1142-1143` | `identity is None` | `pid_identity_unavailable` |
| `:1145-1148` | `/proc` の `scandir` が `OSError` | `proc_scandir_oserror` |
| `:1154-1167` | 個別 `stat` の読取失敗。`FileNotFoundError` 後も path が存在する場合を含む | `proc_stat_read_error` |
| `:1156-1167` | `int(fields[2])` の `ValueError` | `proc_stat_parse_error` |

`end <= 0` や短い fields を現在は単に無視しているため、そこを新たに `None` にしてはならない。既存の residual 判定を変えるからである。

伝播は次の caller 全てに optional callback を通す。

- `_group_member_count` の直接 caller: `_wait_for_group_exit` `:1171-1179`
- `_wait_for_group_exit` の caller: `_terminate` `:1182-1208`、`_normal_reap` `:1211-1216`
- `_terminate` の caller: `_attempt_loop` `:1511-1515`、例外 cleanup `:1523-1527`
- `_normal_reap` の caller: `_attempt_loop` `:1517`

戻り値の型はどの層でも変えない。`AttemptState` の callback が reason を集合へ追加し、最後に `residual is None` なら最後の reason を `final_unknown_source` にする。`:1528-1529` の cleanup 自体が例外になった経路は、4 経路と混同せず `termination_observer_error` とする。

### A3. phase 境界と 2 時計

編集位置は `tools/codex_worker_launch.py:1312-1569`。

既存時計との関係は次のとおり。

- job clock 起点: module import 時の `_LAUNCHER_PROCESS_STARTED_NS` `:35`。`main` が `args.launcher_started_ns` へ束縛する `:3153-3204`
- attempt clock 起点: `AttemptState.started_ns` `:1352-1358`
- receipt の attempt `wall_clock_s`: `:1548-1550`
- receipt の job `actuals.wall_clock_s`: `_receipt` `:1711-1713`

sidecar では `wall_clock_s` という名前を新設しない。F285 M1 の二義性を増やさないため、必ず次の名前を使う。

- `job_elapsed_s_at.<boundary>`
- `attempt_elapsed_s_at.<boundary>`
- `phase_duration_s.<phase>`

phase 境界は次に置く。

| 境界 | 現行アンカー | 意味 |
|---|---|---|
| `attempt_state_created` | `:1352-1358` | attempt clock 起点。job 起点との差が launcher/job preflight 所要になる |
| `attempt_preflight_completed` | hook 検証と wall 判定後、`Popen` 直前 `:1408-1419` | attempt hook preflight の終端 |
| `spawn_completed` | `Popen` と PID identity 読取後 `:1419-1434` | spawn phase 終端 |
| `supervision_drain_completed` | while を抜けた直後 `:1439-1509` | poll、stdout/rollout drain、manifest 観測を含む supervision phase 終端 |
| `process_reap_completed` | `_terminate` / `_normal_reap` 後 `:1510-1517` | terminate または normal reap の終端 |
| `final_drain_completed` | 最終 `observe` 後 `:1518` | 停止後の最終 evidence drain 終端 |
| `artifact_handles_closed` | fsync/close 後 `:1534-1540` | attempt stream の耐久化完了 |
| `attempt_wall_clock_sampled` | 既存 attempt sample `:1548-1550` | 既存 receipt 値との exact 対応点 |
| `attempt_sealed` | `_seal_attempt` 後 `:1554-1564` | attempt record 構築完了 |
| `receipt_published` | `_run_supervised` が戻った直後、`:2239-2245` の外側 | receipt 公開後。sidecar write より前 |

監視中にファイル I/Oを追加しない。既存 `now_ns` は再利用し、新規処理は in-memory timestamp と集合更新だけにする。sidecar の JSON write/fsync は receipt と全 late gate が確定した後に行う。

### A4. latch の全成立集合

次の既存 `if/elif` はそのまま残す。

- process exit 観測 `:1458-1466`
- live `pending_limit` `:1470-1482`
- `_seal_attempt` の late check `:1250-1262`
- retry admission `:2063-2076`
- `_latch_final_job_limit` `:1962-1985`

その直前または直後で、同じ既存 local 値から独立した診断集合を作る。

- live poll は現行どおり `>=`
- natural exit、seal、final job latch は現行どおり `>`
- tuple の順序は `_LIMIT_REASONS` の wall → model → token

`_latch_final_job_limit` には診断用 `site` を追加し、現行 3 caller を区別する。

- `:2077`: `post_attempt`
- `:2093`: `post_first_receipt_audit`
- `:2132`: `post_receipt_staging`

sidecar の `conditions_met` が複数でも、receipt の `limit_trigger` は既存優先順位で選ばれた単一値のままにする。`accepted` 計算 `:1263-1272`、`_LIMIT_REASONS` `:77-81`、truth table は変更しない。

### A5. sidecar の公開点

編集位置は `_run` `:2234-2262`。

`_preflight_run(args)` は現在どおり既存 try の外に残す。artifact dir の安全性が未確定な preflight failure で新規書込を始めないためである。

その後を次の形にする。

```python
diagnostics = LauncherDiagnosticsState(...)
try:
    try:
        rc = _run_supervised(..., diagnostics=diagnostics)
        diagnostics.note_receipt_published(...)
        return rc
    except BaseException as exc:
        # 現行の launcher-error receipt 公開と再 raise をそのまま維持
        ...
finally:
    _publish_launcher_diagnostics_without_changing_result(...)
```

公開 helper の例外は元の rc・例外を上書きしない。書込失敗時は bounded な一行を stderr に出す。物理 I/O failure や launcher 自身の SIGKILL まで sidecar 存在を保証するために rc を変える案は、不変条件 5 と衝突するので採らない。

## 単位 B: pytest 退避 harness

対象: [`orchestrator/tests/test_codex_worker_launch.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:42)

### B1. 発火点

| 行 | 現状の前後 | 変更後の形 |
|---|---|---|
| `:5-18` | import 群 | `shutil`、`tempfile`、安全な path metadata 用 import を追加 |
| `:42-61` | 診断予算、`LauncherReturncodeMismatch` | 例外 class 自体は変更せず、退避 root 定数を追加 |
| `:62` 直後 | `_short_repr` の前 | snapshot helper、局所 pytest plugin、autouse fixture を追加 |
| `:495-530` | `_assert_launcher_returncode` | **変更しない。** 16 KiB message を構築して同じ例外を投げ続ける |
| `:583-637` | unordered 系の直接 raise | **変更しない。** 同じ exception class なので plugin が一括検出する |

module-level の pytest hook は test module から自動登録される保証がないため使わない。代わりに autouse fixture が、当該 test の call phase 中だけ plugin object を登録する。

```python
@pytest.fixture(autouse=True)
def _launcher_failure_artifact_reporter(request, tmp_path):
    plugin = _LauncherFailureArtifactPlugin(request.node.nodeid, tmp_path, ...)
    request.config.pluginmanager.register(plugin, unique_name)
    try:
        yield
    finally:
        request.config.pluginmanager.unregister(plugin)
```

plugin の `pytest_runtest_makereport` は `tryfirst=True` とし、次を満たすときだけ同期退避する。

- `call.when == "call"`
- `call.excinfo is not None`
- `call.excinfo.errisinstance(LauncherReturncodeMismatch)`

`pytest.raises(LauncherReturncodeMismatch)` で処理済みなら test call は正常終了するため発火しない。したがって既存の診断テスト群は保存を量産しない。

コピーは call report の作成中に完了する。pytest の順序は setup → call → call report → teardown であり、さらにこの autouse fixture は `tmp_path` に依存する。従って copy は fixture finalizer、特に `tmp_path` teardown より確実に前である。

保存先は `item.add_report_section` に出す。既存 exception message と `_bounded_failure_message` `:479-492` は変更しないので 16 KiB 契約を保つ。

### B2. 退避先と衝突回避

既定 root は gitignored の次とする。

```text
<repo>/output/runs/pytest-launcher-failures
```

環境変数 `IZANAGI_LAUNCHER_FAILURE_ARTIFACT_ROOT` があれば root だけを上書きする。未設定でも退避は有効である。

```text
<root>/
  <sanitized-PBS_JOBID-or-local>--<hostname>/
    <PYTEST_XDIST_WORKER-or-main>/
      <nodeid-sha256-prefix>--pid<PID>--<time_ns>--<mkdtemp-random>/
        metadata.json
        snapshot-manifest.json
        tmp_path/
          ...
```

- leaf は `tempfile.mkdtemp(dir=worker_dir, prefix=...)` で原子的に作る
- full nodeid は path に入れず `metadata.json` に保存する
- worker、PID、時刻、nodeid digest、mkdtemp suffix を併用する
- `exist_ok=True` で既存 leaf を再利用しない
- 48 xdist worker、同一走 21 failure、同一 nodeid の別走でも上書きしない

`tmp_path` 全体を再帰保存するため、receipt、manifest、attempt stdout/stderr/output、rollout、PID 情報、launcher diagnostics sidecar が一式残る。

FIFO、socket、device を open すると hook 自体が停止しうるため、walk は symlink を追わない。regular file と directory はコピーし、symlink は link 自体を保存する。特殊 file は種類と相対 path を `snapshot-manifest.json` に記録して読み飛ばす。

## テスト計画

### 新設 nodeid

- `orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_records_evidence_stop_and_phase_clock_scopes`
  - `evidence_forced_stop=true`
  - phase の単調順序
  - `job_elapsed_s_at` と `attempt_elapsed_s_at` が別 origin
  - generic な新規 `wall_clock_s` field が無いこと

- `...::test_launcher_diagnostics_records_all_simultaneous_limit_conditions_without_changing_limit_trigger`
  - wall/model/token を同じ poll で全て成立させる
  - sidecar は 3 件全てを記録
  - receipt の `limit_trigger` は従来どおり `max_wall_clock_s`
  - `accepted=False` のまま

- `...::test_launcher_diagnostics_write_failure_does_not_change_control_result`
  - sidecar writer を `OSError` にする
  - normal run の rc、receipt outcome、accepted が変更されないこと

- `...::test_launcher_diagnostics_sidecar_is_outside_receipt_schema`
  - sidecar が存在する状態で `check-receipt` が従来の rc
  -同じ field を receipt 内へ注入すると closed-schema 拒否されること

- `...::test_group_member_count_reports_identity_missing_source`
- `...::test_group_member_count_reports_scandir_failure_source`
- `...::test_group_member_count_reports_stat_read_failure_source`
- `...::test_group_member_count_reports_stat_parse_failure_source`
  - 4 reason code を個別に固定し、どれも数値戻り値は従来どおり `None`

- `...::test_unknown_residual_source_propagates_without_verifying_normal_reap`
  - `_group_member_count` → wait → normal reap まで reason が届く
  - `residual is None`、`verified is False` は維持

- `...::test_launcher_failure_artifact_reporter_is_registered_during_test_call`
  - autouse fixture が実際に plugin manager へ登録済みであること

- `...::test_launcher_failure_artifact_reporter_archives_unhandled_mismatch`
  - synthetic な未処理 mismatch を plugin の hook entry へ渡す
  - root が事前には存在しない状態から bundle が 1 件作られること
  - receipt、nested file、launcher sidecar の exact bytes を確認

- `...::test_launcher_failure_artifact_reporter_does_not_archive_handled_mismatch`
  - call `excinfo=None` の正常 report では bundle が作られないこと

- `...::test_launcher_failure_artifact_paths_are_collision_free`
  -同じ nodeid、worker、root で 2 回発火させる
  -異なる 2 leaf が残り、1 件目の sentinel が上書きされないこと

- `...::test_launcher_failure_artifact_snapshot_does_not_follow_special_files`
  - FIFO を含む source を退避しても block せず、manifest に `special-file` と残ること

### 改名する nodeid

- `test_proc_scan_and_missing_identity_are_unknown`
  - 上記 identity / scandir の 2 nodeへ分割
- `test_individual_proc_read_failure_is_unknown`
  - `test_group_member_count_reports_stat_read_failure_source`
- `test_unknown_residual_never_verifies_normal_reap`
  - `test_unknown_residual_source_propagates_without_verifying_normal_reap`

期待値は維持し、reason の検出力だけを追加する。

### 既存 nodeid への純増 assert

- `test_seal_failure_still_writes_launcher_error_receipt` `:2835`
  - post-spawn exception でも sidecar がある
- `test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output` `:2877`
- `test_receipt_audit_wall_overrun_flips_to_not_accepted` `:2916`
  - late final latch の site が sidecar に残る
- `test_rollout_missing_after_grace_is_stopped_and_not_accepted` `:4102`
- `test_thread_missing_after_grace_kills_process_group` `:4124`
  - `evidence_forced_stop` と terminate phase を検査
- `test_launcher_failure_diagnostic_is_bounded_and_repeats_summary_at_end` `:1639`
  -現行 16 KiB assert はそのまま残す

「保存されたことだけを見る」恒真化を避けるため、positive harness test は archive helper の戻り値を信じない。退避 root を空から始め、hook entry を通した後に実ファイルを glob し、sentinel bytes を直接読む。保存呼出しを削除すれば bundle 数 assert で赤になる。

## consumer 波及

exact launcher receipt signature を検索した結果、active Python/JSON file は次の 4 fileだけだった。

- `tools/codex_worker_launch.py`
- `orchestrator/tests/test_codex_worker_launch.py`
- `tools/dev_wave_codex.py`
- `orchestrator/tests/test_dev_wave_codex.py`

影響は次のとおり。

| consumer | 行 | 影響 |
|---|---|---|
| `_validate_attempt` | launcher `:2265-2382` | `_ATTEMPT_FIELDS` 不変なので変更なし |
| `_validate_receipt` | launcher `:2384-2678` | receipt field 集合・truth table 不変なので変更なし |
| `_audit_receipt_value` | launcher `:2833-3034` | receipt が参照する fileだけを検査し、artifact dir の余分な sidecar は列挙拒否しない |
| `_check_receipt_paths` / CLI | launcher `:3037-3069`, `:3152-3194` | sidecar を読まない。rc と report 不変 |
| `tools/dev_wave_codex.py` | `:200-253` | artifact dir と `receipt.json` pathを組み立てるだけ。sidecar は同 dir に自然に残り、argv 変更なし |
| `orchestrator/tests/test_dev_wave_codex.py` | `:118-133`, `:361-385` | argv と fake launcher の path 契約だけ。receipt schema を検証していない |
| `test_check_receipt_*` 系 | test `:3347`, `:3361`, `:3464`, `:3506`, `:3549`, `:3572`, `:3602`, `:3624`, `:3812`, `:4196`, `:4224`, `:4243` | 既存期待値は変更しない。sidecar 非干渉の新規 nodeだけ追加 |

`tools/dev_waves/receipt.py:97-164` は supervisor receipt の別 schema であり、本 launcher receipt ではない。`tools/dev_wave_wait.py:2720-2765` の “check receipt” も acceptance red-check receipt で別物である。どちらも変更しない。

## 不変条件の照合

1. parser の production 値 `:3098-3124` は変更しない。
2. `_LIMIT_REASONS`、`accepted` `:1263-1272`、truth table は変更しない。
3. `_base_command` の wall=`3` `test:964`、evidence=`1.0` `:1041-1042`、termination=`0.05` `:1043-1044`、poll=`0.01` `:1045-1046` は変更しない。
4. 既存 assert の反転・緩和・skip・削除はしない。分割・改名した residual test も従来の `None` / `False` を維持する。
5. loop の break、terminate/normal reap の選択順、receipt 公開順を変えない。監視中は in-memory 観測だけ、sidecar I/O は最終 receipt 公開後に限定する。

## 恒真化リスクと潰し方

- **fixture を宣言したが plugin が call phase に登録されていない**
  - 登録状態を test 本体から plugin manager 経由で検査する nodeを置く。

- **archive test 自身が destination を作り、copy が no-op でも緑**
  - root 不在から開始し、hook 後の leaf 数と sentinel exact bytes を確認する。

- **全条件集合と言いつつ `limit_trigger` 1 件をコピーしているだけ**
  - wall/model/token 3 条件同時成立を作り、sidecar 3 件と receipt 1 件を同時に assert する。

- **reason code は `_group_member_count` で出るが caller 側で捨てられる**
  - 4 source の単体 test に加え、normal reap と launcher sidecar までの伝播 test を置く。

- **phase field を全て終了時に一括記入して順序だけ成立**
  - preflight delay、evidence stop、terminate を通る既存 seamで、隣接 phase duration の正値と時計 origin 差を検査する。

- **衝突回避を謳うが固定 leaf を再利用**
  - 同一 metadata で連続 2 回発火し、2 directory と1件目の非上書きを確認する。

- **診断 write failure が accepted run を launcher error に変える**
  - writer を強制失敗させても rc=0、accepted、receipt hash が不変な test を置く。

pytest、build、実走は行っていない。今回確認したのは指定資料、対象アンカー、caller、consumer の静的検査のみである。

## 総括

receipt schema と制御フローを凍結したまま、launcher は receipt hash 付き独立 sidecarへ①〜④を記録し、pytest は未処理の rc 不一致だけを call report 時点で常時退避する。これにより設定漏れ、clock 名の二義化、複数 latch の縮約、`residual=None` の原因消失、xdist 上書きをそれぞれ検出可能にする。