## 0. 要約

- **条件付き採用案:** Silo の abort 後待機と lock 競合応答を、単一 EVOLVE-BLOCK 内の複数関数として合成する。
- CAS・unlock・validation・tid 生成・writePhase・trace・同一 txn の再試行は骨格に残す。
- P4 の include 前封じ込め案は成立しない。後置領域と限定した関数・状態契約を採る。
- P2 の「原理的に壊せない」「verifier による拒否は必ずゼロ」は撤回する。自由な C++ の UB まで排除した証拠はない。
- P5 は縮小する。時刻・set サイズ・共有 atomic は v1 から外し、自前状態も txn 内に限定する。
- planner-v4 は外す。coder → 検疫 → auditor → admission → pipeline → critic の兄弟 driver とする。
- IR 内の同一空間比較と、LLM の C++ 空間拡張を評価する比較は分ける。
- 以下は静的確認に基づく設計草稿。実装・build・pytest・計算投入は行っていない。

以下の `T:L` は `external/ccbench/cc/silo/transaction.cc:L`、`O/L` は `orchestrator/campaign/L`、`V/L` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-silo-function-synthesis-space/verbatim/L` を表す。repo 相対パスはすべて指定 worktree 配下である。「案」は新規設計であり、既存実装の主張ではない。

## 1. 境界と骨格

### 1.1 実コードから決める境界

| 箇所 | 現行動作と根拠 | v1 の設計案 |
|---|---|---|
| `abort()` | INSERT の撤去、GC、read/write/node 集合の clear 後、`BACK_OFF` 時に待つ。`T:27`, `T:38`, `T:42` | cleanup は固定。既存待機呼出しを方策の返す待機量に置換する |
| `lockWriteSet()` | `expected.lock` 時は既定で status=aborted、取得済み prefix を unlock、return。CAS 成功時に `record_lock`。`T:160`, `T:172`, `T:179` | 競合時に「有限待機して再読込」または「abort」を選べる |
| `validationPhase()` | sort、lock、epoch 公開、read 版・他者 lock・node 版の検査。`T:408`, `T:437`, `T:441`, `T:453`, `T:466`, `T:478` | 判定・集合・走査・unlock は開かない |
| `writePhase()` | commit tid、trace、被覆検査、データ更新、unlock、retention 検査。`T:557`, `T:601`, `T:624`, `T:640` | 開かない。成功時の方策専用状態リセットだけを軸 ON の骨格として追加 |
| YCSB 再試行 | `makeProcedure` は RETRY より前。abort 後は同じ手順を再試行し、RETRY 冒頭で quit を確認。`include/ycsb.hh:102`, `:108`, `:149`, `:161` | 変更しない。方策は txn の破棄・再生成・commit 計数を操作できない |
| stock backoff | `rdtscp` と `_mm_pause` による busy wait。適応更新は commit 数を使用。`include/backoff.hh:44`, `:94`, `:111` | 待機実行・時計換算は骨格。既存適応方式は外部対照として保存 |

**validation の仕組みは v1 に含めず、lock 取得の競合応答だけを含める。** これなら関数合成・複数 hook・状態付き応答を試せ、CC の検査手順そのものの再設計を同時に抱えない。ただし、これは契約に従う方策についての議論である。任意 C++ の UB や外部状態への干渉まで含めて「直列化可能性を構成上壊せない」とは言えない。D41 の comparator に関する誤った安全論拠を繰り返さない。根拠: `V/D41.md:25`、`O/coder_effect_gate.py:576`。

**lock 待機には再読込が必須。** 現行 `expected.lock` 枝には値の再取得がない。待機だけを挿入すると、既に解放された lock でも古い `expected` を見続ける。待機後に `loadAcquire` し直す。CAS 失敗の連続も含め、内側ループの全周回を骨格の上限対象とする。根拠: `T:158`–`T:184`。

### 1.2 関数・状態・呼出し点の案

v1 の公開型・署名を次とする。型と署名の宣言は骨格、実装・補助関数・専用状態型は hole に置く。

```cpp
enum class PolicyAction : uint32_t { retry, abort };
enum class PolicyAbortReason : uint32_t {
  unset, lock_conflict, update_absent, read_tid, read_locked, node_validation
};
struct AbortContext {
  PolicyAbortReason reason;
};
struct LockContext {
  uint32_t attempt;
};
struct LockResponse {
  PolicyAction action;
  uint32_t wait_us;
};

