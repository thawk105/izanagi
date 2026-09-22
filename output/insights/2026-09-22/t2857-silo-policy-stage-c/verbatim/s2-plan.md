## 前提の検査

**A→B/C の分割は採用できます。ただし P4・P5・P7・P8 は修正が必要です。** 特に、負例の適用可否、既存 registry の波及、単独 TU 自己試験の単一理由性を実装前に固定してください。

以下、`T` は指定 worktree の `external/ccbench/cc/silo/transaction.cc`、`D` は `output/insights/2026-09-21/silo-function-synthesis-space/README.md`、`C/` は `orchestrator/campaign/`、`Q/` は `orchestrator/tests/` を表します。新規 path・interface・規則 ID は**提案**です。build・pytest・patch 適用は実行していません。

| 前提 | 判定 | 根拠・修正 |
|---|---|---|
| P1：A を先行、B/C を分離 | real | 固定 API・骨格が構文検査と probe の共通入力になる。`D:119–145,266–284,339–343`。共有 registry/test の編集所有者を別途固定する |
| P2：専用軸定数・専用構文検査・API 単一正本 | real | `C/axis_trigger_gating.py:22` 以降が定数 module の型。既存 tokenizer はそのままでは位置情報・新契約を満たさない。後述 |
| P3：骨格は二 file の patch、PIN 不動 | real | `Options.cmake:60–68` の universal definitions で配線可能。編集面は `C/source_digest.py:85–100` 内 |
| P4：既存負例の積み直し | 要修正 | lockskip の挿入位置は「内側ループ内」ではなく **ループ直前**。`broken-silo-lockskip-validation.patch:5`、`T:158–161`。norw と lockskip は提案骨格によって文脈が壊れる。early-unlock は既存版を維持できる見込み |
| P5：新 macro を既存 gate に登録 | 要修正 | 必要。ただし二辞書だけでは不足。site 数、define inventory、spawn inventory、materializer 登録にも波及。`C/condition_meaning_gate.py:329–340`、`Q/test_ccbench_spawn_sites.py:2843–2909` |
| P6：機構変異 8 走 | real | `D:324–328` と一致。上限削除は非検出対照であり KILLED 期待にしない |
| P7：既存 evaluate または短い driver | 要修正 | `evaluate` は `authorization_contract`・`build_context` が必須。CLI authority は登録済み入口から発行する。`C/pipeline.py:2607–2639`、`C/build_admission.py:444–495` |
| P8：132/136 秒・受入 0.25 h | 要修正 | brief:36 の親申告値。原ログは未確認。`D:417–449` の旧受入換算 1.14 h と異なる。新値を条件付きシナリオに使い、上限とは扱わない |

不変条件も個別に確認した結果です。

| 不変条件 | 判定 | 根拠 |
|---|---|---|
| OFF で stock identity、既存三軸不変 | real〔要求〕 | `D:111–117,275`。新骨格での成立は未実測 |
| 方策・要因・待機は両 build、TRACE は従来どおり | real | `D:173–182,288–296`、`T:147–153,174–180` |
| 負例・probe・変異を裸 macro とする | real | genome は通常 `CCBENCH_<axis>` に変換する。`C/model.py:84–93,146–152`。裸 macro を genome に入れても同じ供給経路にならない |
| submodule/gitlink/PIN/EBS/ALLOWLIST 不変 | real | 二 file は既存 allowlist 内。`C/source_digest.py:85–100` |
| CCBench build・計算投入の境界 | 要修正 | 今回は投入しない。brief:26 の「hook が拒否」は本調査で未確認。計算ノードで実行する計画自体は維持する |

実アンカー表の検証結果です。

| brief の行 | 判定 | 実コード |
|---|---|---|
| abort・待機 | real | `T:27–53` |
| begin | real | `T:55–59` |
| lockWriteSet・TRACE | real | `T:145–193` |
| 要因七点 | real | `T:98,162,187,458,470,481,739` |
| validation/writePhase/commit | real | `T:383,557,706–713` |
| flags | real | `Options.cmake:20,27–28,60–68`、`cc/silo/CMakeLists.txt:5–6` |
| trigger 骨格の型 | real | `patches/silo-backoff-trigger-gating-variant.patch:124–194` |
| 積み重ね・probe | real | `C/s8a_trigger_coverage.py:274–279,358–368,388–420` |
| 三負例・既存判定 | 要修正 | lockskip は両 X reason を期待する。`C/s3_lock_coverage.py:299–312` |
| define gate | 要修正 | 指定箇所に加えて site 数登録が必要。`C/condition_meaning_gate.py:329–340` |
| tokenizer/TU 前例 | real〔参照位置〕 | `C/backoff_hole_grammar.py:360–454`、`C/sort_swo_oracle.py:2454–2464,2538–2557`。compile flags は転用不可 |
| quarantine/effect/identity | real | `C/diff_quarantine.py:567–594`、`C/coder_effect_gate.py:114–115`、`C/source_digest.py:2160,2205` |
| evaluate/dispatch | real〔入口〕 | `C/pipeline.py:2585–2626`、`tools/pegasus/dispatch_compute.py:116` 以降。実投入条件の全経路は未確認 |

## 単位 A

**所有する新規成果物**

| path | 役割・公開 interface |
|---|---|
| `patches/silo-function-policy-variant.patch` | 二 file の骨格。hole の既定本文は待機 0・即 abort |
| `C/silo_function_policy_api.hh` | API 型・固定署名の単一正本。include を含めず、TU 側が `<cstdint>` を先に読む |
| `C/axis_silo_function_policy.py` | 軸定数のみ。実行時副作用なし |
| `Q/test_silo_function_policy_template.py` | patch 構造、API byte 一致、OFF/ON identity、include、diff-of-diffs |

