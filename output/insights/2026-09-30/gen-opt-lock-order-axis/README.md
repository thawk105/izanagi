# 段 A の軸 silo-lock-order-policy (競合度順の施錠) の受理文法・骨格 API・骨格 patch の実装と生死確認 ([T-2886]、gen-opt md_13、2026-09-30)

- 種別: 実装 (Codex author) + 計算ノード 1 job の生死確認 + 変異検査。wave `dev-wave-lock-order-axis` (branch `worktree-dev-wave-lock-order-axis`)。
- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_13.txt` と `common-4.txt`。
- 仕様の正本: `output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md` §4 (と §11 の訂正)。関門設計: `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` §3.1・§3.4・§7 の U3。
- 段の記録: `verbatim/` (brief・段 2 プラン・段 3 相談 2 本・段 4 裁定と追補 2 本・段 6 レビュー 2 本と裁定・焦点再レビュー)。

## 0. 結論

- LLM の提案文字列を、**検疫 → 受理文法 → 単独 compile** の順に掛けてから hole へ書く入口 (`orchestrator/campaign/silo_lock_order_gate.py` の `order_gate`) と、その hole を持つ骨格 patch (`patches/silo-lock-order-variant.patch`) ができた。
- 名前つき対照 (版が新しいほど先に施錠、仕様 §4.5) を、実物の file のまま `order_gate` に通し、骨格を当てた Silo を計算ノードで trace build して既存判定器に 1 回掛けた。gate は合格、build は trace 版・性能版とも成功、判定器は RMW あり / なしの 2 run とも serializable、性能 build に trace の記号は無かった。
- 並べ替えが実際に起きたことを trace から数えた: commit した UPDATE だけの取引のうち 2 件以上書くものについて、key 順と違う順で施錠した取引が **RMW なしで 98,433 / 251,307 (39.17%)、RMW ありで 77,538 / 197,620 (39.24%)**。0 でない。
- 判定器の serializable は **既存判定器の 1 回の判定であり、certified の根拠ではない**。D1・D2 照合 (md_14) と、全候補をこの gate に通す driver 接続 (U5、[T-2888]) は、この wave には無い。

## 1. 何を作ったか

| file | 中身 |
|---|---|
| `orchestrator/campaign/silo_policy_grammar.py` | 軸固有の表 (型・列挙・field・必須 hook・返り値型・局所変数型・API 名前空間・状態 struct 名・禁止識別子) を `PolicyProfile` に束ね、parser がそれを読む形にした。既定 profile (`FUNCTION_POLICY_PROFILE`) は関数方策の軸のままで、`validate_policy(source)` の呼び方は変わらない。新しい `ORDER_POLICY_PROFILE` を足した |
| `orchestrator/campaign/axis_silo_lock_order.py` | 軸定数 (marker `silo-lock-order-policy`、flag `SILO_ORDER_VARIANT`、patch 名、PIN、手書き対照、排他 patch) |
| `orchestrator/campaign/silo_lock_order_api.hh` | API header (骨格に逐語で埋め込む bytes の正本、800 bytes) |
| `orchestrator/campaign/silo_lock_order_compile.py` | 単独 TU の compile (C++17 `-Wall -Wextra -Werror -fsyntax-only`) と、手書き対照用の UBSan harness。既存 `silo_policy_compile.py` の部品を import して使い、既存 file は変えない |
| `orchestrator/campaign/silo_lock_order_gate.py` | `order_gate`: `p3_s4_loop.quarantine(..., write=False)` → 新 profile の文法 → 単独 compile → (auditor があれば) deny-only veto → **全検査の後にだけ書く**。合格の意味は「検疫・文法・単独 compile の合格」であり、実 build の合格ではない |
| `orchestrator/campaign/silo_lock_order_hand/version_desc.cpp` | 名前つき対照 (`order_enabled` 常に true、`order_priority` = `(epoch << 29) \| tid`) |
| `patches/silo-lock-order-variant.patch` | 骨格 (267 行)。内容は `patches/README.md` の同名節 |
| `orchestrator/campaign/condition_meaning_gate.py` | `SILO_ORDER_VARIANT` を supply domain と compile-time 分岐 witness (site 14) に登録、従属する件数の記述を +1 |
| test | 新規 `test_silo_lock_order_{grammar,compile,gate,template}.py` (自走 `_run` 付き)。既存 `test_condition_meaning_gate.py`・`test_ccbench_spawn_sites.py`・`condition_gate_test_support.py` は新 macro の登録に従属する件数と fixture の追記だけ (§4) |

### 1.1 受理文法

土台は policy-C++ v1 の規則のまま (字句・式・literal・除算と shift・深さと個数の制限・helper の先行定義は共有で、触っていない)。新 profile の表は仕様 §4.4 のとおり: 型 `uint32_t`・`uint64_t`・`bool`・`void`・`OrderState`、列挙 `AbortReason` の 8 値、field `TxnContext {write_count, rand}`・`EntryContext {epoch, tid, locked}`・`AbortContext {reason, rand}`・`CommitContext {}`、必須 hook 4 つ、外部関数 `std::min`・`std::max`。

**禁止識別子は新 profile にだけ持たせ、宣言位置と参照位置の両方で拒否する** (rule_id `order.forbidden-identifier`)。段 3 の相談 (verbatim/consult-a.md 所見 1) が、許可リストの名前解決だけでは参照は拒否されても、状態 field・局所変数・helper の**宣言名**として `write_set_` や `result_` を書けてしまうことを見つけたため (仕様 §4.4 の「これらの名前を含む候補は拒否」に反する)。禁止集合は仕様 §4.4 の拒否表の全名 + この軸の骨格 namespace `izanagi_silo_order_skel`。既定 profile の禁止集合は空で、関数方策の軸の受理集合は変えていない (§3)。

### 1.2 骨格

仕様 §4.3 の処理順のとおり。`validationPhase` の stock の `sort(write_set_)` 1 行だけを、marker で区切った並べ替え関数の呼び出しに替えた。INSERT か DELETE を含む write set では stock の sort をして順序 hook を呼ばない。UPDATE だけなら `order_enabled` を 1 回、true なら各要素の TID word を 1 回だけ読んで `order_priority` を 1 回ずつ呼び、写した優先度・storage・key だけで比較する (比較中に hook も TID の読みも呼ばない)。`SILO_ORDER_VARIANT=0` では追加分がすべて前処理で消え、`source_digest.resolve` が STOCK を返す (§3 の test)。

並べ替え関数を marker で区切った自己完結の template にしたのは、test がその区間を切り出して mock の要素型で compile・実行し、挙動 (降順・tie-break・INSERT/DELETE の戻し・hook と TID 読みの回数・要素の多重集合の保存) を実物で確かめるため (段 4 裁定 B5)。

## 2. 生死確認 (計算ノード、既存判定器)

起動器は repo の外 (`/work/1/SFC/tanab/tmp/lock-order-2026-09-30/launch_lock_order_liveness.py`、Codex author、先例 `gen-opt-gate-liveness` の起動器を雛形)。repo の部品を import し、node-local の pinned checkout に骨格 patch を厳密適用、`order_gate` で名前つき対照を hole へ書き、直 CMake で build、判定器 CLI を `--expected-commits` と `--ccbench-root` で呼ぶ。workload は 200 record・zipf 0.9・rratio 50・1 取引 5 操作・4 thread・1 秒、RMW あり / なしの 2 run。

| job | request | 計算ノード | Elapse (dispatch log) | 起動器 sha256 | 結果 |
|---|---|---|---|---|---|
| live-1 | 37865.nqsv | bnode056 | 7 s | `c4bd66bb…` | preflight で停止: `pin.CURRENT_PIN` は短縮形 `6810666`、起動器が gitlink の完全 SHA と完全一致で比べていた。build 前なので計算の損失は僅か。起動器を Codex が直した (prefix 一致を要求し、以後は完全 SHA を使う。検査は緩めていない) |
| live-2 | 37881.nqsv | bnode052 | 81 s | `0190c5e71ebc69eefc7e9444813768e7d59692b3802845f04ac47ab8ce89400b` | 下表 |

live-2 の起動器自身の計測では、全体 75.9 s (依存物の準備 36.9 s、trace build 6.0 s、run 12.5 s × 2、性能 build 5.9 s)。計測木は `lock-order-c` (HEAD `91a316c7`、production の file は統合 commit `8f112994d` と同一で、差は起動器の scratch file だけ)。

| run | commit | abort | 判定器 | 2 件以上書く UPDATE だけの取引 | うち key 順と違う順で施錠 |
|---|---:|---:|---|---:|---:|
| RMW なし | 313,761 | 141,336 | rc 0、serializable | 251,307 | 98,433 (39.17%) |
| RMW あり | 246,704 | 9,400 | rc 0、serializable | 197,620 | 77,538 (39.24%) |

- gate: 合格 (auditor なし、`origin='initial'`)。trace build・性能 build とも configure / build の rc 0。性能 build の binary に `buildcache._assert_no_trace_symbols` を掛けて合格。
- **発火の数え方と範囲:** 各 `trace_<thid>.log` を判定器と同じ parser で読み、commit した取引の W 行の key の並びを見る。`writePhase` は W 行を `write_set_` の順に出し、`lockWriteSet` も同じ順で施錠するので、UPDATE だけの取引では W 行の順 = 施錠の順になる。YCSB は単一 storage、key は 8 byte (16 桁の小文字 hex で、文字列比較が stock の `key_` の順と一致)。INSERT / DELETE を含む取引は 0 件だった。**abort した取引の施錠の試行と、`order_enabled` を呼んだ回数 (仕様 §4.3 の「並べ替えを使った取引の数」) は数えられない** (計数 build が無い)。後者は段 A の試し ([T-2896]) の評価の前に要る。
- 原データ: `raw/live-1-result.json`・`raw/live-2-result.json`。

## 3. test

親の焦点走 (計算ノード、`tools/run_tests.py --force-dispatch`、変更 test + consumer test + inventory 4 群の 18 file):

| 回 | commit | 結果 | Elapse |
|---|---|---|---|
| f1 | `5120a367a` | 7 failed / 1,757 passed / 5 skipped | 100 s |
| f2 | `2148b469a` | 1,764 passed / 5 skipped | 157 s |

f1 の赤 7 件はすべて、新 macro を条件意味 gate に 1 つ登録したことに従属する箇所の列挙漏れだった (共有 fixture の Options.cmake に新 macro が無く configure が失敗した 3 件と、登録件数・define sink 分類の件数の固定 4 件)。追補裁定 2 (verbatim/s4-ruling-addendum-2.md) で、fixture への 2 行の追記と件数の +1 だけを許し、Codex が直した。既存 test の他の期待値は変えていない。5 件の skip は f1・f2 で同数で、内訳は `-rf` の出力からは特定していない (新 test 4 本は自走で skip 0 件)。

既存 4 軸の受理集合が変わらないことの証拠: (1) 既存の `test_silo_policy_grammar.py`・`test_silo_policy_compile.py`・`test_silo_policy_smoke_entry.py`・`test_silo_function_policy_template.py`・`test_p3_s4_loop.py` を無変更で緑、(2) 新 test が既存の文法 corpus (manifest の全件と手書き方策) を既定 profile に通して `(accepted, rule_id)` が期待どおり、明示の `FUNCTION_POLICY_PROFILE` でも同じ、新 profile ではすべて拒否されること、既定 profile の禁止集合が空であること (関数方策の軸では状態 field `result_` が今までどおり受理される) を確かめる。backoff・sort・trigger-gating の軸の検査器は変えていない (`p3_s4_loop.quarantine` は無変更)。

受入全走 (`tools/dev_wave_wait.py acceptance`、全 test):

- attempt 1 (tip `c3adf2175`): `stage=postcheck rc=70`。受入ツールが local main を取り込んでいる間に main がさらに進んだ競走で、test は 1 件も走っていない。
- attempt 2 (tip `562fec6d1`、取り込んだ main `213d411c6`): **1 failed / 28,423 passed / 74 skipped**。赤は `test_screening_driver.py::test_screening_condition_requests_cover_exact_define_specs` で、`screening_driver._CONDITION_DEFAULTS` の macro 集合が条件意味 gate の `DEFINE_SPECS` と一致することを要求する。新 macro の登録に従属するこの consumer を、段 1〜6 の consumer 列挙と焦点走の file 集合から落としていた (自分起因)。追補裁定 3 (verbatim/s4-ruling-addendum-3.md) で既定値表に `SILO_ORDER_VARIANT: 0` を 1 行足すことだけを許し、Codex が直した。`DEFINE_SPECS` を読む他の consumer (backoff_sweep・s1_direct_comparison・silo_ladder_rung1 と各 test) は attempt 2 で緑だった。

### 3.1 変異検査 (事前登録 M1〜M6、`mutation/`)

段 4 で実装前に登録した 6 変異 (verbatim/s4-ruling.md の表) を、対象 commit `2148b469a` を main に固定した独立 clone (D1009) に `tools/mutation_harness.py` を当て、runner を計算ノードへ直列 dispatch して走らせた。期待 node は login の自走 probe (`mutation/probe-p1.json`、Codex author の probe を親が実行、baseline 緑・各変異の注入と復元の sha256 と porcelain 空を照合) の観測から取った。

| id | 変異 | 赤になった test |
|---|---|---|
| M1 | 新 profile の禁止識別子の**宣言位置**の検査を外す (参照位置の検査は残す) | 宣言位置ごとの禁止名の拒否、新 profile が状態 field `result_` を拒否すること |
| M2 | 並べ替え関数の INSERT/DELETE の戻しを外す | 並べ替えの挙動 (mock compile) |
| M3 | 軸 ON の `NO_WAIT_OF_TICTOC` 未定義の `#error` を外す | 前提 flag の fail-closed |
| M4 | 優先度の比較を昇順にする | 並べ替えの挙動 |
| M5 | gate が文法検査より前に source を書く | gate の文法拒否・compile 拒否で source 不変、実 patch 上の拒否で source 不変 |
| M6 | OFF で骨格 namespace の宣言を 1 つ `#if` の外へ出す | OFF の `resolve == STOCK` |

