単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/s4-adjudication.md — **段 4 裁定とプラン v2 (本作業の正本)。§3「プラン v2」と §5「変異の事前登録」に従う**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/brief.md — 親 brief (不変条件)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s2-plan.md — 段 2 プラン (参考。v2 と食い違う箇所は v2 が優先。trace build 前倒し・開始印・`tier0-interrupted` は v2 で削除済み)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s3-consult-A.md — 段 3 相談 A (参考)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s3-consult-B.md — 段 3 相談 B (参考)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/verbatim/prereg-3.md — 事前登録 §3 (A / B の定義)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py — 所有 file (子の挿入点)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/b5_generator_contrast.py — 所有 file (driver)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/b5_generator_contrast_report.py — 所有 file (report)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_generator_contrast.py — 所有 file。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_generator_contrast_report.py — 所有 file。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_ccbench_spawn_sites.py — 所有 file (`_BOUNDED_RUN_ONCE_CLIENTS` に 1 行)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/pipeline.py — 参照のみ (`_prepare_evaluation_core` 内 `_build_one` の build 引数と例外境界)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/buildcache.py — 参照のみ。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/calibrator/runner.py — 参照のみ (`run_once`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/calibrator/benchparse.py — 参照のみ (既存パーサ)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/lock.py — 参照のみ (`bench_lock`)。読めなければ即停止

## 作業 (プラン v2 の実装単位 A1)

**編集してよい file は次の 7 つだけ** (うち最後の 1 つは新規作成):
`orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/b5_generator_contrast.py`、`orchestrator/campaign/b5_generator_contrast_report.py`、
`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`、
新規 `orchestrator/tests/test_b5_tier0.py`。

**着手前に次の現行挙動を読んで報告に明記する:** (a) B-5 mode の候補 slot で `pipeline-submitted.json` が書かれる位置と、その前にある投入前拒否
(`_b5_proposal_rejected` → outcome `rejected-preprocess`、`drive_iteration` の B-5 早期 return、CLI の rc 3)。(b) 投入後の build 失敗が pipeline で
`build-error` として abort され driver で `build-failed` (候補起因、B 消費) に分類される経路。(c) driver `_header` の `tier0_status="not-implemented"`。
(d) この checkout は local main `36fb14a3d` から切ってあり、`p3_s4_loop.py` を編集する予定の別 wave ([T-2632]、`drive_iteration` の `save_loop_state`
直前に provenance の side channel を足す予定) はまだ land していない。親が [T-2632] の land 後に取り込んで照合するので、**`drive_iteration` の
`save_loop_state` 周辺と provenance 系の関数には触らず、`p3_s4_loop.py` の変更は `_run_one_iteration_resolved` の挿入点・B-5 早期 return 集合・CLI の rc 3 分岐・
新規の helper / 定数に限る** (後で衝突を小さくするため)。

実装内容は s4-adjudication.md §3 の 1〜4 のとおり。要点を再掲する (食い違えば s4-adjudication.md が正本):

1. 子: `_run_one_iteration_resolved` の condition gate の後・`pipeline-submitted.json` の前に、B-5 mode の候補経路だけで Tier0 を実行する。
   module 定数 `B5_TIER0_CONTRACT` を 1 箇所に定義し (smoke flags / timeout 32 s / 通過条件 / 失敗処理 / `applies_to`)、driver はそれを import して使う。
   build は pipeline `_build_one(trace=False)` と同じ呼び方・同じ引数で 1 回 (trace build は作らない)。例外は `(RuntimeError, subprocess.SubprocessError)` だけを
   捕まえて `rejected` / `build-error` にし、それ以外は捕まえない。smoke は `runner.run_once(..., timeout_s=32, strict_returncode=True, use_perf=False)` を
   既存 `bench_lock()` の内側で 1 回、通過条件は既存パーサで commit > 0 かつ throughput 有限正。`tier0.json` を `_write_b5_sidecar` で判定後・submission 前に 1 回書く。
   不通過は submission を書かず outcome `rejected-tier0` を返し、`drive_iteration` の B-5 早期 return 集合と CLI の rc 3 分岐に足す。
2. driver: `classify_slot` の新分岐 (submission の有無と独立に `tier0.json` を読む。identity と `contract == B5_TIER0_CONTRACT` を照合)、`rejected-tier0` は A のみ・retry なし、
   submission ありで passed 証拠が無い/不正なら `unclassified-missing`、台帳 event には `tier0 = {status, reason, sidecar_sha256}` だけ (smoke の数値を載せない)、
   `_header` の `tier0_status="implemented"` と `tier0_contract`。module docstring を実態に合わせる。
3. report: 既存の共通構成比較に `tier0_status` / `tier0_contract` を加える。A / B の回収は変えない。試走 (not-implemented) 台帳の読取りは不変。
4. test: s4-adjudication.md §3 の 4 と §5 の M1〜M17 の各変異が、それぞれ**変更箇所を実際に通る**検査 1 つ以上で落ちるように書く
   (smoke helper 単体 test だけでは呼出し側の binary 取り違えを検出できない — 実挿入点を通る test を置く)。`test_ccbench_spawn_sites.py` の
   `_BOUNDED_RUN_ONCE_CLIENTS` に新しい client 1 行を足し、build sink / condition gate 先行の既存検査が新 build 呼出しを拾って通ることを静的に確かめる。
   既存期待値の変更は `test_series_scores_fresh_sessions_after_endpoint_fix` の `tier0_status` の assert と report fixture の分割だけに限る。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない** (`docs/` 配下、`output/`、`tools/pegasus/README.md` を含む)。所有 7 file 以外の file を作成・編集しない。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、`pytest.main` の埋め込み、test file の自走 harness のいずれも使わない)。
  親が計算ノードで焦点走を行う。報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile <file>`) は行ってよい。
- 追加した呼出し・定数が既存の制約 meta-test に触れないかを**自分で洗い出して静的に確認する** (親の名指しを網羅と見なさない)。少なくとも:
  `test_ccbench_spawn_sites.py` の各目録と build sink / condition gate 先行検査、`test_s8b_floor_campaign.py` の `"--build"` 字面の materializer 閉包、
  `test_p3_build_authority_cli.py`、`test_campaign.py` の certified-writer caller inventory、`test_official_perf_closure.py`、`test_campaign_lock_codec.py` /
  `campaign_lock.py` の contract loader 閉包 (新 module を作らないこと)、`test_p3_s4_loop*.py` の B-5 seam test、`test_b5_contrast_launch.py` (T-2830 所有、編集禁止)。
- 機構の正例・負例は実体を名指しし、依存先を stub しない (`run_once`・既存パーサ・`_write_b5_sidecar`・`classify_slot`・report そのものは stub しない。
  CCBench の実 build が要る検査は親の実測に回し、fixture executable で gateway / parser / timeout / lock を実物で通す)。
- テストを甘くして緑にしない (期待値の緩和、`in` 検査への置換、既存 assert の削除をしない)。期待値に揮発値 (tree hash・時刻・path 名の hash) を焼き込まない。
- 指示外の受理集合を変えない (非 B-5 経路・stock 経路・`do_build=False` の argv / identity preimage / `run_campaign` kwargs を 1 byte も変えない)。規律 2 を緩めない
  (Tier0 は pipeline の verify / anomaly reject を置換・短縮しない。smoke の値を性能値・fitness・current_perf・leading indicators に使わない)。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 着手前の現行挙動 (上記 (a)〜(d))
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と、それぞれが変更で影響を受けるか (受けるなら どう対応したか)
5. 変異 M1〜M17 と、それぞれを落とすはずの test node 名 (変更箇所を通る根拠)
6. 所有外の caller・共有 fixture・consumer test への波及の静的列挙
7. 未実走であることの明記と、親が走らせるべき nodeid / file の候補
最後に `## 総括` を置く。