API header は `D:123–133` の enum/context/response と、`izanagi_silo_policy::PolicyState` の前方宣言・三関数宣言を持たせます。骨格には header の**全 byte をそのまま埋め込む**方式を推奨します。実 transaction.cc に `#include` は追加しません。include の順序込み一致が必要だからです（`C/source_digest.py:2160–2179`）。

```cpp
uint32_t policy_after_abort(
    PolicyState&, const izanagi_silo_api::AbortContext&) noexcept;
izanagi_silo_api::LockResponse policy_on_lock_conflict(
    PolicyState&, const izanagi_silo_api::LockContext&) noexcept;
void policy_on_commit(
    PolicyState&, const izanagi_silo_api::CommitContext&) noexcept;
```

**骨格 patch の hunk 計画**

| 元位置 | 内容 |
|---|---|
| `Options.cmake:24` 付近 | `set(CCBENCH_SILO_POLICY_VARIANT 0 CACHE STRING "...")` |
| `Options.cmake:67` 後 | universal definitions に `SILO_POLICY_VARIANT=${CCBENCH_SILO_POLICY_VARIANT}` |
| `T:9` 後 | flag 未供給の `#error`、ON 前提検査、API block、namespace 外枠、単一 marker、空 stock 枝、骨格 helper |
| `T:47` | ON は abort wrapper→clamp→待機、OFF は既存 Backoff 呼出しを保存 |
| `T:56` 後 | ON の abort reason を unset に戻す。PolicyState は reset しない |
| `T:98,187,458,470,481,739` | status 代入に隣接して対応 reason を記録 |
| `T:158–184` | attempt・上限・競合応答・再読込を追加。CAS と既存 TRACE は共通部に残す |
| `T:708` 後 | writePhase 完了後、成功通知 wrapper を一回呼ぶ |

ON 前提は `!BACK_OFF` ではなく、設計本文どおり **`BACK_OFF != 1`** とします。値 2 も拒否するためです（`D:90,112`）。

```cpp
#if BACK_OFF != 1 || NO_WAIT_LOCKING_IN_VALIDATION != 1 || NO_WAIT_OF_TICTOC != 0
#error "..."
#endif
```

namespace は次の形に固定します（`D:87–103`）。

```cpp
#if SILO_POLICY_VARIANT
// API header の byte を埋込み
namespace izanagi_silo_policy {
#endif
// EVOLVE-BLOCK-BEGIN silo-function-policy
#if SILO_POLICY_VARIANT
// 本文
#else
#endif
// EVOLVE-BLOCK-END silo-function-policy
#if SILO_POLICY_VARIANT
}
namespace izanagi_silo_skel {
// 状態・PRNG・待機器・wrapper
}
#endif
```

骨格には worker ごとの `thread_local ::izanagi_silo_policy::PolicyState` を一個置き、別の reason・PRNG 状態を骨格所有にします。wrapper は `__attribute__((noipa))` を付け、`::izanagi_silo_policy::policy_*` を完全修飾で呼びます。action は `static_cast<uint32_t>(response.action) == 0u` で判定します（`D:102,152,174–179`）。

lock ループは丸ごと複製せず、次の配置にします。

1. tuple ごとの初回 load より前に ON 専用 `attempt=0` を置く。
2. 共通 `for (;;)` の先頭で ON 専用 `attempt >= 32` を検査。
3. 今周回の番号を保存して attempt を増加。hook には **0〜31** を渡す。
4. `expected.lock` の枝だけ ON/OFF に分ける。
5. ON retry は `min(wait_us,50u)` を待ち、`loadAcquire` で expected を更新して次周回へ進む。
6. CAS 成功部分は共通。失敗も次周回へ進むので一回として数える。

CAS 失敗時は `compareExchange` が expected を更新します（`external/ccbench/include/atomic_wrapper.hh:67–69`）。上限判定を conflict 枝だけに置いてはいけません。

上限・action abort・未知 action は、いずれも `status_=aborted`、reason=`lock_conflict`、`itr != begin` のとき `unlockWriteSet(itr)`、return とします。prefix 関数は `[begin,end)` を解放します（`T:367–379`）。既存 `clear_shadow` と CAS 成功後の `record_lock` を新しい `#else` に入れません（`T:152,179`）。

abort 待機は U32 で clamp してから、64 bit に拡幅して cycle 数へ変換します。`ADD_ANALYSIS` の既存 start/latency 計数の内側に置きます（`T:42–51`）。PRNG は固定の非零 seed と unsigned 演算だけの骨格実装にし、時刻・thid を方策へ渡しません（`D:146–155`）。

七点の定数写像は次です。

```python
MARKER_ID = "silo-function-policy"
SOURCE_REL = "cc/silo/transaction.cc"
TEMPLATE_PATCH = "silo-function-policy-variant.patch"
FLAG = "SILO_POLICY_VARIANT"
PIN = pin.CURRENT_PIN
ABORT_WAIT_MAX_US = 1000
LOCK_WAIT_MAX_US = 50
LOCK_ATTEMPT_LIMIT = 32
REASON_NAMES = (
    "unset", "lock_conflict", "update_absent", "read_tid",
    "read_locked", "node_validation", "insert_node", "scan_node",
)
```

記録点の対応は `T:98→insert_node、162→lock_conflict、187→update_absent、458→read_tid、470→read_locked、481→node_validation、739→scan_node`。定数 test は API enum 順序とも照合します（`D:123–144`）。

