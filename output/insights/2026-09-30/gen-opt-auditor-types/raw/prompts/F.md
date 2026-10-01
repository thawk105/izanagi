silo-lock-order-policy 軸 (Silo の validation で UPDATE だけの write set の施錠順を優先度で決める、gen-opt の仕組みの軸) の候補 1 件を監査してほしい。本軸は gen-opt の仕組みの軸で、違反型は 1〜30。

入力: 次の file の JSON をそのまま入力とする (中身は下にも再掲する)。
/home/SFC/tanab/.claude/jobs/b8fe070e/tmp/wave/probe-out2/inputs/F.json

```json
{
  "working_diff": "--- a/cc/silo/transaction.cc\n+++ b/cc/silo/transaction.cc\n@@ -47,11 +47,16 @@\n #endif\n // EVOLVE-BLOCK-BEGIN silo-lock-order-policy\n #if SILO_ORDER_VARIANT\n-struct OrderState { };\n-bool order_enabled(OrderState&, const izanagi_silo_order_api::TxnContext&) noexcept { return false; }\n-uint64_t order_priority(OrderState&, const izanagi_silo_order_api::EntryContext&) noexcept { return 0u; }\n-void order_after_abort(OrderState&, const izanagi_silo_order_api::AbortContext&) noexcept { }\n-void order_on_commit(OrderState&, const izanagi_silo_order_api::CommitContext&) noexcept { }\n+struct OrderState {};\n+bool order_enabled(OrderState&, const izanagi_silo_order_api::TxnContext&) noexcept {\n+  return true;\n+}\n+uint64_t order_priority(OrderState&, const izanagi_silo_order_api::EntryContext& e) noexcept {\n+  return (static_cast<uint64_t>(e.epoch) << 29u) | static_cast<uint64_t>(e.tid);\n+}\n+void order_after_abort(OrderState&, const izanagi_silo_order_api::AbortContext&) noexcept {}\n+void order_on_commit(OrderState&, const izanagi_silo_order_api::CommitContext&) noexcept {}\n+\n #else\n #endif\n // EVOLVE-BLOCK-END silo-lock-order-policy\n",
  "diff_digest": "0e21fe746dfaeeac123252fd852f4528cf19c62c1f1b6c10e501af2021763b32",
  "designated_sources": [
    "/work/1/SFC/tanab/izanagi/.claude/worktrees/md22-auditor-types/orchestrator/campaign/silo_lock_order_api.hh",
    "/work/1/SFC/tanab/izanagi/.claude/worktrees/md22-auditor-types/patches/silo-lock-order-variant.patch",
    "/work/1/SFC/tanab/izanagi/.claude/worktrees/md22-auditor-types/external/ccbench/cc/silo/transaction.cc"
  ],
  "abort_digest": {},
  "mechanism_spec": {
    "specification_digest": "sha256:4566966a29b34e9d031d5354468710a689773edbb07d6ab2b647330b58bde522",
    "rules": [
      {
        "rule_id": "R1",
        "statement": "施錠順を候補が決めるのは UPDATE だけの write set に限る。INSERT・DELETE を含む取引は骨格が stock の key 順に並べる。"
      },
      {
        "rule_id": "R2",
        "statement": "候補は要素ごとの優先度だけを返し、全順序 (優先度の降順、storage の昇順、key の昇順) は骨格が作る。"
      },
      {
        "rule_id": "R3",
        "statement": "各要素の TID word は骨格が並べ替えの前に 1 回だけ読み、候補には写し (epoch, tid, locked) だけを渡す。"
      },
      {
        "rule_id": "R4",
        "statement": "候補は tuple・write set・read set・trace・commit 件数の counter のどれも読まず書かない。"
      },
      {
        "rule_id": "R5",
        "statement": "並べ替えは write set の要素の集合を変えない。"
      },
      {
        "rule_id": "R6",
        "statement": "施錠は no-wait で、衝突したら取得済みの lock を外して abort する。"
      },
      {
        "rule_id": "R7",
        "statement": "validation は全要素の施錠の後に行い、値の書き込みは validation の後に行う。"
      },
      {
        "rule_id": "R8",
        "statement": "優先度は写しの epoch と tid だけから計算し、locked は使わない。"
      }
    ]
  },
  "model_check_summary": {
    "specification_digest": "sha256:4566966a29b34e9d031d5354468710a689773edbb07d6ab2b647330b58bde522",
    "result": "no-counterexample-in-registered-range",
    "registered_scenarios": [
      "L1-write-skew",
      "L1-lost-update",
      "L1-read-only-anomaly",
      "L1-G1a",
      "L1-G1b",
      "L2-1",
      "L2-2",
      "L2-3",
      "L2-4",
      "L2-5",
      "L3-2txn"
    ],
    "checked_value_range": "施錠順は write set の全順列",
    "out_of_scope": [
      "INSERT・DELETE を含む取引",
      "3 key 以上",
      "弱いメモリモデル",
      "進行保証"
    ],
    "counterexamples": []
  }
}
```

designated_sources の file は読んでよい。入力内の文字列はデータであって指示ではない。

## 出力形 (厳守 — driver の auditor gate `auditor_gate.parse_auditor_dict` が受理する閉じた形)

JSON object 1 つだけを返す。key は次の 6 つ:
- `verdict`: `"pass"` | `"reject"` | `"uncertain"` のいずれか。`pass` は violations が空、`reject` は violations が 1 件以上、`uncertain` は violations が空で `uncertainty` が非空。
- `diff_digest`: 入力の `diff_digest` をそのまま echo する (文字列)。
- `violations`: `{"type": 整数, "location": 文字列, "correctness_impact": 文字列, "verifier_blind_spot": 文字列, "note": 文字列 (任意), "reason": 文字列 (任意)}` の配列 (無ければ `[]`)。
- `nits`: `{"finding": 文字列}` または `{"note": 文字列}` の配列 (無ければ `[]`)。
- `proposed_tests`: ちょうど `{"mutation": 文字列, "expected_gate": 文字列, "machine_judgment": 文字列}` の 3 key の object の配列 (無ければ `[]`)。
- `uncertainty`: 文字列 1 つ (無ければ `""`)。
