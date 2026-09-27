単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s1-brief.md — 親の段 1 brief ((P1)〜(P8)、不変条件、受入・実測環境)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/verbatim/T-2273-origin.md — 依頼の逐語。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/verbatim/D2253.md、D2242.md、D357.md、D2068.md、D2061.md、D2062.md — 既裁定の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-precopy-ab/README.md — 対照診断 (P の形の効果、結論 1〜7、§4 限界)。
- 同 dir の verbatim/probe-source.md の `tools/t2273_replica_plugin.py` 節 (`controlled_copy` / `copy_from_snapshot`、`pytest_configure_node`、`pytest_unconfigure`) — 診断で測った P の形 (対照用の差し替え。repo には入っていない)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md — 前回 (D2242、不採用) の実装・変異・実受入。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py — 早期 memo: `_EARLY_MEMO_*` と `_early_memo_selected` (2360〜2386 行)、`_start_early_memo_job` (2388)、`_wait_early_memo_job` (2469)、`_finish_early_memo_job` (2488)、`pytest_collection_finish` (2550)、`pytest_configure_node` (2583)、`_finish_memo_sessions` (2964)、`pytest_sessionfinish` (2745)、`pytest_unconfigure` (3381)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py — `_run_git_bytes` (794)、`_git_visible_output_paths` (814)、`_copy_git_visible_output` (847)、`_t080_remove_tree` (902)、`_T080SharedBases` (920)、`_t080_join_shared_bases` (974)、`_T080_SHARED_BASES` (992)、`t080_shared_cache_probe` 以降の shared base test 群 (1037〜1345)、`test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5` (1346)、`_build_t080_stub_free_e2e_repo` (1437、1458 行が差し替え対象)、`test_t080_output_copy_visibility_matches_production_enumeration` (1899)、`test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` (2001)。必要な範囲だけ grep / sed で引く。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。

## 目的

自分たちの受入 test 基盤の高速化 (受入 shard-0 の律速 = T-080 stub-free E2E fixture の共有 base builder が実 repo (Lustre) の `output/` 可視集合を複製する時間) の実装プランを起草せよ。形は D2253 項 2 で確定している: 既存の早期 memo prewarm と同じ controller の `pytest_configure_node` で背景 thread を起こし、実関数 `_copy_git_visible_output` を session で 1 回だけ実 repo に呼んで session 所有の写しを作り、共有 base の builder はその完成を待ってから写しから局所複製する。D2242 の「最初の builder が作る」形は流用しない。

brief の (P1)〜(P8) は親の provisional 裁定であり攻撃対象。より単純で等価な形があれば示してよい。ただし次は不変:
- 複製される集合と bytes・metadata (fixture の root/output の中身) は現行と同一。D2068 の却下 3 案に触れない。
- `_copy_git_visible_output`・`_git_visible_output_paths` の本体と全件性の検査 2 か所を変えない。関数を別 module へ移さない (実関数を呼ぶ)。
- 既存 test の期待値を変えない。受理集合を変えない (規律 2)。早期 memo の挙動を変えない。
- 仮想リスク向けの gate・検査・台帳・一般化・互換層を足さない。新機構の正例 test は最小にする。
- 変更 file は `orchestrator/tests/conftest.py` と `orchestrator/tests/test_s8b_oracle_driver.py` の 2 つを上限とし、他 (台帳・inventory 等) への波及があれば必要性を示して列挙する。

## 書くこと (file:line 粒度)

1. 変更点: 追加する関数・定数・呼出し箇所。controller 側 (thread 起動の位置と条件、写しの path 規約、完成 / 失敗 marker、join と削除の位置 — `_finish_memo_sessions` との関係、例外の伝播) と worker / builder 側 (path の受け取り方、待ち方と上限、写しからの複製、写しが無いときの経路)。
2. controller で `_copy_git_visible_output` を得る方法 (test module の import を背景 thread 内で行う場合の module 名・二重 import・module 水準の副作用 (`_T080_SHARED_BASES = _t080_join_shared_bases()` が controller で None になるか) の検証)。`test_campaign_import_invariant.py` 等、conftest の import を検査する test への波及。
3. 発火条件 (早期 memo と同じ `_early_memo_selected` か別か)。shard 割付は worker の collection で決まるので controller は 3 shard とも写しを作る点の是非。非 xdist・`-n 0`・`-k` 等の単独走で従来経路になること。
4. 写し → builder の複製で metadata (mode・mtime・symlink) と集合が現行と同じになる理由。写しの時点が builder 開始時 → configure_node 時に変わることで変わる挙動の列挙 (D2242 段 4 A1 の裁定と同じ扱いでよいか)。
5. `t080_shared_cache_probe` が `_T080_SHARED_BASES` を差し替える test、`t080_small_cache_builder`、`test_t080_shared_base_waits_for_builder_lock` の flock 観測、`test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5` の AST 検査、real-repo access 登録 (`REAL_REPO_ACCESS_BY_NODE` 等)、`acceptance_duration_ledger.json`・growth / flaky hold 台帳への波及。
6. 追加する test (最小): 何を正例として固定し、どの変異を殺すか。変異候補 4〜6 個を位置と期待 kill node 付きで。各変異が単一理由で赤になるか (他層の mask が無いか)。
7. 待ち上限の値の根拠 (診断の写し生成 80.8〜103.3 秒、builder 開始は写し開始から 65.7〜70.7 秒、待ち 5.6〜27.1 秒) と、上限超過・生成失敗時の扱い。
8. 効果の見込みで言えること / 言えないこと (shard-1 / 2 の背景 I/O、早期 memo との競合)。

## 出力形式

見出し「## 変更点」「## import と発火条件」「## 波及」「## test と変異候補」「## 待ち上限と失敗時」「## 効果の見込み」「## 未決の設計択一」「## 総括」。各項目は file:line を付ける。「## 総括」は 5 行以内。