**静的 identity と build の分離**

| login 側で行える検査 | 計算ノードで必要な検査 |
|---|---|
| patch の touch-set、marker、空 stock、API block byte 一致 | 実 include 環境でのコンパイル・リンク |
| OFF `resolve(...)=stock` | TRACE/perf の両 build |
| ON `resolve(...)!=stock`、異なる本文で別 token | 三 hook の実呼出し・状態寿命 |
| `assert_includes_match_head` | noipa を含む実 toolchain 適合 |
| `assert_trace_diff_matches_head` | verify・bench・焦点試験 |

`resolve` は build しません。git read と preprocess を使い、`_cpp_normalize` は `g++ -E -P -dD -nostdinc -Werror=undef ... -x c++ -` を起動します（`C/source_digest.py:1686–1692,2467–2485`）。既定 compiler は `g++-13` なので login では実在 compiler を明示します。これは構文・型を検査しません。

静的 identity test も patch 適用用の一時 checkout が必要です。本 read-only セッションでは未実行です。API 一致 test は適用後の API 区間と header 全 byte を比較し、patch テキストの見た目だけを検査しない形にします。

## 単位 B

**所有する新規成果物**

| path | interface |
|---|---|
| `C/silo_policy_grammar.py` | `validate_policy(source: str) -> PolicyDecision`。候補拒否は値で返す。内部障害を候補拒否に変換しない |
| `C/silo_policy_compile.py` | `compile_policy(source: str, *, compiler: str, scratch_dir: Path) -> CompileDecision`。compile 単独呼出し可能 |
| `C/silo_policy_ubsan.py` | `run_suite(fixtures, *, compiler, scratch_dir) -> dict`、`main(argv=None)->int` |
| `Q/fixtures/silo_function_policy/contracts/` | 独立した `.cpp` 本文と期待 stage/rule の manifest |
| `Q/test_silo_policy_grammar.py` | 構文・型・名前解決・境界正例 |
| `Q/test_silo_policy_compile.py` | 単独 TU・自己試験・資源停止 |
| `Q/test_silo_policy_ubsan.py` | harness の結果分類と実駆動 |

`PolicyDecision` は `accepted, stage, rule_id, offset, line, column, reason` を持たせます。compile 結果には `returncode, timed_out, unavailable, diagnostic, diagnostic_truncated, command` を追加します。規則 ID は固定、診断本文は有界にし、後段へ「どの契約が壊れたか」を渡します。既存の構造化拒否の型は `C/backoff_hole_grammar.py:54–77` です。

**tokenizer は直接再利用しないことを推奨します。**

既存 `_tokens()` は longest-match の punctuator、数値 token、括弧深度制限には使えます。しかし以下が不一致です。

- 代替綴りは普通の identifier として通る（`:413–425`）。
- digraph は token として受理する（`:169–175`）。
- literal suffix の認識は `ll/ull`・無接尾辞も含む（`:259–260`）。
- `__` identifier と `::` を禁止しない（`:413–439`）。
- token の index は token 通番で、元 byte offset ではない（`:404,424,439`）。
- `_Malformed` は位置を保持しない（`:160–161`）。

新 lexer はこの走査方式を参考に、元位置を保持する `Token(kind,text,start,end)` を返します。既存三軸の tokenizer は変更しません。代替綴りは内部的には正規演算子へ写せる token 種を持たせ、通常経路では字句規則で拒否します。これにより「字句規則だけ外す自己試験」が後段の parser 拒否で覆われません（`D:338`）。

**parser と型付け**

再帰下降で宣言・文を読み、式は優先順位 parser とします。各式に型・lvalue・const・literal 値・参照先 symbol を付与します（`D:205–257`）。

| 提案規則群 | 実装内容 |
|---|---|
| `lex.*` | 代替綴り/digraph、`__`、先頭 `::`、文字列/文字、配列記号、arrow、整数 suffix/value を検査 |
| `decl.state` | PolicyState 一個、16 member 以下、U32/U64/bool、既定 literal 初期化必須 |
| `decl.constant` | namespace constexpr のみ。先行定数と許可演算による定数式 |
| `decl.function` | 必須署名三個を一意照合、全関数 noexcept、型集合を限定 |
| `name.resolve` | scope stack と symbol table。API 型/field/enum、自前名、min/max のみ |
| `call.dag` | 関数本体の検査完了後に関数名を公開。自己呼出し・前方呼出しを拒否 |
| `stmt.*` | 初期化必須、代入は独立文、void call 文、if/block/switch/return のみ |
| `init.self` | 宣言中 identifier を別管理し、外側同名 symbol があっても自己初期化を拒否 |
| `return.final` | 非 void の関数本体末尾は return |
| `switch.closed` | case/default の終端、case 内宣言の block、条件/label 型を検査 |
| `type.*` | `D:240–257` の演算表をそのまま判定表にする |
| `rhs.literal` | `/ %` は非零 literal、shift は左辺幅未満。複合代入にも適用 |
| `assignment.statement` | 部分式代入、`++ --`、comma operator を拒否 |

U32/U64 の混合算術・除算は U64、shift は左辺型、代入・return・引数の U64→U32 は許可します。bool は数値へ暗黙変換しません。`LockResponse{action,wait}` の第二要素は正確に U32 です（`D:240–257`）。

**契約上の小さい未決事項：名前を省略した仮引数を許してください。** 空の CommitContext を名前付きで受け、何もしない成功通知は `-Wextra -Werror` と衝突します。C-style `(void)c` を許可文法へ追加するより、`const CommitContext&` の無名引数を許す方が狭い変更です。型付き署名は不変です（`D:128,133,214,270`）。実 compiler での確認は未実施です。

