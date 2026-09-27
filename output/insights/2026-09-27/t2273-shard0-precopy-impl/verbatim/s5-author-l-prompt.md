単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

作業木 (あなたが編集してよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl
所有 path (これ以外を編集しない): `orchestrator/tests/conftest.py`、`orchestrator/tests/test_s8b_oracle_driver.py`、`orchestrator/tests/test_real_repo_serialization.py` (後者は既存の模擬 hook fixture を直す必要な行だけ)。所有外の file に波及が必要と分かったら編集せず報告する。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s4-ruling.md — **親の段 4 裁定。「プラン v2」「変異の事前登録」が実装仕様の正本。** 所見表の扱い (環境変数を新設しない、結果 file 1 つ、発火条件は `_early_memo_selected` を共用、時点差は docstring で明記) にも従うこと。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md、s3-consult-a-out.md、s3-consult-b-out.md — 段 2 plan と段 3 相談 (参考。v2 と食い違えば v2 が優先)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/output/insights/2026-09-26/t2273-shard0-precopy-ab/verbatim/probe-source.md の `tools/t2273_replica_plugin.py` 節 — 診断で効果を示した P の形 (`pytest_configure_node` の `produce()`、`copy_from_snapshot`)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/conftest.py — 早期 memo 2360〜2500、`pytest_configure_node` 2583〜2615、`_finish_memo_sessions` 2964、`pytest_sessionfinish` 2745、`pytest_unconfigure` 3381。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/test_s8b_oracle_driver.py — 794〜1033 (列挙・複製・`_T080SharedBases`・`_t080_join_shared_bases`)、1037〜1345 (shared base test 群)、1346〜1470 (consumer AST 検査・builder、1458 が差し替え対象)、1899〜2010 (全件性検査)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/test_real_repo_serialization.py — `_early_memo_cache_probe` (6420 付近) と、shard spec 付き config で本物の `pytest_configure_node` を呼ぶ全 test (grep `pytest_configure_node`)。

## 実装すること

s4-ruling.md の「プラン v2」1〜5 をそのまま実装する。要点:
1. conftest.py: `pytest_configure_node` の `_start_early_memo_job(node)` の直後 (同じ `if _early_memo_selected(node.config):` の中) で `_start_t080_visible_output_snapshot(node)` を呼ぶ。session で 1 回だけ起動 (config 属性に job を保持)。同期部分で dir `Path(tempfile.gettempdir()) / f"izanagi-t080-visible-output-{identity}"` (identity は `test_s8b_oracle_driver._t080_join_shared_bases` と同じ式 `sha256(json.dumps([str(ROOT), run_id]).encode("utf-8")).hexdigest()`、run_id = `node.workerinput["testrunuid"]`、ROOT は conftest の位置から求める repo root) を `mkdir(exist_ok=False)`。非 daemon thread で test module を import し (`importlib.import_module("orchestrator.tests.test_s8b_oracle_driver")`)、`module.ROOT` と conftest の root の一致を確かめ、`module._copy_git_visible_output(module.ROOT, dir / "output")` を 1 回呼び、`result.json` を pending → rename で置く (成功 `{"ok": true}`、失敗 `{"ok": false, "error": repr(exc)}`)。例外は job に保持。
2. conftest.py: `_finish_memo_sessions` の終了列に `_finish_t080_visible_output_snapshot` を足す (early memo の後)。thread を join し、finally で dir を削除 (存在すれば)。保持した例外を伝播。これが worker 全終了後に走る位置であることを確かめて報告する。
3. test_s8b_oracle_driver.py: 1458 行を helper `_t080_copy_visible_output(destination)` 呼出しに替える。helper: `PYTEST_XDIST_TESTRUNUID` があり上の dir が存在すれば `result.json` を上限 180 秒 (module 定数、test で短縮可) まで 0.05 秒間隔で待ち、`ok` なら `shutil.copytree(dir / "output", destination)` (既定引数)、失敗・超過は理由付きの例外。dir が無ければ従来どおり `_copy_git_visible_output(ROOT, destination)`。docstring に「写しは configure_node 時の 1 時点で、session 中の output/ の変更は fixture に反映されない。列挙・除外・全件性の検査は実関数が実 repo に対して行う」を書く。dir の path 導出は `_t080_join_shared_bases` と同じ式で書き、式を二重に持つなら同じ値になることを T1 で確かめる。
4. test (最小、v2 §4): T1 (新規 1 本) と T2 (既存 `test_t080_shared_base_builds_real_builder_once_across_processes` に helper 呼出し回数 == builder 呼出し回数の assert 1 つ)。T1 は本物の conftest `pytest_configure_node` を呼ぶ (conftest module の取り方は既存 test の定型 (`_load_suite_conftest` 等) に揃える)。差し替えてよいのは検査対象の外側の既存 seam だけ: test module の `ROOT` (小さい git repo)、`tempfile.tempdir` (test 局所)、`_start_early_memo_job` (no-op、早期 memo は検査対象外)、`PYTEST_XDIST_TESTRUNUID`。実関数 `_copy_git_visible_output` は `mock.patch.object(..., wraps=<実物>)` で観測だけする (stub しない)。T1 は (a) helper を呼ぶ前に `result.json` が ok で現れる、(b) 実関数が 1 回・(ROOT, dir/output) で呼ばれる、(c) helper を 2 回呼び間に source を変更しても両方が変更前の直接複製と同じ集合・bytes・mtime、(d) finish で dir が消える、を検査する。T1 の置き場所 (test_s8b_oracle_driver.py か test_real_repo_serialization.py か) は、既存 fixture と consumer AST 検査・nodeid 台帳への波及が小さい方を選び理由を書く。
5. 既存の模擬 hook test: shard spec 付き config で本物の `pytest_configure_node` を呼ぶ fixture (少なくとも `_early_memo_cache_probe`) では、新しい起動関数を局所的に no-op へ差し替え、unit test が実 repo の output/ を写さないようにする。既存 test の期待値は変えない。
6. 変えないもの: `_copy_git_visible_output`・`_git_visible_output_paths` の本体、全件性の検査 2 か所とその test、`_T080SharedBases` (get / close / lock / complete.json)、`_t080_join_shared_bases`、早期 memo の挙動、既存 test の期待値。仮想リスク向けの gate・検査・一般化・互換層・環境変数を足さない。

## 規約 (DW-S05-B / DW-S05-C)

- 現行の受理・拒否挙動: builder は常に実 repo の output/ を直接複製する。本変更は受入 (acceptance shard・未絞り込み) の xdist session で複製元を configure_node 時の写しに替えるだけで、fixture に届く集合・bytes・mtime の規則を変えない。これ以外の受理集合変更をしない。
- 既存 test の期待値を変えない。xfail 化・skip・削除・緩和をしない。fixture へ現行 hash を差し込む等、test を甘くして緑にしない。期待値へ揮発 payload (tree hash、絶対 path、時刻の絶対値) を焼き込まない。
- 機構の正例は実体を名指しし、依存先を stub しない。
- 例外文を比較する場合は `str(exc) == msg` の完全一致を避け、先頭行または `match=` で比較する。
- 変異の事前登録 M1〜M7 (s4-ruling.md) を、実装後の test が**単一理由で**殺すかを静的に確認し、殺せない変異があれば理由と、どの assert を足せば殺せるかを報告する (変異そのものは実行しなくてよい。親が harness で走らせる)。
- テストの実走: この sandbox では pytest が拒否されうる。走らせられれば repo root (= 作業木) を cwd に焦点走 (`PYTHONPATH=. python3 -m pytest -q -rf -p no:cacheprovider <file>::<test>`)、走らせられなければ「実装済み・未実走」と書き、少なくとも `python3 -m py_compile` を通す。緑は実走した nodeid と範囲を併記する。子の実走は親の全走を代替しない。
- 新設 test の名前が file 集合列挙・nodeid 台帳・consumer AST 検査 (`test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5` 等)・real-repo access 登録・`acceptance_duration_ledger.json`・hold 台帳に波及しないかを自分で洗い出し、関係する meta-test を列挙する。
- 報告に、所有外 caller・共有 fixture・consumer test (本物の `pytest_configure_node` を呼ぶ全 test を含む) への波及を静的に列挙する。

## 出力形式

- `## 変更` (関数・行・要旨)
- `## 実走` (コマンド、nodeid、結果。未実走はそう書く)
- `## 変異の帰属` (M1〜M7 それぞれ: kill する node と assert、単一理由か、mask の有無)
- `## 波及` (所有外 caller・fixture・meta-test)
- `## 総括` (3〜6 行)
