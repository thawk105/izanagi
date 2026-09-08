## 正しさ検査の素通り

所見 1: (a) T2418 は condition gate → prebuild → campaign の順を通るため、run-kind 分岐そのものによる全面的な素通りはない。ただし `require_all_binary_hashes=False` となり、3 静的 binary の完全性は fail-closed ではない。(b) `s2-plan.md:15` は式を変更しないとしており、`backoff_extended_sweep.py:927-947` では gate と prebuild が無条件だが、全 genome 検査は T2266 のときだけ有効である。汎用検査は `backoff_extended_sweep.py:225-227` で非静的に見える `BuildResult` を無条件に skip し、`backoff_extended_sweep.py:242-243` は確認できた amount が 2 未満なら成功する。(c) 4000／6000／11999 のいずれかの `BuildResult.genome` が誤って `BACK_OFF=0`、負値、別 genome になった場合、その結果は binding 検査より前に除外され、残り 0～1 amount でも通る。正常な `BuildResult` が3個返る通常経路では、3 SHA の相異は実際に検査される。(d) T2418 用に、trace-disabled の期待 canonical genome `{4000,6000,11999}` が全件存在し、各 `BuildResult` が要求 genome に束縛され、SHA が3個とも異なることを検査する小さな helper を追加する。衝突テストに加え、欠落・非静的 genome への置換を拒否するテストが必要である。

所見 2: (a) condition gate は3値の「供給・effectuation」を検査するが、4000／6000／11999 が意図した 2000／4000／9999 µs を意味することは確立しない。これは gate の呼出し漏れではなく、意味 arm が `unestablished` のまま raw measurement に受理される境界である。(b) `backoff_sweep.py:133-153` は `BACKOFF_FIXED=-1` にだけ意味 declaration を与え、正値には `None` を渡す。`condition_meaning_gate.py:3295-3300` はそれを `unestablished` とし、`condition_meaning_gate.py:4058-4063` は `unestablished` を受理する。実際の高域復号式は `patches/silo-backoff-fixed.patch:69-70` にある。(c) patch の `>=3000` の式だけが変わり、Python の codec が不変なら、codec 往復、供給差、binary SHA 相異のすべてが通っても、測っている物理量は誤り得る。(d) 最小の是正は、3 wire 値について既存の `MeaningWitnessDeclaration`／`assert_backoff_fixed_meaning` を用いた pointwise meaning 検査を測定前に行うこと。scope 上追加しないなら、brief の主張を「Python codec と wire 値を構成できる」に狭め、runtime の物理量は未実証と明記する必要がある。

## 恒真になりうる検査

所見 3: (a) 計画中の「gate・prebuild・campaign が同じ genome 群を受ける」は、各引数を相互比較するだけなら自己整合性しか検査せず、候補の正しさについて恒真になり得る。(b) `s2-plan.md:22` と `s2-plan.md:119` がこの比較を提案している。既存の同型テストも `test_backoff_extended_sweep.py:849-875` では集合の一部を literal 化している一方、イベント間の同一性は生産側引数同士の比較になりやすい。(c) T2418 分岐を、正しい `t2418_genomes()` ではなく別の誤った5 genome を返す関数へ接続し、同じ誤集合を gate・prebuild・campaign の全部へ渡すと、相互一致テストと未使用の `t2418_genomes()` 単体テストはともに通り得る。(d) run-path テスト自身で、各捕捉引数を独立 literal `[(0,-1),(1,-1),(1,4000),(1,6000),(1,11999)]` に比較する。併せて選択された config の `run_kind`、slug、trial も literal に照合する。

所見 4: (a) report/WAL テストを `p2_2.REPS` から生成すると、「5反復」の検査は共有定数自身に含意され、D1813 の literal 5 を守れない。(b) `s2-plan.md:120` は「5 points × `p2_2.REPS`」としており、既存 helper も `test_backoff_extended_sweep.py:166-198`、`test_backoff_extended_sweep.py:443-452` で同じ定数を期待値生成にも使用する。生産側も `backoff_extended_sweep.py:893-899` で同じ定数を読む。(c) `p2_2.REPS` を 5 から 4 に変えると、生産、capture、loader、テストのループがすべて4へ追随し、D1813 違反のままテストが通り得る。`EXTIME` も同様である。(d) `p2_2.REPS == 5`、`p2_2.EXTIME == 3`、捕捉された `PerfConfig.reps == 5`、`extime == 3`、各 report point の rep 数が5であることを独立 literal で pin する。

