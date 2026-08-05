# T-399 判定の事前登録 — 実測前凍結 (2026-08-04)

- `authority: none`
- `default_effect: no-state-change`
- 本文書は probe 投入前に凍結する。実測後に本文書の判定式・語彙・閾値を変更しない。
  変更が必要になった場合は erratum を別ファイルで追記し、初回判定を消さない (DW-M02 と同型)。

## 判定語彙 ((149) の規約を継承)

- 観測されなかった signal は `UNKNOWN` と記録し、`SIGKILL` と断定しない
- signal 名を断定できるのはスケジューラ自身の明示出力 (`%NQSV(INFO): ... signal <NAME>`)
  または signal handler の受信記録 (exact signum) がある場合だけ
- `qwait rc=9` は「walltime limit による終端」の証拠であり、signal 種別の証拠にしない

## 捕捉可能性の判定 (leg 別)

- **mitigation leg** (`--accept-sigterm=yes`, `elapstim_req="00:03:00,00:02:00"`,
  `--warning-signal=elapstim:SIGTERM`): 「production-like Python handler へ捕捉可能な構成が
  存在する」と結論できるのは、authoritative attempt (observation_valid ∧ terminal_proven) で
  次がすべて成立した場合だけ:
  1. Python parent 層に exact `SIGTERM` の受信記録 (`signal_abort_caught`) がある
  2. その受信が request・attempt nonce へ束縛されている
  3. cleanup 列が完走し (`finally_exit`)、observer の独立 readback で canary = `ORIGINAL`
  4. 終端が正常終了 (walltime kill でない) — qwait rc=0 側の安全終端契約
- **split-warning leg** (SIGUSR1 錨): Bash trap のみの捕捉は「warning 経路の存在証拠」に
  とどまり、単独では T-360 条件 1 の充足にならない (production launcher は Bash trap を残さない)
- 危険側 (capture 失敗): scheduler 明示出力の SIGKILL + 3 層無受信 + canary `MUTATED` は
  「mitigation 構成でも捕捉不能」という authoritative な危険結論として採用する
- いずれの leg も、上記のどちらにも当てはまらない観測は `UNKNOWN` とし、
  「捕捉可能」「捕捉不能」のどちらの結論にも使わない

## grace の読み方と十分性

- 構成上の nominal grace (PBS bytes から固定): mitigation = 180−120 = **60 s**、
  split-warning = 180−60 = **120 s**
- `first_expected_signal` の定義 (mode 別、いずれも **Python parent** の monotonic_ns event):
  mitigation = warning **SIGTERM** の受信 event。split-warning = warning **SIGUSR1** の
  受信 event。Python parent に受信 event が無い mode (Bash trap のみの捕捉) では
  grace を測定せず、「warning 経路の存在証拠」のみとする
- `cleanup_elapsed = finally_exit − first_expected_signal` (両 event とも Python parent)
- **`G_usable_lower` の代入規則 (一意、固定)**:
  - cleanup が完走した attempt (`finally_exit` event が存在): `G_usable_lower :=
    cleanup_elapsed`。これは「実際に使えた時間の下限」であり、nominal 値や
    survival 時間でこれを置き換えない
  - cleanup 未完 (`finally_exit` 不在): `G_usable_lower := UNKNOWN`。
    `post_signal_survival_lower_bound = last_post_signal_heartbeat − first_expected_signal`
    は**診断値としてのみ**記録し、十分性の式へ代入しない。heartbeat 由来値 (どの層でも) を
    usable grace や exact kill 時刻へ昇格しない。grandchild heartbeat は下限記録のみ
