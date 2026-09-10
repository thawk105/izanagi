# [T-1981]/[T-088] 消費済み 12 cell を実機で測り直せた (request 964035.nqsv)

## 要約

2026-08-24 の床値 pilot (request `945229.nqsv`) が一回性 key を消費した 12 cell を、
D1124 / D1190 の撤去が着地した local main (`2bf9cf387`) から**そのまま測り直せた**。
[T-1981] の残件だった「消費済み 12 cell が再測定を妨げない」ことの実機証明が取れ、
床値の実測値も得た。

同じ課題を別 session が独立に立ち上げていたため、床値 job が 7 秒差で 2 本走った
(964035 = 本 run、964044 = 並行 run)。**両方とも完走した。** その結果、
「2 つの測定世代が同じ 12 cell を同時に保持する」状態を実機で観測できた。

## 合格条件 (前 wave の凍結済み事前登録をそのまま適用)

正本 = `output/insights/2026-08-27_t1981-holdout-oneshot-removal/verbatim/s4-adjudication.md` §6-C。
**緩めていない。** `floor-driver/run-linked` は build と予約より前に出るので合格条件にしない、
という同節の注意も守った。

| # | 条件 | 判定 | 証拠 |
|---|---|---|---|
| 1 | `already consumed` 系の拒否が出ない | PASS | 走行証跡全体 (job-evidence / job-staging / run dir / submission) を `grep -rl "already consumed"` して 0 件 (rc=1) |
| 2 | runner の `campaign-start` が新 journal に出る | PASS | `journal.jsonl` 3 行目 |
| 3 | **最初の attempt 消費が通る** | PASS | `attempt-ledger.jsonl` に `rr80::p2_2_flag_opt::seq0`。旧 96 attempt と併存 |
| 4 | `driver_rc=0` / terminal completed / 96 session / `floors` 有限 | PASS | `job-result.json` の `driver_rc: 0`、journal 最終行 `terminal status=completed`、96 session すべて `valid=True`、floors は下表 |

## 台帳側の証拠

`.git/izanagi/s8b-holdout-admission-v1` の `observation_role=floor_campaign` の予約は、
**同一の 12 cell に対して 3 世代**存在する。

| campaign_run_id | cell 数 | measurement_generation_id | measurement_generation_digest |
|---|---:|---|---|
| `20260824T205358Z-2c8cf9be` (2026-08-24、一回性強制の時代) | 12 | (無し) | (無し) |
| `20260901T014044Z-2c8cf9be` (本 run、964035.nqsv) | 12 | `c9977b832a50a253…` | `98e410c057fbb2b5…` |
| `20260901T014045Z-2c8cf9be` (並行 run、964044.nqsv) | 12 | `368ff52ce63d1912…` | `3b9a1e33674d6f68…` |

cell 集合は 2026-08-24 の走行と**完全一致**する。照合は旧 v1 claim が持たない
`cell_effect_digest` ではなく、両者に共通の不変座標
(`key` の 6 field = `ccbench_pin` / `configuration_id` / `env_tag` / `freeze_holdout_key` /
`freeze_sha256` / `observation_role`、および `cell_id`) を canonical JSON にした集合比較で行い、
両世代とも `True` を得た。新世代の `entry_kind` はいずれも `fresh`。

### 台帳の数量 — 旧 namespace は 1 件も動いていない

D1190 の理由節は 2026-08-27 時点で「旧 claim 36 件・marker 228 件・**ledger 36 行**が現存」と
記録している。2026-09-01 の実測は次のとおり。

| 対象 | 2026-08-27 (D1190 記載) | 2026-09-01 11:31 | 差 |
|---|---:|---:|---|
| 旧 `claims/` | 36 | 36 | 不変 |
| 旧 `consumed/` | 228 | 228 | 不変 |
| `ledger.jsonl` | 36 行 | 60 行 | +24 (新 2 走行が 12 行ずつ) |
| `attempt-ledger.jsonl` | (228) | 420 行 | +192 (96 × 2 job) |
| `measurement-generation-claims/` | (無し) | 24 | 新 namespace、2 世代 × 12 cell |
| `measurement-generation-consumed/` | (無し) | 192 | 新 namespace、96 × 2 job |

**旧 namespace を 1 件も書き換えずに新しい観測が入っている。**
D1190 決定 4 の名前空間分離が実機で効いていることの陽性証拠である。