**単独 TU**

```cpp
#include <cstdint>
#include <algorithm>
#include "/absolute/repo/path/orchestrator/campaign/silo_function_policy_api.hh"
namespace izanagi_silo_policy {
  // hole 本文
}
```

```text
g++ -std=c++17 -Wall -Wextra -Werror -fsyntax-only policy.cc
```

-D・CC include path・masstree は与えません。環境由来の include path も固定し、実 command と compiler version を記録します。固定署名宣言との不整合は compiler にも検査させます（`D:270–274`）。

資源制限は既存 oracle を参考に、compile CPU 8/9 秒、AS 2 GiB、CORE 0、process group ごとの timeout cleanup、診断返却 16 KiB を初期案とします（`C/sort_swo_oracle.py:60,64,2192–2198,2550–2589`）。新 workload の実測上限ではないので、最終 timeout は親の正例実測後に確定します。stderr は file size 上限を持つ一時 file に流し、無制限 PIPE capture を避けます。`-fsyntax-only` では executable の存在を要求しません。

**単一理由性**

`Masstrees` 等の外部名は段 3 の名前解決でも拒否されます。したがって次の二種を分けます。

- 全四段の試験：最初の実効拒否を期待する。
- 段 4 単独の試験：`compile_policy()` を直接呼び、TU 封じ込めの検出力を測る。

後者を「全経路で段 4 だけが拒否した」と報告してはいけません（`D:199–203,272–273`、`docs/dev-wave/mutation.md:5–20`）。

`%:` は行頭なら DiffQuarantine の `_DIRECTIVE_RE` が拒否します。式中の digraph は段 3 の対象です（`C/diff_quarantine.py:53–56`）。loop も `while(true)` 等は effect gate が先に拒否しうるため、段 3 全経路負例には有限条件の loop を使い、実際の初回拒否を確認します（`C/coder_effect_gate.py:107–119`）。

**UBSan**

手書き四方策と runtime UB 負例を、CC 非依存の一個の harness TU に別 namespace で収容します。入力は reason 8 値×attempt 0〜33×固定呼出し列です。列は少なくとも `abort→lock→commit→次txn lock/abort` と `abortのみ` を含めます（`D:343`）。

`-fsanitize=undefined -fno-sanitize-recover=undefined -O1 -g` で作り、正常群を一回走らせ、UB 負例は同じ executable の case 指定で子 process ごとに一回駆動します。一つの UB で残りの試験を飛ばさないためです。runtime zero division・過大 shift・signed overflow を用意し、入力値を runtime に与えます。自己初期化など UBSan が必ず検出するとは言えないものは、sanitizer KILLED 期待に含めません。

## 単位 C

**所有する新規成果物**

| path | 役割・interface |
|---|---|
| `patches/instr-silo-function-policy-probe.patch` | 診断専用 hook/event 計装 |
| `patches/broken-silo-policy-norw-validation.patch` | 新骨格の reason store を含む norw |
| `patches/broken-silo-policy-lockskip-validation.patch` | 新骨格の attempt 初期化を含む文脈へ適用 |
| `patches/broken-silo-policy-<defect>.patch` 八枚 | 相互排他的な機構変異 |
| `C/silo_policy_coverage.py` | `parse_probe(paths)->ProbeReport`、`check_case(case,result)->dict[str,bool]`、`main(argv=None)->int` |
| `C/silo_policy_smoke.py` | 既存 evaluate を呼ぶ生死確認入口 |
| `C/silo_function_policy/policies/{abort0,static5,static10,retry}.cpp` | namespace 本文のみ |
| `Q/test_silo_policy_coverage.py` | parse・判定・欠損拒否・積み重ね試験 |

**三負例の適用**

`patchharness.apply_patch()` は通常の `git apply` です。`--3way` や文脈を削る fuzz 設定はありません。行番号 offset は許容されても、hunk 文脈の内容は一致しなければなりません（`C/patchharness.py:204–211`）。

| 負例 | 骨格上への判定 | 対応 |
|---|---|---|
| norw | **提案骨格では旧 hunk 不一致**。`T:458` 後の reason store が既存 hunk 内に入る | 新版は reason store も含む abort 部全体を既存 `IZANAGI_BREAK_NOREAD_VALIDATION` の else 側に置く |
| lockskip | **提案骨格では旧 hunk 不一致**。`T:159` 直後の上限検査が旧文脈を変える | 新版は初回 load 後、共通ループ前で `max_wset_` 更新→continue。既存 `IZANAGI_BREAK_LOCK_COVERAGE` を再利用 |
| early-unlock | **適用できる見込み**。変更対象は writePhase の write-loop で、A は変更しない | 既存 patch を使用。実 `git apply --check` は未実行 |

norw/lockskip の新 patch は「新骨格＋probe」に対して生成します。既存三負例の実適用結果を装わず、A/C 実装後の厳密適用 test を受入条件にします。適用順は `applied(skeleton)→probe→負例`、退出時は全て restore です（`C/s8a_trigger_coverage.py:356–383`）。

期待判定は既存 driver とそろえます。

| ケース | 方策 | 判定 |
|---|---|---|
| norw | 即 abort／最大待機 | `verdict=="non-serializable" && total_cycles>=1`。`C/s2_verify_calibration.py:411` |
| lockskip | 同上 | 単一 thread で `total_cycles==0`、violations>0、`verdict=="indeterminate"`、X reasons に入口欠落と保持欠落の両方。`C/s3_lock_coverage.py:299–304` |
| early-unlock | 同上 | violations>0、cycles==0、indeterminate、X reasons の集合が保持欠落のみ。`:308–312` |

