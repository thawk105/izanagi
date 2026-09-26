# 段 4 裁定 — [T-2847] 残り (4) si v2 + V28・V29・V36 (2026-09-26 19:5x JST)

入力: brief.md、liveness.md、codex/s2-plan.md、codex/s3-consult-a.md、codex/s3-consult-b.md、codex/parent-position-s3.md。裁定 inbox は wave 開始後に第 36 回 (commit 14ea1fc49、18:52) があり、T-2847 を止める項は無い (D297 の header 受理の設計審査は共有 header を変えない本 wave に掛からない)。local main は 265cce13c まで進んだ (台帳 fragment の fold だけ)、受入の post-claim merge で取り込む。

## 所見の裁定

| ID | 裁定 | 採否 | 反映 |
|---|---|---|---|
| plan §2「V28 は作れない、投入しない」 | refuted | 不採用 | A-01・B-01 のとおり依頼の縮小。YCSB は insert / delete を生成せず (`include/ycsb.hh:117-147`)、版は free でなく pool 再利用 (`cc/si/garbage_collection.cc:82-99`)。V28 は build・実走し、異常終了・停止も結果として分類する (V07 の先例) |
| A-01 / B-01 | real | 採用 | R1 |
| A-02 / B-02 | real | 採用 | R4 の「別の層 (process 異常終了)」、原因は実測なしに特定しない |
| A-03 | real | 採用 | R4: V28 の orphan 0 を不発と判定しない、発火診断と別記 |
| A-04 | real | 採用 | K 条件を変異に使わない (R3) |
| A-05 | real | 採用 | R2 の診断定義 |
| A-06 | real (nit) | 採用 | insight の限界に書く |
| A「推奨 cell」V28 = `max_ope=1, rratio=100, rmw=false` | refuted | 修正採用 | rratio=100 は全取引が読みだけで書き手がいない (inflight 版が生じず発火しえない)。V28 の主 cell は rratio=50 (R3 の S2) |
| B-03 | real | 採用 | 先例どおり条件 gate 経路で build し、2 macro を登録 (R5) |
| B-04 | real | 採用 | W の命題は条件付きで書く。V29 の盲点判定の条件は R4 |
| B-05 | real | 採用 | cell を主 cell と対照に絞る (R3) |
| B-06 | real | 採用 | 本裁定が事前登録。V36 は本走で取り直す |
| B-07 | real (nit) | 採用 | 見積り R7 |

## R1 scope

- v2 patch (`patches/instr-si-trace-v2.patch`、commit a68c312ef + 0db1ae583) は完成。変更しない。
- V29 = `patches/broken-si-first-updater-wins.patch`、裸マクロ `IZANAGI_BREAK_SI_FIRST_UPDATER_WINS`。`install_version()` の committed 後の first-updater-wins の abort (SI:198-206) だけを外す。inflight の分岐 (SI:176-187) と CAS 再試行は残す。
- V28 = `patches/broken-si-read-uncommitted-version.patch`、裸マクロ `IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION`。`read_internal()` の版選択ループ (SI:153-158) の status による除外 (committed / deleted 以外を飛ばす) だけを外し、snapshot 条件 `txid_ < ver->cstamp_` は残す。
- 両 patch は v2 patch の上に重ねて当たる形 (pin C → v2 → 壊し patch の順に厳密適用)。touch set = `cc/si/transaction.cc` だけ。裸マクロ 1 個の `#if` 枝に閉じ、macro 未定義なら v2 適用後の file と、`#if <macro>` … `#endif` の枝を除いてバイト一致 (mocc 壊し patch と同じ隔離規約)。`include/trace.hh`・`tpcc.hh` は変えない。
- 変異 cell の分類に K 条件を使わない (無改変 si が write skew で N を出すため帰属できない)。

## R2 発火診断 (壊し macro の有効枝の内側だけ)

