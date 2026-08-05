---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-f26-recurrence-record
seq: 1
---

## 再発

### F26

- **再発: 2026-08-05** ([T-472] wave の land 後の worktree 撤去)。2026-08-01 の再発と**同一経路**
  である。`git worktree remove` が `working trees containing submodules cannot be moved or removed`
  で拒否した時点で、本エントリが定める判別 (「そこで手を止めて `/cleanup-branches` を読む」) を
  実行せず、即興で `git -C <worktree> submodule deinit -f external/ccbench` を打った。
  結果も同じで、共有 `.git/config` の `submodule.*` 登録が消え main checkout の
  `git submodule status` が `-` prefix になった。復元は `git submodule update --init external/ccbench`
  で即時、pin `d706650` 一致と並行 4 worktree (t452-t453 / t474 / t476 / token-economy) の
  無影響を確認済み。実害は一時的。
- **前回の再発が診断した経路欠落が塞がれていなかった。** 2026-08-01 の追記は
  「dev-wave の段 9 は自分の worktree を畳むよう求めるが、その手順の正本が
  `/cleanup-branches` §3 にあることを指していない」と特定していたが、`DW-S09` への
  ポインタ追記は未実施のままだった。今回その追記を試みたところ
  `docs/dev-wave/**` が hard ceiling 25200 bytes に対し 25377 bytes となり、
  予算超過で入らなかった (上限は上げない規律のため撤回)。**恒久対応の経路は依然未実装**であり、
  裁定へ返した。
- 補足: memory `bg-job-closes-its-own-worktree` は deinit 禁止を本文に持っていたが、
  索引 1 行だけを見て動いたため到達しなかった。索引行に禁止を明記する形へ更新済み
  (repo 外の個人 memory)。
