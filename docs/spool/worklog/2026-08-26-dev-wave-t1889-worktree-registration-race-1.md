---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1889-worktree-registration-race
seq: 1
title: [T-1889] 生きた worktree 登録を読むテストを hermetic 化し、production の競合は裁定へ送った (テストのみ、branch worktree-dev-wave-t1889-worktree-registration-race、変異 matrix = baseline PASSED・8/8 一致・KILLED 7・SURVIVED 1 (登録どおり)・MISMATCH 0)
---

## 本文

- 依頼は「`test_t810_coordinator.py` が生きた worktree 登録を読むため、別セッションの worktree 撤去と
  競合して落ちる。fixture 側で固定するか、既知の非帰属赤として扱うかを決める」。
  **fixture 側で固定するほうを採り、production は 1 byte も変えていない。**
- **親は段 1 で第 3 案 (production への有界な取り直し) を暫定裁定していたが、段 3 の 2 レンズが
  独立に覆した。** 決め手は「取り直しは 1 回の scan の中身は変えないが、**実行の流れ全体では
  受理集合を広げる**」こと。churn 中に撤去された worktree が消えた瞬間の scan が採用されれば、
  その中の work_root / output_root が repository-external として受理されうる。
  F633 自身が「受理集合を変える案は裁定を要する」と書いており、取り直しもその 1 つだった。
  詳細と却下した案は {{D:worktree-registration-race-is-fixed-in-tests-not-production}}。
- **段 1 の不変条件に書いた性質が現行コードに存在しなかった。** 親は「受理の根拠は完全に読み切った
  矛盾のない 1 枚の scan」と書いたが、レンズ A が示したとおり、列挙した admin 名から `gitdir` を
  開くまでの間に同名 admin を作り直す ABA も、列挙後に増えた登録も現行は検出しない。
  守るべき性質と、現に成立している性質を書き分けていなかった。
- **wave 開始 3 分後に main へ入ったユーザー裁定が裁定の向きを決めた。** DW-S04 の
  「段 4 直前に裁定 inbox を再走査する」が実際に効いた例である。
  D1045 は同一の事故ではない (あちらは F632) が、
  主題は同じ「周辺状態に依存して落ちる検査」で、「自分で状態を作る形へ直す」を採り
  「判定器の基準を変える」と「前提未充足なら飛ばす」を却下している。拘束力ある裁定としては
  扱わず、択一の順序の裏付けとして使った。
- **F633 が land 経路も同型と書いている点は、親の独立確認で裏が取れなかった。**
  `test_dev_wave_land.py` は coordinator を import せず、F633 が名指しした land node が起動する
  実 pytest 子の nodeid は spool_fold の 1 件で coordinator の node ではない。land 側自身の失敗本文
  `registered worktree path cannot be resolved` は `output/insights/` と `dev-wave-jobs/` の
  全件検索で 1 件も出ない。**確認できる例は coordinator の 1 例だけ**で DW-G03 の独立 2 例に足りず、
  land 側 production は触らないと裁定した。
- **「既知の非帰属赤」を採らない理由について、親は段 1 で誤った論拠を書いていた。**
  「落ちる node が動くから hold で塞がらない」と書いたが、レンズ B が示したとおり susceptible な
  基底 node 集合は静的に列挙できる (26 件)。正しい理由は (1) 上記ユーザー裁定が却下側、
  (2) hold registry は node ごとの実測赤と canonical failures の逐語一致を要求するので 26 件を
  正直に登録できない (D1017 と同型)、(3) 26 node を hold すると repo-external gate の実 repo 結合が
  丸ごと消える、の 3 つである。
- **レビューが「事前登録した変異を確実に赤にする node が無い」ことを見つけた。** 登録読み取りの
  4 つの拒否 (欠落・symlink・非 regular・読み中変化) を決定的に殺すテストは**変更前から 1 つも
  存在しなかった**。DW-M01 の「確認できなければ登録せず実効 gate へ再照準する」に従い、
  負例 4 件を新設してから変異を登録し直した。
- **変異 harness の node 抽出契約と両立しない変異が 2 件あった。** 抽出器は `FAILED ` 行だけを読むが、
  空骨格 (M1) と authority 常時失敗 (M4) は fixture 内の assert で落ちるため全 hermetic node が
  `ERROR` になり、rc=1 でも失敗 node を抽出できず harness が fail-closed で停止した。
  登録から外し、親が単発で実測した。**M1 = 42 errors / 0 failures** (空骨格は全 hermetic node を
  setup で落とす = 骨格は実物であって素通りではない)、**M4 = live 3 node が FAILED**
  (決定的な失敗は 3 回の再試行を経て必ず再送出される = 再試行は決定的な赤を隠さない)。
  M4 は DW-O19 に従い一時変異させ、`git checkout --` で復元して commit と byte 一致を確認した。
- **反実仮想走 (DW-M08) が「新テストだけが検出する差分」を実測した。** 新設 4 負例とその台帳項目を
  取り除いた木へ同じ production 変異を当てると、**M5 (欠落を許容)・M6 (symlink を追従)・M10
  (非 regular を受理) は 3 件とも SURVIVED**。この 3 つは新テストだけが検出している。
  **M7 (撤去済み claim の破棄) だけは取り除いても KILLED** で、親の SURVIVED 期待が外れた
  (MISMATCH 1 件)。殺していたのは変更前から在る
  `test_git_common_dir_preserves_missing_registered_worktree_claim` だった。
  erratum として残す — M7 は既に守られていたのであって、新テストの寄与ではない。
