# 親 brief — [T-2772] mocc auditor-live 相当の機械実証 wave 1 (経路共通、template 不要)

- wave: `dev-wave-t2772-mocc-mutation-proof-wave1`、branch `worktree-dev-wave-t2772-mocc-mutation-proof-wave1`、base = local main `d2ebef7a4` (2026-09-18 06:15 JST)
- 起点: ユーザーの `/dev-wave [T-2772]` 引数 (D579、D2134 項 3〜5・8)。設計正本 = `output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md` §6〜§7・§12 (§13 の未確定 6 件は本 brief §3 で確定)
- 研究前進: D2114 の「mocc を名指し条件で第 2 例として成立可否を判定できる」主張に要る D579 の独立実証 (機械 4 点のうち残る hot/cold の実行証拠) を、固定 producer (e9e477ca + 計装 patch) の compute 実測で埋める。完了判定 = 新 producer の compute `all_pass`、hot 専用負例の完走 (timeout なし)、stock-U 対照 6 走 certified。**緑でも探索・pin 前進・軸採用は解禁しない** (D2134 項 9)

## 1. scope (本題の実装だけ)

作る物 (設計 §12 wave 1 の表そのまま):

| 物 | path | 内容 |
|---|---|---|
| 新負例 patch | `patches/broken-mocc-hot-update-unlock.patch` | 裸 define `IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK`、preimage = e9e477ca + `instr-mocc-lock-coverage.patch`、§6 の balanced 形 (下記 P2) |
| 新 driver | `orchestrator/campaign/s3_mocc_mutation_proof.py` | 36 走 matrix (§7) と新 check、run record に実 argv・終了状態を記録。旧 driver `s3_mocc_lock_coverage.py`・旧 JSON・14 check は **1 byte も変えない** |
| 新 test | `orchestrator/tests/test_mocc_mutation_proof.py` | 負例の静的検査 (balanced・一意 witness)、matrix / JSON / 入力由来 check、JSON の完全性と sha 束縛 |
| 新 JSON | `output/env/pegasus/calibration/s3_mocc_mutation_proof.json` | 新 proof。旧 JSON は上書きしない |
| docs | `patches/README.md` | 既存 mocc 節に隣接して新負例と限定事項 (docs-only、親が書いてよい) |
| 登録簿閉包 | 下の anchor 表 | 5 箇所 + テスト側 3 箇所 |

scope 外 (足さない): 正式 template・軸定数 module・auditor.md の mocc 節・DQ / consumer 束縛の対照・gate test・n=1 (以上 wave 2)、read 側 hot 経路 witness、RLL 再試行 witness、DELETE 動的被覆、verifier の編集、汎用 driver 登録台帳、全経路解析、pin 前進、`docs/phase3.md` 編集、仮想リスク向けの gate・検査・台帳・一般化。

## 2. 確定済みユーザー裁定と不変条件

- D579 (mocc は変異探索面にしない)、D2134 項 1〜9 (本設計の正本)、D1686 (X 3 点 / P、balanced 負例、exactly-one directive)、D1687 (`#line` 例外、TRACE=0 論理行列)、D95 (実装面は Codex author、親は直接編集しない)、D14 / 規律 1 (trace は build で完全除去)、規律 2 (正しさゲートを緩めない — 負例が沈黙すべき regime で沈黙しない場合は patch 側を疑い、check を緩めない)。
- 旧 driver・旧 JSON・旧 patch 4 本 (sha は旧 JSON に束縛) は不変。`external/ccbench` の gitlink (511c9538) は動かさない。proof は `patchharness.checkout(e9e477ca)` の隔離 checkout で行う (T-2294 と同経路)。
- 新 build launcher は materializer 登録簿で NON_ADMISSIBLE。計測値ではない (性能値の出所にならない)。
- 編集面照合 (起動時、ユーザー指示): 稼働 wave 20 本のうち `patches/` / condition gate に触りうる 2 本 (T-2774 mocc torn-read probe、T-2737 SS2PL gate 対照) へ通知し、両方から「repo 側の `patches/`・登録簿は編集しない」と返答を得た (06:25〜06:28 JST)。全 worktree の dirty / branch 差分走査でも上記 file に hit なし。衝突なし。
- 新 driver は `orchestrator/campaign/` 配下で `tools/pegasus/dispatch_compute.py --task generic` から起動する (T-2294 と同経路)。`hooks/guard_bash.py` の admission 判定は `tools/pegasus/` 配下だけを未登録 deny にするので F660 (新規 Pegasus 実行体) は本 wave に当たらない (親が `_pegasus_admission_entry` 614〜629 行で確認)。

## 3. §13 未確定 6 件の確定 (親が e9e477ca の現物で実測)