- 初回 (tag m1) は spec の外側 timeout (3,600 s) が dispatch の待機契約 (待ち行列 5,400 s + 猶予 5,400 s) より短く、harness が起動前に止めた (rc=2)。外側 timeout を 12,600 s にして再投入した。
- 本走 1 回目 (tag m2、`mutation/out-m2.json`): KILLED 5、MISMATCH 1 (M5)。M5 は 3 test で検出されたが、期待に入れていた `test_touch_markers_api_and_quarantine` が赤にならなかった。login の自走は同じ process で名前順に走るため、変異下で実 patch 上の拒否 test が共有 fixture の source を書き換えたまま残し、後の test がそれを読んで赤になっていた。実行順に依存する巻き添えで、直接の検出ではない (`mutation/erratum-1.md`)。初回結果は残し、M5 の期待を直接検出の 3 node にした。
- 本走 2 回目 (tag m3、`mutation/out-m3.json`、spec sha256 `8c2dff92…`): **KILLED 6 / 6、期待 node と完全一致**、baseline 緑。
- 各変異について、同じ入力を拒否する別の層が前後・内側に無いこと (単一理由性) は、実装子の報告と段 6 のレビュー A (静的照合) で確かめた。M1 は参照位置の検査を残しても宣言位置の禁止名が通ること、M3 は値の不正の検査を残しても未定義が通ることを変異の形で示している。