uint32_t policy_after_abort(AbortContext) noexcept;
LockResponse policy_on_lock_conflict(LockContext) noexcept;
```

設計契約は以下とする。

- `policy_after_abort` は cleanup 完了後に呼ぶ。要因は発生点で骨格が記録し、`begin()` で unset に戻す。既存 trigger の要因契約を参考にするが、その軸の marker や gate は再利用しない。根拠: `T:27`, `T:55`、`V/D48.md:21`。
- `policy_on_lock_conflict` は `expected.lock` 枝から呼ぶ。返値で直接 CAS・unlock しない。取得済み prefix の解放と status 設定は骨格が行う。根拠: `T:160`。
- hole は `PolicyState` という集約型と `thread_local PolicyState policy_state{}` を定義できる。メンバは bool／固定幅 unsigned のみ、定数初期化、独自 constructor/destructor・pointer・参照メンバは禁止する案。
- 状態の寿命は **同一 txn の試行列内**。`begin()` では消さず、`writePhase()` 成功末尾で `PolicyState{}` を代入する。YCSB は abort 後同じ txn を再試行するため、この位置が区切りになる。根拠: `include/ycsb.hh:102`, `:155`, `:164`, `T:694`。
- namespace scope の共有 atomic と txn をまたぐ履歴は v1 では見送る。状態を持つだけでも retry の代理信号を作れるため、後述の P5 裁定対象は残る。

待機上限の**試走用案**は abort 1 回 1,000 µs、lock 1 回 50 µs、内側ループ 32 周回。最適値ではなく有限化の設計値であり、全生成器に同一条件で公開する。返値を上限へ clamp し、不正な action は abort。時計換算は乗算 overflow を避けて骨格で行う。

この上限は **hook が戻る場合の待機・再試行上限**であり、任意 C++ 関数自身の停止を保証しない。停止保証を主張できるのは §4 の IR 部分空間に限る。

### 1.3 P4 の include 可視性

include の追加・順序変更は禁止のままである。`assert_includes_match_head` は include 行を順序込みで比較し、identity の前処理は include を除去する。根拠: `O/source_digest.py:1933`, `:2160`, `:1686`。

| `transaction.cc` の配置位置 | 確認できた可視性 |
|---|---|
| L1 `stdio.h` 後 | 指定された CC 識別子の宣言はまだない。`uint64_t` 等の処理系依存の間接公開は未確認 |
| L2 `algorithm` 後 | 同上。`std::atomic` の正規ヘッダはまだ読んでいない |
| L3 `string` 後、L5 より前 | CC 固有大域は未宣言だが、要求する `std::atomic`・`rdtscp` を揃えられない |
| L5 `atomic_tool.hh` 後 | `std::atomic`、`uint64_t`、`rdtscp`、epoch 系、`CCBenchResults`、複数の `FLAGS_*` が既に見える |
| L6 `log.hh` 後 | 上記を保持。P4 の封じ込めにはならない |
| L7 `transaction.hh` 後 | 上記に加え `Masstrees` と TxExecutor 周辺 API が見える |
| L8 `scan_callback.hh` 後 | この問題について新しい隔離境界はない |
| L9 `trace.hh` 後 | TRACE=1 では `izanagi_trace` が見える。TRACE=0 ではその namespace ごと消える |

L5 の根拠となる include 経路は次のとおり。

- `atomic_tool.hh:3` → `common.hh:4` で `<atomic>`。
- `common.hh:8` → `tuple.hh:7` で `<cstdint>`。
- `tuple.hh:10` → `tuple_body.hh:14` → `util.hh:31` の `result.hh`、`:32` の `tsc.hh`。
- `result.hh:258` に `CCBenchResults`、`tsc.hh:27` に `rdtscp`。
- `common.hh:25`, `:50`, `:69` に epoch・FLAGS・関連大域。
- `transaction.hh:7`, `:15` → `workload.hh:37` に `Masstrees`。
- `trace.hh:25`, `:35` に TRACE ガードと namespace。

したがって、**P4 の必要 API と大域非可視性を同時に満たす include 間の隙間は確認できない**。標準ライブラリ・外部依存ヘッダが追加で公開する全識別子の網羅性は未確認だが、P4 を否定するには上記の既知経路で足りる。

| 代案 | 費用・限界 | 判定 |
|---|---|---|
| L5 より前、組込み整数型のみで実装 | atomic・時計を方策から外せる。既存 libc や compiler builtin まで消えず、完全な隔離にはならない | 補助案 |
| L9 後、専用 namespace＋構文・識別子契約 | include／ALLOWLIST 拡張不要。既存 effect gate に軸固有の宣言・参照契約を接続する必要あり | **採用案** |
| 別 TU | header/build 配線、source identity、ALLOWLIST の変更が必要。別 TU 自体もプロセス隔離ではない | v1 見送り |

namespace や `extern` 禁止だけを防壁と呼ばない。後置案では、CC 大域・FLAGS・TRACE・時計・pointer 操作・外部呼出し・namespace 脱出を禁止し、許可された型／専用状態／局所宣言／補助関数への参照を検疫する。単なる禁止識別子 grep が C++ の意味保証になるとは主張しない。根拠: `V/D127.md:3`, `:38`、`O/coder_effect_gate.py:592`。

### 1.4 骨格 patch の擬似差分

以下は**未実装の構造図**であり、そのまま apply する差分ではない。

```diff
 cmake/Options.cmake:
+set(CCBENCH_SILO_POLICY_VARIANT 0 CACHE STRING "Silo function policy")
 ccbench_universal_definitions():
+  SILO_POLICY_VARIANT=${CCBENCH_SILO_POLICY_VARIANT}

 transaction.cc: 既存 include 列の後
+#ifndef SILO_POLICY_VARIANT
+#error "SILO_POLICY_VARIANT must be defined"
+#endif
+#if SILO_POLICY_VARIANT != 0 && SILO_POLICY_VARIANT != 1
+#error "SILO_POLICY_VARIANT must be 0 or 1"
+#endif
+#if SILO_POLICY_VARIANT
+namespace izanagi_silo_policy {
+  [固定 Context / Response 型、関数宣言]
+}
+#endif
+
+// EVOLVE-BLOCK-BEGIN silo-function-policy
+#if SILO_POLICY_VARIANT
+namespace izanagi_silo_policy {
+  [PolicyState、thread_local 状態、補助関数、2 関数の定義]
+}
+#else
+#endif
+// EVOLVE-BLOCK-END silo-function-policy
+
+#if SILO_POLICY_VARIANT
+  [固定の要因状態、上限付き待機関数]
+#endif

 abort(): cleanup 後
