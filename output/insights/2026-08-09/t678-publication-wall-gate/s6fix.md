## 変更内容

F1 と F2 のテスト観測器だけを修正しました。production への追加変更はありません。

- F1: `_write_json_temp` を wrapper 化し、receipt path の temp 作成だけを記録。呼出しが1回であることと、final receipt が同一 inode であることを検査します。
- F2: helper の置換を廃止。receipt path に対する最初の `os.link` だけを失敗させ、production helper の例外時 cleanup を通したうえで temp 残骸不在を検査します。
- R1 backlog 1、S-A〜S-G、時間予算値は変更していません。
- `tools/codex_worker_launch.py` は段5差分のままで、今回の fix では編集していません。

## 所見対応表

| 所見 ID | closed・partial・regressed | 根拠 (file:line) |
|---|---|---|
| F1 / R2 MF-1 | partial | receipt 限定 wrapper は [test_codex_worker_launch.py:2160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2160)、1回・inode 同一性は [test_codex_worker_launch.py:2178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2178)。実走未完了のため closed とはしていません。 |
| F2 / R1 nit 1 | partial | receipt 限定 `os.link` 注入は [test_codex_worker_launch.py:2192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2192)、既存結果と temp 不在の検査は [test_codex_worker_launch.py:2211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2211)。実走未完了のため closed とはしていません。 |

## 検査結果

次の nodeid を正式 runner で起動しました。

- `test_accepted_publication_reuses_the_staged_receipt_temp`
- `test_receipt_publication_failure_removes_output_and_writes_error_receipt`

`tools/run_tests.py` は `qstat -Q preflight rc=1` の Pegasus dispatch infrastructure failure で停止し、pytest 本体には到達しませんでした。直接 pytest へは迂回していません。したがって判定は **実装済み・未実走**です。

静的検査結果:

- Python AST parse: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし
- `git status`: 指定された既存の2ファイルだけが modified。新規ファイル、git add、commit はありません。

## 静的な波及可能性

- 所有外 caller: repository-wide 検索では、対象 helper の Python caller は許可された production/test ファイル外にありません。
- production 内 caller: `_atomic_create_json`、`_run_supervised`、`_publish_launcher_error_receipt`。F2 は後二者を連続して通しますが、早期 `_atomic_create_json` 経路は直接対象外です。
- 共有 fixture: `_write_fake_codex`、`_base_command`、`_run_main_in_process` は未変更です。
- `LAUNCHER.os` は共有 `os` module ですが、wrapper は receipt destination 以外を元の `os.link` へ委譲し、pytest の `monkeypatch` により終了後復元されます。
- consumer test: 正常 accepted、create-only race、invalid partial receipt 置換、partial visibility の各テストへ publication 契約上の関連があります。親の全走対象に残ります。
- `replace_invalid=True` の inode/cleanup 固定不足は、裁定どおり backlog のままです。

## 総括

- F1 は helper signature 非依存の temp 回数・inode 観測へ変更しました。
- F2 は production helper 内の receipt `os.link` 失敗を通す検査へ変更しました。
- production の受理集合・gate・時間予算は変更していません。
- 焦点2 nodeは runner を起動しましたが、dispatch infrastructure failure で未実走です。
- 静的検査は成功しました。
- 残るリスクは実走未完了と、裁定済み `replace_invalid=True` backlog です。