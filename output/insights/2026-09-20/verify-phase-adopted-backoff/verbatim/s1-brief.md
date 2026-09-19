# 段 1 brief — 採用候補 2 genome の検証相 (独立 8 反復 × 3 workload、長 extime、trace-enabled) を Pegasus で通す

作成 2026-09-19 22:05 JST。wave `dev-wave-verify-phase-adopted-backoff`、worktree base = local main `657e1e5a7`、ccbench pin `511c9538`。

## 研究前進 (1 行)
論文の A-2 / T-1998 結果節が持つ正しさ証拠は「trace-enabled 別走 1 回 (legacy 条件) + performance 側 5 回 (A-2)」に留まる。本 wave は事前登録済みの検証相 (phase3-main-experiment (iv 付属): N_verify = 8 独立反復 × 3 workload、長 extime、規律 2 の全数 anomaly ゼロ) を採用候補 2 genome に通し、results 系列稿 1 本で「操作的事実として独立反復 n=8 × 3 workload で anomaly ゼロ (または失格)」を書けるようにする。完了判定 = 候補ごとに 24 verify の verdict が全件記録され pass/失格が確定、校正値が日付付きで記録され、insight + results 稿 + worklog/decisions fragment が land 済み。

## 確定済みユーザー裁定 (2026-09-19、依頼文)
対象 = T-1998 事前登録の採用 arm と A-2 observed-positive の固定 backoff 値。各候補 N_verify = 8 独立反復 × 3 workload (計 24 verify)。total 予算 ≤ 4 時間/候補、超過見込みなら extime を下げ N_verify は削らない。24 verify すべて anomaly ゼロで pass、1 件でも anomaly なら失格。長 extime は trace-enabled build で extime {3, 6, 10} s の verify 所要を較正し 1 verify ≤ 10 分に収まる最大値。trace-enabled build と性能 build を分ける (規律 1)。verifier = `python3 -m orchestrator.verifier`。seed identity と trace の保全先 (job dir) を記録。形式的信頼度 1−εⁿ は主張しない。24 verify を複数ノードへ同時投入。成果 = 検証相の記録 insight と results 系列稿 1 本。scope 外 = 新 protocol・追加 gate・certification の昇格。

## 対象候補 (一次資料から確定)
| 候補 | genome (silo、共通 `NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`、`BACKOFF_NOINLINE=0`) | 出所 | 期待 identity |
|---|---|---|---|
| fixed-5 | `BACK_OFF=1, BACKOFF_FIXED=5` | T-1998 事前登録 §2/§5 target = A-2 rr50-fixed5 (同一 genome) | T-1998 `source_bytes_sha256` `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` (patch 適用下、`cxx="g++"`)、A-2 `src_token` `21def77c944b…` |
| fixed-10 | `BACK_OFF=1, BACKOFF_FIXED=10` | A-2 rr5-fixed10 (observed-positive 稿 §1・§2.1) | A-2 `src_token` `955b452a332d…` |

pin `511c953`、patch `patches/silo-backoff-fixed.patch` 適用下で build。workload 3 = write-heavy (rr5) / balanced (rr50) / read-heavy (rr95)、共通 `ycsb_tuple_num=1000000, thread_num=48, ycsb_zipf_skew=0.9, ycsb_rmw=0, ycsb_max_ope=10, clocks_per_us=2100` (A-2 policy v2 `performance_common`、entry 1681 と同じ動作点)。「seed×N」= 独立 N 反復 (ycsb は CLI seed を持たない。phase doc「seed×N の操作的定義」)。

