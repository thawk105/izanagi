---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2638-child-worktree-commit
seq: 2
---

## {{D:worker-worktree-terminal-commit}}. 実装子 worktree の終端 commit は起動器と待ち手が行い、対象外・保存未達・親担当を分けて返す

**決定:** D2044 項 16 (作業木の内容を wave 終了時に branch へ commit する) の実装として、次を定める。

1. 発火点は起動器 `tools/dev_wave_codex.py` の launcher 復帰後と、待ち手 `tools/dev_wave_wait.py producer`
   の `--commit-worktree <絶対 path>` (opt-in) の producer 死亡確定後。両者は同じ helper
   `tools/dev_waves/git_state.commit_worker_worktree` を呼ぶ。
2. 起動器の発火条件は `--sandbox workspace-write` かつ stage が author / fix。read-only 子・dry-run は
   何も出さず、workspace-write の他 stage は `worktree-commit: skipped reason=stage` を出して発火しない。
   stage と sandbox は独立に受理されるため sandbox だけでは対象を限定できない (段 2 plan の指摘)。
3. 保存対象は投入先 worktree 全体の残差 (`git add -A` → staged)。内容を選別しない。commit は記録であり、
   採用・land・撤去のどれとも別。
4. 状態は 5 種。`committed <sha>` / `clean` (staged 空) / `deferred reason=operation-in-progress`
   (`MERGE_HEAD` 等の操作進行中 — merge commit は親が作る、DW-C01) / `refused reason=<root-mismatch |
   primary-worktree | detached-head | protected-branch>` (投入先の誤り) / `failed reason=<Git 操作名>`。
   起動器の最終 rc は launcher rc≠0 ならそのまま、rc=0 かつ committed / clean / deferred なら 0、
   rc=0 かつ refused / failed なら 3 (起動失敗 2 と区別し、親を「再投入」でなく「手動 commit」へ導く)。
   待ち手は既存 outcome が成功で refused / failed のとき `producer-commit` で fail-closed にし receipt を
   公開しない。flag 無しの待ち手は stdout / stderr / rc / receipt bytes を 1 byte も変えない。
5. commit message は固定件名 + 本文 7 field + `AI-Agent: product=codex; model=<m>; reasoning=<r>;
   role=author` の 1 行。値は launcher receipt の `recorded_*` → `requested_*` → `unknown` の順で採り、
   `[a-z0-9][a-z0-9._-]*` へ正規化し、`none` は `unknown` に写す (`check_ai_provenance.py` が拒否)。
   待ち手は receipt を読まず `unknown` を書く。message file は `<git-dir>/izanagi-worker-commit.msg`
   (作業木の外) に置き、成功・失敗とも削除する。
6. `index.lock` の特別扱い、rebase / cherry-pick ごとの分岐、done file の内容判定、check-only 経路の
   書込み、submodule 内編集の再帰、同一 worktree 並行投入の排他、撤去 (cleanup) との接続は足さない。

**理由:**

- 依頼が名指した起動器と待ち手の両方を最小配線で実装し、新しい保存 framework・台帳・schema を作らない
  (stdout 1 行と commit だけ)。
- 対象外 (read-only 等) と保存未達 (refused / failed) を分けないと、`.done` の rc=0 が「残差を保存した」
  とも「対象外だった」とも読め、終端契約が空洞化する (段 3 レンズ A、段 6 レビュー A)。
- `requested_*` は launcher が `codex exec -m` / `model_reasoning_effort` へ実際に渡した確定値であり、
  推測ではない。
- `tempfile(dir=None)` は `TMPDIR` 次第で作業木内に落ち、中断時の残置が次の `add -A` で成果物へ混入
  しうる (段 6 レビュー A)。git-dir は Git が返す作業木外の位置で、linked worktree ごとに分離される。

**却下した選択肢:**

- sandbox だけで発火判定 — `dev_wave_codex.py` は plan + workspace-write も受理するため対象外を巻き込む。
- 起動時 snapshot や opt-in flag を起動器に足して親 worktree での発火を防ぐ — 親 worktree での
  workspace-write 起動は DW-C01 の mid-merge だけで、それは `deferred` が受ける。追加の gate は仮想リスク
  向けであり scope 外。
- `index.lock` を `skipped` に分類 — 保存未達が rc=0 に隠れる。Git 失敗として `failed` に集約する。
- 待ち手に launcher receipt path を渡す flag — 待ち手の commit は起動器が死んだときの後詰めであり、
  receipt が無いことが常態。`unknown` は provenance 規約の許容値。
- 子 commit を祖先として保持する統合 (patch 展開の廃止) — 段 5 の所有・投入契約の本体を変える別裁定。
  D2044 項 16 の限定 (記録しただけでは取り込みも撤去可能性も成立しない) に従い本 wave では扱わない。