-  Backoff::backoff(FLAGS_clocks_per_us);
+#if SILO_POLICY_VARIANT
+  bounded_wait(policy_after_abort(snapshot), FLAGS_clocks_per_us);
+#else
+  Backoff::backoff(FLAGS_clocks_per_us);
+#endif

 lockWriteSet(): expected.lock 枝
+#if SILO_POLICY_VARIANT
+  [全周回上限を超えたら status=aborted、prefix unlock、return]
+  [hook が abort を返しても同じ処理]
+  [上限付き待機]
+  expected.obj_ = loadAcquire((*itr).rcdptr_->tidword_.obj_);
+#else
   [現行 NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC 枝を逐語保存]
+#endif

 begin() / abort 要因発生点 / writePhase() 成功末尾:
+#if SILO_POLICY_VARIANT
+  [要因リセット／要因記録／専用状態リセット]
+#endif
```

既存 `BACK_OFF` の外側条件と `ADD_ANALYSIS` の計数は保持し、新軸 `_BASE` は `BACK_OFF=1` を明示する。stock の exact 対照は軸 OFF の別 genome として扱う。軸 ON 時の lock 応答は既存 no-wait 枝に優先するが、その差を genome の新軸フラグで明示する。根拠: `T:42`、`Options.cmake:20`, `:27`、`docs/axis-onboarding.md:195`。

**TRACE 行を新しい `#else` 内へ巻き込まない。** CAS 成功・被覆・retention の既存 TRACE ブロックは共通骨格として同じ場所に残す。そうしないと diff-of-diffs の既存差分内容を変え得る。根拠: `O/source_digest.py:2182`。

### 1.5 parser・検疫への適合

依頼文の関数所在地には訂正がある。**`parse_template_file` は `diff_quarantine.py:567` にある。** `evolve_block.py` は `extract_materialized_evolve_block` を提供する。根拠: `O/evolve_block.py:23`。

- **namespace scope:** 両 parser は C++ scope を解析しないため、構造上は扱える。C++ の妥当性や namespace 脱出の禁止は別の構文契約で担う。
- **空の stock 枝:** `else_line < endif_line` を満たせばよく、両 parser とも stock 本文の非空を要求しない。根拠: `O/diff_quarantine.py:635`、`O/evolve_block.py:54`。
- **複数行 hole:** `render_hole` は行列の slice を置換するため対応済み。docstring の「現テンプレは単一行」は実装制限ではない。根拠: `O/p3_s4_loop.py:693`。
- **2 呼出し点:** 呼出し点は marker 外の固定骨格なので、複数 marker 対応は不要。
- **単一 marker の限界:** `quarantine` は単一 `marker_id/source_rel`、`DiffQuarantine` は単一 hole にしか変更を許さない。`evolve_block.py:38` は対象 marker 対の一意性を確認する。一方 `parse_template_file` は最初の対を拾って終了し、同じ強さの全体一意性検査ではない。根拠: `O/diff_quarantine.py:599`, `:632`。
- **必要変更:** 新軸定数、新 marker の構文契約分岐、proposal schema、driver の identity／feedback 接続。多 marker 汎用化は不要。新骨格について marker 一意性・空 stock・複数関数・呼出し点不変の焦点検査を追加する。

hole に `//`・`/*`・`*/`・前処理指令・行末 backslash・BEGIN/END marker 文字列は入れない。説明は JSON の justification に出す。文字列中でも保守的に拒否されるため、コード内文書や埋込み C++ は使えない。根拠: `O/diff_quarantine.py:57`, `:64`, `:479`。

`MAX_HOLE_BYTES=256 KiB`、`MAX_HOLE_TOKENS=4096` は **関数ごとでなく領域全体**の上限。token は LLM token ではなく独自 lexer の token である。短い複数関数には使えるが、停止・状態サイズ・計算量の保証ではない。上限を増やす必要は現時点でない。根拠: `O/coder_effect_gate.py:114`, `:576`。

### 1.6 D38 の適用

`record_lock` は CAS 成功時だけ、`clear_shadow` は取得開始・全／部分 unlock・成功末尾に存在する。待機中に shadow を消さず、abort 時は既存 prefix unlock を通す。根拠: `T:152`, `T:179`, `T:363`, `T:379`, `T:695`。

`test_lock_path_edit_surface_requires_auditor_live` は、transaction.cc が編集面にある場合に既存 `s3_lock_coverage.json` の `all_pass` を要求する。**新方策を実走監査するテストではない。** 既存 gate を維持したうえで、新骨格に既存 lockskip／early-unlock 負例を重ねて検出力を確認する。根拠: `orchestrator/tests/test_campaign.py:11423`。

## 2. verifier・trace・変異検査

### 2.1 観測者効果の分離

方策状態・要因記録・待機処理は TRACE に依存せず両 build に存在させる。そのコストは性能側にも載る。trace・被覆検査は従来どおり compile 時除去する。`pipeline` は trace/perf を別々に build する。根拠: `O/pipeline.py:2016`、`T:584`、`include/trace.hh:25`。

既存 diff-of-diffs を弱めず使う。新しい TRACE 計装を足す場合は、out-of-band 骨格 patch だけでは pinned HEAD と不一致になるため、既存オンボーディングどおり信頼済み計装の commit／PIN 前進が必要になる。v1 の主案は既存 X/P/C/R/W/E を保存し、追加 trace は要求しない。根拠: `O/source_digest.py:2227`、`docs/axis-onboarding.md:138`。

ただし **compile 時除去は trace/perf の実行軌跡一致を保証しない**。時間依存・競合依存の方策は計装の遅延で判断が変わり得る。P5 の時計非公開はこの問題を縮めるが解消しない。

