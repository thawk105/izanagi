---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: stranded-branch-recovery-20260823
seq: 3
---

## 新規

### {{F:codex-evidence-gate-rejects-valid-output}}. codex launcher の evidence 検査が、同一 prompt で再現的に妥当な成果物を不採用にする [検査の偽陰性]

- 事象: 回収 wave が read-only の監査子を 6 本立てたところ、そのうち 1 本 (`b1`) だけが
  `outcome=not_accepted` / `stop_reason=max_attempts` で終わり、成果物が publish されなかった。
  lane を変え prompt の末尾を変えて計 3 回投入したが、3 回とも同じ形で落ちた。
  同じ launcher で走った他 5 本は 5 本とも `accepted` だった。
- 落ちた位置: `tools/codex_worker_launch.py` の `_evidence_status()` が
  `evidence_status="invalid"` を返し、`launcher_rc=1` になる。
  ただし `validator_rc=0` であり、`tools/check_codex_output.py` の採用条件
  (`## 総括` を含む形式) は 3 回とも満たしていた。出力は 3,874 / 4,232 / 4,892 bytes の
  実体を持ち、3 回とも同じ結論と同じ blocker を独立に述べていた。
- 規模との相関は無い: 不採用 3 本の input token は 728,508 / 1,578,448 / 1,786,564、
  採用 5 本は 332,362 / 1,268,823 / 1,590,941 / 1,871,059 / 2,067,641 で、
  最大の走行は採用されている。`recorded_turn_context_count` はいずれも 1。
- 根本原因: `_evidence_status()` は rollout の妥当性を 6 条件の論理和で `invalid` に畳み、
  どの条件が成立したかを receipt にも diagnostics にも残さない。判定は launcher の内部状態
  (`AttemptState.rollouts`) だけに依存し、`validator_rc=0` で採用条件を満たした成果物であっても
  publish を止める。畳んだ結果しか外へ出ないため、親には再投入以外の手が無い。
- 影響: 妥当な子の成果物が失われる。契約 (`DW-O01`) は launcher が採用しなかった成果物を
  「未完了」として扱うことを求めるので、同じ prompt で何度投げても採用が得られない場合、
  その監査面は独立コンテキストの証拠を持てない。本 wave では判定が `do-not-land`
  (安全側) だったため、親が決定的な主張 1 件を自分で裏取りして先へ進んだ。
- 恒久対応: 未着手。`_evidence_status()` が `invalid` を返した理由 (`stdout_invalid` /
  `stdout_pending` / rollout の `invalid` / `pending` / `session_meta_count != 1` /
  `context_count < 1` のどれか) を receipt か diagnostics へ出すようにするのが先である。
  現状はどの条件で落ちたかが成果物から判別できず、再投入以外の手が無い。
- 再発検知: 不採用時の receipt に、`_evidence_status()` が観測した各条件の値を記録し、
  同一 prompt の連続不採用を親が判別できるようにする ({{T:codex-evidence-gate-diagnostics}} 参照)。
