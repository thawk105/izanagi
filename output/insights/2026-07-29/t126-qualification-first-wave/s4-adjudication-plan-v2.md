authority: none
default_effect: no-state-change

# T-126 qualification-first amendment — 段 4 裁定 / plan v2

## 結論

段 5 へ進む。planner plan v1 は NO-GO とし、敵対相談の real finding を反映した plan v2 へ
差し替える。ユーザー裁定 (a) は維持するが、旧 linux-baremetal の floor 内 pair を
「既知非再現 positive control」とは呼ばない。実 live run は統計主張を持たない
`historically-within-linux-floor observational smoke` とする。

formal への非交差は producer の名前だけで主張せず、Layer3 に qualification provenance の
明示拒否を追加する。一方、receipt は今 wave では evidence-only であり、
`hold_enforced=false` とする。production promotion / receipt hold consumer は別 wave のまま残す。

## 所見の裁定

| 所見 | 裁定 | 採否・scope |
|---|---|---|
| source WAL hash、中央値、+0.506556% が誤り | refuted | 親・planner・proof reviewer の再計算が一致 |
| SPRT Rmax=8 の OC が誤り | refuted | 独立全 256 系列列挙が一致 |
| same-boot で α/β を主張している | refuted | brief も plan も statistical claim を禁止 |
| 専用 layout で `pipeline.evaluate()` は機械的に実行不能 | refuted | duck-typed layout で実行可能。ただし capability hole は real |
| producer 側 marker だけで formal 非交差を保証できる | real / BLOCKER | Layer3 の qualification provenance 拒否を scope へ追加 |
| authority literal / private constructor が authorization proof になる | real | authority は説明 field。write boundary と consumer gate を load-bearing にする |
| receipt が現時点で machine-readable hold を解除する | real | `hold_enforced=false`、future input candidate に限定 |
| in-job receipt だけで scheduler 終端まで閉じる | real / BLOCKER | in-job result + post-job final/failure receipt の二相化 |
| historical floor 内 pair は Pegasus の既知非再現 control である | real / BLOCKER | observational smoke へ降格。期待と観測を分離 |
| linux-baremetal D19 3% を Pegasus floor と主張できる | real | borrowed qualification threshold、`statistical_claim=none` |
| empty numactl の狭い Pegasus 例外は実装不能 | refuted | fullscale lock と launch prefix を分離すれば可能 |
| empty numactl 例外が D36 / 共通受理集合に触れない | real | qualification opt-in だけの D96 境界変更として記録・検査 |
| proposed job prologue が Pegasus 既知依存を閉じる | real / BLOCKER | hardened dependency/perf/staging prologue を必須化 |
| walltime が全 subprocess / lock / verifier まで有限 | real / BLOCKER | process-group member cap と Wmax を exact 固定 |
| `settled=false` / S2 空振りを valid evidence が拒否する | real / BLOCKER | exact runtime evidence を admission に追加 |
| outcome 後の fresh attempt を resume=false が防ぐ | real | canonical attempt / retry gate を追加 |
| queue・budget・quota は現在確認不能 | refuted | 親実測: Active/Enable、86400秒、残407.05、quota余裕 |
| mutation 候補が単一理由性を満たす | real | 下記 matrix へ再登録 |

逐語は `.codex/dev-wave-t126-qualification-jobs/{plan,review-proof,review-stat}/output.md`。

## plan v2

### A. 純粋 contract と evidence-only schema

1. `orchestrator/qualification/` に T-126 専用 package と exact-key protocol JSON を新設する。
   pure SPRT、全系列 OC、canonical identity、balanced alternating order、single-process FSM を持つ。
2. threshold は `0.030` を保つが、field 名と receipt に
   `threshold_origin_env=linux-baremetal`、`pegasus_floor_calibrated=false`、
   `statistical_claim=none` を固定する。
3. terminal は `lower_boundary` / `upper_boundary` / `indeterminate`。別軸に
   `execution_integrity` と `expectation_match` を持ち、逆方向 floor 超を lower に潰さない。
4. synthetic sequence を pure core / parser / FSM / receipt の deterministic positive control にする。
   live pair は observational smoke で、観測結果自体へ pass/fail を付けない。

### B. namespace・proof closure・formal 非交差

5. qualification attempt は `output/env/pegasus/qualification/t126/` 配下だけへ書く。
   root-bound write capability を実際の append/open API の必須引数にし、generic writer を呼ばない。
6. event schema は formal WAL と非互換にし、generic `commit`、`campaign.lock`、formal
   `runs/wal.jsonl` を作らない。内部 evaluate の raw event は qualification marker と attempt root に
   閉じ、formal report の入力にしない。
