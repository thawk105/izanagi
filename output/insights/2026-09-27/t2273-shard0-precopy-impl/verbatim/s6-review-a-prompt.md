単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s4-ruling.md — 段 4 裁定 (プラン v2、変異 P0・M1〜M7 の事前登録、計測の事前登録、ユーザーの計算量回答)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s5-author-l.patch — レビュー対象の実装差分 (wave 木の commit `677ea17b6` と同一)。wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy で `git show 677ea17b6` でもよい。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s5-author-l-out.md — 実装子の報告 (M4 は mask ありと自己申告)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/probe/ — 計測 probe (repo 外、Codex author)。移植元 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/ との差分だけを見ればよい。報告は codex/s5-author-p-out.md。
- wave 木の orchestrator/tests/conftest.py、orchestrator/tests/test_s8b_oracle_driver.py、orchestrator/tests/test_real_repo_serialization.py の該当範囲。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。

## レンズ A — 正しさ境界・整合・変異の帰属・計測の妥当性

実装を守らず、壊れる点を探せ。特に:

1. fixture に届く集合・bytes・mode・mtime が現行 (実 repo からの直接複製) と変わる経路。写しの時点差以外の差があるか。
2. controller 背景 thread: `importlib.import_module("orchestrator.tests.test_s8b_oracle_driver")` が本番の受入 controller (cwd = repo root、`tools/run_tests.py` 経由) で成功するか、`module.ROOT != repo_root` が偽陽性で赤になる経路 (symlink、別 checkout)、thread の例外・`result.json` 書込み失敗・join・削除の順序。`_finish_memo_sessions` が呼ばれる全経路 (unconfigure、失敗経路、`suppress_errors`) で写しが確実に消えるか、worker 終了前に消える経路が無いか。
3. worker 側 helper: `PYTEST_XDIST_TESTRUNUID` と `str(ROOT)` から導く dir が controller 側と一致すること。dir が有るのに result が来ない・失敗の扱い。受入でない xdist 走 (焦点走・絞り込み) で dir が無いこと。入れ子の pytest / subprocess がこの dir を読む経路が既存の共有 base の扱いより広がっていないか。
4. T1 (`test_t080_visible_output_snapshot_starts_once_and_preserves_copy`): conftest を tmp repo へ複写して別名で読み込む形が、本物の hook の検査として妥当か (本物の conftest の module 状態と乖離しないか)。test module を `importlib.import_module` で取り直すことが pytest の collection 名と別 module 物になる場合の副作用 (module 水準の `_T080_SHARED_BASES` の再作成など)。xdist の worker 内で走らせても他 test と干渉しないか (`tempfile.tempdir` の差し替え、`PYTEST_XDIST_TESTRUNUID` の差し替え)。
5. 変異 P0・M1〜M7 (s4-ruling) の単一理由性を、実装の実際の行で検証せよ。M4 は実装子が「`mkdir(exist_ok=False)` の衝突が先に起きる」と申告している。M4 の再照準案 (例: 1 回性の guard を外し、同時に `exist_ok=True` にする 2 置換) と、その場合の kill 理由 (spy 2 回) を示せ。各変異の置換 old 文字列が実装内で一意かも確かめよ。
6. 計測 probe: 移植元からの差分が s4-ruling の計測の事前登録 1〜8 と一致するか (E1 の集合版、4 通り区分、5 分判定、赤の自動 infra 化なし)。移植で壊れた直書き (job dir、slug、import 名) の取りこぼし。

## 出力形式

見出し「## 所見」(各所見に ID A1〜、重大度 must-fix / should / nit、file:line、根拠、修正案)、「## 変異の再照準」(ID ごとに old / new 文字列の案と kill 理由)、「## GO 判定」(GO / 修正後 GO / NO-GO と 1 行理由)、「## 総括」(5 行以内)。