## 4. 段の経過と裁定

- 段 2 プラン (条件付き GO)、段 3 相談 2 本 (どちらも NO-GO)。相談の must-fix: 禁止名が宣言位置で通る (上記 §1.1)、文法変異の照準のずれ、生死確認で既存の本番 build 経路を ~100 行で呼べる前提が不成立 (admission・build_context・証拠が必須) → 先例の起動器を雛形にした、発火計数が仕様の 2 件数のうち片方だけ → 範囲を限定して書く (§2)。
- 段 4 裁定 (verbatim/s4-ruling.md): 全所見を real と裁定。UBSan harness は候補ごとの gate に入れず、手書き対照と test の別入口 (関数方策の軸と同じ)。
- 追補 1・2: 新 macro の登録に従属する件数と共有 fixture を段 4 で列挙し漏れていた。実装子の報告 (件数 57→58) と親の焦点走 (7 件) で見つけ、許す変更を 1 行ずつ列挙してから直させた。
- 段 6 レビュー 2 本 (verbatim/review-a.md・review-b.md)、裁定 (verbatim/s6-ruling-1.md)、焦点再レビュー (verbatim/focus-1.md)。real と裁定して直したもの: template test が repo 外の作業 file を読んでいた、gate と実骨格 patch を通しで結ぶ test が無かった (足した: 実物の対照を gate 経由で実 patch の hole に書き、禁止名の候補では source が 1 byte も変わらない)、pin の直書き。
- nit に降格したもの: `-DSILO_ORDER_VARIANT=foo` のように未定義の識別子を値に渡すと、`#if` はそれを 0 と評価して stock 枝を選ぶ (review-a 所見 1)。Phase 3 の identity を決める前処理 (`source_digest.py`) は `-Werror=undef` で走るので、この build は identity を確定できず fail-closed で止まり、候補として台帳に記録されない。genome の値は driver のコードが整数で与える。関数方策の骨格も同じ形。最初の裁定理由 (「STOCK として記録される」) は焦点再レビューの指摘で誤りと分かり、訂正を裁定 file に追記した。

