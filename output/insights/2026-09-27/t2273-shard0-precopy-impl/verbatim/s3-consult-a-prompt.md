単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s1-brief.md — 親の段 1 brief ((P1)〜(P8))。**brief 自身も攻撃対象である。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md — 段 2 plan (攻撃対象)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/verbatim/ — 依頼の逐語 (T-2273-origin.md) と既裁定 D2253・D2242・D357・D2068・D2061・D2062 の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-precopy-ab/README.md と同 dir の verbatim/probe-source.md (`tools/t2273_replica_plugin.py` 節) — 診断で効果を示した P の形。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py (早期 memo 2360〜2500、`pytest_configure_node` 2583、`_finish_memo_sessions` 2964、`pytest_configure` 2979、`pytest_unconfigure` 3381) と orchestrator/tests/test_s8b_oracle_driver.py (814〜1033、1037〜1345、1437〜1470、1899〜2010)。必要な範囲だけ grep / sed で引く。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。

## レンズ A — 正しさ境界・整合・実効性

plan と brief を守らず、壊れる点を探せ。特に:

1. 受理集合・fixture の中身が現行と変わる経路 (集合・bytes・mode・mtime・symlink、除外 6 件、未 commit 可視 file)。写しの時点が configure_node 時に移ることの帰結が「受理集合を変えない」と言えるか。
2. worker への path の渡し方 (plan 推奨 = workerinput → worker の `pytest_configure` で専用の環境変数)。環境変数が test 内から起動される subprocess (入れ子の pytest、fork、発行 child 等) に継承されたとき、何が起きるか。session 終了後に消えた写しを読む・別 session の写しを読む・入れ子 pytest の builder が親 session の写しを使う経路があるか。より局所な渡し方 (module 属性、config 経由等) の可否。
3. controller 背景 thread での test module import: module 名 (`orchestrator.tests.test_s8b_oracle_driver`) と pytest の collection 時の module 名の一致、import 時の副作用 (`sys.path`、temp root 検査、`_t080_join_shared_bases`)、controller の main thread との GIL・import lock 競合 (早期 memo thread と xdist の gateway 管理を遅らせないか)。
4. 終了処理: join と削除の順序が worker の全終了後か、例外時に写しが残る・二重削除・join 前削除が無いか。controller が異常終了したとき worker が無期限に待たないか。
5. 失敗時の扱い (生成失敗・待ち超過で builder を赤にし直接複製へ戻さない) が、受入の赤率を上げて測定を壊さないか。180 秒上限の根拠 (DW-O13: 実測分布の max への倍率、regime の一致) は妥当か。
6. 変異候補 6 本の単一理由性 (他層の mask、spy の置き方で kill が別理由にならないか) と、正例 1 件で P の形 (collection と重ねる) を固定できているか。builder が実 repo を直接読む変異を確実に殺すか。
7. 実効性: 実装が診断の P と同じ時点・同じ所要になるか (thread 起動位置、import の所要が写しの開始を遅らせないか)。3 shard すべてで写しを作ることの影響。

## 出力形式

見出し「## 所見」(各所見に ID A1〜、重大度 must-fix / should / nit、file:line、根拠、修正案)、「## plan への修正案」、「## brief の誤り」、「## GO 判定」(GO / 修正後 GO / NO-GO と 1 行理由)、「## 総括」(5 行以内)。
