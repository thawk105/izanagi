---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t567-attempt-binding
seq: 1
---

## {{D:attempt-bound-verify-bench-signals}}. verify_done/bench_done を実行 attempt ID に束縛し、consumer は committed attempt record だけを投影する

**決定:**

1. `verify_done` / `bench_done` の WAL record は、その record を生んだ実行 attempt の ID
   (`build_attempt_id`) を payload に持つ。`pipeline.py` の `_run_bench()` は
   `build_attempt_id` を keyword-only 必須引数として要求し、`verify_payload` /
   `bench_payload` へ伝播する。
2. `wal.py` の `_validate_attempt_topology()` は、`verify_done` / `bench_done` を active
   attempt との一致で検証する。variant 単位ではなく attempt 単位で判定し、対象 variant の
   record が active attempt に属さない場合 (別 attempt、build_done より前、finished 済み
   同一 variant の別 attempt 等) は `AttemptTopologyError` で拒否する。
3. `wal.py` に `replay_admitted_records()` を新設し、committed (受理済み) attempt の record
   だけから `EvalState` (`committed_attempt_id` / `committed_build_start` /
   `committed_verify` / `committed_bench`) を構成する純粋関数として提供する。`replay()` は
   これを呼ぶ形に整理する。
4. consumer (`digest.py` の `load_workload()` / `load_verify_abort_signals()`) は committed
   projection だけを見て評価対象を決める。`build_attempt_id` を持たない legacy WAL は、
   既存の variant 単位ロジックへフォールバックする。
5. D193 の recovery-abort・noncertifying semantics 自体は変更しない。

**理由:**

- crash→retry や遅延 receipt (別 attempt の verify_done/bench_done が後から届く) が起きると、
  古い attempt の成功 record が新しい attempt の評価に混入しうる。これは certified 選択・
  proof chain 付き material report が誤った証拠に基づく事態であり、規律2 (正しさゲートを
  緩める変異を許さない) に対する静かな穴になる。
- D193 は attempt の終端化 (recovery-abort) だけを定め、生き残った attempt の評価をどの
  record から構成するかは規定していなかった。本決定はその隙間を、record 生成側
  (pipeline.py)・検証側 (wal.py)・消費側 (digest.py) の3層で塞ぐ。
- consumer 側の post-hoc フィルタでなく WAL replay 層で committed projection を作る設計に
  したのは、consumer が増えるたびに同じ attempt 束縛ロジックを再実装させないため。

**却下した選択肢:**

- variant 単位のまま最新の verify_done/bench_done を常に採用する — crash→retry で古い
  attempt の成功が新しい attempt の評価に混入する (本 wave の negative fixtures が再現する
  脆弱性そのものであり、規律2 を緩める)。
- consumer 側 (digest.py) だけで attempt_id をフィルタし、WAL replay 層は素通しのままに
  する — consumer が増えるたびに同じフィルタを重複実装することになり、1箇所の実装漏れが
  cross-attempt splice を静かに通す。
- 古い attempt の record を WAL から物理的に削除・書き換える — WAL の append-only 性
  (正しさ検証の再現可能性) を壊す。
