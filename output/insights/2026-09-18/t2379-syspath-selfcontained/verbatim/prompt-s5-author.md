単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2379-impl

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2379-syspath-selfcontained/s4-adjudication.md — 親の段 4 裁定 (実装方向 plan v2 の逐語、変異事前登録)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2379-syspath-selfcontained/s1-brief.md — 親の段 1 brief (scope・不変条件・変更面アンカー表)。読めなければ即停止。

「読めなければ即停止」は上の 2 file に限る。

## 依頼 (実装単位は 1 つ、所有 file は 2 つ)

作業 worktree は parent= の絶対 path (branch `impl-dev-wave-t2379-syspath-selfcontained`、base commit 302b94796062cc51c5817fba662c7bb4928adec1)。
s4-adjudication.md の「実装方向 (plan v2)」1 と 2 を**逐語どおり**に実装せよ。

1. `orchestrator/tests/test_s8b_approved.py` 31 行目: `from tests.skiputil import Skip, skip  # noqa: E402` を
   `from orchestrator.tests.skiputil import Skip, skip  # noqa: E402` に置換する。
2. `orchestrator/tests/test_profiler_directive.py` 341 行目 (関数 `test_derived_directive_is_accepted_by_the_role_policy_check` の本体先頭、4 space indent):
   `    from codex_roles import policy  # noqa: PLC0415` を `    from orchestrator.codex_roles import policy  # noqa: PLC0415` に置換する。

背景: 両 file は先頭で repo root を `sys.path.insert(0, ...)` している。`tests.skiputil` と `codex_roles` は `orchestrator/` が sys.path に
載っているときだけ解決し、それは他の test module (`test_campaign.py` 等) の import 副作用である。対象 2 file だけを選択した走では
`ModuleNotFoundError: No module named 'tests'` (収集時) と `No module named 'codex_roles'` (実行時) になることを親が計算ノードで実測済み
(request 5501.nqsv)。`orchestrator/` と `orchestrator/tests/` は `__init__.py` の無い namespace package なので、repo root が sys.path に
あれば `orchestrator.tests.skiputil` / `orchestrator.codex_roles` は解決する (先例: `orchestrator/tests/test_s8b_protocol_builder.py`、
`orchestrator/tests/test_codex_agents.py`)。

受理・拒否の含意: 変えるのは import の解決経路だけ。検査の意味 (policy の関数、Skip/skip) は同一で、受理集合は変わらない。
通る正例 = 対象 2 file だけの選択走が緑 (親が実測する)。

## 禁止 (どれも例外なし)

- `git add` / `git commit` / `git stash` / branch 操作を一度も実行しない。commit は親が行う。
- docs を編集しない (`docs/**`、README、CLAUDE.md、AGENTS.md を含む)。
- 上の 2 file 以外を編集・作成しない。`orchestrator/tests/conftest.py`、`orchestrator/tests/skiputil.py`、`orchestrator/codex_roles/**`、
  `orchestrator/campaign/**`、`pytest.ini`、`tools/**` を変えない。
- 2 file の中でも、指定の 1 行以外 (docstring・他の import・`sys.path.insert` 行・test 本体・末尾の自走 harness) を変えない。
  `sys.path` への挿入を増やさない。`__init__.py` を作らない。
- 新しい gate・検査・helper・互換層を足さない。xfail / skip を付けない。既存 test の期待値を変えない。
- `tools/run_tests.py` や pytest を起動しない (sandbox では計算ノードへ dispatch できず rc=16 になる)。走らせていない結果を緑と書かない。

## 検査 (pytest なしで行う)

- 変更後、worktree 直下で `python3 -B -c` を使い、`sys.path` に repo root だけ (`orchestrator/` は入れない) を置いた fresh process で
  `importlib.import_module("orchestrator.tests.test_s8b_approved")` と `importlib.import_module("orchestrator.tests.test_profiler_directive")`
  が例外なく戻ることを確かめ、出力を報告に写す (IMPORT_PASS)。
- 同じ fresh process 条件で `orchestrator.tests.test_profiler_directive` を import し、
  `test_derived_directive_is_accepted_by_the_role_policy_check()` を直接呼んで例外なく戻ることを確かめる (DIRECT_CALL_PASS)。
- 反実仮想 (file は変更しない): 上と同じ fresh process 条件で、変更前の import 文 `from tests.skiputil import Skip, skip` と
  `from codex_roles import policy` をそれぞれ単独で exec し、`ModuleNotFoundError` になることを確かめる (DID_RAISE)。
  これは報告用の観測であり、コードに残さない。
- 変異 anchor の一意性: 変更後の各 file で `from orchestrator.tests.skiputil import Skip, skip  # noqa: E402` と
  `    from orchestrator.codex_roles import policy  # noqa: PLC0415` の各行がちょうど 1 回出現することを `grep -c` で数えて報告する。
- `git diff --stat` と `git status --porcelain` の出力を報告に写す (読取りは可)。所有 2 file 以外に差分が無いこと。差分は各 file 1 行の置換
  (+1/-1) であること。

## 完了報告 (最終メッセージ本文に全文。file には書かない)

見出しはすべて `##` (H2)。節: `## 変更面` (file ごとの逐語 diff) / `## 検査` (上の項目の実測値、未実走の項目は「実装済み・未実走」と書く) /
`## 波及の静的列挙` (所有外の caller・共有 fixture・consumer test への影響を静的に列挙。`grep -rn "from tests\.skiputil\|from codex_roles import" orchestrator tools` の結果を添える) / `## 総括`。
最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。NFC で書き、U+0300〜U+036F を使わない。
