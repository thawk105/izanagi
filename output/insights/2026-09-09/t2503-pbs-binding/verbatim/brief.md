# 段 1 brief — [T-2503] t316 probe の runtime PBS 束縛が誤った対象を指す

## 研究前進と完了判定

t316 は「計算ノードの sandbox backend が何をどこまで封じ込めるか」を実測する staged probe である。
`_execution_binding` は、その実測 receipt に「どの commit の、どの job body で走ったか」を刻む
束縛関門であり、ここが raise すると probe は 1 stage も観測せずに終わる。現行コードでは
runtime の PBS spool の bytes を `.pbs` ではなく `.py` と比べているため、次に計算ノードで走らせると
必ず `runtime PBS bytes differ from worktree PBS bytes` で落ちる。成果物影響 = t316 の再実測
(封じ込め判定と、それに依存する測定条件の主張) が 1 件も取れない。完了判定 = 束縛が `.pbs` を指し、
誤対象を指す変異が単体テストで確実に落ちること。本 wave では計算ノードへ投入しない。

## 実測で裏取りした事実 (一次資料)

- `git show 5e12db6ce:tools/pegasus/probes/t316_sandbox_backend_probe.py` の tuple は
  index 0 = `.py`、index 1 = `.pbs`。同 commit の `repo_pbs = repo_root / _BOUND_RELATIVE_PATHS[1]` は
  `.pbs` を指していた。
- `0218acc61` が tuple 先頭へ `orchestrator/campaign/condition_meaning_gate.py` を足し、以後
  index 1 = `.py`、index 2 = `.pbs`。比較行は据え置きのため 1 つずれた。
- 意図は receipt が裏づける。`output/env/pegasus/t316-sandbox-backend/0:900383.nqsv/receipt.json` と
  `0:900427.nqsv/receipt.json` はいずれも `runtime_pbs_spool` = `44a35985…31b32` = 同 receipt の
  `tools/pegasus/probes/t316_sandbox_backend_probe.pbs` の sha256。
- job body 側 (`t316_sandbox_backend_probe.pbs:65-80`) は spool を committed `.pbs` と既に照合済みで、
  そこを通った spool は必ず `.py` と bytes が異なる。よって Python 側は「冗長で無害」ではなく確実に赤。
- 既存被覆は純増ゼロ。`orchestrator/tests/test_t316_sandbox_probe.py:1282` は `_execution_binding` を
  monkeypatch で丸ごと差し替えており、この関数の直接被覆は 0 件。`docs/decisions.md` に本束縛の裁定なし。

## scope と scope 外

- scope: `_execution_binding` の runtime PBS 比較対象を `.pbs` へ直す。同じ単位 (同 test file) に、
  誤対象を指す変異が確実に落ちる負例を置く。
- scope 外: 仮想リスク向けの gate・検査・台帳・一般化の追加。他 stage の verdict 論理。
  計算ノードへの実投入。`.pbs` 側 shell 検査の変更。

## 確定済みユーザー裁定・不変条件

- 実装面は Codex `role=author` が書く (D95)。親は実装面を直接編集しない。
- 規律 2 を緩めない。既存の関門 (login node 拒否、`PBS_NODEFILE` 照合、HEAD 一致、
  bound paths の dirty 検査、5 path の `runtime_sha256` 記録) はいずれも弱めない。
- receipt の `runtime_sha256` の key 集合 (`_BOUND_RELATIVE_PATHS` 5 件 + `runtime_pbs_spool`) と
  例外文言 `runtime PBS bytes differ from worktree PBS bytes` を変えない。
- 凍結 bytes pin は不在 (実測)。file の sha256 `d7607e0a…ce802`、blob `32644847…2ef0` とも repo 内 hit 0 件。
  `FROZEN_MANIFEST` に t316 なし。`acceptance_duration_ledger.json` は未知 node を unknown 扱い
  (順序決めのみ) なので新規 test node の追加で赤にならない。新規 test file は作らない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** 束縛は位置 index ではなく**名前**で書く。`.pbs` の相対 path を名前付き定数にし、
  tuple と比較行の両方がそれを参照する。理由 = 同型の再発 (tuple への追加でずれる) を、
  新しい gate を足さずに構造で閉じられる最小差分だから。攻撃されたら段 4 で再裁定する。
- **(P2)** 負例は「性質の主張」でなく `_execution_binding` の**実走**で置く。tmp に実 git repo を作り、
  5 つの bound path を commit し、spool の bytes を `.pbs` と一致・`.py` と不一致にする。
  正例は成功して `runtime_pbs_spool` を返し、比較対象を `.py` (旧 index 1) にした変異は赤になる。
  `socket.gethostname` は monkeypatch する (login node の実 hostname は `pegasus*` で拒否対象)。

## 変更面の実アンカー

| path | anchor | 変更 |
|---|---|---|
| `tools/pegasus/probes/t316_sandbox_backend_probe.py` | `_BOUND_RELATIVE_PATHS = (` (2290) | `.pbs` を名前付き定数へ |
| `tools/pegasus/probes/t316_sandbox_backend_probe.py` | `repo_pbs = repo_root / _BOUND_RELATIVE_PATHS[1]` (2337) | 名前付き定数を参照 |
| `orchestrator/tests/test_t316_sandbox_probe.py` | 末尾へ追加 | 正例 1 + 負例 (誤対象で赤) |

## 成果物と分割

probe の最小差分 (数行) と test の追加のみ。実装子 1 本で足りる。受入・実測環境は login node の
pytest 全走 (計算ノード不要)。
