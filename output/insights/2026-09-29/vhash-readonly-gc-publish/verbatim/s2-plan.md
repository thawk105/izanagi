## 1. P1 の検証結果

**P1 は、`group_commit=0` の YCSB point workload について条件付きで支持する。** ro commit の末尾で `mainte()` を呼んでも、ro の `rts_` と `ThreadRtsArray` を変えない限り、flag の追加だけで必要な版を回収する経路は見つからなかった。ただし「flag は安全に効かない」という無条件の表現は強すぎる。flag は leader に境界を**公開させ**、`GCExecuteFlag` を立てて実際の回収を**起動する**。安全性は、公開値の根拠となる slot と回収条件に依存する。根拠: `external/ccbench/cc/cicada/util.cc:281-323`、`external/ccbench/cc/cicada/transaction.cc:806-888`。

- `begin()` はまず新しい `ThreadWtsArray` を store し、次に `MinWts` を load して `rts_ = MinWts−1` を `ThreadRtsArray` へ store する。この間に leader が割り込んでも、旧 slot は新 slot 以下であり、先に読んだ旧 slot は保守的な境界を作る。新 slot を読んだ場合は、その値が当該 ro の snapshot そのものになる。`MinWts` と各 slot の単調性には、`TimeStamp::generateTimeStamp()` の clock 更新と、leader が各 slot の min を公開する構造が必要である。`ThreadRtsArray` は commit では消されず、次の `begin()` で単調に更新される。根拠: `transaction.cc:34-43,934-937`、`include/time_stamp.hh:24-40`、`util.cc:290-316`。**全 CPU メモリ順序を含む形式証明は未確認**。
- ro の読みは固定 `rts_` で版を選び、読んだ版への pointer は `read_set_` と返された body に残る。`gc_versions()` は `gcq` の wts が `MinRts` 未満のときだけ、当該版より古い鎖を切る。したがって ro 中に slot を上げないことが、将来読む版と保持中の pointer の保護条件になる。`REUSE_VERSION=1` では切った版を再利用するため、誤回収は実際の pointer 破壊に至りうる。根拠: `transaction.cc:93-126,181-184,806-842`、`include/transaction.hh:173-196,229-237`、md_14 `vhash-gc-connection-prototype/README.md:60-63`。
- `INLINE_VERSION_OPT` の inline 版も同じ切断境界に従い、回収時に inline 使用権を返す。`INLINE_VERSION_PROMOTION` は読みの途中で write を作り、ro を update に切り替えるので、その tx は既存の update commit 経路を通す。今回の ro 分岐に入るのは切替後の tx ではない。ただし trace 側は OPT と PROMOTION の同時有効を未対応として止めており、判定器で検証する構成から外す。根拠: `transaction.cc:128-135,934-955`、`include/transaction.hh:173-212,217-244`、md_3 `vhash-cicada-verifier/README.md:51-54`。
- `gc_records()` は delete 済み record の最新 wts と `MinRts` で record 全体を削除する。YCSB の今回の生成手続きは READ/WRITE/RMW で delete を作らないが、一般の Cicada まで安全を拡張しない。`group_commit` は既定 0 で、1 なら leader が別の `ThreadRtsArrayForGroup` を読むため、今回のモデルと実測から除外する。根拠: `transaction.cc:348-407,845-856`、`include/ycsb.hh:55-84`、`include/common.hh:43`、`util.cc:294-311`。
- leader は worker 0 の手続きループ先頭で動く。全 flag が揃っても直ちに公開するとは限らない。ro commit で flag を立てる変更は**公開可能性**を増やすが、leader のスケジュールについて無条件の前進保証はない。根拠: `include/ycsb.hh:98-113`、`util.cc:281-323`。

安全版の条件は、ro が読み終えて `read_set_` と `node_map_` を消した**後**に、既存 `mainte()` の timer・flag 条件で自 thread の flag を立てること、`rts_`・両 slot・版の rts・leader の min 計算を変更しないこと、`SINGLE_EXEC=0`・`group_commit=0` に固定すること。`mainte()` 全体を呼ぶ場合、その冒頭の GC 実行も ro の参照を消した後になる。根拠: `transaction.cc:859-893,919-958`。

## 2. 単位 A (小モデル) のプラン

