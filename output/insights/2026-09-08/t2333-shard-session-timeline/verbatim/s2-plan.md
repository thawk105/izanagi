## 総括

実装方針は、`report.json` の top-level に必須 key `session_timeline` を 1 個だけ追加し、その配下へ 3 種の観測をまとめる形とする。

変更箇所は次の 3 file に限定する。

- [tools/acceptance_shards.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:61): schema、採取状態、xdist 運搬、report 組立、形の検査。
- [orchestrator/tests/conftest.py:2080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:2080): real-repo lock の取得後と解放後を観測。
- [orchestrator/tests/test_run_tests_shards.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/test_run_tests_shards.py:79): report fixture 更新と回帰テスト追加。

`merge_reports` の 6 gate、pytest rc の合成、scheduler 判定、receipt、canonical wall の測定面は変更しない。[verbatim-rulings.md:3-6](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/verbatim-rulings.md:3) の「観測 field」と、[verbatim-rulings.md:23-26](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/verbatim-rulings.md:23) の canonical wall を維持する。

`SCHEMA = "izanagi-acceptance-shard-report/v1"` は変更しない。producer と consumer を同じ変更で同期させ、性能判定 protocol や receipt schema は増やさないためである。

実装、file 編集、commit、pytest 実測は行っていない。

## 足す field の形

正確な JSON 形は次とする。数値例は説明用である。

```json
{
  "session_timeline": {
    "collection_finished_epoch_s": 1788800000.125,
    "workers": {
      "gw0": {
        "first_test_started_epoch_s": 1788800000.250,
        "last_test_finished_epoch_s": 1788800123.750,
        "real_repo_lock_intervals": [
          {
            "acquired_epoch_s": 1788800010.500,
            "released_epoch_s": 1788800021.875
          }
        ]
      },
      "gw1": {
        "first_test_started_epoch_s": 1788800000.375,
        "last_test_finished_epoch_s": 1788800117.250,
        "real_repo_lock_intervals": []
      }
    }
  }
}
```

serial 実行時は worker key を既存の worker 表現と揃えて `"serial"` とする。

```json
{
  "session_timeline": {
    "collection_finished_epoch_s": 1788800000.125,
    "workers": {
      "serial": {
        "first_test_started_epoch_s": 1788800000.250,
        "last_test_finished_epoch_s": 1788800123.750,
        "real_repo_lock_intervals": []
      }
    }
  }
}
```

型と意味は次のとおり。

- `session_timeline`: JSON object。
- `collection_finished_epoch_s`: JSON number。producer では `time.time()` 由来の Python `float`。xdist では全 worker の collection 記録値の最大値。
- `workers`: test report を 1 件以上出した worker ID を key とする非空 JSON object。idle worker は最初と最後の test が存在しないため含めない。
- `first_test_started_epoch_s`: その worker の全 `TestReport.start` の最小値。
- `last_test_finished_epoch_s`: その worker の全 `TestReport.stop` の最大値。
- `real_repo_lock_intervals`: その worker で real-repo lock を実際に取得した protocol ごとの JSON array。対象 test が無ければ空 array。
- `acquired_epoch_s`: `_real_repo_locks(access)` が必要な P/S lock をすべて取得した直後の `time.time()`。
- `released_epoch_s`: 同 context が必要な lock をすべて解放した直後の `time.time()`。
- 全 `*_epoch_s` の単位は Unix epoch からの秒。時刻帯に依存しない。
- 数値は丸めず、採れた `float` を既存の canonical JSON writer へ渡す。
- interval は worker 内で取得時刻順に並べ、worker object は既存の `sort_keys=True` により canonical 化する。

top-level は 3 key に分けず `session_timeline` 1 keyだけを足す。同じ clock domain の観測を一つの subtree に閉じられ、[tools/acceptance_shards.py:61-66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:61) の閉じた top-level schema の変更を最小化できるためである。将来、観測値を増やす場合も top-level gate を追加変更せずに済む。

## 採取と運搬の設計

