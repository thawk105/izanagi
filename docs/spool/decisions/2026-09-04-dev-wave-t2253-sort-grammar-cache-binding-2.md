---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-04
wave: dev-wave-t2253-sort-grammar-cache-binding
seq: 2
---

## {{D:sort-contract-binding-without-entry-gate}}. sort 軸の契約束縛は単一 producer と binder のドメイン分離だけで閉じ、入口 gate と public seam の拡張は足さない

**決定:** D1548 の局所適用は、(1) `p3_s4_loop_sort.py` の単一 producer `_require_sort_oracle_contract(cfg)` が
campaign 宣言と実行中の `ORACLE_CONTRACT_ID` の exact 一致を identity 束縛より前に要求すること、(2) `run_campaign` /
`evaluate` / `resolve_evidence` / `build` / `build_v2` / `_recheck_source_evidence` の keyword-only 引数 (既定 `None`)、
(3) `source_digest` の sort 専用 binder (preimage `sort-src-token/v1\0contract=<id>\0source=<digest>`) と backoff 版との
相互排他、の 3 点で閉じる。`loop.run_campaign` 入口の三者 gate、`loop.py` への `sort_swo_oracle` import、
`resolve()` / `src_token()` の public seam への引数追加は実装しない。driver 側の `sort_swo_oracle` 参照も関数内 import にする。

**理由:**
- 単一 producer が `layout.ensure()` と WAL 作成より前に照合する限り、入口 gate が無いことで変わる in-scope の成果物は無い。
  gate が守るのは producer を迂回して `run_campaign` を直接呼ぶ経路だけで、repo にその caller は無い。
- `loop.py` は全 campaign の共通経路であり、`sort_swo_oracle` は import 時に `inspect.getsource` を実行して失敗を
  fail-closed にする。import を足すと sort を使わない campaign まで import 段階で止まりうる。driver の module-level import も
  B-4 launcher など driver を先に読む経路へ同じ失敗面を広げるので、関数内 import に限る。
- 段 5 sort loop の実経路は `resolve_evidence → _resolved_src_token` であり、`resolve()` / `src_token()` は通らない。
  局所適用の原則に従い、実経路外の seam へは引数を足さない。
- 相互排他 (両方非 `None` → `ValueError`) は binder を選ぶ `_resolved_src_token` の 1 箇所に置く。登録済み producer は
  片方しか渡さないので受理集合は変わらない。

**却下した選択肢:**
- `run_campaign` 入口の三者 gate (backoff の `loop.py` gate の写し) — 仮想リスク向けの防壁新設に当たり、import の失敗面も広げる。
- `SORT_IR_GRAMMAR_VERSION` (int) を既存の `backoff_grammar_version` 経路へ流す — backoff の gate が module 定数と照合するので
  両立せず、corpus / checker / TU template の改版で contract ID が変わっても IR 版だけ据え置きのとき旧 binary を再利用する。
- `resolve()` / `src_token()` まで引数を足す — 実経路外で、変更面と変異の owner を不要に広げる。
