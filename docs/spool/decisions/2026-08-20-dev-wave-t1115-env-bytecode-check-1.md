---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1115-env-bytecode-check
seq: 1
---

## {{D:subprocess-bytecode-guard-scope}}. env= 起動の bytecode guard 欠如は検出 checker で閉じ、既存の env allowlist 修正とは独立させる

**決定:** `tools/check_subprocess_bytecode_guard.py` を新設し、`orchestrator/`・`tools/`
配下で `subprocess.{run,Popen,call,check_call,check_output}` を直接呼び出し `env=` を
明示指定する箇所のうち、checkout 内 Python/pytest 起動を `PYTHONDONTWRITEBYTECODE`
抑止なしで行っている既存箇所を静的検出する。F296 が示した恒久対応の方向
(producer の env allowlist へ抑止変数を足す) そのものは実装せず、対応していない箇所を
機械的に見つける検出レイヤーとして独立させる。

AST 判定は次の2段の shallow heuristic に限定する。

- **P1 (python/pytest 起動判定):** `Call.args[0]` (list/tuple) の argv[0] が
  `sys.executable`・`"python"`/`"python3"` literal・`.py` 終端 literal のいずれかの
  ときだけ python 起動と判定する。argv[0] がこれに該当しなければ、他要素に `.py` や
  `"pytest"` を含んでいても python 起動とみなさない (git 呼び出し等の誤検出を排除)。
- **P2 (env= guard 判定):** dict literal/`dict(...)` の直接キー、argv 中の `"-B"`、
  enclosing 関数内の文字列 literal、**同一ファイル内 1-hop 関数解決** (`x = f()` の形の
  代入だけを1段だけ辿る) のいずれかを guard とみなす。import 越し・2-hop 以上の解決・
  tuple-unpack 代入 (`a, b = f()`) は追跡しない。

**理由:**
- command 引数の依頼は「機械的に検出する検査を新設する」であり、恒久対応 (producer 修正)
  そのものの実装ではない。検出レイヤーとして独立させることで、対象の広さ (実測240箇所の
  直接 subprocess 呼び出し) に対して各箇所の意味を個別判断せず機械的に洗い出せる。
- P1/P2 とも段3 敵対相談2レンズが独立に検算し、argv[0] 起点化と `-B` 認定を real 所見として
  一致させた。shallow 判定である以上、動的 argv・`shell=True` 文字列 argv・
  `os.system`/`os.popen`/`multiprocessing`・pytest-xdist worker 内部起動は検出できない。
  これらは checker の module docstring に明記し、将来の scope 拡張候補として実装しない
  (規律5、盛らない)。

**却下した選択肢:**
- **F296 の producer 側 env allowlist を直接修正する** — 依頼の scope (検出の新設) を
  超える。個々の producer の意味を precise に判断する必要があり、機械的な一括対応にならない。
- **P1 を「argv のどこかに `.py`/`"pytest"` があれば python 起動」とする** (段2プランの初期案) —
  git 等の非 python 呼び出しに含まれる `.py` パス引数を誤検出する (実測: `test_dev_wave_wait.py`
  の `git add tools/foo.py` 型呼び出し)。段3 レンズ1・2 が独立に real 所見として指摘した。
- **P2 に import 越し・多段関数解決の完全な data-flow 解析を持たせる** — 汎用 call-graph
  解析が必要になり規律5に反する。1-hop・同一ファイル限定で打ち切り、限界を docstring と
  worklog ({{F:checker-shallow-tuple-unpack}}) に明記するに留めた。
