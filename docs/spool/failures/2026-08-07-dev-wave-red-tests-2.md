---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-red-tests
seq: 2
---

## 再発

### F106

- **再発: 2026-08-07** — dev-wave-red-tests。**4 度目**で、今回は変異本走ではなく
  **受入全走の走行中**に親が段 7 の記録 (insights 2 本 + spool fragment 2 本) を worktree へ書いた。
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  が赤になり、`1 failed / 6836 passed / 20 skipped` で終わった。このテストは対象ツールの実行前後で
  `git status --porcelain=v1 -z` が一致することを検査するもので、差分の中身とは無関係に
  **走行中に増えた untracked file だけで落ちる**。harness の preflight のように fail-closed で
  止まるのではなく**偽の赤として現れる**点が、2026-08-05 / 08-06 の再発と異なる新しい情報である。
  17 分の走行 1 回が無駄になった。commit 後の再走で緑を確認した。
  親は本 wave の handoff に「走行中は tree を触らない」と自分で書いたうえで踏んでおり、
  **注意書きでは誘因が消えない**という 2026-08-06 の観察を 1 例強めた。
  恒久対応は F106 のまま (投入から結果取得までは commit・stage・tracked file 編集を行わず、
  待ち時間には repo 外の作業だけを置く)。本再発は memory
  `no-tree-writes-during-mutation-run` の射程を受入全走へ広げる根拠として記録する。
