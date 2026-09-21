単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/s6-adjudication.md — **段 6 裁定。本 fix は F1 だけを直す** (F3 / F4 / F5 は前 fix で済み、F2 は対象外)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1-prompt.md — 前 fix の prompt (制約と F1 の検査項目の正本。下の「差し替えの範囲」だけを本 prompt で上書きする)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1.md — 前 fix の報告 (F1 を「差し替え範囲の確認待ち」で正しく止めた)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/s4-adjudication.md — 段 4 裁定とプラン v2・変異 M1〜M17。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-review-A.md — レビュー A。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-review-B.md — レビュー B。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py — 所有 file。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py — 所有 file (編集対象)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_p3_s4_loop.py — **参照のみ (編集禁止)**。`_b5_candidate_fixture` と B-5 seam test 2 件の組み方。読めなければ即停止

この checkout は branch `dev-wave-t2797-unit-a1-fix1b`、HEAD は前 fix の commit `e588f5bfb`。

## 作業 (段 6 裁定の F1)

前 fix の prompt の F1 (検査項目 4 つ: 順序 / perf binary が gateway に届く / 拒否で rc 3・submission なし・digest なし / build 例外の境界と準備段の伝播) と
§5 の M1〜M3・M9〜M11 の再照準を、`orchestrator/tests/test_b5_tier0.py` に**通常走で skip されない test** として実装する。
編集してよい file は前 fix と同じ所有 7 file だけで、実際には `test_b5_tier0.py` だけを編集する想定。**`orchestrator/tests/test_p3_s4_loop.py` は編集しない。**
test 間の import (`test_p3_s4_loop.py` の helper を import する) もしない — 必要な準備は `test_b5_tier0.py` の中に最小限で書く。

### 差し替えの範囲 (前 fix の prompt のこの点だけを上書きする)

- **差し替えてよい (Tier0 の挿入点より手前の準備と、後段の境界):** 既存 `_b5_candidate_fixture` と同じやり方で、checkout / site 判定 / layout・exploration output root /
  condition gate / env contract / authority・coder capability の準備を fixture にしてよい。campaign の本体 (`run_campaign`) は、既存 seam test と同じく境界例外 (または
  呼出しを記録して止める stub) にしてよい。CCBench の build (`buildcache.build_v2` / `buildcache.build`) と source evidence・admission の準備 (`_b5_tier0_build_inputs`) も差し替えてよい。
- **実物を通す (検査対象):** `_run_one_iteration_resolved` の Tier0 挿入点の配線 (build 呼出しの引数 `trace=False`、例外の捕捉境界、smoke への binary の受け渡し、
  `tier0.json` → `pipeline-submitted.json` の順、拒否時の早期 return)、`_run_b5_tier0_smoke`、`orchestrator.calibrator.runner.run_once`、既存パーサ、bench lock、
  `_write_b5_sidecar`、`drive_iteration` の B-5 早期 return、CLI (`main`) の rc 3 分岐。smoke は既存の fixture executable を build の差し替えが返す binary として使う。
- build の差し替えは `trace` 引数ごとに別の fixture executable を返し (trace=True なら「呼ばれたら失敗」を記録する executable)、どちらが gateway に届いたかを観測できるようにする。

制約・報告形式は前 fix の prompt (`s6-fix1-prompt.md`) の「制約」「報告形式」をそのまま全文適用する (git commit しない / docs を編集しない / テストを走らせない /
既存テストの期待値を変更しない / 機構を stub しない / 揮発値を焼き込まない / 受理集合を変えない / 本番コードに test 専用の迂回を入れない / 本番コードの差分 0)。
報告の 1 の対応表は F1 だけでよい。最後に `## 総括` を置く。
