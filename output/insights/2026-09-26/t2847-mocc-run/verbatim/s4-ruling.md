# 段 4 裁定 — [T-2847] mocc-run (2026-09-26)

入力: brief.md、codex/s2-plan.md (受理 rc=0)、codex/s3-consult-a.md (F01〜F08)、codex/s3-consult-b.md (B-01〜B-09)。裁定 inbox 再走査 (段 4 直前): 最新 2026-09-23 full34、wave 開始後の新着なし。local main = 74e6d2f23 (起点からの差は docs のみ、受入前に取り込む)。

## 所見の裁定

| ID | 裁定 | 採否・反映 |
|---|---|---|
| P1 | 部分的 real | 既存 4 本の patch は変えない (診断 overlay は scope 外)。S の cell は「発火未確認の S」を独立の状態として記録し、五分類に押し込まない。V16 の cold (閾値 21 > 温度上限 20、`cc/mocc/include/tuple.hh:12`) だけは source で「未発生 (機構に未到達)」 |
| P2 | 部分的 real | 停止した run は「停止」と記録し verdict を付けない。signal handler・部分 trace の追加 verify は採らない (F01・B-08)。trace は thread_local ofstream の destructor で flush されるので停止時の trace は不完全で、verify しても情報にならない |
| P3 | real | V34 = W の 6 cell、V25 = W の hot t4・hot t1・cold t4・default t4 |
| P4 | real | そのまま |
| P5 | real (限定) | 既存 mocc driver と同じ証人なし verify。S は「証人なし verifier の判定」と明記し commit の完全性は主張しない |
| F01 | real must-fix | 採用 (P2 に反映)。停止 run の診断欠落は「診断欠落」と記録。停止は、同じ job の stock の同 cell が完走していることを対照にして「変異 build で停止」と書くが、相互待ちへの帰属は主張しない (F03) |
| F02 | real must-fix | 採用。主分類 = 期待層の counter が正なら「期待した層で検出」、併発した他層は別欄。期待層が 0 で他層だけ正のときに限り「別の層で検出」 |
| F03 | real should | 採用。V25 の完走 S は「lock 順違反を発火させた完走履歴が certified」と書き、deadlock の実証とは分ける |
| F04 | real should | 採用。V34 の診断は site 別 reached (4) と site 別 boundary (temp == threshold の評価数) を出す。cold は境界未評価が期待。boundary 0 の site について「境界を実測した」と書かない |
| F05 | real | P1 に反映。完了判定を下記 R4 で改める |
| F06・F07 | real should | 採用。旧 pin の数値を pin C の期待値として固定しない (期待は層だけ)。巡回・X・P・version dup・他 integrity を run ごとに別欄で保存 |
| F08 | real should | 採用。段 6 レビューで新 macro が genome / screening の既定値以外から供給されないことを確認 (前回と同じ隔離) |
| B-01 | refuted (前提違い) | 既存の pin 候補経路 `s3_mocc_lock_coverage._candidate_main` (同 file 657 行〜) が、policy を `_load_policy` のまま (policy の mocc_trace.new_oid = e9e477ca、driver の PIN と一致) 読み、build は候補 OID (= C) を checkout している。起動器もこの先例どおり PIN 定数・policy を変えずに読み、checkout だけ C にする。結果 JSON に policy の new_oid と build source の OID を両方書く |
| B-02 | real must-fix | 採用。起動器が `_run_trace`・`_variant_run` と同じ argv・env・timeout・rc 規則の局所版を持ち、stdout・stderr (発火行を含む) を job dir に保存し、verify は既存 `_verify()` をそのまま呼ぶ。trace dir は verify 後に削除 (大きいので保存しない)。verifier の stdout (record) は保存 |
| B-03 | real must-fix | 採用。R4 |
| B-04 | real must-fix | 採用。`test_ccbench_spawn_sites.py` の件数固定 2 箇所 (3553 行・3580 行付近) を登録 author の所有に入れる。[T-2849] の `t2849-unit-a` と同じ行なので、取り込み時に両方の増分を足した値へ Codex が合流させる |
| B-05 | real should | 採用。見積りは R6 (mocc の実測単価 = [T-2844] の compute 1 走、stock 2 走 + 負例 4 走で Elapse 132 秒、worklog entry 1818) で再計算、walltime 上限でも 2 node 時間未満 |
| B-06 | real should | 採用。`compute_checks` / `all_pass` は使わない。run ごとの記録と親の分類 (R4) にする |
| B-07 | real | P1 に反映 |
| B-08 | real should | 採用。signal handler と部分 trace verify を採らない。V25・V34 の inert 確認は author が「macro 未定義で枝を除いた全文が pin C と一致」を示す (前回と同じ)。TRACE=0 の別 build は取らない |
| B-09 | real should | 採用。変異候補 5 (既定値) を外す。帰属は変異 (誤り) 単位 |

