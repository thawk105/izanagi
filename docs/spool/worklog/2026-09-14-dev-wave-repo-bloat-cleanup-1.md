---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-repo-bloat-cleanup
seq: 1
title: リポジトリ膨張を実測し、tracked file の削除確定が 0 件であることを 3 経路で確定した (docs のみ、branch worktree-dev-wave-repo-bloat-cleanup)
---

## 本文

- **ユーザー直接依頼で起票した wave。** 「リポジトリが大きく膨らんだ。あってもなくても研究に
  影響がほとんどないテスト・記録が膨れ上がっているはずだ。慎重に調査し、慎重に掃除してほしい」。
  次の一手台帳に対応する既存 item が無いため、題に ID を付けていない。
- **結論は削除 0 件。** 親の実測、段 2 plan、段 3 の敵対相談 2 レンズが独立に一致した。
  実測と根拠は `output/insights/2026-09-14/repo-bloat-audit/README.md`、子の逐語は同 `verbatim/`。
- **依頼の仮説は記録側について概ね成立しなかった。** tracked 24,684 件 / 約 690 MB のうち
  `output/` が 601,392,319 bytes / 21,965 件を占めるが、重複 blob の大きい群は
  `hash_ledger.json` と bundle manifest が現物で pin しており、`job-staging` 1,206 件は
  他所に同一 blob がゼロで実行コード 4 か所から参照される。0 byte file 2,838 件も
  読まれている fixture・台帳を含む。committed build artifact は 121,111 bytes しか無かった。
- **テスト側は「増えた」は真、「不要」は未証明。** 受入台帳は 14,467 件 / 5,364.9 秒 (D747 実測日)
  から 23,105 件 / 15,306.6 秒 へ、件数 1.60 倍・直列 work 2.85 倍。`orchestrator/tests` は
  同期間に正味 +265,519 行。しかし本体 AST 一致で拾った群のうち現物検分した 10 群はすべて
  入力・module・呼出先が異なる非重複だった。**親の provisional 裁定 (P1-b)「テストについては
  仮説は概ね真」を撤回した。**
- **D747 は母数 2.85 倍でも成立する。** `< 0.01 秒` が 12,223 件で合計 25.8 秒、
  `>= 10 秒` の 372 件が 8,256.0 秒 (全 work の 53.9%)。件数の 53% を消しても直列で 25.8 秒しか減らない。
- **親の brief の誤りを段 3 が 4 件指摘し、すべて採用した。** (1) 削除条件 (a)
  「どこからも参照されない」は過剰で、D1941 の「歴史的言及 ≠ 現役 pin」に反する。
  (2) `DW-O11` の空確認を全 tracked 削除へ課したのは過剰一般化で、原文は `output/` 配下の
  一括削除に対する条件である。(3) `output/insights` 直下を「559 日付 dir」と書いたのは誤りで、
  実際は 559 entries = 264 directory + 295 file、日付だけの dir は 46。(4) 受入・実測環境を
  login node 限定にしたのは不適切で、runner が資源量で実行場所を決める。
- **(P1-a) と (P1-c) も弱めた。** 「output について仮説は概ね偽」は飛躍であり
  「大部分は現役 pin または実測記録で、削除可能と示せたものは無い」へ改めた。
  「台帳の bytes = 毎セッションの読み込み費用」は現行の部分読み導線と一致しないので撤回した。
  checkout・検索の所要は測っていないと明記した。
- **唯一の真の重複は test 1 件 124 bytes だが、実施しないと裁定した。**
  `orchestrator/tests/test_related_work_search.py:1978` は同 file:1581 と同一述語である。
  段 3 sol は削除可能側と判定し、段 3 luna は「124 bytes を削った実績を作るため未確認を
  無影響と扱うな」と反対した。親は `DW-G05` (成果物影響を書けない変更は must-fix にしない) で
  luna を採り、実装面の差分ゼロで閉じた。段 5・6 を飛ばし変異 matrix を免除した。受入全走は実走した。
- **削除できない代わりに、実際に大きい無駄を特定した。** worktree 42 本 (1 本 774 MB)、
  local branch 44 本。取り込み済み worktree 26 本のうち非占有 23 本だが、
  **`git status` が空なのは 3 本だけで 23 本は Codex 実装子の未 commit 編集を抱えている。**
  「取り込み済み × 非占有 × 非 lock × clean」を満たすのは `dev-wave-t1875-delta-min-gate` の
  1 本だけだった。段 3 の「18 本・約 14 GB が撤去可能」という親の推計は、この dirty 検査で覆った。
