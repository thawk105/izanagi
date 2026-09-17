## 段 1 brief (親、2026-09-17 21:37 JST)

**研究前進:** 土台 (dev-wave の受入道具)。止めている研究の実測は無い。ユーザー裁定 D2044 項 5 が P1 で実装手番を指定し、command 引数は worklog 候補より優先 (DW-C00)。最小差分 = `tools/dev_wave_wait.py` の監査呼び出し 1 本の位置移動 + lifecycle 契約 + test。完了判定 = **main にだけ存在する違反 commit** を受入前 merge 段が赤にし、受入 command を 0 回投入・lease 解放 (現状は素通りで、D908 の前提「取り込み後の監査が取り込みの作った違反を捕まえる」が成立していない)。

**実測した現状 (main 38353207f):**
- `tools/dev_wave_wait.py:3831-3872` `_run_acceptance_attempt`: `merge_pending=True` → `git merge --no-ff --no-commit main` (stage `merge`) → `check_ai_provenance.py` (stage `merge-history-provenance`, 引数なし = 既定 authoritative 監査) → `--message-file` (stage `merge-message-provenance`) → `commit --dry-run` → `commit` → `merge_pending=False` → `commit-rev-parse` → `commit-message-postcheck` → `postcheck` → `commit-head-postcheck` → `prerun-clean`。
- `tools/check_ai_provenance.py:1775-1787` `_commit_range`: 既定は `policy..HEAD` の到達集合 (`_resolve_head` = `git rev-parse HEAD`)。HEAD 以外を pin する CLI は無い (`main()` 3391-: `--range` / `--message-file` / `--force-dispatch` のみ)。`--range` は非 authoritative (scope 規則は子孫のみ、known-violation append-only 検査なし) なので同じ監査ではない。
- したがって `--no-commit` 中の HEAD は wave tip のままで、`merge-history-provenance` の選択集合は `preclaim-history-provenance` と同一。取り込んだ main の commit は入らない。
- 中止・後始末: `_AcceptanceLifecycle.merge_pending` (607) → `_cleanup_lifecycle` (3329) → `_cleanup_after_claim` (3285) → `_abort_pending_merge` (3118) = `git merge --abort` + MERGE_HEAD 不在 + `status --porcelain --untracked-files=no` 空を要求。
- cleanup 側 `tools/dev_wave_cleanup.py:575` `_assert_reflog_commits_reachable`: branch reflog と worktree HEAD reflog の全 commit が main 到達でなければ撤去拒否 (D1233: reflog にしか残らない commit は喪失側)。
- 既存 test `orchestrator/tests/test_dev_wave_wait.py`: `_STAGES` (6683-6698) と `test_nonzero_stage_blocks_submission_and_releases` (6701-) が段順序を `_FakeEffects` の厳密な期待列で pin。`git merge --abort` を期待する test: 1149/1163/1382/6353/7260/7331/7444/7700-7747。実 git fixture `_real_waiter_repo` (1081) + 偽 checker `_write_path_aware_provenance_checker` (982) が temp repo の `tools/check_ai_provenance.py` として置ける。
- pin 閉包 (DW-O09): waiter の束縛は live (`dev_wave_land.py:1119-1141` tested tip blob ↔ receipt `waiter_executed_sha256`)。凍結定数・FROZEN_MANIFEST 無し。`acceptance_duration_ledger.json` は未知 node を許容。更新すべき pin は無い。

**scope (in):** (1) `_run_acceptance_attempt` の `merge-history-provenance` を取り込んだ変更を含める位置 (commit 後) へ移す。(2) `merge_pending` / abort / cleanup の契約を同じ変更単位で直す。(3) 既存 test の順序 pin 更新 (正例維持) + 新規負例 (main のみの違反 → merge 段赤 → command 0 回・lease 解放)。(4) docs: F365 追補、insight README + verbatim、spool fragment (worklog / decisions / failures)。

**scope (out):** `check_ai_provenance.py` の変更 (`--head` 追加・`--range` 化)、既知違反台帳の扱い変更、`dev_wave_land.py` / `dev_wave_cleanup.py` の変更、説明文を実装へ合わせる案 (D2044 項 5 で不採用)、仮想リスク向け gate・検査・台帳の追加。

**確定済み裁定:** D2044 項 5 (位置移動 + 契約修正)。D908 (全史監査 2 本は削らない → 位置移動は削減でない)。D95 (実装面は Codex author)。D1233 (reflog 喪失閉包)。F365 (2 位置の監査の由来)。規律 2 (監査赤 → 受入 command 投入 0 回)。

**不変条件:** claim 前監査 (`preclaim-history-provenance`) は不変。`merge-message-provenance` は MERGE_HEAD 前提 (prospective parents) なので commit 前のまま。監査赤で受入 command 0 回・lease 解放・理由本文 (既存 4 test の性質)。既知違反台帳の扱い現行維持。受入 receipt の waiter live 束縛は自動で追随 (更新不要)。

**割れうる前提 (親の provisional 裁定・攻撃対象):**
- (P1) commit 後の監査赤で merge commit を**巻き戻さない** (merge_pending の窓は merge→commit のまま、commit 後の赤は postcheck 等の他 commit 後段と同じく merge commit を残し lease だけ解放)。理由: 巻き戻し (`reset --merge <premerge>`) は捨てた merge commit を branch/HEAD reflog に残し、cleanup の喪失閉包 (D1233) が撤去を拒む (rc=20 型)。reflog を消す手は cleanup 防壁の迂回。残る merge commit は正当な 2 親前進 merge で、land / tested-tip 契約と矛盾しない (main の違反が直るまでどの wave も land できない点は同じ)。
- (P2) 新位置 = `git commit` 直後・`commit-rev-parse` の前 (HEAD = merge commit)。
- (P3) 変異事前登録: M1 = 監査を commit 前 (現行位置) へ戻す → 新規負例が KILL。M2 = 監査呼び出し削除 → 既存 `_STAGES` 系 + 新規負例が KILL。M3 = 監査赤を握り潰す (rc 無視) → KILL。M0 = comment のみ → SURVIVED 対照。新規負例の形: 実 git (`_real_waiter_repo`) + 偽 checker (`git merge-base --is-ancestor <main-only 違反 commit> HEAD` が真なら非 0) で、attempt が stage=`merge-history-provenance` で止まり command 0 回・lease 解放・HEAD = merge commit (P1) を主張。模擬差: 偽 checker は実 checker の到達集合の決め方 (`policy..HEAD`) を HEAD 到達性で模す。

**成果物の形:** 実装 commit (Codex author、`tools/dev_wave_wait.py` + `orchestrator/tests/test_dev_wave_wait.py`)。docs commit (insight `output/insights/2026-09-17/t2670-merge-provenance-position/README.md` + `verbatim/`、spool fragment、F365 追補は failures fragment、D は decisions fragment)。

**並列分割:** 実装子 1 本 (1 file + test 1 file、密結合)。段 3 consult 2 レンズ (A: 裁定・契約整合 D2044/D908/D1233/F365/D518、B: 実装・test 順序 pin・変異被覆・fake の模擬差)。段 6 レビュー 2 本。

**受入・実測環境:** 焦点走は login node (`python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py` 系)、変異 matrix は計算ノード dispatch、受入全走は `tools/dev_wave_wait.py acceptance` (門番 script で混雑待ち)。

