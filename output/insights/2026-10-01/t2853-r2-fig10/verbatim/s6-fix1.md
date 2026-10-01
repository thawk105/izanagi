## 作ったもの

[wrapper](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/t2853_r2_fig10_plot.py) の置換 2、8 行だけを削除しました。新 SHA-256:

```text
a1a1c3ad597d26d8f5d9b4099d64f069035b2083f9eeae59baa2258d61c8e629
```

実走成果物は [scratch/out/s6-fix/](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/out/s6-fix/) に保存しました。図・表・provenance の hash は [SHA256SUMS](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/out/s6-fix/SHA256SUMS) にあります。

## CLI と実走結果

全実走は `python3.10 -B`。control は段 5 と同じ引数、R2・table・負例は指定された wave worktree の生成器と snapshot を使用しました。完全な引数・結果は [verification.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/out/s6-fix/verification.json) に記録しています。

| 実走 | rc | 確認結果 |
|---|---:|---|
| control | 0 | `artist_series`・caption・`tracked_inputs` が既存 provenance と完全一致 |
| r2（実入力） | 0 | PNG・PDF・provenance 生成、両閉包検査通過 |
| table（実入力） | 0 | 両 attempt の `load_evidence` 通過、workload 6 行・cell 12 行 |
| certification hash の先頭を `8→0` に変更 | 2 | SHA-256 不一致で拒否、図なし。実行は 1 回 |

## caption の差し替え一覧

置換 2 を削除し、次の生成器原文が出力 caption に **1 回だけ**あることを確認しました。削除した置換文の痕跡はありません。

> The outer status is the protocol's conjunction over the three workloads and follows from the negative read-heavy effect; it is not a research verdict.

残る 3 置換は変更せず、各原文が 1 回であることを検査する `exactly_once` を維持しました。以下は実 R2 での差し替え箇所です。

| 箇所 | 原文 → 置換後 |
|---|---|
| B-7 material | `B-7 material:` → `B-7 R2 reproduction-package attempt:`。attempt ID の後に `(separate from original attempt b7f5-20260919a)` |
| satisfaction decision | `This is B-7 material, not a B-7 satisfaction decision (D2044 item 3).` → `This R2 reproduction-package attempt supplies B-7 material, not a B-7 satisfaction decision (D2044 item 3).` |
| single attempt | `This figure reports a single attempt of five samples per cell;` → `This figure reports one R2 reproduction-package attempt of five samples per cell (separate from original attempt b7f5-20260919a);` |

## provenance の扱い

caption の生成・閉包再計算は同じ関数を通ります。control・R2 とも `validate_external_sources` と `validate_repo_closure` が通過しました。

R2 の期待 hash・記録判定は引き続き親の record から取得します。provenance は外部 collect 入力の実パス、record、指定 snapshot、実際の呼び出し、新 wrapper hash を記録しています。

## 現行の受理・拒否挙動

測定値の受理条件、レイアウト検査、期待 hash、判定の扱いは変更していません。control の完全一致と指定負例の拒否を実走確認しました。

R2 の outer status は `reject`、床値判定は rr5／rr50 が `no-regression`、rr95 が `regression` です。

## 所有外への波及

書き込みは wrapper と `scratch/out/` 配下だけです。生成器・docs・tests・policy・insight・測定入力は編集していません。commit・子 agent 起動もしていません。

両 worktree の生成器 SHA-256 は作業前後で同一です。

```text
f78da66d4666455dec4da843f51c2c3ea5e7b10fbac2e91ede3d680f480b795f
```

## 未了・懸念

本 fix の未了はありません。閉包検査は、指定された親側の未 commit snapshot を参照して通過しています。

## 総括

A-F4／B-F4 の対象修正を完了しました。原文の維持、残る 3 置換、control、R2 実入力、指定負例を確認済みです。