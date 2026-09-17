---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2638-child-worktree-commit
seq: 1
title: [T-2638] 実装子 worktree の残差を起動器 / 待ち手の終端で子 branch へ commit する終端契約を実装した — fix 子で実データ検証 (起動器が 5a99d99d0 を commit、trailer は receipt 実測値)、DW-S05-A は固定 base 抽出へ (コード + テスト + docs、branch worktree-dev-wave-t2638-child-worktree-commit、変異 matrix = baseline PASSED・負例 15/15 KILLED 期待 node 完全一致・対照 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2638] (D2044 項 16、ユーザー裁定) 実装子 (Codex author) の作業木の終端契約『wave 終了時に内容を
  branch へ commit する』を実装する — 起動器 / 待ち手の終端で作業木の未 commit 内容を実装 branch へ commit し、破棄案は
  採らない。新しい保存 framework は作らない。Codex author (D95)。起動時に対象 file を稼働 wave と照合する。着手直前の
  local main から fresh worktree を作る。規律 2 を緩めない。本題の終端契約だけ。仮想リスク向けの gate・検査・台帳・一般化の
  追加は scope 外」。
- **閉じた。** 設計判断は {{D:worker-worktree-terminal-commit}}、一次資料は
  `output/insights/2026-09-18/t2638-child-worktree-commit/README.md` (逐語は同 `verbatim/`)。
- 実装の要点: `tools/dev_waves/git_state.commit_worker_worktree` (helper 1 関数、`GIT_COMMANDS` に 5 操作)、
  `tools/dev_wave_codex.py` (workspace-write ∧ author/fix の launcher 復帰後に発火、launcher rc≠0 保持、rc=0 ∧ refused/failed
  → rc=3)、`tools/dev_wave_wait.py producer --commit-worktree <abs>` (opt-in、死亡確定後 1 回、refused/failed は `producer-commit`
  で fail-closed)。状態は committed / clean / deferred (操作進行中) / refused (主 checkout・detached・main/master・root 不一致) /
  failed。trailer は receipt の recorded→requested→unknown、`none` は `unknown`。message file は `<git-dir>/izanagi-worker-commit.msg`。
  docs は `docs/dev-wave/workers.md` DW-S05-A を `git diff --cached <base>` (`<base>` = 子作成 SHA) にし終端 commit の 1 文を追加、
  L1.5 予算 (9,696 bytes、空き 0) は同節の意味保存の縮約で相殺。
- **実データ検証**: 段 6 の fix 子は新機構を含む HEAD (fe1e6662e) から起動されたため、起動器が終端で残差を子 branch
  `fix-dev-wave-t2638-child-worktree-commit` へ commit した (5a99d99d0、07:29 JST、trailer `product=codex; model=gpt-6-astra;
  reasoning=medium; role=author`、stdout `worktree-commit: committed …`、作業木 clean、message file 残置なし)。親は新 DW-S05-A の
  固定 base 抽出で commit 後も同じ 3,928 bytes の patch を得た。
- 段 2 plan は brief の (P2)「sandbox だけで対象を限定できる」を反証 (stage と sandbox は独立に受理)。段 3 レンズ A 10 所見
  (real 8、うち採用 6・nit 2)、レンズ B 削除候補 6 + 不足 3 — 待ち手の done 判定・check-only 書込み・rc 再解釈・index.lock 特別
  扱い・rebase 等の個別分岐を削り、両 tool は依頼の名指しどおり最小配線で残した。段 4 で rc=3 を新設 (起動失敗 2 と区別)。
- 段 5 author 子は所有 6 file 545 行。焦点走 (計算ノード 5011.nqsv) 461 passed / 1 failed — 赤は待ち手正例の `err == ""` が
  既存 stderr 診断 (`/proc/<pid>/stat` 読取不能で pid-only へ縮退) を拒む fixture 側。段 6 レビュー A/B の must-fix は 3 件で一致
  (その赤、DW-S05-A の保存範囲・呼出側指定・記録のみの欠落、`tempfile(dir=None)` が TMPDIR 次第で作業木内)。docs は親、残りは
  fix 子で是正。焦点走 v2 (5056.nqsv、変更 3 file + consumer 14 file) 2307 passed / 5 skipped (hold のみ)。焦点再レビューは
  must-fix 全件 closed、新規 must-fix なし (nit: 配置先の回帰検出力、同名 file の上書き)。
- 変異 matrix (container `.codex/worktrees/t2638-mutcontainer` = c5403437c、runner は 3 test file を `-k` で 16 node に絞り
  `--force-dispatch`): probe 走で全 16 変異の観測 node を集め (drift 0、較正走不要)、本走は baseline PASSED・負例 15/15 KILLED
  期待 node 完全一致・対照 M0 SURVIVED・MISMATCH 0。M12 (flag 無しの待ち手が cwd を commit) は既存 test
  `test_producer_waits_while_pid_alive_then_completes_after_death` も殺す。
- 限界 (insight §5): 使用中の message file 配置先はテストで直接観測しない、同名 file の上書き、submodule 内編集は対象外、
  待ち手の trailer は `unknown`。**撤去との相互作用は scope 外** (D2044 項 16 の限定どおり): 稼働中 wave `cleanup-si-routing`
  が DW-O28 を「子 worktree も `dev_wave_cleanup.py` で撤去」へ変えているが、commit 済み子 branch は main 非到達 commit を
  持つため同 tool は拒否する見込み (未実測)。子 commit を祖先として保持する統合は別裁定。段 5 の author 子 (`t2638-impl`、
  旧 HEAD) の残差は旧挙動のまま未 commit で残る。
- 工数: codex 子 6 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1、全段 `gpt-6-astra` / `medium`)。計算ノード:
  焦点走 2、変異 probe 18 request・本走 18 request。受入全走は最終 tip に対して 1 走 (結果は land の受領証)。
- 運用事実: wave worktree の docs が未 commit だと `snapshot_authority` (launch_authority.py) が codex 子を全部拒否するので、
  docs 変更は子起動前に commit した。隔離 session の guard は `for` + 変数付き `git`、`$()` + `grep -rln` を拒否するので
  走査は job tmp の .py へ外出しした。

## 次の一手差分

### 完了

- [T-2638] 起動器 / 待ち手の終端で作業木残差を子 branch へ commit する終端契約を実装し、fix 子の実データで検証した
  (5a99d99d0)。撤去との相互作用は D2044 項 16 の限定どおり scope 外。
  remaining: none
  base: 9b8fd2c8cccba93197dcec91d60cb8b3e9bdcad985e190c2072957945887a5aa
