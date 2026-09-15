---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2642-cleanup-cd-guard
seq: 2
---

## 新規

### {{F:overlap-check-misses-preedit-wave}}. 編集面重複検査が worktree 作成直後の wave を 0 件と数え、2 wave が 28 秒差で同じ面を掴んだ [手順漏れ]

- 事象: [T-2642] の着手前検査 (2026-09-16 ≈04:33 JST) で、全 74 worktree の未 commit 差分・
  branch tip 差分・`ps` のいずれも 0 件と出た。14 分後に [T-2641] の plan 子が `ps` に現れ、
  `.git/worktrees/*` の birth time が相手 04:34:10 / 自分 04:34:38 で**相手が 28 秒先発**と判明。
  編集面 (`.claude/commands/cleanup-branches.md` の §1/§2/§3、`tools/check_docs.py` の
  `CLEANUP_COMMAND_SHA256`) は完全衝突しており、依頼が定めた「重なれば後発が降りる」に従って
  段 3 まで進んだ本 wave が実装を降りた。実害は wave 1 本ぶんの設計が実装へ届かなかったこと。
- 根本原因: 既存の 2 段検査 (branch tip / 作業ツリーの未 commit) はどちらも「相手が既に編集したか」
  を見る。worktree を作った直後でまだ 1 byte も書いていない相手は、定義上どの検査にも映らない。
  dev-wave は worktree 作成から最初の編集まで brief・plan・裁定を挟むため 10 分以上あり、
  この窓は狭くない。`ListAgents` の `started Nm ago` は session 開始であって worktree 作成では
  ないので、同時投入された 2 本では先後を判定できない。
- 恒久対応: memory `overlap-check-must-scan-worktree-dirt` に 3 段目 (存在検査) を追記した。
  対象面が他 wave と衝突しうるときは worktree の存在一覧と `ListAgents` を突き合わせ、主題が近い
  wave があれば `stat -c '%n %w' .git/worktrees/<name>` で birth time を取り、自分より早ければ
  自分が後発と判定して**着手前に**降りる。`docs/dev-wave/operations.md` の `DW-O20` へ収容しようと
  したが単節予算 1000 bytes に対し 1148 bytes となり、D782 の手順で memory 側へ落とした。
- 再発検知: 同じ編集面の wave が 2 本 land しようとしたとき、後発の受入または land が pin 追従の
  やり直しで止まる。段 1 の brief に「先後の判定根拠 (birth time)」を書かせることでも早期に出る。

### {{F:huge-file-cat-breaks-child-evidence}}. read-only 子が射影 file を全文 cat し、成果物が 2 回不採用になった [手順漏れ]

- 事象: [T-2642] の段 3 敵対相談 (lane luna) で、子が
  `/bin/bash -lc "cat orchestrator/tests/test_check_docs.py"` (476 KB / 12753 行) を実行し、
  巨大出力を含む rollout の行が壊れて `evidence_issues: reason=event_invalid` となり
  `outcome=not_accepted` で落ちた。`--job-id` を変えた再投入でも同じ 2 attempt とも同じ落ち方をした。
  子は最後まで走っており (`codex_exit_code=0`、`output_tokens` は正常)、失われたのは出力の公開だけ。
  prompt に読み方の制約を足した 3 回目で採用された。
- 根本原因: `tools/codex_worker_launch.py` の stdout event 検証は 1 行 1 event を要求する
  (`:1429` 付近)。数百 KB の command 出力を含む event 行はこの検証を通らない。射影 file の
  大きさに応じた読み方の指示が prompt 契約に無く、子は既定で全文 `cat` を選ぶ。
- 恒久対応: memory `codex-child-discipline` に節 `huge-file-cat-breaks-evidence` を追記した。
  数百 KB 級を射影する prompt には「全文 `cat` を禁じ、`grep -n` で位置を出し `sed -n` で
  200 行以内ずつ読む」を byte 数・行数の実数つきで書く。`docs/dev-wave/operations.md` の
  `DW-O05` へ収容しようとしたが L1.5 層予算が 9870 > 9696 bytes となり、D782 の手順で
  memory 側へ落とした。
- 再発検知: `launcher_rc=1` かつ `codex_exit_code=0` かつ `.log` が空で成果物が作られない組み合わせ。
  receipt の `attempts[].evidence_issues[].reason` を見れば `event_invalid` が直接出る。