## 5. 限界

- 生死確認は各構成 1 回・小規模 (200 record・4 thread・1 秒)。既存判定器の緑は D1・D2 照合 (md_14) による certified ではない。
- 発火計数は commit した UPDATE だけの取引の W 行の順から取った。abort した試行と `order_enabled` の呼び出し回数は数えていない。
- `order_gate` の合格は単独 TU の compile まで。実 build は生死確認の 1 回だけで確かめた。全候補をこの gate に通す配線 ([T-2888]) は無い。
- 骨格 patch は pin C (`68106660`) にだけ当たる。F への pin 前進 ([T-2854]) や Silo 修正 ([T-2917]) の後は当て直しが要りうる。関数方策の骨格・sort 軸の骨格とは同時に当てられない。
- 並行で着地した MOCC 版の軸の設計 (`output/insights/2026-09-30/gen-opt-mocc-policy-axis/README.md` §4.3) は、文法を「CC に依らない核 + CC ごとの表」に分け、[T-2886] と先に着手した方が核を 1 度だけ作る、と定める。この wave の `PolicyProfile` がその核の最初の形になる。同設計が求める「分ける前の文法の凍結写しと、分けた後の文法を同じ入力列に掛けて判定の全 field と compile の判定が全件一致する」差分 test は、この wave では作っていない (§3 の証拠は既存 test の無変更の緑と `(accepted, rule_id)` の照合まで)。`silo_policy_compile.py`・`silo_policy_ir.py` の表の分離もしていない。
- test 名 `test_module_claim_names_the_exact_79_define_supply_domain` (main 側の vhash-interval-gc が改名した名前) は nodeid を変えないために据え置いたので、名前の数字 (79) は合成後の件数 (80) と合わない。
- land 前の main 取り込みで 2 度、同じ登録簿を変えた並行 wave と合成が要った。(1) main 55dbd4911: `test_ccbench_spawn_sites.py` を両側が別の行で変え、自動合成は競合なしだが実装面が両親のどちらとも違うので、Codex に 4 版を照合させた監査付き message で commit (8dc829e3b)。(2) main e894f5242: vhash-interval-gc が条件意味 gate に CICADA_INTERVAL_* の 4 macro を登録し、件数の行が 3 file で競合した。Codex が両側の登録を残し、件数を「共通祖先 + 両側の増分」で合成した (define 数 80、compile-time witness 62、meaning 63、CMake cache 25、sink 分類 76・80・66、c495d42bf)。競合を解いた merge は land の再実行検算を通らないので、この合成を含めて受入を取り直した。
