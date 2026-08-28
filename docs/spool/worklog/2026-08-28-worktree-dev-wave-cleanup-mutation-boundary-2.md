---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-cleanup-mutation-boundary
seq: 2
title: cleanup-branches の mutation boundary を削除権限だけへ閉じた (code + tests + docs、branch worktree-dev-wave-cleanup-mutation-boundary、変異 baseline PASSED・3/3 KILLED)
---

## 本文

- ユーザー裁定どおり、cleanup command 受領から final まで一般クラス 2 規律より優先する mutation allowlist/default-deny を共有正本の冒頭へ置いた。許可は適格な既存 local branch の `git branch -d` と、所有確認済み eligible worktree の限定撤去だけで、repo file/history・記録・自己改善・project tests/provenance は cleanup 本走から除外した。
- Codex skill は共有 command の全文不可分適用と安全側 overlay だけへ縮約し、real prune は preview のみに維持した。自己改善正本は cleanup 本走を final の候補報告で終端し、実装・台帳・commit を後から明示起動された別 dev-wave に限定した。
- 敵対 review で、無対象 `git worktree prune` が foreign metadata を巻き込める穴を real と裁定した。dry-run 全候補と今回の所有確認済み対象が完全一致しなければ real prune 全体を引き渡す gate へ修正し、焦点再 review は must-fix 0 で受入れた。
- 今回事象は F599 の status 観測面変更とは根本原因が異なるため、新規 {{F:cleanup-class2-authority-leak}} として routing した。command/skill には事故の物語を複製していない。
- command は 3,996 bytes の既存 4,000-byte 上限へ境界を収容できず、既存重複を先に縮約した上で個別上限だけ 5,900 bytes へ引き上げた。現物は 5,888 bytes、5,901-byte 負例を独立 pin し、他 command/self/skill の上限は変更していない。D782 の報告条件に従い、この個別増枠を明示する。
- Codex D95 author は checker と test の 2 ownership unit。段 2 plan、段 3 consult 2 本、段 6 review 2 本、fix 3 巡、焦点再 review 1 本を隔離 launcher で実施した。実装 hunk に親の直接著作はない。
- 焦点 3 node は最終統合後 3 passed。変更 test file 単独は request `954481.nqsv` で 571 passed / 3 skipped。`check_codex_agents` は 0 native active / 13 dormant、`check_docs` は違反なし。
- 変異は temporary repo fixture の固定 commitだけで実施した。180 秒初回は M2 dispatch の orphan hold で停止し、request `954415.nqsv` の終端/不在を確認後に残存 1 行を HEAD 値へ復元して hold/sidecar を解除した。600 秒 final2 は baseline PASSED、KILLED 3、MISMATCH/SURVIVED/TIMEOUT 0。M2/M3 の初回過小 expected-node 集合は旧 ledger に erratum として保持した。
- full acceptance は `child-green`、18,537 passed / 62 skipped、raw/normalized rc=0、tested main `dcf9224a157668b4a6e9919841f5f242ee2ae84a`、tested tip `b1b7296982f3eef560cb57ddd3ca3e79569431a6`、log SHA-256 `729a592d8209cd16c886ea64a0a8bbc702d2db83720e6658ad5b2cdee45d0587`、effective scheduler `loadgroup`。
- 実装+failure commit `c012c7e42` 後の full-history provenance は新規違反 0。既知違反 54 は既知台帳どおりで、本 wave の緑主張には使っていない。push・remote 操作、既存 cleanup 対象の branch/worktree 削除、事故 commit `45b693d6b` の除去/history rewrite は未実行。

## 次の一手差分
