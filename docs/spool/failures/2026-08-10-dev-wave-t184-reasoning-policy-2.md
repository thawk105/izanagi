---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t184-reasoning-policy
seq: 2
---

## 再発

### F57

- **再発: 2026-08-10 ([T-184] 受入全走)。** bnode021 の全走 (7,864 件、request `898552.nqsv`、
  1316.27 秒) で `test_codex_worker_launch.py::test_late_rollout_writer_does_not_change_sealed_receipt`
  が 1 件落ちた (1 failed / 7843 passed / 20 skipped)。同一 checkout の単独再走は
  1 passed / 3.35 秒 で再現しない。当該 wave の差分は **docs のみ**で launcher 実装・同 test file へ
  到達しえず、`DW-O18` により帰属しない。**新しい情報が 2 つある。** (1) 失敗の様態が従来の
  `assert 1 == 0` / returncode 不一致ではなく、`failed_predicates=["process_group_residual",
  "termination_verified"]` という**終了検証側の述語 2 本の不成立**だった
  (`codex_exit_code=0` / `validator_rc=0` / `evidence_status='complete'` /
  `metering_status='complete'` はすべて正常で、`wall_clock_s=0.0994` は上限 3 秒に対し十分小さい)。
  (2) 失敗時の `runtime_context` に `loadavg=(15.05, 3.57, 1.18)` が記録されており、
  **1 分平均だけが突出した瞬間負荷**の下で発火している。これは「wall 上限の超過」ではなく
  「高負荷下で子 process group の終了確認が期限内に観測できない」機序を示唆する。
  従来の再発記録は returncode 系に偏っており、述語側の不成立は本件が初出である
### F154

- **再発: 2026-08-10 ([T-184] reasoning policy wave)。3 例目、かつ 2 例目と同じ file・同じ機構族。**
  親 brief は `DW-S05-A` の `reasoning=high` を `tools/check_docs.py` の pin 閉包へ加える計画を
  (P2) として立てたが、**この拡大はちょうど [T-667] が「見送りで終端」と裁定済み**だった
  (「`DW-S05-A` の `high` と `DW-S06-B` への pin 拡大はしない」、防御的堅牢化・D205 既定)。
  裁定は `docs/archive/worklog-phase3-0809-330-331.md` にしか無く、親の brief 前検索は
  対象タスク ID ([T-184] / [T-181] / [T-183]) と decisions の索引までで、
  **本 F の恒久対応が既に要求している「対象機構名で archive まで意味検索する」を行わなかった**。
  D223 も同じ拡大を却下していたが、こちらは段 2 のプラン子が見つけた。
  検出は再び段 3 の敵対レンズで、**2 本が独立に到達し 2 本とも NO-GO** を返した。
  消費は codex 子 3 本 (段 2 プラン 1 + 段 3 敵対 2)。
- **新しい情報 1: 見送り裁定に再訪条件が付いており、親はそれを実測できた。**
  [T-667] の再訪条件は「当該節の drift の実測」である。親が `docs/dev-wave/workers.md` を含む
  全 19 commit (2026-07-24 `2cd329d5` 〜 2026-08-08 `f9e2756e`) を走査したところ、
  当該節の effort 抽出値は一貫して `reasoning=high` のみで **drift は 0 件**、
  再訪条件は成立しなかった (`DW-S02` / `DW-S03` も `max` 不変)。
  従来の再発記録は「見送り裁定の存在に気づく」段までしか書いていないが、
  **気づいた後に再訪条件を実測して成立/不成立を確定する**段がある。これを行わないと、
  見送りが恒久なのか条件付きなのかを親が判断できず、ユーザーへ返す問いも曖昧になる。
- **新しい情報 2: 見送り裁定の本文自体に事実誤りがあり、誤った安心を与える。**
  [T-667] の項は括弧書きで「`DW-S05-A` は D207 の pin が別途ある」と書くが、**これは誤りである**。
  D207 は prose 規定だけで pin を持たない (D223 が「実測すると `check_docs.py` に `reasoning` の
  出現は 0 件で、規定は prose だけだった」と明記している)。実在する pin は D223 のもので、
  対象は `DW-S02` / `DW-S03` の `max` に限られる。したがって段 5 の値は**機械防壁の外にある**。
  見送り裁定を読んだだけの後続 wave は「別の pin が守っている」と誤読しうる。
  台帳は凍結 archive にあるため本文は訂正せず、本項と
  `output/insights/2026-08-10_t184-reasoning-policy-adoption.md` を訂正の正本とする。
- 再発検知: 変更なし。本件も段 3 の敵対レンズが捕まえた (`DW-S03` の
  「親 brief 自身も攻撃対象」)。本 F の既存の恒久対応で足り、新しい手順は足さない