「lockskip は入口欠落だけ」という exact-set 判定は既存実装に反します。

**probe と焦点試験**

probe macro は `IZANAGI_SILO_POLICY_PROBE`。方策本体や stock build には入れません。診断専用出力は verifier trace と別 file にし、例えば次の schema を固定します。

```text
P1 worker seq txn event reason attempt requested effective state_before state_after
```

実際の policy 呼出し直前/直後、`T:708` 後の commit 完了点、retry 後の CAS 成功、上限出口、clamp、reason 記録点から emit します。方策の field 値は焦点用方策に限り、既知の `epoch` member を観測します。任意方策の state layout を推測しません（根拠位置：`T:47,159–181,708`、`D:339–342`）。

判定は aggregate 数だけでなく txn/event 対応も使います。

| check | 判定式 |
|---|---|
| abort wiring | `abort_hook_calls == abort_counts`、かつ対象走で abort_counts>0 |
| lock wiring | 実 conflict-site 数と lock-hook-call 数が一致し、対象走で >0 |
| commit wiring | 成功 txn ごとに commit hook 一回、abort txn では零回 |
| state lifetime | commit 後に方策が増加させた epoch が、同 worker の次 txn hook の before に一致 |
| retry reload | 他者の release 後、同じ取得試行が attempt<32 で成功 |
| limit | holder を維持した焦点走で limit-abort>0、reason=lock_conflict、prefix が解放済み |
| clamp | requested>上限、effective==上限を対応 event で確認 |
| reason conservation | reason 別 abort 合計==abort hook calls |
| reason accuracy | 記録 site の期待 reason と実 context.reason が一致 |

abort 総数の取得は `C/s8a_trigger_coverage.py:91,274–279`、保存則の前例は `:394` です。欠損・重複・順序破損・負の値・未知 schema は parse error にして all_pass に入りません。

YCSB の通常競合だけでは reload・limit・次 txn の hook 発火を決定的に保証できません。計算ノードの焦点 harness は**実 `TxExecutor::lockWriteSet/commit/abort` を呼ぶ専用 fixture**とし、holder/releaser を barrier で制御します。TxExecutor constructor と対象メソッドは公開です（`cc/silo/include/transaction.hh:68–76,84–98,138–154`）。初期化・link の具体構成は未確認です。模倣 lock ループだけの試験で骨格を検証したとは数えません。

七要因すべて >0 を YCSB に要求してはいけません。既存 driver は unset/update-absent/node/insert/scan を構造ゼロとしています（`C/s8a_trigger_coverage.py:86–89`）。七点の実経路発火は、専用 CC fixture を作れたものだけ動的実証とし、残りは写像の静的検査と未測定表示を分けます。

**機構変異の形**

八枚の相互排他的 patch に、同じ裸 macro `IZANAGI_BREAK_SILO_POLICY` を使う案を推奨します。一回に一枚だけ適用し、case ID・patch SHA・source SHA を結果に束縛します。一枚に八 macro を入れるより registry の増加を小さくできます。各 patch は一個の `#if IZANAGI_BREAK_SILO_POLICY` と else の正常断片を持ちます。

| defect | 変更点 | 期待 |
|---|---|---|
| no-clamp | abort 待機 clamp を除去 | UINT32_MAX 方策で `trace-timeout`。正常骨格対照は完走 |
| no-reload | retry 後 loadAcquire を除去 | 焦点試験の release→取得成功が不成立。timeout は期待しない |
| no-limit | attempt>=32 の出口を除去 | 非検出対照。KILLED としない |
| no-prefix-unlock | 共通 conflict/limit abort 出口の unlock を除去 | legacy RMW で `trace-timeout` |
| no-abort-hook | wrapper の方策呼出しを固定応答へ置換 | abort wiring 不成立 |
| no-lock-hook | 同上 | lock wiring 不成立 |
| no-commit-hook | 成功通知の実呼出しを除去 | commit wiring/state lifetime 不成立 |
| wrong-reason | lock_conflict を node_validation へ付け替え | reason accuracy/構造ゼロが赤、保存則は維持 |

計数を wrapper の入口だけに置くと、wrapper 内の呼出し解除を見逃します。**実方策呼出し**を計数し、独立した site/txn event を分母にしてください（`D:328,341–342`）。

clamp と prefix unlock の timeout は競合条件付きです。実 workload で到達確認できるまでは期待結果であり、検出実績ではありません（`D:324,327`、`docs/dev-wave/operations.md:98–108`）。

**macro 登録**

追加 macro は推奨案では三個です。

| macro | DefineSpec |
|---|---|
| `SILO_POLICY_VARIANT` | CMAKE_CACHE、owner=`("cc/silo/transaction.cc",)`、target=`ycsb_silo.exe`、骨格 patch、inert=`("0",)` |
| `IZANAGI_SILO_POLICY_PROBE` | CMAKE_CXX_FLAGS、同 owner/target、probe patch、companion に軸 ON |
| `IZANAGI_BREAK_SILO_POLICY` | CMAKE_CXX_FLAGS、同 owner/target、代表変異 patch、companion に軸 ON |

既存 norw/lockskip/early-unlock macro は再利用し、新しい macro を増やしません。新 macro の specimen は `C/condition_meaning_gate.py:65–83,225–255` と同形です。