## R1 — scope (確定)

- 既存 4 本 (`patches/broken-mocc-{lockskip-validation,permutation-erase,early-unlock,hot-update-unlock}.patch`) を無変更で pin C に当て、driver の MATRIX 36 cell を実走。
- 新規 2 本: V25 = `patches/broken-mocc-skip-canonical-restore.patch` / `IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE`。V34 = `patches/control-mocc-negated-temperature-predicate.patch` / `IZANAGI_BREAK_MOCC_NEGATED_TEMPERATURE_PREDICATE` (前回の対照と同じく `IZANAGI_BREAK_*` 接頭辞。既存の `mocc-temperature-predicate-variant.patch` とは別物)。
- 登録: `condition_meaning_gate.py` の `_DEFINE_SPECS` (mocc 既存と同形 `_MOCC_OWNER`・`ycsb_mocc.exe`)・`_CONDITIONAL_BRANCH_WITNESSES`・`_CONDITIONAL_BRANCH_SITE_COUNTS` (site 数は patch の実 `#if` 行数)、`screening_driver.py` の既定値 0、test の表 (`test_condition_meaning_gate.py`・`test_p3_s4_loop.py`・`test_ccbench_spawn_sites.py` の在庫照合と件数固定 2 箇所・`test_screening_driver.py`)。受理条件は緩めない。
- 起動器 `launch_mocc_run.py` (repo 外、job dir)。

## R2 — V25・V34 の patch と発火診断 (契約)

- V25: plan の限定 gate (`vioctr > 0` ∧ upgrade でない ∧ 再取得する RLL_ の key と保持中の CLL_ suffix に共通 tuple が無い) が成立するときだけ、`cc/mocc/transaction.cc` 835〜859 行の解放と CLL_ 除去を飛ばす。不成立なら元の復元。正準順 lock loop・対象 tuple の lock・X emitter・validation は変えない。
- V34: 4 site (297・460・567・971) の `temp >= FLAGS_temp_threshold` を `!(temp < FLAGS_temp_threshold)` に。971 は `||` の結合を括弧で保つ。
- 診断 (前回 R2 と同形): macro 有効時だけ file static の `std::atomic<uint64_t>` を relaxed で加算、transaction-local の flag を `begin()` で落とし、commit 成功で committed を加算、process 終了時に static object の destructor から stderr へ 1 行 `T2847_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>[ <extra>=<n> ...]`。文字列に `IZANAGI_` を含めない。lock 保持中に I/O を置かない。
  - V25: reached = 限定 gate の評価で vioctr > 0 だった回数、changed = 復元を実際に飛ばした回数 (保持したまま省いた lock ≥ 1)、committed、extra `skipped_locks` = 飛ばした lock の総数。
  - V34: changed = 0 (定義上)、extra `site297` `site460` `site567` `site971` = site 別評価回数、`boundary297` … `boundary971` = site 別の temp == threshold の評価回数。committed は reached を含む取引の commit 数。
- 停止した run では診断行が出ないことがある (診断欠落として記録)。

## R3 — cell (事前登録。変更しない)

共通 = driver の W (200 tuple・zipf 0.9・rratio 0・rmw true・max_ope 5・1 s) / U (W の rmw false・max_ope 1)、STOCK_G、CLK 2100、regime hot 0 / cold 21 / default 10、run timeout 120 s。

| 行 | build | cell |
|---|---|---|
| stock | S | 各 job で使う (workload, regime, thread) ごとに 1 run |
| V13 | L | W × 3 regime × {1,4} |
| V14 | P | W × 3 regime × {1,4} |
| V15 | E | W × 3 regime × {1,4} |
| V16 | H | U × 3 regime × {1,4} |
| V25 | R | W × {hot t4, hot t1, cold t4, default t4} |
| V34 | T | W × 3 regime × {1,4} |

## R4 — 期待と分類 (事前登録)

期待 (層): V13 = X (t4 は巡回・version dup の併発を別欄)、V14 = P (`size-changed`)、V15 = X、V16 = hot で X (t4 は version dup 併発を別欄)、cold は未到達で S、default は S (発火未確認)、V25 = hot t4 は停止または完走 S (X/P 0)、hot t1 は完走 S、cold/default t4 は S または停止、V34 = 全 cell で非空 S・X/P・他 integrity 0。stock = 全 cell で非空 S・X/P・他 integrity 0。

