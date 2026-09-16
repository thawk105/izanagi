# 段 6 裁定 追補 3 — F2 の残件 2 件 (fixture 衝突・所有外 caller)

**正本の関係:** `stage6-ruling.md`・追補 1・2 に続く。衝突したら本書が優先する。

## 発生

fix 単位 F2 は B2 を直し M9 の node を新設したが、次の 2 件を残件として正しく報告した。

### E3-1 — `_submit_fixture()` の staging と symlink 負例の衝突 (本 wave 起因)

`orchestrator/tests/test_t126_pegasus_tools.py:4025`
`test_submit_rejects_symlink_component_hidden_drift_and_skip_worktree` は、`output/env` を
repo 外への **symlink** にして submit が rc=2 で拒否することを検査する負例である。
本 wave (単位 B / C) が `_submit_fixture()` を「checkout の staging
`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/{gflags,glog}` に依存 source を作る」形へ
変えたため、`output/env` が**実 directory として先に存在**し、`symlink_to` が `FileExistsError` になる。
**単独でも rc=1。回帰。**

### E3-2 — `prepare_toolchain()` の所有外 caller (本 wave 起因)

F2 が `prepare_toolchain(policy, *, repo_root)` と必須 keyword を足した。
`tools/pegasus/probes/t293_perf_site_probe.py:783` は `prepare_toolchain(policy)` と呼んでおり、
そのままでは `TypeError`。

## 決定

### (1) E3-1 — 負例の意図を保ったまま fixture と両立させる

- **検査の強さを変えない。** 「`output/env` の path 成分が symlink なら submit は rc=2 で拒否する」
  という負例はそのまま残す。
- fixture が作った staging を `outside` (repo 外の実 directory) へ移してから
  `output/env` → `outside` の symlink を張る、のように、**symlink 成分が実際に path に入る形**で
  staging を到達可能にする。symlink を別の path へ逃がして拒否を成立させない形は禁止
  (検査対象の成分が変わる)。
- `_submit_fixture()` 自体の変更が最小なら、そちらでもよい。ただし他の node の受理・拒否を変えない。
- 変更後、同 file の全走で **赤 0** を確かめる。

### (2) E3-2 — probe の呼出しを追従させる

- `tools/pegasus/probes/t293_perf_site_probe.py:783` に `repo_root=` を渡す。
  probe が既に持つ repo root (probe 内で解決している checkout root) を使う。**新しい引数・env を足さない。**
- `tools/pegasus/` 配下の**既存 file の編集**であり、新規 file ではない (F660 には触れない)。
- 変更後、`orchestrator/tests/test_ccbench_spawn_sites.py` (行番号・起動本数 pin) が緑のままか確かめる。
  赤になったら所有外なので直さず報告して止める。

### (3) 所有

単位 **F4** = `orchestrator/tests/test_t126_pegasus_tools.py`、`tools/pegasus/probes/t293_perf_site_probe.py`。
F2 の作業場 (`.codex/worktrees/t548-f2-t126`) で、F2 の未 commit 差分の上に載せる。
**F2 の差分 (`submission.py` と M9 の node) を変えない。**