- heartbeat も event も無い区間は `UNKNOWN`
- **十分性の判定式 (固定)**: `G_usable_lower ≥ 5 s + 5 s + R_restore_bound`。
  `G_usable_lower = UNKNOWN` または `R_restore_bound = null` なら十分性は `UNKNOWN`。
  `R_restore_bound` = mutation_harness `_restore_targets` (書戻し + pycache purge + byte 検証)
  の上限で、**本 wave では未実測 = null**。したがって本 wave の結論は
  「捕捉可能な構成の有無」までとし、production harness への十分性は `UNKNOWN` と記録する。
  同一 raw から十分性が true/false の両方に読める余地を残さない — 代入規則は上の 2 分岐だけ

## retryable infra reason (閉じた enum、これ以外で再投入しない)

- `qsub_rc_nonzero` (投入自体が失敗し request が生成されていない)
- `qstat_permission_error` / `qstat_transient_error` (lifecycle 観測の欠落) —
  ただし raw に signal 安全性の内容 (signal event / canary 状態) が既にある attempt は
  理由を問わず置換 retry 禁止。初回 raw は常に保存し、後続 attempt で上書きしない
- `queue_deadline_reached` (RUN に入らず QUE deadline 到達、controller が bounded qdel 済み)
- per-leg attempt cap = **2** (初回 + 再試行 1)。session 全体は既存上限
  (6 request / 40 node-min) を超えない
- `attempt_safe=false`、`accounting_available=false` のみ、`UNKNOWN` 判定は retry 理由にしない

## 投入手順 (runbook §8 準拠) と回収

1. 事前: `qstat -Q`、`pegasusinfo`、`check_quota`、`rbudgetcheck` (すべて rc=0 を記録)。
   walltime = 各 leg 180 s + scheduler 側 margin (PBS 記載値)、node 数 = 1 (`-b` 指定なし単 node)、
   OMP/hybrid 非該当 (probe は Python + bash のみ、48 thread 制約に非接触)。
   **controller の実行場所分類は §7.0 の実測手続に従う**: 未計測 command を login で
   走らせない義務と「測定は login 上で command を走らせて行う」という §7.0 の手続を、
   次の形で両立させる — (i) `resolve` を §7.0 の systemd-run scope + busy sampler で
   3 回以上測り、certified peak (観測ピーク + max(25%, 128 MiB)) < 512 MiB を先に確認する。
   (ii) `run --signal-legs-only` の**初回実行そのものを §7.0 測定手続として行う**:
   同じ scope + sampler に加えて **`-p MemoryMax=512M` の hard cap** を掛け、超過時は
   kernel が controller を止める (fail-closed — 未知の重さが login node を侵食する経路を
   構造的に閉じる)。観測 peak・cap・繰り返し数・commit・argv は §7.0 の記録義務どおり
   本 wave の RESULT へ残し、certified peak が 512 MiB 以上なら以後の login 実行を止めて
   dispatch 設計をユーザーへ返す。controller は qsub を発行するため計算ノードへは移せない。
   probe 側の単独性は fresh root + nonce 束縛 + compute marker (hostname/jobid) で担保する
2. `resolve` (migration 含む) → rc=0 を確認 → `run --signal-legs-only`
3. 追跡: controller の表示する session ID / request ID / attempt ID / state 行を
   handoff (`/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-t399-t400-signal-mitigation.md`) へ
   逐次転記する
4. `run` が非 0・例外・terminal-unproven で終わった場合: **再投入せず** `resolve` を 1 回だけ
   実行して終端実証を試み、それでも未解決なら fail-closed のまま停止して worklog へ記録する
5. crash して evidence staging に届かない場合の凍結先: 外部 root
   (`/work/1/SFC/tanab/izanagi-jobs/3a7f810a/probe-runs/<leg>/<attempt>/`) と
   controller transcript を `output/insights/2026-08-04_t399-t400-signal-mitigation/evidence/`
   へ read-only コピーする (改変せず、コピーである旨を README に記す)
6. RESULT 固定パス: `output/insights/2026-08-04_t399-t400-signal-mitigation/RESULT.md`。
   判定は本文書の式へ機械的に当てはめ、逸脱があれば判定せず erratum を書く
