---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t692-r3-xdist-walltime
seq: 1
title: [T-692] R3 の xdist 対応を実装し、受入 wall の律速が real-repo group の直列和であることを実測で確定した — 恒久策は分配側に無い (コード + docs、受入 7746 passed / 20 skipped / 1247.95 秒、変異 8/8 検出・SURVIVED 0、branch worktree-dev-wave-t692-r3-xdist-walltime)
---

## 本文

- **依頼の前提を 1 つ訂正した。** 依頼は「受入全走の pytest-xdist 対応」「並列化の可否」だったが、
  suite は**既に xdist で並列実行されている** — `tools/run_tests.py` が `--dist loadgroup` を
  既定付与し、計算ノードでは `site_policy.default_test_jobs` が cap 無しで affinity 全数 =
  **48 worker** を使う。問題は導入の可否ではなく現行分配の改善余地だった。
- **wall の律速を実測で確定した。** baseline (bnode055、7685 passed、wall 1407.97 秒) の
  junit を集計すると、直列総和 16534.55 秒に対し実効並列度は **11.74 worker 相当 (48 の 24.5%)**。
  `real-repo` group の直列和 **1388.80 秒**が critical path 下界で、実測 wall との差は 19.17 秒。
  **worker は余っており、並列度を上げても下界は動かない。** その 96.0% はたった 2 node
  (680.23 秒 + 653.50 秒) で、残り 41 node の合計は 55.07 秒しかない。
- **R3 原案の値段を数値化した。** R3 (実 repo 読み取りテストを同一 group へ寄せる) は
  **寄せた分がそのまま critical path に加算される**。[T-438] の 1 node で **+69.45 秒**、
  s8c candidate 3 node で **+58.35 秒**。R3 の目的 (フレーク除去) と依頼の目的 (wall 短縮) は
  同じ 1 本の直列鎖を取り合う。
- **恒久策は分配側に無い、と結論した。** 律速の正体は実 repo の T-080 receipt 解決で、
  `real_repo_receipt_memo.py` 自身が「commit 数に比例」と記録している。しかも 1 走で
  **構造的に 2 回**要る — 共有 memo 側 1 回と、CLI を別 interpreter で起動する
  `test_cli_subprocess_returns_rc_2_on_gate_refused` が払う production 経路 1 回。
  後者に test 側 cache を注入するのは規律 2 に反するため、wall ≈ `2q + tail` は分配では消せない。
  段 3 のレンズ B も独立に同じ結論に達した。裁定パッケージは
  `output/insights/2026-08-10_t692-xdist-walltime/package.md` の R-a〜R-e。
- **親の実測が段 3 で 1 件 refuted された。** 親は重量級 3 本を `-n 0` で走らせて
  「670 秒は競合による膨張」と分解したが、`junit-serial3.xml` の `hostname` は `pegasus02` =
  **ログインノード**で、baseline (bnode055) と機体が違った。`run_tests.py` が計算ノードへ
  dispatch するのは受入形だけである。分解は撤回し、残る主張を
  「単一プロセス内では最初の 1 本だけが解決を払い、以後は 2〜3 秒」に狭めた。
- **段 3 は 2 本とも NO-GO** (レンズ A: Critical 1 / Major 5、レンズ B: Critical 3 / Major 5 / Minor 1)。
  全 15 所見を real と裁定し refuted は 0 件。段 2 の推奨案 (収集順で 2 解決を重ねて約 876 秒) は
  「同時開始を仮定した条件値。非重複なら 1529.17 秒」と両レンズが計算したため、
  **期待値としては採用せず実測で返す**方針に切り替えた。
- **段 6 も 2 本とも NO-GO** (Critical 1 / Major 6 / Minor 2)。must-fix はすべて
  「ゲートが恒真で事前登録変異を単一理由で殺せない」型だった。fix を 3 巡回した。
  Critical (ungrouped payer が D63 閉包の外) は**本 wave の変更が作った穴ではなく既存**で、
  段 4 で裁定パッケージへ回した。
