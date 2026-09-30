# 段 6 fix1 裁定 — md_22 [T-2911] (2026-09-29 23:5x JST)

入力: 統合 commit 2a48fa7a4、レビュー A (`codex/stage6a/out.md`、NO-GO)、レビュー B (`codex/stage6b/out.md`、NO-GO)、焦点走 1 (focus-1、結果は下の「焦点走」節)。
先例の確認: md_3 (`output/insights/2026-09-29/vhash-cicada-verifier/README.md` §1 の 5・表 76-82 行) と md_14 (同 `vhash-gc-connection-prototype/README.md` 表 127-130 行) で、Cicada の trace は巡回 0・integrity clean でも判定器の上限が indeterminate (rc=3) だった (Cicada に証拠面が無い)。

## 所見の裁定
| 所見 | 判定 | 扱い |
|---|---|---|
| A1 探索範囲が 2 worker・1 key・ro read 1 | real (must-fix) | 下記 FA-1 |
| A2・B8 bad-raise-slot が stock から到達を示していない初期 prefix から始まる | real (must-fix) | FA-2 |
| A3 safe 腕で古い版の切断が一度も起きない (「違反 0」が空の主張) | real (must-fix、最重要) | FA-3 |
| A4・B2 J1 が固定履歴 | real | FA-4 (J1 の探索結果と adapter を削除し、直列化可能性の主張を外す) |
| A5 driver と作図器の raw schema 不一致 | real (must-fix) | FB-1 |
| A6 verify が rc=3 を accepted にする | 一部 real | rc=3 (巡回 0・integrity clean) を上限とする受理は先例どおりで正しい。ただし field 名 `accepted` が認証済みと読める。FB-2 |
| A7・B1 test が旧文言 `Fifty-one` を期待 | real (must-fix) | FB-3 |
| B3 陰性対照 neg-early-flag が「前進あり」 | refuted | 段 4 裁定 P2 の「発火」は GC 安全違反を指し、前進 (MinRts の値の変化) は対象外。flag を早く立てれば公開は起きうるが、slot が境界を押さえるので違反 0 は予想どおり。ただし test と JSON で「progress = 長い ro active 中の MinRts の値の変化 (公開回数ではない)」と明記する (FA-5) |
| B4 (b) の集計と stock 公開 0 の明示が図に無い | real (must-fix) | FB-4 |
| B5 smoke に時間見積りが無い | refuted (driver 側) | build の `elapsed_s` と run の `wall_s` は raw にあり、見積りは親が smoke raw から計算して一次資料と裁定に書く |
| B6 非同居の証拠 | 親の手番 | 投入前の qstat と他 wave の job の node・時刻を親が記録して照合する (driver は変えない) |
| B7 patch test が字面だけを見る | real (should-fix、限定) | 挙動の確認は smoke の計数行 (COUNT・workload) で行う。test は MB1 用に FB-5 だけ足す |
| B 削除表: `--records`・`--extime` | 不採用 | smoke と verify の規模指定は内部で持つが、measure の短縮実行に使えるので残す (作図器が本計測以外を拒否するのは正しい) |
| B 削除表: throughput の二重検査 | 不採用 | 事前 (build 前) と記録時の 2 層は目的が違う (build を始めない、記録を取り違えない) |
| B 変異予測: MB5 は test が `P.ORDER` を期待値に使うので生存しうる | real | FB-6 |

## fix の内容
### 単位 A (fix 子 A、所有: `tools/vhash_forwarding_model/ro_gc_publish.py`、`orchestrator/tests/test_vhash_forwarding_model_rogc.py`)
- **FA-1 範囲:** 少なくとも (1) 2 worker (worker 0 = update と leader を兼ねる、worker 1 = ro を 2 手続き続ける) × key 1〜2 × ro read 1〜2、(2) 3 worker (worker 0 = update と leader、worker 1 = ro、worker 2 = update または ro) を探索する。状態上限を超える構成は「未完探索」として結果に出し、test は完了した構成だけで結論を固定する。探索した構成・状態数・完了の有無を JSON と test で固定する。
- **FA-2 共通初期状態:** 全腕を同じ初期状態 (`State()` 相当) から始める。bad-raise-slot は「ro が読んで版を保持している間に slot を最新 MinWts−1 へ上げる」を、stock と同じ遷移で到達した状態から起こす。最短 witness は共通初期状態からの step 列として取り直す。bad-clear-slot は「safe 腕に slot の ∞ 化を足した正例」と明記する。
- **FA-3 安全腕で切断を起こす:** update 側が同じ key に 3 版以上を作り、ro が手続きを終えて次の手続きで slot を上げた後に、適法な鎖切断が起きる状態列を含める。各腕の JSON に境界 load 数・切断数・切断なし数を出し、test で safe-flag・safe-mainte の切断数 > 0 を要求する。stock は ro worker が flag を立てないので公開・切断が起きない (0) ことも固定する。GC 安全 oracle は回収側の境界計算から独立のまま。
- **FA-4 J1 の削除:** 探索中の J1 呼び出し・固定履歴・adapter とその test を削除する。JSON に `serializability: not modeled (checked by the trace verifier on the C++ build)` を出す。
- **FA-5 用語:** `progress` を「長い ro が active の間に MinRts の値が変わる公開があったか」と docstring・JSON の説明欄に書く。neg-early-flag の test は違反 0 を固定し、progress は記録するだけにする。
- 規模上限: module 800 行、test 500 行。

