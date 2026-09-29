## 所見

1. **must-fix — 回収時の版鎖と tuple の寿命を、X1 の安全性として扱えない。** X1 は `latest` から `next_` を追加で辿るが、`gc_records()` は GC lock を取らずに `delete rec` する。一方、別 thread の `gc_versions()` は lock 下で鎖を切り、版を再利用候補に入れる。scan 結果、read set、他 thread の `gcq_` も tuple または版の参照を保持し得る（[transaction.cc:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:423)、[transaction.cc:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:806)、[transaction.cc:845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:845)）。これは最新版が deleted の既存正常経路にもある寿命問題だが、X1 は従来 ERR で停止した状態でも実際に回収するため、その状態への安全性の論証が必要。放置すると修理 commit は停止を解消しても、参照中 tuple の解放を許す可能性がある。**具体的な UAF の到達は静的には未確認。**

2. **should-fix — 「回収時に pending 版は無い」は未証明。** `begin()` は wts を公開した後に `MinWts−1` を rts として公開し、時刻生成には `wts >= rts` の保証がない（[transaction.cc:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:34)、[time_stamp.hh:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/include/time_stamp.hh:30)）。leader は公開済み配列の最小値を使うだけで、この大小関係を補正しない（[util.cc:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/util.cc:281)）。時計ずれ等で大小が逆転する場合、`latest.wts < MinRts` を pending 不在の証拠にはできない。X1 は pending を見たら ERR を残すので、その状態を黙って回収する直接の穴ではないが、「pending 不在」を根拠とする安全性の結論は一次資料に書けない。abort 後の clock boost は次回の時刻にしか効かない（[transaction.cc:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:745)）。

3. **should-fix — trace 合格条件は、競合する delete を検査した証拠にならない。** `thread_num=4` と `W ... D` の正数だけでは、その delete が他 thread の同一 NewOrder 行への操作と重なったことは分からない（[plan.md §確かめ方](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md>)）。D1 の故障はまさに同一行への後発 delete が abort 版を残す経路である。放置すると修理版 trace の合格を、修理分岐が発火した履歴の合格として過大に報告する。診断 patch 相当の発火計数、または修理分岐の別途計数を同じ trace run に対応付けるべき。

4. **should-fix — `CUSTOM` 起動器の総合合否は提案した判定をまだ強制しない。** 現状は verifier の実行エラーしか `failed` に反映せず、巡回数、存在履歴違反、C 行数などは総合 rc の条件外である（[launch_gcfix_run.py:1138](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/launch_gcfix_run.py:1138>)）。plan 自身も修正必要と記す。放置すると成果物の判定器合否が、失格 trace に対して成功になり得る。

5. **nit — X1 の受理集合についての表現を限定する。** X1 は validation と commit を変えず、先頭から aborted を越えた最初の確定状態が deleted の場合だけ回収する。deleted の上の後発版は validation (b) で abort する構造で、D1 の 10 件は先行する read 再検査 (a) で abort した（[transaction.cc:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:543)、[transaction.cc:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:576)、[D1 結果](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/d1-result-summary.md>)）。したがって「観測した条件では受理集合を変えない」は妥当。ただし `INLINE_VERSION_OPT=1`、`SINGLE_EXEC=1`、`group_commit>0` まで一般化する実測は無い。X2 は正しい並行 unlink と reclamation を実装できれば意味上の受理集合を保てるが、現コードへの単純な unlink は参照寿命を壊す。X3 の早期 abort は受理集合を縮めるが、abort だけなら直列化可能性を悪化させる理由にはならない。ただし単独では既存の aborted 版を除けず D1 を直さない（[plan.md §修理案の比較](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md>)）。

## 親の実測と一般化への指摘

D1 の 10/10 件は X1 が狙う `aborted → deleted` を直接示す。ただし 1 job、1 node の観測であり、全設定での pending 不在や回収寿命の証明ではない（[D1 結果](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/d1-result-summary.md>)）。判定器の存在履歴検査は記録された W の I/U/D と R の版を調べる。不在の読みと空の scan は表現されないため、`existence_violations=0` と巡回 0 は完全な直列化可能性の証明ではない（[dsg.py:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/orchestrator/verifier/dsg.py:385)）。

TRACE=0 の修理は意図的に `transaction.cc` の命令を変える。変更箇所を同 TU の数行に限れば他 TU への直接変更はないが、`ERR` の `__LINE__` は行数変更で変わり得る。既存の TRACE=0 命令列一致は**修理前の計装**に関する結果であり、修理後の他 TU と ERR 行番号の確認を代用しない（[plan.md §編集](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md>)、[既存資料 §6](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md>)）。

## 変異の事前登録案

- **負例:** 同じ job の無修理 F×t4/t8 で既知の `gc_records` ERR が少なくとも 1 回発生し、修理版は完走する。単なる ERR 行の消失だけを成功としない。
- **修理分岐の正例:** trace run に、先頭 aborted を越えて deleted に到達した回数と、対象表・key・版状態を診断として対応付ける。`W-D>0` に加えてこの回数が正であることを要求する。
- **防壁の負例:** 最初の非 aborted 状態を committed または pending にした制御された変異では、X1 が回収へ進まず ERR または明示的延期となることを確認する。特に「ERR すべき committed を読み飛ばす」変異を失格にする。

## 総括

X1 は D1 で見えた状態に合い、commit 判定を変えない第一候補である。採用時は、**追加で回収する状態の参照寿命**と**同じ trace 走行で修理分岐が実際に発火した証拠**を完了条件に加えるべき。現行 `CUSTOM` の総合 rc も trace の数値判定を強制する必要がある。