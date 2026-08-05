| 所見 | 判定 | 対応 |
|---|---|---|
| 空 registry の受理 | closed | 空 mapping を `ValueError` とし、diagnostic 付き縮退へ移行。回帰テスト追加。 |
| 内部例外時の偽陽性 pin | closed | 非実行の Pegasus mention は rc=2、無関係 command は rc=0、正常時は mention も rc=0 と固定。 |
| loader 子プロセス監督 | not-done | 親裁定どおり対象外。 |
| inode read 前後照合 | not-done | 親裁定どおり対象外。 |
| stale pyc／配線 skip | not-done | 他者所有・対象外のため未変更。 |

## 総括

- [guard_bash.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/hooks/guard_bash.py:231) と [test_hooks.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1772) のみ編集。
- `main()` の挙動、既存期待値、正常24 entryの受理集合は変更していない。
- AST parse は成功。
- pytest は指示どおり未起動。**実装済み・未実走**。