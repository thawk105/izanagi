# 親が取った実測値 (下書き。段 7 で insight へ移す)

すべて 2026-09-04 に Pegasus login (pegasus02) から既存 artifact を読んで得た。新規の走行ではない。

## 1. 当日 9 走の shard 別 wall 分解 (`/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/shard-N/{junit.xml,report.json}`)

wall = junit testsuite の `time` (pytest session、collection 開始〜teardown 終了)。
maxocc = report.json `worker_occupancy` の最大 (worker ごとの setup+call+teardown 合計)。
sum/48 = 全 worker 占有の和 / 48。

```
digest(8)  時刻  shard host      wall  maxocc(items) 2nd  sum/48
8ec6c054  15:58  0 bnode142     287   149(2)        146  126
                 1 bnode146     188   131(13)       117  115
                 2 bnode062     219   162(42)       119   96
4ce68c3c  16:20  0 bnode014     251   152(2)        151  129
                 1 bnode008     193   120(118)      120  118
                 2 bnode041     212   152(42)       104   86
de56d7b3  16:27  0 bnode068     333   187(2)        185  160
                 1 bnode094     275   214(3)        207  205
                 2 bnode062     293   232(42)       194  149
af8d2d2c  16:30  0 bnode010     369   162(2)        157  136
                 1 bnode037     170   108(3)        102  100
                 2 bnode017     226   164(42)       145  100
0b0f9958  16:37  0 bnode003     274   179(2)        178  155
                 1 bnode002     178   119(38)       115  113
                 2 bnode019     215   157(42)       116   88
3537e8a6  16:51  0 bnode021     345   150(2)        147  123
                 1 bnode037     184   121(5)        119  117
                 2 bnode023     218   149(42)       125   88
42da05c5  16:52  0 bnode042     303   159(3)        159  136
                 1 bnode041     214   156(3)        154  151
                 2 bnode068     199   142(42)        97   80
f7673695  21:16  0 bnode009     412   233(2)        160  140
                 1 bnode002     185   118(91)       118  117
                 2 bnode003     216   159(42)       119  100
fed009ef  21:33  0 bnode010     356   234(2)        229  199
                 1 bnode002     265   195(3)        187  185
                 2 bnode003     221   163(42)       119  103
```

読み:
- shard 1/2 の wall − maxocc は 57〜73 秒でほぼ一定 (collection + 起動 + teardown)。
- shard 0 の wall − maxocc は 95〜207 秒で、走ごとに大きくぶれる。maxocc とは相関しない。
- shard 0 の maxocc は常に item 2 個の worker (t080 stub-free e2e の最重量 node)。
- 占有は setup/call/teardown の和なので、`pytest_runtest_protocol` wrapper 内 (conftest 2073-) の
  real-repo lock 待ちは占有にも junit にも含まれない。real-repo group は shard 0 に載る。

## 2. 21:16 走 shard-0 の worker 占有 (report.json)

48 worker、和 6703 秒、最大 232.8 秒 (gw27、item 2)、中央 133.1、最小 132.1。上位 5:
gw27 233 / gw16 160 / gw22 158 / gw9 156 / gw24 154。

## 3. real-repo group は worker に固定されていない (D1593 鎖 1 の反証)

- `orchestrator/tests/conftest.py:2061` `_strip_real_repo_loadgroup_suffix` が、
  `pytest_collection_modifyitems` wrapper の yield 後に process-memo 4 node 以外の `@real-repo`
  suffix を剥がす (commit 5ac638955、2026-08-26「受入の real-repo 排他鎖を資源別 RW lock へ細分化する」)。
- 21:16 走 shard-0 report.json `group_to_workers["real-repo"]` は gw0, gw1, gw11, gw12, gw13, gw14, gw15,
  gw16, gw18, gw19, gw2, gw22, gw25, gw27, gw29, gw3, gw30, gw31, ... の 26 worker 以上。
  `campaign-repository-scan` は gw0、`s8c-predicate-snapshot` は gw3、`s8c-preregistration-candidate` は gw1。
- したがって D1593 が「鎖 1 = 303.7 秒」と数えた group 直列は、裁定日 (09-04) の 9 日前から存在しない。
  D1618 (T-2297) が承認した「worker grouping を read/write で割る」実装は、現物では既に
  suffix strip + `_real_repo_locks` の LOCK_SH/LOCK_EX で実現されている。

