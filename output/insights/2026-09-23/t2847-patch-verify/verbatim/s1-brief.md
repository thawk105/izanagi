# 段 1 brief — [T-2847] 残り (2) の一部: 既存 silo 壊し patch 11 本の実走と検出期待表の突合

wave: dev-wave-t2847-patch-verify / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/t2847-patch-verify
(branch worktree-t2847-patch-verify、起点 local main 3886a1fd3、開始 gate rc=0、ccbench pin e9e477ca)

1. 研究前進: VLDB 差分分析 P0「検証の意味」。insight t2847 §4 の検出期待表 (静的推定) のうち既存 silo patch 11 本の行を、現 pin の計算ノード実走で「期待どおり / 別の層 / 未発生 / その他」に分類した表にする。完了判定 = 11 本すべてに観測 (または実走不能の理由) と分類が付いた表が insight に着地。
2. scope: norw・highkey・lockskip・early-unlock・permutation-erase・permutation-swap・sort-nonswo・write-intent-{erase,forge,opswap,ptrswap}。mocc・trigger-misattr・新規 18 変異・コーパス test・容量・si は外。tracked の CCBench・verifier・test_verifier.py は編集しない。性能値は取らない。gate・検査・台帳・一般化の追加はしない。
3. 確定裁定: 計算は job 合計 (開発の検査を含む) 2 node 時間以上なら job Elapse の実測単価で見積りを示しユーザー確認 (D2212 項 4、D2219 項 1)。規律 2 不変。patch 適用は driver と同じ厳密さ (patchharness.apply_patch = git apply、fuzz なし)。適用成功を検証成功と数えない。
4. 親が段 1 で実測した前提 (攻撃対象):
   (P1) s3_lock_coverage / s5_permutation_coverage は PIN = pin.CURRENT_PIN = e9e477c で現 submodule と一致。main() は stock を buildcache.build で、壊し patch を _build_broken の直接 cmake で build する。
   (P2) s2_verify_calibration は PIN = "dff0f1e" 直書きで、main() は旧 pin 前提の較正 (48 thread・100 万 tuple の perf 反復) を含む。現 pin では assert_pinned_clean で止まる。壊し patch の部分は _broken_build_and_verify(patch, define, workloads) に切り出されている。親の暫定案: s2.PIN を pin.CURRENT_PIN に差し替えて _broken_build_and_verify だけを呼ぶ起動器 (repo 外)。
   (P3) t152_write_intent_coverage は patchharness.checkout で IZANAGI_T152_CCBENCH_SHA の使い捨て worktree を作り、CMAKE_PREFIX_PATH (gflags/glog install) を必須とする。現 pin には I 行 emitter が無い (silo transaction.cc の stream は P/C/E のみ) ので、各 check は偽で all_pass=false の見込み。これは §4.3 V09〜V12 の「盲点」期待の観測になる。
   (P4) sort-nonswo は 4 driver のどれにも経路が無い (CCBENCH_SORT_VARIANT の別系統、condition_meaning_gate に未登録の可能性)。親の暫定案: 新しい実行器は足さず「その他: 既存 driver に経路なし・未実走」と表に書く。
   (P5) 計算ノード (Pegasus gen_S) は外部ネットワークが無く、システムに glog/gflags が無い。s2/s3/s5 の直接 cmake は依存物を供給しない (FetchContent の masstree/mimalloc/googletest を取りに行く)。Pegasus 対応済みの s3_mocc_lock_coverage._prepare_dependencies (tools/pegasus/fetch_third_party.py hydrate + gflags/glog の使い捨て install) と _common_configure_args の FETCHCONTENT_SOURCE_DIR_* が既存の供給経路。buildcache.build (stock) が計算ノードで依存物をどう得るかは未確定。
   (P6) 4 driver とも repo 内 tracked JSON (output/env/.../calibration, characterization) を上書きする。親の暫定案: 実走は wave worktree で直列に行い、出力 JSON を job dir へ退避してから tracked file を git checkout で戻す (commit しない)。
5. 投入経路: tools/pegasus/dispatch_compute.py --task generic --walltime HH:MM:SS -- <argv> (計算ノードでだけ実行、cwd=repo root、環境変数は受け取らない)。同一 worktree の dispatch は直列。
6. 成果物: insight output/insights/2026-09-23/t2847-patch-verify/README.md (観測表と 4 分類、生出力は raw/)、worklog fragment。repo 内の実装差分はゼロを目標 (起動器は job dir に置く。Codex author が書く)。
7. 分割: 段 2 plan 1 本 (起動器の設計と依存物供給の経路を file:line で)、段 3 相談 1 本、段 5 author 1 本 (起動器)、段 6 review 1 本 (表と起動器)。変異 matrix は repo 内実装差分ゼロなら免除 (DW-S04)、受入全走は行う。
