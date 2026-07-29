第2修正を指定範囲内で実装しました。production・docs・output・git index・commitには触れていません。

### 変更

変更ファイルは [test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:90) のみです。

- [pure parser](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:1552)
  - exact 4 keys、型、PASS/SKIP/FAIL、exit対応を検証
  - duplicate key、extra/missing key、wrong type、noncanonical fields、exit mismatchを拒否
  - SKIP reasonを単一の非空 `exception_args` に束縛
  - 親は検証済み `_ServeChildResult` だけを使用
- [parametrized control](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:1636)
  - canonical PASS/SKIP/FAIL
  - KeyboardInterrupt/SystemExit payload保持
  - malformed、duplicate key、exit mismatch等を直接検査
- [SignalRelay束縛](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:1243)
  - child-local factoryで実生成instanceをproxyへ登録
  - reader intと実 `fileno()` を比較
  - `daemon_mod.SignalRelay` と `daemon_mod.select` を同じfinallyで復元
- [timeout cleanup](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:1750)
  - `start_new_session=True` のharness groupへ `killpg`
  - TERM → bounded wait → KILL → bounded reap
  - `ProcessLookupError` とexit raceを許容
  - nested session全体の回収は主張しない

差分stat：

- HEAD→working tree: `1 file changed, 677 insertions(+), 26 deletions(-)`
- 再review時の `+411/-26` からは `+266/-0`
- index側は開始時と同じ `+291/-24` のまま
- status: `MM orchestrator/tests/test_dev_waves_integration.py`

### テスト

指定focused一括実行は rc=0：

- pure parser/control: `14 passed`
- isolation contract: `3 passed`
- long-path node: `1 skipped`
- 合計: `17 passed, 1 skipped`

SKIP理由は `sandbox does not permit AF_UNIX bind through /proc/self/fd` です。greenには数えていません。

追加検査：

- `check_codex_agents.py`: rc=0
- `check_docs.py`: rc=0
- `git diff HEAD --check`: rc=0

### 残るNOT_RUN

- capability gate以降のreal socket roundtrip、実relay reader、serve lifecycle
- timeout時のTERM/KILL強制発火control
- M1〜M6 mutation
- M7: `NOT_RUN(design-invalid)` のまま。telemetryは追加していません
- nested sessionを跨ぐ一般process-tree containment

### manager再review観点

- SKIP reasonを `exception_args` 単一要素へ束縛するschemaが裁定意図と一致するか
- parentが未検証dictを参照せず、KeyboardInterrupt/SystemExitもstructured FAILとして扱うこと
- actual `SignalRelay.fileno()` 比較が `lease._fd` 等へのmutationを確実に赤くすること
- restore ownershipがchild-local module binding内に閉じていること
- `killpg(process.pid, …)` の保証範囲をharness group限定として記録していること
- capability環境でreal long-path nodeを再走するまで、relay/roundtripを実証済みにしないこと

## 総括

第2修正の実装とcapability非依存検査は完了です。blockerは、このsandboxではlong-path実経路がcapability SKIPとなり、real relay/roundtripとmutationが未実証なことです。commit・index更新・対象外編集は行っていません。