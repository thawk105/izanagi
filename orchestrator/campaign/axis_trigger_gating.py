# -*- coding: utf-8 -*-
"""silo-backoff-trigger-gating 軸の軸定数ブロック (C 段成果物、D48 必須条件 5)。

axis-onboarding §1 脚注 / §7.2 の「軸定数ブロック」— D 偵察器と E 段 loop driver の
**両方がここから import する**単一の正本。sort 軸の現物 (偵察器 `s6_sort_sweep.py` が
E 段 driver `p3_s4_loop_sort.py` を import する歴史的経緯) は踏襲しない (D48/
axis-onboarding 敵対レビュー must-fix)。軸定義の全文はシート insight
(`output/insights/2026-07-10_s8a-stage-b-sheet-backoff-trigger-gating.md`)、採用条件は
D48 が正本 — ここには機械が消費する定数だけを置き、設計判断は書かない。

**偵察 firewall (D48 必須条件 7、axis-onboarding §3-D):** D 偵察 (機械 sweep) の
insight には勝ち点の具体実装・順位が載る。**E 段の coder/planner 入力に流してよいのは
軸の生死二値 (floor 超地形の有無) のみ** — 偵察の具体勝ち点・要因部分集合・順位・
シートの診断数値リテラルを leakproof_context / planner direction / whiteboard に
入れてはいけない。シート自体も coder 入力の材料にしない。偵察 insight を見た事実は
campaign provenance に情報源として記録する (D46 決定 1 のループ版)。
"""
from __future__ import annotations

from . import pin

# ---- identity 核 (D 偵察器 / E 段 driver 共通) ----
MARKER_ID = "silo-backoff-trigger-gating"
SOURCE_REL = "cc/silo/transaction.cc"
TEMPLATE_PATCH = "silo-backoff-trigger-gating-variant.patch"
PREDICATE_HOLE_INDENT = "  "
FROZEN_TEMPLATE_HOLE_BYTES = b"  izanagi_gate_pass = true;"
FROZEN_TEMPLATE_ABORT_HEAD_BYTES = (
    b'void TxExecutor::abort() {\n'
    b'  // remove inserted records\n'
    b'  for (auto& we : write_set_) {\n'
    b'    if (we.op_ == OpType::INSERT) {\n'
    b'      Masstrees[get_storage(we.storage_)].remove_value_if_present(we.key_);\n'
    b'      delete we.rcdptr_;\n'
    b'    }\n'
    b'  }\n'
    b'\n'
    b'  gc_records();\n'
    b'\n'
    b'  read_set_.clear();\n'
    b'  write_set_.clear();\n'
    b'  node_map_.clear();\n'
    b'\n'
    b'#if BACK_OFF\n'
    b'#if ADD_ANALYSIS\n'
    b'  std::uint64_t start(rdtscp());\n'
    b'#endif\n'
    b'\n'
)
FROZEN_TEMPLATE_ABORT_TALLY_BYTES = (
    b'#if BACKOFF_TRIGGER_GATING && TRACE\n'
    b'  // izanagi (Phase 3 stage 8a, D48/AUD-4): abort-reason tally -- verification-\n'
    b'  // only instrumentation (characterization patch, NOT part of the axis\n'
    b'  // skeleton). Emits one "A <reason>" line per abort so the coverage driver\n'
    b'  // can cross-check recorded reasons against ADD_ANALYSIS counters and prove\n'
    b'  // the misattribution mutation turns red. Lives in a separate patch layered\n'
    b'  // over the skeleton for characterization runs only: baking it into the\n'
    b"  // template patch would make the variant's TRACE=1/TRACE=0 preprocess diff\n"
    b"  // diverge from pinned HEAD's and trip assert_trace_diff_matches_head\n"
    b'  // (\xe8\xa6\x8f\xe5\xbe\x8b1 \xe4\xb8\x80\xe6\xac\xa1\xe9\x98\xb2\xe5\xa3\x81) on every loop evaluation. All 7 skeleton stores happen\n'
    b'  // before abort() is entered (status_ is set at the abort decision point;\n'
    b'  // the run loop then calls abort()), and nothing inside abort() writes the\n'
    b'  // reason, so the value emitted here is exactly what the gate below reads.\n'
    b'  {\n'
    b'    static const char* const izanagi_abort_reason_names[] = {\n'
    b'        "unset",           "lock-conflict", "update-absent", "readvali-tid",\n'
    b'        "readvali-locked", "node-vali",     "insert-node",   "scan-node"};\n'
    b'    izanagi_trace::stream(thid_)\n'
    b'        << "A "\n'
    b'        << izanagi_abort_reason_names[static_cast<unsigned>(\n'
    b'               izanagi_abort_reason_)]\n'
    b"        << '\\n';\n"
    b'  }\n'
    b'#endif\n'
)
FROZEN_TEMPLATE_PROLOGUE_BYTES = (
    b'#if BACKOFF_TRIGGER_GATING\n'
    b'  // izanagi skeleton (D48): gate scaffold. The predicate variable and the\n'
    b'  // gated call below live OUTSIDE the EVOLVE-BLOCK markers = coder-\n'
    b'  // untouchable (DiffQuarantine outside-region). Initial true = stock\n'
    b'  // default (back off).\n'
    b'  bool izanagi_gate_pass = true;\n'
    b'#endif\n'
)
FROZEN_TEMPLATE_BLOCK_BYTES = (
    b"  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
    b"  // izanagi Phase 3 (D48/phase3.md): this conditional-compilation skeleton\n"
    b"  // is the coder (LLM) edit surface -- ONLY the single assignment in the\n"
    b"  // branch selected when BACKOFF_TRIGGER_GATING >= 1 (the gate predicate).\n"
    b"  // Contract (D48 decision 2): the predicate may read the\n"
    b"  // IzanagiAbortReason enum and compile-time constants ONLY; straight-line,\n"
    b"  // side-effect free (reason recording is the skeleton's exclusive domain).\n"
    b"  // Explicitly forbidden reads: thid_ (per-thread priority gate = fairness\n"
    b"  // hack), result_ counters (adaptation to the run's own fitness signal),\n"
    b"  // read/write/node containers (cleared above -> silent degeneration).\n"
    b"  // kUnset must map to true (stock fallback -- fail-safe sentinel\n"
    b"  // contract). Closed-region constraint (D23 route Y): no #include\n"
    b"  // changes, no new functions/types/globals/macros, no raw preprocessor\n"
    b"  // directives, no nondeterministic builtins (this comment avoids raw\n"
    b"  // tokens so marker scanning does not false-positive).\n"
    b"#if BACKOFF_TRIGGER_GATING\n"
    b"  izanagi_gate_pass = true;\n"
    b"#else\n"
    b"  Backoff::backoff(FLAGS_clocks_per_us);\n"
    b"#endif\n"
    b"  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
)
FROZEN_TEMPLATE_EPILOGUE_BYTES = (
    b"#if BACKOFF_TRIGGER_GATING\n"
    b"  if (izanagi_gate_pass) {\n"
    b"    Backoff::backoff(FLAGS_clocks_per_us);\n"
    b"  }\n"
    b"#endif\n"
)
FLAG = "BACKOFF_TRIGGER_GATING"          # cmake CACHE = CCBENCH_BACKOFF_TRIGGER_GATING
PIN = pin.CURRENT_PIN                    # 511c953 — 骨格は patch のみ (PIN 前進なし、D48 決定 2)

