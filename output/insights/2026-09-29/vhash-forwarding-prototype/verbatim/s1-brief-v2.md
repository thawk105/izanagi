# 段 1 brief v2 — md_6: Cicada 選択的 forwarding 試作 (GC 不変)

v1 (brief-stage1-v1-invalidated.md) と段 2・3 の成果物は DW-O13 の期限後成立で無効化した (2026-09-29 03:55 JST)。理由: 新 patch の `#if` macro は condition_meaning_gate の許可ドメイン (DEFINE_SPECS) へ登録しないと既存テストが赤になり、登録は既存 gate の受理集合を増やす = gate の新設に当たる。旧 plan・review は流用しない。

- wave: dev-wave-vhash-forwarding / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding
- 基準: izanagi HEAD = local main 51f896352 (2026-09-29 03:23 JST 取得)、CCBench gitlink 68106660686232781bca3be792a750d3e19d7a8a
- 依頼: /work/1/SFC/tanab/tmp/vhash-2026-09-29/md_6.txt と common.txt (逐語は同 dir)
- 仕様草案: /work/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/spec-draft-v1.md (P1 の本体)

## 研究前進
VHash 論文 (docs/paper-story-vhash、main 未着地のため /work/1/SFC/tanab/tmp/vhash-2026-09-29/docs-snapshot/) の中心機構
「cold 境界での選択的 forwarding」(出典メモ §12, §29 段階 3, §25 構成 C/F) の最初の実装と実測。完了判定 = inert patch・計測 driver が
land し、stock/C/F を同時刻に並べた条件別の forwarding 成功率・失敗理由内訳・throughput 比較の図が一次資料にある (全値「未検証の診断値」)。

## scope
- 入: 仕様 (P1)、patches/cicada-forwarding-variant.patch (C++、Codex author)、計測 driver と pytest (Codex author)、作図生成器、Pegasus 計測、一次資料、spool fragment。
- 入 (所有の拡張、P8): condition_meaning_gate.py の登録 (自分の macro の entry だけ)、test_condition_meaning_gate.py・test_ccbench_spawn_sites.py・test_p3_s4_loop.py の登録簿への自分の entry の追加と件数の更新。
- 外: 物理 hot 配置 (VHash)、GC 保護の前進 (段階 5)、固定 snapshot・range・insert・delete、Cicada 検査用トレース (md_3)、診断計器 (md_2)、submodule gitlink 前進、paper-story-vhash の編集、ledger.json、condition gate の意味論・判定の変更。

## 確定済みの裁定・事実
- ユーザー就寝中: needs input を出さず codex 賛否 2 立場で決める (マネージャー連絡 2026-09-29 03:23)。
- 合計 2 node 時間未満なら確認不要 (common.txt 3)。md_4 のモデル検査は待たない。md_3 検査器が段 9 前に main にあれば使う。
- Cicada の性能値はすべて「未検証の診断値」。serializable と書かない (common.txt 4、絶対規律 2)。
- 計数入り build の throughput は性能値に使わない (絶対規律 1)。

## 不変条件
- 既定 (macro 未定義) で patch 適用後の Cicada は stock と同じ前処理結果・挙動 (D18 第 4 類 inert)。
- GC 保護 (ThreadWtsArray / ThreadRtsArray / MinRts / MinWts) の計算は C/F でも stock と同一。
- pending 版の設置後に T.ts を変えない。最終保証は stock validation を最終 ts で走らせること (P1)。
- 同時刻の対照: stock/C/F は同じ job・同じノードで rep ごとに順序を回して交互に測る。

