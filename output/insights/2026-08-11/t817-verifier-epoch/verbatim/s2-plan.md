# 実装プラン

静的読解のみを行った。コード変更・pytest 実走・成果物生成はしていない。

## provisional 裁定の評価

| 裁定 | 評価 | 根拠 |
|---|---|---|
| P1 | 条件付き採用 | admission と当時の verifier verdict は既に別次元である（[artifact_admission.py:4–12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:4)）。歴史値を改変せず、replay/guided の現行選択に deny-only overlay を置く。 |
| P2 | 採用 | `canonical_preimage` は `search_config` 全体を hash する（[ident.py:151–178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/ident.py:151)）。既存の `verify` は pass 構成用なので、新しい epoch key と分離する。 |
| P3 | 一部棄却 | witness 不在は pre-witness 世代を示すが、witness の存在だけでは lock に宣言された policy identity まで証明しない。また `aborts`・`workload`・`verify_configs` に中間世代がある。 |
| P4 | 条件付き採用 | raw stdout 単体では「同一 run」を証明できない。lock/WAL/record/binary/stdout を束縛した同伴 receipt と trusted Git snapshot が揃うものだけを権威化する。 |

## 単位 A — verifier-policy epoch と campaign identity

### 1. epoch の正本

新規 artifact `orchestrator/campaign/campaign_verifier_policy_v1.json` を正本にする。trust-critical loader は新規 Python module ではなく [ident.py:35–52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/ident.py:35) に置く。

新規 module を避ける理由は、enforcement source closure が現在 exact 8 path であり、`ident.py` は既に含まれる一方（[campaign_lock.py:29–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/campaign_lock.py:29)）、新しい path の追加は既存 v2 authority の exact path 集合検査を壊すためである（[campaign_lock.py:168–180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/campaign_lock.py:168)）。

artifact は canonical compact JSON + 終端 LF の exact bytes とし、少なくとも次を列挙する。

- `schema_version`
- `epoch_id`
- `pass_resolution`: `verify` 不在なら `legacy`、`legacy+s2` なら `legacy → s2`
- `acceptance_gates`: 正常終了、非空 trace、abort counter、commit counter、batch=0、verifier certified
- `stdout_witness_normalization`: 一意な非コメント・非負十進 counter
- `historical_selection`: same-run witness 照合、照合不能時の除外、WAL writeback 禁止
- rejection code の閉集合

「同じ policy」は、同じ `epoch_id` かつこの artifact の exact raw-byte SHA-256 が同じこと、と定義する。空白だけの変更も別 epoch になる保守的定義とする。

過去文書の `verifier_policy_sha256` は参照先 artifact が未存在と明記された設計語である（[phase3-8c-wiring-design.md:55–77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/docs/phase3-8c-wiring-design.md:55)）。また [artifact_admission.py:91–121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:91) の `policy_sha256` は build-admission policy で、代用できない。

したがって新しい identity field は次の別名にする。

```json
"campaign_verifier_epoch": {
  "schema_version": "campaign-verifier-epoch-ref/v1",
  "epoch_id": "commit-witness-bound/v1",
  "policy_artifact_sha256": "<artifact exact bytes SHA-256>"
}
```

`verify`、`verifier_policy_sha256`、build-admission の `policy_sha256` のいずれにも被せない。

### 2. `search_config` への注入

[ident.py:39–52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/ident.py:39) の `bind_admission_policy` に keyword-only `verifier_epoch` を加える。

- 既定値は current artifact から導出した reference。
- `verifier_epoch=None` は `{}` を返し、key 自体を追加しない歴史専用形。
- 既存 key が current と一致すれば idempotent。
- 異なる reference、または `None` 指定時に key が既にあれば reject。
- [ident.py:432–484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/ident.py:432) の新規・再開 write gate は current reference の exact 一致を必須にする。これにより binder を迂回した epoch 不在の新規 lock を作れない。

`canonical_preimage` 自体には自動補完を入れない。epoch 不在 config は従来と byte-for-byte 同じ preimage になり、[screening_search_config(None)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/ident.py:101) と同じ歴史保存意味論を持つ。

既存 lock については次を区別する。

