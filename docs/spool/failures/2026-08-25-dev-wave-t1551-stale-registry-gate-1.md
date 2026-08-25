---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1551-stale-registry-gate
seq: 1
---

## 新規

### {{F:probe-mutation-seen-by-concurrent-reviewer}}. 親の一時変異が走っている tree を read-only の子が読み、誤った must-fix を出した [テスト代表性] [手順漏れ]

- 事象: 段 6 の敵対レビュー 2 本を起動した後、親が同じ worktree で変異 probe
  (`if False and ...` を production へ一時適用) を実行した。レビュー子の 1 本がその窓で
  tree を読み、「事前登録した変異が production に残存しており受入は静的に赤である」を
  最重要 must-fix として報告した。実際には probe は復元済みで、親が `cmp` で
  段 5 成果物との byte 一致を確認できた。所見は誤報だった。
- 根本原因: `DW-O19` は一時変異の**復元**を規定するが、**その間に同じ tree を読む
  read-only の子が居ないこと**を要求していない。親は「復元すれば影響ない」と考えたが、
  観測者は復元前後の任意の時点を読みうる。
- 影響: 誤報 1 件。親が現物照合で否定し、fix 子の prompt へ「これは誤報である」と
  明示したため実装への波及はゼロ。ただし焦点再レビューまで誤報が伝播しており、
  否定を渡さなければ実装子が無害な callsite を「直す」危険があった。
- 恒久対応: 一時変異は read-only の子が 1 本も走っていない窓でだけ行う。
  子の生存は `pgrep -af <worktree path>` で確認する。この規律は
  {{D:flaky-stale-delegation-by-dsession}} とは独立で、`DW-O19` の復元規律に足す運用側の条件である。
- 再発検知: 変異 probe の直前に子の生存確認を行った記録が handoff にあること。
  誤報が出た場合は現物 (`cmp` と `git diff`) で否定してから fix へ渡すこと。

## 再発

### F174

- **再発: 2026-08-25** — [T-1551] wave の段 6 で、段 5 実装子の未 commit 変更が乗った tree に
  probe 変異を当て、復元に `git checkout -- orchestrator/tests/conftest.py` を使ったため
  実装子の変更ごと HEAD へ戻った。3 例目である。今回は probe 適用**前**に
  `git diff` 全文を退避してあり、`git apply --include=<path>` で復元して
  `cmp` により byte 一致を確認した (実害ゼロ)。以後の probe では復元のたびに
  同じ退避 patch との `cmp` を行い、一致を確認してから次へ進んだ。
  F174 の恒久対応「実編集 probe の前に `git status --porcelain` が空であることを確認する」は
  **本 wave でも守られなかった**。守れない要因は、段 6 の probe が「未 commit の子成果が
  乗っている状態」を前提に行われることであり、precondition が構造的に成立しない。
  退避 patch + `git apply --include=` + `cmp` の 3 点を、空 tree 確認の代替経路として記録する。
