# 親の実走 (dogfood) で確定した must-fix

段 6 のレビュー所見と**同格の must-fix** である。すべて親が実機で実測した (静的推測ではない)。

証拠: request `874266` (gen_S、bnode016、11:55:25 投入 → 11:55:33 開始 → 11:55:36 終了)。
receipt = `output/pegasus-dispatch/e71d222d552dfb6d5555b1b6df9556ab/receipt.json`

## D1 [blocking] 終了済み request で状態機械が END を認識できず 35 分空回りする

**実測**: `qstat -f 874266.nqsv` は終了後、
`Batch Request: 874266.nqsv does not exist on nqsv.` を **rc=0** で返す。

`tools/pegasus/dispatch_compute.py` の待機ループは
`current.returncode != 0` か `state == "END"` でしか break しない。
上記出力は `_STATE_RE` にも `_CURRENT_STATE_RE` にも当たらないので `state is None` となり、
`run_seen` は既に True なので queue-wait timeout も効かない。結果、
`total_deadline = started + walltime_s(1800) + overall_grace_s(300)` まで
**約 35 分ポーリングし続け、最後に `overall-timeout` で rc=16 を返す**。

子は `result.json` で `child_rc=0` / 15 passed を既に返しており、
`.o` / `.e` も会計サマリ付きで着地している。**成功した実行が infra 失敗として報告される。**

**成果物影響**: 受入全走が毎回 35 分ハングし rc=16 になるため、
`tools/run_tests.py` の rc=0 を受入判定に使えなくなる (= 本 wave の受入自体が不能)。

**修正方向**: scheduler が request を知らない状態 (`does not exist` / `ENOREQ` 相当) を
**終端として扱う**。rc=0 でも request 不在なら END とみなす。判定は stdout の literal 依存を
最小にし、`qstat` の rc と「request ID が出力に現れないこと」の両方で終端を導く。
偽終端 (投入直後にまだ見えない) と区別するため、**immediate qstat で可視だった事実**を前提条件にする。

## D2 [must-fix] `Staging` / 終了遷移中の状態が未対応

**実測**: 投入直後の `qstat -f` は `Current State = Staging` / `Previous State = Queued` を返す
(receipt の `immediate_qstat` に逐語)。`_scheduler_state()` の map は
running / pre-running / run / queued / queue / waiting / wait / held / hold / holding /
completed / complete / finished / ended / exited / exit / terminated だけで、
**`Staging` が入っていない**。`STG` は `qstat -Q` のカウンタにも実在する状態である。

**成果物影響**: state_history に `UNKNOWN` が並び、queue 待ちの帰属が不正確になる。
`Staging` が長引く request では queue-wait timeout の起点判定が誤る。

**修正方向**: `Staging` / `staging` / `STG` を **queue 側 (未実行)** として map する。
`Exiting` / `Post-running` / `EXT` を終端側として map する。
未知状態は `UNKNOWN` のまま残し、**未知状態が続いても総時間上限で必ず抜ける**ことを保つ。

## D3 [must-fix] `site_policy.py` が Python 3.9 で import 不能

**実測**: `orchestrator/campaign/site_policy.py` は `str | None` (PEP 604) を関数注釈で使うが
`from __future__ import annotations` を持たない。**計算ノードの素の `python3` は 3.9.13** である
(runbook §4、F46)。3.9 では import 時に `TypeError: unsupported operand type(s) for |` になる。

他の変更ファイル (`dispatch_compute.py` / `run_tests.py` / `guard_bash.py` / `buildcache.py`) は
すべて `from __future__ import annotations` を持つ。**`site_policy.py` だけが例外**である。

**成果物影響**: 計算ノードで `qlogin` して素の `python3 tools/run_tests.py` を打つと、
テストが 1 件も走らないまま import エラーで死ぬ。`guard_bash` は import 失敗時 fallback へ倒れるため
site 判定の精度が落ちる。F46 (ログインノードの前提を計算ノードへ誤適用) の同型再発である。

**修正方向**: `site_policy.py` に `from __future__ import annotations` を足す。
併せて **3.9 で import できることを機械検査する**テストを置く
(例: `ast` で全新規/変更 module の PEP 604 注釈と future import の有無を照合する、
あるいは `python3.9` が在る環境でだけ走る条件付き検査ではなく、静的に future import を要求する)。

## D4 [should-fix] 親の stdout が block-buffered で進捗が見えない

**実測**: `python3 tools/run_tests.py ... > log` でリダイレクトすると、
dispatch 中の進捗が 1 行も log に現れない (親が生きている間 size 0)。
`print(..., flush=True)` になっていない、または進捗出力自体が無い。

**成果物影響**: 成果物の値は変わらない。ただし数分の待機中に「何が起きているか」が分からず、
ハング (D1) と正常待機の区別ができない。CLAUDE.md「長時間待機中は約 1 分ごとに報告」の運用が困難。

**修正方向**: 投入・request ID・状態遷移・収集の各節目を `flush=True` で 1 行ずつ出す。
