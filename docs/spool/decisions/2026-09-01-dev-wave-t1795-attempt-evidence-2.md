---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t1795-attempt-evidence
seq: 2
---

## {{D:local-attempt-marker-admission}}. 計算ノードと task 内 marker の二重条件でだけ local の attempt 記録を許す

**決定 (D965 の独立 wave):** 変異 harness の attempt sidecar は、これまで `--runner-mode dispatch`
でのみ使えた。束ね経路 (dispatch の `--task mutation`) は job の内側が local 実行になるため、
attempt 証拠を残せなかった。次の**二重条件が同時に真のときだけ** `--runner-mode local` での
attempt sidecar を受理する。

- 条件 A: 現在地が Pegasus 計算ノードである (`site_policy.current_site(require_evidence=True)` が
  `PEGASUS_COMPUTE`)。
- 条件 B: task の内部でだけ立つ marker が存在し、現在の job と整合している。

marker は `orchestrator/campaign/mutation_attempt_marker.py` が定義し、計算ノード上の
`tools/pegasus/dispatch_compute.py` の `_job_run` が、request SHA-256 検査・bound envelope 検査・
argv policy 検査・environment allowlist 検査・compute hostname 検査を**すべて通した後**に、
`task == "mutation"` のときだけ子環境へ明示代入する。marker key は task の env allowlist にも
clean 環境の既定 key 集合にも入れないため、親からは構造的に届かない。request の `environment` へ
入れた場合は allowlist 違反として child 起動前に拒否される。

wrapper (`tools/mutation_worktree.py`) と harness (`tools/mutation_harness.py`) は、
`attempt_out is not None and runner_mode == "local"` の一点でだけ**同一 validator の同一呼び出し**を
行う。dispatch mode と、attempt を伴わない local では validator を呼ばない。

**永続証拠の形。** local + marker 走行の attempt sidecar は root へ `local_authorization` を持ち、
validator が実際に検証した object (marker schema・dispatch root・submission dir・PBS job ID・
hostname・request SHA-256) をそのまま記録する。値は検証した object から取り、再構成しない。
sidecar の `schema` は `izanagi-dev-wave-mutation-attempts-local/v1` を名乗る。
**invocation ごとの `request` は `None` のままにする** — この field は「invocation 1 本 =
scheduler request 1 本」という既存の意味を持ち、外側 job 1 本を全 entry へ重複記入すると
その意味が壊れるからである。

**変えないもの。** 束ね経路の受理集合 (`_validate_task_argv` の `mutation-worktree-v1`)、
job script、dispatch mode の受理集合と sidecar bytes、marker を伴わない local の受理集合は
1 bit も変えない。fan-out 経路 (`tools/mutation_fanout.py` と `tools/mutation_fanout_contract.py`) も
無編集である。その結果、local sidecar は fan-out 契約の exact root key 検査に**必ず落ちる**。
これは欠陥ではなく意図した性質で、local の証拠を dispatch 側の水準と取り違える経路が
構造的に閉じる。

**この機構が保証しないこと (主張せず明記する)。**

- 条件 A は、正規の marker がある限り条件 B に含意される。正規 marker は計算ノード上でしか
  鋳造されないからである。したがって A を**独立した第 2 の権威証拠と呼ばない**。A が独立に
  発火するのは、marker が偽造または持ち出されて非計算ノードで使われた場合だけである。
- submission dir が dispatch root の内側であることの判定は、`dispatch_root` も binding 由来で
  あるため、**binding 内部の整合と canonical 性だけ**を保証する。偽造者に対する権威ではない。
- 同一 UID が計算ノード上で自己整合する偽の submission dir を作れば通る。閉じるには marker の
  外側にある信頼根 (scheduler または kernel が保証する job membership) が要り、新機構の追加になる。
  これは D387 が既に認めている限界と同型である。**本機構が実際に閉じるのは、束ね経路の外で
  local + attempt を使い、attempt 対応に見える証拠を偶発的に作ってしまう経路**である。
- 子は現 PBS job ID を独立に読めない (clean 環境の既定 key 集合に `PBS_JOBID` は無い)。
  したがって陳腐化した binding の実行時検出は構造的にできない。代わりに `local_authorization` を
  永続化して**事後監査を可能にする**ことで置き換えた。
- `local_authorization` を読む消費層は本 wave では作っていない。この証拠は現時点では
  監査者が読む形で残る。
- 本変更は束ね経路と direct harness の**2 つの entrypoint を同じ条件で開く**。
  direct harness は共有 wrapper lock を通らない。

**却下した選択肢:**

- 束ね経路そのものの改修として証拠を足す — D965 が却下済み。受理集合の変更を運搬の改良へ
  紛れ込ませる形になる。
- 外側 job の scheduler request を invocation ごとの `request` へ重複記入する — 既存 field の
  意味を壊し、証拠の水準を偽る。
- marker を job script から `export` する — script bytes と export 内容はログインノード側で
  生成され、request hash・task・argv・environment を検証する前である。親が書いた bytes が
  admission token になってしまう。
- local 走行の sidecar が dispatch と同じ schema 識別子を名乗る — 形の違う文書が同じ識別子を
  名乗ると、識別子だけを見る consumer に対して証拠の水準を偽る。
- scheduler / kernel の job membership を信頼根にする、job liveness を検査する — 新機構の追加で
  あり、本 wave の scope 外。裁定へ返す。
