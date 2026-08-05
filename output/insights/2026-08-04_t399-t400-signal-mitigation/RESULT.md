# T-399 実測結果 — mitigation 構成は捕捉可能、十分性は R_restore_bound 待ち (2026-08-05 確定)

- `authority: none`
- `default_effect: no-state-change`
- 判定は `verdict-preregistration.md` (+ erratum-1, erratum-2) の凍結式への機械的当てはめ。
  可変状態の正本は worklog。

## 判定入力 (authoritative attempt)

- session `20260804T125421Z-5e03df98c93b444e`、**t362-mitigation attempt a1**
  (request `887918.nqsv`、`--accept-sigterm=yes`, `elapstim_req="00:03:00,00:02:00"`,
  `--warning-signal=elapstim:SIGTERM`)
- authoritative 化の経路: 初回評価は旧 evaluator が会計欠測 (racct の
  `sudo: パスワードが必要です` = permission gate、T-401 の実発火) を観測無効へ誤変換して
  非 authoritative。fix6/7 (欠測と完全性違反の分離、cross-field 不変条件、staged raw からの
  決定的再評価経路) の後、`resolve` の再評価 (新規 qsub なし、旧評価は
  `superseded_evaluation` に保存) で `observation_valid=true ∧ terminal_proven=true`。
- split-v2 値: `observation_valid=true`, `probe_cleanup_outcome=safe`, `unsafe_reason=none`,
  `termination_cause_consistent=true`, `attempt_safe=null` (衛生項: 費用取得と observer
  停止時刻の非終端。safety 帰属とは分離済み), `accounting_available=false (permission)`

## mitigation の捕捉可能性 — 条件 1〜4 の当てはめ

1. Python parent の exact SIGTERM 受信 + `signal_abort_caught` — **成立**
   (events-parent: signal +118.929 s → signal_abort_caught +118.931 s)
2. request・attempt nonce への束縛 — **成立** (identity/束縛検査を含む observation_valid=true)
3. cleanup 完走 + observer 独立 readback で canary `ORIGINAL` — **成立**
   (finally_enter +118.932 s → canary_restore_verified +123.942 s → finally_exit +123.943 s、
   `probe_cleanup_outcome=safe`)
4. walltime kill でない自発終了 (erratum-2 の操作化) — **成立**
   (scheduler `.e`: `signal SIGTERM` [SIGKILL でない]、`Elapse: 134S / Remaining Elapse: 46S`、
   `finally_exit` 存在。qwait rc=9 は警告配送の反映であり判定に不使用)

**結論: 「production-like Python handler へ捕捉可能な signal と grace を与える構成が存在する」
= 成立。** D139 決定 (4) の未解決問い (mitigation 構成の捕捉可能性) は肯定側で決着した。
危険側の凍結条件 (scheduler 明示 SIGKILL + 3 層無受信 + canary MUTATED) は不成立。

## grace と十分性 (凍結式)

- nominal grace = 180 − 120 = 60 s (構成上)
- `first_expected_signal` = +118.929 s (Python parent の SIGTERM 受信 event)
- cleanup 完走のため `G_usable_lower := cleanup_elapsed = 5.013 s`
  (内訳はほぼ TERM wait 5 s + 復元/検証)。これは「実際に使った時間」の下限であり、
  凍結規則により nominal 60 s や walltime までの残余 61 s へ昇格しない
- `R_restore_bound = null` (未実測) → **十分性 = UNKNOWN** (凍結式
  `G_usable_lower ≥ 5 + 5 + R` は判定保留)。「捕捉可能な構成の有無」までが本 wave の結論

## split-warning (診断 leg)

attempt a1 (request `887919.nqsv`) は **非 authoritative** (`observation_valid=false`、
`termination_cause_consistent=false`)。safety 側の生値は `unsafe /
post_restore_canary_mismatch` — SIGUSR1 は Bash trap に届いたが Python parent は保護されず
canary は `MUTATED` のまま。凍結どおり split-warning 単独は T-360 条件 1 の充足にならず、
非 authoritative のため verdict は `UNKNOWN` と記録する (per-leg cap は a2 を 1 回残す)。

## §7.0 記録 (controller の login 実行)

systemd-run scope + busy sampler + `MemoryMax=512M`。観測 peak: resolve 22 / 17 / 17 / 44 MiB、
run 53 / 29 MiB。certified peak = 53 + 128 = **181 MiB < 512 MiB → local-ok**。
commit = 本 wave の HEAD、argv = `resolve` / `run --signal-legs-only`。

## T-360 (変異本走の計算ノード束ね) への含意

- D130 条件 1 (裁定=択(a)) ✓、条件 4 (T-363) ✓、条件 2 (flock) = D140 の確定保留のまま
  ([T-402])、**条件 3 (signal) = 捕捉可能構成の実在を実証、十分性は [R_restore_bound の実測]
  を残す**。mutation_harness の cleanup 下限 約 10 秒 + 復元に対し、warn margin (60 s) は
  構成で拡大可能 (`elapstim_req` の warn 値は自由) であり、設計上の障害は残っていない。
  着手可否はユーザー裁定 (D131 前提 6 点 + D105 supersede を伴う次 wave)
