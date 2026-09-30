# 段 4 裁定 — dev-wave-lock-order-axis ([T-2886])

入力: brief.md、plan.md (段 2、条件付き GO)、consult-a.md (レンズ A 正しさ境界、NO-GO: must 2・should 4)、consult-b.md (レンズ B 実効性・過剰、NO-GO: must 2・should 3・nit 1)。段 4 直前に裁定 inbox (/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox) を再走査し、wave 開始後の更新は 0 件。local main は 4f412c67b のまま。

## 所見の裁定

| # | 所見 | 裁定 | 採否・対応 |
|---|---|---|---|
| A1 | 禁止名が参照では拒否されるが宣言名 (状態 field・局所変数・helper・引数・constexpr) としては通る | real (現行 parser の `name()` は型名と keyword 以外を許す) | 採用。新 profile にだけ「禁止識別子集合」を持たせ、**すべての宣言位置と参照位置**で照合して拒否する。既存 profile では空集合 (既存受理集合を変えない)。禁止集合 = 仕様 §4.4 の拒否表の全名 + この軸の骨格 namespace 名 + `TRACE`。 |
| A2 | 文法変異「許可表へ write_set_ を追加」は照準が外れる | real | 採用。変異 M1 を「A1 の宣言位置検査を外す」に再照準 (下表)。 |
| A3 | `#error` が未定義マクロを 0 と評価して通す | real (既存 patch は defined と値の両方を見る) | 採用。`SILO_ORDER_VARIANT` の未定義・範囲外、ON 時の `NO_WAIT_LOCKING_IN_VALIDATION`・`NO_WAIT_OF_TICTOC` の未定義と不正値をそれぞれ `#error`。 |
| A4 | 単独 compile 合格と骨格込み build 合格の区別 | real | 採用。gate の合格は「検疫・文法・単独 compile の合格」と呼ぶ。実 build の成否は生死確認で別に記録する。 |
| A5 / B4 | UBSan harness の適用先が曖昧 | real | 採用。既存の関数方策の軸と同じく **候補ごとの gate には入れない**。手書き対照と test 用の別入口 (`run_ubsan_harness` 相当) とし、brief の完了判定からも「(+UBSan)」を外して「手書き対照が UBSan harness を通る」を別に書く。 |
| A6 | 本 wave の保証範囲を固定する | real | 採用。一次資料と fragment に「gate 関数と対照を成立させた。全候補への強制配線 (U5 [T-2888])・D1/D2 照合 (md_14)・certified 判定はこの wave では無い」と書く。 |
| B1 | 発火計数が仕様 §4.3 の 2 件数のうち片方 (commit 済み UPDATE のみ・単一 storage の W 順) だけ | real | 採用。生死確認では W 由来の件数を「commit した UPDATE だけの取引で、key 順と違う順に施錠した取引の数 (YCSB 単一 storage)」と限定して記す。「並べ替えを使った取引の数」は計数 build が要るので [T-2896] の評価前の前提として worklog に持ち越す (本 wave では作らない)。 |
| B2 | 生死確認 driver が既存 build・検証経路を ~100 行で呼べる前提が未成立 | real (buildcache.build は admission・build_context・source_evidence 必須) | 採用。本番 campaign 経路 (run_campaign) は使わない。先例 `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/launch_gate_liveness.py` (repo の部品を import し node-local checkout に patch を当て直 CMake で build、判定器 CLI を --expected-commits と --ccbench-root で呼ぶ) を雛形に単位 C を Codex author が書く。判定器 rc 0/1/3 は判定結果として扱う。 |
| B3 | profile 化の範囲が広い | real (一部) | 採用。profile 化は軸固有の直書き箇所だけに限り、字句・式・literal・制限は触らない。既存の文法 test corpus 全件と hand policy の `(accepted, rule_id)` を変更前後で一致させる回帰 test を置く。 |
| B5 | test 所要 | real | 採用。pinned clone + patch 適用は新 template test 全体で 1 回の fixture に集約する (module scope)。バイナリ全体の build は test に入れない。TRACE=0・variant=0 の同一性は `source_digest.resolve == STOCK` (前処理後 bytes) で示す (同一 bytes → 同一命令列)。variant=1 の性能 build の trace 記号検査は生死確認 job で行う。骨格の並べ替えの挙動は、骨格の並べ替え部分を marker で区切った自己完結の関数にし、test がその区間を切り出して mock の要素型で小さく compile・実行する (1 回の g++ で数秒)。 |
| B6 | 共有登録簿の衝突面 | real (nit) | 採用。condition_meaning_gate.py と test_condition_meaning_gate.py は追記だけ。新 test は既存と同じ自走 `_run` を持たせ README allowlist を使わない。 |
| P1〜P6 | 親の provisional | P1 採用 (B3 の限定付き)、P2 採用 (p3_s4_loop.quarantine は無変更)、P3 採用、P4 は B1 の限定付きで採用、P5 採用、P6 採用 (置き場 `orchestrator/campaign/silo_lock_order_hand/`) |

## プラン v2 (確定)

名前: 軸 ID・marker ID = `silo-lock-order-policy`、flag = `SILO_ORDER_VARIANT`、API namespace `izanagi_silo_order_api`、hole namespace `izanagi_silo_order`、骨格 namespace `izanagi_silo_order_skel`、patch `patches/silo-lock-order-variant.patch`、API header `orchestrator/campaign/silo_lock_order_api.hh`、hand dir `orchestrator/campaign/silo_lock_order_hand/` (名前つき対照 `version_desc.cpp`)。

