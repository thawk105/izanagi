---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-cleanup-mutation-boundary
seq: 1
---

## 新規

### {{F:cleanup-class2-authority-leak}}. cleanup のクラス 2 が repo 記録と commit の変更権限へ拡張された [権限] [手順漏れ]

- 事象: cleanup 対象の branch/worktree 削除が 0 件だった実行で、一般クラス 2 の worklog 規律を適用し、cleanup 結果だけの spool fragment 1 file を main へ直接 commit した。
- 根本原因: cleanup 固有の mutation allowlist/default-deny と一般クラス 2 規律への優先例外がなく、削除権限と repo file/history の記録権限を合成した。
- 影響: cleanup が local main、surviving tracked/untracked contents、Git history を非 cleanup mutation で汚し、削除 0・罠発見・検査赤でも自己改善 commit へ移行できた。
- 恒久対応: `.claude/commands/cleanup-branches.md` §0/§6 を共有境界とし、`.agents/skills/cleanup-branches/SKILL.md` は全文不可分適用と安全側 overlay だけを持つ。`docs/skill-self-improvement.md` は cleanup 本走を final 候補報告で終端し、実装・記録を後続の明示 dev-wave に限定する。
- 再発検知: `tools/check_docs.py` の whole-file pin、`orchestrator/tests/test_check_docs.py` の独立 fixture/byte/1-byte 負例、および command 単体と command+skill の敵対読解で、削除 0・罠・検査赤・外側クラス 2 の各終端を判定する。
- 家族: F599 と同じく cleanup が共有 main を動かす型だが、F599 は status の見た目を目的化した観測面変更であり、本件は作業種別規律から mutation 権限を誤導出した別原因である。