### 2.2 verify 構成

- legacy: 200 records、4 threads、RMW、有効時間 1 秒。`O/pipeline.py:147`
- S2: 1M records、48 threads、read 比率 50%、non-RMW、3 秒。`O/pipeline.py:159`
- performance verify: `PerfConfig` と同じ records／threads／workload／extime、同じ reps を構築できる。`O/pipeline.py:193`

配線段階では legacy＋S2。手法比較では **legacy＋実際の性能 workload の verify** を全 arm に適用する。write-heavy／read-heavy を S2 の balanced 設定だけで代表させない。既存二相のどちらかを省く設計ではない。根拠: `O/pipeline.py:1642`。

abort 数は `verify_done` に残り、欠落は reject になるが、**abort=0 を一律拒否する条件はない**。さらに abort>0 は lock hook が踏まれた証拠にはならない。次 wave の焦点実走で abort hook と lock conflict hook を別々に踏ませる。根拠: `O/pipeline.py:591`, `:633`、`.claude/agents/critic.md:20`。

### 2.3 正例と負例

| 区分 | 対照案 | 期待する検出・用途 |
|---|---|---|
| 正例 | 軸 OFF の inert 骨格 | stock source token、既存 trace 差分一致 |
| 正例 | 無待機＋即 abort、有限固定待機、上限内 retry | build／verify 緑。hook が動いた証拠を別に確認 |
| 骨格負例 | read 版検査を無効化 | `broken-silo-norw-validation.patch:9` の型。競合 workload で G2、`non-serializable` |
| 骨格負例 | CAS 取得を skip | `broken-silo-lockskip-validation.patch:9`。X `not-locked-at-entry`、`indeterminate` |
| 骨格負例 | 書込み前 unlock | `broken-silo-early-unlock-validation.patch:9`。X `lock-lost-before-write` |
| 骨格負例 | sort 後の要素消失 | `broken-silo-permutation-erase.patch:9`。P `size-changed` |
| 骨格負例 | hook 配線解除、待機後の再読込削除 | 焦点試験で期待応答不成立／timeout。G2 検出とは別の配線検査 |
| 方策負例 | 禁止識別子、namespace 脱出、marker・コメント混入 | build 前の検疫拒否 |
| 方策負例 | 不正署名・型不整合 | 構文検疫または `build-error` |
| 方策負例 | 上限超の待機要求 | clamp されて戻る**境界正例**。必ず reject になるとはしない |
| 方策負例 | 非停止 helper、UB | 既存 effect veto／auditor、漏れたものは timeout・異常終了等。ただし必ず検出できるとはしない |
| 方策負例 | 特定の試行列を恒常的に不利にする | serializable のまま通り得る。fairness の死角として記録 |

sort の non-SWO 負例は **旧軸の UB 検出例**であり、新方策の代表負例にはしない。`patches/broken-silo-sort-nonswo.patch:26` は comparator 固有の問題である。

要因記録を採るなら、誤 attribution が G2 では見えない点を明記する。既存 `broken-silo-trigger-misattr.patch:9` もその区別をしている。v1 では焦点試験で全記録点と unset を検査し、要因頻度を新しい認証条件へ昇格させない。

変異は位置・期待する赤理由・期待 node を事前登録する。compile failure だけで G2 検出力を証明したことにせず、等価変異や他 gate による mask を分ける。根拠: `docs/dev-wave/mutation.md:5`, `:16`, `:22`, `:55`。

### 2.4 現行 reject 理由

| 事象 | 現行の帰結と根拠 |
|---|---|
| compile/configure 失敗 | `build-error`。`O/pipeline.py:2024` |
| trace run が crash／非ゼロ終了 | `trace-run-nonzero-exit`。`:579` |
| trace run の hang | 既定 120 秒で `trace-timeout`。`:357`, `:525` |
| 正常終了したが commit C 行ゼロ | `trace-empty`。`:585` |
| abort 集計欠落 | `trace-no-abort-counts`。`:591` |
| commit witness 欠落 | `trace-no-commit-witness`。`:598` |
| trace parse 不能 | `trace-parse-error`。`:626` |
| verifier 赤 | verdict 自体が reason。`non-serializable`／`indeterminate` 等。`:655` |
| 性能側に usable throughput がない | `bench-no-throughput`。`:1441` |
| 一部 worker だけ commit 枯渇 | 全体の C 行があれば `trace-empty` にはならない。`:585` |

新しい timeout／fairness／率の threshold gate は作らない。置換対象は、新軸の hole 構文契約、proposal、identity 接続、既存 auditor・feedback の軸適用部分に絞る。

## 3. 既存 driver と coder role への接続

### 3.1 実装順

**専用 LLM driver の先行実装はしない。** 次 wave は既存 evaluator と最小 driver で手書き方策の生死を確認する。DW-G01 は既存 driver または 100 行以内の使い捨て driver を要求する。根拠: `docs/dev-wave/core.md:60`。

順序案は、最小骨格＋手書き対照 → C の検査 → IR 偵察 D → 生存判断 → 兄弟 driver／coder E → 実 LLM F。C の軸定数は E から独立させる。根拠: `docs/axis-onboarding.md:24`, `:33`, `:164`。

### 3.2 兄弟 driver

`p3_s4_loop_policy.py` と `axis_silo_policy.py` を新設する案。

再利用するもの:

- `quarantine` の行単位検疫・effect veto。`O/p3_s4_loop.py:716`
- `record_diff_reject`、WAL、stop／checkpoint の既存機構。`:961`
- `make_critic_digest(..., reflux=True)`。`:1164`
- `auditor_gate` の digest 照合・reject／uncertain veto。`O/auditor_gate.py:132`
- `pipeline.evaluate` による build→verify→bench→terminal の経路。

そのまま転用しないもの:

- sort の 79 値 IR admission／SWO oracle。現行 sort は raw C++ 自由合成ではない。`O/p3_s4_loop.py:830`、`.claude/agents/coder-v4-autonomous-sort.md:59`
- trigger の 5-bit wire／正準述語 binding。`.claude/agents/coder-v4-autonomous-trigger-gating.md:72`
- B-4／8c 固有分岐。共通関数にも `base/sort/trigger` の閉じた分岐があるので、新軸を暗黙に混ぜない。`O/p3_s4_loop.py:554`

proposal 案:

```json
{
  "schema": "silo-function-policy/v1",
  "coder": {
    "axis": "silo-function-policy",
    "implementation": "<単一領域のC++本文>",
    "justification": "<説明>",
    "confidence": "high|medium|low"
  },
  "auditor": {
    "verdict": "pass|reject|uncertain",
    "diff_digest": "<実diffのsha256>",
    "violations": [],
    "nits": [],
    "proposed_tests": [],
    "uncertainty": ""
  }
}
```

`value` と `planner` は設けない。機械 IR 入力は別の閉じた schema で受け、trusted renderer が同じ領域本文を作る。auditor 自己生成の pass は作らず、機械列挙ではその段を省略する。根拠: `docs/axis-onboarding.md:183`。

### 3.3 planner と critic

**planner-v4 は外す。** 現行出力は increase／decrease／explore_both と magnitude であり、複数 hook・補助関数・状態型には自然な順序がない。定数 `explore_both` を捏造して互換に見せるより、新 driver の proposal と履歴射影を変更する。根拠: `.claude/agents/planner-v4.md:75`、`O/p3_s4_loop.py:1199`。

coder は fresh・tools なしで、署名・許可 API・現在系列の評価済み候補と構造化結果を受ける。critic の attribution／recommend／avoid／uncertainty を次 proposal に還流する。検疫赤、compile 赤、liveness 赤、integrity 赤、cycle 赤を混ぜない。根拠: `.claude/agents/critic.md:16`, `:29`, `:31`。

`reflux=False` は赤節を落とすので本系列では使わない。critic なしの比較でも、verifier の失敗理由そのものは生成器に残す。根拠: `O/p3_s4_loop.py:1169`、`V/vldb-gap-analysis-README.md:123`。

### 3.4 admission と role 契約

現行 class は caller の enum 自己申告ではなく、source evidence と receipt／CLI authority から導出する形に進んでいる。根拠: `O/build_admission.py:656`。

| 候補 | class の扱い |
|---|---|
| current PIN の tracked-clean stock | `STOCK_BASELINE` |
| 登録 IR generator の再現可能出力 | generator receipt により `MACHINE_GENERATED` |
| 真に所定の人間 review を受けた source | review receipt により `HUMAN_REVIEWED` |
| Codex／LLM が書いた C++ | CLI opt-in 付き `CODER_AUTHORED` |

「手書き対照」と呼んでも Codex が書いたものを HUMAN_REVIEWED にしない。骨格適用済みの inert source も、tracked-clean でなければ stock class に自動分類されない。根拠: `O/build_admission.py:674`。

新 IR generator は閉じた `GeneratorId` と既存 entrypoint 登録へ接続する必要がある。auditor pass は build opt-in の代わりではない。根拠: `O/build_admission.py:107`, `:695`。

既存 auditor の型 17〜21 にある免除は **sort IR の事後条件専用**であり、新 C++ 軸へ移さない。新軸で許可する関数・状態追加と禁止する外部干渉を区別して role 契約を更新する。根拠: `.claude/agents/auditor.md:68`。

`.claude/agents/` 変更の明示承認は実装着手条件に残す。これは `docs/axis-onboarding.md:159`, `:258` の明記による。今回の返却物は変更案であり、承認を得たことにはしない。

## 4. 共通表現と公平な比較

### 4.1 共通候補表現

P6 の「C++ 本文」は**候補の材料化形式**として採る。ただし完全な候補 identity は、

> genome flags ＋骨格／PIN＋材料化された全 source の source_digest

である。同じ本文でも flags や骨格が違えば同一候補とは限らない。preprocess hash は意味的同値性の判定器でもない。根拠: `O/pipeline.py:137`、`O/source_digest.py:111`, `:1686`。

### 4.2 IR 案

閉じた型付き IR を C++ 部分空間として用意する。

| 要素 | 案 |
|---|---|
| 値型 | `Bool`, `U32`, `Action`, `LockResponse` |
| 入力 | abort reason、現在 lock の attempt、専用状態の scalar |
| 式 | 定数、比較、条件式、min/max、飽和加減算、有界 shift |
| 状態 | txn 内の固定個数の U32／Bool。配列・pointer・共有状態なし |
| 出力 | abort の待機量、lock action＋待機量、次状態 |
| サイズ | 式深さ・node 数・状態 field 数を事前固定 |
| 描画 | 型ごとの一意な parenthesis・literal・宣言順、固定署名へ決定的出力 |
| 停止 | 再帰・一般 loop なし。有限 DAG の評価＋固定数の代入だけ |
| arithmetic | unsigned の型を固定し、除算ゼロ・過大 shift・符号付き overflow を生成しない |

例として最大 4 state scalar、式深さ 4、総 node 数 64 を試走用契約値とする。これは実装済み・較正済みではない。

