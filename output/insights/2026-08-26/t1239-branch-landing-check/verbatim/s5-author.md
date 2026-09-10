## 実装

指定された 2 file のみ新設しました。

- [tools/check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:1)
- [test_check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_check_branch_landed.py:1)

主な実装内容:

- `git rev-list branch --not main` の全 commit closure と全 parent edge を検査。
- `(path, mode, object type, oid)` の同時一致のみを決定的内容証拠として採用。
- spool receipt miss は `indeterminate`。frontmatter 除外後の構造単位を ledger/archive から検索し、非決定の `observations.ledger_probe` に記録。
- 逐語、patch-id、task ID は全て非決定の `observations`。
- task ID は worklog、decisions、failures、phase3、archive を検索。
- 候補上限、履歴走査量上限、候補数、走査 commit 数、所要時間を分離して出力。
- timeout、上限、shallow、replace ref、parse error、ref 移動は安全側へ処理。
- D720 条件 1 限定、条件 2 未検査、land 非許可を全 JSON に明示。
- self-run harness を実装し、README allowlist は変更していません。

既存 tool・caller の受理集合は変更していません。新設 checker の挙動は以下です。

- `landed`, exit 0: closure 空、または全証明単位が exact state／exact receipt で証明済み。
- `not-landed`, exit 1: 完全探索済みの真の純追加で、同 path も同一 object の別 path 移植も存在しない場合。
- `indeterminate`, exit 2: receipt miss、逐語だけの一致、状態不一致、探索打ち切り、repository integrity 不確定。
- CLI 構文不正は exit 64、`--help` は exit 0。

## 実走結果

pytest は実装済み・未実走です。正規 runner を3回起動しましたが、いずれも pytest child が開始される前に rc=16 となりました。

- `qstat -Q preflight rc=1`
- `NQSconnect: [API ESYSCAL] Can't create socket. (errno: 1)`
- `child_started=false`
- login headroom も固定予約 2 GiB と最小 test 予算 1 GiBを満たさず、local 実行不可。

したがって、緑と申告できる pytest nodeid はありません。assertion failure も未観測ですが、これは node 未起動のためであり、赤がないことを意味しません。

未実走範囲:

- `orchestrator/tests/test_check_branch_landed.py`: 25 test 関数、parametrize 展開前の静的見積もりで 26 node。
- file 集合メタテスト:
  - `orchestrator/tests/test_plain_runner_coverage.py` 全3 node。
  - `orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`

pytest 以外で緑を確認したもの:

- `python3 -m py_compile` — rc=0
- `git diff --check` — rc=0
- closure 空の checker CLI smoke — exit 0、`branch-closure-empty`
- 実 repo の raw diff parser smoke — 9 state を正常 parse
- 実 repo の receipt parser／ledger corpus smoke — receipt 1,736件、ledger 750 file を正常 parse
- `python3 tools/check_codex_agents.py` — rc=0
- `python3 tools/check_docs.py` — rc=0
- U+0300〜U+036F — 検出なし

親が再実走すべき command:

```bash
python3 tools/run_tests.py -q orchestrator/tests/test_check_branch_landed.py
python3 tools/run_tests.py -q \
  orchestrator/tests/test_plain_runner_coverage.py \
  orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests
```

## 静的な波及確認

- 既存 caller: なし。`check_branch_landed` の参照は新 tool と新 test のみ。
- 共有 fixture: 変更なし。新 test は `tmp_path` と `monkeypatch` のみ使用。
- consumer test:
  - `test_plain_runner_coverage.py` が新しい `test_*.py` を列挙。
  - `test_pytest_collection_config.py` が同じ file 集合を glob。
  - 通常の `tools/run_tests.py` 全 collection に新しい test が追加される。
- `orchestrator/tests/README.md` は self-run harness があるため変更不要。
- `git status --short` で変更は指定 2 file のみ。
- commit、add、stash、merge、rebase、checkout、switch、reset、branch は作業 repo に対して実行していません。

## M1〜M10 実装位置

全て [tools/check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:1) 内です。

- M1 — `tools/check_branch_landed.py:674`
- M2 — `tools/check_branch_landed.py:789`
- M3 — `tools/check_branch_landed.py:341`
- M4 — `tools/check_branch_landed.py:341`
- M5 — `tools/check_branch_landed.py:444`
- M6 — `tools/check_branch_landed.py:685`
- M7 — `tools/check_branch_landed.py:254`
- M8 — `tools/check_branch_landed.py:444`
- M9 — `tools/check_branch_landed.py:1003`
- M10 — `tools/check_branch_landed.py:880`

M3/M4 は merge を除外しない単一の closure 列挙式、M5/M8 は path を含む完全 tuple の単一比較式を共有します。

## 総括

A1〜A8 と改訂 P1〜P3 を指定 2 file に実装し、既存の受理集合には触れていません。syntax、静的差分、read-only CLI、repo checker は通過しています。

残る不確実性は、pytest 26 node、file 集合メタテスト、M1〜M10 の変異が未実走である点です。親は queue または login headroom 回復後に上記 runner command を実行し、全 node の緑と変異 KILLED を確認してから統合してください。