`_CONDITIONAL_BRANCH_WITNESSES` は `(SOURCE_REL, "#if <macro>")`。骨格と probe は複数 site を持つため `_CONDITIONAL_BRANCH_SITE_COUNTS` に完成 patch の exact 数を登録します。八変異はそれぞれ一 site に固定します。既存検査は行全文一致と site 数を要求します（`:3018–3046`）。

閉集合 test は supply に三個、meaning の branch 集合に三個を足し、現行 22/23 を **25/26** に変更する案です（`Q/test_condition_meaning_gate.py:3380` 以降）。related decode 集合の拡張要否は未確認です。

driver 自前 preprocess だけで登録を避ける案は、現行の patch define inventory test に反します（`Q/test_ccbench_spawn_sites.py:2888–2901`）。閉集合の例外追加まで要するため推奨しません。ただし既存 meaning gate は macro 分岐の選択証拠であり、break の目的動作までは証明しません。各負例の preprocess 出力に対象 break が残る証拠も保存します。

**生死確認**

手書き本文は四本とします。

- abort0：abort 待機 0、lock 即 abort。
- static5/static10：abort 待機 5/10 µs、lock 即 abort。
- retry：lock 待機 0、一定 attempt まで retry、その後 abort。

`parse_template_file`→`render_hole`→四段検査→実 source に materialize→`resolve_evidence`→evaluate の順です（`C/diff_quarantine.py:567`、`C/p3_s4_loop.py:695–705`、`C/source_digest.py:2413–2464`）。

```python
Genome("silo", {
    "BACK_OFF": 1,
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
    "SILO_POLICY_VARIANT": 1,
})
```

stock 対照は未改変 pinned tree を使います。OFF 骨格は src_token が stock でも tracked-clean ではないため、`STOCK_BASELINE` 判定とは同一ではありません（`C/build_admission.py:674–676`）。

CLI は `--allow-coder-derived-build` を登録済み coder entrypoint で受け、`build_run_context` に authority を一度渡します。手書き方策には generator/review receipt を渡さず `CODER_AUTHORED` を導出します（`:468–495,521–544,695–699`）。新入口の materializer 登録が必要です（`C/materializer_admission.py:152–174,197–236`）。

`evaluate` に legacy と `performance_correctness_workload(perf)` を渡し、同 job で stock＋四方策を一回ずつ実行します。env tag は compute 側で確定した既存環境契約の値を使い、任意文字列を捏造しません（`C/pipeline.py:193–215,2585–2626`）。環境契約・計測 authorization の具体的構築は未確認で、既存入口の再利用を優先します。

結果は `output/env/<tag>/calibration/silo_function_policy_{coverage,smoke}.json`。`runs`、`checks: dict[str,bool]`、`all_pass=all(checks.values())` に加え、source/patch/API/hole digest、compiler、condition receipts、admission、実 command、verdict、probe を保存します。既存形式は `C/s8a_trigger_coverage.py:347–350,418–425` です。

## 閉集合と meta-test の波及

**確認できた波及は以下です。repo 全体の閉集合を全列挙できたとは断言しません。**

| 検査・registry | 必要な対応 |
|---|---|
| `Q/test_ccbench_spawn_sites.py:2888–2901` | 新 patch の define と `_DEFINE_SPECS` を一致させる |
| 同 `:2904–2909` | 新 build sink が供給・意味の両 gate を経由する構造を用意 |
| 同 `:2843–2850` | 新 subprocess site を exact inventory に追加。TU compiler/UBSan は非 CCBench、probe は診断 CCBench として区別 |
| `Q/test_condition_meaning_gate.py:3380` | supply/meaning 集合・件数・新 spec の期待値 |
| `Q/test_p3_s4_loop.py:8432–8465` | `IZANAGI_` token を含む新 patch を path 別許容集合へ追加。E 段の variant registry に混ぜない |
| `C/materializer_admission.py:140–200` | smoke の coder entrypoint、coverage の非認定 materializer を登録 |
| `Q/test_campaign.py:11405–11420` | 新 axis module と SOURCE_REL の組を追加。現状は追加漏れでも自動赤にならない |
| 同 `:11386–11402` | EBS/ALLOWLIST は変更不要。期待値も維持 |
| `Q/test_plain_runner_coverage.py:60–85` | 新 test は実行する自走 harness か README allowlist のどちらか。両方にはしない |
| `Q/conftest.py:627–652`、`Q/README.md:248` | 実 repo を読む test は既存 resource 分類・排他対象を確認。一時 repo のみの test に一律 group は不要 |
| `Q/test_mocc_template_proof.py:95–111` | 全 patch 走査は MOCC marker 用。Silo patch 追加だけで期待集合を変更する必要は認められない |
| `patches/README.md:451` 付近 | 軸・診断専用・適用順・裸 macro・性能値へ混ぜない旨を追記 |

`patches/README.md` に全 patch の記載を強制する専用 test と、全 marker ID の単一閉集合は今回の検索では見つかりませんでした。generic marker parser 自体は任意の marker_id を受けます（`C/diff_quarantine.py:567,590–591`）。「存在しない」との断定はしません。

docs path lint、materializer 関連の全 exact-set test、追加 GeneratorId の必要性とその波及は未確認です。A/B/C に共有 test を同時編集させず、**既存 registry/meta-test の変更は C 所有**にまとめることを推奨します。

## 事前登録の候補

以下の node 名は新規予定です。**実観測した KILLED node 集合ではありません。** 最終 anchor と期待失敗 node 全集合は、実装 commit 後の self-run または dispatch probe で確定します（`docs/dev-wave/mutation.md:55–61`）。