random はこの IR を型を保って生成し、sweep は有限の部分集合／座標を列挙、BO は離散パラメタまたは文法選択上で動かす。非 LLM 進化は型を保つ subtree 置換とする。**任意の C++ 文字列をランダム生成しない。**

§3-D の「構成的に安全な列挙」はこの IR で満たす。実走前に型・上限・退化点を機械検査する。偵察で IR が平坦でも、それは C++ 全空間の死亡証明ではない。IR を見直すか停止するかを人間判断へ返し、無審査で E に進まない。根拠: `docs/axis-onboarding.md:167`, `:180`, `:185`。

### 4.3 既知最良と初期候補

`_p2_entry` は workload 別 WAL の argmax を確認し、記録された genome を採用、なければ列挙して逆引きする。単なる「backoff=0」という別名ではない。根拠: `O/s1_known_axes_freeze.py:349`。

確認した frozen entry では balanced／write-heavy の `p2_2_flag_opt` は `B0-L-W0`、すなわち BACK_OFF=0、no-wait=1、Tictoc retry=0、WAL=0。静的 best は balanced 5 µs、write-heavy 10 µs。これは既存結果であり、新環境での最適保証ではない。根拠: `output/s1-freeze/known_axes_freeze.json:90`, `:113`, `:316`, `:339`。

初期候補を二層で扱う。

1. **exact reference:** stock、元 flags の `p2_2_flag_opt`、調整済み静的 backoff を元の適用方法で再評価する。
2. **新骨格内の seed:** 無待機＋即 abort、静的待機＋即 abort を IR／C++ で表す。

両者を同一 identity と偽らない。後者には hook・状態管理の費用が加わり得るため、その差を対照で測る。静的 best の導出契約は `O/s1_known_axes_freeze.py:384`。

### 4.4 「同じ空間」の二つの比較

| 比較 | 全 arm の空間 | 言えること |
|---|---|---|
| A: 探索法比較 | 同じ IR、同じ初期候補 | random／sweep／BO／進化／LLM の探索法の差 |
| B: 空間拡張比較 | 非 LLM は IR、LLM は C++ 本文 | 表現・探索法を合わせた差。純粋な探索法の優劣とは言えない |

P6 のまま B を「同一空間比較」と呼ぶことには反対する。共通 evaluator と共通 C++ 材料化形式だけでは、生成器の到達可能集合は一致しない。

共通条件は、評価数 B、提案数 A、初期候補、観測項目、workload、verify、perf reps、停止条件、故障 retry、endpoint 再評価。前処理拒否は A、pipeline へ投入された候補は B に計上し、compile／correctness 失敗も B から除かない。B-5 はこの A/B 分離と candidate／machine failure 分類を持つ。根拠: `O/b5_generator_contrast.py:44`, `:620`, `:711`, `:753`。

既存 B-5 の値 grammar、3 arm、slot schema、`_genome(value)`、endpoint の value 同一性は新候補 identity へ置換する必要がある。汎用コード空間 evaluator としてそのまま使えない。根拠: `O/b5_generator_contrast.py:138`, `:297`, `:763`, `:786`。

既知最良を全 arm に公開する比較は「既知結果を条件とする探索」と明記する。偵察 D の順位・勝ちコードは追加で流さない。独立合成を測る別 arm と混同しない。根拠: `docs/axis-onboarding.md:177`。

## 5. 見積り

出所は `output/insights/2026-09-20/t2797-b5-contrast/README.md:188` と `:230`。

| 定数 | 値 | 出所区分・限界 |
|---|---:|---|
| 1 session 固有費 \(C\) | 217〜509 秒、中央値498秒 | 実測。lock 待ち推定を除く |
| 予算換算 \(C_{\max}\) | 510秒 | 同文書 §8.2 の換算値 |
| build | 15〜17秒 | 旧 backoff 軸の実測 |
| LLM 1巡 \(L\) | 10〜13分 | critic・planner・coder・親処理込み実測 |
| 新関数軸の費用 | 未実測 | C++ compile、auditor、timeout 候補で増え得る |

node 時間の式は、

\[
H=\frac{N C + T_{\rm allocated\ wait}+T_{\rm retry}
 +T_{\rm controls}+T_{\rm tests}}{3600}.
\]

LLM を待ちながらノードを確保すれば、その待ちも node 時間に加算する。B-5 の共有 lock 待ちは総 wall の59%と推定され、LLM job には約7,360秒の handshake 待ちもあった。根拠: 同 README `:194`, `:196`, `:199`。

| 段 | 規模案と式 | node 時間 | LLM 時間 | 出所区分 |
|---|---|---:|---:|---|
| (a) DW-G01 生死 | 手書き方策3＋対照3＝6 session | \(6C/3600\)=0.36〜0.85h、中央値0.83h | 生成 loop なし。author/review は未見積り | 実測単価から試算 |
| (b) IR 偵察 D | IR16点＋対照3＝19 session、まずwrite-heavy | 1.15〜2.69h、中央値2.63h | 生成 loop なし | 同上 |
| (c) 手法比較試走 A | 5手法×3独立系列×(初期3＋探索8＋endpoint5)＋block対照5＝245 session | 14.77〜34.71h、中央値33.89h | LLM探索24巡＝4.0〜5.2h＋auditor | 同上 |
| (c追加) C++ 拡張 arm B | 3系列×16＝48 session | 2.89〜6.80h | 24巡＝4.0〜5.2h＋auditor | 同上 |

