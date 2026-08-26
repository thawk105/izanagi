## 総括

- FIX-A1/A2 を訂正裁定に沿って実装した。
- tracked 418 file と指定祖先 4 directory を可視に保つ。
- 同 prefix 内の untracked path は引き続き除外する。
- snapshot 1 回の Git process は 14 から 5 へ減った。
- 許可された 4 file だけを変更し、`git add`、commit は実施していない。
- pytest は制約上未実走のため、両 must-fix は `unverified`。

## FIX-A1 の実装と対の control

fail-closed を撤去し、ignored prefix 配下の tracked path とその祖先を `git_visible_paths` として保護した。ignored prefix 自体は残るため、同じ prefix 内の untracked path は除外される。

tracked path の祖先は metadata 正規化対象にも加えた。これにより、可視化された祖先 directory の metadata が untracked peer の作成によって snapshot 差分を生まない。

逆向きだった control を改名・置換した。

- positive control: `runs/nested/tracked.txt`、`runs`、`runs/nested` が snapshot 集合へ現れる。
- negative control: 同じ directory の `runs/nested/untracked.txt` は現れない。

書込みなしの実 repository probe では、`job-staging` 配下の tracked file が 418/418 可視、指定祖先が 4/4 可視、synthetic untracked peer は除外となった。

## FIX-A2 の実装 (process 数の前後と memo の論証)

内部関数が `(prefixes, ancestors)` を一度に返し、公開関数と snapshot caller が共有する形にした。

1 snapshot 当たりの process 数:

- 変更前: 14
- 変更後: 5
- 内訳: `rev-parse` 1、`config` 1、`check-ignore` 1、batch `ls-files --cached` 1、`ls-files -o -i` 1

静的 probe でもこの順序と 5 process を確認した。レビュー B の約821〜825 process に対し、従来の94 helper 呼出しを上限としても470 process以下になり、combined 呼出し分だけ実際はさらに少なくなる。

memo は置いていない。

- `.gitignore`、info/exclude、global exclude の bytes は snapshot 呼出しごとに再読する。
- index も snapshot 呼出しごとに再照会する。
- prefix と ancestor が共有するのは、同じ同期的 snapshot 呼出し内の結果だけ。
- before/after 間では一切再利用しない。
- 実在依存の `git ls-files -o -i` も毎回実行するため、状態変化を cache が隠す経路はない。

## FIX-A3 の判断

linked worktree fixture は追加しなかった。現実装は正しく `git rev-parse --git-path info/exclude` を使っており、追加 fixture は今回の must-fix を越えて変更量を増やすため、指示どおり親が起票する backlog とした。

## 変更した file と行

- [output_snapshot_ignores.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/output_snapshot_ignores.py:28): tracked 例外付き prefix、batch index 照会、combined API、除外判定。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_s8b_oracle_driver.py:561): combined 呼出し。行707から対 control。
- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_real_repo_serialization.py:543): combined 呼出し。
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_s8b_floor_campaign.py:1485): optimized/reference snapshot の tracked 例外適用。

## 実走したか (nodeid と範囲、または「実装済み・未実走」)

**実装済み・未実走。**

必須の `tools/run_tests.py` は `output/task-runs/` を書くため、今回の許可 write 集合では使用できない。pytest の直接起動も repository 規律に反するため実施していない。

実施した非pytest検査:

- `git diff --check`: 対象4 file、rc=0
- AST parse: 対象4 file
- Git process 計数 probe: 5 process
- 実 repository probe: tracked 418/418、祖先 4/4、untracked negative control

改名した node:

- `test_git_ignored_output_prefixes_rejects_tracked_rule_descendant`
- → `test_git_ignored_output_prefixes_preserve_tracked_rule_descendant`

レビュー A の確認では、この node を exact 登録する meta-test はない。duration ledger は90% collection coverageで、即時の全node登録を要求しない。

## 各 must-fix の状態 (closed / unverified / not-done)

- FIX-A1: **unverified** — 実装と静的 probe は完了、pytest未実走。
- FIX-A2: **unverified** — 5 process を実測、pytest未実走。

## 所有外への波及可能性

- `GitIgnoredOutputPrefixes` は tuple subclass になった。tuple equality、反復、membership、sort順は維持するが、`type(value) is tuple` を要求する未知の consumer には波及しうる。射影レビューで確認された caller は今回更新した3 test fileのみ。
- oracle/serialization の `_t080_output_snapshot` と、floor の optimized/reference snapshot が combined API を使う。
- `test_real_output_snapshot_matches_reference_and_is_deterministic` は両 floor 実装のconsumerである。
- `conftest.py`、共有 fixture、duration ledger、`.gitignore` は変更していない。
- docs、failure ledger、backlog closure は親の所有範囲。

## 期待赤の finding 集合

fix 子 B 未landに由来する期待 finding は次の2群に限定する。

- `test_pegasus_dispatch_compute.py` の control-lock thread test群: 偽 clock 未注入、実 sleep、5秒 Event deadline、watchdog不統一が残る。既知 node は `test_control_lock_allows_peer_after_pending_hold_is_durably_released`。
- `test_flaky_test_holds_contract.py` の非空 summary cardinality: `2/1/1` の分離 control がまだ復元されていない。

これ以外の pytest 赤、特に今回の4 fileに属する赤は回帰として扱う。

## 未完・未確認

- 焦点 pytest、受入全走、48並列走は親による実測待ち。
- FIX-A3 の linked worktree fixture は backlog。
- fix 子 B の2修理と親所有の docs closure は未land。
- `git status --short` は対象4 fileのみ `MM`。段5の既存 staged 差分に本fixの unstaged 差分が重なった状態で、こちらから `git add` はしていない。