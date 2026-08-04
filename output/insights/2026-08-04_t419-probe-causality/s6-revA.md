現行の閾値演算と `INVALID ⇒ NOT_EVALUATED` の返却分岐自体は裁定どおりです。しかし、実験成立条件を検証しないまま `VALID+CONFIRMED` に到達でき、事前登録変異にも生存があります。静的レビューのみで、pytest は実行していません。

### R1-1

**主張:** M1 は生存する。`no_effect` と `all_out_of_band` は paired contrast 以外の条件でも REFUTED になる過剰決定 fixture である。

**file:line:** [t419_probe_causality.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:348)、[t419_probe_causality.py:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:750)、[t419_probe_causality.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:808)

**具体的な失敗シナリオ:** `no_effect` は pinned rate=0 と positive contrast=0 の二重失敗、`all_out_of_band` は nonpinned rate=1 と positive contrast=0 の二重失敗である。M1 で contrast を恒真化しても、前者は pinned 条件、後者は nonpinned 条件で REFUTED のままなので全テストが緑になる。

**成果物影響:** paired contrast が実効 gate でなくなり、正の CPU が45以下でも、残り2条件だけで `CONFIRMED` になる受理集合へ拡大する。

**強度:** 強。fixture 値から静的に確定する。

**最小の是正案:** 48×5を保ち、3 CPUだけ pinned=1/5・control=47/235、残る45 CPUを pinned=5/5・control=0 とする fixture をテスト側へ置く。pinned=228/240、nonpinned=141/11280、positive=45となり、contrast だけが偽になる。

### R1-2

**主張:** pytest の oracle が driver 内にあり、裁定値・境界演算を独立に固定していない。

**file:line:** [test_t419_probe_causality.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:19)、[t419_probe_causality.py:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:734)、[t419_probe_causality.py:795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:795)

**具体的な失敗シナリオ:** 外側の8テストはすべて `assert_synthetic_fixture()` を呼ぶだけである。定数を `0.95→0.90`、`0.05→0.10`、`46→45` と変更しても現在の fixture の verdict はすべて不変で緑になる。`>=→>`、`<=→<`、46判定の `>=→>` も、fixture が境界上にないため生存する。driver 内 assertion の削除・同期変更も外側から検出できない。

**成果物影響:** 裁定と異なる閾値や開閉区間で `causal_verdict` の受理集合が拡大・縮小しても、テストが承認してしまう。

**強度:** 強。

**最小の是正案:** 期待値をテストファイルへ移し、定数そのものと、228/240、564/11280、46/48、band上下限ちょうどを独立に assert する。偶数個 median、NaN/inf、空 vector も外部 oracle で固定する。

### R1-3

**主張:** A1 の validity は総読取数しか検査せず、48 CPU×5、pin順、anchorを成立条件にしていない。

**file:line:** [t419_probe_causality.py:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:484)、[t419_probe_causality.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:663)、[s4-adjudication.md:15](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s4-adjudication.md:15)

**具体的な失敗シナリオ:** 240読を CPU 0〜45だけへ配り、各 target だけを帯外にする。CPU 46・47を一度も pin しなくても、read count、affinity、vector は検査を通り、pinned=1、nonpinned=0、positive=46なので `VALID+CONFIRMED` になる。さらに合成正例は anchor 0件・`pin_order` なしでも CONFIRMED である。

**成果物影響:** 「48 CPUを固定seedで全掃引し、各 affinity 変更後をwarm-upした」という未実施の介入を根拠に因果結論が受理される。

**強度:** 強。

**最小の是正案:** CPUごとに primary 5件、targetがallocated集合内、reader=target、anchorがCPUごとに1件、`pin_order` が48 CPUの permutationであることを validity に追加する。欠落CPU fixture は `INVALID+NOT_EVALUATED` とする。

### R1-4

**主張:** busy/sham 介入成立を証拠から再検査せず、自己申告の `"VALID"` だけを信頼している。

**file:line:** [t419_probe_causality.py:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:547)、[t419_probe_causality.py:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:691)、[s4-adjudication.md:33](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s4-adjudication.md:33)

