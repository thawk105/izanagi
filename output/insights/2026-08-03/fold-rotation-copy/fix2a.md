F1/F2/F3 を `tools/spool_fold.py` のみに実装しました。commit・stage は行っていません。

## 総括

- **F1: closed** — [_rotate_worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1617)
  - projected entry 全体から、閾値以下になる最小の連続 prefix を archive へ移します。
  - レビューの6 fragment条件では、変更前は entry 117–120 が archive、121–127 が current となり **104,462 bytes** で拒否されました。
  - 変更後は entry 117–121 が archive、122–127 が current となり、静的算出で **89,661 bytes**。境界は `121 → 122` と連続し、entry の飛ばしはありません。
  - 新 entry がない場合は従来経路を維持。最新 projected entry を残しても超過する場合は引き続き `rotation-capacity` で拒否します。

- **F2: closed** — [item相対 tokenizer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:383)、[completion field 判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:469)
  - completion item 専用に `- ` の container 幅2を除いた fence view を使用します。
  - raw 4/5-space の backtick・tilde fence、および未閉鎖 fence 内の `remaining: none` decoy は `completion-remaining-field` で拒否されます。
  - top-level `_visible_markdown_lines` は container 幅0のままで、`check_docs.py` 側の受理集合を広げていません。

- **F3: closed** — [_insert_deferred_appends](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1468)
  - replay 判定を対象 item の先頭行末 `endswith(suffix)` に限定しました。
  - 継続行、comment、fence、先頭行途中の同一 byte 列は初回追記を妨げません。
  - 先頭行末の完全一致と同一 fold 内の exact 重複は従来どおり拒否し、error ID も維持しています。

- 検査:
  - `python3 -m py_compile tools/spool_fold.py`: rc=0
  - `git diff --check -- tools/spool_fold.py`: rc=0
  - pytest nodeid、`tools/check_docs.py`、`tools/check_codex_agents.py`、実 land は**走らせていません**。`pegasus02` からの dispatch 迂回も行っておらず、テスト緑は主張しません。
  - worker B の対応 node 3件は静的照合のみ実施しました。

- 波及:
  - [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/check_docs.py:616): `validate_spool_tree` の動的 import によりF2/F3の判定が伝播。F1後のcurrentは既存100,000-byte検査対象です。
  - [tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1795): `plan_fold` がF1の新境界を使い、worklog・archive・archive indexを既存path closureへ載せます。
  - `hooks/`: spool grammar consumer はなく変更不要です。
  - docs、tests、`output/` は編集していません。表示中のdocs/test差分は親・worker Bの既存作業です。

- 未解決項目: 親による計算ノード上の対象pytest、6 fragment統合 `plan_fold`、`check_docs.py`、land受入の実走のみです。