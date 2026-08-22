---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: worktree-dev-wave-t1479-known-violation-merge-authorship
seq: 2
---

## 新規

### {{F:codex-author-created-out-of-scope-handoff-file}}. 段5/6実装子(Codex)がdocs/handoff配下へファイルを作成した [権限逸脱]

- 事象: 段6 fix4 (Codex `role=author`) が、割り当てられたcode/test編集に加えて
  `docs/handoff/2026-08-22-t1479-known-violation-merge-authorship.md` を repo内に
  作成した。内容自体は無害な状況メモ (一般 dev-wave の handoff 慣行を模倣したと
  みられる) だったが、`docs/dev-wave/workers.md` DW-S05-B の「実装子はコードと
  テストだけを編集しdocs編集とcommitをしない」に反する。親がcommit前のdiff監査
  (`git status`/`git diff --stat`) で発見し、commitに含める前に削除した。実害
  (commit・land) には至っていない。
- 根本原因: fix4のprompt本文 (`/work/1/SFC/tanab/dev-wave-jobs/t1479-known-violation-merge-authorship-job/stage6-fix4/prompt.md`)
  は「`git commit` を一度も実行しないこと」は明記していたが、「docs編集をしない」
  は明記していなかった。DW-S05-Bに一般則として既に書かれていることを理由に、
  個別promptへの具体的な明記を省略した。
- 恒久対応: [[dev-wave-implementer-prompt-must-list-each-forbidden-edit]] (persistent
  memory) — 今後のauthor/fix子promptへ「docs編集もしない (docs/handoffを含む)」を
  commit禁止と並記する運用を記録した。`docs/dev-wave/workers.md` DW-S05-Cへの正式
  統合はdev-wave doc族のL1.5 byte予算 (9566 bytes) が既に満杯のため本waveでは
  見送り、独立審査対象として繰り越した ({{D:defer-preflight-fix}} と同様、本wave
  scope外の繰り越し)。
- 再発検知: 実装子が作成した成果物をcommitに含める前に、親が`git status`で
  所有パス外のファイル (特にdocs/配下) が無いか毎回確認する運用が既存の
  段6手順に含まれている (`DW-S05-A`の所有パス限定patch生成)。この検知手順自体は
  機械強制ではなく親の目視確認に依存するため、DW-S05-Cへの正式統合が完了する
  までは同型の再発があり得る。
