---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t726-pickaxe-epoch
seq: 3
---

## 新規

### {{F:duplicate-dev-wave-job}}. 同一タスクの背景 job が 2 本、同じ worktree と job dir を共有した [手順漏れ]

- 事象: 同じ [T-726] の `/dev-wave` を受け取った背景 job が 2 本同時に走り、
  `EnterWorktree` の名前が同じだったため一方が他方の worktree を resume した。両者が同じ
  job artifact dir を使い、handoff を相互に上書きした。上書きされた側は当初これを
  「外部からの内容混入」と判定して規律 6 の anomaly として扱っており、原因究明に時間を使った。
  同じ計測 (最大 package preflight) を 2 本が独立に計算ノードへ投入する重複も起きた
  (36.467 秒と 36.527 秒。値自体は 0.06 秒差で整合した)。
- 根本原因: wave slug が worktree 名・branch 名・job dir 名の唯一の識別子であり、
  **タスク ID から機械的に決まる**。同じタスクを 2 回起動すると必ず衝突する。
  `EnterWorktree` は既存名を resume する仕様で、これ自体は正しい動作である。
  起動時の 3 点検査 (`tools/check_wave_startup.py`) は local main との乖離・handoff の実在を
  見るが、**同じ worktree を他 process が使用中かは見ない**。
- 恒久対応: memory `dev-wave-duplicate-job-collision` — handoff が自分の書いた内容と違ったら
  外部混入と断ずる前に重複起動を疑い、`pgrep -af <worktree path>` と worktree lock 保持者を見て、
  後着が撤退する。機械化 (`tools/check_wave_startup.py` に「同一 worktree path を argv に持つ
  生存 process が自分以外に居ない」の fails-closed 検査を足す) は
  {{T:wave-startup-detect-duplicate-job}} として起票した。
- 再発検知: 起動直後に handoff の内容が自分の書いたものと異なることを検出したら、
  外部混入と断ずる前に `pgrep -af <worktree path>` と `git worktree list` の lock 保持者を見る。
  今回は先方からの cross-session message で原因が判明した。