## 4. certified_evidence 鎖の現在値 (21:16 走 shard-0 junit、setup+call+teardown)

17 consumer の合計 ≈ 82 秒 (18.6 / 17.6 / 15.9 / 6.0 / 4.7 / 3.3 / 3.2 / 3.2 / 2.7 / 1.9 / 0.7 x 5 / 0.6 x 2)。
ledger (`acceptance_duration_ledger.json`) は同 node を 18〜19 秒で持つ (m07 / m13 / m09 が各 18 秒) が、
junit では m07 / m13 が 0.7 秒。ledger 由来の 258.1 秒は現況ではない。

## 4b. M-A: 全 suite 非 shard 走の timeline (bnode095、2026-09-04 22:20、HEAD 1b7822110、`-n 48`、非受入形)

`measure/run_a.py` + `tl_plugin.py` (controller の `pytest_runtest_logreport` で report.start/stop/worker を記録)。
`analyze_a.py` の出力:

```
events=61348 reports=61298 workers_collected=48
configure->first worker_collected: 117.5  ->last: 119.0
configure->sessionfinish (wall): 487.1
first test start after configure: 119.1; last stop after configure: 480.3
worker  span  busy  inner_gap  lead  tail  items
 gw32   361.2  332.9     28.0    0.0    0.0   397
 gw24   361.0  335.5     25.2    0.0    0.2   354
 (48 worker すべて span 359.9〜361.2、busy 330〜343)
sum busy=15961 sum inner_gap=1301 workers=48
top gaps (> 2.0s): なし
top hidden time inside a test (span - phases) (> 2.0s): なし
```

読み: wall 487 = collection/起動 119 + test 区間 361 + 終了 7。48 worker は完全に均衡し、report の
setup/call/teardown に現れない待ち (lock 待ちなど) は 2 秒超が 0 件。inner_gap 28 秒/worker は
item 遷移あたり 0.07 秒の xdist scheduling 費用。**非 shard 全走では「見えない lock 待ち」は存在しない。**
pytest rc=1 は `test_dev_wave_cleanup.py` の 44 赤 (占有走査、非受入形・本 session の環境差) で、
本 wave の差分 (0) には帰属しない。

node 別 (setup/call/teardown、秒):
- certified_evidence consumer の setup: 13.3 (manifest_driver) / 12.5 (non_guarantees) / 11.6 (m01) / 11.1 (m17) /
  11.0 (assembly) / 10.8 (m04) / 5.4 (m13) / 4.5 (m03) / 4.2 (m12) / 4.1 (m10) / 1.9 (m07) / 他 <1。
  合計 ≈ 90 秒。これが現行 LOCK_EX 鎖の実測 (seed 生成 + 排他待ち)。junit の値と整合。
- t080 stub-free e2e: 143.1 / 138.2 / 133.6 / 132.6 / 132.0 (call のみ、setup 0)。
  `test_never_issued_generator_tamper_reaches_public_driver_gate_g7` 139.5、`f28` 系 3 本 132〜133。
  受入 21:16 走の 155.7 / 151.6 / 147.4 と同帯。**48 worker 同時では isolated (ledger 55 秒) の 2.5 倍。**
- 全体最長: `test_role_sink_bytes_vary_only_at_declared_declassifications` 252.0 (受入 21:16 走では shard-2、82〜191 秒)。
- `test_real_repo_serialization.py` 57 node 合計 278 秒、最長 60.3 / 59.0。

## 4c. M-B: t080 stub-free e2e の phase 内訳 (bnode019、22:36 と 22:39 の 2 回、`-n 0` 単一 process、非受入形)

`measure/run_b.py` + `phase_plugin.py` (test module の helper / `migration.*` / `shutil.copytree` /
`subprocess.run` を包み、呼び出しごとの self time を記録)。5 node (single-defect 4 param + draft-finalize)、
5 passed、call 合計 rep1 165.7 秒 / rep2 179.6 秒。

