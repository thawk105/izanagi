# 留保値の既存出現の検索 (親の実行、2026-09-22 09:5x JST)

- 実行場所: wave worktree `.claude/worktrees/dev-wave-t2851-transfer-prereg`、HEAD = local main `8fd2a2f5c775954d6a32cee019ac7ce276298e4d`。
- 対象: git 管理下の `output/`・`docs/`・`orchestrator/`・`tools/` (`git grep` は未追跡 file・別 worktree・repo 外を見ない)。
- 各 block は実行した command と、その stdout の全文である。stdout が空の command は「(出力なし)」と書く。
  例外は 2 つで、thread 12/24 の行内容の block と silo_ladder_rung1 の receipt の block は、8b holdout の値を
  key=value の書式で写さないために要約した (各 block の注に書いた)。
- 式は key=value・JSON の両書式 (`"key": "value"`・`"key":value`) を拾うように `["=: ]+` で区切りを許し、値の直後に数字が
  続く場合 (例: 250) を除く。

```
$ git grep -l -E -e 'ycsb_rratio["=: ]+"?(25|75)"?([^0-9.]|$)' -- output docs orchestrator tools | head -20
(出力なし)
```

```
$ git grep -l -E -e 'ycsb_zipf_skew["=: ]+"?(0\.7|0\.99)"?([^0-9]|$)' -- output docs orchestrator tools | head -20
(出力なし)
```

```
$ git grep -l -E -e 'thread_num["=: ]+"?(12|24)"?([^0-9]|$)' -- output docs orchestrator tools | head -20
docs/failures.md
output/insights/2026-08-25/t525-holdout-binding/README.md
output/insights/2026-08-25_ss2pl-lock-protocol-study/figures/ss2pl_abort_rate.provenance.json
output/insights/2026-08-25_ss2pl-lock-protocol-study/figures/ss2pl_paired_effects.provenance.json
output/insights/2026-08-25_ss2pl-lock-protocol-study/figures/ss2pl_scalability.provenance.json
output/insights/2026-08-25_ss2pl-lock-protocol-study/raw/controls.json
output/insights/2026-08-25_ss2pl-lock-protocol-study/raw/replication.json
output/insights/2026-08-25_ss2pl-lock-protocol-study/raw/sweep.json
```

```
$ git grep -n -E -e 'thread_num["=: ]+"?(12|24)"?([^0-9]|$)' -- output/insights/2026-08-25/t525-holdout-binding/README.md docs/failures.md | cut -c1-220
docs/failures.md:18278: (本文は下の注で要約)
output/insights/2026-08-25/t525-holdout-binding/README.md:83: (本文は下の注で要約)
```

(上の 2 hit は、8b の H1 の admission を持ったまま別の読み比率や thread 24 の引数で走る形を例示した文で、測定ではない。
本文は 8b holdout の読み比率を key=value の書式で含むので、本 insight では逐語を写さず path と行番号だけを残す
(F1013 の再発防止)。原文は上の 2 file の該当行にある。)

```
$ git grep -l -E -e 'ycsb_max_ope["=: ]+"?20"?([^0-9]|$)' -- output docs orchestrator tools
(出力なし)
```

```
$ git grep -l -E -e 'ycsb_max_ope["=: ]+"?(5|20)"?([^0-9]|$)' -- output docs orchestrator tools | head -20
docs/decisions.md
docs/paper-story/figures/fig8_b10_static_tail_not_observed.provenance.json
docs/paper-story/figures/fig8b_b10_static_tail_cohort2.provenance.json
docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md
docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md
docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md
orchestrator/campaign/p3_s4_loop.py
orchestrator/campaign/paper_story_a2_certification.v2.json
orchestrator/campaign/paper_story_a6_certification.v2.json
orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json
orchestrator/campaign/pipeline.py
orchestrator/campaign/s3_lock_coverage.py
orchestrator/campaign/s3_mocc_lock_coverage.py
orchestrator/campaign/s5_permutation_coverage.py
orchestrator/campaign/s8a_trigger_coverage.py
orchestrator/campaign/silo_ladder_rung1.py
orchestrator/qualification/artifacts.py
orchestrator/tests/fixtures/README.md
orchestrator/tests/test_b5_tier0.py
orchestrator/tests/test_t126_pegasus_tools.py
```

(`head -20` で切った。操作数 20 の単独検索は上のとおり 0 件なので、hit は操作数 5 である。親は各 file の中身を
1 件ずつは読んでいない。`orchestrator/campaign/pipeline.py` の `CorrectnessWorkload` (200 レコード・4 thread・操作数 5・
read-modify-write・extime 1) と同じ小規模検証 workload の定義・記録と推測するが、全 file について確かめてはいない。)