- codec・artifact reader・prefix discovery は引き続き読める。
- policy が変わった writer が epoch 不在 lock へ追記することは拒否する。
- 歴史 preimage の再現試験だけは `verifier_epoch=None` を明示する。

これは「再開経路の破壊」ではなく、異なる verifier policy の WAL 混在を止める S1 の本体である。

### 3. `campaign.lock` 互換性

`campaign_lock.IDENTITY_KEYS` は現在も top-level 5 key だけである（[campaign_lock.py:15–18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/campaign_lock.py:15)）。`search_config` 内部は object 型だけを検査するため（[campaign_lock.py:137–148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/campaign_lock.py:137)）、nested epoch key の追加で v1/v2 wire schema は変わらない。

また、

- `verify_admission_preimage` は top-level exact 5 key と `search_config.build_admission` だけを見る（[ident.py:76–98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/ident.py:76)）。
- `verify_against_lock` は最終的に canonical preimage 全体を比較する（[ident.py:327–360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/ident.py:327)）。

したがって admission 検査を二義化せず、epoch drift は既存の exact preimage 比較で拒否できる。

実 P2-2 lock は epoch だけでなく `build_admission` もない（[campaign.lock:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/output/campaigns/p2-2-silo-balanced-enumerate-f1588056/campaign.lock:1)）。これを現在の `canonical_preimage` で再計算できるとは主張せず、[replay.py:93–116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:93) の prefix discovery を維持する。

## 単位 B — 旧 COMMIT の評価と現行選択 gate

### 1. 旧記録の epoch 導出

新規 `orchestrator/campaign/verifier_selection.py` を追加し、`AdmittedCampaign` の immutable records を読む。[WalRecord.payload](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/model.py:98) は consumer-specific object であり、generic WAL parser も payload schema は consumer の責務としている（[wal.py:251–289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/wal.py:251)）。

epoch 判定の実在入力は次のとおり。

- lock の `search_config.campaign_verifier_epoch`
- `commit.payload.verify_configs`。現 emitter は [pipeline.py:1169–1185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:1169) と [pipeline.py:1218–1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:1218) で実際に書く。
- `verify_done.payload.commit_witness`、`commits`、`aborts`、`workload.tag`。実 emitter は [pipeline.py:1032–1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:1032)。
- build record の `genome` と `trace_bin`。
- artifact-admission decision の `campaign_lock_sha256` / `wal_sha256`（[artifact_admission.py:91–105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:91)）。

`commit_witness` は COMMIT payload の field ではなく、その COMMIT に先行する `verify_done.payload` の field である。実 P2-2 は build_start・build_done・witness なし verify_done・bench_done・COMMIT の並びである（[wal.jsonl:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/output/campaigns/p2-2-silo-balanced-enumerate-f1588056/runs/wal.jsonl:1)、[wal.jsonl:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/output/campaigns/p2-2-silo-balanced-enumerate-f1588056/runs/wal.jsonl:3)、[wal.jsonl:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/output/campaigns/p2-2-silo-balanced-enumerate-f1588056/runs/wal.jsonl:5)）。

分類は二軸にする。

- `declared_epoch`: lock の current reference または `null`
- `record_epoch`:
  - `verdict-only/pre-witness`
  - `abort-accounted/pre-witness`
  - `commit-witness-shaped`
  - `mixed-or-unknown`

witness 不在なら pre-witness と判断できる。一方、witness 形があるだけの記録は `commit-witness-shaped` であり、lock 宣言済み current epoch と同義にはしない。

### 2. 同一 attempt の切り出し

`verify_done` には `build_attempt_id` が実在しないため、存在を前提にしない。現 COMMIT には書かれるが、verify payload にはない（[pipeline.py:1032–1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:1032)、[pipeline.py:1218–1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:1218)）。

immutable record の物理順から、variant ごとに `build_start` から terminal `commit/abort` までを attempt segment として切り出す。

- segment 内の build/verify/commit だけを相関する。
- `verify_configs` があれば verify sequence/tag と exact 一致させる。
- `verify_configs` 不在かつ lock の `verify` も不在なら単一 `legacy` とだけ推定する。
- 複数 pass なのに tag がない、terminal 重複、segment が曖昧なら構造化除外する。
- 別 attempt の verify/stdout を最後勝ちで流用しない。