**単位 A (Codex author、所有):** `orchestrator/campaign/silo_policy_grammar.py` (profile 化、既定 profile で既存挙動不変、新 profile + 禁止識別子集合)、新規 `axis_silo_lock_order.py` (定数・排他 patch の名を明記)、`silo_lock_order_api.hh`、`silo_lock_order_compile.py` (単独 compile と UBSan harness。既存 `silo_policy_compile.py` の関数を import して使い、既存 file は変えない。新しい subprocess 起動箇所を作るなら test_ccbench_spawn_sites.py の固定表への 1 entry 追記を許す)、`silo_lock_order_gate.py` (`order_gate`: quarantine(write=False) → 新 profile 文法 → 単独 compile → auditor veto (auditor が None でなければ) → 全検査後にだけ write。policy_gate と同形)、`silo_lock_order_hand/version_desc.cpp`、新規 test `orchestrator/tests/test_silo_lock_order_grammar.py`・`test_silo_lock_order_compile.py`・`test_silo_lock_order_gate.py` (自走 `_run` 付き)。

**単位 B (Codex author、所有):** `patches/silo-lock-order-variant.patch` (pin 68106660 に単独厳密適用。Options.cmake の CACHE と universal definitions、transaction.cc の #error 群・API 埋め込み (BEGIN/END marker、header と bytes 一致)・EVOLVE-BLOCK (既定本体: `order_enabled` false、`order_priority` 0、通知 hook 空)・骨格 namespace (thread_local 状態・乱数・noipa wrapper)・validationPhase の sort 1 行の条件化 (UPDATE だけなら hook、INSERT/DELETE を含めば stock sort で順序 hook 不呼出し、TID word は 1 要素 1 回 loadAcquire、(prio 降順, storage_ 昇順, key_ 昇順) で添字を並べ替え順列として再配置、並べ替え部分は marker で区切った自己完結の関数)・abort と commit の通知 hook・abort reason の代入点)、`orchestrator/campaign/condition_meaning_gate.py` (SILO_ORDER_VARIANT の DefineSpec inert_values=("0",)・branch witness・site count を追記)、`orchestrator/tests/test_condition_meaning_gate.py` (該当の固定表へ新 entry を追記するだけ)、新規 `orchestrator/tests/test_silo_lock_order_template.py` (clone 1 回の fixture、touch set、marker 1 個、API bytes 一致、OFF の resolve == STOCK と include/trace 差分の検査、ON の非 STOCK、#error 各組合せ (前処理で確認)、並べ替え関数の mock compile による挙動 test)。

**単位 C (Codex author、repo 外):** `/work/SFC/tanab/tmp/lock-order-2026-09-30/launch_lock_order_liveness.py`。A・B 統合 commit を載せた checkout で、pinned clone → 骨格 patch 厳密適用 → `order_gate` で version_desc.cpp を hole へ (auditor None・origin='initial' 相当は使わず write を許す経路を確認して使う) → TRACE=1・SILO_ORDER_VARIANT=1 の ycsb_silo.exe を直 CMake で build → CorrectnessWorkload 相当 (200 record・zipf 0.9・rratio 50・max_ope 5・4 thread・1 s、RMW あり / なしの 2 run) → 判定器 CLI → W 行から発火計数 (B1 の限定) → 同じ hole で TRACE=0・SILO_ORDER_VARIANT=1 を build し `buildcache._assert_no_trace_symbols` 相当の記号検査。結果 JSON に host・時刻・pin・patch と source と binary の sha256・commit/abort・判定器 JSON・発火計数・各段の所要を書く。起動は `tools/pegasus/dispatch_compute.py --task generic`、1 job、walltime 30 分、見積り 0.1 node 時間。

## 不変条件 (実装子への契約)

- 既存 test の期待値を変えない。例外は **追記だけ** の次の 2 か所: test_condition_meaning_gate.py の SILO_ORDER_VARIANT の新 entry、(新しい起動箇所を作った場合だけ) test_ccbench_spawn_sites.py の新 entry。それ以外の既存 test が赤なら実装側が誤り。
- 既存 4 軸の受理集合を変えない。p3_s4_loop.py・p3_s4_loop_policy.py・silo_policy_compile.py・silo_policy_contrast*.py・diff_quarantine.py・coder_effect_gate.py・codex_roles/ は編集しない。
- 規模上限: 単位 A の production 追加・変更 700 行以内、単位 B の patch 300 行以内 (test は別)。超えたら理由を報告。

## 変異の事前登録 (DW-M01。実装後に単一理由性を確認し、成立しなければ登録を外して再照準する)

| id | 位置 | 変異 | category | 赤になるべき test |
|---|---|---|---|---|
| M1 | silo_policy_grammar.py の新 profile 禁止識別子の宣言位置検査 | 検査を外す | positive | test_silo_lock_order_grammar.py の「禁止名を状態 field・局所変数・helper 名に宣言した候補の拒否」 |
| M2 | patch の並べ替え関数の INSERT/DELETE 判定 | 判定を外す (常に候補順) | positive | test_silo_lock_order_template.py の並べ替え挙動 test (INSERT/DELETE を含む集合で stock 順・順序 hook 呼出し 0) |
| M3 | patch の ON 時 `#error` (NO_WAIT_OF_TICTOC の未定義検査) | 外す | positive | test_silo_lock_order_template.py の #error 組合せ test |
| M4 | patch の並べ替え比較 | priority を昇順にする | positive | test_silo_lock_order_template.py の降順・tie-break test |
| M5 | silo_lock_order_gate.py | 文法検査より前に write する | positive | test_silo_lock_order_gate.py の「拒否時に source 不変」 |
| M6 | patch の OFF 枝 | OFF でも骨格 namespace の宣言 1 つを前処理に残す | positive | test_silo_lock_order_template.py の OFF resolve == STOCK |

patch の変異は superproject tracked の patch file を harness の対象にする (submodule 内は変異できない)。
