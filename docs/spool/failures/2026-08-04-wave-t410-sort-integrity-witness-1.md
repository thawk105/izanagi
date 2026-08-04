---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: wave-t410-sort-integrity-witness
seq: 1
---

## 新規

### {{F:main-checkout-mutated-from-worktree-session}}. worktree の wave で主 checkout を編集した near-miss [手順漏れ]

- 事象: 段 4 の前提実測で「verifier を一時変異させると committed evidence の再束縛検査が赤になるか」を
  測る際、`cd <主 checkout> && ... >> orchestrator/verifier/report.py` を実行し、
  **wave の worktree ではなく主 checkout を編集した**。直後に `git checkout --` で復元し
  差分ゼロを確認したため実害は無い。その後 worktree で測り直して所期の結果を得た
- 根本原因: セッションの shell は毎回 cwd を worktree へ戻す。read-only の調査中は
  `cd <主 checkout> &&` を前置しても無害なので癖として蓄積し、**最初の書き込み操作でそのまま
  危険になった**。`DW-O19` は復元手順 (`git diff` と `git checkout --`) を定めるが、
  **どの checkout で変異させるか**は書いていない
- 恒久対応: 変異前の clean 確認を `cd` 無しで行い、`pwd` が wave の worktree であることを
  同じ command 内で表示してから変異する (`DW-O19` の「変異前を clean 確認し」の実行形)。
  read-only 調査で主 checkout を指す `cd` を使ったら、書き込み操作の前に必ず落とす
- 再発検知: 一時変異の直前に `pwd` と `git rev-parse --show-toplevel` を出力し、
  wave branch 名と一致しなければ変異しない

## 再発

### F30

- **再発: 2026-08-04** — 逆向きの pin を見落とした。F30 は「自分の成果物の bytes を pin している
  台帳」を数え落とす型だったが、今回は「**自分の編集面 source を bytes で pin している成果物**」
  (qualification evidence の `binding.runtime_modules` が `orchestrator/verifier/**.py` を全件束縛)
  を段 1 で数え落とし、段 3 の敵対相談で blocker として出た。成果物パスからの `grep` は
  この向きを見つけない。段 1 では「この成果物を pin しているのは誰か」に加えて
  「**自分が編集する source を pin している成果物はあるか**」も列挙する。