## 前提の実測と新事実
- entry 1681 (Pegasus bnode041、現行 verifier): read-heavy 3 s trace-enabled = 17.13M commit、verifier CLI 421.7 s、maxrss 43.95 GiB。node DRAM 128 GiB (上限約 115 GiB)。→ read-heavy は 3 s が上限見込み、6 s は ≈ 88 GiB で完走見込みだが 600 s 超見込み。
- **新事実 (裁定時の未見、段 4 で再裁定):** `docs/phase3-main-experiment.md` は `output/s1-freeze/known_axes_freeze.json` の source sha256 として凍結され、`verify_document` が照合する。1 行追記の模擬 → `FreezeError: source sha256 不一致` (historical 両モード)。凍結文書 raw sha は `t080_freeze_migration.KNOWN_AXES_RAW_SHA256` に pin、`IZANAGI_FREEZE_HOLD` は解除 = ユーザー明示命令のみ。**本 wave では phase doc への「日付付き追記」は成立しない。**
- 既存被覆: 検証相の実走記録は decisions / worklog / failures に無し (2026-07-16 の校正のみ、cygnus)。純増。関連 peer `[bfe104]` は同 arm の性能退行 (別 build・別成果物)。
- 計算ノードは外部 net 不在 (hydrate staging 必須)、既定 python3 は 3.9 (`python3.10` 明示)、同一 worktree からの dispatch は直列 (job ごとに detached submit-tree)。gen_S QUE 12 / RUN 29 @21:50。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- **(P1) extime の決め方:** 候補ごとに 1 値。各 (候補, workload) で {3, 6, 10} を昇順に各 1 回 trace run + verifier 実走し、verifier wall > 600 s で残候補を打ち切り (07-16 と同じ規則、`s1_verify_extime_calibration.choose_extime` を流用)。候補の extime = 3 workload すべてで ≤ 600 s を満たす最大値。次に見込み総所要 (Σ_w 8 × 校正実測 (bench+数え直し+verifier) + job 固定費) が 4 h を超えるなら 1 段下げる (3 s が床、N_verify は不変)。代案 = workload 別 extime。
- **(P2) 校正確定値の記録先:** phase doc へ追記せず、決定 fragment (D) + insight README + results 稿に日付付きで記録し、phase doc (iv 付属) への追記は凍結束縛の解除後の別 wave へ送る (理由と模擬結果を D に書く)。凍結文書の再発行・hold 解除は本 wave で行わない。
- **(P3) 校正走の verdict の扱い:** 校正で完走した verifier の verdict も規律 2 の対象 (anomaly → 当該候補は失格、検証相本走へ進めない)。hard timeout (1800 s) / OOM で verifier が完走しない校正走は `indeterminate` として記録し、その extime 以上を打ち切る (anomaly でも pass でもない。丸めない)。
- **(P4) 投入形:** 段 A = 校正 6 job (候補 2 × workload 3、各 node 1 本、走行内で 3→6→10 直列)。親が extime を書面で確定してから段 B = 検証 12 job (候補 2 × workload 3 × 2 job、各 job 4 反復直列)。各 job は detached submit-tree から generic dispatch、node-local `/scr` に checkout・build・trace、完了前に job dir へ回収。
- **(P5) trace の保全:** 全 verify の trace 原本を job dir `run/` へ保全 (zstd -T0 圧縮、圧縮前後 sha256 と bytes・行数を記録。zstd 不在なら非圧縮)。verifier JSON・bench stdout・計時・identity (resolve_evidence の `src_token` / `source_bytes_sha256`、binary sha256、python3.10 realpath、repo HEAD、verifier module 群 sha) を verify ごとに記録。

## 不変条件
- 規律 1: trace-enabled build の bench 値を性能主張に使わない (throughput は記録するが results 稿では「性能値ではない」と明記)。規律 2: verifier の verdict をそのまま採り、昇格・降格・解釈を足さない。verifier の受理集合・引数意味論に触れない。規律 7: 07-16 の cygnus 校正・A-2/T-1998 の既存 certified 記録を無効にしない (併記)。
- 1−εⁿ を主張しない。24 verify の判定は「anomaly ゼロ」の操作的事実として書く。
- N_verify = 8 は削らない。extime の床は 3 s。結果を見た後に extime・N・判定規則を変えない (校正と判定規則は段 4 で書面確定してから段 B を投入)。
- 凍結成果物 (`output/s1-freeze/**`、T-1998 事前登録 bytes、A-2 権威 bytes) に触れない。

## 成果物の形
- repo: `output/insights/2026-09-19/verify-phase-adopted-backoff/README.md` (+ `verbatim/` に brief・plan・consult・ruling・review・runner source の逐語)、`docs/paper-story/results/2026-09-19-verify-phase-adopted-backoff.md` (+ `docs/paper-story/README.md` results 表 1 行)、`docs/spool/worklog/…`、`docs/spool/decisions/…` (P2 の記録先裁定)。
- job dir: `probe/verify_phase_runner.py` (Codex author、sha256 で同定、repo に入れない)、`run/calib/<cand>-<wl>/`、`run/verify/<cand>-<wl>-<job>/`、`s4-ruling.md` (extime 確定を含む)。
- 実装面 (repo 内) の差分ゼロ → 変異 matrix 免除 (`DW-S04`)。受入全走は免除しない。

## 変更面 (実アンカー)
| path | 種別 | 扱い |
|---|---|---|
| `docs/phase3-main-experiment.md` | 凍結 source (known_axes_freeze) | **触らない** (P2) |
| `docs/paper-story/results/2026-09-19-verify-phase-adopted-backoff.md` | 新規 (append-only 系列) | 親が書く |
| `docs/paper-story/README.md` results 表 | docs | 1 行追加 |
| `output/insights/2026-09-19/verify-phase-adopted-backoff/**` | 新規 insight | 親が書く |
| `docs/spool/{worklog,decisions}/…` | fragment | 親が書く |
| job dir `probe/verify_phase_runner.py` | 実装面 (repo 外) | Codex author |

## 分割方針
段 2 plan 1 本 (read-only codex) → 段 3 敵対相談 2 本 (レンズ A = 事前登録・規律 1/2/7 と自由度の混入、レンズ B = 実行計画の実在性・資源・失敗の形) → 段 4 裁定 → 段 5 author 1 本 (runner) → 親が login selftest → 段 A → 段 4 追補 (extime 確定) → 段 B → 段 6 review 2 本 (runner + 走行記録 + README・results 稿の独立検算) → fix → 段 7。

## DW-G05
放置時: 採用候補の正しさ証拠が legacy 1 回 + 5 回 (A-2) のまま results 稿に「検証相未実施」と書き続ける。本 wave は certified 選択・台帳の値を変えず、候補の検証相 pass/失格という新しい事実を results 系列へ足す (失格なら当該候補は規律 2 で無価値と記録)。