cell の状態 (一意):
1. **期待した層で検出** — 期待層の counter が正 (verdict N / I)。併発した他層は別欄に数値で書く。
2. **別の層で検出** — 期待層が 0 で、他層の counter が正。
3. **盲点として certified** — S で、診断の changed ≥ 1 ∧ committed ≥ 1 (V25 のみ)。
4. **未発生** — S で、診断が reached または changed = 0 を示す、または source で未到達が示せる (V16 cold)。
5. **誤検出** — 対照 (stock・V34) が N / I。V34 が N/I なら patch の等価性を再監査。
6. **発火未確認の S** — 診断の無い既存 4 本の S (V16 default ほか)。五分類に入れない。
7. **停止** — run timeout。verdict なし。同 job の stock 同 cell が完走していれば「変異 build で停止」、相互待ちへの帰属は主張しない。診断欠落なら併記。
8. **帰属不能** — 同 job の stock の同 cell が N / I・空・integrity 不良・停止。

行 (V) の要約は cell の状態の内訳 (件数) で書き、1 語に潰さない。**完了判定** = 6 行の全 cell (既存 36 + V25 4 + V34 6 = 46) に上の 8 状態のどれかが実測で付いた insight。状態 6・7・8 が残っても完了とし、限界として書く (結果を見て patch・cell を足さない)。

## R5 — job 分割 (事前登録)

| job | build | run | walltime |
|---|---|---|---|
| J1 | S + L + P | stock W 6 + L 6 + P 6 = 18 | 00:12:00 |
| J2 | S + E + H | stock W 6 + stock U 6 + E 6 + H 6 = 24 | 00:12:00 |
| J3 | S + R | stock W 4 (R と同じ cell) + R 4 = 8 | 00:18:00 |
| J4 | S + T | stock W 6 + T 6 = 12 | 00:12:00 |

各 job は専用の計測用 checkout (wave の実装 commit の detached worktree、submodule 初期化、lock) から `tools/pegasus/dispatch_compute.py --task generic` で同時投入。

## R6 — 計算の見積り (D2212 項 4)

実測単価: mocc の compute 1 走 ([T-2844]、build を含み stock 2 + 負例 4 run) Elapse 132 秒、silo の変異 job (build 4〜5・run 4〜8) 139〜194 秒。見込み: J1・J4 ≈ 150〜250 秒、J2 ≈ 200〜350 秒、J3 ≈ 150 秒 + 停止 1 本あたり 120 秒 (最大 4 本) → 実走計 ≈ 0.2〜0.45 node 時間。焦点走 2 回 ≈ 0.1、変異 matrix (probe + final) ≈ 0.4、受入 1〜2 回 ≈ 0.25〜0.5 → **合計 ≈ 0.95〜1.45 node 時間**。walltime 上限でも実走 54 分 = 0.9 + 検査 1.0 = 1.9 < 2。よって投入前のユーザー確認は不要。実績が 2 に達しそうになった時点で止めて確認する。

## R7 — 変異 matrix (事前登録、段 6 で実走)

実装面 = 新 patch 2 本、condition_meaning_gate.py の登録、screening_driver.py の既定値、test 4 本の表。
- M0 (正例): 登録 file の comment 1 語変更 → 生存
- M1: `_DEFINE_SPECS` から `IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE` を削る → 在庫照合・domain 固定が赤
- M2: `_CONDITIONAL_BRANCH_WITNESSES` から V34 の 1 件を削る → witness の patch 束縛が赤
- M3: `_DEFINE_SPECS` の V34 の key を 1 字違える → 登録名と patch の macro の不一致で赤
- M4: `_CONDITIONAL_BRANCH_SITE_COUNTS` の V25 の site 数を +1 → site 数と patch 本文の不一致で赤
期待 node は probe で観測し final で固定 (DW-M08)。帰属は変異単位。patch の中身 (inert・1 patch 1 機構・等価性) は test では殺せないので、author・レビューの source 照合と実走で確かめる。

## R8 — 段 5 分割

- U-A (author): patch 2 本 (V25・V34)。所有 = `patches/broken-mocc-skip-canonical-restore.patch`・`patches/control-mocc-negated-temperature-predicate.patch`
- U-D (author、U-A と並列): 起動器。所有 = unit worktree の `.t2847-launcher/launch_mocc_run.py` (親が job dir へ退避)
- U-C (author、U-A 統合後): 登録。所有 = `orchestrator/campaign/condition_meaning_gate.py`・`orchestrator/campaign/screening_driver.py`・`orchestrator/tests/test_condition_meaning_gate.py`・`orchestrator/tests/test_p3_s4_loop.py`・`orchestrator/tests/test_ccbench_spawn_sites.py`・`orchestrator/tests/test_screening_driver.py`
- `patches/README.md` の節と insight は親 (docs)。

## gate の禁止と正例 (DW-S04)

- 禁止: 登録 macro の supply は `ROUTE_CMAKE_CXX_FLAGS` の既定 0 のみで、genome の CCBENCH_ key から供給できない。正例: `_build_variant(macro="IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE")` が条件 gate を通り `-D…=1` で build される。
