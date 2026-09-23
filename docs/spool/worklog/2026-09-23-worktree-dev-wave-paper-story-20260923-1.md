---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: worktree-dev-wave-paper-story-20260923
seq: 1
title: 論文ストーリー 2026-09-23 版を作った — 起点 65fd1422f までの正典 (entry 1819〜1846、D2219〜D2234) を反映し、§3・§6・§7・§8 を導き直した。K2 の同 job 対照の成立、TPC-C 段 1 の silo trace の certified、関数単位の軸の段階 C・D、B-5 本走と pin 候補 C の認可を、記述値・認可・公開 API の判定として限定して書いた (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-paper-story-20260923)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260923/verbatim-request.md`): 2026-09-22 版以後の着地を正典から読み直し、§3・§6・§7・§8 を更新して `docs/paper-story/2026-09-23.md` と README の版の表を書く。ComSys 原稿と図は触らない。版 = `docs/paper-story/2026-09-23.md`。
- 起点 = local main `65fd1422f` (fresh worktree、開始 gate rc=0)。軽量版 (段 2・3 なし、実装面の差分ゼロで変異 matrix は免除、段 6 は一次資料の再抽出を含むので Codex read-only レビュー 1 本)。submodule 初期化は 1 回目 `update-no-fetch` (30 秒 timeout 型)、再走で rc=0。
- **親の provisional 裁定 (段 1):** (P1) 依頼の列挙は entry 1831〜1844 だが、README の運用契約 (新しい日付の版はその日付時点の正典全体からの導出) に従い、前版の起点 `8fd2a2f5c` より後の 1819〜1846 全体を反映した。(P4) 依頼は「README の版の表だけ」だが、stale 注記節に積まれていた 4 件を版が本文へ取り込んだので、移管先を示して節を空に戻した (積んだままだと節の定義に反する)。段 6 レビューはどちらも README 契約に沿うと判定した。
- 版の作り方: 前版を複製して時点語を機械置換 (「前版」→「2026-09-21c 版」269 件、「この版」→「前版」222 件) し、継続の主張 17 か所を「前版でもこの版でも」へ延ばした。冒頭・§0・§10 は差し替え、§3・§6・§7・§8 を導き直し、§1・§2・§4・§5・§9 は起点で偽になった状態語 (「未 push」「今も真」など) を直した。§7 は前半 133 項 + 後半 8 項 = 141 項。見出しの禁止句そのものが起点で真になった項 (TPC-C の段の分割、K2 の pair の成立、B-5 本走の認可ほか) は、見出しを書き換えず「前版の起点までの規律」と読む範囲を更新文で示した。
- 段 6 (Codex `gpt-6-sol` read-only レビュー 1 本、20:22〜20:26 JST): NO-GO、must-fix 2 (certified の保証範囲を YCSB に無条件で限る文が TPC-C 段 1 の公開 API での certified と矛盾、§9 の論文用結論が K2 を未成立・B-5 を未認可と現在形で書く)。親は 2 件とも real と裁定して直した。P1・P3 (訂正 0 件)・P4・項数・置換件数への攻撃は不成立。焦点再レビュー 1 巡目 (20:27〜20:29 JST) は GO (M1・M2 とも closed、新規所見 0)。
- 記録前検査: 三軸語の走査器 (`s8b_holdout_freeze search`) は rc=1 だが、holdout の hit は main に既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file だけで本 wave の file は 0 件 (paper-story の図 provenance 6 件は陽性対照の hit)。`check_docs` 違反なし、`git diff --check` 指摘なし、fold の dry-run は planned、版が引く path の実在確認 (304 path、欠けて見える 5 件は旧版から運んだ雛形表記と削除済み文書)。受入全走は記録 commit の後に行い、結果は land の受領証に残る。
- 親の誤り (near miss、land 前に閉じた): 段 6 の fix commit を `git commit -m` の 3 分割で作り、AI-Agent trailer が最終段落に入らず全史 provenance 監査が新規違反 1 件 (rc=1) を出した。forward correction の枠は消費済みなので、未共有のうちに `20db3244d` へ soft reset して記録 commit と 1 つにまとめて作り直した (fix の内容は同じ)。wave branch の reflog に旧 commit が残るので、land 後の自己撤去は rc=20 で拒否されうる。
- **受入 attempt 1 (tested main `620a6bb13`、tip `9a616cf84` = main の前方 merge 後、20:44〜21:07 JST) は赤 1 件で rc=70、非帰属と判定した。** 赤は `orchestrator/tests/test_dev_wave_cleanup.py::test_remove_child_detached_ancestry_and_empty_backup` だけで (1 failed / 27,509 passed / 74 skipped)、本文は「occupancy result is indeterminate or inconsistent; … issues=[{"error":"missing","source":"cwd",…}]」(占有検査の `/proc` 走査中に他 process の cwd が消えた競走、entry 1829・1834・1835・1839 と同じ型)。本 wave の差分は docs と spool fragment だけでこの試験から到達しない。同じ tip で 1 件を `tools/run_tests.py` で単独再走して 1 passed (7.70 s) で再現しない。hold 登録簿へは登録しない。本追記を含む tip で受入を取り直す。
- 受入の前方 merge で取り込んだ main `620a6bb13` に第 33 回 /rulings (D2235、20:06 JST) が着地していた。依頼が起点を着手直前の main に固定したので版は動かさず、版の記述を古くした 2 点 (TPC-C の ccbench branch `izanagi-tpcc-v3-trace` が 09-23 08:4x JST に人間の push で公開済みだったこと、関数方策の軸は段階 E の前に既知最良との小比較を 1 回走らせること) を README の stale 注記に 1 項として積んだ。受入 3 回目 (tested main `3204c8186`、tip `6fbddd98c`、21:45〜22:03 JST) は child-green (27,510 passed / 74 skipped) だったが、その後に [T-2864] の ADRS 判定 (entry 1849) と [T-2858] の pin 前進 (entry 1850、gitlink `e9e477ca` → `68106660`) が着地し、どちらも版の記述 (「ADRS は正典で未判定」「gitlink は `e9e477ca` のまま」) を古くしたので、main `973db24ed` を取り込んで 2 項を stale 注記へ足し、受入を取り直した (受入 2 回目は試験前に main の前進との競走で postcheck rc=70、計算未使用)。land 1 回目 (22:05) は main checkout の dirt (並走 wave の処理中) で rejected、main は不変。
- 工数: Codex 子 = review 1 本、focus 1 本。Claude の子は使っていない。計算ノードは受入のみ。

## 次の一手差分
