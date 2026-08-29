---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t2027-t2043-external-input
seq: 3
---

## 新規

### {{F:unusable-resume-hint}}. 変異 wrapper が `--out` 未生成の中断でも resume command を表示し、その resume は必ず失敗する [手順漏れ]

- 事象: T-2027/T-2043 の変異走行 attempt 1 が collection 段の手前で child_rc=2 で止まった。
  wrapper の receipt (`mutation-result-1.json.wrapper-receipt.json`) は
  `container_preserved: true` / `teardown_completed: false` を記録し、`--out` に指定した
  `mutation-result-1.json` は**生成されていない** (lock と wrapper receipt だけが残った)。
  それでも wrapper は `resume command: ...` を stderr へ出したので、その通りに resume すると
  必ず失敗する。中断した wave は再走経路を探すのに時間を使った。
- 根本原因: 表示条件と成立条件がずれている。`tools/mutation_worktree.py` の
  `_print_preserved_resume()` は container を保持したら**無条件に** resume command を出す
  (`--out` の実在を見ない)。一方 `tools/mutation_harness.py` の `--resume` は既存 ledger を
  必須にし、`--resume + --attempt-out には既存の symlink でない通常 file が必要` で
  fail-closed する。`--out` を書く前に死んだ run は、定義上その前提を満たせない。
- 恒久対応: wrapper の resume command を無条件に信じない。中断後はまず `--out` の実在を
  確かめ、不在なら resume ではなく `DW-O19` の既存規則どおり **`--out` と `--attempt-out` を
  新しい path にして再走**する (既存 path は rc=2)。container の保持は evidence 退避のためで
  あって resume 可能性の証明ではない。
- 再発検知: 変異走行が非 0 で戻ったら、resume command を読む前に `--out` に指定した path を
  `ls` する。不在なら resume 経路は成立しないので、新 path での再走を選ぶ。
