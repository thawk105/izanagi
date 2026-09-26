# mocc の既存壊し patch 4 本と新規 V25・V34 を pin C で実走し、検出期待表と突き合わせた ([T-2847] 残り (2) の mocc 部分、2026-09-26)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-t2847-mocc-run` (branch `worktree-dev-wave-t2847-mocc-run`)、起点 local main `42d148868` (開始 gate fresh rc 0、2026-09-26 13:5x JST)、CCBench submodule = pin C `68106660` (動かしていない)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/` (brief・Codex の prompt / 出力・起動器・計測の原本 JSON と stdout / stderr・変異 harness の記録)。
段 1〜6 の全文は `verbatim/` (依頼、段 1 brief、段 2 plan、段 3 相談 2 本、段 4 裁定、段 5 共通契約と author 3 本、段 6 review 2 本と裁定)。

期待の出所は `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` (以下「設計書」) の §4・§5.1。V 番号は設計書のもの。事前登録 (cell・期待・job 分割・分類の規則) は `verbatim/s4-ruling.md` の R3〜R5。手順の先例は `output/insights/2026-09-23/t2847-mutation-run/README.md` と D2239。

## 1. 依頼と結論

依頼 (ユーザー直接起動の `/dev-wave [T-2847]`、逐語は `verbatim/request.md`): 残り (2) のうち mocc の既存壊し patch 4 本 (V13〜V16) と新規 V25・V34 を、現 pin C の上で計算ノードで実走し、検出表を実測で埋める。

結論:

1. **pin C の上では、既存 4 本は計装 patch なしでそのまま当たる。** C は mocc の X/P 計装を含む commit なので、旧来の「e9e477ca + `instr-mocc-lock-coverage.patch` + 壊し patch」ではなく「C + 壊し patch」を build した (`git apply --check` は壊し 4 本 rc 0、計装 patch は rc 1)。既存 driver (`s3_mocc_mutation_proof.py`) は旧 pin と計装 patch を固定しているので `main()` は使わず、repo 外の起動器が driver の build・verify 関数を呼んだ (§2.2)。
2. **6 行 34 cell の内訳:** 期待した層で検出 20 (V13・V14・V15 の全 18 cell と V16 の hot 2 cell)、別の層で検出 0、盲点として certified 1 (V25 の hot 1 thread)、未発生 2 (V16 の cold 2 cell、source 上で機構に届かない)、発火未確認の S 2 (V16 の default 2 cell)、停止 3 (V25 の 4 thread 3 cell)、対照正常 6 (V34 の全 cell、誤検出 0)。同じ job の stock 対照 28 run はすべて certified (表は §3)。
3. **4 thread では、1 つの変更が複数の層を同時に発火させた。** V13 lockskip と V15 early-unlock の 4 thread は、期待した X に加えて巡回 (1,403〜3,570) と version dup が出て non-serializable だった。主分類は期待した層 (X) で、併発した層は別欄に書く (段 4 裁定 R4)。単一理由の検出は 1 thread の cell (X だけで indeterminate) が示す。
4. **V25 (逆順 lock の正準順への復元を飛ばす) は、4 thread の 3 cell すべてで 120 秒の run timeout で停止した。** 同じ job の stock の同じ cell は約 1 秒で完走した。停止には verdict を付けず、相互待ちか自己待ちかは確定していない (診断行も trace も得られない)。1 thread では復元の省略が 447,413 回起き、それを含む取引 177,188 件が commit した履歴が certified だった。これは「lock 順の違反を含む完走履歴を verifier は捕まえない」という観測で、deadlock の実証ではない (設計書 §4.3 の「X は要る lock が無いことを見る検査で、相互待ちは見ない」と合う)。
5. **V34 (温度述語 4 site の等価変形) は 6 cell すべてで certified、X/P と他の integrity は 0 だった。** ただし workload W (読み比率 0・rmw・max_ope 5) で評価されたのは 297 行と 460 行の 2 site だけで、567 行 (delete 経路) と 971 行 (read set の要素がある validation) は全 cell で 0 回だった。境界 (temp == threshold) の評価も hot の 2 site だけ。対照が示すのは評価された 2 site の等価性と verifier の正常判定までである (§3.3)。
6. 計算ノードの使用 (job Elapse): 計測 4 job 計 1,376 秒 (§2.3)、焦点走 144 秒 (§6)、変異 matrix 1,378 秒 (§7)、計 2,898 秒 ≈ 0.81 node 時間。受入全走は §8。