既存 `wal._validate_attempt_topology` は build_start/build_done/COMMIT/ABORT を attempt ID で検査するが、verify_done は attempt ID へ結合していない（[wal.py:1029–1149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/wal.py:1029)）。したがってこの consumer 固有相関が必要である。

### 3. 保存 stdout の探索と権威化

raw stdout だけを権威にしない。新設 gate は次の同伴 receipt を要求する。

- schema / producer ID
- campaign lock SHA-256
- WAL SHA-256
- variant
- build_start/build_done/verify_done/commit の物理行番号
- verify tag
- WAL に実在する `trace_bin` または `trace_bin_sha256`
- stdout repo-relative path / stdout SHA-256
- subprocess return code

[artifact_admission.py:367–392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:367) の trusted historical Git snapshot 機構を narrow public API にし、次を行う。

1. admitted historical campaign の exact snapshot commit と campaign path を得る。
2. その snapshot の campaign subtree を列挙し、`commit_counts_` を持つ stdout を必ず候補化する。
3. 同じ snapshot にある receipt と stdout hash を照合する。
4. receipt と immutable WAL segment の全 binding を照合する。
5. stdout を現行 parser と同じ規則で parse する。正本は [pipeline.py:230–253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:230)。
6. `commit_counts == verify_done.commits`、`batch_commit_counts == 0` を要求する。必要な abort counter、flags、genome も照合する。
7. 候補 0 件、複数、receipt 不在、producer 不一致、hash/ordinal/variant 不一致はすべて除外する。

production に「witness 0 件」という空 ledger は置かない。snapshot の実 subtree を毎回探索するため、正しく束縛された stdout が存在すれば positive branch に入る。

別 producer の t139 stdout は有効そうな counter を持つ（[run log:1–21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/run-25-W2-mode2-r4.log:1)）が、producer は専用 script が直接 redirect したもの（[t139_positive_control_probe.sh:486–523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/tools/pegasus/probes/t139_positive_control_probe.sh:486)）。campaign subtree・receipt・trace binary binding を満たさないので権威化しない。

raw stdout が残っていても binding receipt がなければ「候補を見落とした」のではなく `unbound-stdout-candidate` として可視化する。raw file だけで同一 run を証明する案は採らない。

### 4. 構造化除外

新規 immutable `CertificationAssessment` と `CertifiedSelectionExclusion` を設ける。除外 object は最低限次を持つ。

```json
{
  "schema_version": "campaign-certified-selection-exclusion/v1",
  "code": "same-run-stdout-witness-not-found",
  "campaign_id": "...",
  "variant": "...",
  "commit_line": 5,
  "verify_line": 3,
  "declared_epoch": null,
  "record_epoch": "verdict-only/pre-witness",
  "missing": [
    "verify_done.payload.commit_witness",
    "trusted_same_run_stdout_receipt"
  ],
  "evidence": {
    "lookup_status": "not-found",
    "campaign_lock_sha256": "...",
    "wal_sha256": "..."
  }
}
```

別 code として `epoch-reference-invalid`、`attempt-ambiguous`、`stdout-receipt-unbound`、`stdout-witness-malformed`、`commit-count-mismatch`、`batch-commit-nonzero` を用意する。

## consumer での除外位置

[replay.py:47–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:47) の `GenomeResult.certified` は「当時 WAL に記録された事実」として残す。そこへ `selection_assessment` を追加し、false へ上書きしない。

[replay.py:119–151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:119) の `load_landscape` は committed genome と fitness を従来どおり全件返し、assessment を付加する。これにより歴史解析と既存の raw projection を壊さない。

現行 certified 選択は次の三重 gate にする。

- [replay.assert_complete:154–167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:154): 8 genome・当時 certified に加え、全件 `selection_eligible` を要求。違反時は `CertifiedSelectionUnavailable(AssertionError)` と structured reasons を返す。
- [replay_evaluate:170–179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:170): 単体呼出しでも ineligible genome を配らない。
- [winner_tied_set:182–207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:182): `assert_complete` を迂回した ranking も拒否する。

