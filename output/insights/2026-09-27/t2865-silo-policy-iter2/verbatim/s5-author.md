## 変更 file と要点 (file:line)

- [骨格 patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/patches/silo-function-policy-variant.patch:79): `thread_local` の seed 済み印と、`thid` を splitmix64 で混合して `| 1ul` で非 0 にする関数を追加しました。[`begin()` hunk](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/patches/silo-function-policy-variant.patch:137) では未 seed のときだけ呼びます。patch の追加は計 10 行です。
- [焦点 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/orchestrator/tests/test_silo_function_policy_template.py:96): 実 patch 適用後の関数と `begin()` の seed 処理を抜き出し、worker ID ごとの差、再現性、系列の継続、`thid_` との結線を検査します。既存 test は変更していません。

## CCBench 側の確認 (begin の順序・thid_、file:line)

[transaction.hh:45,68](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/external/ccbench/cc/silo/include/transaction.hh:45) で `thid_` は `size_t`、constructor 引数は `int` です。[runner.hh:183,282](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/external/ccbench/common/runner.hh:183) は worker ごとに executor を作ります。[ycsb.hh:113,149](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/external/ccbench/include/ycsb.hh:113) では `begin()` が処理、abort、lock conflict より先です。保証範囲はこの「1 worker thread に 1 executor」の寿命です。

## patch の適用確認 (git apply --check・適用後 marker・hook 位置)

pinned CCBench `68106660686232781bca3be792a750d3e19d7a8a` の `/tmp` clone で `git apply --check` と実適用がともに成功しました。適用後の EVOLVE-BLOCK marker は 41・54 行、hook 呼出しは `after_abort` 139 行、`on_lock_conflict` 277 行、`on_commit` 850 行にあります。hunk ヘッダは追加行数を累積して更新しました。

## test の実走 (コマンド・nodeid の範囲・passed / failed / skipped 件数、または未実走)

`python3 tools/run_tests.py -n 1 orchestrator/tests/test_silo_function_policy_template.py` は `qstat -Q` 事前確認で rc=16 となり、**子 test は未起動**です。実走 nodeid はなく、passed / failed / skipped 件数も得られていません。したがって焦点 test は実装済み・未実走です。

適用後ソースから作った単独 TU は、`find_compiler()` が選ぶ `/usr/bin/g++-12` で compile し、実行 rc=0 でした。`git diff --check`、`check_codex_agents.py`、`check_docs.py` も通りました。これは焦点 test 全体の緑判定ではありません。

## 変異 M1〜M3 の単一理由性の見立て

M1 は異なる `thid` の初回値比較、M2 は再度の `begin()` 相当処理後の系列継続、M3 は適用後 `begin()` 分岐の `seed_random(thid_)` 結線検査で、それぞれ赤になる設計です。変異 test 自体は未実走です。

## 所有外への波及と、変えなかった受理・拒否挙動

EVOLVE-BLOCK、API、hook 呼出し点、待機上限、patch の 2 file touch set、stock 側の source 行は変更していません。diff 検疫と構文・単独 TU による候補判定、stock token の既存検査も変更していません。所有外の利用先は `test_silo_policy_compile.py`、`test_silo_policy_grammar.py`、`condition_meaning_gate.py`、`silo_policy_coverage.py`、`p3_s4_loop_policy.py` です。

制約 meta-test を確認したところ、新 test は実 CCBench を使う一方、所有外の `conftest.py` にある real-repo node 登録には含まれません。この分類と独立 golden を検査する `test_real_repo_serialization.py` への波及は未実走です。所有外 file と既存 test の期待値は変更していません。

## 総括

指定の 2 file に seed 修正と焦点 test を実装し、pinned source への適用と単独 TU の動作を確認しました。pytest の緑判定と制約 meta-test の確認は、runner の事前確認失敗により残っています。commit は作成していません。