## 凍結境界への間接的な接触

所見 5: (a) T2418 は凍結対象の patch と codec を直接再利用するため間接接触はある。また PBS job の commit binding は job script だけで、driver、patch、`pin.py`、condition gate の working bytes を `CURRENT_COMMIT` に拘束していない。(b) patch の実行経路は `backoff_extended_sweep.py:907-913`、codec は同 file `64-79`。job は `b10_backoff_grid.sh:354-379` で自身の SHA だけを HEAD blob と比較し、Izanagi worktree の tracked cleanliness は検査しない。検査している cleanliness は detached CCBench 側だけである (`b10_backoff_grid.sh:449-459`)。(c) commit 後に `patches/silo-backoff-fixed.patch` や `backoff_extended_sweep.py` が dirty になっても job script が不変なら投入でき、completion は `repository_commit` を記録しつつ working bytes を実行する。brief の「commit 済みなら条件を満たす」はこの場合に成り立たない。(d) job 冒頭で Izanagi repo の tracked status が空であることを要求するか、少なくとも driver、patch、`pin.py`、condition gate の working SHA を `$CURRENT_COMMIT:<path>` の blob SHA と照合する。

所見 6: (a) `EXTENDED_SWEEP_US` は上端だけでなく、正式 report の長さ・集合・順序・隣接関係を pin する production consumer を持つ。T2418 を別定数にする計画はこの境界と整合しており、現プランから既存格子を変更する経路は見つからなかった。(b) `backoff_extended_sweep_report.py:87-94` が長さと集合、同 file `172-176`、`203`、`413-415`、`443-444` が index・端点・隣接点を意味に使う。別の独立 literal consumer も `backoff_requested_us.py:69-72`、`624-627` にある。(c) 探索値を `EXTENDED_SWEEP_US` へ加えたり、順序だけ変えたりすると、単なる上端テスト以上に正式 shape 判定、onset 選択、D1106 reference admission の意味が変わる。(d) `T2418_*` を完全に別集合のまま保ち、T2418 config に正式系列の `sweep_us` keyを追加しない。既存格子・T2266定数・codec・patch・freeze hash の差分ゼロをレビュー時に確認する。

## 識別子と consumer

所見 7: (a) `t2418-explore`、schema、slug、trial、scale、report stem の直接衝突は現行 tree にはなく、既存 consumer がこの値を既定へ静かに落とす経路も確認できなかった。ただし `run_kind` は repo 全体で一つの共有 enum ではなく、別々の語彙で使われる。(b) production で `run_kind` を扱う file は10個だった。B10系は `backoff_extended_sweep.py:854-857`、`b10_backoff_grid.sh:30,186-189`、`submit_b10_backoff_grid.sh:12,36-40`、`plot_t2266_tail_mechanism.py:142-166`、`t2216_backoff_walk_model.py:283-300`。別系統の T810 は `t810_budget.py:309,433-434`、`t810_coordinator.py:285-334`、`t810_guard.py:392-421`、`t810_harness_schema.py:306,385-399`、`t810_pbs_wrapper.py:154-156,762-763` である。(c) T2418 report を T2266 plot/model に渡せば exact schema/run-kind で拒否され、T810 に渡せば同系統の閉集合外として拒否される。T2418 の新値を T810 の `RUN_KINDS` に登録する必要はない。(d) B10 の三入口で三値を literal に受理し、T2266 consumer の拒否テストを維持する。識別子探索ゼロだけでなく、「T2418 report は既存正式/T2266 consumer に拒否される」負テストを追加すると境界が明確になる。

## 「混ぜない」の実装としての十分性