`tools/vhash_forwarding_model/ro_gc_publish.py` を**別 module**として追加し、既存 `model.py`・`judge.py`・`scenarios.py`・`cli.py` の結果を変えない。既存モデルの J1 は commit 履歴の `ww/wr/rw` 閉路判定として流用できるが、Cicada の ro snapshot と slot を既存 `gc_floor` に同一視してはいけない。新 module 内の履歴を J1 入力形へ写す adapter を設け、GC 安全は別判定にする。根拠: `tools/vhash_forwarding_model/judge.py:30-69,84-119`、`gc_connection.py:11-20`、md_10 `vhash-gc-connection-model/README.md:47-56`。

| 状態・step | 設計 |
|---|---|
| 状態 | 2〜3 worker の `local_wts`、`rts`、`ThreadWtsArray`・`ThreadRtsArray`、各 flag と execute flag、`MinWts`・`MinRts`、leader の走査 index と読取済み min、ro の phase・保持 pointer・読取履歴、2 key の版鎖、GC queue・切断済み版 |
| 原子性 | 共有変数の load/store/CAS **1 回を 1 step**。`begin` の wts store、MinWts load、rts slot storeを分離。leader の flag 判定、各 slot load、MinWts/MinRts store、flag reset、execute flag storeを分離。GC の境界 load、鎖切断、再利用も分離 |
| 場面 | 長い ro 1 本＋更新、短い ro 多数＋更新、`begin` の MinWts load 前後への leader 割り込み、ro commit 後すぐ次の `begin`。固定の初期版・後続版を使い、全 interleaving を探索 |
| 判定 | 回収 step 直前に「active tx が後で選びうる版」「保持 pointer の版」を列挙し、切断・再利用・record 削除で消えたら違反。commit 時の J1 閉路、公開回数と長い ro 存在中の公開到達列を別記。公開できても `MinRts` が同値なら「境界前進」と数えない |

安全版は二形を探索する。(1) ro commit 後に timer 条件で flag だけ立てる。(2) 実コードどおり execute flag があれば GC を走らせてから flag を立てる。後者が patch の主対応物。比較用 stock は ro commit で何もしない。根拠: `transaction.cc:859-893,934-955`。

| md_22 の例示 | 危ない版と期待する検出 |
|---|---|
| 「flag を上げる前に reader の参照が残る」 | **flag だけを ro の途中で上げる**版 (P2 iii) は slot 不変なら GC 違反を期待しない。例示そのままを「必ず壊れる正例」にしない。別の正例として、参照中に slot を最新 `MinWts−1` へ上げる版 (i) を入れる。md_14 ではこの型で保持版の変化を実測した。 |
| 「境界を下げる」 | ro commit で slot を ∞ にし、次の `begin` の slot store 前に leader が公開する版 (ii)。後で低い `rts_` に戻って必要版を読むと GC 違反。公開値が下がった事象自体も数える。 |
| 追加 | ro commit の `read_set_` clear **前**に `mainte()` 全体を呼び、同 thread の GC が保持 pointer を切れるか探索する。ただし slot 不変なら不発の可能性が高く、正例と事前断定しない。 |

探索は key 2、worker 2〜3、各 key 初期版＋後続 1〜2、ro read 1〜2、各 worker の手続き 2 回まで。各場面で到達状態を canonicalize し上限 200 万状態を仮設定、上限に達したら「未完探索」と出す。状態数は**実走前の見積り**として場面あたり \(10^4\)〜\(10^6\)、全体 \(10^7\) 未満を目標にする。実測値ではない。既存 63 構成の行ごとの照合は親が実施する。根拠: md_10 `vhash-gc-connection-model/README.md:198-210,256-259`。

新テスト `orchestrator/tests/test_vhash_forwarding_model_rogc.py` の node は `test_safe_flag_only_and_full_mainte`、`test_begin_interleavings_preserve_floor`、`test_long_ro_can_publish_without_boundary_advance`、`test_bad_raise_slot_reclaims_held_version`、`test_bad_clear_slot_reclaims_future_read`、`test_early_flag_alone_is_not_assumed_unsafe`、`test_j1_adapter_detects_cycle`、`test_existing_cli_rows_unchanged` とする。

## 3. 単位 B (patch・driver・登録簿) のプラン

### Patch

`IZANAGI_CICADA_RO_GCFLAG` を既定 0 とし、`cc/cicada/transaction.cc:936-937` の clear 後、return 前に `#if IZANAGI_CICADA_RO_GCFLAG`、`#if !SINGLE_EXEC`、`mainte();` を挿入する。`#else` 側にファイル名なしの `#line 937`、分岐終了後に元の `return true` の行へ `#line` を置き、macro 0 の前処理後 token と行番号を stock に合わせる。`mainte()` 自体は編集しない。根拠: `transaction.cc:859-893,934-955`、既存の inert `#line` 方式 `patches/instr-cicada-trace.patch:119-130`、`patches/instr-cicada-version-lifetime.patch:844-880`。