## 2. 何をどう走らせたか

### 2.1 patch

- 既存 4 本 (無変更): `patches/broken-mocc-lockskip-validation.patch` (V13、`IZANAGI_BREAK_MOCC_LOCK_COVERAGE`)、`broken-mocc-permutation-erase.patch` (V14、`IZANAGI_BREAK_MOCC_PERMUTATION`)、`broken-mocc-early-unlock.patch` (V15、`IZANAGI_BREAK_MOCC_EARLY_UNLOCK`)、`broken-mocc-hot-update-unlock.patch` (V16、`IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK`)。発火診断は持たない。
- 新規 2 本 (Codex author、`patches/README.md` の該当節): `broken-mocc-skip-canonical-restore.patch` (V25、site 5) と `control-mocc-negated-temperature-predicate.patch` (V34、site 9)。裸マクロ 1 個の `#if` 枝に閉じ、未定義の枝を除いた全文が pin C とバイト一致する (実装子が枝除去 script で確認)。条件 gate の許可ドメインへ 2 macro を登録した (既存の mocc 壊し patch と同形。判定基準は変えていない)。
- V25 の変更は、`lock()` の中で `vioctr > 0` のとき、upgrade でなく、対象 tuple が保持中の lock (CLL_) に無く、直後に正準順で再取得する key が保持中の suffix と重ならない場合に限って、逆順に取った lock の解放と CLL_ からの除去を飛ばす。段 2 plan が「単純に飛ばすと同じ lock の再取得と `unlockCLL()` の二重解放を招く」と指摘したので、この限定を入れた。段 6 レビュー A は gate が 4 条件を満たし、変更由来の二重取得・二重解放の経路は見つからないと判定した。
- 発火診断 (新規 2 本だけ、段 4 裁定 R2): V25 は reached (gate の評価で vioctr > 0)・changed (復元を実際に飛ばした)・committed (changed を含む取引の commit)・`skipped_locks`。V34 は site 別の評価回数と `temp == threshold` の評価回数 (changed は定義上 0)。relaxed atomic の加算だけで、process 終了時に stderr へ 1 行。timeout で止めた process では出ない。verifier の判定には使っていない。

### 2.2 起動器と経路

repo 外の起動器 `launch_mocc_run.py` (Codex author、job dir、sha256 `c65acb772a8f213a858bd89ce326725f091c498c7a2bc896ba233d6e481c1efa`):

- policy (`tools/pegasus/mocc_trace_v1_policy.json`) は driver の `_load_policy` のまま読む。policy の `mocc_trace.new_oid` は e9e477ca で driver の PIN と一致し、build だけ C を checkout する。これは既存の pin 候補経路 (`s3_mocc_lock_coverage._candidate_main`、C 上の先行 6 走を出した経路) と同じ扱いで、結果 JSON に policy の new_oid と build source の OID を両方記録した。
- build ごとに `checkout(C)`・`assert_pinned_clean`、壊し / 対照 patch は `_apply_owned_patch` (touch set = `cc/mocc/transaction.cc` の検査と厳密適用)、build は `_build_variant` (condition gate と `-D<macro>=1`)。計装 patch は当てない。
- run は driver の `_run_trace` と同じ argv・cwd・`IZANAGI_TRACE_DIR`・120 秒 timeout・rc 規則の局所版で、stdout と stderr を全文保存した (driver 版は保存しない)。完走した run だけ driver の `_verify` (証人なし、既存 mocc driver と同じ) に掛けた。停止した run の部分 trace は verify していない (trace は worker の終了時に flush されるので不完全)。
- driver の `compute_checks` / `all_pass` は使わない (32 check のうち trace0 系は「計装 patch の前後比較」という C では成り立たない前提を持つ)。分類は §3.2 の規則で親が行った。

