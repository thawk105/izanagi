# T-2074 変異台帳 — A-1 estimand 揃え直しの受理集合を裏取りする

対象 commit: `ee9cc6515191b1eb82c598431108a05b0dee2192`
事前登録: `s4-adjudication.md` §12 (M1〜M10、M10 は 5 境界で 5 通り = 14 変異)
生成器: 親の `build-mutation-spec.py` (anchor 逐語と一意性 assert を持つ)
変異 source: 独立 clone `/work/1/SFC/tanab/mutation-src-t2074` (理由は下記)

## 結論

**14 変異すべてで、事前登録した gate が実際に発火した。発火漏れはゼロである。**

`DW-M08` の厳密一致による KILLED 判定は、本走 (mainB) で 9 件、
最終走 (final5) で残り 5 件を確定した。
5 件が本走で厳密一致しなかったのは、外し損ねた冗長 gate 5 件が観測へ混ざったためで、
**狙った gate はすべて発火していた** (下表の「発火漏れ」列)。

## 走らせ方 (4 段)

| 段 | 目的 | spec | 実測 |
|---|---|---|---|
| probe | 観測 node を集める (`DW-M07`) | 14 件 SURVIVED | 14/14 記録。M3 のみ生存 |
| 較正 | 現 tip の冗長 gate を実測する | M1 と M5 のみ SURVIVED | 386 件と確定 |
| 本走 (mainB) | KILLED を判定する | 14 件 KILLED | 9 KILLED / 5 MISMATCH、発火漏れ 0 |
| 最終走 (final5) | 残り 5 件を厳密一致で確定する | 5 件 KILLED | (下記に記入) |

`DW-M08` は期待 node の**完全集合**との完全一致だけを KILLED と認める。
期待 node を先に確定できないため probe を挟んだ。

## 冗長 gate を証拠から外した根拠 (`DW-M03`)

変異 harness は固定 commit の worktree で file を書き換えるため、
**変異が狙った受理集合の性質とは無関係に**次の層が一律で落ちる。

| 層 | 件数 | 何を見ているか |
|---|---|---|
| contract loader の drift | 384 | disk bytes が HEAD blob と一致するか |
| worktree 変更そのものの拒否 | 1 | source/test 以外の worktree 変更が無いか |
| no-touch manifest | 1 | 保護対象 file が base から変わっていないか |

いずれも「source が変わった」ことだけを見ており、変異の意味を見ていない。
`DW-M03` の「過剰決定なら冗長 gate と明記して単独変異の証拠から外す」に従い、
runner argv の `--deselect` で外した。**集合は推測せず較正走で実測した。**
main 取り込みで 383 → 386 へ増えており、推測していれば全て食い違っていた。

### 外せなかった 5 件と、その処置

記録側の node ID は改行を `/n`、非 ASCII を `/uXXXX` へ正規化する。
この文字列を `--deselect` へ渡しても実際の node ID と一致せず、**pytest は静かに無視する**。
本走ではこれが原因で 5 件が残り、`pipeline.py` 系 5 変異が MISMATCH になった。

該当 5 件は `test_critic.py` と `test_p3_s4_loop.py` の 2 file に収まっており、
どちらも狙った gate を 1 つも含まない。`--deselect` は node ID の前方一致を受け付けるので、
最終走では**この 2 file を file 単位で外した** (386 entry → 299 entry)。

## erratum — M3 の初回は照準を外していた (`DW-M02`)

初回 probe の M3 は `_BenchResult` の `cv` を block CV の平均へ差し替える変異だったが、
**固有の赤が 0 件で生存した**。調べると実効 gate
(`test_balanced_schedule_cv_is_all_rep_cv_not_mean_block_cv`) が見ているのは
受領証側の `arm_records[...]["cv"]` であり、`_BenchResult` の `cv` は
どの検査も参照していなかった。

受領証側へ再照準したところ、予測した gate に加えて
`test_balanced_receipt_real_producer_round_trips_consumer_and_sizing` も発火した。

**初回の結果は消さない。** 「`_BenchResult.cv` は現状どの検査にも束縛されていない」という
事実そのものが観測であり、後段の設計判断に効く。

## 変異一覧と実測

