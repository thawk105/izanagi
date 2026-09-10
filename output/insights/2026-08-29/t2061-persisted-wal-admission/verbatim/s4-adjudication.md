# 段 4 裁定 — [T-2061] persisted WAL の verdict/receipt を共通 admission helper へ通す

親裁定。基準 main d03855e92。入力は段 2 プラン (`s2-plan.md`)、段 3 レンズ A (`s3-lens-a.md`)、
段 3 レンズ B (`s3-lens-b.md`)、親 brief (`brief.md`)、確定裁定 D1246。

## 結論

**実装する。ただし段 2 プランのままでは実装しない。** 述語を D1246 の最小へ縮め、
閉包を 21 module / 29 site へ広げ、恒真な二重呼び出しを落とす。

scope は D1246 の文言どおり「**現に存在する** certified consumer」で閉じる。新たに見つかった
4 site は将来の consumer でも一般化でもなく、現に persisted WAL から certified 主張を出している
実在 consumer なので scope 内である。汎用 proof framework、新台帳、新署名主体は作らない。

## 所見の裁定

| ID | 判定 | 採否 | scope | 裁定 |
|---|---|---|---|---|
| A-01 / B-09 | real | **採用** | 内 | S1/S8B/backoff の lock-only 経路で、epoch 判定・lock SHA・WAL 読取が別 read になる TOCTOU 窓を閉じる。lock bytes を 1 回読んでそこから SHA を導き、WAL 読取の前後で lock SHA の一致を要求する。 |
| A-02 / B-05 | real | **採用** | 内 | D1246 を越える述語を削る。下記「採用する述語」参照。 |
| A-03 | real | **採用** | 内 | `batch_commit_counts == 0` を persisted helper から削る。live producer 側の gate (`pipeline.py:1273-1287`) は触らない。CCBench は batch commit を独立集計し TPS にも加えるため、将来 batch trace が正当に certify 可能になったとき旧制約で拒否する。 |
| A-04 | real | **採用 (部分)** | 内 | receipt evidence 列との完全一致が `verdict`/`certified`/「verify 1 件以上」を含意する。code は可読性のため残すが、**変異事前登録から外す**。恒真な検査を gate の実効性として数えない (DW-M03)。 |
| A-05 | refuted | — | 内 | 手順 4・7 自体による受理集合の拡大は無い。ただし削除する独自判定は helper が同等以上に拒否することを実装で確かめる。 |
| A-06 | refuted | — | 内 | 絶対規律 2、epoch gate、環境契約、source binding は弱まらない。配置 (`:1157` の epoch gate 後、view 発行前) を守る。 |
| A-07 | refuted | — | 内 | 4 種の例外変換が無害な診断へ格下げされる consumer は無い。 |
| A-08 / B-01 | real | **採用** | 内 | 親 brief の「22 site 全て chokepoint」は誤り。訂正する。 |
| A-09 | real | **採用** | 内 | 親の「repo 内 30 campaign は v1 だから既存保存成果物の consumer を壊さない」は成立しない。`test_bench_first_real_wal.py:244-305` が実 artifact を E1 へ昇格して certified consumer へ渡す。訂正する。 |
| A-10 / B-01 | real | **採用** | 内 | S6/S8A の**行単位** helper 呼び出しは中央 chokepoint 後には恒真。**実装しない**。代わりに未結線の `_replay_outcome()` を結線する。 |
| B-02 | real | **採用** | 内 | S6 `_replay_outcome():400` と S8A `_replay_outcome():499` は raw `wal.replay()` の COMMIT だけで `replayed-certified` を返す。helper へ結線する。 |
| B-03 | real | **採用** | 内 | `backoff_repro._bench_tps():80` と `paper_story_a2_certification._raw_cell_from_wal():2574` も同型。helper へ結線する。A-2 の `observed-positive` は headline 成果物なので DW-G05 の must-fix。 |
| B-04 | real | **採用** | 内 | 3 bypass は一般化ではなく実在 consumer。手順 4〜6 は削らない。 |
| B-06 | refuted | — | 内 | `log_receipted_commit()` だけでは fixture は完成しないが、`wal.log()` との組合せで実現可能。実装子へ明示する。 |
| B-07 | real | **採用** | 内 | `s8b_oracle_report.py` の bytes は `s8b_oracle_manifest.py:458` の generator source hash として検査され、独立 golden `test_s8b_oracle_manifest.py:90` に現行 SHA が固定されている。**同じ変更単位で golden を追随させる**。 |
| B-08 | refuted | — | 内 | production は 6 file ではなく 8 file。分割案は下記。 |
| (P1) | real | **支持** | 内 | helper は新 module を作らず `artifact_admission.py` 内に置く。新 module を exact 24 path 閉包へ足すと `campaign_lock.py:221-233` の exact key 集合が 25 件になり既存 v2 authority が codec 段階で全拒否される。 |
| (P2) | **refuted** | **不採用** | 内 | 中央で全 COMMIT を検査すれば 1 variant anomaly campaign も view 発行前に拒否される。行単位の二重検査は要らない。必要なのは chokepoint より前に動く raw resume 経路の結線だった。 |
| (P3) | real | **採用** | 内 | fixture 波及は artifact admission だけでなく critic、S1、S8B oracle、backoff consumer、A-2 まで届く。 |

