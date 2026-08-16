# 親の実測値 — [T-1262] (2026-08-17 00:50-01:10 JST, Pegasus login, worktree 内)

probe は repo 外 (job tmp): `probe_t1262.py` / `probe_t1262b.py` / `probe_t1262c.py`。

## M1. 現行 gate が受理する攻撃 (合成 snapshot、closure 有効 = production 既定)

| # | 攻撃 | 結果 |
|---|---|---|
| A | 空 CCBench: `read-tree --empty` + worktree 全削除 + `submodule.<n>.ignore=all` + 再 seal | ACCEPTED |
| B | worktree の `child.txt` bytes 差し替え + `ignore=all` | ACCEPTED |
| C | index+worktree に HEAD^{tree} 外の `extra.txt` + `ignore=all` | ACCEPTED |
| D | `.git` marker を `../../.git/modules/rogue` (admin の複製) へ | ACCEPTED |
| A' | A から `ignore=all` を外した形 | REJECTED (`dirty set mismatch` / `numstat mismatch`) |
| A'' | A から再 seal を外した形 | REJECTED (`git fsck exited 2` / unreachable 1) — 内容照合ではなく偶発 |

## M2. 実 CCBench (external/ccbench @ 511c9538) の index と worktree

- index entry 405 件 = `100644` 285 / `100755` 119 / `160000` 1 (third_party/shirakami)
- **生 bytes の blob sha1 と index の blob id の不一致 = 0 件 / 404 件** (gitlink を除く全件)
  - symlink は 0 件。欠落 0 件。
- **mode 不一致 = 0 件** (実行 bit・symlink 種別とも index と一致)
- `.gitattributes` は `* text=auto eol=lf` を持つが、**Linux 上の checkout 結果は LF のみ**なので
  生 bytes と blob が一致する。

## M3. 費用 (実 CCBench、cold)

| 操作 | 時間 |
|---|---|
| `rev-parse HEAD^{tree}` | 0.010s |
| `diff-index --cached --quiet HEAD --` | 0.011s |
| `diff-files --name-only` | 0.218s |
| `ls-files --stage` (405 行) | 0.005-0.006s |
| **Python で 404 file を全件 sha1 (生 bytes)** | **0.199s** |

## M4. snapshot 生成経路の stat cache

`_derive_snapshot_from_base` は `shutil.copytree(..., copy_function=shutil.copy2)` を使う
(`tools/codex_reasoning_ab.py:1545-1550`)。copy2 は mtime を保つが **inode・device・ctime は
変わる**ため、git の index stat cache は必ず無効化され、git は内容を再 hash する。
したがって stat cache の陳腐化に由来する偽陽性・偽陰性はこの経路では発生しない。

## M5. 凍結 pin 閉包 (DW-O09)

- `submodule_manifest_sha256` を持つ成果物: `output/insights/2026-07-30_t181-reasoning-ab/schedule.json`
  と `output/insights/2026-08-09_t181-certified-rerun/schedule.json` の 2 件のみ (コード外)。
- この 2 件の live consumer は `run-outputs` 配下の rollout だけ
  (`orchestrator/tests/test_codex_reasoning_ab.py:78-84`)。
  `verify_manifest` / `_replay_manifest` をこの 2 件へ当てる test は **0 件**。
