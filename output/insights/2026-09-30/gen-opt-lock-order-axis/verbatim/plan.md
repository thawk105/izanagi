# 段 2 実装プラン — silo-lock-order-policy

**判定: 条件付き GO。** 既存の policy-C++ v1 パーサーを profile 化して使う方針は妥当です。ただし、骨格の inert 性と、`W` 行から言える発火の範囲を実装・test で厳密に分ける必要があります。以下は静的検査に基づく計画です。**テスト、build、計算 job は実行していません。**

## 1. 所有と実装順

| 単位 | 変更・新規 file | 実装箇所 |
|---|---|---|
| A | `orchestrator/campaign/silo_policy_grammar.py`、新規 `axis_silo_lock_order.py`、`silo_lock_order_api.hh`、`silo_lock_order_compile.py`、`silo_lock_order_gate.py`、`silo_lock_order_hand/version_desc.cpp` | 文法 profile、API、単独 compile・UBSan、gate、手書き対照 |
| A | 新規 `orchestrator/tests/test_silo_lock_order_grammar.py`、`test_silo_lock_order_compile.py`、`test_silo_lock_order_gate.py` | 新軸の受理・拒否と既存受理集合の回帰 |
| B | 新規 `patches/silo-lock-order-variant.patch`、`orchestrator/tests/test_silo_lock_order_template.py` | CCBench の `cmake/Options.cmake` と `cc/silo/transaction.cc` に当てる単独骨格、inert・条件 build の test |
| B | `orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/tests/test_condition_meaning_gate.py` | `SILO_ORDER_VARIANT` の登録と固定 test |
| 親の統合 | `patches/README.md`、一次資料、spool fragment、必要なら `orchestrator/tests/README.md` | 追記だけ。A・B の実装所有には入れない |
| C | repo 外の約 100 行の使い捨て driver | A・B 統合後の生死確認 |

**A ∩ B の所有 path は空集合です。** A は文法・API・gate とその test、B は patch・意味登録とその test を所有します。新規 test に自走 harness を付けない場合は、親が `orchestrator/tests/README.md` の pytest 専用 allowlist に追記します。これを機械的に要求するのは [test_plain_runner_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_plain_runner_coverage.py:44) の `test_every_test_file_is_self_runnable_or_allowlisted` です。

## 2. A — 文法、API、compile、gate

### 文法の profile 化

[現行パーサー](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/silo_policy_grammar.py:57) の軸固有の直書きは次の全箇所です。

| 行 | 現在の直書き | profile へ移す内容 |
|---|---|---|
| 57–62 | `_TYPES`、API namespace、`_ENUMS`、`_FIELDS` | 型・列挙・field 表 |
| 151、173–175 | 名前・型の照合 | profile の型表を参照 |
| 205–207、239 | `PolicyState` の必須名 | `state_name` |
| 240–250 | 3 つの必須 hook と署名 | `required_hooks` |
| 254、267–269 | 返り値、参照引数、context 型 | 許可される返り値・引数型 |
| 347–350、406 | ローカル宣言に使える型・`izanagi_silo_api` | profile の宣言開始名・ローカル型 |
| 429–430 | 列挙の namespace | `api_namespace` と列挙表 |
| 458 | 代入不能な状態・context 型 | profile の複合型集合 |
| 502–512 | `LockResponse` の aggregate 特例 | 旧 profile 専用の aggregate 規則。新 profile では無効 |
| 513–523 | `std::min`・`std::max` | 外部関数表。両 profile とも同じ 2 名 |
| 548、555、558 | API namespace、状態 field、`LockResponse` 可変 field | profile の namespace・field・可変性 |
| 568 | 比較可能な列挙 | profile の列挙表 |
| 579–583 | `validate_policy` の parser 生成 | 既定 profile を渡す入口 |

字句、式の優先順位、literal の型と範囲、除算・shift 制限、深さ・個数制限、helper の先行定義規則は共有します。[`_lex` と構文処理](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/silo_policy_grammar.py:76) を複製しません。凍結した `FUNCTION_POLICY_PROFILE` を既定引数にし、既存の `validate_policy(source)` 呼び出しは同じ profile、同じ拒否順、同じ `rule_id` を通します。旧 corpus の manifest 全件で `(accepted, rule_id)` が一致することを回帰条件にします。

新 profile は `OrderState`、`izanagi_silo_order_api`、`izanagi_silo_order`、`AbortReason` の既存と同じ 8 値、次の context を登録します。