- **受入 1 走目が本 wave 由来の赤を 1 件出した。** `pytest_collection_finish` へ順序固定を
  足したため、`test_run_tests_task_run.py` の偽 item に `name` / `path` が無くて
  `AttributeError` になった。**テスト観測器側だけを直し**、production の hook は
  fail-open にしていない (順序固定が静かに効かなくなる経路を作らないため)。
  親の対象走行にこのファイルが入っていなかったのが検出漏れの原因である。
- **wall は縮んだが、断定はしない。** 変更なし 2 走 = 1408.04 / 1379.26 秒、
  変更あり 2 走 = 1265.09 / 1247.95 秒。試験数はむしろ 7685 → 7746 に増えており、
  [T-438] の +69.45 秒も込みである。方向は一貫するが、**ノード差と走行間変動 (既知で数 %) を
  分離していない**ので短縮量は主張しない。
- **変異は 8 件すべて検出、SURVIVED 0** (KILLED 3 / MISMATCH 5)。MISMATCH はいずれも
  「事前登録した node は落ちたうえで、もう 1 node も同時に落ちた」= 過剰決定であり生存ではない。
  期待値を結果に合わせて書き換えることはしていない (DW-M03)。事前登録 MT3
  (hook の skip 分岐を消す) は**落ちないと再レビューが実証した** — 現行 canonical node に
  既存 marker が無いため marker が二重化しない。DW-M01 (F28) に従い
  「hook が付ける group 名を `real-repo` → `real_repo` に変える」へ再照準した。
- **変異 harness の recipe を 2 度間違えた。** (i) `-rf` 欠落 (DW-M08)、
  (ii) `--force-dispatch` 欠落で単一ファイル指定が login node の local 実行になり、
  dispatch receipt 行 0 = PARSE_ERROR。いずれも harness が fail-closed で止め、
  tree に残骸を作らなかった。失敗記録は消さず新 artifact 名で再投入した。
- **並行 wave との所有境界を守った。** `dev-wave-t553-git-budget` が
  `test_s8c_preregistration_invariant.py` を編集所有していたため s8c の canonical 化を外した。
  同 wave は本 wave の途中で land し所有は解けたが、**t553 の git 時間予算の定数は現行 group 構成下の
  並行度を前提に実測されている**ため、同じ wave で両方を動かさない判断を維持した ({{T:s8c-canonical-group}})。
- エージェント工数: Codex 9 session (解析 1 / plan 1 / 段 3 相談 2 / 実装 1 / 段 6 レビュー 2 /
  fix 4 のうち 3 は段 6・1 は受入赤対応 … 実数 9)。
  親 = brief・計測全走 2 本・切り分け実験 1 本・裁定・統合 commit 2 本・変異 3 投入・受入 3 投入・記録。
- **段 8 自己改善は候補 3 件、採用 1 件。**
  (採用) 受入 lease 取得後の main 取り込みに `--ff-only` を使うと、wave branch が自前 commit を
  持った時点で必ず失敗する。実測で取得済み lease を 1 回捨てた。runbook §7.3 を是正し、
  取り込みは投入前に親が merge commit で済ませ、待ち手は子孫検査だけにすると明記した。
  (返す) 変異 harness を `runner-mode=dispatch` で使うとき、対象を絞った runner argv には
  `--force-dispatch` も要る (無いと login 実行になり receipt 行 0 で PARSE_ERROR)。
  本 wave で 1 回空振りした。行き先は `DW-M08` だが、
  **`docs/dev-wave/**` の L1.5 層は unique footprint 9566 bytes の予算に対し余裕 0 bytes** で、
  159 bytes の追記が入らない。安全義務を削って空けることは自己改善契約が禁じるため候補のまま返す。
  (返す) 親が段 6 で走らせる対象テストの選び方に、変更した hook の consumer を repo 全体から
  洗う導線がない。本 wave は `pytest_collection_finish` へ追記したのに
  `test_run_tests_task_run.py` を走らせておらず、受入全走 1 回 (21 分 + lease 1 枠) を空費した。
