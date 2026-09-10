## 総括

実装済み・pytest 未実走です。commit、docs、`orchestrator/preregistration/`、`orchestrator/publication/__init__.py` は変更していません。

実装ファイルと公開 API:

- [approval_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_guard.py:105)
  - `require_resolved_approval_markers(repository_root: str | os.PathLike[str], decision_payloads: Iterable[bytes]) -> None`
  - `ApprovalGuardError`
  - `UnresolvedApprovalMarkerError`
  - `UNRESOLVED_APPROVAL_MARKERS`
- [addendum_p_envelope.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/addendum_p_envelope.py:24)
  - `require_addendum_p_exact_fields(blob: bytes) -> None`
  - `ADDENDUM_P_EXACT_FIELDS = frozenset({"p01", "p02", "p03"})`
- 新規テスト:
  - [test_t793_approval_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_approval_guard.py:46)
  - [test_t793_addendum_p_envelope.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_addendum_p_envelope.py:23)

`tools/spool_fold.py` の変更箇所:

- fresh `_discover()` で decision fragment raw bytes を検査: [spool_fold.py:1038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1038)
- 共通 guard adapter: [spool_fold.py:1054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1054)
- plan/state から decision payload を安全に取得: [spool_fold.py:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1072)
- `apply_fold()` で stored plan 確定後、state 永続化・canonical 書込み前に検査: [spool_fold.py:2347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2347)

3 経路の結線:

- fresh `validate_spool_tree()` / `plan_fold()` → `_discover()` の [1038 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1038)
- plan 直接 `apply_fold()` → [2354 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2354)
- CLI resume → state plan を読む [2572 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2572) から `apply_fold()` [2582 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2582) を経て同じ 2354 行の gate

検査結果:

- `python3 tools/spool_fold.py --dry-run --fold-date 2026-08-11`
  - rc=0、`status=noop`。P2 の現行 repo smoke は通過。
- `python3 -m py_compile ...`、`git diff --check`
  - 成功。
- `python3 tools/check_codex_agents.py`
  - 成功。
- `python3 tools/check_docs.py`
  - `check_docs: 違反なし`。
- pytest は以下を runner 経由で起動しましたが、双方とも `qstat -Q preflight rc=1`、runner `rc=16` で実行開始前に停止しました。したがって緑は主張しません。
  - `orchestrator/tests/test_t793_approval_guard.py` と `test_t793_addendum_p_envelope.py`
  - `orchestrator/tests/test_spool_fold.py` 全体

未実走で影響しうる既存 nodeid prefix は `orchestrator/tests/test_spool_fold.py::` 全体です。特に直接影響するのは以下です。

- `test_n12_second_fold_after_gc_is_noop`
- `test_n16_transaction_rejects_third_state`
- `test_interrupted_transaction_resumes_before_and_after_targets`
- `test_explicit_dry_run_plan_object_is_directly_applicable`
- `test_p02_three_ledgers_with_cross_references_apply`
- `test_p03_empty_spool_is_noop`

所有外への波及可能性:

- `tools/check_docs.py` が `validate_spool_tree()` を直接ロードする。
- `tools/dev_wave_land.py` が `plan_fold()` / `apply_fold()` を呼ぶため、新 deny が land 経路にも発火する。
- 新テストは既存 `test_spool_fold.py` の共有 fixture helper を利用するため、その helper 変更の影響を受ける。
- package-level exportが必要なら lane A 所有の `orchestrator/publication/__init__.py` 側での判断が必要。今回は触れていない。
- 追補 P wrapper は明記どおり production caller がなく、単体検査専用。