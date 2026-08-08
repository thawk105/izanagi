---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-dangling-audit-offrepo-authority
seq: 1
---

## 新規

### {{F:budget-trim-removed-safety-pointer}}. byte 予算を捻出するために、他文書にしか無い義務への到達手段を削った [手順漏れ]

- 事象: `.claude/commands/cleanup-branches.md` へ監査の探索根配線 (1 行) を足す byte を作るため、
  親が同 command から「正本は `docs/failures.md` F26。」を削った。見出しに `(F26)` が残るので
  重複ポインタだと判断したが、**F26 本文には command に複製されていない「1 worktree ずつ削除し、
  必要なら timeout を延ばす」という運用則があり、bare な `F26` だけでは到達先が非一意**だった。
  同時に whole-file SHA-256 pin 3 箇所 (checker 定数・test 定数・test の合成コピー) を再同期した
  ため、**意味の欠落を含んだ bytes が「正しい bytes」として固定される**ところだった。
- 根本原因: 予算捻出の判断で「重複しているか」だけを見て、「削る文字列が他文書にしか無い義務への
  唯一の到達手段になっていないか」を確認しなかった。`docs/skill-self-improvement.md` は
  「予算のために安全義務を削除・弱化してはならない」と定めており、規則自体は存在していた。
- 恒久対応: 予算のために削る変更は、削除対象が他文書の義務への到達手段 (正本ポインタ・ID・path)
  でないことを確認してから行う。到達手段であれば削らず、別の重複記述から捻出する。
  本 wave では削除を撤回して復元した (command は 3959 bytes、上限 4000)。
  **機械化は `docs/dev-wave/**` の byte 予算に阻まれており、段 8 の改善候補として残す。**
- 再発検知: 段 6 の焦点再レビューに「親が byte 予算のために削った箇所が安全義務を弱めていないか」
  を明示的なレンズとして入れる。本件はそれで捕まった (`s6re.md` の所見 2)。
- 併記: whole-file SHA-256 pin は bytes しか守らないため、**安全文を削って 3 箇所を同時に再 pin
  すれば検査は通る**。この構造的な穴は本 wave の scope 外として裁定へ返した。