| 観測 | 採取 hook | serial | xdist |
|---|---|---|---|
| collection 終了 | acceptance plugin の `pytest_collection_modifyitems` 末尾 | config-local state を直接読む | 各 worker の custom workeroutput へ載せ、controller で最大値を取る |
| worker 最初・最後の test | acceptance plugin の controller-side `pytest_runtest_logreport` | `"serial"` の min `start` / max `stop` | 標準 xdist `TestReport` が運ぶ `start` / `stop` と `worker_id` を使う |
| real-repo lock interval | `conftest.py` の `pytest_runtest_protocol` wrapper | config-local state へ直接追記 | worker-local stateへ追記し、custom workeroutput で controller へ運ぶ |

具体的な変更は次のとおり。

1. [tools/acceptance_shards.py:798-803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:798) に `_WORKER_TEST_BOUNDS` のような process-local dict を追加する。値は worker ごとの first/last の 2 float とする。

2. [tools/acceptance_shards.py:806-822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:806) の acceptance plugin 有効時初期化で、この dict を空に戻す。既存 global と同様、逐次 session の値を持ち越さない。

3. [tools/acceptance_shards.py:826-852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:826) では、既存の item 分類や deselect 部分を書き換えない。現在の `setattr(config, "_izanagi_acceptance_shard_state", ...)` が完了した直後に、その state dict へ次を追加する。

   - `real_repo_lock_intervals = []`
   - 最後の処理として `collection_finished_epoch_s = time.time()`

   これにより、並行 wave が触る [brief.md:61-65](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:61) の既存 837-850 行を書き換えず、末尾だけを伸ばせる。

4. [tools/acceptance_shards.py:862-874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:862) の controller-side `pytest_runtest_logreport` で、既存の worker 決定後に `report.start` と `report.stop` を読む。

   - worker 初回なら両値で entry を作る。
   - 以後は `first = min(first, float(report.start))`、`last = max(last, float(report.stop))`。
   - setup、call、teardown の全 report を対象にするため、setup 開始から teardown 終了までを worker 全体で囲める。
   - worker process 側は現在の早期 return を維持する。

5. xdist の test 時刻は新しい custom payload へ載せない。pytest 9.1.1 の `TestReport.start` / `stop` が既存の report 経路で worker から controller へ届き、現在も同 hook が `report.worker_id` を利用しているためである。[tools/acceptance_shards.py:862-872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:862)

6. [tools/acceptance_shards.py:913-925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:913) の `_worker_payload` には全 worker について次の 2 要素を追加する。

   - `collection_finished_epoch_s`
   - `real_repo_lock_intervals`

   `records` と `selected` は現状どおり `gw0` だけに載せる。timeline 2 要素は worker ごとに異なるため全 worker が載せる。

7. [tools/acceptance_shards.py:877-885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:877) の既存 `pytest_testnodedown` と `_WORKER_PAYLOADS` をそのまま運搬路として使う。新規 IPC、file、manifest は作らない。

8. [tools/acceptance_shards.py:928-952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:928) の `_controller_state` の返値へ collection 終了時刻と worker 別 lock interval map を加える。

   - serial branch は config-local state の時刻と interval を返す。
   - xdist branch は全 `_WORKER_PAYLOADS` から collection 時刻を集めて `max` を取り、lock interval は `_WORKER_PAYLOADS` の worker ID ごとの map にする。
   - 既存 digest 一致、authority worker 数、records、selected の検査は変更しない。

9. [tools/acceptance_shards.py:955-1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:955) の controller report 組立で、`_WORKER_TEST_BOUNDS` と `_controller_state` が返した lock map を worker ID で結合し、上記の `session_timeline` を生成する。

10. `merge_reports` の出力である `MergeResult` へ timeline は加えない。[tools/acceptance_shards.py:603-701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:603) の 6 gate、rc、scheduler、failure、terminal count の処理は不変とする。

## conftest 側の設計

[orchestrator/tests/conftest.py:2080-2097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:2080) の wrapper を、概念上次の形にする。

```python
with _acceptance_timed_real_repo_locks(item.config, access):
    with patchharness._pytest_node_context(node_id, access):
        return (yield)
```

`_acceptance_timed_real_repo_locks` は同 wrapper の直前へ追加し、次を保証する。

