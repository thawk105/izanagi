## 変更したファイルと行

- [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:137)
  - `note: str = ""`、7件目の固定 entry、逐語 note guard、`_known_violation_line()` を追加。
  - rc=0/1 両方の出力を helper 経由へ変更。
- [test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1323)
  - 指定4テストを7件仕様へ更新・改名。
  - 5-case `test_broken_registry_note_is_rc2` と、非空 note の rc=1 合成テストを追加。
  - `_known_spec()` と既存の空 note stdout テストは変更なし。

所有外の変更、index変更、commitはなし。作業ツリーは上記2ファイルのみ `M`。

## 走らせた検査

テスト実走を次で試行しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_check_ai_provenance.py::test_known_violation_ledger_is_exactly_seven_literal_entries orchestrator/tests/test_check_ai_provenance.py::test_known_violation_ledger_matches_real_commit_findings orchestrator/tests/test_check_ai_provenance.py::test_broken_registry_note_is_rc2 orchestrator/tests/test_check_ai_provenance.py::test_known_violation_nonempty_note_is_public_on_rc1 orchestrator/tests/test_check_ai_provenance.py::test_empty_registry_restores_all_seven_real_findings orchestrator/tests/test_check_ai_provenance.py::test_ledgered_3f2c43d7580b_is_known_and_rc0 orchestrator/tests/test_check_ai_provenance.py::test_known_violation_stdout_is_public_on_rc0_and_rc1 orchestrator/tests/test_check_ai_provenance.py::test_every_checker_main_call_in_this_suite_pins_the_site
```

- rc=16
- Pegasus dispatch の `qstat -Q preflight rc=1`
- pytest開始前のため passed=0 / failed=0
- 指定8 nodeid（note matrixは5 case）すべて実装済み・未実走
- 拡張範囲 `-k known_violation` とファイル全体も未実走
- 指示どおり直接pytestへ迂回していない

静的検査:

- `python3 -c 'import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding="utf-8"), filename=p) for p in ("tools/check_ai_provenance.py", "orchestrator/tests/test_check_ai_provenance.py")]'`
  - rc=0、nodeidなし、passed/failed対象外
- `git diff --check -- tools/check_ai_provenance.py orchestrator/tests/test_check_ai_provenance.py`
  - rc=0、nodeidなし
- `python3 tools/check_codex_agents.py`
  - rc=0
- `python3 tools/check_docs.py`
  - rc=0、`check_docs: 違反なし`

## 受理集合の変化

変更前:

- 固定6件だけを full SHA完全一致 × finding種別一致で既知化。
- `3f2c43… / missing-ai-agent` は新規違反、rc=1。
- 型・重複・非full SHA・未知種別・空ruling・staleはrc=2。

変更後:

- `3f2c43d7580b8c26724d90278589862057508965 / missing-ai-agent` の1組だけを既知集合へ追加。
- 非空noteは `str` かつ単一行のみ受理し、破損はrc=2。
- prefix一致、種別wildcard、同commitの他finding吸収、一entry複数件吸収への拡張はない。
- correction、waiver、message-file、ancestry-path、stale判定は不変。

## 波及の静的列挙

- 所有外caller:
  - `__main__`
  - `tools/task_run_check.py`
  - `tools/pegasus/dispatch_compute.py`
  - `tools/dev_wave_land.py` のmessage preflight
  - `tools/dev_waves/checker.py` からの間接実行面（stdoutを捨てる既知課題T-621は未解決）
- 共有helper:
  - `_init_repo()`、`_commit()` を新規テストで再利用。
  - `_known_spec()` のsignatureは不変。既存3引数constructionも互換。
  - repository-local pytest fixtureはなし。
- consumer test:
  - correction、waiver、message-file、site/dispatch、並列監査の各 `main()` consumer。
  - 空noteの逐語互換をpinする `test_known_violation_stdout_is_public_on_rc0_and_rc1` は未変更。
- production/test以外に `KNOWN_PROVENANCE_VIOLATIONS` または `known-violation` recordをparseするPython consumerは静的検索で見つからなかった。

## 期待して赤くなるもの

なし。親のworklog／D221 decisions fragment未landを理由に赤くなるコードテストはありません。

pytestは未実走のため、将来の実走で今回のdispatch infrastructure failure以外に赤が出れば回帰として扱う必要があります。

## 総括

7件目の既知違反と裁定済み単一行noteを実装しました。  
full SHA × 種別、一entry一件、stale rc=2などの不変条件は維持しています。  
静的検査4本はrc=0ですが、pytestはdispatch preflight失敗により未実走です。  
docs編集・stage・commitは行っていません。