1. `loadepot.temp` = `Epotemp` の `uint64_t temp : 32` bitfield (`cc/mocc/include/tuple.hh:34〜41`)、`FLAGS_temp_threshold` = `DEFINE_uint64(temp_threshold, 10, …)` (`cc/mocc/include/common.hh:40`)、`TEMP_MAX` = 20 (`tuple.hh:12`)。閾値 0 で述語は常に true、21 で常に false。
2. U workload (`ycsb_rratio=0, ycsb_rmw=false, ycsb_max_ope=1`) は `include/ycsb.hh:58〜79` で全操作が `Ope::WRITE`、`:128〜133` で `tx.update()` 直接呼出。`update()` (`transaction.cc:418〜485`) は read_set_ を作らない。**実走での確認は compute JSON の `txns > 0` と R 行 0 (`non_insert_writes == txns`) で示す**。
3. 温度上昇は `construct_RLL()` (`:915〜955`) の `failed_verification_` を持つ read 要素だけで起きる。blind update は read_set_ 空 → 温度は 0 のまま → 既定閾値 10 で述語 false。default/U 沈黙の前提は成立 (静的)。
4. 4 thread hot 強制での hang: 未実測。U では validation が abort しない (lock() は CLL 既存で早期 return `:744〜746`、absent 検査は DELETE 無しで偽、read_set_ / node_map_ 空) ので RLL は常に空、pending の再取得は 1 lock 待ちのみ → 循環待ちは静的には無い。**compute で timeout 120 秒を hang と判定し、hang なら失敗として記録する (完走未確認を実証済みと書かない)。**
5. spawn_sites 側の裸 define 登録簿 = `orchestrator/tests/test_ccbench_spawn_sites.py` (`_patch_added_define_interfaces` 623〜 が `patches/*.patch` から裸 define を導出し `DEFINE_SPECS` と exact 一致を要求、`_DIRECT_SAFE_ALLOWLIST` 42〜 が module 別 subprocess site を exact 登録、`test_direct_spawn_allowlist_constants_cannot_reach_protected_ratios` 4094〜 が module の FLAGS を holdout 判定)。加えて `test_p3_s4_loop.py:7862` (B-3 `allowed_non_variant_tokens`) が `patches/*.patch` の裸 macro を patch 別に allowlist。
6. §3.2 (a) は別 T-2774 が同時刻に稼働中 (本 wave は触れない)。

## 4. 親の provisional 裁定 (攻撃対象)

- (P1) 新 driver は旧 driver の private helper を **import で再利用**する (`PIN`, `SOURCE_REL`, `STOCK_G`, `SINGLE_FLAGS`, `HIGH_FLAGS`, patch 定数, `_load_policy`, `_resolve_toolchain`, `_prepare_dependencies`, `_common_configure_args`, `_verify`, `_trace_counts`, `_trace0_record`, `_sha256_file`, `_run_checked`, `_apply_owned_patch`)。新 driver 自身が持つのは `_require_condition_gate` (driver_id = `orchestrator.campaign.s3_mocc_mutation_proof`)、`_build_variant` (新 materializer 登録)、`_run_trace` (実 argv・rc・timeout を record に残し、例外にしない = 新 spawn site)、matrix、`compute_checks`、`main`。700 行の複製はしない。旧 driver は無変更のまま。
- (P2) 負例 patch の形: file scope に `#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK` 1 組 (`static constexpr bool izanagi_break_mocc_hot_update_unlock` と `static thread_local Tuple* izanagi_hot_update_pending = nullptr;` を両腕に宣言、`[[maybe_unused]]`) + `#line 17`。site 1 = `update()` の `:459` を block 化し `lock(tuple, true)` の直後、`status_ != aborted` かつ pending が空のときだけ `tuple->rwlock_.w_unlock(); pending = tuple;` (CLL の writer 記録は残す)。site 2 = `writePhase()` の publish 検査後・`__atomic_store_n` (`:1195`) 前に `if (pending == (*itr).rcdptr_) { pending->rwlock_.w_lock(); pending = nullptr; }`。site 3 = `abort()` の `unlockCLL()` (`:1069`) 前に同じ再取得。site は `if constexpr` で従い、各 block 後に `#line` で論理行を復元。`TxExecutor::lock()` は使わない (stale CLL で再取得が省略され `0 → 1` に壊れる、設計 §6 項 3)。
- (P3) 設計 §7 の「別 integrity 異常 (`version_dups` / `dup_txids` 等) は区分を問わず赤」は **観測のみの t4 負例走には適用しない** (lock を壊した 4 thread では同 tid の重複 version が正当に起きうる — T-2294 の lockskip_high は cycle 3,754 を出しており、integrity clean を要求すると恒偽になる)。integrity は全走で記録し、要求するのは受入必須走 (stock 12 走、t1 負例、hot-update の cold/default 4 走) だけ。→ 設計からの逸脱なので段 3 で攻撃し段 4 で裁定する。
- (P4) regime は runtime gflag `-temp_threshold={0,21,10}` を run flags で渡す。build は trace=1 × 5 (計装 stock、負例 4 本) + trace=0 × 2 (identity) = 7 本。stock-W と stock-U は同じ計装 stock binary。
- (P5) check 名は設計 §7 の表の候補名をそのまま採る (`stock_{hot,cold,default}_{t1,t4}_certified_and_silent` … `hot_path_evidence_method_is_negative_control`、`trace0_*` 3 本、`toolchain_matches_policy`、`all_broken_patch_touch_sets_are_transaction_only`)。観測のみ 11 走は run record に `acceptance: "observe"` を持ち check に対応させない。`matrix_runs_complete_and_terminated` は 36 走の実 argv・rc=0・verifier record の存在だけを見る。
- (P6) 時間予算 (DW-O13 の実測): verifier は write-only 合成 trace 100 万 txn で wall 17.3 秒・RSS 0.96 GB (login、load 25、2026-09-18 06:31 JST)。4 thread U の txn 数は未実測 (推定 300〜800 万)。新 driver は `RUN_TIMEOUT_S = 120`、`VERIFIER_TIMEOUT_S = 900` (= 100 万 txn 実測の 52 倍)、job は gen_S (Elapse 3600 秒)。総所要見積 20〜25 分。超過が compute 1 回目で判明したら regime 別 3 job への分割を fix で入れる (先回りしては作らない、DW-G05)。
- (P7) `_run_trace` は timeout / 非 0 rc を例外にせず run record (`terminated`, `returncode`, `timed_out`) に残す。JSON は走ごとに atomic に書き足す (job kill でも部分証拠が残る)。`all_pass` は `checks` 全 true かつ 36 走揃いのときだけ。
- (P8) 4 thread hot-update-unlock-U の期待は「X>0、P=0」を観測として記録し、reason 別正数を要求しない (設計 §6)。