### 世代識別子の導出は三段 (実物 24 件で数値照合、rc=0)

`orchestrator/campaign/s8b_holdout_admission.py:785-814` を読み、同 module の
`_canonical_bytes` と同じ canonical JSON
(`ensure_ascii=False` / `sort_keys=True` / `separators=(",", ":")`、UTF-8) で再計算した。

1. `measurement_generation_id = sha256({observation_role, campaign_run_id})`
2. `measurement_generation_digest = sha256({measurement_generation_id, observation_role, campaign_run_id})`
3. `measurement_generation_claim_digest = sha256({measurement_generation_digest, cell_effect_digest})`
   — claim / marker の file 名になるのはこれ

`measurement-generation-claims` の 24 件すべてで、3 段と file 名が実物と一致した。
**D1190 決定 2 が定めるのは第 1 段 (id) の導出であり、digest と claim_digest はその上の段である。**
`campaign_run_id` は fresh では開始時刻と protocol hash から作られるため**別 run は必ず別世代**になり、
resume は同じ `campaign_run_id` を使うので同じ世代へ戻る (同決定 2)。

### D1190 決定 3 の陽性証拠

同決定 3 は「同一世代の同一 attempt の二重消費は引き続き拒否する。**別世代からは同じ論理 attempt を
消費できる**」と定める。2 世代が同じ 12 cell を同時に保持し、それぞれ独立に 96 attempt を
消費した状態を実機で観測した。**1 本だけ走らせていたら取れない観測である。**

## 環境・実行パラメータ (本 run)

- **実行環境**: Pegasus、queue=gen_S、nodes=1、elapstim_req=10:00:00、実行ノード `bnode130`
- **投入元 commit**: `2bf9cf387643bf7ac087c31f5c38cfcc5539de68` (投入時点の local main)
- **request ID**: `964035.nqsv`、**submission nonce**: `6cae6db1e5dc35ee775d8c968835d9f0`
- **投入コマンド**: `tools/pegasus/submit_floor.sh` (承認引数なし。D1124 により不要)
- **ccbench pin**: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- **protocol**: `protocol_sha256=2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`
  (`n_sessions=8` / `reps=5` / `stock_configuration=stock_common`)
