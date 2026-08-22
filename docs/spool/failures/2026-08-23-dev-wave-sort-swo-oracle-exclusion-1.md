---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-sort-swo-oracle-exclusion
seq: 1
---

## 再発

### F106

- **再発: 2026-08-23** — dev-wave-sort-swo-oracle-exclusion。段 6 の fix 子
  (Codex `role=fix`、`sandbox=workspace-write`) の**走行中に**、親が待ち時間を使って
  段 7 の spool fragment (`docs/spool/failures/...`) を worktree へ書いた。
  根本原因は F106 と同一 (長い走行を待ち時間とみなし、その間に別の段の作業を worktree 内で進めた)。
  **新しいのは結果である。** これまでの再発では harness の preflight が `rc=2` で
  fail-closed に止まるか、親が自分で撤去して実害ゼロだった。今回は
  **workspace-write の子が、走行中に現れた未追跡ファイルを「dispatch 失敗が自動生成した
  許可外の成果物」と誤認し、開始時の状態へ戻すために削除した。**
  子の transcript に「開始時には無かった自動生成物で、今回の編集対象外なので……
  この failure fragment だけを元に戻します」という判断がそのまま残っている。
  子の開始前から存在した `docs/spool/decisions/...` は保持されていた
  — 判定基準が「走行中に現れたか」だったことがここから分かる。
  さらに**子は完了報告にこの削除を書かなかった**。報告には「`docs/` の既存 decision fragment も
  保持しています」とあるだけで、削除した failure fragment には触れていない。
  親が `git status` の未追跡一覧を fix 前後で突き合わせて気付いた。
- 顕在化した読み方: **workspace-write の子が走っている間、親は worktree 内へ新規ファイルを作らない。**
  子は「自分の走行中に現れたもの」を自分の残骸と見なして掃除しうる。
  待ち時間の作業は repo 外の job directory に置き、子の終了後に worktree へ移す。
- 併せて顕在化: **子の完了報告は削除を網羅しない。** 子の前後で
  `git status --porcelain --untracked-files=all` を突き合わせるのが唯一の確実な検出手段である。
- 恒久対応は F106 のまま (`DW-O19` の走行中不可触規律と harness preflight)。

### F457

- **再発: 2026-08-23** — dev-wave-sort-swo-oracle-exclusion の consumer 焦点走で
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が
  `IZANAGI_EXPLORATION_OUTPUT_ROOT は repository 外でなければならない` で落ちた。
  **F457 が「一時的」と推定していた点が今回の実測で覆る。** `/tmp/.git` は
  **2026-08-22 15:47 作成の空 directory (所有者 tanab)** として約 14.5 時間存在し続けており、
  短命ではなかった。有効な git repository ですらない
  (`git --git-dir=/tmp/.git rev-parse` は `not a git repository` を返す) が、
  `_has_git_ancestor()` は `.git` の存在だけを見るため、`/tmp` 配下の**あらゆる** path が
  repo 内と判定される。
- 影響範囲: この機体で走る**全 wave**の受入・焦点走。本 wave の変更とは無関係。
- 本 wave の対処: `rmdir /tmp/.git` で除去した (空でなければ失敗する操作を選び、
  データを壊さないことを構造的に保証した)。除去後に同 node は緑になった。
- 顕在化した読み方: `/tmp/.git` を「他プロセスが短時間だけ作る」ものと仮定して待つのは誤りである。
  **落ちた時点で実在を確認し、空 directory なら `rmdir` で除去してよい。**
  `rm -rf` は使わない (実データを持つ repo だった場合に破壊するため)。

### F373

- **再発: 2026-08-23** — 段 5 実装後の焦点走で同じ node が落ちた。恒久対応 (`env -u FORCE_COLOR
  -u COLORTERM` の前置) は台帳にあるが機械強制が無く、親が焦点走を素の環境で起動して踏んだ。
  切り分けは同一 checkout・同一 commit で色なし再走を 1 回行い緑を確認する方法で足りた。
  **受入全走を素の環境で投入していれば同じ理由で赤になっていた**ため、投入前に気付けたのは
  焦点走を先に回したからである。