node 別 call (rep1 / rep2、秒):
- single-defect[known-artifact] 72.4 / 67.5 (base 構築を含む: `_t080_stub_free_e2e_repo` 67.6 / 62.7、verify 4.9)
- single-defect[holdout-artifact] 4.6 / 4.8 (base は memo 済み。copytree base→test ≈ 2、verify 2.5)
- single-defect[ccbench-current] 15.2 / 15.5 (verify_receipt 4 回 = 11.7、git commit-tree/checkout 1.4)
- single-defect[unknownness-layer2] 4.4 / 5.3
- draft-finalize 69.0 / 86.5 (別 key で base をもう 1 度構築: 59.5 / 77.0、verify 7.1)

self time の内訳 (rep1 / rep2、秒、5 node 合計):
- 子 python `-I` (draft_receipt → validate_draft → finalize_receipt → git add/commit → verify_receipt → gate_check): **60.6 / 60.2** (base 1 回あたり ≈ 30)
- `migration.verify_receipt` (test 本体側): 27.4 / 27.4
- `git add -A` (2300 file): 14.0 / 14.0 (base 1 回あたり 7)
- `_copy_git_visible_output` + その配下の copytree (raw / verbatim / insights / ledgers / pages …): ≈ 21 / 27
- `git ls-files`: 3.1 / 4.0、`git commit`: 1.7 / 1.7、`git submodule add` (`git -c`、file transport): 1.1 / 1.2
- `orchestrator/` の copytree: 1 秒未満 (集計の閾値以下)

**結論 (T-2273 (2) の問い「build か直列性検査か外部 command か」):** どれでもない。CCBench の build は
走らず、直列性検査 (verifier) も走らない。時間の本体は (a) 受領証発行の子 python (base 1 回 ≈ 30 秒、
中で closure の hash と git 走査)、(b) `git add -A` 7 秒、(c) git 可視 output の複製 ≈ 10 秒、
(d) `verify_receipt` 1 回 2.3〜11.7 秒、である。base 構築 (60〜77 秒) は process 内 memo なので
**xdist worker ごとに繰り返され**、受入 48 worker では t080 の 11 node が 11 worker に散って各自 base を
組み、同じ node 上で git / copy が同時に走るため isolated の 2 倍超 (132〜155 秒) になる。

## 4d. M-C: shard-0 の file 集合 (111 file、6818 node 相当) だけを 48 worker で走らせた timeline (bnode080、22:43、非受入形)

```
configure->first worker_collected: 55.6  ->last: 56.1
configure->sessionfinish (wall): 250.5
first test start after configure: 56.1; last stop after configure: 245.8
worker  span  busy  inner_gap  lead  tail  items
 gw28   189.7  189.6      0.1    0.0    0.0     3
 gw22   180.5  180.5      0.0    0.0    9.1     2
 gw46   155.1  126.0     28.8    0.0   34.6   215
 gw27   155.0  155.0      0.0    0.0   34.6     2
 gw16   152.1  152.1      0.0    0.0   37.6     2
 (以下 item 2 個の worker が 138〜147)
sum busy=6380 sum inner_gap=342 workers=48
top gaps (> 2.0s): 20.1 秒 x 3 (test_slow_* の直前、gw38/40/46)
top hidden time inside a test: なし
```

読み: wall 250 = collection 56 + test 190 + 5。test 区間は item 2〜3 個の worker (t080 系の重量 node) が
決め、他の worker は 34〜51 秒早く終わる。**見えない待ちは無い。** 同じ file 集合の受入 shard-0 が
251〜412 秒なのに対し、非受入形では 250 秒。受入形との差 (0〜160 秒) は受入 plugin 側
(全 20452 node の collection と deselect、LPT 並べ替え、report 生成) と host 差の混合であり、
本測定では切り分けられない。

注意 (計測汚染): この走は実装子が `test_p3_b4_raw_record_producer.py` を編集中 (mtime 22:45:13) の
作業木で走った。`test_m18_symlinked_evidence_is_rejected_with_regular_control` の赤 1 件と同 file の
所要は HEAD の値ではない。timing の構造的結論 (shard-0 集合の wall 分解) には影響しない。
`test_dev_wave_cleanup.py` の 44 赤は M-A と同じ非受入形の環境差。

## 5. t080 stub-free e2e の中身 (現物読解)