- `access is None`、または `config` に `_izanagi_acceptance_shard_spec` が無い場合は、現在の `_real_repo_locks(access)` をそのまま通す。clock read、acceptance module import、state 更新を一切しない。
- acceptance shard かつ `access is not None` の場合だけ計測する。
- underlying `_real_repo_locks(access).__enter__()` が正常終了した直後に `acquired_epoch_s = time.time()` を取る。
- underlying `__exit__()` が正常終了し、全 lock が解放された直後に `released_epoch_s = time.time()` を取る。
- protocol 内側の例外情報は underlying `__exit__` へそのまま渡し、lock 解放後に同じ例外を再送出する。
- lock 取得自体が失敗した場合は acquire/release の組を記録しない。
- lock 解放が失敗した場合も、成功した release として記録しない。
- 正常な acquire/release の組が完成した時だけ、`tools.acceptance_shards.record_real_repo_lock_interval(config, ...)` を呼ぶ。

実際の flock 取得は [orchestrator/tests/conftest.py:1251-1260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:1251)、最終 unlock と fd close は [orchestrator/tests/conftest.py:1283-1290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:1283) にある。wrapper の時刻は、[orchestrator/tests/conftest.py:1347-1360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:1347) が取得する全対象 lock を囲む区間とする。個々の legacy/common lock や P/S resource ごとの時刻は追加しない。

`record_real_repo_lock_interval` は [tools/acceptance_shards.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:798) 付近へ追加し、次の順で動く。

```python
if getattr(config, "_izanagi_acceptance_shard_spec", None) is None:
    return
state = getattr(config, "_izanagi_acceptance_shard_state", None)
if type(state) is not dict:
    return
intervals = state.get("real_repo_lock_intervals")
if type(intervals) is not list:
    return
intervals.append({
    "acquired_epoch_s": acquired_epoch_s,
    "released_epoch_s": released_epoch_s,
})
```

通常の `run_tests` に対する no-op は二重に保証する。

- conftest helper が `_izanagi_acceptance_shard_spec` 不在なら既存 lock context へ直行する。
- recorder 自身も同 attr 不在なら state を参照せず return する。

この attr は acceptance plugin の `pytest_configure` だけが設定している。[tools/acceptance_shards.py:813-822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:813) 通常実行では `_PLUGIN_CONFIG` の process-global 値に依存せず、現在の `config` が持つ明示的な shard spec を authority とする。

## `_REPORT_FIELDS` と検査の扱い

[tools/acceptance_shards.py:61-66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:61) の `_REPORT_FIELDS` へ `"session_timeline"` を必須 key として 1 件追加する。

`set(report) != _REPORT_FIELDS` は維持する。[tools/acceptance_shards.py:618-620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:618) を部分集合判定へ緩めると、未知 top-level field を持つ report まで受理し、[brief.md:17-21](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:17) の既存 gate を緩めないという不変条件に反する。したがって (P1-a) を支持し、厳密一致 gate の緩和案は採らない。「緩和しても規律 2 に反しない」という例外説明は不要である。

`validate_report_evidence` には新 field の構造検査を足す。[tools/acceptance_shards.py:512-518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:512) の直前または直後に専用 helper を置き、[tools/acceptance_shards.py:518-600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:518) から呼ぶ。

検査内容は以下だけに限定する。

- `session_timeline` の key 集合が `{"collection_finished_epoch_s", "workers"}` と一致する。
- `collection_finished_epoch_s` が bool でない有限 JSON number。
- `workers` が非空 dict。
- worker ID が非空 str。
- worker entry の key 集合が `{"first_test_started_epoch_s", "last_test_finished_epoch_s", "real_repo_lock_intervals"}` と一致する。
- first/last が bool でない有限 JSON number。
- `real_repo_lock_intervals` が list。
- 各 interval の key 集合が `{"acquired_epoch_s", "released_epoch_s"}` と一致する。
- acquired/released が bool でない有限 JSON number。

一方、次は意図的に検査しない。

- collection と first test の前後関係。
- first と last の前後関係。
- acquired と released の前後関係。
- interval の重複、長さ、合計時間。
- worker 数と worker occupancy の一致。
- wall、閾値、scheduler、pytest rc との比較。