| fixture／変異 | 位置・置換 | 期待段・規則／node |
|---|---|---|
| OFF 骨格 | FLAG=0 | `test_template_off_is_stock`：stock/include/diff-of-diffs |
| ON 四方策 | 各 hole | `test_template_on_is_honest`、build＋両 verify＋bench |
| U32/U64 境界 | 2³²−1、2³²、2⁶⁴−1、`u/ul` | grammar 正例。2⁶⁴ は `lex.integer-range` |
| 算術境界 | `/1ul`、U64→U32、shift 31/63 | 正例。shift 32/64、`/0u` は `rhs.literal` |
| bool 算術 | `(b1+b2)<<31u`、`(~b)<<1u` | 段3 `type.numeric` |
| 変数 divisor | `s.m /= v` | 段3 `rhs.literal` |
| bool return | U32 関数で `return true` | 段3 `type.conversion` |
| 自己初期化 | `uint32_t x=x`、`uint32_t x=helper(x)` | 段3 `init.self` |
| 既存変数の更新 | 初期化済み `x=helper(x);` | **正例**。これを自己参照として拒否しない |
| return 欠落 | 非 void の末尾が if/block | 段3 `return.final` |
| 部分式代入 | `(a.m=1u)+(b.m=2u)` | 段3 `assignment.statement` |
| ++/comma | `x++`、`(x,y)` | 段3 `stmt.forbidden` |
| 永続状態 | static 局所、追加 thread_local | 段3 `decl.storage` |
| 宣言逸脱 | operator==、template、配列、loop、再帰 | 段3 対応規則。全経路では前段拒否の有無を確認 |
| 字句逸脱 | `__TIME__`、`__COUNTER__`、`bitand`、digraph、先頭 `::` | 段3 `lex.*` |
| `%:define` | 行頭 digraph 指令 | 段1 content-directive。段3 の証拠に数えない |
| 外部名六種 | Masstrees/FLAGS_thread_num/TRACE/izanagi_trace/rdtscp/GlobalEpoch | 全経路は段3、compile 単独は段4赤 |
| 不正 flags | ON＋BACK_OFF=0、ON＋TICTOC=1 | 骨格 #error。追加境界として BACK_OFF=2、NO_WAIT_LOCKING=0 |
| 上限超 wait | UINT32_MAX | grammar/TU は正例、骨格で clamp |
| norw×二方策 | 新 norw patch | non-serializable＋cycles≥1 |
| lockskip×二方策 | 新 lockskip patch | indeterminate＋両 X reason |
| early-unlock×二方策 | 既存 patch | indeterminate＋保持 X のみ |
| clamp 削除 | abort wait helper | trace-timeout |
| reload 削除 | retry 後 load | focus retry-success 赤、timeout 不要 |
| limit 削除 | attempt 上限出口 | 非検出対照 |
| prefix unlock 削除 | conflict/limit abort 出口 | legacy trace-timeout |
| 三 hook 解除 | 実方策呼出し各一点 | 対応する probe check 赤 |
| reason 誤記録 | lock→node | reason accuracy 赤 |

設計末尾の四組は、dev-wave 変異として次のように登録します。

| 変異 ID | 実装後に固定する置換 | 単一理由 fixture | 期待 KILLED node 案 |
|---|---|---|---|
| M-TU-GLOBAL | TU builder の api 後に `uint64_t GlobalEpoch;` を一行追加 | GlobalEpoch のみを使う compile 単独負例 | `test_compile_rejects_external_global` |
| M-TU-MACRO | compile argv に `-DTRACE=1` を追加 | `return TRACE;` を含む compile 単独負例 | `test_compile_rejects_unsupplied_macro` |
| M-TYPE | numeric operand validator の bool 拒否を bool→U32 扱いへ置換 | 他の規則に違反しない bool 算術 | `test_grammar_rejects_bool_arithmetic` |
| M-LEX | alternative-token 拒否を除去、正規演算子への内部写像は維持 | 合法な二項 `x bitand y` / `a and b` | `test_grammar_rejects_alternative_binary_tokens` |

M-TYPE は型規則を単に一箇所消しても後続型規則で拒否される可能性があります。実効的に受理集合が変わる置換を確認して登録します。M-LEX に配列 digraph や単項 bitand を使わない理由も同じです（`D:334–338`）。

UBSan の負例はこれらと別枠にします。診断文字列だけ変わる変異は KILLED とせず、diagnostic sensitivity として記録します（`docs/dev-wave/mutation.md:16–20,55–61`）。

## 計算の見積り

四手書き方策＋stock 一個、負例六走、機構変異八走＋probe 正例一走を採用したシナリオです。単価は brief:36 の親申告を使用し、同 regime の実測上限ではありません。

| job | 走数・内容 | Elapse 換算 |
|---|---|---|
| J1：骨格負例 | 3×2=6 走 | `6×132=792秒`＝0.220 node h |
| J2：probe・機構 | 8＋正例1=9 走 | `9×136=1,224秒`＝0.340 node h |
| J3：生死確認 | 四方策＋stock=5 session | `5×217〜510=1,085〜2,550秒`＝0.301〜0.708 node h |
| J4：受入 | 一回 | 親単価なら `0.25×3600=900秒` |
| 小計 | 上記 | `4,001〜5,466秒`＝**1.111〜1.518 node h** |

**この小計は投入総額ではありません。** 次を追加する必要があります。

```text
総 node 時間
= 1.111〜1.518 h
+ 不正 flags 二 build の実費
+ 焦点 harness の独立 build/駆動が単価に含まれない分
+ dev-wave 変異 probe/final の実費
+ timeout 負例の単価超過分
+ setup/cleanup の未包含分
```