`test_s8b_oracle_driver.py:1010 _build_t080_stub_free_e2e_repo`: git init、`orchestrator/` 全体の
copytree、`_copy_git_visible_output` (git 可視 output の copytree)、basis file の copy、
`git submodule add` (CCBench を file transport で clone)、checkout pin、`git add -A`、commit、
`inspect_receipt_history`、子 python で draft→finalize→commit→verify→gate_check。
`:893 _t080_stub_free_e2e_repo` が process 内 memo (worker ごとに base 1 回)、test ごとに base を copytree。
docstring の自己申告は「36MB / 2300 ファイル、1 回 15〜22 秒」。build も直列性検査も含まない。
ledger 55 秒に対し 48 worker 全走では 145〜153 秒 (21:33 走では 216〜226 秒)。

## 6. 受入 (2026-09-05 00:24、canonical、K=3、48 worker) と同時刻の対走

本 wave (新 lock、tested_main 0679f61f4 / tested_tip 7b585a1f1、child-green 20488 passed / 68 skipped):

```
shard 0 bnode035 wall 303.4 maxocc 162(items 3) sum/48 148
shard 1 bnode047 wall 179.3 maxocc 112(items 136) sum/48 110
shard 2 bnode038 wall 204.5 maxocc 139(items 42) sum/48 80   <- test_p3_b4_raw_record_producer.py (50 node) はここ
```

同時刻の別 wave (旧 lock、00:23):

```
shard 0 bnode009 wall 331.9 maxocc 244(items 2) sum/48 225
shard 1 bnode017 wall 203.3 maxocc 145(items 2) sum/48 140
shard 2 bnode018 wall 223.4 maxocc 164(items 42) sum/48 104  <- 同 file (40 node) はここ
```

`test_p3_b4_raw_record_producer.py` の node 所要 (junit、上位、秒):

```
新 lock (本 wave)                                         旧 lock (別 wave)
61.3 test_positive_201_block_certified_preserves...      88.2 test_positive_201_block_certified_preserves...
59.7 test_positive_201_block_all_terminal_records_absent 87.4 test_positive_201_block_all_terminal_records_absent
28.6 test_non_guarantees_name_the_residual_lock...       31.9 test_m16_judgment_fields_are_unknown_request_fields
27.8 test_m08_publication_rejects_reuse...               28.5 test_m18_symlinked_evidence_is_rejected...
25.4 test_m18_symlinked_evidence_is_rejected... (writer) 26.6 test_m08_publication_rejects_reuse...
23.8 test_m04_final_assembly_rejects_different...        23.6 test_manifest_driver_must_match...
23.0 test_m16_judgment_fields_are_unknown...             22.9 test_m02_planned_path_lookup...
19.7 test_m01_assembly_rederives_precursor...            22.8 test_m05_campaign_lock_classification...
18.3 test_m10_certified_off_digest_absence...            22.6 test_m01_assembly_rederives_precursor...
17.2 test_m17_terminal_receipt_validation... (writer)    20.2 test_m13_integer_reference...
16.3 test_m12_nonterminating_reference_ratio...          18.9 test_m17_terminal_receipt_validation...
15.4 test_m03_assignment_comes_from...                   17.9 test_m10_certified_off_digest_absence...
15.0 test_manifest_driver_must_match...                  17.0 test_m04_final_assembly_rejects_different...
14.4 test_assembly_rederives_judgments...                16.1 test_m12_nonterminating_reference_ratio...
11.2 test_m07_non_binary_exact_decimal_lexeme...         15.0 test_non_guarantees_name_the_residual_lock...
10.6 test_m13_integer_reference...                       14.2 test_assembly_rederives_judgments...
                                                         11.2 test_m07_non_binary_exact_decimal_lexeme...
17 consumer 合計 290.1                                    17 consumer 合計 345.9
```

読み: 同時刻の対走で consumer 合計は 346 → 290 秒、同 file の shard の wall は 223 → 205 秒。host が違うので統制比較では
ない。新 lock でも consumer が 10 秒以上かかるのは、最初の読み手が seed を EX で作る ≈ 10 秒の間に他の読み手が並んで待つ
(host あたり 1 回) ことと、書き手 2 本 (M17 17.2 秒、M18 25.4 秒) の EX 窓での待ち。21:16 走 (m07 0.7 秒) との差は、
consumer が時間的に散っていた (待ちが無かった) 走と、同時に集中した走の差であり、lock の設計差ではない。
小さい test (0.0〜0.4 秒) は両走とも変わらず、node 全体の一様な遅延ではない。
