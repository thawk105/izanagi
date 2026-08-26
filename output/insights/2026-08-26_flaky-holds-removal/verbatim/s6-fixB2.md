## 総括

- 2 本の thread test に、偽 clock の利用を直接観測する control を追加した。
- wall-clock 上界は追加せず、既存 watchdog も変更していない。
- `sleep=` と `clock=` の削除をそれぞれ決定的に検出できる。
- 既存の性質 assertion は削除、緩和、並べ替えをしていない。
- commit、add はしていない。
- 対象 nodeid は実行基盤の preflight failure により未実走。

## 足した control の設計 (なぜ実時間を測らないか)

`_Clock` を包む `_RecordingClock` を追加し、thread ごとに次を記録する。

- 注入 sleeper の呼出し列 `sleep_calls`
- 偽 clock の仮想時刻 `now`
- 注入 clock の読出し回数 `read_calls`

下限は実所要ではなく構成値から算出する。

- latch test: `poll_interval_s * initial_qstat_failures`
- pending-hold test: 各 scheduler について `poll_interval_s * states.index("DONE")`

後者は既定状態 `QUE`, `RUN`, `DONE` のため、`DONE` 前の poll 遷移数から導かれる。負荷や実時間は観測していない。

## 2 変異それぞれが赤になることの追跡

1. `sleep=clock.sleep` を削除する

   production の実 sleeper が使われ、既知の実 sleep は 30 秒 watchdog 内で終了するため、thread 生存確認は通る。その直後の `assert clock.sleep_calls` が空列に対して赤になる。後続の `results`、qsub 回数、hold、latch assertion は先に発火せず、mask しない。

2. `clock=clock` を削除する

   記録 sleeper は呼ばれるため `sleep_calls` と仮想時刻下限は通るが、production から記録 clock は読まれない。`assert clock.read_calls > 0` が赤になる。これも既存の性質 assertion より前に発火する。

したがって、今回は両方の変異を検出できる。

## 新設・変更した nodeid

新設 nodeid はない。変更した nodeid は次の 2 件。

- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_control_lock_serializes_latch_check_through_immediate_visibility`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_control_lock_allows_peer_after_pending_hold_is_durably_released`

## 変更した file と行

[test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_pegasus_dispatch_compute.py:53)

- 53–71 行: `_RecordingClock`
- 5417–5459 行: latch test の thread 別記録と control
- 5484–5545 行: pending-hold test の thread 別記録と control

ソース編集はこの 1 ファイルだけ。

## 実走したか (nodeid と範囲、または「実装済み・未実走」)

**実装済み・未実走。**

上記 2 nodeid を `python3 tools/run_tests.py` で指定したが、pytest 起動前の Pegasus `qstat -Q` preflight が rc=1、runner が rc=16 で終了した。したがって緑は主張しない。

静的検査は実施済み。

- Python AST parse: 成功
- `git diff --check -- orchestrator/tests/test_pegasus_dispatch_compute.py`: 成功

## 所有外への波及可能性

- caller: production の `DC.dispatch` は未変更。変更は対象 2 callsite の注入値だけ。
- 共有 fixture: `conftest.py` と fixture は未変更。
- consumer test: `_RecordingClock` は module 内の上記 2 nodeidだけが参照する。他の `_Clock` 利用 test には波及しない。
- production、tools、docs、他の test file に静的な変更波及はない。

## 未完・未確認

- 対象 2 nodeid の実走と acceptance 範囲は未確認。
- 2 変異は指示どおり静的追跡のみで、変異実走はしていない。
- 失敗した test wrapper が `output/pegasus-dispatch/` 配下に dispatch failure receipt を生成した。編集禁止範囲のため削除していない。