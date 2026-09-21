単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/s6-adjudication.md — **段 6 裁定 (本 fix の正本)。F1 / F3 / F4 / F5 を直す。F2 は本 fix の対象外**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/s4-adjudication.md — 段 4 裁定とプラン v2・変異 M1〜M17 (実装の正本)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-review-A.md — レビュー A (所見の根拠)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-review-B.md — レビュー B (所見の根拠と削除表)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s5-author-A1.md — 前段 author の報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/focus-f1.log — 焦点走 f1 の出力 (赤 3 件の本文)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py — 所有 file。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py — 所有 file (主な編集対象)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_p3_s4_loop.py — **参照のみ (編集禁止)**。既存 B-5 seam test の fixture `_b5_candidate_fixture` と
  `test_machine_no_authority_guard_and_sidecar_before_campaign` / `test_b5_duplicate_skip_returns_failure_without_restore` の組み方を読み、通常走で動く挿入点 test の組み方の参考にする。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_plain_runner_coverage.py — 自走入口の要件。読めなければ即停止

この checkout は branch `dev-wave-t2797-unit-a1-fix1` で、HEAD は統合 commit `b5935b88e` (前段 author の成果を統合済み)。

## 作業 (段 6 裁定の F1 / F3 / F4 / F5)

**編集してよい file は次の 7 つだけ:** `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/b5_generator_contrast.py`、`orchestrator/campaign/b5_generator_contrast_report.py`、
`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`、`orchestrator/tests/test_b5_tier0.py`。
**`orchestrator/tests/test_p3_s4_loop.py` は編集しない** (別 wave の所有予定。F2 は親が後で別の fix に回す)。

1. **F1:** `test_b5_tier0.py` に、`IZANAGI_B5_TIER0_TEST_RECEIPT` 無しで (skip されずに) 走る挿入点 test を足す。差し替えてよいのは CCBench の build
   (`buildcache.build_v2` / `buildcache.build`) と、source evidence・admission の準備 (`_b5_tier0_build_inputs`) だけ。Tier0 の配線 (`_run_one_iteration_resolved` の挿入点)・
   `_run_b5_tier0_smoke`・`run_once`・既存パーサ・`_write_b5_sidecar`・`drive_iteration` の B-5 早期 return・CLI の rc 3 分岐は実物を通す
   (smoke は既存の fixture executable を build の差し替えが返す binary として使う)。少なくとも次を検査する:
   - 順序: build → smoke → `tier0.json` → `pipeline-submitted.json` → campaign 境界。拒否時は `pipeline-submitted.json` も campaign 境界も無い。
   - build は `trace=False` で 1 回だけ呼ばれ、その戻り値の binary が smoke (gateway) に届く (trace build の binary を渡す変異が落ちる形。例: 差し替えが trace ごとに別の executable を返す)。
   - 拒否 (smoke の rc 非 0 など) で outcome `rejected-tier0`、CLI では rc 3、digest を作らない。
   - build が `RuntimeError` / `subprocess.SubprocessError` を投げたら `build-error` の `tier0.json` と rc 3 (正例)。`OSError` 等それ以外は伝播し、`tier0.json` も submission も書かれない。
     `_b5_tier0_build_inputs` の例外も伝播する。
   既存の `test_live_*` は親の生死確認用として残してよい (変更不要)。
2. **F3:** `test_b5_tier0.py` の末尾に、隣接 test (`test_b5_generator_contrast.py` など) と同じ形の `if __name__ == "__main__":` pytest 自走入口を足す。
   subprocess で python を起動する test があれば `env` の dict literal に `"PYTHONDONTWRITEBYTECODE": "1"` を入れる。
3. **F4:** `p3_s4_loop.py` の Tier0 前の `execution_guard.require_certified_writer_authorization(...)` 追加呼出しを削除する (後続 pipeline の既存認可は触らない)。
4. **F5:** `_b5_tier0_build_inputs` から ReviewReceipt の import・分岐を削る (GeneratorReceipt / None / 不正型の拒否は残す)。
5. s4-adjudication.md §5 の M1〜M3・M9〜M11 の kill 先を、上の通常走 test に再照準する (報告に node 名と、変更箇所を通る根拠を書く)。

## 制約 (段 5 の実装子契約を全文継承、すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない** (`docs/`、`output/`、`tools/pegasus/README.md` を含む)。所有 7 file 以外の file を作成・編集しない。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除・`xfail` 化をしない。既存 test が赤なら実装側が誤りとする。期待値が誤りだと考えるなら、実装を変えずに報告して止める。
  (前段 author が今回足した test も「既存」に含める。削除候補として挙げるのはよいが、本 fix では消さない。)
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、`pytest.main` の埋め込み、test file の自走 harness のいずれも使わない)。親が計算ノードで焦点走を行う。
  報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile <file>`、`git diff --check`) は行ってよい。
- 追加・変更が既存の制約 meta-test に触れないかを自分で洗い出して静的に確認する (親の名指しを網羅と見なさない)。少なくとも `test_ccbench_spawn_sites.py` の各目録と
  build sink / condition gate 先行検査、`test_s8b_floor_campaign.py` の `"--build"` 字面の materializer 閉包、`test_plain_runner_coverage.py`、
  `test_check_subprocess_bytecode_guard.py`、`test_campaign.py` の certified-writer caller inventory、`test_official_perf_closure.py`。
- 機構の正例・負例は実体を名指しし、依存先を stub しない (上の F1 で許した 2 つの差し替え以外は実物)。期待値に揮発値 (tree hash・時刻・path 名の hash) を焼き込まない。
- 指示外の受理集合を変えない (非 B-5 経路・stock 経路・`do_build=False` の argv / identity preimage / `run_campaign` kwargs を 1 byte も変えない)。規律 2 を緩めない。
- 本番コードに test 専用の迂回 (偽 checkout なら Tier0 を飛ばす等) を入れない。
- 規模: 本番コードの差分は F4 / F5 の削除だけ (増やさない)。test の追加は F1 / F3 に要る分だけ。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 所見ごとの対応表 (F1 / F3 / F4 / F5 × closed / partial / 未着手、根拠の file:line)
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と影響
5. M1〜M3・M9〜M11 の新しい kill 先 node 名と、変更箇所を通る根拠 (その他の M は変更なしと明記)
6. 未実走であることの明記と、親が走らせるべき nodeid / file の候補
最後に `## 総括` を置く。