- **親の自己違反を 1 件記録する。** 最初の焦点走を `| tail -40` に通して rc を消し、
  1 件の赤を「rc=0」と読みかけた。パイプなしで取り直した。
- **焦点走の赤 1 件は F57 の既知・決定的・site 依存の赤だった** (計算ノードでのみ発火、所有 [T-1079])。
  台帳の既定手順どおり `--deselect` し、他は 452 passed で rc=0。
- **land を 2 度止められ、2 度目の理由は本 wave が裁定へ送った欠陥そのものだった。**
  1 度目は archive 名の月日衝突 (別 wave が修理して着地。本 wave の差分とは無関係) で
  `rc=26 fold-failed`。修理着地後の再挑戦では `rc=11` (lock-busy) を 2 回踏んだ後、
  3 回目が `rc=31 fold-gate-failed` で止まった。本文は
  `registered worktree path cannot be resolved: [Errno 4] Interrupted system call` で、
  **落ちた path は自分の wave ではなく別 wave の worktree** である。
  すなわち **land 側の生きた worktree 登録の読み取りが、一斉着地の負荷下で一時的な syscall 中断で
  落ち、それが非再試行の内容失敗として分類された** ({{F:land-registration-scan-eintr-is-classified-as-non-retryable}})。
  段 3 のレンズが must-fix として予告し、親が scope 外として裁定へ送った項目
  ({{T:land-registration-scan-failure-is-not-retryable}}) が実機で発火した形である。
  **land 側 production を触らないという段 4 の裁定は変えていない** — 触るには受理集合と
  retry 意味論の裁定が要る。非再試行の判定を迂回して同一 request で投げ直すことはせず、
  受入を取り直した。緑の全走 1 本を捨てている。
- **codex 子の工数**: plan・敵対 2 本・author・review 2 本・fix の 7 本。全て accepted、失敗ゼロ。
- 一次資料は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1889-worktree-registration-race/` の
  `brief.md`・`s4-ruling.md`・`primary-measurements.md`・`s2-plan.md`・`s3-{sol,luna}.md`・
  `s5-author.md`・`s6-{revA,revB,fix}.md`・`mfinal-result.json`・`mcounter-result.json`・
  `mprobe2-result.json`・`m4.out`・`focus2.out`。

## 次の一手差分

### 完了

- [T-1889] 周辺依存の 30 関数を hermetic 化し、live authority に主題が結び付く 3 node だけを逐語
  allowlist に残した。登録読み取りの 4 拒否を殺す負例を新設し、新しい node が再び live registry を
  読む形を塞ぐ AST gate を足した。production は未変更で、競合そのものは裁定へ送った。
  remaining: none
  base: 45f323ae95de6695827511421ec1d6066588e0f46eb1a2fcc7328df039e35385

### 新規

- {{T:worktree-registration-scan-consistency-ruling}} **P2・新規・ユーザー裁定待ち**:
  生きた worktree 登録を読む production の競合をどう閉じるか。有界な取り直し・`missing_ok` 相当・
  走行開始時 snapshot はいずれも受理集合を変える。現行は churn 中を fail-closed で拒否する。
  実測は {{F:worktree-registration-scan-has-two-failure-modes}} に置いた。
- {{T:worktree-registration-scan-detects-no-aba}} **P2・新規**: 列挙した admin 名から `gitdir` を
  開くまでの ABA 置換と、列挙後に増えた登録を現行 scan は検出しない。「矛盾のない 1 枚」は
  現行にも存在しない。受理集合を狭める hardening なので独立に裁定する。
- {{T:land-has-a-third-live-registration-reader}} **P2・新規**: `tools/dev_wave_land.py` の
  `_worktree_snapshot` と `_validate_admin_binding` が第 3 の生きた登録読み取り経路である。
  本 wave の scope 外。無関係な worktree の撤去で land が `RC_CONTROL_PLANE` のまま失敗しうる。
- {{T:land-registration-scan-failure-is-not-retryable}} **P2・新規**:
  `_registered_worktree_paths` の resolve 失敗は `_FoldGateFailure` の既定
  (`retryable_same_request=False`) で送出され、`release_safe=True` になって lease が解放される。
  取り直しの有無に関わらず現存する欠陥で、同一 request を再利用できなくする。
- {{T:coordinator-registration-scan-has-no-time-bound}} **P2・新規**: coordinator の登録 scan には
  時間上限が無い。親の実測で単一 process でも 808.553 ms の外れ値が出ており、
  metadata stall 時にテスト全体 5 分上限を静的に証明できない。
- {{T:mutation-harness-cannot-classify-setup-errors}} **P2・新規**: 変異 harness の node 抽出器は
  `FAILED ` 行だけを読むため、fixture / setup で落ちる変異を rc=1 でも分類できず fail-closed する。
  本 wave では 2 件を登録から外して親が単発で実測した。抽出契約を `ERROR` 行まで広げるかを裁定する。