```
$ git grep -l -E -e 'ycsb_rmw["=: ]+"?(1|true)"?([^0-9a-z]|$)' -- output docs orchestrator tools | head -30
docs/archive/worklog-phase3-0825-947.md
docs/decisions.md
docs/paper-story/figures/fig8_b10_static_tail_not_observed.provenance.json
docs/paper-story/figures/fig8b_b10_static_tail_cohort2.provenance.json
docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md
docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md
docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md
orchestrator/campaign/p3_s4_loop.py
orchestrator/campaign/paper_story_a2_certification.v2.json
orchestrator/campaign/paper_story_a6_certification.v2.json
orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json
orchestrator/campaign/pipeline.py
orchestrator/campaign/s3_lock_coverage.py
orchestrator/campaign/s3_mocc_lock_coverage.py
orchestrator/campaign/s5_permutation_coverage.py
orchestrator/campaign/s8a_trigger_coverage.py
orchestrator/campaign/silo_ladder_rung1.py
orchestrator/campaign/t152_write_intent_coverage.py
orchestrator/qualification/artifacts.py
orchestrator/submission_gate/_semantic_validator.py
orchestrator/tests/fixtures/README.md
orchestrator/tests/test_b5_tier0.py
orchestrator/tests/test_holdout_observation.py
orchestrator/tests/test_s8b_floor_campaign.py
orchestrator/tests/test_s8b_freeze_io.py
orchestrator/tests/test_silo_ladder_rung1_evidence.py
orchestrator/tests/test_t126_pegasus_tools.py
orchestrator/tests/test_t126_qualification_artifacts.py
orchestrator/tests/test_t810_runner_policy.py
output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json
```

(`head -30` で切った。性能測定として留保条件 bal-rmw1 と同じ引数の組を持つのは、下の silo_ladder_rung1 の run receipt で、
これは調査子の報告を親が 1 件開いて確かめた。他の hit の多くは小規模検証 workload の flag と推測するが、全件は読んでいない。)

```
$ cat output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/runs/perf-04-W-hw-stock-r2/run.command.json | head -40
(argv の要約) read-modify-write 真、Zipf skew 0.9、レコード 1,000,000、操作数 10、thread 48、extime 3。
(読み比率の引数は無い = CCBench 既定の 50)  elapsed_monotonic_s 3.4217203090083785、completed_at_utc 2026-07-29T08:17:48.659174Z、returncode 0
```

(この block だけは全文でなく、親が必要な field を抜き出した要約である。原本は上の path にある。)

## [T-2849] の比較基盤の設計書の検索 (段 6 焦点再レビュー F1 への対応、2026-09-22 20:3x JST)

local main `eef04f5a7fae95153e6253d362ce872555e65d4e` を wave 木へ取り込んだ後 (merge `33a13d503`) に、同書 (最終版 commit
`449045e764cd2fc150077b945fbd0d0b9cfdbd26`、`git merge-base --is-ancestor` で取り込んだ main の祖先であることを確認) を検索した。

```
$ grep -n -E "0\.7|0\.99|rr25|rr75|読み比率 ?(25|75)|thread ?(12|24)|(12|24) ?thread|max_ope|操作数|rmw|read-modify-write|skew" output/insights/2026-09-22/t2849-comparison-harness-design/README.md | cut -c1-160
333:- MOCC の動作点の較正 (calibrator)。参照した記録 (`patches/README.md` の T-2294 の記載と `output/insights/2026-09-21/t2844-mocc-xp-hook-b
```

(hit の 333 行は MOCC の既存の certified 記録 (T-2294: tuple 200・extime 1 秒・thread 1 / 4・読み比率 0・rmw) を述べる行で、
留保条件を学習・選択に使う記述ではない。)

```
$ grep -n "1M records・48 threads・3 秒\|転移 (\[T-2851\]\|stock 比で報告" output/insights/2026-09-22/t2849-comparison-harness-design/README.md | cut -c1-200
48:- 未知条件への転移 ([T-2851] が別に扱う)。他 protocol・他環境での成立。
64:手法によって評価経路を変えない。S1 の経路は B-5 と同じで、`p3_s4_loop --run-iteration <proposal>` → 文法・帰属整合 (value == literal)・diff 検疫 → Tier0 (perf
335:- 既知最良: `p2_2_flag_opt` に当たる MOCC の実測は、調査子が decisions・worklog・`orchestrator/` を関連語で検索した範囲では見つからなかった。MOCC_SPACE (BA
```

(48 行は同書 §1.3、64 行は §2.3 (同じ行の後半に「動作点は較正済みの 1M records・48 threads・3 秒・5 rep、workload は write-heavy /
balanced / read-heavy」)、335 行は §9.3 (同じ行の後半に「MOCC の比較は stock 比で報告し、既知最良の参照が無いことを明記する」)。
後半は `cut -c1-200` で切れているので、親が同書の該当行を別に読んで確かめた。)

## 調査子 (sonnet、read-only) の検索

既知結果の棚卸しは調査子にも依頼した。子の報告の要点は `facts.md` の 9 に写した。子が使った検索式は子の報告に
書かれたもの (例: `"-ycsb_rratio=(25|30|40|60|70|75|90)"`、`"-ycsb_rmw=true"`、`"-thread_num=(1|2|4|...|44)"`、
`"-ycsb_max_ope=(1|5)"`、`"-ycsb_tuple_num=(2000000|4000000)"`、`tpcc_silo\.exe|tpcc_mocc\.exe|"-warehouse`) で、
親は子の実行を再現していない。上の親の検索は、留保の値に限って独立に行った。