- 一次資料と逐語 = `output/insights/2026-08-10_t692-xdist-walltime/`。

## 次の一手差分

### 完了

- [T-438] `test_ruleops.py` の実 checkout reader を canonical `real-repo` group へ移し、
  手書き status 比較を D63 の共有 helper へ置き換えた。表記ゆれ (`xdist_group(name="real_repo")`)
  で相互排他が効いていなかった穴を塞いだ。同型の再発は新設した収集監査 (marker の個数・表記・
  group 名集合・provenance の 4 検査と各々の合成負例) が塞ぐ。受入全走で緑を確認済み。
  remaining: none
  base: e79b9aae34a87462a623493e1a2b2c8aee683a1a43c8f9ac1dfdd5b9916767f5

### 新規

- {{T:realrepo-payer-closure}} **P1・ユーザー裁定要**: 実 repo を読む ungrouped payer
  (`test_s8b_oracle_driver.py` の `_run()` 系) を D63 の競合閉包へ入れるか。
  `verify_receipt` → `enumerate_repository_files` が untracked と ccbench submodule を実際に
  列挙・読取するため、memo が miss した最初の 1 本は必ず実 repo を読む。memo は cache path 不明・
  lock 失敗・store 失敗で `_resolve_now()` へ **fail-open** する。段 3 レンズ A と段 6 レビュー B が
  独立に Critical と判定した**既存の穴**。択一 = (a) 閉包へ寄せる / (b) prewarm + fail-closed /
  (c) reader/writer flock 化 / (d) 何もしない。推奨は (b)。
  正本 = `output/insights/2026-08-10_t692-xdist-walltime/package.md` の R-a
- {{T:s8c-canonical-group}} **P2・ユーザー裁定要**: s8c candidate 3 node を canonical
  `real-repo` group へ寄せるか。R3 の射程内で、値段は実測 **+58.35 秒**。
  [T-553] の land で所有は解けたが、同 wave の git 時間予算の定数は現行 group 構成下の
  並行度を前提に実測されているため、本 wave では動かさなかった。正本 = 同 package.md の R-b
- {{T:acceptance-walltime-ceiling}} **P2・ユーザー裁定要**: `DEFAULT_WALLTIME` (00:40:00) を
  上げるか。`tools/pegasus/dispatch_compute.py:28` の固定値で `run_tests.py` は `--walltime` を
  渡さないため**呼び出し側から上げられない**。上げても消費は縮まず期限が延びるだけだが、
  receipt 解決の短縮が効くまでの時間稼ぎにはなる。正本 = 同 package.md の R-d
- {{T:cli-second-resolution}} **P2・ユーザー裁定要**: 受入 1 走で 2 回必要な T-080 receipt 解決の
  うち、production CLI 子プロセス側 1 回を無くす設計変更を認めるか。wall の下界を `2q` から `q` へ
  落とす唯一の道だが、当該テストは production CLI の受理経路を実プロセスで検査する
  positive control であり、test 側 cache の注入は規律 2 に反する。
  production 側に正当な cache を持たせる設計は受理集合と proof chain に触る。
  正本 = 同 package.md の R-e
- {{T:mutation-expected-node-overdetermination}} **P3・新規**: 変異 matrix の
  `expected_nodes` 完全一致判定が、広い契約テスト
  (`test_real_repo_group_collection_exactly_matches_canonical_nodes`) の同時発火で
  MISMATCH を量産する。5/8 が該当した。過剰決定を「冗長 gate」として宣言できる
  spec field を harness へ足すか、判定を包含関係にするかを検討する ([T-709] と同型)