| 型 | field |
|---|---|
| `TxnContext` | `write_count: U32`, `rand: U64` |
| `EntryContext` | `epoch: U32`, `tid: U32`, `locked: bool` |
| `AbortContext` | `reason: AbortReason`, `rand: U64` |
| `CommitContext` | なし |

必須 hook は `order_enabled → bool/TxnContext`、`order_priority → U64/EntryContext`、`order_after_abort → void/AbortContext`、`order_on_commit → void/CommitContext` の各 1 定義です。外部関数は `std::min`・`std::max` だけです。`locked` は既存の `bool` 型として field 表に置き、`if (e.locked)` と `== true/false` を許します。数値演算へ暗黙変換せず、状態 field の可変性も与えません。[仕様 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md:182) の正例をそのまま受理 fixture にします。

### 新しく書くもの

- API header は [既存 header](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/silo_function_policy_api.hh:1) と同じ「骨格への埋め込み bytes の正本」にします。候補へ pointer、添字、key、handle を渡しません。
- `silo_lock_order_compile.py` は [既存 compile](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/silo_policy_compile.py:17) の `_run`、制限、診断の上限を再利用し、`API_HEADER` と [`_translation_unit`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/silo_policy_compile.py:95) の header・namespace、[`_HARNESS`・`_UB_CASES`・`run_ubsan_harness`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/silo_policy_compile.py:120) の hook 入力だけを新軸用に書きます。既存 module の CLI と 1904 calls の期待値は変えません。
- 新 harness は `epoch={0, UINT32_MAX}`、`tid={0, 2^29−1}`、`locked={false,true}` の直積を `order_priority` に渡します。`write_count` の 0・1・複数、8 種の `AbortReason`、commit と連続 abort、乱数の端も通します。`tid` の実幅は [Tidword](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/include/tuple.hh:12) の 29 bit です。負の UBSan 対照は新 context の field を用いて division by zero と overshift を維持し、期待 call 数は入力集合から計算します。
- `silo_lock_order_gate.py` に `order_gate(sub, implementation, auditor, *, compiler, scratch_dir, write, origin=None)` を作ります。[既存 `policy_gate`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/p3_s4_loop_policy.py:233) と同じく `quarantine(..., marker_id=axis.MARKER_ID, source_rel=axis.SOURCE_REL, write=False)` → 新 profile 文法 → 単独 compile → auditor veto → **全検査が通った後だけ write** の順にします。拒否 digest は新 axis ID を使い、`POLICY_GRAMMAR`・`POLICY_COMPILE` を再利用できます。
- [`p3_s4_loop.quarantine`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/p3_s4_loop.py:738) は marker と source path を既に引数で受け、構造検疫と [`coder_effect_gate.scan_host_effects`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/p3_s4_loop.py:803) を汎用で実行します。新 marker は backoff／trigger 専用分岐に入らないため、ここへの分岐追加は不要です。

## 3. B — 骨格 patch と build 意味登録

patch は pinned CCBench `68106660` に**単独適用**します。[関数方策 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/patches/silo-function-policy-variant.patch:1) の構造を借り、[sort patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/patches/silo-sort-variant.patch:34) が触る同じ sort 行を置換します。