所見 8: (a) campaign identity の分離は WAL の同居防止には有効だが、「正式系列へ混ぜない」の単独の十分条件ではない。外側の group prefix と completion schema は正式 extended と共有され、少なくとも一つの downstream consumer は `run_kind` を読まない。(b) group は全 run kind で `b10-backoff-grid-*` のまま (`submit_b10_backoff_grid.sh:93-103`)、completion schema も共通 (`b10_backoff_grid.sh:645-652`)。`backoff_requested_us.py:581-589` はこの schema/status/workload/campaign_id を読むが `run_kind=="extended"` を要求しない。ただし続く `backoff_requested_us.py:617-627` の正式 grid と `698-713` の overthrottle manifest 検査により、現プランのT2418成果物は最終的には拒否される。正式 report 自身も exact slug で読む (`backoff_extended_sweep_report.py:462-469`)。(c) 将来 T2418 に互換用 `sweep_us` や overthrottle manifest が足される、または外部 collector が group prefix／completion schema／workloadだけで集めると、campaign IDが別でも候補に入る。したがって brief の「campaign identity が別になることが実装」という一般化は強すぎる。(d) 最小の是正は、既存正式 consumer に `completion["run_kind"] == "extended"` を必須化し、T2418 root の拒否テストを置くこと。brief は identity、専用 schema/stem、machine-readable disclosure、consumer の exact allow-listを合わせた境界だと書き換える。

## 親 brief の実測と一般化

所見 9: (a) 「3点は現行 main の経路で構成できる」は、実測された codec 往復については正しいが、condition gate通過、build成功、runtime meaningまでを含む表現としては実測を超えている。(b) `s1-brief.md:34-39` の実測は `2000→4000→2000` 等のPython往復である。runtime側の式は `patches/silo-backoff-fixed.patch:69-70`、意味未確立の受理は所見2の各行に示した。(c) patch の高域式、CMake、実コンパイラのいずれかだけが高域で失敗しても、記載された往復実測は成功したままである。(d) 「codec/wire 構成を確認した。実 gate/build/runtime は未測定」と限定するか、3値の pointwise meaning gate と build実測を別途証拠化する。

所見 10: (a) 「F660 は発火しない」という結論は静的には妥当だが、「実測」というラベルは不正確である。(b) main側登録簿には job が `dispatch-required` (`admission_registry.json:22-26`)、submitter が `local-ok` (`admission_registry.json:322-326`) で既登録である。guard は exact path と classだけを見る (`guard_bash.py:614-629`, `1205-1215`)。F660 は新規 path が main登録簿に無い場合の失敗である (`failures.md:18629-18643`)。(c) 新しい wrapper/pathを介する、main側登録簿が異なる／読めない、または既存 pathとして解決されない呼び方をすると結論は崩れる。既存二 pathを通常経路で使う限り、内容SHAを登録簿が pin しないという推論は成立する。(d) brief を「main側登録簿と guard 実装による静的確認。hook発火実測ではない」と訂正する。実投入前には exact command surface の hook probe結果を別記録に残す。

所見 11: (a) 「反復数は共有定数なので自動的に同じ」は現行値については正しいが、D1813 の literal 5 を凍結する一般化にはならない。(b) `s1-brief.md:38-39`、`p2_2.py:54-57`、`backoff_extended_sweep.py:893-899` がこの共有を示す一方、計画の report test は `s2-plan.md:120` で同じ定数へ追随する。(c) 共有定数が4へ変われば既存 sweepとT2418は「同じ」だが、裁定された REPS=5 には反する。T2418だけ `reps=p2_2.REPS-1` にする変異も、PerfConfig literal検査がなければ見逃し得る。(d) 所見4の literal pinを受入条件へ加え、「共有により配線は同じ、literal 5/3 は独立テストで固定」と記述する。

## 根拠なしの疑い

該当なし。現在の production consumer について、workload名や trial名の部分一致だけでT2418を正式数値へ静かに合流させる経路は確認できなかった。上記の懸念はすべて具体的なコード経路に基づく。

## 総括

プランどおりに分岐を追加すれば、T2418 は condition gate と静的 SHA 検査を通り、既存正式/T2266 consumerにも現状は混入しない。ただし着手前に直すべき境界がある。

- T2418 の static SHA 検査を、期待3 genomeの完全性まで fail-closed にする。
- 高域3値の runtime meaning を確立するか、brief の主張を codec 構成までに狭める。
- REPS=5／EXTIME=3 と run-path genomeを独立 literal で検査する。
- 測定時の Izanagi driver／patch等を HEADへ拘束する。
- 正式 consumer に `run_kind=="extended"` を明示し、campaign identityだけを「混ぜない」の十分条件と扱わない。

pytest、`bash -n`、PBS投入は実行しておらず、テストが緑とは報告しない。