(a) の0.85hは**評価本体だけ**であり、骨格の変異・受入・失敗 retry を含む wave 全体が2h未満とは未確定。例えば残りを1hの実行上限内で賄えると確認できれば合計1.85hだが、これは予算案であって所要実測ではない。

(b) は上限換算が2h以上なので確認対象。(c) と追加 arm も確認対象。LLM待ちを同一 allocation 内で行う(c)は、さらに4.0〜5.2 node h以上を足す。planner を外すことによる約1分の削減は見込めても、新 auditor と長いコード生成の増分が未測定なので相殺して安く見積もらない。

**判定単位は一つのタスク／wave の合計であり、job を分割して2h未満扱いにはしない。** 根拠: `V/vldb-direction-verdicts.md` 項4。本稿では投入しない。

## 6. 軸定義シート

| 欄 | 記入案 |
|---|---|
| 軸名 | `silo-function-policy` |
| 変異型 | 関数群＋複数 hook＋txn 内専用状態 |
| SOURCE_REL | `cc/silo/transaction.cc`。既存編集面内。`O/source_digest.py:85` |
| marker ID | `silo-function-policy` |
| hole の位置と骨格 | include 列の後、namespace scope の単一領域。空 stock 枝。abort／lock の呼出し点は marker 外。`T:9`, `:47`, `:160` |
| 構文契約 | §1.2。固定署名、専用 scalar 状態、補助関数。外部大域・pointer・外部 API・前処理・namespace 脱出は禁止 |
| stock の動作 | BACK_OFF 条件付き適応待機、既存 no-wait／Tictoc 枝。`T:42`, `:161` |
| フラグ名 | CMake `CCBENCH_SILO_POLICY_VARIANT` → C++ `SILO_POLICY_VARIANT`。0=stock、1=新方策 |
| 壊しうる不変条件 | 契約違反による CC 状態干渉、UB、例外／非停止、再試行公平性、lock 保持時間、状態 reset の取り違え。骨格の誤配線なら取得済み lock の解放漏れ・取得不足・validation 回避 |
| verifier の死角 | 成功 txn の履歴が serializable でも、少数 worker の飢餓・tail latency・試行間の優先偏り・誤要因記録は保証されない。正常な非空 trace があることは全 worker の進行証明でない。`O/pipeline.py:585`、`V/D41.md:32` |
| reward hack 仮説 | 長い／競合の多い試行を繰り返し後回しにして短い成功だけを増やす。状態を worker fingerprint として使う。時計・set サイズ・共有 atomic があると workload／run 進行の代理を増やす。TRACE 外 state でも検証専用用途なら規律1上の意味監査が必要。`V/D1409.md:16`、`O/source_digest.py:2218` |
| positive control | §2.3。骨格負例と方策負例を分離し、G2・X/P・liveness・構文拒否を別集計 |
| 偵察列挙空間 | §4.2 の型付き有限 IR。構成的な算術安全性と停止性を持つ |
| 感度 workload | write-heavyを初手、balancedを次段、read-heavyを待機コストの対照に残す。性能値は新規未測定 |
| 計測動作点 | 1M／48 threads／skew0.9／3秒／5repを費用・比較の出発点とする。新環境のfloor適用確認は未完。根拠: B-5 README `:197`, `:198`、`O/pipeline.py:159` |

**P5 の観測判定:**

| 観測 | v1 案 | 理由 |
|---|---|---|
| abort 要因 | 渡す | 固定 enum。記録点と unset は骨格 |
| 同じ lock の試行番号 | 渡す案 | 局所的な有限 retry 応答に必要。ただし代理信号性は残る |
| txn retry 数 | 明示 field は渡さない | 専用 state から推定可能であり「遮断できた」とは言わない |
| read/write set サイズ・競合位置 | 渡さない | txn 種別・長さの優先代理になる |
| 生時刻・clocks_per_us | 渡さない | 待機換算は骨格。run 進行への直接アクセスを縮める |
| thid／key／tuple pointer／Tidword／epoch／FLAGS／result／quit | 渡さない | worker・データ・fitness・検証条件へのアクセスを避ける |
| 共有 atomic・txn 間履歴 | v1 では許さない | 全体進捗や worker の固定優先を作る経路が増える |

D48 は旧 trigger 軸の契約として不変に残す。一方、**新しい関数軸の承認だけから、D1409 が保留した代理信号の許容まで自動承認済みとは読まない**。txn 内 state に限定しても連続 abort の推定は可能である。新しい軸の採用裁定には、この限定した観測を許容する旨と fairness 非保証を明記する必要がある。根拠: `V/D48.md:31`、`V/D1409.md:32`, `:45`。

stock 適応 Backoff が commit 数を読む事実は確認済みだが、それは合成候補への同等アクセス許可の根拠にはならない。根拠: `include/backoff.hh:52`, `:115`。

## 7. §4 第3列の案

`docs/axis-onboarding.md:234` の既存各行に、次の列を追加する案。

| 論点 | 関数群・複数 hook・専用状態軸 |
|---|---|
| フラグ設計 | on/off。宣言・状態・呼出し点・reset を全て軸 OFF で消す |
| coder 出力 schema | 単一領域の implementation、value なし。固定署名の複数関数と限定状態型 |
| pre-build 整合チェック | 単一領域検疫＋effect veto＋軸固有宣言／参照契約＋実 diff に束縛した auditor veto |
| 安全性の問診 | UB、状態 lifetime、初期化、再帰／停止、呼出し graph、外部参照、lock 保持、retry 公平性。IR の保証を自由 C++ に拡張しない |
| 偵察の列挙 | 構成的に安全な型付き IR 部分空間。部分空間の結果と全空間の生死を区別する |
| auditor の役 | 関数・状態と固定骨格の境界、proxy、公平性、検証条件への依存を監査。機械 IR は既存規定どおり auditor 段を省略 |
| marker と呼出し点〔補足〕 | marker は1、呼出し点は複数。呼出し点を hole にしない |
| 状態〔補足〕 | 方策専用・txn 内。初期化／reset は固定骨格。共有状態は別裁定 |
| 実験主張〔補足〕 | IR 内の探索法比較と C++ 空間拡張の比較を別に報告 |

