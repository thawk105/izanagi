X-1〜X-3 は実装済みですが、pytest は未実走です。

- `py_compile`: 対象8ファイル成功
- `git diff --check`: 成功
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功
- pytest: 計算ノード dispatch を2回試行し、いずれも `qstat -Q preflight rc=1`、rc=16。実行 0 node
- commit・git操作なし

所有外への波及可能性:

- 削除した `certifying_input` 引数を使うリポジトリ外 caller は `TypeError` になる。
- `record_trial_terminal()` の hash 引数を使う外部 caller は追随が必要。
- alternate lifecycle ledger や start と異なる run directory を使う acceptance は拒否される。
- `t080_freeze_migration.py` の schema reader は片側だけの certifying/receipt を新たに拒否する。

## 総括

| 所見 | 状態 | 対応 |
|---|---|---|
| X-1 | partial（実装済み・未実走） | generic bool 引数を廃止。verified receipt 経路だけが true と receipt を同時投影。cross-field invariant と負例を追加 |
| X-2 | partial（実装済み・未実走） | 発行 object identity 限定の one-shot capability、canonical ledger、内部 hash 導出、run-root 一致検査と負例を追加 |
| X-3 | partial（実装済み・未実走） | 5 field の self-consistent 変異、completeness 明示迂回、期待 reason 完全一致を追加 |

受理集合の拡大はありません。X-1/X-2 の不正入力についてのみ意図した縮小があります。X-3 はテスト強化のみです。

予告する赤: なし。ただし baseline `6246 passed / 0 failed / 19 skipped` との比較は未実走です。