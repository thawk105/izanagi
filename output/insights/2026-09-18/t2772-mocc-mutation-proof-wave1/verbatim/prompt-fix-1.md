単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2772-mocc-mutation-proof-wave1

## 必読事項の射影

次の絶対パスを読む。読めなければ即停止し、読めなかったパスを `## 総括` に書いて終わる。

- /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/s6-reviewA-2.md (段 6 レビュー A。所見 1・2 が must-fix、所見 5 は nit)
- /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/s6-reviewB-2.md (段 6 レビュー B。所見 1 が must-fix、所見 5 は nit)
- /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/s4-ruling.md (段 4 裁定 R1〜R12。契約の正本)
- /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/prompt-author.md (段 5 author の契約。**禁止事項・所有 path・報告形式をそのまま継承する**)
- /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/s5-author-1.md (author の最終報告)
- /home/SFC/tanab/.claude/jobs/46142ba5/tmp/wave-t2772/focus-1.log (親の焦点走 log。赤 1 件の本文 39〜58 行)

作業 repo は **/work/1/SFC/tanab/izanagi/.codex/worktrees/t2772-fix1** (branch impl-dev-wave-t2772-mocc-mutation-proof-wave1-fix1、HEAD b112a2898 = author 実装の統合 commit、submodule external/ccbench は 511c9538)。wave worktree (parent) には書かない。

## 所有 path (これ以外を編集しない)

- `orchestrator/tests/test_mocc_mutation_proof.py`
- `orchestrator/campaign/s3_mocc_mutation_proof.py`

## 禁止事項 (author 契約をすべて継承。加えて)

- 既存テストの期待値を変えない (反転・緩和・skip・削除は禁止)。赤なら実装側を疑う。期待値が誤りなら変えずに報告して止める。
- 旧 driver `s3_mocc_lock_coverage.py`・旧 test・旧 patch・旧 JSON・新 patch `patches/broken-mocc-hot-update-unlock.patch`・登録簿 7 file は触らない。
- 新 module の直接 `subprocess` 呼出し site を増やさない (`_run_trace` の 1 箇所のまま。`_verify` は旧 `_run_checked` 経由を維持)。
- `git add` / `git commit` 等の git 状態変更をしない。docs を編集しない。scratch は system tmp を使い、repo 内に残骸を残さない (`git status --short` は所有 2 file の M だけ)。
- `tools/run_tests.py` と `python -m pytest` は使わない。実走は `PYTHONPATH=. python3 orchestrator/tests/<file>.py` の自走 harness だけ。

## 依頼

段 6 fix 1 巡目 (must-fix 2 件 + should 1 件)。

1. **共有 scratch の競合を除去する** (A 所見 1 / B 所見 1、must-fix)。`orchestrator/tests/test_mocc_mutation_proof.py` の `_source_root` (93〜112 行) から repo 内 `.scratch-t2772` と `created` 判定・共有親への `rmdir()` を削除し、旧 test `orchestrator/tests/test_mocc_proof_surface.py` の `_source_root` (95〜100 行付近) と同じく **system tmp** の `tempfile.TemporaryDirectory(prefix="mocc-mutation-proof-")` を呼出しごとに所有する形にする (repo 内に一時 dir を作らない。xdist 並列で他 worker と共有しない)。`git archive` / `git init` / `git apply` の手順は変えない。
2. **verifier の異常終了を正しく記録する** (A 所見 2、must-fix)。`orchestrator/campaign/s3_mocc_mutation_proof.py` の `_verify` (221〜239 行付近) で、旧 `_run_checked` を **rc を広く許容する `allowed_returncodes`** (例: `frozenset(range(-128, 256))`) で呼び、プロセスが終了したら先に `terminated=True` と実 `returncode` を record に保存し、その後で `returncode ∉ {0, 1, 3}` を `error` (`record` は None のまま) として扱う。timeout は従来どおり `RuntimeError.__cause__` が `subprocess.TimeoutExpired` のときに `timed_out=True`、起動失敗 (OSError 由来) は `terminated=False` のまま `error` に残す。`_matrix_complete` の `verifier["returncode"] not in {0, 1, 3}` 判定は不変 (rc=2 は matrix 赤のまま)。新 test `test_mocc_mutation_verify_binds_protocol_root_and_timeout` に **rc=2 と負の rc (signal 終了)** の 2 例を足し、`terminated is True`・実 rc が保存され・`record is None`・matrix check が false になることを検査する。mock は新 module の binding (`M._run_checked`) に限定し、`M.legacy.subprocess.run` / `subprocess.run` の global patch を `_verify` の検査では使わない (A 所見 5 の nit 対応。`_run_trace` の検査で `subprocess.run` を patch している箇所はそのままでよい)。
3. **経過時間の局所記録** (B 所見 5、should): `_run_trace` と `_verify` の process record に `wall_seconds` (float、`time.monotonic()` 差) を 1 field 足す。`_empty_process` の初期値は `None`。`_matrix_complete` はこの field を検査しない (受理集合を変えない)。新 test の合成 baseline / matrix 検査が `wall_seconds` の有無で赤にならないことを確認する。汎用台帳は作らない。

## 実走と報告

`PYTHONPATH=. python3 orchestrator/tests/test_mocc_mutation_proof.py` (JSON consumer 1 node は JSON 不在で赤が正しい)、`... orchestrator/tests/test_mocc_proof_surface.py` (回帰)。`python3 -c "from orchestrator.campaign import s3_mocc_mutation_proof as m; print(m.CHECK_KEYS == tuple(m.CHECK_KEYS), len(m.MATRIX))"` で import 確認。実走できない検査は「実装済み・未実走」と書く。所有外への波及 (登録簿の Counter・`_DEFERRED_GATE_MEMBERS` の lineno・`acceptance_duration_ledger`) を静的に列挙する。

## 出力形式

Markdown。見出しはすべて `##` (H2)。節: `## 変更 file 一覧`、`## 所見ごとの是正内容` (A1/B1、A2、B5 の順)、`## 実走した検査` (nodeid と結果、赤の内訳)、`## 波及の静的列挙`、`## 総括`。最後の節は必ず `## 総括` (`#` を 2 個) とし、`git status --short` の結果 (所有 2 file の M だけであること) を書く。予算が尽きそうなら途中結論を出力形式どおり書いて終わること (無出力が最悪)。