**具体的な失敗シナリオ:** 現在の `confirmed` 合成正例には child PID、affinity、liveness、tick増分が一切ない。それでも pairの `status="VALID"` と contentionの `intervention_status="VALID"` だけで validity を通る。statusと証拠が矛盾する入力も同様である。

**成果物影響:** A2/A3介入が未成立でも execution全体がVALIDとなり、因果 verdict と2×3表を台帳へ記録できる。

**強度:** 強。

**最小の是正案:** statusを入力として信用せず、各 sham/busy child証拠から affinity・liveness・wait・busy tick閾値を純粋関数で再計算する。証拠欠測・status不一致 fixture を追加する。

### R1-5

**主張:** 欠測・例外に対する fail-closed が不完全で、parser例外はVALIDへ、band欠測は未捕捉例外へ進む。

**file:line:** [t419_probe_causality.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:559)、[t419_probe_causality.py:1571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1571)、[t419_probe_causality.py:574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:574)

**具体的な失敗シナリオ:** canonical parser import例外は `"unavailable"` に変換されるが、validity が拒否するのは `"mismatch"` だけである。実際に合成 `confirmed` も `"unavailable"` のまま通る。また `pin_verified=True, band=None` は分析をskipした後、`causal_metrics(..., None, ...)` で未捕捉例外となり、`INVALID+NOT_EVALUATED` を返さない。

**成果物影響:** 前者はparser一致未立証の値で `CONFIRMED` を受理する。後者はresult参照そのものを欠落させ、3終端契約を壊す。

**強度:** 中。経路は静的に確定するが、実環境でのimport失敗・不整合calibrationは未実測。

**最小の是正案:** crosscheckは `status=="match"` かつ保存3ファイルすべてmatchだけを受理する。bandを validity 内で検証し、causal analysis例外も必ず `INVALID+NOT_EVALUATED` に落とす。

### R1-6

**主張:** 単独性 tracker は `/proc/stat` 差分を記録するだけで gate に使わず、短命競合を見逃す。

**file:line:** [t419_probe_causality.py:1218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1218)、[t419_probe_causality.py:1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1244)、[t419_probe_causality.py:1257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1257)

**具体的な失敗シナリオ:** 競合processが連続する2回のprocess snapshotの間に起動・終了すると、前後どちらのPID集合にも現れない。CPU tickは `/proc/stat` deltaへ出るが `_competitors` 判定には使われず、`competition_detected=False` のままVALIDになる。なお `disallow_child()` が更新する `active_children` は `_allowed()` で使われず、過去child PIDも永久allowlistになる。

**成果物影響:** 外乱でA1帯外率が上がっても単独性gateを通り、誤った `CONFIRMED` を生成し得る。

**強度:** 中。検出漏れ経路は確定しているが、実ジョブでの発火と効果量は未実測なので因果影響の主張は弱い。

**最小の是正案:** process snapshotとCPU counterを入力にする純粋な競合判定を設け、未帰属tickをfail-closedにする。短命processの合成snapshot fixtureと、active child解除fixtureを追加する。

### R1-7

**主張:** α/β/γ表は入力集合の完全性を検査せず、空集合を「誤り0件」と記録できる。

**file:line:** [t419_probe_causality.py:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:258)、[t419_probe_causality.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:242)、[t419_probe_causality.py:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:547)

**具体的な失敗シナリオ:** top-level A2 reads=80とA3 contention reads=15を残しつつ、pairの`conditions`とA3の`blocks`を空にしてstatusだけVALIDにする。validityは通るが、α should-rejectは `evaluated=0, false_negative=0`、β/γはA2 busy 40件を無視して15件だけになる。またshould-passはA0/A3 quietに限定され、quietなA2 shamを使わない。

**成果物影響:** 2×3表の分母と偽陰性数が過少になる。γについて、評価されたpassは正しく `false_negative_missed_deviation_count` に入るため直接の意味反転はないが、欠測した40件は偽陰性0件として見えなくなる。

**強度:** 強。

**最小の是正案:** pairごとにsham/busy各5件、A3 block数・各5件、flat readsとの同一性をvalidityで照合する。期待件数0・不一致は集計値0ではなくINVALIDにする。should-pass領域へshamと非自明なself-only例を入れる。

### R1-8