**P4 の「1 file で三形に適用」は静的には難しい。** trace は ro 分岐の `if` 直後、vlife は clear 直前へ大きな hunk を加える。同じ ro 末尾への patch hunk は文脈が変わる。`cicada-ro-gcflag-variant.patch`（pin と pin+trace）と `cicada-ro-gcflag-vlife.patch`（pin+vlife）を分ける。後者は vlife が追加した `#line 935` の後ろへ挿入する。親の `probe-stack.sh` は trace と vlife の相互適用だけを測っており、**新 patch の三形への厳密適用は未確認**。author は使い捨て checkout で各順序の `git apply --check` → `git apply` を行い、両 patch 適用後の macro=1 の ro commit 分岐を前処理 token として照合する。`--3way`・fuzz は使わない。根拠: `patches/instr-cicada-trace.patch:119-130`、`patches/instr-cicada-version-lifetime.patch:844-880`、`probe-stack.sh:1-17`。

condition gate は `condition_meaning_gate.py` の `_DEFINE_SPECS` に owner `cc/cicada/transaction.cc`、target `ycsb_cicada.exe`、route `CMAKE_CXX_FLAGS`、inert `0`、patch は通常版を登録し、branch witness に同 owner の `#if IZANAGI_CICADA_RO_GCFLAG`、site count **1**、companion **0**を登録する。meaning は owner TU の前処理を見るため、分岐を別 TU のみに置かない。実際の count は patch 作成後に gate の列挙値と照合する。根拠: `orchestrator/campaign/condition_meaning_gate.py:65-89,393-400,550-589`。

登録簿の閉包は次のとおり。`condition_meaning_gate.py` と同 test、`screening_driver.py:_CONDITION_DEFAULTS`、`test_p3_s4_loop.py:allowed_non_variant_tokens`、`patches/README.md`、`orchestrator/tests/README.md`。新 driver に字面の `"--build"` を持つ関数を作るなら `materializer_admission.py`、`test_p3_build_authority_cli.py` の `MANUAL_BUILD_FILES`・`EXPECTED_NON_ADMISSIBLE` を加える。新たな `subprocess.run` site は `test_ccbench_spawn_sites.py` で CCBench 診断実行、build subprocess、非 CCBench のどれかへ分類する。先例の変更集合は `git show --stat 7a4f9a592` と `a3bc64e3b` で確認済み。`patches/ledger.json` は entry 数 1 の契約と衝突するため編集しない。根拠: `screening_driver.py:51-75`、`test_p3_s4_loop.py:8547-8557`、`test_p3_build_authority_cli.py:159-185`、`test_ccbench_spawn_sites.py:47-98`、`patches/README.md:874-879,913-928`。

C++ の壊し正例は、今回の本筋に対して費用が大きい。追加するなら **slot を ro 中に最新 `MinWts−1` へ上げる**壊し patch を trace または保持 pointer 計器だけで走らせ、`READ_WTS_MISMATCH`、異常終了、保持版の変化を検出する。判定器の巡回だけでは GC の use after free を十分検出しない。md_14 が同型の不具合を実測済みなので、まず小モデル正例と既存実証を根拠にし、新 C++ 正例は予算が残った場合の焦点走に限る。根拠: md_14 `vhash-gc-connection-prototype/README.md:60-63,121-131`、md_3 `vhash-cicada-verifier/README.md:46-49`。

### Driver と作図

新 `orchestrator/campaign/vhash_ro_gc_publish.py` は vlife を**import**し、`PIN`、`TUNED_GENOME`、`genome_args()`、`verify_genome_commands()`、`parse_vlife_line()`、`summarize()`、site/toolchain/dependency helper を再利用する。vlife の `_build_variant()` は固定 `MACROS`・patch 適用の都合でそのまま主 build へ流用しにくいので、新 driver 側に自分の materializer を置く。vlife file は編集しない。`smoke`（三重適用・inert・短走）、`verify`（trace build と判定器）、`measure`（計器 build の GC 指標）、`throughput`（計器・trace なし）を分け、全出力に patch SHA、pin、genome、flags、arm、反復、build macro、計器有無を保存する。根拠: `vhash_cicada_vlife.py:31-64,388-439,801-875`、`vhash_forwarding_prototype.py:37-65`。

