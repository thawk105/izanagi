単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/s6-adjudication.md — **段 6 裁定。本 fix は末尾「追補」の F6 だけを直す**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1-prompt.md — 制約と報告形式の正本 (全文適用)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1b-prompt.md — 差し替えの範囲の正本 (Tier0 より手前の準備層は差し替えてよい)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/mutation-probe-m0-stdout.txt — **親の変異 probe で、等価変異 M0 (p3_s4_loop.py に comment 1 行) を注入したときの pytest 出力**。挿入点 test 16 node が contract-loader-drift で落ちている。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py — 所有 file (唯一の編集対象、`insertion_case` fixture)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py — 参照 (`drive_iteration` 入口と `_run_one_iteration_resolved` 内の `ident.ensure_resumable_attempts`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/ident.py — 参照 (`ensure_resumable_attempts`、`ensure_campaign_identity`、`_capture_current_loader_binding`)。読めなければ即停止

この checkout は branch `dev-wave-t2797-unit-a1-fix1d`、HEAD は `8469b6d4b` (fix1c までを統合済み)。

## 事実 (親の実測)

- 焦点走 f3 (HEAD = 8469b6d4b、作業木 = HEAD) では `test_b5_tier0.py` は全件緑。
- 変異 probe (作業木だけに一時変異を注入、HEAD は 8469b6d4b のまま) では、**内容に意味の無い等価変異 M0 でも** 挿入点 test 16 node
  (`test_insertion_build_smoke_sidecar_submission_order` / `test_insertion_rejection_rc3_no_submission_wal_or_digest` / `test_insertion_preparation_and_build_errors_propagate` の全 parameter) が
  `main` → `drive_iteration` 入口 → `ident.ensure_resumable_attempts` → `ensure_campaign_identity` の `contract-loader-drift: disk bytes が HEAD blob と不一致: orchestrator/campaign/p3_s4_loop.py`
  で落ちる。このため `p3_s4_loop.py` の配線変異 (M1 / M2 / M3 / M9 / M10 / M10b / M11) の kill を変異の内容へ帰属できない。

## 作業 (F6)

- `insertion_case` fixture で、Tier0 より手前の identity 準備 (`ident.ensure_resumable_attempts` — `drive_iteration` 入口と `_run_one_iteration_resolved` 内の両方の呼出し) を
  差し替え、挿入点 test が `p3_s4_loop.py` の作業木変化そのもの (contract-loader の HEAD blob 照合) に反応しないようにする。差し替え後も、その先で contract-loader の
  HEAD blob 照合に触れる呼出し (例: campaign id / preimage の計算、sidecar payload) が残っていないかを実コードで辿り、残っていれば同じく準備層として扱うか理由を報告する。
- 検査項目 (順序・perf binary・拒否 rc 3・submission / WAL / digest なし・例外境界と伝播) と parameter は変えない。検査対象の機構は差し替えない。
- 変更後、「作業木の `p3_s4_loop.py` に comment を 1 行足しても挿入点 test の判定が変わらない」ことが静的に言えるかを報告する (親が probe で実測する)。
- 編集は `orchestrator/tests/test_b5_tier0.py` だけ。本番コードの差分 0。

制約・報告形式は `s6-fix1-prompt.md` の「制約」「報告形式」を全文適用する (git commit しない / docs を編集しない / テストを走らせない /
既存テストの期待値を変更しない / 機構を stub しない / 揮発値を焼き込まない / 受理集合を変えない / 本番コードに test 専用の迂回を入れない)。
報告の 1 の対応表は F6 の 1 行でよい。最後に `## 総括` を置く。
