単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md` — 親の段 4 裁定。**「プラン v2 (実装子への確定指示)」が命令の正本**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/brief.md` — 段 1 brief。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s2-plan-out.md` — 段 2 plan。裁定で訂正された箇所は裁定が優先。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py` — 編集対象 1。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py` — 編集対象 2。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py` — 共通 fixture。読めなければ即停止。

## 依頼

段 4 裁定の「プラン v2 (実装子への確定指示)」をそのまま実装せよ。あなたはコードとテストだけを編集する。

## 権限境界 (違反禁止)

- **編集してよい file は 2 つだけ**である。
  - `tools/pegasus/probes/t316_sandbox_backend_probe.py`
  - `orchestrator/tests/test_t316_sandbox_probe.py`
- **触ってはいけない:** `orchestrator/tests/test_hooks.py`、`orchestrator/tests/test_official_perf_closure.py`、
  `docs/` 配下の全 file、`orchestrator/tests/acceptance_duration_ledger.json`、
  `tools/pegasus/probes/t316_sandbox_backend_probe.pbs`、`output/` 配下、
  `orchestrator/tests/test_frozen_artifacts.py`。
- **docs を編集しない。commit しない。git の状態を変えない** (`git add` / `git commit` / `git stash` /
  branch 操作をしない)。統合と commit は親が行う。
- 指示外の受理集合変更をしない。新しい gate・検査・台帳・framework・一般化・互換層を足さない。
- 既存テストを甘くして緑にしない。既存テストの期待値を変えない。意図的に赤になるテストを
  xfail 化しない。

## 実装内容

段 4 裁定の「プラン v2」の 1. と 2. を逐語で実装せよ。特に次を落とすな。

- 比較対象は名前付き定数 `_RUNTIME_PBS_RELATIVE_PATH` にする。`_BOUND_RELATIVE_PATHS` の
  **値と順序は変えない** (3 番目の要素がその定数を参照する形にする)。
- 例外文言 `runtime PBS bytes differ from worktree PBS bytes` と、
  `runtime_sha256` の key 集合 (`_BOUND_RELATIVE_PATHS` の 5 件 + `runtime_pbs_spool`) を変えない。
- test helper では、**git を 1 度でも呼ぶ前に** git 環境変数の隔離を済ませる。
  `monkeypatch.delenv(name, raising=False)` を使う。
- **すべての git subprocess に明示 timeout を付ける。** `git -C <repo>` で木を明示する。
- 5 つの bound path を互いに異なる bytes で作り、`.py` と `.pbs` の bytes が異なることを assert する。
  commit 後に `git status --porcelain --untracked-files=all` の stdout が空であることも assert する。
- runtime spool と `PBS_NODEFILE` は repo 外に置く。
  `monkeypatch.setattr(probe.socket, "gethostname", lambda: "compute-test.example")` で hostname を固定し、
  nodefile にも同じ名前を書く。
- test 名は裁定が指定した 2 つを**そのまま**使う。名前を変えるな。
- 負例は `pytest.raises(ValueError, match="^runtime PBS bytes differ from worktree PBS bytes$")` で
  受ける。例外型だけで受けてはならない (前段の関門が出す別の `ValueError` を成功と誤認するため)。
- `git` 不在で skip しない。`shutil.which("git") is not None` を assert して明示的に赤にする。

## 検査と報告の義務

- **緑と書くときは実走した nodeid と範囲を必ず併記せよ。** 実走できなかったものを `closed` と
  申告してはならない。実走不能なら「実装済み・未実走」と書け。
- テストを新設する単位では、親の名指しを網羅と見なさず、**制約 meta-test を自分で洗い出して走らせよ**。
  この repo には test 収集規約・命名規約・受入台帳・自走 harness に関する meta-test がある。
  どれが自分の追加に掛かるかを自分で探し、走らせた結果を報告せよ。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしてはならない。
  正例・負例は実体を名指しし、依存先を stub してはならない。
- 期待値へ揮発 payload (working tree の hash、実 hostname、実 job id 等) を焼き込むな。
- 完了報告に、所有外の caller・共有 fixture・consumer test への波及可能性を静的に列挙せよ。
- scope の実装前に、当該箇所の**現行の受理・拒否挙動**を 2〜3 行で明記せよ。

## 実行方法の注意

- あなたの sandbox では `tools/run_tests.py` は使えない (rc=16 になる)。
  test file の自走 harness (`python3 orchestrator/tests/test_t316_sandbox_probe.py`) を
  `PYTHONPATH=.` を付けて repo root から実行せよ。`python3 -m pytest` は guard に拒否される。
- 実走した command と rc を報告に逐語で書け。

## 出力形式

見出しは H2 (`##`) で統一し、最後に `## 総括` を置く。`## 総括` には
実装した差分の要点、実走した nodeid と rc、未実走のもの、波及可能性を各 1〜3 行で書く。
結合文字 U+0300〜U+036F を使わない。
予算が尽きそうなら、途中でもこの出力形式どおりに結論を書いて終われ。無出力が最悪である。