### 2.3 cell と job

共通 = driver の W (200 tuple・zipf 0.9・読み比率 0・rmw・max_ope 5・1 s) / U (W の rmw なし・max_ope 1)、STOCK_G = mocc {BACK_OFF 1, KEY_SORT 0, TEMPERATURE_RESET_OPT 1}、`clocks_per_us` 2100、regime = temp_threshold hot 0 / cold 21 / default 10、thread 1 / 4。

| run | request | 計算ノード | Elapse | 起動器の rc | commit (checkout) | build と cell |
|---|---|---|---|---|---|---|
| m1-J1 | 29446.nqsv | bnode096 | 235 s | 0 | `237ec9286` | stock W 6 + V13 W 6 + V14 W 6 |
| m1-J2 | 29447.nqsv | bnode097 | 540 s | 0 | `237ec9286` | stock W 6・U 6 + V15 W 6 + V16 U 6 |
| m1-J3 | 29453.nqsv | bnode072 | 444 s | 0 | `267b8992f` | stock + V25 (W の hot t4・hot t1・cold t4・default t4) |
| m1-J4 | 29454.nqsv | bnode102 | 157 s | 0 | `267b8992f` | stock W 6 + V34 W 6 |

J1・J2 は既存 4 本だけを使うので、新規 2 macro の登録 commit (`267b8992f`) の前の `237ec9286` (新規 patch 2 本の追加だけ) から投げた。J3・J4 は登録後の commit から投げた。各 job は専用の計測用 worktree (detached、submodule 初期化、lock) から `tools/pegasus/dispatch_compute.py --task generic` で投げた。toolchain は 4 job とも policy の compiler digest と一致した。

## 3. 観測と期待の突き合わせ

「巡回」は verifier の `total_cycles`、X は `lock_coverage_violations`、P は `permutation_violations`。integrity の他の項目 (orphan read・version dup・txid の重複と欠番・genesis への commit・版の不一致・frame の破れ・I) は、表に書いたもの以外すべて 0。

stock 対照 28 run (J1 の W 6、J2 の W 6・U 6、J3 の W 4、J4 の W 6) はすべて serializable・certified・X/P と他の integrity 0、commit は W で 179,782〜200,816、U で 1,051,996〜3,555,838。

### 3.1 検出表

