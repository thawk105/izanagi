単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/s6-adjudication.md — **段 6 裁定。本 fix は F2 (表の行) と 追補 3 の F7 を直す**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1-prompt.md — 制約と報告形式の正本 (全文適用。ただし編集してよい file は下の 2 本に置き換える)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/focus-f3.log — 親の焦点走 f3 (取り込み前、2 failed = F2 の seam 2 件)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py — 編集対象 1 (F7: `_PROVENANCE_OUTCOMES`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_p3_s4_loop.py — 編集対象 2 (F7: `test_base_provenance_records_b5_early_returns`、F2: `_b5_candidate_fixture`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py — 参照 (Tier0 そのものの検査。本 fix では編集しない)。読めなければ即停止

## この checkout の状態 (重要)

branch `dev-wave-t2797-unit-a1-fix2b`、HEAD = `2e53f3649` = 本 wave の Tier0 実装 (fix1〜fix1d 統合済み) に local main `755242b11` を取り込んだ merge commit (clean)。
取り込んだ main には別 wave ([T-2632]) の land が入っており、`p3_s4_loop.py` に base provenance の side channel (`_PROVENANCE_OUTCOMES`、`_append_provenance_entry`、
`_wal_attempt_provenance` と、`drive_iteration` での記録) が足された。自動 merge はテキスト競合なしで通ったが、意味上の不整合 (F7) が残っている。

## 作業

1. **F7:** `p3_s4_loop.py` の `_PROVENANCE_OUTCOMES` に `"rejected-tier0"` を足す。Tier0 拒否は WAL を書かず `variant=None` で返るので、`_wal_attempt_provenance` は既存の
   variant None 分岐 (wal_refs 空) を通ることを実コードで確かめて報告する。他の provenance 関数は変えない。
2. **F7 の test:** `test_p3_s4_loop.py` の `test_base_provenance_records_b5_early_returns` の parametrize に `"rejected-tier0"` を 1 つ足す (既存 2 ケースと期待値はそのまま)。
3. **F2:** `test_p3_s4_loop.py` の共通 fixture `_b5_candidate_fixture` **1 箇所だけ**で、Tier0 の準備 (`_b5_tier0_build_inputs`)・build (`buildcache.build_v2` / `buildcache.build`)・
   smoke (`_run_b5_tier0_smoke`) を「通過」として提供する差し替えを足し、`test_machine_no_authority_guard_and_sidecar_before_campaign` と
   `test_b5_duplicate_skip_returns_failure_without_restore` が本来検査する campaign 境界へ届くようにする。両 test の本体と期待値は変えない。同 fixture を使う他の test
   (候補の前処理拒否、文字列 preflight 拒否など) の結果を変えないことを静的に確かめて報告する。取り込み後の版で [T-2632] がこの fixture や周辺を変えていれば、それに合わせる。
4. 取り込み後の `drive_iteration` (provenance の事前検証 `_load_provenance`、keyword 引数 `initial_proposal_sha256`、`--run-iteration` が常に capture を渡す変更) の下で、
   `test_b5_tier0.py` の挿入点 test (fixture は `ident.ensure_resumable_attempts` を差し替えている) が引き続き Tier0 の挿入点まで届くかを静的に確かめて報告する (編集はしない)。

**編集してよい file は `orchestrator/campaign/p3_s4_loop.py` と `orchestrator/tests/test_p3_s4_loop.py` の 2 本だけ。** 本番の変更は F7 の 1 語だけ。
[T-2632] が足した他の test・fixture・本番コードには触らない。本番に「偽 checkout なら Tier0 を飛ばす」等の迂回を入れない。

制約・報告形式は `s6-fix1-prompt.md` の「制約」「報告形式」を全文適用する (docs を編集しない / テストを走らせない / 既存テストの期待値を変更しない /
揮発値を焼き込まない / 受理集合を変えない)。報告の 1 の対応表は F2 と F7 の 2 行。5 の変異は「M18 (`_PROVENANCE_OUTCOMES` から `rejected-tier0` を外す) を落とす node」を書く。
最後に `## 総括` を置く。