## 親の provisional 裁定 (攻撃対象)
- (P1) 仕様は spec-draft-v1.md のとおり (発火 = 見える版の物理位置 > K、目標 = 先頭 K 版の最古 committed、ts' = その wts 超の最小の自 thread 形式、
  早期確認は read set 全件 + write set 制約、rts は書かない、前進時に new_ver の wts 書換と read/write set の later_ver_ 破棄、localClock_=clock(ts')+1)。
- (P2) patches/ledger.json に entry を足さない: silo_ladder_rung1_contract.py:516-517 が entries != 1 を拒否し、test_silo_ladder_rung1.py の実 ledger テストが赤になる。patches/README.md の節だけで登録。
- (P3) macro 名に IZANAGI_ 接頭辞を使わない (合成 variant の命名慣行に合わせる。gate 登録 (P8) は接頭辞に関係なく必須なので、検査を逃れる効果は無い) (CICADA_FWD_MODE / CICADA_FWD_K 相当 / CICADA_FWD_COUNT / CICADA_LONGTX)。
  test_p3_s4_loop.py:8547 (B-3) は IZANAGI_ 裸 macro patch に ledger 登録を要求するが ledger は P2 で使えない。先例の variant (BACKOFF_FIXED, MOCC_TEMP_PREDICATE) も接頭辞なし。
  これが B-3 の回避 (検査逃れ) に当たるかを段 3 で攻撃させる。
- (P4) 長い tx の 2 型は patch 内の Cicada 専用 workload (ycsb_cicada.cc 側) で作り、FWD_MODE と独立の compile 時 macro + 実行時 flag にする
  (stock CC + 長い tx の build が要るため)。CCBench の include/ycsb.hh (全 protocol 共有) は変えない。長い tx を走らせる thread は末尾 L 本 (thread 0 = leader は通常)。
  既存の batch_* flag は表示だけで未実装、WORKER1_INSERT_DELAY_RPHASE は未定義名 thid を参照しており有効化で compile 不能 (transaction.cc:924, 実測でなくコード読み)。
- (P5) 計測条件: 48 thread、100 万件 (Pegasus 既存較正 output/env/pegasus/calibration/between_run_noise_t48_* と同じ。Silo 用の較正なので限界として記録)、
  zipf 0.9、rratio 50、max_ope 10、extime 3、clocks_per_us 2100、numactl --interleave=all。
  workload 3 型 {通常, 操作数が多い (長い thread L=4、1000 ops、rratio 90), 読み取り後に待つ (L=4、10 ops 読んだ後 1000 us 待つ)} × gc_inter_us {10, 100, 1000}
  × {stock, C, F} × perf 3 rep (順序を rep ごとに回転) + 計数 build 1 rep (C, F)。K=3 主、K∈{1,8} は操作数型 gc=100 だけ。
  workload ごとに 1 job (3 ノード同時) + 事前 smoke 1 job。見積り 1 job 約 20〜25 分 → 合計約 1.3〜1.6 node 時間 (< 2)。
- (P6) inert の証拠は計算ノードの smoke で「pin の stock と patch 適用 + 既定 macro の transaction.cc / ycsb_cicada.cc の前処理出力 (行番号 marker 除去) 一致」を記録する。gate にはしない。
- (P7) driver = orchestrator/campaign/vhash_forwarding_prototype.py (patchharness.checkout/applied + 自前 cmake、--target ycsb_cicada.exe、-DCMAKE_CXX_FLAGS="-D<macro>")、
  投入 = tools/pegasus/dispatch_compute.py --task generic、結果 = output/env/pegasus/vhash-forwarding-prototype/*.json、単独性 = pgrep -af 'ycsb_.*\.exe' を job 冒頭と各 run 直前。
  作図生成器は一次資料 dir に置く (実装面なので Codex author)。

- (P8) gate 登録: patch が持ち込む `#if` macro はすべて condition_meaning_gate.DEFINE_SPECS と CONDITIONAL_BRANCH_WITNESSES に登録し、
  test_condition_meaning_gate.py の supply domain 完全集合・件数 (43/44)・docstring の件数文 (61 / Forty-three) と
  test_ccbench_spawn_sites.py:2917 の inventory、test_p3_s4_loop.py の関連登録簿を追随させる。先例 = commit 3867e6ec5 (si の 2 macro 登録、6 file)。
  既存テストの期待値の「緩和」ではなく「登録簿への自分の entry の追加」であり、既存 entry と判定は変えない。md_6 の「所有」の外なので、
  必要最小 (自分の entry と件数だけ) に限り、理由を一次資料と decisions fragment に書く。md_2・md_3 も同じ登録を行いうるので、land 時の合流は両方の entry を残し件数を数え直す。
  macro の数は最小にする (登録面を減らす)。各 macro の `#if` は 1 つの owner TU に閉じる (DefineSpec.owner_tus は 1 個必須、condition_meaning_gate.py:1128-1131)。
- (P9) driver の build は silo_policy_coverage.py:305-340 と同じく macro ごとに supply/meaning の 2 腕を通して admission を得てから build する
  (test_ccbench_spawn_sites.py:2933 の cross product 検査)。ycsb binary の起動箇所は test_ccbench_spawn_sites.py の起動一覧
  (_DIRECT_CCBENCH_DIAGNOSTIC_SITES または _BOUNDED_RUN_ONCE_CLIENTS、:36-110) に登録する。
- (P10, DW-O13) gate の入力の実在: gate が読む owner TU の `#if` 行、cmake の compile command (cc/cicada/CMakeLists.txt の ccbench_add_protocol)、
  ycsb_cicada.exe target が Cicada で実際に解決されるかは、これまで Cicada で一度も通っていない (Cicada を build する driver は repo に無い)。
  段 5 の smoke の最初の手で gate の 2 腕を Cicada に対して実走し admitted を確認する。admitted にならなければ計測へ進まず原因を記録して段 4 へ戻る。

## 成果物
- patches/cicada-forwarding-variant.patch、patches/README.md の節、driver + pytest、作図生成器、計測 JSON、
  output/insights/2026-09-29/vhash-forwarding-prototype/README.md (仕様・knob・条件表・図・未検証の明記・次に要るもの)、spool fragment (worklog / decisions)。

## 分割方針
- 段 5 は所有 path の素集合 2 単位: A = patches/cicada-forwarding-variant.patch (C++)。B = driver・pytest・作図生成器・gate 登録と登録簿の追随 (P8/P9)。B は A の macro/flag/出力行の名前を段 4 の plan v2 で固定して並行。
- 計測は段 6 の受入後、段 7 の前に行う (計測値は実装 commit に束縛)。
- 受入・実測環境: pytest は tools/dev_wave_wait.py acceptance (計算ノード dispatch)。build・計測は Pegasus 計算ノード (login で計測しない)。

## 変更面の実アンカー表
| 面 | 実アンカー |
|---|---|
| read 経路 | external/ccbench/cc/cicada/transaction.cc:79-138 (read_internal), :144-190 (read) |
| 検証 | transaction.cc:463-609 (validation), include/transaction.hh:247-293 (precheckInValidation), :295-308 (readTimestampUpdateInValidation) |
| 書込み | transaction.cc:196-298 (update), include/transaction.hh:217-245 (newVersionGeneration) |
| timestamp | include/time_stamp.hh:24-40, transaction.cc:34-43 (begin), :745-773 (abort) |
| GC | transaction.cc:806-893, util.cc:281-322 (cicadaLeaderWork) |
| workload | external/ccbench/include/ycsb.hh:55-170 (共有、変えない), cc/cicada/ycsb_cicada.cc:1-55, common/runner.hh |
| build 定義 | cc/cicada/CMakeLists.txt, cmake/Options.cmake |
| ledger 契約 | orchestrator/campaign/silo_ladder_rung1_contract.py:495-540, orchestrator/tests/test_silo_ladder_rung1.py:48-56 |
| B-3 | orchestrator/tests/test_p3_s4_loop.py:8547-8640 |
| build 経路の先例 | orchestrator/campaign/patchharness.py:247,346、silo_ladder_rung1.py:2106,4044、silo_policy_coverage.py:363,556,751 |
| 単独性 | orchestrator/calibrator/runner.py:382-403 |
| gate 登録 | orchestrator/campaign/condition_meaning_gate.py:65-80 (DefineSpec), :80-344 (_DEFINE_SPECS), :395-540 (CONDITIONAL_BRANCH_WITNESSES 等), :1111-1144 (make_define_request) |
| gate の pin | orchestrator/tests/test_condition_meaning_gate.py:3470-3560, :3753-3760 |
| patch define inventory | orchestrator/tests/test_ccbench_spawn_sites.py:659-760 (_patch_added_define_interfaces), :2917-2938 |
| 起動一覧 | orchestrator/tests/test_ccbench_spawn_sites.py:36-110 |
| gate 呼出しの先例 | orchestrator/campaign/silo_policy_coverage.py:305-362 |
| 登録の先例 commit | 3867e6ec5 (condition_meaning_gate.py, test_ccbench_spawn_sites.py, test_condition_meaning_gate.py, test_p3_s4_loop.py ほか) |
