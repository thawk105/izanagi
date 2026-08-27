pytest は実走していない。以下は静的検査のみで、Web は使用していない。

## RB1 — M7 は既存検査に先取りされる

- 所見 ID: RB1
- 一次資料: [tools/codex_reasoning_ab.py:11207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11207)、[tools/codex_reasoning_ab.py:9266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9266)、[tools/codex_reasoning_ab.py:9327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9327)、[test_codex_reasoning_ab.py:13625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13625)
- 主張: M7 の対象行 `task_manifest=task_manifest` は実在し、`TASK_MANIFEST` への変異で対象 node が赤になること自体は確実である。しかし loader は新しい per-task 述語へ到達する前に、artifact digest 不一致と既存 union validator で外部 alpha/beta finding を拒否する。従って M7 は「外部 manifest が新しい task-specific 分岐へ渡った」ことへの単一理由帰属になっていない。
- **成果物影響:** 変異時は既存理由だけで `valid=false`、`experiment_complete=false`、主要台帳と `decision=null` になるため誤受理はないが、証拠台帳の M7 参照が新分岐の配線証明を過大主張する。
- 修正案: 実 `_load_adjudication` へ委譲する spy wrapper で、渡された `task_manifest` の digest または object identity を呼び出し境界で直接検査する。実 loader はそのまま通し、既存 digest reason を M7 の kill 根拠に数えない。

## RB2 — M8 は診断文字列だけの kill

- 所見 ID: RB2
- 一次資料: [tools/codex_reasoning_ab.py:9371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9371)、[tools/codex_reasoning_ab.py:9394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9394)、[tools/codex_reasoning_ab.py:9932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9932)、[test_codex_reasoning_ab.py:13713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13713)
- 主張: `stage="malformed-stage"` は `_slot_dimension_map` が先に `s01: schedule stage does not match benchmark task manifest` を `reasons` へ追加する。その後の packet-scoped reason を削って `continue` を残す変異でも slot は joined されず、成果物は既存 reason で無効なままなので、現テストの赤は exact reason 文字列だけによる。
- **成果物影響:** `valid=false`、`experiment_complete=false`、主要台帳と `decision=null` は変わらず、`failure_reasons` から packet-scoped 参照だけが消えて slot-scoped reason は残る。
- 修正案: M8 を acceptance mutation から外し、診断/reference-only と明記する。実効 fail-closed は `_slot_dimension_map` の reason と aggregate の missing `oracle_kind` 検査へ帰属させる。

## 成立を確認した点

- alpha/beta の `known_finding_ids` は実際に `alpha-finding` と `beta-finding` で異なる。負例は union 内かつ beta 集合外の `alpha-finding` を明示検査している。[test_codex_reasoning_ab.py:6109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:6109)、[test_codex_reasoning_ab.py:13669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13669)
- 正例の raw verdict は `findings=[]` でも `equivalent_to=None` でもなく、実 `make_packets`、`_validate_schedule`、`_replay_manifest`、`_load_adjudication` を通る。[test_codex_reasoning_ab.py:13402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13402)
- schedule は alpha 2 slot、beta 2 slotで、各 block は連続する同一 dimension の2行、かつ `(arm, requested_model)` が異なる。descriptor は packet source にあり、scheduleless 経路を使っていない。[test_codex_reasoning_ab.py:13233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13233)、[test_codex_reasoning_ab.py:13370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13370)
- R7 の aggregate cross-task 負例はこの wave で新設され、既存版には同等の負例がなかった。[test_codex_reasoning_ab.py:12187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:12187)
- `_full_manifest`、`_aggregate_rows`、`_verdict_packet_swap_restore_fixture`、`_bound_cost_aggregate` と全 `_aggregate_verified` 直接 caller に、静的検索上の追随漏れは見つからなかった。

## 総括

must-fix: **RB1、RB2**

- M1: **帰属成立** — union 内、beta 外の parent finding は既存 union 検査を通り、per-task 引数削除で対象 reason だけが消える。
- M2: **帰属成立** — second-reader 方向が独立に parametrized され、parent 限定変異を検出する。
- M3: **帰属成立** — 対象行は hash 計算前に実在し、削除すると独立構築された judgment hash と不一致になる。
- M4: **帰属成立** — default 追加変異では `missing` だけが赤、`wrong` は引き続き mismatch となり緑の構造である。
- M5: **帰属成立** — exact 比較削除で `wrong` と `missing` の両方から唯一の rejection reason が消える。
- M6: **帰属成立** — 新設された直接 aggregate 負例だけが、既存 task-specific equivalent gate の削除を検出する。
- M7: **不成立** — 変異 node は赤になるが、既存 digest・union 検査が新しい per-task 分岐より先に拒否する。
- M8: **不成立** — 既存 dimension reason が先に成果物を無効化し、追加 reason 削除の赤は診断文字列だけである。
- M9: **帰属成立** — 正例は両 task の非空 finding を実 loader の per-task ループへ通し、集合を `set()` にすると赤になる。