[replay.main:210–231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/replay.py:210) は現在 `AssertionError` を warning 化した後も `winner_tied_set` を実行する。これを structured stderr + 非ゼロ終了へ変更し、ランキングを出さない。

guided は以下の順序へ変える。

- `cmd_start`: landscape load/gate を `layout.ensure`・lock・meta・WAL より前へ移す。現状は gate 前に lock/meta を書く（[guided.py:163–193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/guided.py:163)）。
- `cmd_evaluate`: landscape gate を `ensure_resumable_wal` より前へ移す。現状は source landscape 判定前に tail repair し得る（[guided.py:196–227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/guided.py:196)）。
- `trial_result`: winner 計算前に gate を置く（[guided.py:230–245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/guided.py:230)）。
- `_log_eval`: 最初の `wal.log` より前に result 単体の eligibility を検査する（[guided.py:131–141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/guided.py:131)）。

[search_baselines.run_workload:303–317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/search_baselines.py:303) は既に `assert_complete` を通る。CLI は全 workload の preflight を表示前に行い、1 workload でも除外なら部分レポートを出さず非ゼロ終了させる。

実 P2-2 は全件 witness/receipt 不在なので、結果として P2-5 replay・guided・baseline は停止する。これは黙った緑ではなく、N2 をそのまま可視化する挙動である。

## 変更禁止面

以下は編集対象から外す。

- `output/s1-freeze/known_axes_freeze.json` と全 freeze bytes。SHA pin は [test_frozen_artifacts.py:38–42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_frozen_artifacts.py:38)、検査は [test_frozen_artifacts.py:125–153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_frozen_artifacts.py:125)。
- `s1_known_axes_freeze.py`。現在は COMMIT を直接選ぶ（[s1_known_axes_freeze.py:266–295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/s1_known_axes_freeze.py:266)）ため、この consumer へ新 gate を入れない。generator 自身の SHA も freeze が検査する（[s1_known_axes_freeze.py:831–879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/s1_known_axes_freeze.py:831)）。
- 既存 WAL bytes。`wal.py`、`model.py` も編集しない。新 gate は `AdmittedCampaign.records` の read-only projectionだけを読む（[artifact_admission.py:134–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/artifact_admission.py:134)）。
- `wal.replay` は trigger orphan recovery を追記し得るため（[wal.py:1481–1487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/wal.py:1481)）、selection assessor から呼ばない。
- `_run_trace`、trace directory、stdout 永続化経路。現状の capture/parse と tmpdir 削除（[pipeline.py:311–363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:311)、[pipeline.py:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:928)、[pipeline.py:1063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/campaign/pipeline.py:1063)）は T-816/trace-format 面なので変えない。
- `external/ccbench/**`。

## ファイル所有と依存順序

### 単位 A の専有