| V | 変異 | cell | 観測 | 分類 |
|---|---|---|---|---|
| V13 | validation の writer lock を飛ばす | W hot / cold / default t1 | indeterminate、X 1,072,230 / 1,877,685 / 1,885,977 (3 理由が同数)、巡回 0 | 期待した層で検出 (X、単一理由) |
| V13 | 同上 | W hot / cold / default t4 | non-serializable、X 1,228,132 / 2,349,066 / 2,368,502、巡回 679 / 3,471 / 3,570、version dup 3,725 / 19,591 / 21,405 | 期待した層で検出 (X)。併発 = 巡回・version dup |
| V14 | sort 後の write set から要素を落とす | W 全 6 cell | indeterminate、P (`size-changed`) のみ: hot t1 616,898・t4 4,433、cold 222,527 / 236,948、default 223,173 / 230,295。巡回 0・X 0 | 期待した層で検出 (P、単一理由)。hot の commit は t1 8 件・t4 183 件だけ |
| V15 | 入口検査の後に lock を外し公開直前に再取得 | W hot / cold / default t1 | indeterminate、X 1,310,422 / 1,358,158 / 1,370,868 (lock-lost の 2 理由)、巡回 0 | 期待した層で検出 (X、単一理由) |
| V15 | 同上 | W hot / cold / default t4 | non-serializable、X 1,453,797 / 1,448,105 / 1,466,025、巡回 3,393 / 1,403 / 1,430、version dup 16,006 / 8,454 / 8,866 | 期待した層で検出 (X)。併発 = 巡回・version dup |
| V16 | hot の update 経路で早期 lock を外す | U hot t1 / t4 | indeterminate、X 2,055,633 / 7,331,144、t4 は version dup 68,698、巡回 0 | 期待した層で検出 (X)。t4 の併発 = version dup |
| V16 | 同上 | U cold t1 / t4 | certified、commit 1,055,656 / 3,560,813 | 未発生 (閾値 21 > 温度上限 20 で hot 分岐に届かない、`cc/mocc/include/tuple.hh:12`) |
| V16 | 同上 | U default t1 / t4 | certified、commit 1,060,159 / 3,557,150 | 発火未確認の S (診断なし) |
| V25 | 逆順 lock の正準順への復元を飛ばす | W hot t1 | certified、X/P 0、commit 182,801。診断 reached 1,304,770・changed 447,413・committed 177,188・skipped_locks 576,713 | 盲点として certified (lock 順違反を含む完走履歴) |
| V25 | 同上 | W hot / cold / default t4 | 120.1 秒で run timeout。stdout は起動時のフラグ表示だけ、診断行なし | 停止 (同 job の stock 同 cell は約 1 秒で完走。原因は未確定) |
| V34 (対照) | 温度述語 4 site を `!(temp < threshold)` に | W 全 6 cell | certified、X/P と他の integrity 0、commit 178,965〜198,911 | 対照正常 (誤検出なし)。評価は site 297・460 だけ (§3.3) |

### 3.2 分類の規則と集計

分類の規則は事前登録 (段 4 裁定 R4) に、段 6 の erratum を 1 つ足したもの: 期待した層の counter が正 → 期待した層で検出 (併発層は別欄)。期待した層が 0 で他層だけが正 → 別の層で検出。S のとき、V25 は changed ≥ 1 かつ committed ≥ 1 なら盲点として certified。S で診断や source が未到達を示せば未発生。診断の無い既存 4 本の S は発火未確認の S (五分類に入れない)。run timeout は停止 (verdict なし)。同 job の stock 同 cell が異常なら帰属不能 (今回 0)。**erratum (段 6、`verbatim/s6-ruling.md`):** stock と V34 の正常な S に名前が無かったので「対照正常」を足した。計測の後に足した名前で、変異 cell の分類は変えていない。

| 分類 | cell 数 | 内訳 |
|---|---|---|
| 期待した層で検出 | 20 | V13 6、V14 6、V15 6、V16 hot 2 (うち 4 thread の 7 cell は巡回・version dup の併発あり) |
| 別の層で検出 | 0 | — |
| 盲点として certified | 1 | V25 hot t1 |
| 未発生 | 2 | V16 cold t1・t4 |
| 発火未確認の S | 2 | V16 default t1・t4 |
| 停止 | 3 | V25 hot t4・cold t4・default t4 |
| 対照正常 (誤検出なし) | 6 | V34 全 cell |
| 誤検出・帰属不能 | 0 | — |
| 計 | 34 | 変異 28 + 対照 6 (stock 28 run は別) |

### 3.3 V34 の到達範囲

site 別の評価回数 (t1 / t4): 297 行 = hot 839,305 / 896,703、cold 892,763 / 932,229、default 893,668 / 933,028。460 行 = hot 839,305 / 930,430、cold 892,763 / 970,573、default 893,668 / 972,708。567 行・971 行 = 全 cell 0。境界の評価は hot だけ (t1 = 297・460 とも 839,305 で全評価、t4 = 249,177 / 256,672)、cold・default は 0。W は読み比率 0・rmw なので READ_MODIFY_WRITE だけを生成し delete を呼ばない。read した tuple は write set にも入り、`construct_RLL()` が重複した read 要素を飛ばすので、site 567・971 に届かない (段 6 レビュー A の F3)。