132/136 秒は旧 driver 全体の実費なので、新しい一ケース単価としての適用は仮置きです。さらに受入を旧設計の 1.14 h で換算すると、小計だけで **2.001〜2.408 h** になります（`D:417–449`）。

推奨は、J1/J2 を同一 compute job で逐次実行し依存 build を再利用、J3 は同 job 内で stock と四方策を近接実行、J4 は既存受入方式に従う構成です。複数 node へ分けても node 時間は減りません。bench lock の分離が未確認なので性能走の並列化は推奨しません（`D:455` 付近）。

login の grammar/TU/UBSan は node 時間に加算しません。投入前には親が実測単価の原ログと追加費用を埋めて合計を提示する必要があります。今回は投入・承認要求を行っていません。

## 未確認とリスク

**DW-O13 の入力実在・到達可能性**

| 新検査 | 入力となる実成果物／field | 到達可能性 |
|---|---|---|
| 字句規則 | `.cpp` fixture／将来 proposal の `implementation` の token | 各違反を本文で構成可能。compile 不要 |
| 宣言・storage・state 数 | 同本文の AST 宣言 | 0/1/2 state、16/17 member 等を構成可能 |
| 名前解決・DAG | symbol table と call target | 未宣言・自己・先行/後続関数を構成可能 |
| 文・return・switch | AST statement と terminal | 対応本文を構成可能 |
| 算術・型・literal 制約 | 各式の inferred type/value | U32/U64/bool 境界は構成可能。実 compiler との照合は未実施 |
| 単独 TU | 生成 TU、argv、returncode、stderr | 外部名・TRACE 未供給の赤は予測可能。GCC 11.4 実測は未実施 |
| API 一致 | header bytes／適用後 transaction の API bytes | 静的比較で到達可能 |
| identity | SourceEvidence.src_token、include list、trace pair diff | preprocess で取得可能。新骨格は未作成なので値未確認 |
| abort 保存則 | stdout abort_counts／probe abort-call | 既存 stdout field は実在。新 probe は未作成 |
| commit 一回・abort 零回 | txn ごとの completion と hook event | 計装点は `T:706–712` に存在。専用焦点走は未実測 |
| 次 txn の state | 専用方策 epoch の before/after | 同 worker の継続列で構成可能。実 CC harness は未確認 |
| release 後取得・limit | release event、attempt、CAS success、limit-abort | 通常 YCSB で必ず到達するとは言えない。barrier fixture が必要 |
| clamp | requested/effective | UINT32_MAX 方策で構成可能。lock 側は conflict が別途必要 |
| 七要因 accuracy | record-site ID／AbortContext.reason | 七記録点は実在。YCSB では全値に到達不能。未発火分を緑にしない |
| norw verdict | verifier verdict/total_cycles | 既存 driver の field は実在。軸 ON×二方策の到達は未測定 |
| lockskip/early X | violations/x_reasons/verdict | 既存単一 thread fixture に前例。新骨格との組合せは未測定 |
| 機構 timeout | runner の timeout/reject reason | clamp/prefix は条件付き。事前の競合・prefix 取得証拠が必要 |

参照根拠は `D:186–284,323–343`、`C/s8a_trigger_coverage.py:274–311,388–416`、`C/s3_lock_coverage.py:293–312`、`C/s2_verify_calibration.py:411` です。新 probe field は**提案 schema**であり、実在済みと扱っていません。

残る重要点は次のとおりです。

- 実 CC の焦点 harness の初期化・link 構成が未確認。ここが C の最大の実装リスクです。
- `evaluate` の環境 authorization 構築、GeneratorId の選択・追加、関連 exact registry の全波及は未確認です。
- condition gate の共有変異 macro 案は source/case digest への束縛が前提です。八 patch の機構差は macro 名だけでは識別できません。
- 全 meta-test の網羅性と新 patch の実適用は未確認です。列挙済み項目を「全て」として完了判定しないでください。
- timeout・資源上限・node 時間は、異なる既存 workload の値を流用した暫定値です。DW-O13 の実測到達確認は親の実走で残っています。
- 無名仮引数を許すこと、七要因のうち実 CC 動的試験をどこまで作るかは実装前に固定すべき択一です。

## 総括

1. A：骨格 patch・API header・軸定数・template test を所有する。
2. B：専用 lexer/parser・TU compiler・UBSan・契約 fixture/test を所有する。
3. C：probe・負例・八変異・coverage/smoke・手書き方策・既存 registry/meta-test 更新を所有する。
4. 所有 path は分離し、共有の既存 file を B/A が並行編集しない。
5. 依存順は API/骨格仕様固定→A→B/C→統合静的検査→見積り確定→親の計算投入。
6. 既存 tokenizer の直接流用は避け、既存三軸の受理集合を保つ。
7. norw/lockskip は新骨格対応版、early-unlock は既存版を使う。
8. lockskip は既存どおり入口・保持の両 X を期待する。
9. 機構変異は相互排他的八 patch＋共通裸 macro 案を推奨する。
10. 単独 TU 自己試験は段を直接呼び、前段拒否による偽の検出力を避ける。
11. 生死確認は既存 evaluate、手書き対照は CLI opt-in の CODER_AUTHORED。
12. 残る択一は無名仮引数、焦点 CC harness の構成、七要因の動的実証範囲。
13. 計算小計は条件付き 1.111〜1.518 node h。未包含費用があり、投入総額は未確定。
14. 本回答は静的計画であり、patch 適用・build・試験合格・DW-O13 実測完了を報告するものではない。