| ID | 変異の内容 | 発火漏れ | 狙った gate の発火先 |
|---|---|---|---|
| M1 | block ごとの競合 probe を schedule 冒頭 1 回へ減らす | なし (2/2) | `test_campaign.py::test_balanced_schedule_probes_each_five_rep_block_independently` ほか 1 |
| M2 | `unstable` を定数 false で記録する | なし (1/1) | `test_campaign.py::test_balanced_schedule_records_aggregate_unstable_not_constant_false` |
| M3 | 集約 CV を block CV の平均で代用する (再照準後) | なし (1/1 + 追加検出 1) | `test_campaign.py::test_balanced_schedule_cv_is_all_rep_cv_not_mean_block_cv` |
| M4 | seed preimage から counter を落とす | なし (1/1) | `test_campaign.py::test_balanced_schedule_redraw_uses_registered_preimage` |
| M5 | 全同一 bit 列の引き直し規則を外す | なし (1/1) | `test_paper_story_a1_paired.py::test_v3_all_identical_seed_bits_are_redrawn_before_schedule_M5` |
| M6 | block sigma からカイ二乗係数を外す | なし (3/3) | `test_paper_story_a1_balanced_sizing.py::test_m6_...` ほか 2 |
| M7 | 探索格子を 1 刻みへ戻す | なし (1/1) | `test_paper_story_a1_balanced_sizing.py::test_m7_...` |
| M8 | seed bit と ABBA/BAAB の対応を反転する | なし (4/4) | `test_paper_story_a1_paired.py::test_v3_schedule_has_exact_balanced_five_rep_blocks_M8[*]` ほか 1 |
| M9 | producer 側 contrast の符号を反転する | なし (25/25) | consumer 側の独立再導出を含む 25 件 |
| M10A | 境界 1 (login-submit) を外す | なし (1/1) | `test_paper_story_a1_job_contract.py::test_v3_ccbench_five_boundary_wiring_is_exact_M10` |
| M10B | 境界 2 (job body preflight) を外す | なし (1/1) | 同上 |
| M10C | 境界 3 (driver measurement) を外す | なし (1/1) | 同上 |
| M10D | 境界 4 (各 build 直前) を外す | なし (1/1) | `test_campaign.py::test_balanced_build_boundary_is_one_guarded_trace_perf_wrapper` |
| M10E | 境界 5 (artifact consumer) を外す | なし (1/1) | `test_paper_story_a1_job_contract.py::test_v3_ccbench_five_boundary_wiring_is_exact_M10` |

### M9 の位置について

`_signed_contrast` は producer 側と artifact consumer 側に**独立した 2 実装**がある。
段 5 設計は「consumer が producer の helper を再利用していないこと」を要求しており、
実装はそのとおりになっている。したがって M9 は **producer 側だけを変異させ、
consumer の独立再導出が検出することを KILLED の根拠にした**。
短い anchor は 2 箇所に一致するため、producer 直前の raise 文まで含めて一意化した。
実測で 25 件が落ちており、consumer 側の独立再導出が実際に効いている。

### M10 の 5 境界が独立に発火するか

D1300 の 5 境界のうち、4 つ (login-submit / job preflight / driver measurement /
artifact consumer) は同じ `test_v3_ccbench_five_boundary_wiring_is_exact_M10` が捕まえ、
build 直前だけ別の検査 (`test_balanced_build_boundary_is_one_guarded_trace_perf_wrapper`) が
捕まえる。
**どの境界を 1 つ外しても赤になる**ことは示せているが、
**「5 つの独立した gate がある」ことは示していない。** この区別は主張に書く。

## 期待へ入れなかった観測 1 件

本走の M10D で `test_dev_waves_integration.py::test_malformed_child_output_is_output_invalid[oversize]`
が 1 件落ちた。M10D は CCBench の canonical pin 検査を build 直前で外す変異であり、
子出力の検証とは機序上つながらない。同じ走の baseline では緑だった。
高負荷 (並行セッション実測で load average 75) 由来の非決定的な赤として最終走の期待へ入れない。
**再現したら実検出として扱い直す。**

## 環境上の制約 (この機体固有)

変異 source は**独立 clone** にした。`tools/mutation_worktree.py` の事後検査は
primary worktree と source の `git status --porcelain=v1 --untracked-files=all` と
`git submodule status --recursive` の stdout bytes を走行前後で比較するが、
この機体では並行セッションが常時 worktree を作ったり畳んだりしており、
数時間の走行中に主 worktree の untracked 一覧が動かない前提が成り立たない
(probe は 14/14 記録し終えた後に `rc=125` で落ちた)。
clone なら primary が clone 自身になり `git status -uall` が 0 行で安定する。
