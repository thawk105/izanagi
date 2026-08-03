---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t313-read-budget
seq: 2
---

## 再発

### F82

- **再発: 2026-08-03 (3 度目)** — `verify_declared_fold_commit` の fold 署名検査が、
  **DW-O23 が指示する「land 前の wave 側 main 取り込み」を全面的に禁止する**ことを実測した。
  `_commit_diff` は `git diff-tree -m` を使うため merge commit では親ごとの差分を出す。
  main を wave へ取り込む merge commit の第 1 親 (wave 側) との差分には、main が既に land 済みの
  fold commit の署名 (`M docs/spool/FOLDED.md`、fragment の `D`) が必ず現れ、
  `_landed_fold_output_path` が `landed-fold-owned-path` で弾く。
  main の tree は 1 byte も再適用されない (本件では `ea6ca43..9fbed42` の変更は wave 側 9 ファイルのみ)
  にもかかわらず、ff-only 自体が不能になる。
  fold は 2026-08-02 以降すべての land が `FOLDED.md` を触るため、
  **main が動いた後に取り込みが要る wave は今後すべて land 不能**である。
  署名という表現自体は F82 の恒久対応どおりだが、**merge commit で署名を親ごとに評価する**
  ことで受理集合が再び過剰に縮小した。F82 が定めた再発検知「新設 gate の裁定には正例を必ず
  1 つ書く」の正例 =「wave が main を取り込む merge commit を含む landed 区間が受理される」が
  今回も書かれていなかった。
  恒久対応の候補 (実装は別 wave): 署名判定を merge commit では第 1 親でなく merge base
  (または `--cc`) に対して行う、あるいは landed 区間から merge commit を除外して
  「main に無い変更」だけを署名判定にかける。
  検出: [T-313] wave の段 9 land が `status=fold-failed` / `reason=landed-fold-owned-path` で停止
  (main は `ea6ca43` のまま未変更)。

### F50

- **再発: 2026-08-03** — [T-313] wave の立ち上げで、専用 handoff を背景 job harness の既定
  (`$CLAUDE_JOB_DIR/tmp` = home 配下の `~/.claude/jobs/<id>/tmp`) に作り、ユーザーに止められた
  (near-miss、実害なし)。前回 (2026-07-29) は worktree 内、今回は home 配下で、**置き場を
  間違える型は同じ**である。原因は `DW-O20` の「専用handoffはworktree外（背景jobはjob tmp）」
  という文言が、要件 (worktree の外) ではなく harness 既定の実体 (home 配下) を指しており、
  Pegasus の「home に不要物を置かない」規律 (runbook §6 の領域分担) と衝突したこと。
  repo 内 `.claude/jobs/` への退避も worktree 隔離ガードが Write を拒否するため使えず、
  最終的に repo 外の `/work` 配下へ置いた。
  恒久対応 = `DW-O20` の当該語を byte 中立で「背景jobはrepo外」へ是正 (本 wave の段 8) と、
  auto-memory `pegasus-keep-home-clean`。
