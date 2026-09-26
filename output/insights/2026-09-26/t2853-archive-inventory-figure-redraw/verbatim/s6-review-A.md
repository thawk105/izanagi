## 所見

1. **must-fix** — [pipeline.py:2705](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2705): build 後、保全前に `evidence.source_root` の tracked source または HEAD が変わる入力では、保存する patch は検証に使った固定 snapshot と一致せず、`ccbench_pin` と patch の基準 HEAD もずれうる。**影響:** inventory から組む R1 の source と proof-surface 判定が元の評価から変わる。**代案:** 保全時に diff の hash と HEAD を build 時の evidence に照合し、不一致なら inventory を `failed` にする。

2. **should** — [test_t2853_trace_preservation.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:57): `git_source()` は `tracked.txt` だけを作る。`cc/silo` が無い入力では proof source が `unavailable` となり、同 file 79 行の `assert result.certified and calls` が R1 項目の assert より先に落ちる。**影響:** M1・M2・M4〜M7 の名指し kill 点を判定できない。**代案:** 認証に必要な Silo source を fixture に入れ、無変異の焦点走が緑であることを確認する。

3. **should** — [test_t2853_trace_preservation.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:100): fixture の実際の diff は `before`→`after` だが、`tracked_diff_sha256` の期待値は空 bytes の hash。**影響:** evidence の値を記録する経路は検査できても、記録した値が保存 patch と対応する R1 入力かは検査できない。**代案:** 実 diff から evidence の期待 hash を作り、保存値と比較する。

## 変異 kill 点の判定

| ID | 判定 | 理由 |
|---|---|---|
| M1 | 不成立 | 名指し test は argv の assert 前に `certified` で赤になる。 |
| M2 | 不成立 | 同上。 |
| M3 | 成立 | 空 trace は witness 設定前に abort し、null の assert が変異を検出する。 |
| M4 | 不成立 | HEAD の差は fixture にあるが、`certified` で先に赤になる。 |
| M5 | 不成立 | pin の assert 前に赤になる。 |
| M6 | 不成立 | patch の assert 前に赤になる。 |
| M7 | 不成立 | module hash の assert 前に赤になる。 |
| M8 | 不成立 | `subprocess.run` と `Path.read_bytes` の差し替えは pipeline に届くが、先行する `result.certified` が赤になる。 |
| M9 | 成立 | 非 Git root の `git diff` 失敗が評価へ漏れる変異は、結果比較の assert で検出できる。 |
| C0 | 成立 | docstring のみの変更で、判定経路は変わらない。 |

## 総括

**NO-GO。** must-fix は保全時の source／HEAD を build 時の evidence に照合していない点。加えて fixture を直し、変異前の焦点走と M1〜M9 の単一理由を再確認する必要がある。今回は指定どおり静的検査のみで、pytest・変異は実走していない。