7. Layer3 loader は、完全な campaign shape に見えても qualification marker / lineage があれば
   fail-closed に拒否する。通常の formal campaign を受理する正例も同じ境界テストへ置く。
8. source WAL / lock bytes を attempt へ snapshot し、元 repo-relative path・SHA-256・size を記録。
   superproject commit/tree、gitlink、protocol/schema、pipeline/verifier/buildcache modules、
   job script、toolchain、submission receipt を identity / closure に含める。
9. `authority` は説明 field に限定し、`evidence-only/no-promotion`、
   `hold_enforced=false` を exact 固定する。

### C. qualification driver と Pegasus

10. qualification opt-in に限り Pegasus contract の empty numactl を受理し、fullscale lock /
    admission は必須のまま launch prefix だけ空にする。legacy/formal caller の既存拒否は不変。
11. 各 member は process group 全体を `member_cap_s=900` で囲み、
    TERM → grace → KILL、子孫消滅確認を行う。`settled=true`、reps=5 / rc=0、
    `unstable=false`、legacy+S2 exact argv、commits>0、aborts>0、anomalies=0、
    trace/perf distinct binary manifest を evidence admission にする。
12. round order は seed で初回を決め、その後 alternating。任意 prefix の first-position 差を1以下にする。
    gap は前 round 第2 member terminal から次 round 第1 member start まで `round_gap_s=1800`。
13. policy は既存 `floor_walltime_s=36000` と別名の qualification 10時間枠を固定する。
    `Wmax = prologue 900 + 16*member 900 + 7*gap 1800 + attestation 600 + finalize 600
    = 29100 < 36000`。round 前に残時間を再検査する。
14. Pegasus job prologue は tracked-only `/scr` staging、pinned-clean gflags/glog build、
    functional perf candidate、Python版、attestation、persistent output を閉じる。
15. job 内は create-only `series-result.json` まで。終了後 collector が submission receipt、
    result / job-result、`.e/.o`、会計を閉じて final qualification receipt または failure receipt を作る。
16. first x 観測後・clean terminal 後の再投入を禁止する。x 未観測の pre-registered infra failure
    に限り最大1回 retry 可。pair 差替えは protocol version と新裁定を要する。
17. live submit 前に clean committed tree、queue Active/Enable、queue Max≥36000、
    budget / quota、submission receipt の実 FS 永続、`qstat` 可視性を親が再確認する。

### D. docs と受理集合記録

18. parent が統合 commit 前に次の空き D 番号で user ruling (a) と D96 の受理集合変更を記録する。
    qualification selector / receipt loader、Layer3拒否、Pegasus empty-numactl opt-in、
    observational outcome classifier、future hold consumer 不在を列挙する。
19. sequential-stopping design へ Rmax=8 OC と amendment の限定を追記し、phase / worklog と同 commit にする。
20. author worker はコード・テスト・実行 script だけを編集し、docs と commit は行わない。

## 変異事前登録

実装後に anchor の実在と前段 mask 不在を再確認し、単一 tracked 変更として走らせる。

| ID | 単一変異 | 変わる受理差分 | 唯一の期待赤理由 |
|---|---|---|---|
| M1 | SPRT x 判定 `rel > floor` を `>=` | exact floor が 0→1 | exact-floor boundary |
| M2 | Layer3 の qualification lineage 拒否を削除 | formal-shaped qualification が受理 | qualification provenance |
| M3 | source snapshot SHA 照合を削除 | tampered source snapshot が受理 | source hash mismatch |
| M4 | `settled is True` 条件を削除 | 外乱未静定 member が受理 | unsettled measurement |
| M5 | S2 exact evidence 条件を削除 | legacy-only / tag-only が受理 | missing exact S2 evidence |
| M6 | post-job accounting closure 条件を削除 | in-job result だけで final receipt | accounting missing |
| M7 | first x 後の retry 拒否を削除 | outcome-dependent retry が受理 | retry after observation |

過剰拒否 control は、通常 formal Layer3 campaign、clean lower / upper / indeterminate の3 terminal、
x 未観測 infra failure の許可済み1回 retry をそれぞれ受理する正例で固定する。

## 受入

- 新規 qualification / Layer3 / pipeline / Pegasus tool test
- 関連 campaign、env contract / attestation、Layer3、plain runner suite
- 上記 mutation matrix
- `bash -n`、`python3 tools/run_tests.py` 全走、Codex agent / docs 検査
- commit 後 provenance
- live job と post-job collector。clean unexpected outcome でも観測を改変せず receipt を保持する