- **freeze**: `freeze_sha256=315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- **manifest**: `manifest_sha256=ac285aeae7e7af5bec2f5aa513e71ab9d6ab8a9f5442c2e1e75c74459f81fbca`
- **formula**: `s8b-floor-stats/v2`、`wired_min_rel_floor=0.03`、`scale_adequacy_rel_tolerance=0.10`
- **perf**: `status=unavailable, reason=nonzero-rc`。本機で perf を要求しない既定方針どおり
  blocker としない
- **所要**: scheduler 会計で Created 10:40:09 / Started 10:40:17 / Ended 11:30:29、**Elapse 3016S**
  (50.3 分)。§6-C の「過去の完走は約 48 分」と整合する。所要は job の Elapse を正とする

## 床値の実測値 (floor 案)

**これは floor の「案」であって、何も発効していない。** `eligible_for_refreeze=false` は
`mode=pilot` によるもので、freeze への floor 書込みは別途の判断による。

| holdout | scalar_alt | scale_ref (m_stock) | pairs |
|---|---:|---:|---|
| `rr20` | 3.545e+04 | 1.182e+06 | 5 pair すべて 35449.5 |
| `rr80` | 4.849e+04 | 1.523e+06 | `p2_2_flag_opt` = 48486.594、他 4 pair = 45692.985 |

## セル統計 (session-median の散らばり、n_valid は全セル 8)

| cell | m (median) | s (stdev) | cv | machine_anomaly |
|---|---:|---:|---:|---|
| `rr20::backoff_fixed_best` | 3.624e+06 | 9,158 | 0.002527 | なし |
| `rr20::ident_all` | 1.184e+06 | 1.41e+04 | 0.01193 | なし |
| `rr20::p2_2_flag_opt` | 2.649e+06 | 1.534e+04 | 0.005793 | なし |
| `rr20::sort_best` | 1.211e+06 | 7,050 | 0.005829 | なし |
| `rr20::stock_common` | 1.182e+06 | 7,098 | 0.006012 | なし |
| `rr20::system_gate` | 1.254e+06 | 6,933 | 0.005527 | なし |
| `rr80::backoff_fixed_best` | 6.96e+06 | 2.137e+04 | 0.003069 | なし |
| `rr80::ident_all` | 1.526e+06 | 1.396e+04 | 0.00915 | なし |
| `rr80::p2_2_flag_opt` | 7.404e+06 | 4.529e+04 | 0.006111 | なし |
| `rr80::sort_best` | 1.514e+06 | 2.252e+04 | 0.01484 | なし |
| `rr80::stock_common` | 1.523e+06 | 1.731e+04 | 0.01135 | なし |
| `rr80::system_gate` | 3.161e+06 | 8,763 | 0.002772 | なし |

## 走行の健全性

- **12 セル × 8 session = 96 attempt がすべて `valid=True`。**
- **除外 session は 0 件。retry も 0 件** (台帳の 96 行はすべて `kind=planned`)。
- 各 attempt の所要は 26.73〜28.05 秒。前回 945229 は 26.79〜26.93 秒。
- session CV は最小 0.001656 / 最大 0.02974。`machine_anomaly` は全セルで無し。
- 実行ノードは本 run が `bnode130`、並行 run が `bnode136` で**別ノード**。相互汚染は無い。

## 3 走行の比較 — 床値は「3% 相対床」に張り付き、ノイズ項が超えた cell だけ持ち上げる

同じ 12 cell・同じ protocol・同じ freeze・同じ ccbench pin での 3 回の測定である。
一次資料 (各 run の `result.json`) から引いた。

| 量 | 945229 (08-24) | 964035 (本 run) | 964044 (並行 run) |
|---|---:|---:|---:|
| rr20 `scalar_alt` | 35551.92 | 35449.5 | 36025.348 |
| rr20 非 `p2_2` pair | 35551.92 (全 pair 同値) | 35449.5 (全 pair 同値) | 35548.245 |
| rr80 `scalar_alt` | 45509.145 | 48486.594 | 75975.565 |
| rr80 非 `p2_2` pair | 45509.145 (全 pair 同値) | 45692.985 | 45835.665 |
| rr80 `stock_common` median | 1.517e+06 | 1.523e+06 | 1.528e+06 |
| rr80 `p2_2_flag_opt` median | 7.206e+06 | 7.404e+06 | — |

**非 `p2_2` の pair 値は 3 走行で 0.72% 以内に収まっている** (45509.145 / 45692.985 / 45835.665)。
一方 rr80 の `scalar_alt` は 45.5k → 48.5k → 76.0k と動く。差分はすべて
`p2_2_flag_opt` pair 由来である。

機構は承認済みの式そのままで、欠陥ではない。`docs/phase3-8b-descriptor-design.md` の
2026-07-18 裁定が定める `floor_pair(c) = max(u_noise(c), wired_min_rel_floor × m_stock)` を、
本 run の `result.json` に対して機械照合した (全セル・両 holdout で成立)。

- `rel_floor = wired_min_rel_floor (0.03) × scale_ref`。本 run の rr80 では
  `0.03 × 1523099.5 = 45692.985` で、非 `p2_2` の 4 pair はすべてこの値である。
- セルごとの `floor = max(rel_floor, u_noise)`。
- `scalar_alt = 全 pair の max`。
- 本 run で `rel_floor` を超えたのは `rr80::p2_2_flag_opt` だけで、その `u_noise` は 48486.594。
  同セルは 12 セル中で最もスループットが高く (median 7.404e+06)、cv がわずかに上がるだけで
  絶対値としての `u_noise` が大きく動く。

**したがって pilot の床値「案」は、`scalar_alt` の水準では run 間で再現しない。**
再現するのは 3% 相対床の側である。**これは繰り返し測れるようになったから初めて見えた性質**であり、
一回性が強制されていた間は原理的に観測できなかった。本 wave では機構を足さず、観測として記録する
(床値は pilot 案であり何も発効していないため、現時点で成果物の値・受理集合・参照は変わらない)。

**worklog 1053 の `4.551e+04` がどの量かは一次資料で確定した。** 945229 の `result.json` では
rr80 の `scalar_alt` = 45509.145 であり、かつ 5 pair すべてが同値である。したがって
1053 の値は `scalar_alt` であり、`pairs` の一つではない。

## 依頼文と台帳の前提が 1 件誤っていた

[T-088] の持ち越し本文 (entry 1029、2026-08-27) と D1124 の「実害」節は、
2026-08-24 の run を**「途中で死に、成果物が残っていない」**と書いている。これは誤りである。

- `docs/archive/worklog-phase3-0825-924.md:1` = 「[T-1431] 床値 pilot が初めて完走し、
  床値の実測値が得られた (計測、request 945229.nqsv、12 セル 96 attempt すべて valid・
  除外 0・retry 0)」
- `docs/archive/worklog-phase3-0827-1053.md` が同じ否認を既に書いていた

**D1124 の決定は覆らない。** 中核の論拠「性能測定は繰り返しても何も無効化しない」は
run が死んだか完走したかに依存しない。訂正されるのは成果物影響の言い方だけで、
正しくは「床値が 1 つも出ない」ではなく**「同じ cell を測り直せない」**である。
[T-088] の stub は 1029 から更新されないまま本 wave の依頼文へ伝播していた。

## 並行 session との調整と相互訂正

分担は次のとおり合意した。測定は両方走らせ (D1124 により同じ cell を何度測ってもよく、
床値 job が過去に落ちてきた経緯から冗長性に価値がある)、**記録と land は本 wave が持つ**。
相手は締めの fragment を書かず、自分の走行を第 2 の独立観測として渡した。
**相手の job には一切触れていない。**

相互訂正が 2 件あり、どちらも一次資料・実物で決着した。

1. 相手の「`ledger.jsonl` 36 行は投入前と同じ」は誤りで、実測は 60 行だった。相手は再測して
   受け入れた。D1190 の理由節が 2026-08-27 時点の 36 行を記録しており、差 24 行は
   ちょうど今日の 2 走行分である。
2. 親 (本 session) の「世代 digest = `sha256({observation_role, campaign_run_id})`」は取り違えで、
   その式が与えるのは `measurement_generation_id` である。相手の指摘を受けて実装を読み、
   claim 24 件全件を数値照合して三段導出を確定した。帰属は変わらない。

## 運用上の落とし穴 (両 session が独立に実測した)

**`submit_floor.sh --dry-run` は third-party staging を飛ばす。** 新規 worktree では
dry-run が rc=0 でも、実投入は `floor third-party source root is missing or unsafe` (rc=2) で
qsub 前に落ちる。`tools/pegasus/fetch_third_party.py hydrate` で永続 cache から供給する必要がある
(`tools/pegasus/README.md` §6 の既定手順であって実装の欠陥ではない)。
**dry-run の緑を投入可能性の証拠にしない。**

## 証拠の所在

将来の official 床値 job の起動証明 (`clean_scan_digest` の hit 0 件要求) を止める
holdout clean-scan の汚染を避けるため、repo 外へ退避した。

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-t088-floor-remeasure/evidence-bundle-964035/`

