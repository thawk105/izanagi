## 実装した内容

所有範囲に次を作成しました。

- `orchestrator/campaign/silo_policy_grammar.py`
- `orchestrator/campaign/silo_policy_compile.py`
- 契約 fixture 85 本と `manifest.json`
- grammar／compile の test 2 file、計 20 node

固定 interface、無名仮引数、専用 lexer、再帰下降 parser、部分式の型・lvalue・const・literal・symbol 情報を実装しました。

| §2.7 の規則 | 主な規則 ID |
|---|---|
| 代替綴り、digraph | `lex.alternative-token`、`lex.digraph` |
| 予約識別子、先頭 `::`、禁止字句 | `lex.reserved-identifier`、`lex.global-qualifier`、`lex.forbidden` |
| 整数の接尾辞・範囲 | `lex.literal-suffix`、`lex.integer-range` |
| State の個数・メンバ数・初期値 | `decl.state` |
| constexpr、記憶域 | `decl.constant`、`decl.storage` |
| 関数署名・noexcept・宣言名 | `decl.function`、`decl.name` |
| 名前・メンバ解決、自己呼出し禁止 | `name.resolve`、`call.dag` |
| 局所宣言、自己初期化 | `decl.local`、`init.self` |
| 禁止文・演算子 | `stmt.forbidden` |
| 最終 return、switch の閉鎖 | `return.final`、`switch.closed` |
| 算術、比較、変換、引数、return | `type.numeric`、`type.conversion` |
| 条件式、min/max | `type.branch`、`type.minmax` |
| divisor・shift の literal 制約 | `rhs.literal` |
| 独立文への代入限定、代入先 | `assignment.statement`、`assignment.target` |
| その他の構文逸脱 | `syntax.expected` |
| 入力・token・再帰深度制限 | `limit.source`、`limit.tokens`、`limit.depth` |

未実装として残した規則はありません。ただし全規則の test 実走・変異による検出力確認は未了です。

compile 側には、絶対 path の API include、指定 argv、環境変数除去、compiler 選択、rlimit、process group の停止、有界診断、UBSan harness と CLI を実装しました。

## 確認の実測

| 確認 | 結果 |
|---|---|
| 新規 Python 4 file の `py_compile` | rc=0 |
| 手書き 6 方策の `check_policy_body` | 全件 grammar／compile 受理、CLI rc=0 |
| 骨格 patch の hole 既定本文 | grammar／compile 受理、CLI rc=0 |
| fixture 全件への `validate_policy` | **85/85 一致**。受理21、拒否64。不一致なし |
| fixture 全件の直接単独 TU compile | **85/85 一致**。受理64、拒否21 |
| 外部名6種の TU 単独 compile | 全件 rc=1 |

外部名6種は `Masstrees`、`FLAGS_thread_num`、`TRACE`、`izanagi_trace::record_lock`、`rdtscp`、`GlobalEpoch` です。grammar 単独でも全件 `name.resolve` で拒否しました。

compiler は **g++-12 (Ubuntu 12.3.0-1ubuntu1~22.04.3) 12.3.0**。UBSan CLI は **rc=0、`all_pass=true`** でした。

- 正常6方策：各 **1,904 呼出し**、rc=0、UBSan 報告なし。
- 全8要因 × attempt 0〜33 を、`abort→lock→commit→lock→abort` と `abort→abort` で駆動。
- 零除算・過大 shift・signed overflow：個別子 process で各 rc=1、UBSan 報告あり。
- `focus.cpp` は確認時点ではありませんでした。実装は全 `.cpp` を列挙します。

以下の test node はすべて **実装済み・未実走**です。test module の import・実行はしていません。

`orchestrator/tests/test_silo_policy_grammar.py::`

```text
test_manifest_grammar_contracts
test_manifest_first_rejection_stage
test_hand_policies_and_default_grammar
test_grammar_rejects_alternative_binary_tokens
test_grammar_rejects_bool_arithmetic
test_grammar_rejects_self_initialization
test_grammar_requires_final_return
test_grammar_rejects_subexpression_assignment
test_grammar_requires_literal_divisor
test_grammar_limits_are_candidate_rejections
test_grammar_internal_errors_propagate
```

`orchestrator/tests/test_silo_policy_compile.py::`

```text
test_manifest_compile_contracts
test_hand_policies_and_default_compile
test_compile_rejects_external_global
test_compile_rejects_unsupplied_macro
test_compile_unavailable_and_grammar_short_circuit
test_compile_timeout_kills_process_group
test_compile_diagnostic_bound
test_compile_environment_isolation
test_ubsan_harness_real_execution
```

## 現行の受理・拒否挙動と波及

既存 tracked file の差分はありません。専用 lexer を新設し、既存 grammar・effect gate・DiffQuarantine・oracle は変更していません。既存 caller も接続していないため、既存軸の受理集合は変えていません。

所有外への波及は次のとおりです。

- **C1**：smoke から `check_policy_body` を呼び、拒否・例外・timeout・unavailable で build を止める接続が必要です。
- **C2**：`test_ccbench_spawn_sites.py` の `_EXPLICIT_NON_CCBENCH_PROCESS_SITES` に、`("campaign/silo_policy_compile.py", "<module>._run"): 1` の分類追加が必要です。
- **consumer test**：4段経路と build の接続、検査本文／materialize 本文の digest 一致は C1/C2 側に残ります。
- **共有 fixture**：変更なし。新規 manifest の閉集合確認は新 test 内にあります。
- **自走 harness**：両 test file に追加済み。既存 plain-runner meta-test 自体は未実走です。

## 未了と疑問

- 4段経路の最初の拒否段を照合する test、timeout cleanup、環境除去、診断上限、compiler 不在の test は未実走です。
- `%:define` は manifest で段1 `content-directive` と登録しました。今回の直接確認を段3だけの検出力証拠には数えていません。
- 指定名の変異 kill-point test は実装しましたが、変異 matrix は未実走です。KILLED は主張しません。
- 自己初期化3例と今回の fallthrough 本文は `-fsyntax-only` では受理されました。manifest はその実測に合わせ、grammar の拒否期待は維持しています。
- 巨大 literal の境界正例は U64 戻り型にし、U64→U32 変換は変数経由の独立した正例にしました。

## 総括

単位 B の実装と指定された直接確認を完了しました。fixture は grammar／TU とも **85/85 一致**、正常6方策と既定本文は受理、UBSan 正常群・負例群は期待どおりです。

test 20 node と変異試験の実走は親へ引き継ぎます。docs・所有外 tracked file・git index／履歴は変更していません。`.scratch-t2857-b/` は削除済みです。