したがって、これは timeline の値を用いた性能判定や第 7 gate ではない。現在も `validate_report_evidence` は「診断 payload」の shape を 6 gate より前に検査している。[tools/acceptance_shards.py:518-524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:518) [tools/acceptance_shards.py:608-633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:608) 新 helper はその既存 schema-integrity 層へ observation envelope の形だけを追加する。

[verbatim-rulings.md:16-18](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/verbatim-rulings.md:16) が却下したのは「timeline に基づく判定や gate」である。有限な数値なら時系列が逆転していても merge verdict を変えないテストを置き、観測値から判定していないことを固定する。

## テスト計画

[orchestrator/tests/test_run_tests_shards.py:79-111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/test_run_tests_shards.py:79) の `_reports()` が各 report に正規の `session_timeline` を含むよう更新する。既存 merge/gate テストはそれ以外を変えずに通す。

追加する node ID と検査内容は以下とする。

- `orchestrator/tests/test_run_tests_shards.py::test_session_timeline_is_one_required_top_level_report_field` — `_REPORT_FIELDS` に `session_timeline` だけが追加され、削除 report と未知 top-level key 付き report が `report-invalid` になること。
- `orchestrator/tests/test_run_tests_shards.py::test_session_timeline_shape_validation_rejects_malformed_observation` — root、worker entry、interval entry、時刻型、NaN、infinity の各 malformed shape を parametrize し、全て `report-invalid` になること。
- `orchestrator/tests/test_run_tests_shards.py::test_session_timeline_numeric_order_never_changes_merge_verdict` — collection、first/last、acquired/released を意図的に逆順の有限値にしても、既存の 6 gate が `ok` のままであること。
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_logreport_tracks_first_start_and_last_stop_per_worker` — synthetic `gw0`、`gw1` report を到着順と時刻順をずらして渡し、worker ごとの min `start` と max `stop` が得られること。
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_logreport_uses_serial_worker_name_without_xdist` — `worker_id` 不在時に既存規約どおり `"serial"` へ記録されること。
- `orchestrator/tests/test_run_tests_shards.py::test_worker_payload_carries_collection_and_lock_observations_but_not_test_bounds` — custom workeroutput に collection と lock は入るが、test bounds は重複して入らないこと。
- `orchestrator/tests/test_run_tests_shards.py::test_controller_timeline_state_uses_serial_local_state` — serial branch が `_WORKER_PAYLOADS` を要求せず、config-local collection と lock interval を返すこと。
- `orchestrator/tests/test_run_tests_shards.py::test_controller_timeline_state_uses_latest_xdist_collection_and_all_worker_locks` — xdist branch が全 worker の collection 値の最大値を選び、lock interval を worker ID ごとに保つこと。
- `orchestrator/tests/test_run_tests_shards.py::test_lock_interval_recorder_is_noop_without_acceptance_shard_state` — spec 不在と state 不在の通常実行相当で例外も mutation も起きないこと。
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_records_after_lock_acquire_and_release` — synthetic lock context と clock を使い、acquired が enter 後、released が exit 後に記録されること。
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_preserves_inner_exception_while_recording_release` — inner protocol の例外を置換せず、lock 解放成功時には complete interval を 1 件だけ残すこと。
- `orchestrator/tests/test_run_tests_shards.py::test_sessionfinish_writes_exact_session_timeline_for_serial_and_xdist` — report writer を捕捉し、serial と xdist の両方で最終 JSON subtree が上記の正確な key/type 構造になること。

新テストは既存の evidence/schema テストが並ぶ [orchestrator/tests/test_run_tests_shards.py:892-938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/test_run_tests_shards.py:892) 周辺へ置く。既存様式どおり synthetic mapping、`monkeypatch`、`pytest.mark.parametrize`、最終 `_merge()` verdict を使い、実 host や wall time に依存させない。

## コスト見積り

