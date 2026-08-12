## 所見 1 — provenance の配置順が裁定・runbook と不一致

- **[real の根拠]** 実装は [`git merge` 後に checker を実行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:872)する一方、runbook は [`checker → merge`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:830) と記述している。さらに checker は `MERGE_HEAD` の有無で検査対象 path を変えるため、順序は受理集合にも影響する。[`_merge_preflight_parents()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/check_ai_provenance.py:1191) は merge 後なら prospective parents を使うが、merge 前の clean index では staged path が空になる。
- **[成果物影響 1 行]** 現状は裁定外の追加拒否を行いうるうえ、checker 失敗が単純な release ではなく merge abort 失敗による rc=74 に昇格しうる。
- **[must-fix]** 単純に前へ移すと merge 固有の provenance 検査が弱くなる。形式検査を merge 前、merge path を使う完全検査を merge 後に分けるか、現順序を再裁定して runbook と受理集合を一致させるべきである。機械状態だけなら merge 前が安全だが、現 checker の意味的検出力は merge 後が強い。

checker 非 0 時の現 cleanup 自体は正しく配線されている。`merge_pending=True` は merge 前に設定され、commit 成功後まで解除されないため、checker 失敗は `merge --abort` の後、ACQUIRED なら release、HELD_SELF なら保持になる。

## 所見 2 — checker subprocess だけ ambient Git 環境を継承する

- **[real の根拠]** subprocess wrapper は argv 先頭が `git` の場合だけ `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE` 等を除去する。[checker 呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:879)は Python argv なので無加工の環境を継承する。一方 checker の [`_git()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/check_ai_provenance.py:745) も Git discovery 環境を除去していない。実 Git テストは明示的にこれらの変数を除いた環境を渡しているため、この経路を覆わない。
- **[成果物影響 1 行]** ambient `GIT_DIR` 等がある起動では checker が別 repo/index を見て rc=0 を返し、不正な merge provenance が受入後の全史監査まで残りうる。
- **[must-fix]** checker 呼出しにも direct Git と同じ、または checker 側の `_REPO_DISCOVERY_ENV` 全体の sanitization が必要。

## 所見 3 — 新 checker stage に 300 秒 timeout が適用されない

- **[real の根拠]** [`_run_subprocess()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:123) が bounded stage とするのは direct `git` と `wave_land_window.py` だけである。`check_ai_provenance.py` は `_run_capture` 経由でも `subprocess.run` の無 timeout 経路へ入る。
- **[成果物影響 1 行]** checker または配下 Git が停止すると、pending merge と lease を保持したまま waiter が止まり、TTL 後は排他性まで失う。
- **[must-fix]** provenance checker も stage subprocess として process group・300 秒 timeout の対象に含めるべきである。

なお `--message-file` は [`args.message_file is None or args.force_dispatch`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/check_ai_provenance.py:2344) の site/dispatch gateを通らない。今回の argv に `--force-dispatch` はないため、Pegasus dispatch や compute queue 待ちは発生しない。

## 所見 4 — M3/M4 は殺すが、報告された「単一理由性」は fake の形に依存する

- **[real の根拠]**
  - M3 は [`test_preflight_untracked_dirty_rejects_before_claim`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1914) が rc=2・stage・claim 不投入を exact に見るため赤になる。ただし旧 argv は strict fake の期待 `_STATUS_ARGV` と一致せず、実際には untracked を見逃して `prerun-clean` へ進む前に `unexpected-error` となる。裁定表が述べた「rc=2→70・lease 無→有」の意味的経路は実行していない。
  - M4 も [`test_malformed_ai_agent_message_fails_provenance_before_commit`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1846) で赤になるが、fake が checker rc=9 を直接与え、dry-run 成功応答は用意していない。呼出し削除時は次の expected argv との不一致で赤になるため、「実 checker だけが拒否し dry-run は通る」の証明ではない。
- **[成果物影響 1 行]** mutation score は緑でも、claim 消費の変化や実 checker と Git dry-run の結合契約に対する回帰検出力を過大評価する。
- **[nit]** M3 は両 status argv を理解して結果を分ける fake または実 Git untracked 負例、M4 は実 checkerを使う結合負例が望ましい。登録された変異そのものは両方とも殺せる。

## その他の確認

- `prerun-clean` は rc=0 後の `stdout` 非空を拒否し、status 非 0 は `_run_capture` が同 stage で拒否するため恒真ではない。generic stage testには status rc=9 のケースもある。
- `prerun-clean` は behind 値に関係なく postcheck 後、command argv 出力前に実行される。
- 新設 fake テスト 7 本はいずれも `assert_drained()` を持つ。実 Git 1 本は本物の Git repoと waiter subprocessを使い、実 lease helperを包む claim wrapperが tracked fileを変更する。command は stdout にのみ sentinel を出すため、その不出力は未投入の有効な証拠である。
- `skip` / `xfail` の追加、揮発 hash・時刻・pid・絶対 tmp path の焼き込み、既存 assertion の緩和はない。
- `_cleanup_lifecycle`、`_cleanup_after_claim`、`_abort_pending_merge`、`_claim_once`、`_wait_until_acquired` に差分はない。

### 変異判定

| 変異 | 判定 | 主なテスト |
|---|---|---|
| M1 | KILLED | tracked/untracked/postmerge/held-self dirty |
| M2 | KILLED | tracked dirty |
| M3 | KILLED。ただし上記のとおり形依存 | preflight untracked |
| M4 | KILLED。ただし上記のとおり形依存 | malformed provenance |
| M5 | KILLED | behind>0 postmerge dirty |
| M6 | KILLED | clean 正例 |

## 総括

- must-fix: **3 件**
  1. provenance の配置順が裁定・runbook と不一致
  2. checker subprocess が ambient Git 環境を継承
  3. checker stage が timeout 対象外
- 殺せない変異: **なし**
- nit: **M3/M4 の mutation kill が意味的経路ではなく strict fake の argv/queue 形にも依存する**
- pytest は依頼どおり実走せず、静的読解のみで判定した。