## 5. 模擬 / 実の差

- 静的検査・登録簿閉包・focus test は login で実測する。build は login で生死確認 (T-2294 の `liveness-run.sh` 型: 負例 4 本 + 計装 stock を TRACE=1 で build、`-Wall -Wextra -Werror` で通す。benchmark は走らせない)。
- 36 走の実測は compute (gen_S) の generic dispatch 1 job。login で benchmark は走らせない (runbook)。
- 変異 matrix は段 4 で事前登録し段 6 で走らせる。受入全走は tip に対して 1 回。

## 6. 変更面の実アンカー表

| file | 箇所 | 変更 |
|---|---|---|
| `patches/broken-mocc-hot-update-unlock.patch` | 新規 | (P2) |
| `orchestrator/campaign/s3_mocc_mutation_proof.py` | 新規 | (P1) |
| `orchestrator/tests/test_mocc_mutation_proof.py` | 新規 | 設計 §12 の 4 node 候補 + JSON consumer |
| `orchestrator/campaign/materializer_admission.py` | `:78〜87` の隣 | `orchestrator.campaign.s3_mocc_mutation_proof._build_variant` を NON_ADMISSIBLE で追加 (`_install_dependency` は旧 module のものを再利用するので追加不要) |
| `orchestrator/campaign/condition_meaning_gate.py` | `:201〜204` の隣 (DefineSpec)、`:267〜269` の隣 (witness) | `IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK` を `ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe", "patches/broken-mocc-hot-update-unlock.patch"` で、witness は `("cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK")` |
| `orchestrator/campaign/screening_driver.py` | `:80` の隣 | `"IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": 0` |
| `orchestrator/tests/test_condition_meaning_gate.py` | `:40` (`_COMPILE_TIME_BRANCH_MACROS`)、`:2685` (supply_domain) | macro を追加 (parametrize node が 1 つ増える。受入 ledger は未登録 node を 1 秒扱いなので追記不要) |
| `orchestrator/tests/test_ccbench_spawn_sites.py` | `:20〜28` import、`:62` の隣 (`_DIRECT_SAFE_ALLOWLIST`)、`:208` の隣 (`_run_checked` 型があれば)、`:4108〜4113` の隣 | 新 module の `_run_trace` を allowlist に (U は rr0)、FLAGS の holdout 判定を追加 |
| `orchestrator/tests/test_p3_build_authority_cli.py` | `:158〜170` `MANUAL_BUILD_FILES`、`:174〜189` `EXPECTED_NON_ADMISSIBLE` | 新 file / 新 materializer を追加 |
| `orchestrator/tests/test_p3_s4_loop.py` | `:7913〜7921` の隣 | `"patches/broken-mocc-hot-update-unlock.patch": frozenset({"IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK"})` |
| `patches/README.md` | `:575〜597` の mocc 負例節に隣接 | 新負例の説明 (親が docs-only で書く) |
| `output/env/pegasus/calibration/s3_mocc_mutation_proof.json` | 新規 | compute の生成物 (親が dispatch し受け取る) |

## 7. 並列分割方針と予算

- 段 2 plan 1 本 (read-only、`gpt-6-astra`、reasoning medium)。段 3 レンズ A = 正しさ境界・恒真性 (負例が沈黙すべき regime で沈黙するか、balanced 形の hang 条件、P3 の当否)、レンズ B = 過剰・削除 (DW-G05: scope 超え・仮想リスク向け機構の削除、P1 の再利用範囲、P6 の予算)。
- 段 5 author 1 本 (workspace-write、patch + driver + test + 登録簿 5 箇所を 1 子で。分割すると patch と driver の契約が割れる)。段 6 review 2 本 (A 正しさ、B 過剰・削除) + fix ≤ 3 巡。
- compute: 1 job (P6)。login: 生死確認 build 1 回、focus test、変異 matrix、受入全走。
