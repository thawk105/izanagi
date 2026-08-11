## 総括

現行挙動は次のとおりです。

- 固定 `F_p` の実 bytes、14 top-level keys、承認 2 role、三つ組、`document_relations` 全体、9 値写像を満たす場合だけ受理します。
- 数値は Decimal、ordinal は集合、真偽値は bool、2 canonical 文字列は空白正規化後に比較します。
- 欠落・余剰・重複、別 digest、relation 改変、値不一致、旧 candidate、投入状態の変更を拒否します。
- report は後続 supersession がなければ D291 の承認事実を示します。発見時は `approval_status = not_asserted_after_supersession` に切り替えます。
- 常に `submission_authority=not_granted`、pilot/main とも `forbidden` です。

実装したファイルは指定された 5 ファイルのみです。docs・`orchestrator/preregistration/` は変更せず、commit も作成していません。

- [approval_d291.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py:458)
  - private: `_parse_d291_payload(decisions_blob: bytes) -> D291ApprovalPayload`
  - `load_d291_payload(repository_root: str | Path) -> D291ApprovalPayload`
  - `require_d291_projection_exact(payload: D291ApprovalPayload, projection: Mapping[str, object]) -> None`
  - `resolve_d291_approvals(repository_root: str | Path, *, candidates: Mapping[str, BlobRef] | None = None) -> dict[ApprovedRoleName, D291RoleResolution]`
- [report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py:191)
  - `build_approval_report(repository_root: str | os.PathLike[str]) -> ApprovalReport`
  - `approval_report_to_dict(report: ApprovalReport) -> dict[str, object]`
  - `main(argv: Sequence[str] | None = None) -> int`
- [__init__.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/__init__.py)
- [test_t793_approval_d291.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_approval_d291.py)
- [test_t793_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_report.py)

段 3 blocker は以下の形で閉じました。

- A6: D291 節を次の可視 `## ` または EOF で終端。P1 に実 `F_p` bytes を使用。
- A7: `F_p` と decisions SHA-256 を module literal に固定。任意 bytes parser は private。
- A8: 公開 resolver は常に 2 role 全体を一括検査・返却。単一 role API なし。
- A11: `git show HEAD:docs/decisions.md` を走査し、後続 supersession 時は現在承認を断言しない。

検査結果:

- pytest nodeid実行: **0件（実装済み・未実走）**
- 対象 2 test file の runner 実行を2回試行: `qstat -Q preflight rc=1` により rc=16、テスト開始前に停止。
- F42 meta-test `test_plain_runner_coverage.py` も同じく rc=16、未実走。
- 原因は workspace sandbox から scheduler socket を作れないことです。login headroom も local 実行基準未満でした。
- 補助確認: 決定的 JSON CLI exit 0、canonical parser probe成功、4種の値変異拒否、AST parse、`git diff --check`、`check_codex_agents.py`、`check_docs.py` は成功。ただしpytest緑の代替とは扱いません。

所有外への波及可能性:

- 現時点で既存 production caller はありません。
- `BlobRef` / `read_pinned_blob` の既存署名に依存しますが、当該 packageは未変更です。
- lane B/C、新しい追補P freezer・validator・consumerが将来の主な利用候補です。
- 共有 fixture / `conftest.py` は変更していません。新規testは自己実行 harnessを持たせています。