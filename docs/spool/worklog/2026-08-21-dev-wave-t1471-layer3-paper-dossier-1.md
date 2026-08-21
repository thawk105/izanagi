---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1471-layer3-paper-dossier
seq: 1
title: layer3 paper evidence dossier を作成した (docsのみ、branch worktree-dev-wave-t1471-layer3-paper-dossier)
---

## 本文

- 依頼は「T-1471」という識別子付きで来たが、`docs/worklog.md`・`docs/decisions.md`・`docs/handoff/`
  のいずれにも landed な予約 ID としては存在しなかった (grep 0件)。段3 敵対相談レンズAが、
  並行稼働中の worktree `dev-wave-t1473-d58-ablation-preflight` の handoff
  (`2026-08-21-t1473-d58-ablation-preflight.md`) を発見し、その `spool_fold.py --dry-run` が
  当時の状態で予測した番号がたまたま `[T-1471]` であり、同 handoff 自身が「並行 land でずれうる
  ため確定値として扱わない」と明記していたことを突き止めた。つまり依頼文の「T-1471」は
  landed な予約ではなく他 wave の dry-run 予測値だった。`docs/spool/worklog/README.md` の規則
  (角括弧 ID は既存 active item のときだけ) に従い、本 fragment の title には角括弧 ID を
  付けていない。
- T425/T1371/T1438/T1458 の稼働 worktree はいずれも本 dossier と無関係と確認 (floor実装・
  official run root provenance・oracle prewarm・non-certifying consumer)。ただし T425 自身の
  再監査 insight (`output/insights/2026-08-20_t425-dependency-reaudit/README.md:143-148`) が
  `orchestrator/campaign/layer3_report.py` を worktree `dev-wave-t470-accepted-consumer` が
  別途編集中と記録しており、本 dossier は renderer を実行しないためこの並行編集の影響は受けない
  ことを report 本文 §6.2 に明記した。
- dev-wave 軽量版で実施: 段2 (codex plan, reasoning=max, read-only) が資料棚卸しと分類初案を
  起草し、段3 敵対相談2レンズ (`--lane sol`/`--lane luna`、同じく reasoning=max) が独立に検証した。
  両レンズが検出した実所見はすべて親が一次資料 (WAL、JSON、docs) へ直接あたって裏取りし、
  修正して report 本文へ反映した。主な修正:
  (1) 段2プランの file:line 索引の多くが、実データ行ではなく直前の見出し/表ヘッダ行を指していた
  (レンズBが最低12件の抜取りで半数以上の不一致を検出、親が全件裏取り)。
  (2) `output/insights/2026-07-13_s6-report-language.md` の S-2 verdict は「不成立」だが、段2
  プランは同じ表内で「不成立」と「未検証」を両方使っており内部矛盾だった (両レンズが独立検出)。
  (3) `backoff-sweep-silo-read-heavy-sweep-8ff95955` は段2プランが「同種の D58 screening 個体」
  と記述していたが、WAL (`runs/wal.jsonl:1-2`) を直接読むと `build-error`
  (ccbench_commit 不一致) で screening/bench に到達すらしていないと判明した (両レンズが独立検出、
  親がWALで確定)。D58 の positive control として decisions 本文が名指しするのは `6f169f90`
  だけである。
  (4) `campaign.lock` の screening field path は段2プランが `#screening` (top-level) と書いて
  いたが、実際は `search_config.screening` である (レンズBが検出)。
  (5) p2-2/backoff-sweep/sort-sweep を「known-no-claim」と分類していたのは不正確で、
  `output/s1-freeze/known_axes_freeze.json` の `selection_rules` を実際に読むと、これらは
  S-1a の `p2_2_flag_opt`/`backoff_fixed_best`/`sort_best` 比較対象を機械選定する**直接入力**
  であると確認した (両レンズが指摘、親が freeze ファイルで確定)。report 本文では
  「certified な S-1 baseline input」という独立区分で扱った。
  (6) D58 ablation の現況は、当初 decisions.md の D601/D629/D630 だけから「Pegasus 基盤工事中」
  という粗い理解だったが、T-1473 の handoff を読んだことで、g++-13 blocker 解消・read-heavy
  Pegasus calibration 未較正・T425/T972 との編集面競合という具体的な blocker まで確認できた。
  T-1473 は未 land (`5db135b0`、段9 で lease 他 holder 保持中のため中断) であり、report 本文には
  「未 land の handoff、main 取り込み後は再確認要」と明記した。
- 成果物: `output/reports/layer3_paper_evidence_dossier.md` (新規)。既存 layer3 renderer
  (`orchestrator/campaign/layer3_report.py`) は実行しなかった (campaign 単位の入出力契約であり
  複数 campaign 横断の paper synthesis を生成する契約がないと段2プラン・レンズBの両方が
  renderer の実装 (`build_report` シグネチャ) を読んで確認したため)。新規測定・production code・
  correctness gate 変更・S/S' 再主張は行っていない。

## 次の一手差分
