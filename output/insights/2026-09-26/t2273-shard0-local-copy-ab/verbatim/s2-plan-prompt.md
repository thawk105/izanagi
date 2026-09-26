単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s1-brief.md — 親の段 1 brief ((P1)〜(P5)、不変条件、受入・実測環境)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/verbatim/T-2273-origin.md — 依頼の逐語。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/verbatim/D2044-item15.md、D2068.md、D357.md — 既裁定の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md — 第 4 回診断 (結論 1〜8、§4 限界)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py — `_run_git_bytes` (794 行付近)、`_git_visible_output_paths` (814)、`_copy_git_visible_output` (847)、`_t080_remove_tree` (903)、`_T080SharedBases` (920)、`_t080_join_shared_bases` (975)、`_t080_stub_free_e2e_repo` (995)、`t080_shared_cache_probe` 以降の shared base test 群 (1036〜1230 付近)、`_build_t080_stub_free_e2e_repo` (1437、1458 行が差し替え対象)、`test_t080_output_copy_visibility_matches_production_enumeration` (1899)、`test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` (2003)。必要な範囲だけ grep / sed で引く。

## 目的

自分たちの受入 test 基盤の高速化の実装プランを起草せよ。対象は T-080 stub-free E2E fixture の共有 base builder が、実 repo (Lustre) の `output/` 可視集合を builder ごとに複製している箇所 (1458 行) である。第 4 回診断では、session 内で 8 本の builder が同時にこの複製を行い、複製元を node-local に差し替えた対照で shard-0 の W_0 が −123.9 秒だった。本 wave は brief の (P1)〜(P5) の形 (xdist session ごとに共有置き場へ 1 回だけ写しを作り、builder は写しから局所複製) で実装する。

brief の (P1)〜(P5) は親の provisional 裁定であり、より単純で等価な形があれば示してよい。ただし次は不変:
- 複製される集合と bytes (fixture の root/output の中身) は現行と同一。D2068 の却下 3 案 (whitelist / alternates / 独立 index) と圧縮設定に触れない。
- `_copy_git_visible_output`・`_git_visible_output_paths` の本体と、`test_t080_output_copy_visibility_matches_production_enumeration` の全件性検査 2 か所 (1983〜1984 行、1994〜1998 行) を変えない。
- 既存 test の期待値を変えない。受理集合を変えない (規律 2)。
- 仮想リスク向けの gate・検査・台帳・一般化・互換層を足さない。新機構の正例 test は最小 (1〜2 本) にする。
- 変更 file は原則 `orchestrator/tests/test_s8b_oracle_driver.py` の 1 file。

## 書くこと (file:line 粒度)

1. 変更点の一覧: 追加・変更する関数/メソッド、呼び出し箇所、lock・完成 marker・残骸処理の扱い (既存 `_T080SharedBases.get` の flock + complete.json + `_t080_remove_tree` の型に揃えるか)。写しの path 規約と、session 共有置き場 (`_T080SharedBases.parent`) の削除との関係。
2. 単独走 (`_T080_SHARED_BASES is None`) と、`t080_shared_cache_probe` が `_T080_SHARED_BASES` を test 局所に差し替える場合の挙動。`t080_small_cache_builder` を使う test 群 (builder を mock) と、`test_t080_shared_base_waits_for_builder_lock` の flock 観測 (LOCK_EX を全部観測する) に波及しないか。
3. 写しから builder への複製で metadata (mode・mtime・symlink) が現行 `shutil.copytree` (copy2) と同じになるか。写しを作る関数が返す visible 集合を builder が使っているか (現行 1458 行は戻り値を捨てている)。
4. 未 commit の可視 file (modified tracked / untracked) の扱いが現行と同じになる理由。写しを作る時刻の違い (builder ごと → session で 1 回) で変わる挙動の列挙。
5. 追加する test (最小): 何を正例として固定し、どの変異を殺すか。変異候補 (段 4 で事前登録する) を 3〜5 個、位置と期待 kill node 付きで。各変異が単一理由で赤になるか (他層の mask が無いか) も書け。
6. 既存の consumer test・inventory test (helper consumer の AST 検査 1390〜1435 行付近など) への静的波及の列挙。
7. 効果の見込みで言えること / 言えないこと (1 本の写しの生成が Lustre 上で何秒かは未測定。診断の staging 43.9 秒は git clone で方式が違う)。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## プラン` (上の 1〜7)
- `## brief への異議` (brief の (P1)〜(P5)・不変条件・計測計画への反論。無ければ「なし」)
- `## 総括` (3〜6 行)