### scope 外として実装しないもの (裁定パッケージへも送らない = 既に別 T がある)

- `_CERTIFIED_VIEW_TOKEN` の外部 capability 化 (T-2062)。
- `current-closure-unavailable` の撤去 (T-2060)。
- plot provenance の 2 本、paper-story A-1、campaign registry、B10 shape sweep — いずれも明示的に
  `HISTORICAL_RAW` か non-certifying であり、certified 主張をしない。
- known-axes freeze generator の再生成時 certification 要求。**凍結 bytes を変えないので今回は無関係。**
  将来の再生成に current certification を要求するかは別裁定候補として insight に記録するだけにする。
- 汎用 proof framework、将来 consumer の自動登録、新 receipt schema、新台帳、新署名主体。

## 確定した consumer 閉包 (21 module / 29 source-level admission site)

### A. full admission chokepoint 経由 (16 module / 22 site) — helper は chokepoint 1 箇所で守る

`orchestrator/critic/digest.py:1586` / `p3_b4_closed_critic.py:740,1779` /
`p3_autonomous_workload_trial.py:3088` / `s6_sort_sweep.py:475` /
`backoff_extended_sweep_report.py:459` / `backoff_sweep_report.py:57` / `backoff_overthrottle.py:145` /
`p3_b4_wiring_probe.py:1475` (`runtime.artifact_admission.*`) / `p3_s4_loop_sort.py:546,743` /
`autonomous_trial_completeness.py:4423,4912,4959` / `p3_s4_loop_trigger_gating.py:1088` (`L.*`) /
`p3_s4_loop.py:1240,1576,1791` / `s8a_trigger_sweep.py:577` / `replay.py:184` /
`layer3_report.py:685` / `p3_s4_red.py:191`

### B. lock-only / raw-WAL 経由 (3 site) — 個別に結線が要る

`backoff_requested_us.py:450` (`artifact_admission.*`) / `s1_report.py:385` /
`s8b_oracle_report.py:553` (`_artifact_admission.*`)

### C. 識別子検索では出ず編集面 path 検索でだけ出た certified site (4 site) — 個別に結線が要る

`s6_sort_sweep.py:400-403` (`_replay_outcome`) / `s8a_trigger_sweep.py:499-502` (`_replay_outcome`) /
`backoff_repro.py:80-93` (`_bench_tps`) / `paper_story_a2_certification.py:2064,2574-2678` (`_raw_cell_from_wal`)

**C はユーザー指示が警告したとおりの取りこぼしである。** 識別子 key だけの検索では 4 site が落ちた。

## 採用する述語 (D1246 の最小)

helper `require_persisted_certified_commit(records, commit_record, *, campaign_lock_sha256)`:

1. COMMIT の `build_attempt_id` が非空 exact `str` (caller misuse guard。変異登録しない)。
2. 同一 variant・同一 attempt・COMMIT より前の `verify_done` を選び、1 件以上を要求する。
3. 選んだ各 verify について `verdict == "serializable"` かつ `certified is True`
   (可読性のため残すが、7 に含意されるため変異登録しない)。
4. `type(anomalies) is int and anomalies == 0` (**独立に必要。receipt に anomalies field が無い**)。
5. `workload.tag` が非空 `str` (7 の照合に使う。exact key 集合は要求しない)。
6. COMMIT payload から `commit_verification_receipt` を除いた terminal payload を作り、既存
   `commit_receipt.validate_serialized_receipt()` を `sink_kind="campaign-wal"`、実 lock SHA、
   `record.variant` で呼ぶ。
7. validated receipt の `operation_identity == COMMIT.build_attempt_id`、および receipt evidence の
   順序付き `(workload_tag, verdict, certified)` 列を WAL verify 列と完全一致させる。

**削る述語 (段 2 プランから撤去):** `commits > 0`、`aborts >= 0`、`commit_witness` の exact 2 key /
`commit_counts == commits` / `batch_commit_counts == 0`、`workload` の exact key 集合、
`verify_configs` の順序保持 deduplicate 一致。いずれも D1246 が求める verdict/receipt の束縛に不要で、
実行側の診断 schema を将来にわたって固定する。live producer 側の既存 gate は一切触らない。

例外: `CommitReceiptError` は `ArtifactAdmissionError` へ cause 付き変換。caller misuse は `TypeError`。
新しい例外階層は作らない。

## 同一 snapshot 契約 (A-01/B-09)

lock-only 経路 (B の 3 site) と raw 経路 (C の 4 site) では、lock bytes を 1 回読んでその bytes から
SHA-256 を導き、WAL 読取後に lock SHA を再取得して一致を要求する。不一致は helper 呼び出し前に
`ArtifactAdmissionError` 相当で拒否する。epoch 判定に使った lock と receipt が束縛する lock が
別物になる窓を閉じる。

## 実装の分割 (同一 land 単位、2 つの逐次 author 単位)

- **単位 1 (author-1):** `artifact_admission.py` の helper 本体 + chokepoint 結線
  (`:1157` の epoch gate 後・view 発行前に全 COMMIT を通す) + helper の正負 unit test +
  full-admission fixture 追随 (`test_artifact_admission.py`、`test_bench_first_real_wal.py`、
  `test_critic.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`)。
- **単位 2 (author-2):** B の 3 site + C の 4 site の結線、同一 snapshot 契約、
  `s8b_oracle_manifest.py` の PIN_GATE_SPEC と `test_s8b_oracle_manifest.py:90` の golden 追随、
  fixture 追随 (`test_s1_report.py`、`test_s8b_oracle_report.py`、`test_backoff_consumers.py`、
  `test_backoff_requested_us.py`、`test_paper_story_a2_certification.py`)。

単位 1 → 単位 2 の逐次。両方が同じ land 単位に載る。単位 1 だけで land しない
(raw consumer 7 本の穴が残るため、D1246 完了と記録できない)。

## 変異事前登録 (DW-M01)

受理集合を縮める wave なので、承認外の過剰拒否を検出する正例変異も登録する。
parametrize id はすべて ASCII。

### 負例側 (受理集合を広げる変異。KILLED を期待する)

| # | 変異させる file:line | 期待して赤になる node |
|---|---|---|
| M1 | helper の `anomalies == 0` 検査 | `test_artifact_admission.py::test_persisted_commit_gate_rejects[anomalies-positive]` |
| M2 | helper の durable receipt validator 呼び出し | `test_artifact_admission.py::test_persisted_commit_gate_rejects[receipt-terminal-mismatch]` |
| M3 | helper の receipt operation 一致 | `test_artifact_admission.py::test_persisted_commit_gate_rejects[receipt-operation-mismatch]` |
| M4 | helper の evidence 列比較 | `test_artifact_admission.py::test_persisted_commit_gate_rejects[receipt-evidence-mismatch]` |
| M5 | helper の verify attempt 一致 | `test_artifact_admission.py::test_persisted_commit_gate_rejects[verify-attempt-mismatch]` |
| M6 | chokepoint `artifact_admission.py:1157` を先頭 COMMIT だけに | `test_artifact_admission.py::test_certified_view_checks_every_commit[second-commit-invalid]` |
| M7 | `s1_report.py` の helper 結線 | `test_s1_report.py::test_persisted_certification_invalidates_sample[s1]` |
| M8 | `paper_story_a2_certification.py` の helper 結線 | `test_paper_story_a2_certification.py::test_raw_cell_requires_persisted_certification[a2]` |
| M9 | `s6_sort_sweep.py:400` の resume 結線 | `test_s6_sort_sweep.py::test_replay_outcome_requires_persisted_certification[s6]` |