- `bundle-manifest.json` — 構成 manifest。944 file・61,720,222 bytes の全件 sha256 と、
  run の識別情報・floors を持つ。manifest 自身の sha256 =
  `bd5eb9bd489f8edbc567c75189cabf96ca188ce4fc05c448ae502ffa49cc2c27`
- `run-dir/20260901T014044Z-2c8cf9be/` = `result.json` / `result.md` / `manifest.json` / `journal.jsonl`
- `job-staging/0:964035.nqsv/` = checkpoint 由来の toolchain 実測値、`job-result.json`、
  各段の stdout / stderr
- `job-evidence/` = `/work/1/SFC/tanab/izanagi-job-evidence/pegasus/964035.nqsv` の複製
  (`checkpoint.jsonl`)
- `submission/` = 投入 receipt 3 件 (dry-run / 第三者 source 未供給で落ちた初回 / 本投入)。
  本投入の `scheduler.stderr` に PBS 会計痕跡が入っている
- `binaries/` = content-addressed binary store (manifest と result が `store_path` で参照する)
- `s8b-build-cache/` / `claims/` = build cache と campaign 側 claim

並行 run (964044) の成果物は相手 session が自分の job dir へ退避しており、本 bundle には含まない。

## 残るもの

床値は pilot の「案」であって何も発効していない。次はいずれも別項である。

- official 解禁 (`_assert_official_permitted`、restart runbook の W-1)
- holdout freeze v2 の再凍結 (W-3) — pilot 成果物は再凍結へ渡せない
- oracle manifest の production 配線と oracle 実走 (W-4 / W-5)
