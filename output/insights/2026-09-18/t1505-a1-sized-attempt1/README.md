# [T-1505] A-1 balanced5 sized 本走 attempt-0001 — 投入・完走・受領証の記録 (2026-09-18)

- authority: none
- default_effect: no-state-change
- 裁定: D2120 項 3 (2026-09-17、択 (a) = 既存 submit 経路で 1 attempt を認可、落ちたら再投入せず報告して止める)。
- 対象 study: `paper-story-a1-20260901-balanced5-sized-v1` (policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`、sha256 `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`; 事前登録 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`、sha256 `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2`)。
- **本 wave は投入・待ち・complete・materialize・記録だけを行った。実装面の差分はゼロ (変異 matrix 免除)。** 事前登録・policy・source 契約・追補の bytes は変えていない。
- 成果物 (公開 leaf、policy の `materialization_relative_path`): `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (README.md / receipt.json / result.json / .complete.json、materializer が submit-tree に排他作成したものを byte 保持で複製)。
- この文書は記録であって、A-1 の充足・formal 化・昇格のいずれも判定しない (§6)。

## 1. 結論 (1 行ずつ)

1. **全層が実機で通った。** submit rc 0 (06:30 JST) → 3 job とも driver rc 0 / shell rc 0 / status `finished` (06:36〜06:43 JST) → complete rc 0 (06:44 JST) → materialize rc 0 (06:45 JST)。stdout / stderr はいずれも空、failure 受領証なし。
2. **3 workload とも `valid=true` / `errors=[]`、`complete=true` / `all_workloads_terminal=true`、各 30 対。** 6 arm の verifier は全て `serializable … 0 anomalies` (規律 2 の判定は既存 verifier のまま)。
3. **登録済み解析の分類は 3 workload とも `resolved-above-floor`** (B = baseline 平均の 3%)。符号は write-heavy 正、balanced 正、read-heavy 負。`variance_plan_breach` は 3 本とも false (標本 sd は計画 sigma の 0.70 / 0.97 / 0.85 倍)。
4. **これは `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` の非認証 lane の結果である。** workload をまたぐ結論は作らない (事前登録 §7.2)。
5. 再投入はしていない (認可は 1 attempt のみ)。sized の attempt はこの 1 本だけで、pilot の公開先には何も書き足していない。

## 2. 投入の形 (pilot attempt-0004 と同形、差は §2.2)

### 2.1 経路

- submit-tree: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1505-a1-sized-submit/submit-tree` = local main `d2ebef7a407dc6be61622ed596cf08b8b518f606` の detached worktree (着手直前の local main = origin/main)。submodule 再帰初期化、CCBench `511c9538e4e8efa54b45cda62e72389ed3b706ec` tracked-clean、`git worktree lock`。投入前・hydrate 後とも `status --porcelain --untracked-files=all --ignore-submodules=all` は 0 行。投入後は 1 byte も書いていない (materializer の出力だけが増えた)。
- 記録用 wave worktree (`.claude/worktrees/dev-wave-t1505-a1-sized-submit`、同じ SHA) と分離。
- hydrate (`tools/pegasus/fetch_third_party.py hydrate`、cache `/work/1/SFC/tanab/izanagi-thirdparty-cache`、5 本とも pin 一致): (a) submit-tree の既定 staging root `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` (gitignore 済み、job body が gflags / glog を読む既定 root)、(b) job dir `third-party-hydrated` (`--third-party-source-root`、job body が masstree / mimalloc / googletest を `cp -a` する root)。`verbatim/hydrate-default.json` / `verbatim/hydrate.json`。
- 起動 script (`run-hydrate.sh` / `run-submit.sh` / `run-watch.sh` / `run-stepc.sh` / `run-stepm.sh` / `detach.sh`) は実行可能 script なので repo へは複製せず job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1505-a1-sized-submit/` に残す。argv は以下に逐語で写す。
- submit (`run-submit.sh`、submit-tree を cwd に): `python3 -B -m orchestrator.campaign.paper_story_a1_paired submit --study-id paper-story-a1-20260901-balanced5-sized-v1 --expected-head d2ebef7a407dc6be61622ed596cf08b8b518f606 --attempt-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001 --third-party-source-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1505-a1-sized-submit/third-party-hydrated`。
- complete (`run-stepc.sh`): `python3 -B -m orchestrator.campaign.paper_story_a1_paired complete --study-id paper-story-a1-20260901-balanced5-sized-v1 --expected-head d2ebef7a407dc6be61622ed596cf08b8b518f606 --attempt-root <上の attempt root>`。
- materialize (`run-stepm.sh`): `python3 -B -m orchestrator.campaign.paper_story_a1_paired materialize --expected-head d2ebef7a407dc6be61622ed596cf08b8b518f606 --raw-result <attempt>/raw/results/result.json --raw-receipt <attempt>/raw/results/receipt.json --job-terminal <attempt>/raw/job-terminal.json --completion-receipt <attempt>/receipts/completion.json --destination <submit-tree>/output/insights/2026-09-13/paper-story-a1-balanced5-sized` (pilot attempt-0004 と同じ argv 形)。
- 監視 (`run-watch.sh`): 60 秒ごとに `qstat` 一覧の行頭 RequestID で 3 request の生存を見て、全消滅で終了 (`verbatim/watch.log`)。`qstat -f` の rc は生存述語にしていない。

### 2.2 pilot との差 (段 1 の provisional (P2))

pilot (2026-09-11) 時点の helper は FetchContent 3 本だけを hydrate し、gflags / glog は別経路だった。2026-09-16 以降の helper は 5 本を同じ staging root へ置く。本 wave は上の (a)(b) の 2 箇所へ hydrate した。差の判定は job 冒頭の dependency preflight (HEAD / dirty 検査) に委ね、自前の検査は足していない。結果、3 job とも preflight を通り bench に到達した。

## 3. 時系列 (JST、`date` / mtime / NQSV accounting から。推定値なし)

| 時刻 | 事象 | 出所 |
|---|---|---|
| 06:20:04 | wave worktree の submodule 初期化 | date |
| 06:24:21 | submit-tree 作成完了 (`.git` mtime) | mtime |
| 06:28:23 → 06:29:14 | hydrate 2 箇所 rc 0 | `hydrate.pid` / `hydrate.done` mtime |
| 06:30:16 → 06:30:38 | submit rc 0、intent (06:30:36) と submission 受領証 (06:30:38) | `submit.stdout` / `submission.json` mtime |
| 06:30:37 / 06:30:45 | 3 request 作成 / write-heavy・balanced 開始 (read-heavy は 06:31:13) | job.stderr の NQSV accounting |
| 06:32:45 / 06:32:47 / 06:33:15 | ready barrier (balanced / write-heavy / read-heavy) = 両 arm の build + verify 完了 | `barrier/ready/*.json` mtime |
| 06:33:15 | bench-start barrier 3 本同時 (最後の ready の直後) | `barrier/bench-start/*.json` mtime |
| 06:36:41 / 06:40:02 / 06:43:24 | job 終端 read-heavy / write-heavy / balanced (driver rc 0) | `jobs/<w>/job-terminal.json` mtime、NQSV `Ended Request Time` |
| 06:44:13 → 06:44:28 | complete rc 0 (group terminal + completion 受領証) | `stepc.*` mtime |
| 06:45:00 → 06:45:38 | materialize rc 0 (公開 leaf 4 file) | `stepm.*` mtime |

投入から全終端まで 13 分 (pilot 60 対は 24 分)。NQSV の Elapse は write-heavy 562 s / balanced 763 s / read-heavy 332 s。materializer の accounting は CPU 合計 9121.2 / 9121.1 / 9118.3 s、elapsed 553.96 / 755.30 / 323.80 s。

## 4. 3 job と受領証

| workload | request | node | intent 内 arm | verify (variant / baseline) | driver rc | scheduler terminal |
|---|---|---|---|---|---|---|
| write-heavy | `4939.nqsv` | bnode107 | fixed10 / no-backoff | serializable 0 anomalies (459238 commits) / 0 anomalies (544423 commits) | 0 | `request-disappeared-after-visibility` |
| balanced | `4940.nqsv` | bnode108 | fixed5 / no-backoff | 0 anomalies (516607) / 0 anomalies (515988) | 0 | 同上 |
| read-heavy | `4941.nqsv` | bnode109 | fixed2 / no-backoff | 0 anomalies (466561) / 0 anomalies (483318) | 0 | 同上 |

- submission 受領証: schema `paper-story-a1-paired-group-submission/v1`、route `direct-qsub-workload-fanout`、intent sha256 `7eb404861e9a5336c6169445885a7083c12f801ade5068e9b1ad09ad025a2750`、3 request とも投入直後の qstat 可視性 `QUE` / queue `gen_S`。
- completion 受領証: schema `paper-story-a1-paired-group-completion/v1`、group terminal `raw/job-terminal.json` sha256 `c46ae55cd9be5866956d5ffdefe5b86326de5899e8aa611725d6cf51631bbd15`。scheduler terminal は 3 本とも「投入時に可視、終端後に qstat から消失」形 (state / exit_status は未観測として記録、成功は driver_rc=0 / shell_rc=0 / status=finished で独立に確定)。
- 公開 leaf `.complete.json`: README.md `880919db73901d44ed3f8e6508239267d1acc15c2be997603edbe2b7c6db2d88`、receipt.json `a2039dc1457cf34828714a98955faf3df68d335c0442d144122686f4e177e930`、result.json `372f199e674cce28d46e2aeeed90b0f5b6c06e894bca63bcb779b580a8bb75a0`。publish 機構は `a1-exclusive-claim-check-then-renameat2` (RENAME_NOREPLACE が EINVAL の fallback、materializer が自ら限界を記録)。
- result.json: schema `paper-story-a1-paired-result/v3`、`policy_sha256` = 上の policy sha、`source_binding.evidence_level = source-routed-trace0` (artifact 単独の証明ではない)、束縛 file 9 本 (paired.py / v3-sized.json / a1_source.py / source v2 契約 / pipeline.py / calibrator runner / 追補 README / `patches/silo-backoff-fixed.patch` / job script)。
- 各 file の byte 数・mtime・sha256 は `MANIFEST.tsv`。複製は `receipts/` (intent / submission / completion / group terminal / 各 job terminal / barrier 6 本 / non-certifying observation / 各 job stdout・stderr)。campaign.lock / WAL は複製しない (原本 path は `receipts/non-certifying-observation.json` が sha256 付きで指す)。

## 5. 登録済み解析の出力 (materializer の README と result.json から逐語。descriptive のみ)

| workload | contrast | n | 対差平均 (variant − baseline) tps | 記述区間 tps | B tps (3%) | baseline 平均 tps | 標本 sd / 計画 sigma | 分類 |
|---|---|---:|---:|---|---:|---:|---|---|
| write-heavy | fixed10 − no-backoff | 30 | +1,591,948.50 | [1,568,036.997, 1,615,860.003] | 68,795.219 | 2,293,173.967 | 46,253.31 / 66,403.45 (0.70) | resolved-above-floor |
| balanced | fixed5 − no-backoff | 30 | +448,830.17 | [420,478.567, 477,181.766] | 115,876.896 | 3,862,563.200 | 54,842.03 / 56,697.44 (0.97) | resolved-above-floor |
| read-heavy | fixed2 − no-backoff | 30 | −576,749.77 | [−609,713.465, −543,786.068] | 310,204.402 | 10,340,146.733 | 63,763.47 / 74,668.49 (0.85) | resolved-above-floor |

- k = 2.8315526875186725 (df 29)、`h = k · s / sqrt(30)`。分類は policy の `classification_rules` (`abs(mean) − h > B` → resolved-above-floor) による。**事前登録 README §5.2 の語 (`resolved-beyond-floor (improvement / regression)` / `bounded-within-floor`) と policy / 実装の語 (`resolved-above-floor` / `bounded-below-floor`) は異なるが、述語は同値** (`L > B` または `U < −B` ⟺ `abs(mean) − h > B`)。向きは平均の符号で読む: write-heavy と balanced は improvement 側、read-heavy は regression 側。これは観察であり、本 wave では何も直していない。
- 派生値 (登録量ではない、読み手の目安): 対差平均 / baseline 平均 = write-heavy +0.694、balanced +0.116、read-heavy −0.056。符号は C1 (D496 以前の旧環境、+38.3% / +11.3% / −6.6%) と 3 workload とも一致するが、**再現判定ではない** (推定対象・環境・分母の処理が異なる。D1993 / L23 の区別を維持)。
- pilot の観測値は最終推定へ 1 点も入っていない (`sizing_inputs` の pilot は反復数の決定にだけ使われた)。

## 6. 言わないこと

- **A-1 の充足・formal 化・昇格は判定しない。** policy は `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` のままで、これは事前登録・policy の編集だけで反転させない (事前登録 §7.2)。「A-1 の値がある」と書けるかどうかは、この非認証 lane の結果をどう位置づけるかの裁定に属し、本 wave の scope 外。
- **性能の優劣を主張しない。** 上の表は登録済み解析の descriptive 出力であり、workload をまたぐ結論・headline 値・再現判定にはしない。
- **再投入の判断をしない。** bench 開始後の失敗も性能値も再投入理由にならない (事前登録 §6.4)。本 attempt は落ちていないので再走の要否は生じていない。
- **submit-tree と耐久 base は本 wave では撤去しない** (原本の所在。撤去は別途の掃除判断)。

## 7. A-1 状態欄 (`docs/paper-story/…` §8 の A-1 項) が本記録から書ける事実

- 「本走未投入・認可据え置き」→ **「D2120 項 3 (2026-09-17) が 1 attempt を認可し、attempt-0001 を 2026-09-18 に投入、3 workload とも `valid=true` / `errors=[]` で完走した (job `4939` / `4940` / `4941`、各 30 対、source `d2ebef7a4`)」**。
- 「試験運転専用の分岐を外す実装が閉じたことを記録する着地済みの正典は無い」→ entry 1590 (commit `ad83b108b`) が着地済みで、本 attempt は sized の全層 (submit / job preflight / 依存 build / 条件関門 / 両 arm build+verify / bench / complete / materialize) を実機で通した。
- 登録済み解析の出力: 3 workload とも `resolved-above-floor`、符号は +/+/−、`variance_plan_breach=false`。**非認証 lane (`formal=false`) のまま**である。
- 一次資料: `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (公開 leaf) と本 dir (受領証・時系列)。

## 8. 段の記録 (dev-wave 軽量版)

- 段 1 brief = `verbatim/brief.md`、段 4 裁定 = `verbatim/adjudication.md` (実装しない、子ゼロ、変異免除)。段 2・3・5・6 は省略 (設計択一なし・防壁に触れない・受理集合不変)。
- 実測は親 (submit / 監視 / complete / materialize)。codex 子は 0 本。
- 受入全走は記録 commit 後の tip で 1 走 (結果は land の受領証)。