- **「lock が撤去不能を作る」は refuted。** `tools/dev_wave_cleanup.py:943` は自対象の lock を
  解除する。残置は land と cleanup の分離 (D702) と、cleanup が親の生存に依存する設計による。
  原因未確定の 23 本を一括して新しい failure 型にはしない ({{D:worktree-residue-needs-owner}})。
- **別 session から受入律速の実測が届き、親が現物で検算して一致した。**
  `orchestrator/tests/test_s8b_oracle_driver.py:1003` が orchestrator 全体を、`:1006` が
  git 可視 `output/` 全件を fixture ごとに複製する。`:873` の docstring は
  「36MB / 2300 ファイル」だが、今日のコピー元は 22,994 件 / 639,961,594 bytes である。
  **`output/` が削れないことは、解を「fixture のコピー対象を絞る」側へ確定させる。**
  ただし `:1302` と `:1328` が全件性そのものを検査しているので、絞る変更はその 2 件を赤にする。
  相手が当初報告した「最遅 shard は shard-0」は D1918 の shard-2 と食い違ったため裏取りを求め、
  相手が 112 走で shard-0 103 走 (92%) を示し、**親も独立に直近 53 走を数えて shard-0 49 走
  (92.5%)、最遅 shard の wall が 300 秒超 53 走中 52 走を確認した。** D1918 の前提は失効している。
  この記録は相手の wave が残す。
- **受入 attempt 1 が、この wave の主題を実演して赤になった。** 23,308 passed / 68 skipped /
  6 error、子 rc=1、受領証未発行 (待ち手 rc=70)。6 件はすべて
  `test_t1259_qsub_env_delivery_probe.py` の setup error で、
  `git -C <wave worktree> ls-files --others --exclude-standard -z` の 30.0 秒 TimeoutExpired。
  同 tip・同 file の単独再走は 51 passed / 16.67 秒 / rc=0 で非再現。
  **親が同 argv を 3 連続実行した wall は 34.60 / 24.96 / 15.90 秒**で、30 秒の境界を跨いでいた
  (load average 68.35〜88.49)。F945 の 3 度目の観測として再発を追記し、恒久対応は変えず
  `DW-O18` に従って受入を再走した。**膨張が受入 gate を間欠的に壊す段階に来ていることの実測である。**
- 段 2 に codex plan 1 本、段 3 に consult 2 本 (sol / luna) を使った。実装子は起動していない。

## 次の一手差分

### 新規

- {{T:worktree-residue-retirement}} **P1・ユーザー裁定待ち**: 撤去候補
  `.claude/worktrees/dev-wave-t1875-delta-min-gate` (取り込み済み・clean・非占有・非 lock) の
  撤去可否と、`dev-wave-t2267-exec-site-class` (同条件だが locked) の扱いを裁定する。
  実行には対象を限定したユーザー指示と `/cleanup-branches` の起動が要る (D204 / D854 /
  cleanup-branches §0)。残り 23 本は未 commit 差分があり撤去対象外。
- {{T:worktree-residue-permanent-fix}} **P2・裁定待ち**: 親の生存に依存しない worktree 回収経路を
  作るか、残置を許容するかを裁定する。根拠は {{D:worktree-residue-needs-owner}}。
- {{T:duplicate-tier-api-test-removal}} **P3・着手可能**: `test_related_work_search.py:1978` の
  重複 test 1 件 124 bytes を削除する。`conftest.py:1502-1539` の台帳 validator が
  `nodeid_count == len(durations)` を要求するので、行と件数を同時に整合させる。
  着手点は `output/insights/2026-09-14/repo-bloat-audit/README.md` §3.2。
- {{T:oracle-driver-fixture-copy-scope}} **P2・別系列所有**: `test_s8b_oracle_driver.py` の
  fixture が git 可視 `output/` 全件を複製する構造を絞る。受入 wall 短縮系列 (D1894 / D1918) の
  所有であり、本 wave は記録だけを残す。`:1302` と `:1328` の全件性検査を同じ変更単位で扱う。