- collection: collection owner process ごとに `time.time()` 1 回、dict 代入 2 回。per-item 処理は増えない。追加 I/O、file、explicit syscall は無い。
- worker test bounds: `TestReport` 1 件につき属性参照 2 回、有限値確認、dict の min/max 更新。通常は setup/call/teardown の最大 3 report 程度なので O(report 数)。新しい clock read、I/O、custom xdist message は無い。
- real-repo lock: lock 対象 item だけ `time.time()` 2 回と list append 1 回。既存 flock/open/close の回数は増えない。追加 file I/O、fsync、lock syscall は無い。
- `time.time()` は target Linux では通常 vDSO clock read であり、明示的な kernel syscall を追加しない。ただし Python/platform の fallback までは schema 契約に含めない。
- worker-controller 間: collection と lock interval は既存の workeroutput message に同居するため、message 数は増えず payload bytes だけが増える。test bounds は既存 `TestReport` の属性を読むだけで追加 payload を作らない。
- report 永続化: [tools/acceptance_shards.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:1023) の既存 create-only write 1 回だけ。write、flush、fsync、directory fsync の回数は変わらず、書込 byte 数だけが O(worker 数 + real-repo item 数) 増える。
- 目安として worker entry は 1 worker あたり約 150 byte、lock interval は 1 件あたり約 80 byteであり、48 worker と 100 interval でも増分は十数 KiB 程度である。
- acceptance wall への見込みは sub-second 級だが、最終判断は親が行う canonical 全走実測に委ねる。D1620 の receipt wall 自体は変更しない。

## (P1) の評価

- **(P1-a) 支持。** `"session_timeline"` を `_REPORT_FIELDS` の必須要素に足し、[tools/acceptance_shards.py:619-620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:619) の厳密一致を維持する。部分集合判定は未知 field を受理する緩和であり、[brief.md:17-21](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:17) の不変条件に反する。

- **(P1-b) 支持。ただし「運搬不要」は「新しい custom 運搬が不要」の意味に限定する。** worker test の `start` / `stop` は標準 xdist `TestReport` が既に controller へ運ぶため、[tools/acceptance_shards.py:862-874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:862) で集計できる。collection timestamp と conftest lock interval は worker-local に発生し、標準 report に無いため、[tools/acceptance_shards.py:913-925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:913) の custom worker payload を拡張する。

- **(P1-c) 支持。** 全値を Unix epoch 秒の float とする。shard が別 host になり得るという [brief.md:39](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:39) の前提では、process-local `time.monotonic()` を report 間で比較できない。monotonic clock は既存 deadline 処理のまま残し、timeline には使わない。

- **(P1-d) 支持。** lock の真の境界を知るのは [orchestrator/tests/conftest.py:2081-2097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:2081) なので、そこから `tools.acceptance_shards` の記録関数を呼ぶ。逆方向にすると acceptance plugin が test-suite 固有 lock 実装へ依存する。通常 run の no-op は config-local shard spec の二重 guard で保証し、process-global `_PLUGIN_CONFIG` の残留には依存しない。

## 残る不確実性

- brief が指定する `pytest_collection_modifyitems` 末尾は、acceptance plugin の selection/deselection 完了時点である。一方、conftest の wrapper は inner hook 後に suffix strip と duration reorder を行う。[orchestrator/tests/conftest.py:2065-2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:2065) したがって、この計画の `collection_finished_epoch_s` は厳密には「acceptance shard の collection 選別完了」であり、全 wrapper unwind 完了よりわずかに早い。brief の「同関数末尾」指定を優先するが、完全な hook-chain 終了を意味させるなら `pytest_collection_finish` へ移す裁定が必要になる。

- epoch 秒は別 host の値を同じ座標へ置けるが、host 間 clock skew を補正しない。timeline は観測専用であり、そのためにも前後関係や所要時間を gate に使わない。

- pytest 9.1.1 の `TestReport.start` / `stop` が xdist controller まで保持されることは親の起動時調査に基づく。[brief.md:29-31](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:29) synthetic 単体テストに加え、親の実測で xdist report の実値を確認する必要がある。

- `SCHEMA` の v1 維持は observation-only 変更を最小化する選択である。repository の別規律が「必須 field 追加は必ず schema major 更新」と定めている場合は v2 化が必要だが、射影資料にはその要件は無い。