process 終了時に stderr へ 1 行、mocc 壊し patch と同じ出し方 (relaxed atomic の加算、終了時の出力):
- V29: `T2847_FIRED slug=si-first-updater-wins reached=<n> changed=<n> committed=<n>`。reached = 元コードなら abort した条件 (`txid_ < vertmp->cstamp_`) が真になった回数。changed = その条件を越えて CAS に成功し版を公開した回数。committed = changed を 1 回以上経験した取引が commit に成功した件数 (取引ごとに 1 回、取引開始で印を戻す)。
- V28: `T2847_FIRED slug=si-read-uncommitted-version reached=<n> changed=<n> committed=<n>`。reached = ループが status が committed / deleted でない版で、snapshot 条件を満たすもの (元コードなら飛ばした版) に出会った回数。changed = その版を選んで返した回数 (元コードなら別の版か not found)。committed = changed を 1 回以上含む取引が commit に成功した件数。
- 診断は verifier の判定に使わない。timeout・異常終了の process では出ないことがある。

## R3 cell と job (事前登録)

共通: `ycsb_tuple_num=200 ycsb_zipf_skew=0.9 extime=1 -clocks_per_us=2100`、run timeout 120 s、verifier `--protocol si` 証人なし。

| cell | flags (共通に加えて) | 使う行 |
|---|---|---|
| K | `ycsb_rratio=50 ycsb_rmw=false ycsb_max_ope=10` | V36 (write skew) |
| S1 | `ycsb_rratio=0 ycsb_rmw=true ycsb_max_ope=1` | V29 (1 取引 1 key の RMW、別 key の write skew は起きない) |
| S2 | `ycsb_rratio=50 ycsb_rmw=false ycsb_max_ope=1` | V28 (読み専用取引と blind write 取引の混在、R が残る、write skew は 2 操作が要るので起きない) |

| job | build と cell |
|---|---|
| J1 | V2: K t1・K t4・S1 t4 / V29: S1 t4 |
| J2 | V2: S2 t4 / V28: S2 t4 |

V2 = 無改変 si + v2 patch (= V36 の build)。V2 の S1 t4・S2 t4 は同 job の対照。

## R4 期待と分類 (事前登録)

si は証拠面が無いので S は出ない。どの行も certified と呼ばない。1 cell の記録 = process 状態 (完走 / 異常終了 rc・signal / timeout)、verdict、巡回数、integrity の各 counter、trace 行数、発火診断。優先順: timeout → 「停止」(verdict なし)、rc≠0 → 「別の層 (process 異常終了)」(verify しない、原因は特定しない)、完走なら以下。

- **V36 (V2、K t4):** 期待 = N (巡回 > 0)。巡回 > 0 → 「無改変 si の巡回検出」。巡回 0 → 「巡回未観測」(schedule 依存)。K t1 の期待 = I・巡回 0 (1 thread は巡回しえない、対照)。
- **V29 (S1 t4):** 期待 = I・巡回 0・integrity 0 (同じ key の R が update で消え、lost update は ww 辺だけが残る)。changed > 0 かつ committed > 0 かつ巡回 0 かつ integrity 0 → 「盲点 (発火し commit したが trace に現れない)」。巡回 > 0 または integrity のどれかが正 → 「別の層で検出」(層を書く)。changed = 0 → 「未発生」。
- **V28 (S2 t4):** 期待する層 = orphan (I)。orphan > 0 → 「期待した層で検出」(併発した層は別欄)。orphan 0 で巡回か他の integrity が正 → 「別の層で検出」。orphan 0・巡回 0・integrity 0 で changed > 0 かつ committed > 0 → 「盲点」(R の版番号は trace 出力時の再読なので dirty read が正常な番号に置き換わりうる、設計書 §4.5)。changed = 0 → 「未発生」。
- **対照 (V2 の S1 t4・S2 t4):** 期待 = I・巡回 0・integrity 0 → 「対照正常」。対照が巡回 > 0・integrity 正・異常終了・停止なら、同 job の変異 cell は「帰属不能」。
- 期待と違う結果が出ても patch・workload・規則を事後に変えない (D2239 項 4)。直すのは patch が意図した機構以外を変えていることを source で示せる実装の誤りだけで、初回の結果も記録する。

## R5 条件 gate 登録 (先例 267b8992f と同形)