### 正例側 (受理集合を承認以上に縮める変異。KILLED を期待する)

| # | 変異 | 期待して赤になる node |
|---|---|---|
| M10 | helper を「campaign の全 verify を正常必須」へ拡大 | `test_artifact_admission.py::test_persisted_commit_gate_accepts[aborted-red-attempt-coexists]` |
| M11 | helper を「campaign に COMMIT 必須」へ拡大 | `test_artifact_admission.py::test_persisted_commit_gate_accepts[no-commit-campaign]` |
| M12 | helper を `HISTORICAL_RAW` にも適用 | `test_artifact_admission.py::test_historical_raw_unaffected[incomplete-receipt]` |
| M13 | `aborts == 0` へ過剰強化 | `test_artifact_admission.py::test_persisted_commit_gate_accepts[nonzero-aborts]` |

M1〜M13 はいずれも「同じ入力を拒否する層が前後に無い」ことを実装子に code で確認させる。
確認できないものは登録から外し、実効 gate へ再照準する。

**M3・M4・M5 の fixture 注意点 (レンズ A):** 単純な ID 改変は topology が先に赤にする。
M5 は「attempt A が正常 verify 後 ABORT、attempt B が verify 無しで self-consistent な receipt 付き
COMMIT」という topology-valid な 2 attempt 入力にする。M4 は WAL tag と `verify_configs` を同時に
`s2` へ揃え terminal hash を再発行し、receipt evidence だけ `legacy` に残す。
M3 は `commit_receipt_support.campaign_receipt()` で operation を独立指定し receipt ID まで正しく再発行する。

## 通る正例

実在する外部 official campaign
`/work/1/SFC/tanab/b10-backoff-grid-runs5/b10-backoff-grid-20260826T234647Z-783837-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/runs/wal.jsonl:3,5`。
同 attempt・正常 verify・実 lock/variant/attempt/terminal payload に束縛した receipt を持つ。
repo 内 `output/campaigns` の 30 campaign は全て v1 で E0 拒否されるため正例にならない。

## 凍結 bytes の裁定

- `t080_freeze_migration.py` の `_KNOWN_REPIN_ROWS` は migration basis commit の blob を読む
  (`:1365-1381`)。S6/S8A の live source 編集では**再 pin しない**。
- `FROZEN_MANIFEST` は exact 23 output path で Python source は 0 件。**触らない**。
- `output/s8b-freeze`、`output/s1-freeze`、T-080 receipt、既存 campaign artifact の bytes は**変更しない**。
- `s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW` 内 report SHA と `PIN_GATE_SPEC_SHA256`、および
  `test_s8b_oracle_manifest.py:90` の独立 golden は、`s8b_oracle_report.py` を編集する**同じ commit で追随**させる。
- `artifact_admission.py` の byte 変更は future campaign の E1 表示 ID と B4 projection hash を変える。
  既存 campaign の admission は D1163 の availability-only により無効化されない。

## 新規名の gate 抵触

- 新 test file は**作らない**。既存 test file へ追加する (`test_plain_runner_coverage.py:44` の
  自走 harness 要求を避ける)。
- 新 parametrize id は ASCII のみ。`test_critic.py` は acceptance duration ledger の凍結 suite prefix に
  含まれるため、追加 node の所要時間増を受入前に確認する。
- 新 insight は `output/insights/` 配下。`check_docs.py:2611` の内容走査対象なので書式に従う。