vlife の schema 2 から取れる量は、公開回数 `summary.gc_publications`、境界年齢の平均 `gc_boundary_mean_us`、p50 bucket 上界 `gc_boundary_p50_bucket_us`、観測走 D-C の `dc_ro_gap_sum_us` と `dc_interval_sum_us`、終了時の論理生存版数 `tuple_num + Σ(install−detach)`。**時間平均の生存版数は vlife にない**。必要なら md_14 の等間隔 `uniform.live_sum/count` 型の最小追加計器を新 patch に設けるか、「終了時の論理生存版数」と明記して比較する。D-C の `Δ_ro` は variant の因果効果ではなく、各 arm の観測走をそれぞれ分割した量として扱う。根拠: `vhash_cicada_vlife.py:190-211,301-363,477-480`、md_14 `vhash-gc-connection-prototype/README.md:55-65`、md_15 `vhash-readonly-share/README.md:86-93`。

**throughput の workload は P5 のままでは成立しない。** `izanagi_ronly_pct` は `IZANAGI_CICADA_VLIFE` 内でのみ手続きを書き換える。`IZANAGI_CICADA_LONGTX` は待機を作るが、長い worker を ro に固定する `izanagi_long_kind` の反映も VLIFE 内にある。計器なし build で `ycsb_rratio=50/95` とするだけでは「ro tx 50/95%」にならない（10 操作すべて read の確率に依存する）。B に**計器から独立した小さな workload patch/macro**を加え、手続き生成時に指定確率で全 op を READ、非 ro では少なくとも 1 write、worker 1 は長い ro に固定する。vlife の計器版と同一手続き分布・retry 不変を test と実現 ro 率で照合する。新 macro の owner・companion・登録簿も上記閉包へ加える。これは P5 の必須修正である。根拠: `include/ycsb.hh:55-84`、`patches/instr-cicada-version-lifetime.patch:195-216,346-390,831-839`。

`verify` は pin+trace+variant の build で `--protocol cicada` を使い、default genome と調整済み genome、ro を含む point read/update workload を走らせる。長い ro の trace は workload patch の独立 knob で作る。trace の ro hook は clear 前に R を保存し、commit 件数一致・integrity 数値項目・巡回・`READ_WTS_MISMATCH` を確認する。巡回が出れば失格、出なくても判定上限は indeterminate。OPT=1/PROMOTION=0 の調整済み genome は md_11 の観測最良であり、md_20 の正しさ結果が未着なら未確認と記す。根拠: md_3 `vhash-cicada-verifier/README.md:15-19,38-54,70-84`、md_11 `vhash-cicada-baseline-tuning/README.md:114-139`。

作図は新生成器を `tools/plotting/plot_vhash_ro_gc_publish.py` または一次資料内 `make_figures.py` に置き、raw JSON から再計算する。図は公開回数・境界年齢・終了時生存版・計器なし throughput を別 panel にし、反復点と 95% CI、条件、入力 SHA、PNG/PDF/provenance を揃える。全格子相当の fixture と実データ実走で layout を確認する。根拠: `tools/plotting/FIGURE_CONVENTIONS.md:23-37,65-83,85-129`。

## 4. テスト計画

単位 A の新 node は §2 の 8 件。既存 `test_vhash_forwarding_model.py`、`test_vhash_forwarding_model_gc.py`、`test_vhash_forwarding_model_helper.py` を焦点走に含め、旧 63 構成の CLI 出力を行単位で比較する。根拠: md_10 `vhash-gc-connection-model/README.md:256-259`、`orchestrator/tests/test_vhash_forwarding_model_gc.py`。

単位 B の新 `orchestrator/tests/test_vhash_ro_gc_publish.py` は `test_patch_three_strict_preimages`、`test_split_patches_same_enabled_branch`、`test_default_preprocess_matches_stock`、`test_macro_gate_owner_and_counts`、`test_condition_grid_and_pair_order`、`test_vlife_metric_mapping_and_zero_publication`、`test_throughput_rejects_instrumented_build`、`test_workload_realized_kind_contract`、`test_verify_rejects_cycle_and_accepts_indeterminate_label`、`test_raw_figure_inputs_and_provenance` を設ける。既存波及は `test_condition_meaning_gate.py`、`test_vhash_cicada_vlife.py`、`test_p3_s4_loop.py`、`test_p3_build_authority_cli.py`、`test_ccbench_spawn_sites.py`。焦点走はこれらと新 A/B test file、必要なら `test_vhash_forwarding_prototype.py`。テストと build の実測は親が `tools/run_tests.py` 経由で行う。本段では未実行。根拠: `AGENTS.md` の実行規律、`orchestrator/tests/README.md:188`、先例 commit `7a4f9a592`・`a3bc64e3b` の変更 file 一覧。