### 単位 B (fix 子 B、所有は段 5 と同じ)
- **FB-1:** driver の raw と作図器の schema を一致させる。正規の measure / throughput raw の形 (driver の `_record` の出力) の fixture を作図器に通す結合 test を足す。
- **FB-2:** verify の record の field を `accepted` から意味どおりの名前 (例 `no_cycle_upper_bound_indeterminate`) に変え、`verdict_label` に判定器の rc=0 なら `certified`、rc=3 なら `no-cycle (upper bound indeterminate)` を入れる。受理条件 (rc∈{0,3}・巡回 0・integrity clean・mismatch 0・COUNT>0) は変えない。
- **FB-3:** `test_condition_meaning_gate.py` の旧文言の assert を現行の件数・文言へ直す (関数名も)。
- **FB-4:** 作図器 (または同じ生成器の数表出力) に (b) を足す: variant 腕の wait10msR と none の境界年齢差 (条件内平均と反復点)、公開時の保持者のうち ro の割合 (vlife の holder 集計)、stock の公開回数 0 を「公開 0 回」と明示 (境界年齢は未定義と表示)。
- **FB-5:** variant patch の追加行のうち `mainte();` が `#if IZANAGI_CICADA_RO_GCFLAG` の内側にあることを確かめる構造 test (MB1 用)。
- **FB-6:** 均衡順序の test は `P.ORDER` を期待値に使わず、事前固定の列 `(stock,variant),(variant,stock)×3` を test 側に literal で書く。

### 両単位共通
- **既存テストの期待値を変更しない** (FB-3 は本 wave が段 5 で足した件数更新の取り残しを直すもので、tracked だが本 wave の変更の一部)。反転・緩和・skip・削除を禁じる。赤なら実装側を直す。
- commit しない、docs を編集しない。

## 変異登録の erratum (DW-M01・M02、fix 前に確定)
- MA6 (J1 adapter の rw 辺削除): FA-4 で adapter を削除するため**登録から外す**。
- MA5 (参照解放前に GC 実行): 実装後に発火を確かめ、不発なら等価変異として記録して外す (段 4 のまま)。
- 追加 MA7: safe-mainte の切断を起こさなくする (update 側の 3 版目を作らない) → FA-3 の「切断数 > 0」test が殺すはず。
- 追加 MB9: 作図器の (b) 集計で variant と stock を取り違える → FB-4 の test が殺すはず。
- MB2・MB8 は字面の移動・削除だけを殺す (レビュー B 所見 7)。挙動は smoke の計数行で確認する旨を一次資料に書く。

## 焦点走
焦点走 1 (commit 2a48fa7a4、44 file、36371.nqsv、23:45〜23:50 JST): **10 failed, 5133 passed, 8 skipped** (rc=1)。log は job dir の `focus-1.log` (赤の本文は 100〜530 行)。赤はすべて単位 B の登録簿で、本 wave の変更に帰属する (FB-7 で直す):
1. `test_condition_meaning_gate.py::test_compile_time_branch_selection_accepts_each_registry_macro[IZANAGI_CICADA_ROGC_WORKLOAD]` (1590 行、`compile-...count-mismatch`)
2. 同 `::test_new_branch_selection_supply_meaning_and_admission[IZANAGI_CICADA_ROGC_WORKLOAD]` (1632 行)
3. 同 `::test_new_branch_green_schema_rejects_count_value_and_argv_mutations[IZANAGI_CICADA_ROGC_WORKLOAD]` (1784 行)
4. 同 `::test_module_claim_names_the_exact_69_define_supply_domain` (3864 行、旧文言 `Fifty-one`、FB-3)
5. 同 `::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` (1240 行、`CONDITIONAL_BRANCH_WITNESSES` の順序・集合が `_COMPILE_TIME_BRANCH_MACROS` と不一致)
6. 同 `::test_v1_domain_and_claim_boundaries_are_exact` (3741 行)
7. `test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member` (2954 行、新 macro 4 件 × `vhash_ro_gc_publish.py:_build_variant` が `reachable` のまま未分類)
8. 同 `::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` (3598 行)
9. 同 `::test_define_sink_cross_product_t2520_certify_entry_removal` (3620 行)
10. `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` (85 行、自走 harness を持つ `test_vhash_forwarding_model_rogc.py` を pytest 専用 allowlist に載せた)

- **FB-7:** 上の 10 件を実装側で直す。workload macro の分岐目印の件数 (owner TU `ycsb_cicada.cc` の前処理で見える宣言件数) を実 patch と一致させる、`_COMPILE_TIME_BRANCH_MACROS` と `CONDITIONAL_BRANCH_WITNESSES` の対応を既存の登録と同じ規則で揃える、spawn site の define 交差表に新 driver の build sink を既存の先例 (vlife・forwarding driver) と同じ分類で登録する、README の pytest 専用 allowlist から `test_vhash_forwarding_model_rogc.py` を外す (自走 harness 側を正とする)。既存の test の期待値 (先例 macro の件数・分類) は変えない。
