## 作った file と役割

- [壊し patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/patches/broken-cicada-promotion-ronly-stale-recheck.patch): F1 の読み取り専用 promotion 抑止を戻し、再検査起点の差を残して commit した tx の event と終了時の集計を stderr に出します。
- [確認 job](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py): `ycsb`・`tpcc`・`ci` を分割実行し、入力の同一性、build 定義、実行 flags、判定結果、M1〜M3、D297 を記録します。[診断用共通関数](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/promo_diag_support.py) と [CI image 実行 body](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/run_ci_image.sh) を同梱しました。
- [README](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/README.md): 数え上げ、見積り、事前予測、受理条件を記載しました。

## 数え上げと見積り

YCSB は **25 build・52 走行**、TPC-C は **16 build・34 走行**、CI は全 protocol build 1 回です。合計 **42 build・86 走行、0.8～1.3 node 時間**と見積もります。単位 D の見積りと合わせると **1.06～1.74 node 時間**です。M3 の patch が適用できない場合は build・走行が各 1 減ります。

## login で行った検査と結果（未実走の明記）

修理後の使い捨て clone で、壊し patch は標準 trace と promotion 診断変種の双方に `git apply --check` **rc=0**。TPC-C 計装を重ねた順序でも **rc=0** でした。診断変種＋壊し patch の `transaction.cc` 一 TU は、指定 promotion genome・`TRACE=1` の `g++-11 -fsyntax-only` **rc=0**。Python の `py_compile` と CI shell の `bash -n` も **rc=0** です。

`clang-format-14 --dry-run --Werror` は **失敗**しました。報告された箇所は既存 trace 計装の行で、新しい壊し部分は整形済みです。修理後 tip の commit と bundle がまだ無いため、仮の土台を tip に指定した `--dry-run` は byte 同一性不一致を **rc=2** で拒否しました。正式 tip での dry-run、全 build、判定・ASan・CI の計算ノード実走は**実装済み・未実走**です。使い捨て clone は削除し、commit・`git add` は行っていません。

## 既存 test・meta-test への波及

`patches/*.patch` を列挙する `test_ccbench_spawn_sites.py`、`test_p3_s4_loop.py`、`test_mocc_template_proof.py` を静的に確認しました。新 patch に `IZANAGI_` 条件 macro や MOCC marker はありません。既存 test、判定器、計装 patch、共有 fixture は編集していません。実利用側は Cicada の YCSB・TPC-C、CI image body、D297 検査器です。pytest は指示どおり login で実行していません。

## 予測と M1〜M3 の期待

修理後 YCSB の観測 cell は巡回 0、土台の K/R は巡回再現を予測します。M1 は壊し event の tx を C 行の `(hi, lo)` に写し、witness の巡回辺の key と照合します。M2 は F3 逆適用で abort／`writeSetClean` 起点の ASan UAF、M3 は F2 逆適用で素通り計数 `>0` を期待します。M3 は判定器の kill には数えません。

段 4 追補 1 の D1 実測で、TPC-C の `Tuple::init` 起点の `bad_alloc` 候補が見つかっています。F4 は未裁定のため、F1〜F3 の tip でも TPC-C が失敗し得る予測として記録しました。

## 総括

親が正式 tip と bundle を渡せば、3 part の job を計算ノードで実行できます。結果の緑は実走後に判定し、巡回 0 は `no_cycle_upper_bound_indeterminate` として記録します。