**主張:** 実装は事前登録総量430読に、未裁定のA3 contention 15読を追加している。

**file:line:** [s4-adjudication.md:34](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s4-adjudication.md:34)、[t419_probe_causality.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:55)

**具体的な失敗シナリオ:** 定数表の合計は30+240+30+50+80+15=445である。裁定は「総量据置」、A3=10×5=50、合計約430と事前登録しているため、combined armの15件は配分根拠がない。

**成果物影響:** raw read countは430でなく445となり、α should-rejectに3 block、β/γに15観測が追加され、2×3表の重みと受理表の実測値が事前登録から変わる。

**強度:** 強。

**最小の是正案:** 段4へ巻き戻し、A3の既登録50件をquiet/combinedへどう配分するか明文化してから、その総量だけを実装する。445件を既登録済みとして記録してはならない。

### R1-9

**主張:** A2のbusy/sham条件間に裁定済み1秒cooldownがない。

**file:line:** [s4-adjudication.md:24](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s4-adjudication.md:24)、[t419_probe_causality.py:1830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1830)、[t419_probe_causality.py:1869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1869)

**具体的な失敗シナリオ:** busyが先のpairでは、child停止・wait直後にsham childを開始する。1秒sleepはA2 arm全体の終了後にしかなく、直前busyのP-state・熱履歴がshamへ持ち越される。

**成果物影響:** `busy_minus_sham_target_mean_mhz`、帯外率、2×3 should-reject値が条件順の持ち越しを含む値へ変わる。

**強度:** 契約違反は強。実際のバイアス方向・量は未実測なので、その部分は弱い。

**最小の是正案:** 各childのterminate→wait→liveness確認後、次条件の開始前に1秒cooldownを置き、時刻を記録する。

### R1-10

**主張:** M2〜M6のうち、M3・M4・gate側M5だけは明確にkillされる。M2とM6は事前登録粒度ではkillを主張できない。

**file:line:** [t419_probe_causality.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:766)、[t419_probe_causality.py:795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:795)、[s4-adjudication.md:80](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s4-adjudication.md:80)

**具体的な失敗シナリオ:**

| 変異 | 静的判定 |
|---|---|
| M2 | 欠測検査全体を消せば `missing_reads` が赤にする。一方、top-level例外検査だけを無効化する変異は生存する。完全観測＋`exceptions=[...]` のfixtureがない。 |
| M3 | kill。101.0は[98,102]内だがmedian/2101厳密一致ではないため直接assertが赤。 |
| M4 | kill。累積最大では110が残り、最終canonical passが偽になる。 |
| M5 | `competition_detected→INVALID` のconsumer gate無効化はkill。ただしtracker側の検出無効化は、fixtureがflagを直接設定するため生存する。 |
| M6 | literalにshould-reject行だけを常時rejectへすると生存する。テストはshould-pass行しかassertしない。共有predicate全体を常時rejectへする場合だけ`overreject`が赤にする。 |

**成果物影響:** mutation matrixへ実在しないKILLED証拠と誤った期待nodeが記録され、M2例外経路・M5 detector・M6行局所の弱体化を見逃す。

**強度:** 強。ただし実際のmutation-spec anchorは今回の指定読取物にないため、M2/M5/M6は上記の位置別判定である。

**最小の是正案:** M2を欠測・例外に分割し、完全観測＋例外1件fixtureを追加する。M5は純粋detector fixtureを追加する。M6はα/β/γそれぞれの共有predicateをanchorにし、quiet・self-only should-passを別nodeで直接通す。

## 総括

- (a) **だめ**。現在の算術式は正しいが、未成立の介入・不完全な掃引でも `VALID+CONFIRMED` を生成できる。
- (b) must-fix 1: 外部oracle化し、M1専用の単一理由fixtureと全境界fixtureを追加する。
- (b) must-fix 2: A1配置・anchor、介入証拠、parser、nested block、単独性をfail-closed validityへ入れる。
- (b) must-fix 3: 430読の配分と2×3表の母集団を段4へ戻して固定する。
- (c) 生存: **M1**。加えてM2の例外-only、M5のdetector-side、M6のshould-reject行局所版も生存する。
- M3、M4、`competition_detected` consumer gateを消す狭義M5はkillされる。