- `orchestrator/campaign/ident.py`
- `orchestrator/campaign/campaign_verifier_policy_v1.json`（新規）
- `orchestrator/tests/test_verifier_policy_epoch.py`（新規）
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_campaign_lock_codec.py`
- identity pin の影響を受ける既存テスト群。ただし `test_guided.py` は B 専有とする。

### 単位 B の専有

- `orchestrator/campaign/artifact_admission.py`
- `orchestrator/campaign/verifier_selection.py`（新規）
- `orchestrator/campaign/replay.py`
- `orchestrator/campaign/guided.py`
- `orchestrator/campaign/search_baselines.py`
- `orchestrator/tests/test_verifier_selection.py`（新規）
- `orchestrator/tests/test_guided.py`
- `orchestrator/tests/test_bench_first_real_wal.py`
- `orchestrator/tests/test_artifact_admission.py`

両集合は素である。B は A の epoch reference loader/API に依存するため並行着手しない。

順序は次のとおり。

1. A が artifact・identity API・lock metamorphic tests を実装。
2. `ident.py` は enforcement closure 内なので、A を commit してから A の test を実行する。
3. B が A の確定 API を import して selection overlay と consumers を実装。
4. `artifact_admission.py` も closure 内なので、B も commit 後に test を実行する。
5. 関連 test、全体 test、`check_codex_agents.py`、`check_docs.py`、commit 後 provenance を実施する。pytest は直接起動せず `tools/run_tests.py --force-dispatch` を使う。
6. 性能計測・floor・oracle・freeze producer は起動しない。

## テスト設計

### 単位 A

- artifact exact schema、canonical bytes、literal SHA pin。
- artifact 1 byte変更で `policy_artifact_sha256` と campaign ID が変わる。
- `verifier_epoch=None` で key が不在になり、pre-T817 の代表 ID が不変。
- current epoch を加えた ID は歴史 ID と異なる。
- `verify` の pass 構成変更と `campaign_verifier_epoch` の policy 変更が独立に ID を変える。
- v1/v2 lock の top-level 5 key が不変で、nested epoch を codec が受理する。
- `verify_admission_preimage` が epoch 追加後も build-admission だけを正しく検査する。
- same epoch resume は通り、epoch 欠落・foreign digest・schema mismatch は lock 作成や追記より前に拒否する。
- 既存 T343/T530 pin は削除せず「epoch 不在の歴史値」として残し、新しい T817 current pin を追加する。

### 単位 B

正例:

- trusted snapshot 内に exact receipt + stdout を置き、stdout counter と WAL `verify_done.commits` が一致する場合だけ `eligible/recovered-same-run-stdout`。
- WAL に valid `commit_witness` が実在する current-shape record は `eligible/recorded-witness`。
- candidate を削除すると正例が必ず exclusion に反転し、探索が恒真でないことを示す。

負例:

- stdout/receipt 不在。
- raw stdout はあるが receipt 不在。
- t139 のような別 producer stdout。
- producer ID、lock SHA、WAL SHA、variant、record ordinal、trace binary、stdout SHA の各単独 mutation。
- duplicate/negative/noninteger/missing counter。
- `commit_counts != verify_done.commits`。
- `batch_commit_counts != 0`。
- 複数候補で曖昧。
- 別 attempt の witness 流用。
- pass tag/`verify_configs` 不一致。
- epoch key はあるが artifact digest が foreign。

consumer 回帰:

- [test_bench_first_real_wal.py:173–182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_bench_first_real_wal.py:173) の raw landscape key/fitness 期待は変更しない。
- historical `certified=True` を維持しつつ `selection_eligible=False` を検査する。
- `assert_complete`、`replay_evaluate`、`winner_tied_set` が同じ structured reason で拒否する。
- replay CLI が warning 後に ranking へ進まない。
- guided start は拒否時に directory/lock/meta/WAL を一切作らない。
- guided evaluate は拒否時に truncated WAL bytes を変えず repair receipt も作らない。
- guided result と `_log_eval` の直接呼出しでも gate を迂回できない。
- 既存 guided の lock-before-meta、tail repair、歴史 lock 非書換えテスト（[test_guided.py:275–313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_guided.py:275)、[test_guided.py:336–427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_guided.py:336)）は eligible fixture を明示して従来の期待を維持する。
- artifact-admission の exact classification map と historical admission 期待（[test_artifact_admission.py:749–759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_artifact_admission.py:749)、[test_artifact_admission.py:865–873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_artifact_admission.py:865)）は変更しない。
- 既存 witness gate/parser test（[test_campaign.py:6102–6223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_campaign.py:6102)、[test_campaign.py:6285–6304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-verifier-epoch/orchestrator/tests/test_campaign.py:6285)）を反転・緩和・削除・skip しない。

## 総括

要点は、named policy artifact の exact digest を独立した `campaign_verifier_epoch` として `search_config` に入れ、歴史 record の `certified` 事実を保持したまま、現行 replay/guided 選択だけを構造化 gate で止めることである。WAL・freeze・CCBench は一切変更しない。

最大のリスクは、実 P2-2 に権威ある same-run stdout/receipt が一件もなく、正しく実装すると P2-5 の全アームが停止することにある。これは brief の N1/N2 どおりで、黙って回避してはならない。

未解決点は stage 4 の再裁定である。推奨は「P2-5 は新しい certified landscape が得られるまで明示 unavailable」とすること。再開を求めるなら、scope 外の P2-2 再計測または人間レビュー済みの detached provenance artifact が必要であり、raw stdout 単体を same-run authority とみなす案は採用しない。