`orchestrator/campaign/condition_meaning_gate.py` に `_SI_OWNER = ("cc/si/transaction.cc",)` と 2 macro の `DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _SI_OWNER, "ycsb_si.exe", "patches/<name>.patch")`、witness、site 数 (patch の実 `#if <macro>` 行数)。表を固定する test (`test_condition_meaning_gate.py`・`test_p3_s4_loop.py` の裸マクロ allowlist・`test_ccbench_spawn_sites.py`・`test_screening_driver.py`) と `screening_driver.py` の既定値 0 を追随。判定基準・受理述語・供給経路は変えない。追加の検査 (仮想リスク向け) は足さない。

## R6 起動器の拡張 (repo 外、Codex)

`launch_si_run.py` に: BUILDS V29 = [v2, V29 patch] + macro、V28 = [v2, V28 patch] + macro。macro 付き build は、mocc の `_require_condition_gate` と同じ手順 (capture → request → 供給と意味 → admission) を si 用の局所関数で行い、成功記録を結果へ保存し、`-DCMAKE_CXX_FLAGS=-D<macro>=1` を足す。cell S1・S2、JOBS J1・J2 (R3)。完走 run の stderr から `T2847_FIRED` 行を抽出して結果へ。rc≠0 の signal 番号を記録。dry-run は checkout へ順に当てる照合に直す。判定を再実装しない。

## R7 計算の見積り (D2212 項 4、job Elapse の実測単価)

済: 生死確認 2 job 100 s。予定: 計測 2 job (L0 は 1 build + 4 run で 36〜64 s、J1 は 2 build + 4 run、J2 は 2 build + 2 run、1 job ≤ 200 s、V28 の停止があれば +120 s) ≈ 400〜500 s、焦点走 2 回 ≈ 400 s、変異 matrix (probe + final) ≈ 1,400 s、受入 2 回 ≈ 1,800 s。合計 ≈ 4,200 s ≈ 1.2 node 時間 < 2。ユーザー確認は不要。超えそうなら投入前に確認する。

## R8 所有と分割

- U-A (Codex author): `patches/broken-si-first-updater-wins.patch`・`patches/broken-si-read-uncommitted-version.patch`。
- U-C (Codex author、U-A の macro・site 数の確定後): `orchestrator/campaign/condition_meaning_gate.py`・`orchestrator/campaign/screening_driver.py`・`orchestrator/tests/test_condition_meaning_gate.py`・`orchestrator/tests/test_p3_s4_loop.py`・`orchestrator/tests/test_ccbench_spawn_sites.py`・`orchestrator/tests/test_screening_driver.py`。
- U-D (Codex author、U-A と並列): `.t2847-launcher/launch_si_run.py` (untracked、親が job dir へ退避)。
- 親: `patches/README.md` の節、insight、fragment。

## R9 変異 matrix (事前登録、実装面 = 条件 gate の登録)

runner = `tools/run_tests.py --force-dispatch` で `test_condition_meaning_gate.py`・`test_ccbench_spawn_sites.py`・`test_screening_driver.py`・`test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`、`tools/mutation_worktree.py` を独立 clone に当てる (先例 mocc-run §7)。

| 変異 | 誤り | 期待 |
|---|---|---|
| M0 (正例) | `condition_meaning_gate.py` の comment 1 語の変更 | SURVIVED |
| M1 | `_DEFINE_SPECS` から V29 の macro を削る | KILLED |
| M2 | `_CONDITIONAL_BRANCH_WITNESSES` から V28 を削る | KILLED |
| M3 | `_DEFINE_SPECS` の V28 の key を 1 字違える | KILLED |
| M4 | V29 の site 数を 1 増やす | KILLED |

probe (全件 SURVIVED 期待の観測走) で赤 node を観測し、final で期待 node に固定する。各変異が単一の誤り (登録の 1 件の欠落・名前違い・件数違い) から生じることを置換の一意性で確かめる。patch の中身 (未定義側の一致・1 patch 1 機構) は test では殺せないので、実装子と親の source 照合と段 6 レビュー、実走で確かめる。

## gate の禁止と正例

- 禁止: 登録で既存の受理述語・供給経路・判定基準を変えること。正例: 2 macro の DefineSpec・witness・site 数の追加だけで、既存 macro の件数照合 test が新しい総数で緑。
- 禁止: 壊し patch を V2 (対照) build に当てること。正例: J1 の V2 build の patch 列が [v2 patch] だけ。
