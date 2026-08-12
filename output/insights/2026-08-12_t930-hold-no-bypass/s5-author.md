段 4 の plan v2 を実装しました。docs、`conftest.py`、保留台帳、既存期待値は変更せず、commit も作成していません。

## 変更ファイル

- [growth_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/growth_test_holds.py:212): `GrowthTestHoldBypassRefused`、call-time wrapper、`enforce_held_functions()` を追加。範囲は 212-271 行。
- [test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_growth_test_holds_contract.py:316): AST binding、30 node wrapper、subprocess matrix、exact token、fixture / parametrize、過剰拒否検査を追加。主範囲は 316-634 行。
- 8 held file に末尾 2 行の binding を追加:
  - [test_campaign_import_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_campaign_import_invariant.py:1707)
  - [test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_codex_reasoning_ab.py:4269)
  - [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_env_attestation.py:1359)
  - [test_ruleops.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_ruleops.py:3455)
  - [test_s8b_binding_driftguards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_binding_driftguards.py:536)
  - [test_s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_holdout_freeze.py:1222)
  - [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_oracle_driver.py:4931)
  - [test_s8b_repo_scan_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_s8b_repo_scan_invariant.py:54)

台帳は 30 row、key digest は `8e4917269631347e1a78c2ac82875efc6ac509bba1181037ee7fab26208f6205`、`release_condition` は全件 `explicit-user-command-only` のままです。

## 実走結果

Pegasus login node の headroom が不足し、`tools/run_tests.py` は計算 node dispatch を選択しましたが、`qstat -Q preflight rc=1` となりました。runner の終了値は rc=16 です。このため、pytest の結果を緑とは申告しません。

| 対象 | 件数 | rc | 結果 |
|---|---:|---:|---|
| `test_growth_test_holds_contract.py` | 未収集 | 16 | 実装済み、未実走 |
| `test_plain_runner_coverage.py` | 未収集 | 16 | 実装済み、未実走 |
| `test_env_attestation.py` | 未収集 | 16 | wrapper 経由も dispatch 失敗。`103 passed, 1 skipped` は未確認 |
| A: `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control` | 未収集 | 16 | 実装済み、未実走 |
| B: 同 node、`--noconftest` | 未収集 | 16 | 実装済み、未実走 |
| E: `python3 test_s8b_repo_scan_invariant.py` | held body 到達 0 件 | 1 | prefix 付き拒否を確認、0.2 秒未満 |
| fixture / parametrize opt-in contract node | 未収集 | 16 | 実装済み、pytest 未実走 |

追加の非 pytest probe は次を確認しました。

- G 経路は rc=1、`IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1` を出力。
- 別 process からの held 関数直接 call は rc=1、同 prefix を出力。
- 実 module の registry 30 / 30 node が wrapper 化され、unset では全件 body 到達前に拒否。
- 合成軽量 body は typo token で到達 0 件、exact token で到達 1 件。
- AST binding は 8 / 8 file が成立し、in-memory で call を除去した負例を検出。
- syntax compile、`git diff --check`、分解 Unicode combining mark 0 件を確認。

fixture / parametrize については、held 名を持つ軽量 test を tmp file に作り、fixture 1 件と parametrize 2 caseを exact token 下で実行する契約 testを実装済みです。ただし上記 rc=16 のため、実際の `2 passed` は未確認です。

## 波及可能性

所有外 caller、fixture、consumer への静的影響は次のとおりです。

- `conftest.py`: 未変更。通常 pytest の skip、hold metadata、`xdist_group("real-repo")` は従来経路のままです。
- 自前 `_run()` 2 file: held 関数からの例外を既存 `except Exception` が受け、ERROR と rc=1 に変換します。runner 本体は未変更です。
- `pytest.main()` 委譲 3 file: 通常 collection では conftest の skip が wrapper call より先に効く設計です。
- shared fixture: `repository_scan`、`benchmark_snapshots`、`tmp_path`、`monkeypatch`、`capsys` など。`functools.wraps` により signature と `pytestmark` を維持します。
- parametrized held 関数: `test_m3_focus_artifact_directions`、`test_prompt_replacement_count_zero_expected_and_excess`。marker は wrapper へコピーされます。
- `test_plain_runner_coverage.py`: 既存 `_run()` / `pytest.main()` signal は未変更。ただし実走は未確認です。
- `test_pytest_failure_digest.py`: `conftest.py` bytes が不変なので copy 契約への変更はありません。
- real-repo serialization consumer: node 名と既存 markerを保存するため、collection identityを変えない設計です。
- 非 held testまたは別 processから held 関数を直接呼ぶ caller: tokenなしでは新たに拒否されます。これは段 4 で明示された封鎖範囲です。
- production caller、production hold、CLI、設定ファイルへの変更はありません。

## 受理・拒否差分

| 経路 | 現行 | 変更後 |
|---|---|---|
| A、tokenなし | conftest が skip | 同じ。wrapper は呼ばれない設計 |
| A、exact token | held body 実行 | 同じ |
| A、typo token | conftest の UsageError | 同じ |
| B、tokenなし | 30 node を迂回実行可能 | held node call時に rc != 0 と prefix |
| B、exact token | held body 実行 | 同じ |
| E、自前 `_run()` 2 file | held body 実行可能 | body 到達前に拒否、rc=1 |
| E、`pytest.main()` 3 file | conftest が skip | 同じ設計 |
| E、`__main__` なし 3 file | 0 test、rc=0 | 同じ |
| G、conftest import後の runpy | 迂回可能 | call-time 拒否 |
| held 関数の直接 call | 迂回可能 | call-time 拒否 |
| 非 held 関数 | 実行 | wrapper 対象外、変更なし |

解除口は既存の `IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` だけです。新しい env、CLI flag、設定は追加していません。

意図的に赤へ変更した既存 test はありません。現時点の rc=16 は test failure ではなく dispatch infrastructure failureです。

## 総括

段 4 裁定どおり、sentinelや conftest 変更を使わず、registry 由来の node 単位 call-time wrapper で B、E、G、直接 call の迂回を封鎖しました。コード、契約 test、8 file の binding は完成しています。

pytest 系の必須検証だけは Pegasus の headroom不足と dispatch接続不能により未実走です。docs編集と commitは行っていません。