## 総括

lane B の識別束縛を実装しました。予約 writer・予約 entry は作成しておらず、commit もしていません。

実装ファイル:

- [ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/ledger.py)
- [test_t793_publication_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_publication_ledger.py)
- [t139-publication-reservations.jsonl](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/registry/t139-publication-reservations.jsonl) — 0 bytes

公開 API:

- `canonical_publication_ledger_path() -> Path`
- `read_publication_ledger() -> PublicationLedger`
- `PublicationLedger(entries: tuple[PublicationReservation, ...])`
- `PublicationReservation(family_root: str, kind: str, ordinal: int, schema_version: str)`
- `PublicationLedgerError`

公開 reader/path API は引数なしです。repository root を受ける seam はテスト専用の private 関数に限定しました。環境変数による path 差し替えもテストで拒否しています。

固定値:

- `family_root = 88d68f9127b31df5aafc3d59607896626a1652e8`
- `kind = individual_publication`
- `schema_version = t139-publication-reservation/v1`
- canonical path = `output/registry/t139-publication-reservations.jsonl`

実装した検査:

- 0-byte 台帳を「存在するが予約なし」として受理
- file 不在、非 regular file を拒否
- canonical JSONL、重複 JSON key、exact key-set
- publication 固有 root・kind・schema
- 正の整数 ordinal（bool は拒否）
- `(family_root, kind, ordinal)` 重複
- primary の `(dce4ae4f…, alpha_reservation)` 空間との衝突
- committed history の削除・再作成、非 prefix extension

既存 `trial_registry` と重複する検出力:

- canonical JSON encoding、重複 key、exact schema
- regular-file read
- committed history の strict prefix extension
- delete/recreate 拒否

publication 固有の純増分:

- 固定 identity からの無引数 canonical path 導出
- 0 bytes と file 不在の区別
- `individual_publication` の閉集合
- publication 固有 root/schema
- primary `(root, kind)` 空間との互いに素性
- publication reservation identity の重複拒否

予約 writer、`reserve_next_publication()`、成功を `True` で返す admission API はありません。実台帳への予約行もありません。原子予約は canonical main + land lock との統合が必要なため scope 外のままです。

検査結果:

- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- AST・末尾改行・0-byte 静的検査: 成功
- 引数なし production P4 smoke: canonical path、entry 0 件、file size 0 を確認

pytest は未実走です。次を `tools/run_tests.py` に指定しましたが、いずれも pytest 起動前に `qstat -Q preflight rc=1`、runner rc=16 で停止しました。

- `orchestrator/tests/test_t793_publication_ledger.py`
- 同ファイルの collection-only
- 上記ファイル + `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`

したがって緑は主張しません。

0-byte file の既存検査への影響:

- `check_docs.py`: `output/registry` を対象にせず、実走 rc=0
- `test_frozen_artifacts.py`: exact 23 path のみを検査し、新規 ledger は対象外。静的には赤経路なし
- `run_tests.py` の受入形: unstaged deletion を拒否するが、安定した 0-byte tracked file 自体を拒否する検査はなし
- plain-runner meta-test: 新規テストに `_run()` / `__main__` harness を実装済み。ただし未実走

所有外への波及可能性:

- `orchestrator/publication/__init__.py` は lane A 所有のため未変更。top-level re-export は本 lane では行っていません
- production caller・validator・consumer は未結線
- shared fixture は未変更
- `orchestrator/preregistration/`、`orchestrator/campaign/`、docs、primary 台帳は未変更
- primary 台帳は引き続き 143 bytesです。