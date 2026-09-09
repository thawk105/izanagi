単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/brief.md` — 親の段 1 brief。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py` — 修正対象。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.pbs` — job body。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py` — 負例を置く単位。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py` — test の共通 fixture と収集規約。読めなければ即停止。

## 依頼

上記 brief の scope を実装するための plan を、**file:line 粒度**で起草せよ。あなたは plan だけを書く。
コードを編集してはならず、commit してはならない。

## 前提 (逐語・変更不可)

- 修正の本体は `_execution_binding` の 1 箇所である。`repo_pbs = repo_root / _BOUND_RELATIVE_PATHS[1]` が
  `.py` を指している。意図した対象は `tools/pegasus/probes/t316_sandbox_backend_probe.pbs` である。
- 既存の関門を 1 つも弱めない。receipt の `runtime_sha256` の key 集合と例外文言を変えない。
- 仮想リスク向けの gate・検査・台帳・framework・一般化・互換層を足さない。本題の実装だけ。
- 新規 test file を作らない。負例は `orchestrator/tests/test_t316_sandbox_probe.py` に置く。
- あなたは書込可能な tmp を持たない read-only sandbox で走る。**pytest を実走しなくてよい**。
  静的検査 (既存 fixture の読解、import 可能性、collect される命名規約の確認) で足りる。
  テストの実測は親が行う。あなたが実走していないものを「緑」と書いてはならない。

## 答えるべき点

1. **修正案 (file:line)**: `_BOUND_RELATIVE_PATHS` と比較行をどう書き換えるか。brief の (P1)
   「位置 index ではなく名前付き定数で束縛する」を採るか、index 2 への単純訂正に留めるか。
   どちらが良いかを理由つきで 1 つ選び、退けた方の弱点を書け。
2. **負例の設計 (file:line)**: 「比較対象を `.py` に戻す変異」が確実に赤になる test を設計せよ。
   `_execution_binding` は `PBS_JOBID`・`IZANAGI_T316_EXPECTED_COMMIT`・
   `IZANAGI_T316_EXPECTED_WORKTREE_ROOT`・`PBS_NODEFILE`・`IZANAGI_T316_RUNTIME_PBS` の環境変数と、
   実在する git repo (HEAD 一致・bound path が clean) と、`pegasus[0-9]+` でない hostname を要求する。
   これらを test 内でどう用意するか、具体的な API と行で書け。`_JOB_ID_RE` の実際の正規表現を読んで
   合致する値を決めよ。**fixture の repo で `.py` と `.pbs` の bytes が必ず異なるようにすること**
   (これが負例の検出力の本体である)。既存 test に流用できる fixture / helper があるならそれを使え。
3. **正例**: 修正後に成功し、返り値の `runtime_sha256["runtime_pbs_spool"]` が `.pbs` の sha256 と
   一致することを確かめる test。
4. **既存 test への影響**: `orchestrator/tests/test_t316_sandbox_probe.py:1282` の
   monkeypatch 差し替えを含め、既存 test が壊れないことを静的に確認せよ。
5. **副作用の棚卸し**: この変更で bytes が変わる repo 内の他の成果物・pin・台帳があれば列挙せよ。
   無ければ「無し」と根拠つきで書け。
6. **リスクと落とし穴**: この plan が失敗しうる点を挙げよ。特に「login node で走る test が
   実 hostname や実 repo に依存して落ちる」型を検査せよ。

## 出力形式

見出しは H2 (`##`) で統一し、最後に `## 総括` を置く。`## 総括` には採用案・負例の要点・
未解決の疑問を各 1〜3 行で書く。結合文字 U+0300〜U+036F を使わない。
予算が尽きそうなら、途中でもこの出力形式どおりに結論を書いて終われ。無出力が最悪である。