1. `cmake/Options.cmake` の既存 CACHE 群付近へ `CCBENCH_SILO_ORDER_VARIANT 0 CACHE STRING ...`、`ccbench_universal_definitions` へ `SILO_ORDER_VARIANT=${CCBENCH_SILO_ORDER_VARIANT}` を追加します。他プロトコルには未使用 define だけが渡ります。
2. `transaction.cc` の file scope、既存 include の直後へ `#ifndef`・0/1 範囲の `#error`、ON 時の `NO_WAIT_LOCKING_IN_VALIDATION==1` と `NO_WAIT_OF_TICTOC==0` の `#error` を置きます。API BEGIN/END marker 内の bytes は新 header と一致させます。`namespace izanagi_silo_order` の 1 個の `EVOLVE-BLOCK` は `#if SILO_ORDER_VARIANT` の候補本体、`#else` の空 stock 枝という既存関数方策と同じ枠にします。既定本体は `OrderState {}`、`order_enabled=false`、`order_priority=0`、空の通知 hook とします。
3. hole の外に骨格 namespace を置き、`thread_local OrderState`、abort reason、乱数状態と seed、4 hook の `noipa` wrapper を置きます。乱数の初期化は [関数方策骨格](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/patches/silo-function-policy-variant.patch:74) の方法に合わせ、`begin()` で reason を `unset` に戻します。abort の通知は [`abort()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:27) で集合の clear より前に 1 回、commit の通知は [`commit()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:706) の `writePhase()` 後、`return true` 前に 1 回です。reason の代入点は関数方策 patch の abort site を移植します。
4. [`validationPhase` の 408 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:383) の `sort(write_set_.begin(), write_set_.end())` のみを条件化します。ON では `WriteElement` が継承する [`op_`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/include/op_element.hh:16) を全要素で見て、`OpType::INSERT` または `OpType::DELETE` があれば stock sort に戻し、決定用 2 hook は呼びません。通知 hook は引き続き呼びます。UPDATE のみなら `order_enabled` を 1 回呼び、true のときだけ各 `rcdptr_->tidword_.obj_` を 1 回 `loadAcquire` し、`epoch`・`tid`・`lock` の写しから優先度を得ます。固定配列相当の `(priority, 元の添字)` を、**priority 降順、`storage_` 昇順、`key_` 昇順**で並べて元の `write_set_` を順列として再配置します。[既存の pre/post sort の P 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:391) はその外に保ちます。
5. OFF 時には追加の宣言・wrapper・hook・条件本体をすべて前処理で消し、sort の stock 行を逐語で残します。したがって対象 owner TU の正規化後 bytes が stock と一致し、[`source_digest.resolve`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/source_digest.py:2467) は [`STOCK`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/source_digest.py:2307) を返す設計です。追加 include 行は置きません。[`assert_includes_match_head`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/source_digest.py:2160) と [`assert_trace_diff_matches_head`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/source_digest.py:2205) も通す必要があります。

