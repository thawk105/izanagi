---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1431-floor-pilot-submit
seq: 3
title: [T-1431] 床値 pilot を実投入し、止めていた到達不能述語を実測で確定して直した (コード + docs、branch worktree-dev-wave-t1431-floor-pilot-submit、変異 matrix = baseline PASSED・KILLED 9/9・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「床値 pilot を実投入して床値の実測値を取る。前回の一次要因と潜在要因の両方が
  現在の main で解消しているかを投入前に実測で確かめ、解消していなければ直してから投入する」。
  投入前の実測で、記録された 2 blocker はどちらも解消していると確認した。
  一方で **`sort_best` build が落ちる根本原因そのものは未特定のまま**であり、
  そのまま投入すれば前回同様 0 セルで終わる公算が高いことも明らかだった。
  ログインノードでは `cmake --build` を guard が拒否するため compile の実測が取れず、
  診断は計算ノードでしか得られない。T-1578 の耐久診断が入っている以上、
  投入が最も安く確実に原因へ到達する経路だと裁定して投入した。**この判断は当たった。**
- **投入 1 回で原因が確定した。** request `944884.nqsv` は前回と同じく 3 セル build 完了 /
  計測 0 で止まったが、握り潰されていた例外の本文が残った
  (`BuildCacheError: CMakeCache.txt の masstree_SOURCE_DIR が一意な絶対 path でない`、
  `message_truncated=false`)。コンパイル失敗ではなく、izanagi 側の build 後検査が
  現行 CCBench pin では**出現しえない** CMakeCache key を要求していた。
  逐語と一次資料は `output/insights/2026-08-25_t1431-floor-pilot-submit/README.md`。
- **admission チケットの消費は 0 枚。** `retry_slots_per_cell=2` は全 12 セル満枠のままである。
- 親はログインノードで独立再現した。同 cmake 3.25.0 / 同 g++ / 同 payload / 同 configure argv で
  cell configure は rc=0 になり、生成された CMakeCache の `masstree_SOURCE_DIR` は 0 件、
  `POPULATED` も 0 件だった。実在するのは `FETCHCONTENT_BASE_DIR` と
  `FETCHCONTENT_SOURCE_DIR_MASSTREE` である。
- **段 3 の敵対相談 2 本が、親の provisional 裁定を独立に倒した。** 親は
  「CMakeCache から uppercase key を読み戻せば D425 の要求を満たす」と置いていたが、
  両レンズとも「CMake の変数解決では通常変数が cache 変数を shadow するので、
  ambient な toolchain file が source root を差し替えても CMakeCache には現れない。
  それは D425 が名指しで警戒した経路そのものだ」と指摘した。親は案を捨て、
  生成された build system が記録する解決済み root との一致を要求する案へ改めた
  ({{D:effective-masstree-root-needs-two-independent-witnesses}})。
- **段 6 のレビューが、変異 3 件が他層に mask されて SURVIVED になることを本走前に見抜いた。**
  m03 / m04 / m05 は、対象の検査を外しても A/B 一致検査が別理由で拒否し続けるため
  検出できない構成だった。fix 子に単一理由の negative 9 case を足させ、
  probe で観測 node を集め直してから本走した。結果は KILLED 9/9、期待 node 完全一致。
  逐語は `output/insights/2026-08-25_t1431-floor-mutation.md`。
- 段 6 レビュー A の must-fix「旧述語で publish 済みの entry が cache hit で A/B 検査を
  迂回する」は **refuted** とした。`fetchcontent_archive_sha256` は cache preimage に入り、
  その値 (masstree の in-tree build 成果物 hash) は run ごとに変わるため、
  `sort_best` cell の cache hit は job を跨いで構造的に起きない。加えて旧述語は
  一度も publish に成功していないので、汚染 entry は存在しえない。
- **親が tracked file を消す事故を 1 件起こした** ({{F:git-status-is-not-a-tracked-absence-proof}})。
  `git status` を untracked 確認に使ったが、tracked かつ無変更の file は出力されないため
  不在証明にならなかった。除去直後の `git status` で検出し全件復元した (実害なし)。
- **段 6 の子を `run_in_background` へ直接投げて途中死させた。** `DW-O01` の detach 形
  (`nohup setsid ... </dev/null`) を使わなかったため、子は 200KB 分の events を出した後に
  消え、`.done` も成果物も残らなかった。**harness の通知は exit code 0 を返した**ので、
  通知だけでは死を検出できない。detach 形で投げ直して回復した。
  なお最初の 2 本は実際には完走しており (receipt の outcome=accepted、
  成果物 hash も receipt と一致)、再投入は重複だった。段 8 の候補として登録した。
- **受入 attempt 1 の赤 32 件は親の操作が原因だった** ({{F:umask-in-launcher-corrupts-merged-worktree-modes}})。
  受入 launcher に書いた `umask 077` を受入ラッパが継承したまま local main を merge したため、
  git が作業ツリーへ書いた incoming 47 file すべてが 0600 になり、
  repo snapshot の mode を検査する `test_codex_reasoning_ab.py` が落ちた。
  **単独再走は 454 passed で緑だったが、それは非帰属の証明ではなかった。**
  junit の assertion 本文 (`st_mode mismatch ... 0o100600 != 0o100644`) まで読んで
  初めて帰属が確定した。mode を全件戻し、`umask` を触らない launcher で再投入した。
  attempt 2 は 15427 passed / 60 skipped / 0 failed で receipt が出た。
- エージェント工数: 段 2 plan 1 本、段 3 consult 2 本、段 5 author 1 本、段 6 review 2 本、
  段 6 fix 1 本。すべて `gpt-5.6-sol`。plan / consult は `xhigh`、
  author / review / fix は段既定 (`--reasoning` 指定不可)。
  段 5 と段 6 fix の子はどちらも Pegasus dispatch の preflight 失敗で pytest を実走できず、
  テストの実測はすべて親が行った。

## 次の一手差分

### 更新

- [T-1431] **P1・投入済み / 停止点は修正済み**: 床値 pilot を実投入し
  (request `944884.nqsv`)、止めていた到達不能述語を実測で確定して直した。
  ただし**床値の実測値そのものはまだ得ていない** (計測到達セル 0)。
  修正を land した後に同じパラメータで再投入する。
  admission チケットは 2 回とも 0 枚消費で、`retry_slots_per_cell=2` は満枠のままである。
  パラメータは `output/insights/2026-08-25_t1431-floor-pilot-submit/README.md` の
  「環境・実行パラメータ」節をそのまま使う。
  base: 0b62ee3307b44f576f4a92316a5208dce77b97aa3e98cc038dc000b583725b5f

### 新規

- {{T:heavy-guard-variable-indirection}} **P2・新規**: ログインノードの重い処理防壁が
  shell 変数の間接で発火しない ({{F:heavy-work-guard-bypassed-by-shell-variable}})。
  `hooks/guard_bash.py` の head 判定を是正し、直書き形と変数間接形で判定が一致することを
  要求する positive control を足す。正しさ防壁の改訂であるため実装前にユーザー裁定が要る。
- {{T:floor-sort-best-cache-always-cold}} **P3・新規**: `sort_best` cell の build cache は
  job を跨いで必ず cold である。`fetchcontent_archive_sha256` が cache preimage に入り、
  その値は masstree の in-tree build 成果物 hash なので run ごとに変わるためである。
  床値 campaign の所要見積りに効く。是正するか、cold を前提に見積もるかを決める。
