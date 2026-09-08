---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-cleanup-inventory-20260908
seq: 1
title: cleanup-branches §1 の棚卸しを --left-right 1 回走査へ替え、worktree の clean 再確認を明文化する (docs + 実装面 pin、branch worktree-dev-wave-cleanup-inventory-20260908)
---

## 本文

ユーザー依頼は「§1 の棚卸しが branch 170 本規模で 4 分超かかる。exact な inventory 義務を一つも
落とさずに所要を下げる」と「§1 と実際の削除の間に状態が変わる件 (F538 と同型) を明文化すべきか判定」。
依頼文は未検証の草案として `git branch --merged main` を ahead=0 の神託に使う案を添えていた。
**実測の結果この草案は採らず、別解を採った。**

実測 (この repo、local branch 168 本、login node、load 5.6〜10.6、git 2.34.1)。
同じ 168 本へ 3 方式を交互に 2 巡させた:

| 方式 | git 呼び出し | 1 巡目 | 2 巡目 |
|---|---|---|---|
| A = 現行 §1 (branch あたり 2 call) | 336 | 54.5s | 81.2s |
| B = `git rev-list --count --left-right <b>...main` (1 call) | 168 | 34.8s | 40.1s |
| D = 依頼の草案 (`--merged` + merged は behind のみ) | 225 | 57.8s | 42.4s |

- **B を採用。** `--left-right` は ahead と behind を 1 回の walk で同時に返すため、呼び出しが
  ちょうど半分になり、exact な ahead も behind も 1 つも失われない。
- **D を不採用にした理由は「遅いから」ではなく「効かないから」。** `--left-right` を使うと
  merged 側にも behind の walk が 1 本要る。つまり `--merged` は呼び出しを 1 本も減らさない。
  草案が効くのは 2 call 形を保ったときだけで、B と併用しても無意味である。
- 前提そのものは真だった: `git branch --merged main` の集合は ahead==0 の集合と 168 本全数で一致。
  真だが、B を採ると使えない梃子だったという関係にある。
- 向きの実測: `<b>...main` の出力は **ahead⇥behind** の順。既存の 2 call 値と全数照合して確認した。
- 168 本全数で A と B の (ahead, behind) は一致。唯一差が出た 1 本は測定中に別 session が
  動かした branch で、同時刻に測り直すと一致した (F538 と同型の churn を測定中に実際に踏んだ)。
- `git for-each-ref --format='%(ahead-behind:main)'` は **使えない**。当該 atom は git 2.41+ で、
  この環境は 2.34.1、実測 rc=128 `fatal: unknown field name`。速度比は 2 標本からの外挿であり、
  他環境への一般化は主張しない。

F538 型の論点には次の結論を出した。**branch 側は閉じている** — §2 が `git branch -d` を必須にし
`-D` を禁じ、拒否時は停止と報告を求めるので、棚卸し後に ahead>0 化した branch は機械的に弾かれる。
**worktree 側には穴があった** — §1 で測る「未コミット差分なし」が §3 の削除直前に測り直されない。
§3 が直前に走らせる `check_worktree_occupancy.py` は docstring どおり cwd/argv の占有だけを見て
dirty を見ず、`git -C <worktree> checkout --detach` は未コミット差分を持ち越すため、
差分を書いた process が終了していれば占有検査を素通りして directory 撤去で差分が消えうる。
敵対レビューが独立にこの経路を real と判定し、+1 byte で収まる文面を出したので採用した。
§2 の worktree 行を `- worktree: §1 の status 空を削除直前に再確認し、HEAD が main に取り込み済みのみ。`
へ置換した。予算のために安全義務を削る必要はなかった。

依頼文の前提のうち 1 つを実測で訂正した。「command だけを変えるなら必須更新は
`CLEANUP_COMMAND_SHA256` の 1 定数」とあったが、**pin は 8 か所**だった。
`orchestrator/tests/test_check_docs.py` が command 全文の逐語複製 `_SYNTHETIC_CLEANUP_COMMAND` と
byte 数 assert 4 つを持つ。path 検索と sha 値検索の両方で全数を出してから着手した。

予算は 5,888 -> 5,898 / 5,900 (余り 2)。§1 と §2 の 3 行以外は 1 byte も触っていない。
`TextLimit` の第 2 引数 110 は byte でなく**文字数**判定 (`len(line)`) であることを実装で確認した。

工数: Codex `role=author` 1 本 (pin 追従 13 分)、`role=review` 1 本 (敵対検査 14 分)、
`role=fix` 1 本 (pin 再追従 11 分)。実装面 (`tools/check_docs.py`、
`orchestrator/tests/test_check_docs.py`) は親が直接編集していない。

記録 commit 前に実走した検査:
- `python3 tools/check_docs.py` rc=0 (違反なし)
- `orchestrator/tests/test_check_docs.py` 単独走 571 passed, 3 skipped
- check_docs の consumer test 9 file の焦点走 1621 passed, 3 skipped
受入全走は記録 commit 後に land 対象 tip へ投入する (DW-O12)。

受入は land 競合で 3 回投入した。attempt 2 (tip ab78e7b3d) と attempt 3 (tip 2f8cc08a4) は
`verdict=child-green`、21,732 passed / 68 skipped。attempt 4 (tip 8a672eafa、main 2fcafc6b7 を
取り込んだ後) だけ `orchestrator/tests/test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed`
が 1 件赤で、21,787 passed / 1 failed だった。**非帰属と判定した。** 根拠は
(a) 本 wave の変更面は `.claude/commands/cleanup-branches.md`、`tools/check_docs.py` の
sha 定数 1 個、`orchestrator/tests/test_check_docs.py` の pin、spool fragment だけで、
当該 test file は `check_docs` を import せず差分から到達しない (consumer 検索で確認)、
(b) 同一 tip で単独再走したところ 211 passed / rc=0 で再現しない、
(c) 当該 test は SIGTERM を無視する子を kill する時間依存の検査で、共有 login node の
負荷で締切を割りうる型である。DW-O18 に従い単独再走 1 回・受入再走 1 回だけ行った。

## 次の一手差分

### 新規

- {{T:cleanup-bare-ref-and-branch-d-basis}} **P3・ユーザー裁定待ち**:
  敵対レビューが `/cleanup-branches` の**既存**欠陥を 2 件出した。いずれも今回の変更が持ち込んだ
  ものではなく、変更前の 2 call 形にも同じだけ在る。両方ともこの repo では現に到達しないことを
  実測したので、今回は収容しなかった。
  (a) **裸 ref の曖昧性**: `<b>...main` も `main..<b>` も裸 ref なので、branch と同名の tag が
  あれば tag 側に解決され、未着地 branch を ahead=0 と報告しうる。`refs/heads/<b>...refs/heads/main`
  が安全だが +22 bytes 要り、現在の余り 2 bytes に入らない。実測: tag は
  `t1806-pre-rebuild-history` の 1 本だけで branch 名と衝突なし。
  (b) **`git branch -d` の判定基準**: upstream が設定された branch では upstream への merge を
  基準にしうるため、「`-d` が main 包含の最後の防壁」という説明は一般には強すぎる。実測:
  local branch 170 本のうち upstream を持つのは `main` の 1 本だけで、`main` は §2 が削除対象から
  除外している。設定が変われば到達しうるので、文面で塞ぐか監視するかの裁定を求める。