# hole は `#if BACK_OFF` ブロック内に居るため BACK_OFF=1 の明示が必須 (D48/F6 —
# Options.cmake の CACHE 既定への暗黙依存を避ける、D43 と同じ理由)。
_BASE = {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
         "NO_WAIT_OF_TICTOC": 0, "WAL": 0, FLAG: 1}

# ---- characterization 資材 (C 段、положitive control。E/F 段では使わない) ----
# 計装 (A 行 tally) は characterization 専用の重ね当て patch — template patch に
# 入れると diff-of-diffs (assert_trace_diff_matches_head) と衝突する (driver docstring)。
INSTR_PATCH = "instr-silo-backoff-trigger-gating-tally.patch"
MISATTR_PATCH = "broken-silo-trigger-misattr.patch"
MISATTR_DEFINE = "IZANAGI_BREAK_TRIGGER_MISATTR"   # 裸マクロ (CCBENCH_ 外、規律 2)

# ---- 要因 enum のミラー (骨格 IzanagiAbortReason と同順。計装 A 行の語彙) ----
REASON_NAMES = ("unset", "lock-conflict", "update-absent", "readvali-tid",
                "readvali-locked", "node-vali", "insert-node", "scan-node")

# 偵察の列挙空間の根 (シート「偵察の列挙空間」欄): gate 可能な実要因 5 種の部分集合
# = 2^5 = 32 点。退化点 = 空集合 (全素通し = 真の BACK_OFF=0 相当)、stock 対照 =
# 全集合 (全要因で backoff)。insert-node / scan-node は YCSB 不発 (coverage で実証、
# s8a_trigger_gating_coverage.json の structural_zero) のため列挙から除外 — D 段の
# 必須前提 1 (要因別頻度の事前実測で不感ビット確定) はこの実測を出発点に再確認する。
GATEABLE_REASONS = ("lock-conflict", "update-absent", "readvali-tid",
                    "readvali-locked", "node-vali")

# ---- 構文契約 (D48 決定 2)。E 段 coder 定義・auditor 目視の転記元 (必須条件 4) ----
# gate 述語が読めるのは骨格の要因 enum (IzanagiAbortReason) とコンパイル時定数のみ。
# straight-line・副作用なし (要因記録への書込は骨格の専権)。kUnset (sentinel 未記録)
# は true (= stock: backoff する) に写す fail-safe 契約。
# 明示禁止 (読んだら auditor 型 16 / チェックリスト 13 で reject):
SYNTAX_CONTRACT_FORBIDDEN = (
    "thid_",        # per-thread 優先 gate = fairness hack (ギャラリー型 15 系)
    "result_",      # run 自身の fitness 信号への適応 = 入力隔離の破れ (型 12 系)
    "read_set_",    # gate 点では clear 済み (abort() 冒頭) — 空コンテナの silent 縮退
    "write_set_",
    "node_map_",
)
