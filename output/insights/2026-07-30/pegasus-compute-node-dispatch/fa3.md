## 総括

FA-8 / FA-9 / FA-12 はすべて **closed（実機再受入は親担当）** です。

- **FA-8:** `qsub` rc=0 の最初の判定直後、receipt capture 前に `active=True` としました。capture 中の SIGINT/SIGTERM 相当例外でも job name / submission dir から ID を探索し、`qdel` を試みます。[dispatch_compute.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fa/tools/pegasus/dispatch_compute.py:862)
- **FA-9:** qstat 判定語を単一定数へ集約。権限・所有権系は F47 ラッチ、一時系および未知の非ゼロは再試行後も非ラッチ、成功・request不在は従来どおりラッチします。F47 の逐語応答 `Not permitted to access` も正例にしました。[dispatch_compute.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fa/tools/pegasus/dispatch_compute.py:45)
- **FA-12:** 人工的な最終 child 注入 fixture を削除し、親 pop・dispatcher allowlist・job script の3 nodeへ分割しました。各 docstringに冗長 gateであることと、DW-M03により単独変異の受理挙動証拠から外す旨を記載しました。

実行結果:

- `orchestrator/tests/test_pegasus_dispatch_compute.py` 全範囲: **54 passed**
- `orchestrator/tests/test_run_tests_task_run.py` 全範囲: **47 passed**
- 新規焦点 node群の先行走行: **15 passed + 2 passed**
- 所有4ファイルの `py_compile`: rc=0
- `git diff --check HEAD -- <所有4ファイル>`: rc=0

FA-12 の期待赤 node:

- `orchestrator/tests/test_run_tests_task_run.py::test_m7_parent_dispatch_environment_isolated_redundant_gate`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_m7_dispatcher_request_allowlist_isolated_redundant_gate`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_m7_job_script_unset_isolated_redundant_gate`

波及可能性は `tools/run_tests.py` からのdispatcher呼出、immediate-qstat receiptのattempt recordへの `classification` 追加、F47ラッチ理由の追加です。receipt schemaや公開関数の引数は変更していません。

実 qsub、build、全suite、所有外meta-test、docs編集、commitは実施していません。