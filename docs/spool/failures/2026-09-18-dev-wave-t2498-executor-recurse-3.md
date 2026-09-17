---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2498-executor-recurse
seq: 3
---

## 再発

### F709

- **再発: 2026-09-18** — near miss (着地前に段 6 レビューが捕まえた)。`hooks/guard_bash.py` の script-executor
  層剥き (D1891 の実装、段 5) を Python の自己再帰で書いたところ、`-m cProfile` を 1,100 層重ねた 13 KB の
  command で `RecursionError` になり、`main()` の例外経路 (防護 path を含まない入力は rc 0) が後続 segment の
  `pytest -q` を検査せず**許可**した (実入口での deny→allow、D428 違反)。深さが入力データ (今回は command の
  層数) に比例する再帰という F709 と同じ型で、対応も同じ — 層剥きを while 化し深さを O(1) にした
  ({{D:executor-inner-same-judgment}})。再帰上限の引き上げ・深さ上限での拒否は採らなかった。再発検知は
  `test_bash_login_executor_recursion_deep_nesting_has_no_stack_limit` (1,100 層で例外なく後続 pytest を拒否し、
  深い軽量形は許可) と、D428 反転検査 runner が例外を fail-closed で数える経路。**新しい情報:** hook の
  例外経路は「防護対象を含む入力だけ fail-closed」なので、重量判定の層で起きた例外は許可へ倒れる。
  `decide()` の戻り値だけを比べる反転検査ではこの後退を捉えられず、例外を別枠で数える必要がある。
