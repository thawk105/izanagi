## 実装結果

編集は指定された3ファイルだけです。

- [tools/pegasus_admission_registry.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/tools/pegasus_admission_registry.py:37)
- [hooks/guard_bash.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/hooks/guard_bash.py:175)
- [orchestrator/tests/test_hooks.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1391)

`tools/pegasus/admission_registry.json` および所有外ファイルは編集していません。commit も作成していません。

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| A1 wrapper postcondition | closed | plain `dict`/`str`、canonical Pegasus path、exact 4 field、非空値、class 閉集合を再検証。管轄外 registry lookup も遮断 |
| A1 main 内部例外 | closed | `BaseException` を捕捉し、raw の `tools/pegasus` / `tools.pegasus` mention を rc=2 に変更 |
| A2 FIFO・cleanup | closed | `O_NONBLOCK`、regular-file 判定、cleanup 例外の正規化・隔離を実装 |
| A3 stale pyc | closed | import machinery を廃止し、source bytes の `compile()` / `exec()` に変更。unchecked stale pyc fixture を追加 |
| A4 fault matrix | closed | 指定された malformed return、top-level/function の `SystemExit`・`KeyboardInterrupt`、entry fault、sanctioned 導出 faultを timeout 付き実 subprocess・exact rc=2 で固定 |
| A5 fd 防護検出器 | closed | symlink、directory、oversize、FIFO、権限拒否 fixtureと、regular・stat cap・bounded read の独立検出器を追加 |
| A6 negative corpus | closed | 順序、indent、改行、空 entries、各種不正 path、field 欠落・余分・空を direct loader／実 hook 双方へ追加 |
| A7 制御文字 | closed | NULを含む Unicode `Cc` 制御文字を path で拒否 |
| loader deadline 子プロセス化 | not-done | 親裁定どおり実装せず |
| A8・launcher 残穴 | not-done | scope外裁定どおり未変更 |

正常24 entryの4 field、literal golden、LOGIN/SUSPECT・OTHER/COMPUTEの既存期待値は変更していません。

## 検査

`python3 -m py_compile tools/pegasus_admission_registry.py hooks/guard_bash.py orchestrator/tests/test_hooks.py` は rc=0 でした。

Pegasusログインノードのため pytest は起動していません。したがって、状態は「実装済み・未実走」です。緑は主張しません。`check_docs.py`、`check_codex_agents.py`、provenance監査も未実走です。

## 静的な波及可能性

- `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` は共有loaderのconsumerです。公開APIは不変ですが、FIFOの即時拒否と制御文字拒否が波及します。
- `.claude/settings.json` 経由の実hook起動は、wrapper初期化と`main()`の例外処理変更の影響を受けます。
- `test_hooks.py` 内の `_prepare_guard_fixture`、`_load_guard_fixture` を拡張し、新しい subprocess fixtureと共有しています。
- runbook、各README、registry投影表はデータ変更がないため編集していませんが、計算ノードでconsumer testを実測する必要があります。

## 総括

- A1〜A7の採用所見を指定3ファイル内で修正しました。
- registry本体24 entryと既存期待値は未変更です。
- source直実行により stale／unchecked pyc 経路を排除しました。
- fault・特殊ファイル・canonical negative corpusの検出器を強化しました。
- 構文検査rc=0、pytestはログインノード規律により実装済み・未実走です。