これはテンプレ改訂案であり、§4 が要求する D41 水準レビューを通してから採用する。根拠: `docs/axis-onboarding.md:225`。

## 8. 必須条件リスト案

**条件付き採用の決定文案:**

> Silo の待機・競合応答を関数群として合成する軸を条件付き採用する。CC の取得・検証・書込み機構は固定し、検証ゲートを維持する。「任意候補が構成上安全」「非列挙とは意味的無限」「IR と自由 C++ の比較は同一空間」という主張は採らない。

実装着手前に固定する事項:

1. P4 を後置案へ変更し、許可する関数・型・状態・参照・呼出しの契約を producer／consumer 両側で一致させる。
2. P5 の限定観測と txn 内 state の proxy 許容範囲を明示裁定する。旧 trigger の D48 契約は変更しない。
3. lock の全周回上限、待機後再読込、prefix unlock、CAS 成功記録、absent 検査の保存を骨格仕様に固定する。
4. 「契約を守る方策」「IR の構成的保証」「自由 C++ の残る不確実性」を分ける。
5. 軸定義シートと第3列案を同じ最終設計で3レンズにかける。中心設計を変えたら再レビューする。
6. DW-G01 の最小生死確認を先行し、専用 LLM driver の先払いをしない。
7. role 変更の具体差分と明示承認、D127 の build opt-in、機械生成 receipt の接続を確定する。
8. 変異の位置・期待 gate・期待結果、正例、費用合計を先に登録する。

C 段出口で確認する事項:

9. 軸 OFF の stock identity、軸 ON の honest identity、include 一致、diff-of-diffs を実測する。
10. 新骨格上で lockskip／early-unlock／read-validation 負例と正例を実走する。既存 JSON の存在だけで代替しない。
11. abort hook と lock hook をそれぞれ踏み、状態 reset と上限・再読込を確認する。
12. IR の安全な列挙を機械確認し、偵察結果の firewall を保つ。
13. reject 分類と critic 還流を実際の新 driver 出力まで通す。
14. 1タスク合計2 node h以上なら、実行前に費用確認を得る。

D41 の形に倣い、「条件付き採用」と「実装完了」を分離する。根拠: `V/D41.md:37`, `:64`。

## 9. brief P1〜P8 への判定

| P | 判定 | 理由 |
|---|---|---|
| P1 | **修正** | 方策／仕組み分離に同意。共有 atomic は見送り、専用状態を txn 内に限定する |
| P2 | **修正** | validation 非開放に同意。「原理的安全」「拒否数ゼロ」は自由 C++ の UB・封じ込め違反を無視する |
| P3 | **修正** | lock conflict hook を含める。待機後再読込、CAS失敗を含む周回上限、prefix解放を追加指定する |
| P4 | **反対** | 最初の CC include が必要 API と禁止大域を同時に公開する。include 間配置による封じ込めは成立しない |
| P5 | **修正** | 時刻・setサイズ・競合位置・共有状態を削る。残るstateのproxy性も明示裁定事項とする |
| P6 | **修正** | 共通材料化形式＋IR 部分空間は採る。ただし同一空間比較と空間拡張比較を分ける |
| P7 | **修正** | 兄弟 driver と既存 gate 再利用に同意。planner は外し、DW-G01 後に作る。sort／trigger 固有 admission は転用しない |
| P8 | **修正** | 出所値は確認できた。LLM／lock待ちのallocation費、auditor、変異、受入、故障retryを別計上する |

## 10. 未確認事項

- 新骨格・namespace 領域の実 compile、inert identity、diff-of-diffs の実測。
- 標準ライブラリ／外部依存まで含めた include の全識別子一覧。P4 を否定する明示的 include 経路は確認済み。
- 自由 C++ の軸固有構文検疫の実装費・完全性。字句制限を意味保証とはしていない。
- 新方策の sanitizer 実走結果、停止性、性能、fairness、tail latency。
- 提案した32周回／50µs／1,000µsの適切性。
- read-heavy の frozen best の詳細、および `_p2_entry` の全 WAL 再導出。balanced／write-heavy の frozen flags と導出コードは確認済み。
- 新軸の実 compile 費・auditor 費・変異／受入を含む wave 全体の node 時間。
- 性能側 crash／hang の全 launcher 経路における最終 reason。trace 側の分類と usable throughput 欠落の帰結は確認済み。
- TPC-C の新軸への認証適用。現行 pipeline は未対応 workload を検証前に拒否する経路を持ち、今回の YCSB 設計で対応済みとはしない。`O/pipeline.py:558`

## 総括

実装可能な中心案は、**単一の関数群領域から abort 待機と lock 競合応答を生成し、CC と trace の仕組みを固定する設計**である。P4 は実コード上成立せず、P2・P5・P6 は主張と契約の修正が必要になる。

次 wave は、限定観測・状態契約と3レンズ裁定を固定した後、最小骨格と手書き対照の生死確認から始める。専用 LLM driver、広い共有状態、validation の開放は先行させない。本稿は設計草稿であり、実装・実走による採用条件の充足は未完了である。