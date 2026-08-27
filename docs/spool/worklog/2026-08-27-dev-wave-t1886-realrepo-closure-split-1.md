---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1886-realrepo-closure-split
seq: 1
title: [T-1936] real-repo 排他閉包の穴 7 点を閉じ、受入 wall の床が排他鎖でないことを実測した (コード + docs、branch worktree-dev-wave-t1886-realrepo-closure-split、変異 matrix = baseline PASSED・KILLED 9/9・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「[T-1886] と [T-1936] を 1 つの変更単位で扱い、受入 wall の床を排他閉包の細分化で下げる。
  D1035 が細分化を選んでいるので個別テストの高速化に流れないこと」だった。
  **細分化の側は実装していない。既に実装済みだったからである。**
- **[T-1886] の前提が崩れた。単一 `real-repo` 直列鎖は実行時に存在しない。**
  `orchestrator/tests/conftest.py` の collection hook が、process memo 4 本を除く全 real-repo node から
  `@real-repo` suffix を除去する。xdist 3.8.0 の `LoadGroupScheduling._split_scope` は suffix の無い
  nodeid を full nodeid scope として扱うので、残りは 1 node = 1 work unit になる。
  既存テストの docstring も
  `Historical name: only the four process-memo nodes remain one work unit` と書いていた。
  この形は **D1008 (2026-08-26) が既に決定・実装し、D1103 (2026-08-27) が K=3 を実測している。**
- **親が因果的に実測した。** ledger 合計 266.32 秒の 90 node 集合を `tools/run_tests.py` 経由で
  走らせると **pytest wall 74.91 秒**で終わった (Pegasus 自動 dispatch request `951549.nqsv`、rc=0、
  52 passed / 41 skipped)。**合計の 3.6 分の 1 である。この集合は直列鎖を作っていない。**
  210.5 秒 / 258.92 秒 / 266.32 秒はいずれも marker 付き node の所要の**総和**であって、
  直列鎖の長さでも wall 短縮量でもない。D600 と D1052 がまさにこの型を禁じている。
- **したがって [T-1886] は不採用にせず、新事実を添えてユーザー再裁定へ戻した** (`DW-S04`)。
- **親 brief の中心的前提 (P1) は段 2 プランが反証した。** 親は brief に
  「単一 group が 90 node を 1 worker へ閉じ込める」と書いたが、現物と一致しない。
  親は xdist の実装と既存テストの docstring を自分で確かめて受け入れた。
- **親の実測にも誤りが 2 件あり、親自身と段 3 レンズ B が見つけた。**
  (i) ledger 集計で `@real-repo` suffix 付き key を別 node として数えており、
  合計 258.73 → 258.92 秒、writer 1 本が 0.00 → 0.19 秒。
  (ii) parametrize instance まで正規化すると 93 instance / 266.32 秒で、ledger 欠落 family は 0 件。
- **「排他 writer は 0.00 秒」は regime 固有の言明だった。** `(read, write)` の 3 本は
  `cmake` / `gcc-13` / `g++-13` / `nm` を要求する `skipif` 付きの slow real-build canary で、
  **この login node には `gcc-13` / `g++-13` が無い** (親が実測)。固定 toolchain のある
  計算ノードでは走って実 build cache へ書く。転移させてはならない。
- **[T-1936] の閉包の穴は 3 点ではなく 7 点だった。** 依頼が名指しした 3 点に、段 2 が 1 点
  (`current_commit_snapshot` module fixture)、段 3 レンズ A が 2 点 (suite 全体を subprocess
  collect する node、controller prewarm)、段 6 レビュー B が 1 点 (3 本目の全 suite collect node、
  台帳 14.0 秒) を足した。
- **偽赤の機序を親が独立に確定した。** `test_t810_coordinator.py` の node は
  `REAL_REPO_CLASSIFIED_NODES` (92 件) に 1 つも入っていないのに、
  `tools/pegasus/t810_coordinator.py` の `repository_roots_from_git_identity` が
  親 Git common-dir 配下の `worktrees/*` を列挙して各 `gitdir` を読む。他 wave が
  `git worktree add` している最中は「管理 dir はあるが `gitdir` は未書込」の窓があり、
  そこで落ちる。**本 wave の起動時にも別 wave の `git worktree add` が進行中だった。**
- **段 2 plan の中心設計を親が却下した。** plan は長寿命 fixture 15 本を canonical `real-repo`
  group へ統合する案だったが、費用を実測すると `s8c-preregistration-candidate` 83.5 秒と
  `s8c-predicate-snapshot` 52.0 秒が**現在は並行に走っている**ものを 1 worker 上の 135.6 秒の
  直列鎖に変える。5 分の絶対上限の余裕を半分近く食い、D1035 の方向とも逆である。
  代わりに group を分けたまま shard の衝突辺で同一 shard へ寄せる形にした ({{D:realrepo-conflict-edges-same-shard}})。
- **段 6 の敵対レビュー 2 本が独立に別の BLOCKER を出し、全件 real と裁定して land 前に直した。**
  レビュー A は「module scope の共有 fixture を保持したまま同 module の function scope の
  排他 fixture へ入ると、別 fd を開くため 245 秒 timeout で自滅する」を、
  レビュー B は「common-dir を解決する `git rev-parse` が旧・新どちらの lock も取る前に走っており、
  読取り自体が無保護」を出した。前者は {{D:realrepo-lock-manager-per-process}}、
  後者は {{D:realrepo-lock-key-common-dir}} で閉じた。
- **段 5 実装子の「選択・skip・期待値・受理集合は変更していない」という申告は事実と違った。**
  段 6 レビュー B が差分で反証した (collection が 10 node 増え、11 node の marker が変わっている)。
  実際には skip は不変、collection は 10 node 拡大、marker と配置と一部期待値は意図的な変更である。
  詳細は {{F:implementer-claimed-unchanged-acceptance-set}}。
- **1 本目の fix 子は、レビュー A が求めた「function scope を検査へ含めよ」を、
  状態共有を前提とする別の検査にまで広げて赤を出した** ({{F:fix-widened-wrong-candidate-set}})。
  親は「候補集合の取り違えであって閉包の穴ではない」と裁定し、2 本目の fix 子で
  候補集合だけを session / module scope へ戻した。検査の削除・緩和・allowlist は禁じた。
- **D358 の却下理由の生死を分けて記録する。** (a) 未抑止の Git 呼出しは**生きている** —
  real-repo node から `GIT_OPTIONAL_LOCKS=0` 無しで起動される git が 6 family 残る。
  (b) 閉包未確定は本 wave で閉じた。(c) worker 跨ぎの fixture 重複は存在するが、
  wall を悪化させるという却下理由自体は D1008 が実測で退役させている。
  **(a) は本 wave では直さなかった** — D1008 が出荷した設計の既存性質であり、
  `test_s8b_*` は稼働中の別 wave の編集面だからである。ユーザー裁定へ送った。
- **codex 子の工数: 8 本** (plan 1 / consult 2 / author 1 / review 2 / fix 2)。いずれも
  `gpt-5.6-sol` / `reasoning=xhigh`、rc=0、`check_codex_output.py` rc=0。
  **実装子と fix 子はいずれも sandbox から計算ノードへ dispatch できず
  (`qstat -Q preflight rc=1`)、pytest を 1 件も走らせられなかった。** 実測はすべて親が行った。
- 親の焦点走 (13 file、`tools/run_tests.py` 経由で計算ノード dispatch) は
  段 5 後が 4 failed / 1180 passed、1 本目の fix 後が 1 failed / 1184 passed、
  2 本目の fix 後が **1185 passed / 7 skipped / rc=0 (pytest 95.83 秒)**。
- 変異 matrix は anchor `cf1a5c9202f1ac2732545e7f0e43e1a0e27365ab`、`--runner-mode dispatch`。
  probe (全件 SURVIVED 期待) で観測 node を延べ 16 件集めてから本走し、
  **baseline PASSED、KILLED 9 / 9、SURVIVED 0、MISMATCH 0、TIMEOUT 0。**
  閉包の穴を復活させる 2 変異は独立に 3 本の検査が殺した。
- 起動時の編集面重複検査では、指示にあった稼働中の t1805 は私の編集面に対して差分ゼロだった。
  `conftest.py` には別 branch 2 本が未着地の差分を持つ。
- **段 8 の裁定。** 改善候補は 2 件 ({{F:implementer-claimed-unchanged-acceptance-set}} と
  {{F:fix-widened-wrong-candidate-set}}) で、どちらも単発事故である。しかも
  **どちらも既存の機構が実際に捕まえた** — 前者は段 6 の敵対レビューが差分で反証し、
  後者は親が fix 後に焦点走を実走したことで出た。子の自己申告を実測で置き換える型は
  failures 台帳に既に複数の先例と恒久対応があり、本 wave はその機構が働いた事例である。
  `DW-G03` に従い failures 台帳への記録に留め、command / reference の編集は見送った。
- 受入全走は本エントリの記録 commit の後に投入するため、本エントリには結果を書かない。
- 一次資料は `output/insights/2026-08-27_t1886-realrepo-closure/`。

## 次の一手差分

### 完了

- [T-1936] `real-repo` 排他閉包の穴を閉じた。依頼が名指しした 3 点に段 2・段 3・段 6 が
  見つけた 4 点を足した 7 点をすべて閉じ、変異 9 / 9 KILLED で裏を取った。
  remaining: none
  base: b37571b6d5c90ed86bb39f495c7fe03daf3c6d1e3506c8a024dbc9b664bede2b

### 更新

- [T-1886] **P1・ユーザー再裁定待ち**: D1035 が選んだ「排他閉包の細分化で床を下げる」は
  **D1008 と D1103 で先行達成済み**であり、本 wave に追加の性能介入は無い。
  裁定の前提だった「床は `real-repo` 排他鎖」は成立しない — 同じ 90 node の
  ledger 合計 266.32 秒に対し、実走の pytest wall は 74.91 秒である。
  台帳から落とすか、D1008 より先へ進む具体的な操作を新たに裁定するかを決めてほしい。
  base: 2d0c0396e174132ab10863424b8ef42b835c043792db089e46e6f747b7a9c02b

### 新規

- {{T:unprotected-git-optional-locks}} **P2・ユーザー裁定待ち**: real-repo node から
  `GIT_OPTIONAL_LOCKS=0` 無しで起動される git が 6 family 残る。D358 の却下理由 (a) は
  この意味で生きている。選択肢は (A) 全 live Git 経路へ抑止を入れて閉包を広げる、
  (B) D1008 が D358(a) を supersede したとして受容する、の二択。
- {{T:cross-host-realrepo-exclusion}} **P2・ユーザー裁定待ち**: `/tmp` の flock の保証は
  同一 host・同一 filesystem までである。並行 acceptance を別 host で許す運用のままにするか、
  共有 filesystem lock または worktree 隔離へ進むかを決める。
- {{T:function-fixture-realrepo-audit}} **P3・新規**: canonical node と共有される
  function scope fixture が実 repo へ触れているかを個別に監査する。
  本 wave では「function scope は consumer 間で実体を共有しない」という理由で
  共有 fixture 閉包検査の候補から外したが、fixture の**コード経路**が実 repo へ触れるなら
  consumer 側の登録が要るという読みも成り立つ。対象を数えるところから始める。