### 3.4 先行記録との関係

- 旧 pin (e9e477ca + 計装 patch、2026-09-18、設計書 §5.1) と層の型は同じだった: V13・V15 は 1 thread で X だけ、4 thread で巡回と version dup が併発、V14 は全 cell で P だけ、V16 は hot で X (4 thread は version dup 併発)・cold と default は certified。件数は pin・run が違うので比べない。
- C 相当の先行 6 走 (`output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json`、既定 regime のみ) とも型が一致する。本 wave はそれを再利用せず、同 job の stock と揃えて取り直した。

## 4. 走らせなかったもの

- si の V28・V29・V36: 現行 parser が si の旧形式 trace を拒否する (残り (4)、[T-2854] の実装単位 (12) の後)。
- 停止 run の部分 trace の verify、停止時の診断を取り出す signal handler: 段 4 で採らなかった (停止は verdict を持たず、部分 trace は不完全で情報にならない)。
- 既存 4 本への発火診断の追加: 依頼の scope 外 (段 4 裁定 P1)。そのため V16 default の S は「発火未確認」のまま残る。

## 5. 記録の置き場と束縛

- `raw/m1-J{1,2,3,4}.agg.jsonl`: 結果 JSON から親が抜き出した行 (meta = hostname・checkout HEAD・build source の OID・policy・patch の sha256 と touch set、run = verdict・各層の数・X/P の理由別件数・発火行・stderr の sha256)。抽出 script は job dir の `extract.py`。
- 結果 JSON の原本 (job dir `runs/`、大きいので repo に入れない): m1-J1 `2cae8d3f3b8c3a6b494f2962912aec7268ec05875849859679e76d869caad07b` (4,629,392 bytes)、m1-J2 `ebbc51b43dad7025ed03a71f6b93b58baf46bf1c7a112fe640358a493543d0f8` (10,018,679 bytes)、m1-J3 `c2d8e1d0905b97b40b78de30665d5421efa202d335143b230e4894f75b64dc7c` (238,337 bytes)、m1-J4 `f44ed450a2fad4c99f4b347c8e56c39f6dac8238f8dedd6ccfe7f0bdfac31a17` (260,943 bytes)。
- run ごとの stdout / stderr の原本は job dir `runs/m1-J*/raw/J*/`。

## 6. 焦点走

変更した本体 2 file (`condition_meaning_gate.py`・`screening_driver.py`) を参照する test と patch を glob する test、DW-O26 の inventory 4 群の計 33 file を、計測の終わった clean な計測 checkout (HEAD `267b8992f`) から `tools/run_tests.py --force-dispatch` で走らせた: **4,049 passed・8 skipped・失敗 0** (Elapse 144 秒)。実装子が `test_screening_driver.py` に足した追加検査 (既定値 0 の固定と、Genome 経由で裸マクロを供給できないことの固定) は、依頼の scope 外として統合しなかった。既存の key 集合 test はこの状態で緑である。新 macro を Genome から供給できないことは、既存の汎用 build 経路照合 (`screening-build-route-mismatch`) に依る (前回の silo 14 本と同じ)。

## 7. 変異 matrix (実装面の変異テスト)

実装面 (条件 gate の登録) の誤りを既存の test が殺すかを、`tools/mutation_worktree.py` を独立 clone (main = `267b8992f`) に当てて確かめた。runner = `tools/run_tests.py --force-dispatch` で `test_condition_meaning_gate.py`・`test_ccbench_spawn_sites.py`・`test_screening_driver.py`・`test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`。変異は段 4 裁定 R7 のとおりで、置換対象の一意性は spec を作る script が確かめた (job dir `make_spec.py`)。

