単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s1-brief.md — 親の段 1 brief ((P1)〜(P4)・(P2')、事前登録案、費用)。**brief 自身も検査対象である。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/verbatim/T-2273-origin.md — 依頼の逐語。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/verbatim/D2243-head-item1-2.md (項 2)、D2242.md、D1936-item35.md、D357.md — 既裁定の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md — 第 4 回診断 (結論 1〜8、§3、§4)。同 dir の verbatim/s4-ruling.md (事前登録の先例) と verbatim/probe-source.md (probe の逐語、runner / plugin / analyzer)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md — 前回の実受入の隣接対 (結論 1〜5、§5)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-20/t2243-collection-contention/README.md — collection の温 / 冷の実測。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py — `_copy_git_visible_output` (847)、`_T080SharedBases` (920)、`_t080_join_shared_bases` (974)、builder `_build_t080_stub_free_e2e_repo` (1437、複製呼出し 1458、発行 child 1564〜1710、subprocess.run 1712)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py — `_early_memo_selected` (2368)、`_start_early_memo_job` (2388)、`pytest_configure_node` (2583)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/tools/run_tests.py — login 側の collection (`_collect_login_universe` を grep)、計算ノードへの env (PYTHONDONTWRITEBYTECODE を grep)。
- 必要なら D2242 実装 `git show eb65d322f -- orchestrator/tests/test_s8b_oracle_driver.py`、第 4 回 probe `git show 7f38ac7fd:tools/t2273_replica_runner.py` 等 (read-only の git show は可)。

## レンズ A — 計測の妥当性と、(a) の実装形への忠実さ

親 brief は、候補 (a)「局所の写しを builder より前 (collection 中) に作る」の効果を、repo に入れない replica probe の隣接対で測る計画である。プランを守らず、次を攻撃せよ。

1. (P1) の見立て「第 4 回 replica の pre 約 130 秒は bytecode / rewrite cache が冷だから」は一次資料で支えられるか。他の説明 (plugin の import、資源標本、smoke、`_collect_login_universe` が replica に無いこと、早期 memo prewarm の発火条件 D2061 の (2) shard spec が replica で成立しているか等) を挙げ、どれが pre を 2 倍にしうるか。login で温める手順が実受入の状態を再現するか (何を温め、何は温まらないか)。温めで clean-tree 検査・受理集合が変わらないか。
2. (P2) の P 条件は、(a) を実装するときの自然な形 (controller の早期 job) を忠実に写しているか。controller 側 thread の GIL・xdist 制御 loop への影響、worker 側の identity と一致するか (testrunuid の取り方)、共有置き場の作成・削除 (`_T080SharedBases` の lifetime lock、最後の worker の削除) と写しの寿命が衝突しないか、非共有 builder (`test_t080_shared_base_builds_real_builder_once_across_processes` 系) にどう効くか。
3. 有効性の条件: A と P で「builder ごとの複製結果が同一」をどう観測すべきか (実関数の戻り値は P の builder では呼ばれない)。複製の metadata (mtime・mode) 差が test の outcome に効く経路はあるか。
4. (P2') 早期 memo 待ちの帰属規則は妥当か。P で memo 待ち超過が起きたとき、それを「P の失敗」と数えることで判定が歪む経路。
5. 判定規則 (有効 3 対すべて Δ>0 ∧ 対率中央値 ≥ 10 %) と順序 (A,P / P,A / A,P、同一 job 内隣接、job は逐次) の妥当性。同一 job 内の後走 warm (Lustre client cache・page cache) が P / A のどちらを有利にするか。
6. (P4) 発行 subprocess の内訳計測の方法 (child の code を観測 wrapper で包む) が、child の `-I -B`、import closure 検査 (`module.__loader__` が `_CurrentSourceLoader`)、`sys.path` 検査を壊さずに実現できるか。壊すなら代案。
7. brief の file:line の誤り、親の実測値 (第 4 回・前回の数値の引用) とその一般化の誤り。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` — 各所見に ID (A1, A2, ...)、重大度 (must-fix / should / nit)、根拠 (file:line か資料の節)、放置時に診断の結論 (効果の値・推奨) がどう変わるかを 1 行、推奨する修正。
- `## brief への異議` — (P1)〜(P4)・(P2') ごとに 同意 / 修正 / 撤回。
- `## 総括` (3〜6 行、GO / 修正後 GO / NO-GO)