## 5. 計測の条件表と所要見積り

| 軸 | 主格子 |
|---|---|
| genome | md_11 の B0 O1 P0 R1 W0。default は `verify` の対照 |
| ro 指定率 | 0、50、95%。計器なし build でも同じ**手続き単位**の確率 |
| 長い tx | none、worker 1 の wait10msR |
| skew | 0.9、0 |
| GC 間隔 | 10 µs、1000 µs |
| arm・反復 | stock、ro GC flag。3 反復、同一 job 内で rep ごとに順序を交替 |
| run | 48 worker、1M 件、3 秒、`group_commit=0`、`SINGLE_EXEC=0` |

1 build 種あたり \(3×2×2×2×2×3=144\) run、3 秒の実行本体は 432 秒。計器版と throughput 版で 864 秒。md_15 の本計測 job は 288・285・287・377 秒（合計 1,237 秒）であり、build・依存準備・verify・smoke の余裕を加えても**1 node 時間前後、2 node 時間未満を狙える見積り**である。ただし workload patch の build 数と trace 量は未実測なので、投入前に実際の job 分割と \(Σ(\text{条件数}×\text{走行秒})+\text{build見積り}\) を再計算し、2 node 時間以上なら止める。診断と性能を別 job にし、各 job 内の stock/variant を交互に走らせる。他 wave と同じノードでは計測しない。根拠: md_15 `vhash-readonly-share/README.md:250,268-269`、`inputs/common.txt:27-40`、`docs/pegasus-runbook.md:744-769`。

一次資料では **(a)** を「同じ固定 snapshot 規則のまま ro commit に flag を加えたときの、公開回数・公開間隔・境界年齢・終了時生存版・throughput の stock との差」として実測する。併せて md_15 の D-C は介入前の局所的機会量 \(\sum Δ_{\rm ro}/\sum\text{公開間隔}\) と明記する。**(b)** は長い ro の slot が `MinRts` の min になる時間・同値再公開の割合・境界保持 tx の内訳を測り、固定 snapshot では越えられない遅れとして記す。ro snapshot の変更や forwarding の効果量はこの wave の実測値として推定しない。公開 0 回の走では公開時の境界年齢は未定義とし、終了時の未公開時間を別記する。根拠: md_15 `vhash-readonly-share/README.md:72-108,204-212,241-250`、`vhash_cicada_vlife.py:346-361`。

## 6. brief への修正提案 (P1〜P5 ごとに 同意 / 修正 / 反対)

| 仮裁定 | 判断 | 修正 |
|---|---|---|
| P1 | **修正** | `group_commit=0`・YCSB delete なし・slot 不変・ro の参照 clear 後という条件を明示する。flag は公開と GC 実行を起動するので「版安全に効かない」と一般化しない。根拠: `transaction.cc:806-888,934-955`、`util.cc:281-323`。 |
| P2 | **修正** | (i)(ii) を GC 違反の正例候補とし、(iii) は flag 単独なら不発を予想する陰性対照とする。「参照が残る」は flag 単独では不十分で、slot の誤変更または GC 実行時の保護破綻を伴わせる。根拠: md_14 `vhash-gc-connection-prototype/README.md:60-63`。 |
| P3 | **同意** | `mainte()` 全体を ro の clear 後に呼ぶ。flag だけの形は小モデルの比較腕に残す。根拠: `transaction.cc:859-893,934-955`。 |
| P4 | **修正** | trace と vlife の ro 末尾 hunk は異なる。二 patch に分けて厳密適用を author/親が実測し、macro=1 の同一変更を前処理で照合する。現時点で三形の適用は**未確認**。根拠: 両計器 patch の ro hunk、`probe-stack.sh:1-17`。 |
| P5 | **反対** | 計器なし build の `izanagi_ronly_pct` と長い ro 固定は VLIFE 内なので、提案のままでは同じ workload を作れない。独立 workload knob を B に追加し、条件数・build 数・予算を再計算する。根拠: `patches/instr-cicada-version-lifetime.patch:195-216,346-390`。 |

## 総括

実装の芯は、ro commit の参照解放後に既存 `mainte()` を呼び、**slot と snapshot を触らない**ことにある。最大の計画上の修正は throughput 用の独立した ro workload 生成である。これを入れなければ計器付き診断と計器なし性能の同条件比較が成立しない。新 patch の厳密適用、モデルの状態数、実行時間、判定器結果は本段では未確認であり、親の実測ゲートに残す。