- probe (全件 SURVIVED 期待の観測走、spec sha256 `496ae71f45301dd727374756141abfb1f54baa32358db3a3ccfc744dea1a2ad6`): 基準走 PASSED、正例 M0 は生存、M1〜M4 はすべて赤 (`raw/mutation-probe-summary.json`)。
- final (観測した赤 node を期待 node に固定、spec sha256 `612bca78c810dad14e849398174c34336bdc23c21fb5dd837000e696f2bd6b62`): 基準走 PASSED、**KILLED 4・SURVIVED 1 (正例)・MISMATCH 0** (`raw/mutation-final-summary.json`、原本 sha256 `ae57956afdaf299ebb7c926e69a9b64b8ec8716e0ce1cc892bf3ab1415e24e55`)。

| 変異 | 誤り | 赤 node 数 | 赤の理由 |
|---|---|---|---|
| M0 (正例) | comment 1 語の変更 | 0 | — |
| M1 | `_DEFINE_SPECS` から V25 の macro を削る | 7 | 登録簿から 1 件欠けた (在庫照合・domain 件数・branch 選択の 3 parametrize・screening の既定値照合) |
| M2 | `_CONDITIONAL_BRANCH_WITNESSES` から V34 を削る | 5 | witness の欠落 (patch 束縛・branch 選択の 3 parametrize・domain 件数) |
| M3 | `_DEFINE_SPECS` の V34 の key を 1 字違える | 7 | 登録名と patch の macro の不一致 |
| M4 | V25 の site 数を 5 → 6 | 4 | site 数と patch 本文の不一致 |

各変異の赤 node は複数だが、どれも 1 つの誤り (登録簿の 1 件の欠落・名前違い・件数違い) から生じている。赤 node の形は前回の silo 14 本の登録 (`output/insights/2026-09-23/t2847-mutation-run/README.md` §7) と同じだった。patch の中身の誤り (未定義側の一致・1 patch 1 機構・等価性) は test では殺せないので、実装子と親の source 照合、段 6 レビュー、§3 の実走で確かめた。

計算ノードの使用 (job Elapse): probe 7 request 691 秒、final 7 request 687 秒。

## 8. 受入全走

受入全走と land は本書を含む記録 commit の後に走るので、本書には結果を書かない (job dir の `acceptance-*` / `land-*` が正本)。

## 9. 限界・言わないこと

- 各 cell は 1 回の有限の走の観測である。停止の 3 cell は、原因 (worker 間の相互待ちか、変更が持ち込んだ自己待ちか) を確かめていない。段 6 レビュー A は source 上で変更由来の二重取得・二重解放の経路を見つけなかったが、停止時の stack や lock 所有は採っていない。
- 「盲点として certified」(V25 hot t1) は、lock 順の違反を含む取引が commit した履歴が certified になったという観測で、verifier の欠陥の主張ではない (lock 順は直列化可能性の条件ではない)。
- V16 default の certified は、発火診断が無いので「変異が起きなかった」のか「起きたが捕まらなかった」のかを区別できない。
- V14 hot の 2 cell は commit が 8 件と 183 件しかない短い履歴での検出である。P の件数 (616,898・4,433) は commit 数を大きく上回り、commit しなかった試行でも P 行が出ている。hot で commit がほぼ止まった理由は確かめていない。
- V34 の対照は評価された 2 site (297・460) についてだけ言える。567・971 の実行時の等価性は測っていない。
- verify は既存 mocc driver と同じ証人なし verifier で、certified は commit trace の完全性までは主張しない (設計書 §2)。
- 性能値は取っていない。job の Elapse は計算資源の記録である。
- tracked の verifier・driver・policy・既存 patch・calibration JSON は編集していない。条件 gate への登録・screening の既定値・test の表の更新は、新しい patch を既存の経路で build するためのものである。