[`condition_meaning_gate.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/condition_meaning_gate.py:82) には `SILO_ORDER_VARIANT` の `DefineSpec(ROUTE_CMAKE_CACHE, _SILO_OWNER, "ycsb_silo.exe", patch, inert_values=("0",))`、条件枝 witness、実 patch から数えた branch site 数を追記します。既存 test の [`_COMPILE_TIME_BRANCH_MACROS` と `_NEW_BRANCH_EXPECTATIONS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_condition_meaning_gate.py:47) にその 1 entry を加えます。[`RELATED_DEFINE_DECODE_MACROS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/condition_meaning_gate.py:675) は関連 define の復号専用で、新マクロを無根拠に足しません。

## 4. test と事前登録する変異

- 文法受理: 仕様 §4.4 の `locked`、版の合成、状態更新、`std::min` を含む正例、および `version_desc.cpp`。拒否: 仕様 §4.4 の表の**全群**、すなわち trace、counter・結果、集合・索引、tuple・要素、実行器・同期、sort、他軸・骨格 namespace の各名前。加えて pointer、配列、loop、handle 相当の独自名、マクロ、コメント、文字列、`__` 識別子を拒否します。
- 既存 4 軸: [`test_silo_policy_grammar.py` の manifest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_policy_grammar.py:20) と hand policies の判定一致、[`test_silo_policy_compile.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_policy_compile.py:31)、[`test_silo_policy_smoke_entry.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_policy_smoke_entry.py:1) を無変更で通します。backoff・sort・trigger-gating は既存の各 grammar/quarantine corpus を無変更で通し、変更前後の `(accepted, rule_id)` を比較します。
- patch: [既存 template test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_function_policy_template.py:37) と同じ pinned clone に厳密適用し、touch set、marker 1 個、API bytes、OFF の `resolve == STOCK`、ON の非 STOCK、include と TRACE 差分、INSERT/DELETE fallback、#error の各不正組合せを確認します。trace build と TRACE=0 build を作り、後者には [`_assert_no_trace_symbols`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/buildcache.py:3792) 相当の記号検査を掛けます。build は `tools/run_tests.py` 経由です。[spawn site 固定 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_ccbench_spawn_sites.py:149) の期待を無用に変更しません。
- 期待値には compiler version、digest、実行件数などの揮発値を焼き込まず、同じ実行で求めた基準と比較します。

変異は実装後に**単一理由性**を確認してから 1 個ずつ適用します。

| 変異 | 赤になるべき test |
|---|---|
| 文法許可表へ `write_set_` を追加 | `test_silo_lock_order_grammar.py::test_forbidden_name_groups` |
| INSERT/DELETE fallback を外す | `test_silo_lock_order_template.py::test_insert_delete_use_stock_sort_without_decision_hooks` |
| ON 時の前提 `#error` を外す | `test_silo_lock_order_template.py::test_required_build_flags_fail_closed` |
| priority 比較を昇順にする | `test_silo_lock_order_template.py::test_priority_descending_and_stock_tie_break` |
| OFF 時の wrapper を前処理に残す | `test_silo_lock_order_template.py::test_off_resolves_stock` |
| 文法・compile 前に書く | `test_silo_lock_order_gate.py::test_rejection_leaves_source_unchanged` |

## 5. C — 生死確認 driver

repo 外の使い捨て script が pinned clone を作り、骨格 patch を厳密適用し、A の `version_desc.cpp` を gate 経由で hole に入れます。本体は `order_enabled` が常に `true`、`order_priority` が `(uint64_t(epoch) << 29u) | tid`、通知 hook が空です。これは[仕様 §4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md:221) の名前つき対照です。

trace build と検証には既存の [`buildcache.build(..., trace=True)`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/pipeline.py:2085)、[`pipeline._run_trace`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/pipeline.py:429) と [`verify_trace_dir_with_capability` を使う検証経路](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/pipeline.py:626) を使います。既定の [`CorrectnessWorkload`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/pipeline.py:150) は 200 record、4 thread、1 秒です。結果は既存判定器の 1 回の verdict として記録し、新 D1/D2 による certified と呼びません。

発火は各 `trace_<thid>.log` の同一 txid の `W` 行から key の順を取り、UPDATE だけで 2 件以上の書きを持つ commit 取引について、stock の `(storage,key)` 順との相違を数えます。[`lockWriteSet` は write_set 順で INSERT を飛ばす](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:155) 一方、[`writePhase` の W は write_set 順](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:610)です。**W は成功して commit した取引の順序の証拠であり、abort した取引の施錠試行や `order_enabled` の呼出し総数は数えられません。** INSERT/DELETE を含む tx は fallback のため計数対象から除きます。`W` は key のみを出すので、複数 storage を含む取引の厳密な stock 順比較は別の証拠が要ります。YCSB の単一 storage に限定した計数であることを report に明記します。

起動 argv は `python3 tools/pegasus/dispatch_compute.py --task generic -- python3 /work/SFC/tanab/tmp/<作業名>-<日付>/liveness.py ...` の形です（[`generic` task と argv の区切り](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/tools/pegasus/dispatch_compute.py:4750)）。見積りは brief の 0.2〜0.3 node 時間、2 node 時間未満です。これは**予定値であり未測定**です。

## 6. provisional 裁定への判断

| 裁定 | 判断と根拠 |
|---|---|
| P1 | **賛成、条件付き。** profile 化は 600 行の複製を避けられます。ただし表以外にも状態名、必須署名、ローカル型、aggregate 特例が直書きされています（文法 205–269、347、502–558 行）。すべて profile へ移し、既定 profile の拒否順を固定します。 |
| P2 | **賛成。** `quarantine` は marker/source を引数にし、構造検疫・効果 gate を共通実行します（738–805 行）。新軸の文法・compile は別 gate に置けます。 |
| P3 | **賛成。** sort patch は同じ sort 1 行を置換します（sort patch 34–63 行）。関数方策 patch も同じ `transaction.cc` を広く編集します。単独適用を axis 定数、README、template test に記します。 |
| P4 | **限定して賛成。** W 行と lock loop は同じ `write_set_` 順です（transaction.cc 155–158、610–615 行）。ただし W は commit 分だけで、INSERT は施錠されず、storage は W に出ません。上記の対象限定を report と計数器に入れます。 |
| P5 | **賛成。** `DefineSpec`、branch witness、site count、固定 test への 1 entry 追加が必要です（condition_meaning_gate 104、436、597 行、test 47・116・1253 行）。site count は完成 patch から決めます。 |
| P6 | **賛成。** [既存 hand directory](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/axis_silo_function_policy.py:27) と同じ構造で、新 directory を軸ごとに所有できます。 |

## 総括

- **GO:** A・B を上記の素集合 ownership で実装し、静的契約と test を通してから統合する。
- **GO の条件:** OFF の `source_digest.resolve == STOCK`、新旧文法 corpus の一致、ON の build 前提、UPDATE 限定の sort、TRACE=0 記号検査を受入条件にする。
- **未決事項:** W 行による発火数は「単一 storage の、commit した UPDATE だけの取引」の証拠に限る。生死確認 report でその範囲と、abort 試行を数えられない限界を明記する。
- **未実施:** 本段は read-only の静的検査のみ。テスト、build、dispatch、実測は行っていない。