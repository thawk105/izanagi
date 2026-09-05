## 受理・拒否挙動

現行 verifier は clean・非巡回 trace を認証し、巡回検出時は `non-serializable / certified=False`、integrity 不良時は `indeterminate / certified=False` とする。今回 production コードは変更しておらず、実行時の受理集合は不変である。

テスト側の受理集合は狭まり、clean な長さ 4 の G2、正確な commit/thread 順序、4 辺、空の `abort_reasons` を維持できない実装・fixture を拒否する。

## 実装

- 指定どおり [trace_0.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/r9_dense_cycle4/trace_0.log:1) 12 行、[trace_1.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/r9_dense_cycle4/trace_1.log:1) 4 行を追加。
- [test_dense_cycle4_clean_g2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:124) を追加。`abort_reasons`、4 組の `(txid, thid, commit)`、統計・G2・4 辺を pin。
- [_V2_FIXTURE_FILES](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:293) と [README 表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:30) を更新。
- README の所有外行、既存 assert、`orchestrator/verifier/` は未変更。commit・index 操作も未実施。

## 検査結果

実走を試みた範囲は `test_verifier.py` 全体と次の meta-test だった。

- `test_verifier.py::test_dense_cycle4_clean_g2`
- `test_verifier.py::test_all_v2_fixture_files_have_clean_framing`（在庫完全一致と framing）
- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`（素の runner 契約）

ただし Pegasus dispatch の `qstat -Q` が認証エラーとなり、`rc=16 / child_started=false` で停止した。実走した nodeid は 0 件で、実装済み・未実走である。user cgroup の観測 headroom は約 1.26 GiB だった。

静的検査は以下が成功した。

- `git diff --check`
- Python AST 構文解析
- `tools/check_codex_agents.py`
- `tools/check_docs.py`
- 許可された 4 file 以外の差分なし

## 波及可能性

- fixture root の再帰在庫・framing 検査が新しい 2 file を共有 fixture として扱う。
- 素の runner は `globals()` の全 `test_*` を動的収集するため、新テストも自動的に対象となる。
- CLI、campaign、receipt、admission、oracle、report は verifier 結果の downstream consumer だが、production API・判定ロジックに変更がないため挙動への直接波及はない。
- 新 fixture 名の参照は今回の test・在庫・README に限定され、所有外 consumer の literal 更新は不要。

## 総括

- clean な長さ 4 G2 fixture と回帰テストを、指定された 4 file だけに実装した。
- production 差分、commit、index 操作はない。
- 静的検査とリポジトリ checker は緑。
- pytest/meta-test は dispatch 基盤 `rc=16` のため未実走。観測されたテスト赤はなく、未検証 node が残る。