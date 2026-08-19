---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1115-env-bytecode-check
seq: 1
---

## 新規

### {{F:checker-shallow-tuple-unpack}}. 新設 checker の1-hop 関数解決が tuple-unpack 代入を追跡できず fix が2巡した [手順漏れ]

- 事象: `tools/check_subprocess_bytecode_guard.py` の P2 判定 (`_one_hop_guard`) は
  `env = f()` 形の単純代入だけを1段辿って guard を探す。local main 取り込みで
  `orchestrator/tests/test_dev_wave_wait.py` に他wave由来の新規呼び出しが加わり、
  その `env` は `repo, lease, env = _real_waiter_repo(...)` という tuple-unpack
  代入で得ていた。1回目の fix は呼び出し先 `_real_waiter_repo()` 内部の env dict へ
  guard を足したが checker はなお rc=1 を返し続けた。
- 根本原因: checker の `_FileIndex.visit_Assign`
  (`tools/check_subprocess_bytecode_guard.py:208-219`) は
  `len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)` の場合だけ
  代入を索引する。`ast.Tuple` をターゲットに持つ tuple-unpack 代入はこの条件を満たさず
  索引から漏れるため、`_one_hop_guard` が呼び出し先関数まで辿る前提(代入の右辺が
  ローカル関数呼び出しであること)自体が成立しなかった。
- 恒久対応: 部分的。2回目の fix で、呼び出し元関数 (`_run_real_self_report_merge_case`)
  自身の scope に `env["PYTHONDONTWRITEBYTECODE"] = "1"` を直接追加し、
  `_scope_has_guard` (同一関数内の文字列 literal 探索) で guard ありと判定される形にした。
  **checker 自体の tuple-unpack 追跡は実装していない** — 汎用 data-flow 解析は
  規律5に反するため、既知の shallow 判定の限界として残す
  ({{D:subprocess-bytecode-guard-scope}} の却下した選択肢を参照)。
- 再発検知: 無し (checker の恒久対応が部分的なため、同型の tuple-unpack 代入を持つ
  将来の env= 呼び出しは、呼び出し元関数自身に guard が無い限り同じ2巡を要する)。
  `tools/check_subprocess_bytecode_guard.py` の module docstring に
  「1-hop 関数解決は単純代入のみ対象、tuple-unpack は対象外」を追記する改善は
  次に同checkerへ触れる wave の候補とする。
