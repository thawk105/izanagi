単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 5 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- 段 4 裁定 (本 wave の正本。§4 プラン v2 と §5 変異事前登録を実装せよ):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s4-ruling.md`
- 親 brief (scope・不変条件・fixture 実測):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/brief-s1.md`
- 段 2 プラン (アンカー表・test 設計。裁定と食い違う箇所は裁定が優先):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s2-plan.md`
- 段 3 レンズ A (A-1/A-3/A-4 の具体的な負例値):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s3-A.md`
- 段 3 レンズ B (B-1 の fixture 衝突、B-2 の到達点):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s3-B.md`

# 段 5 — 実装 (Codex author、workspace-write)

あなたは izanagi の dev-wave 段 5 の実装子である。cwd は worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer` (branch `worktree-dev-wave-t2385-t2437-record-producer`、local main 34af5a571 と同一)。
**コードとテストだけを編集せよ。docs を編集するな。commit・push・branch 操作をするな。** commit は親が行う。

## 所有 (この 4 file だけを編集する)

- `orchestrator/campaign/reflux_result_evidence.py`
- `orchestrator/campaign/reflux_formal_consumer.py` (wrapper 差し替えと import だけ。判定式・reason code・受理集合は不変)
- `orchestrator/tests/test_reflux_result_evidence.py`
- `orchestrator/tests/test_reflux_formal_consumer.py`

**触ってはいけない:** `orchestrator/tests/reflux_origin_fixture_builder.py`、`orchestrator/tests/reflux_origin_fixture_baseline.json`、`orchestrator/tests/acceptance_duration_ledger.json` (親が実測後に更新)、`orchestrator/campaign/wal.py`、`orchestrator/campaign/pipeline.py`、`orchestrator/verifier/*`、`orchestrator/tests/test_verifier.py`、docs 全般。新しい file (test file・module) を作るな (`WAVE_PRODUCTION_FILES` 15 件 pin と自走 harness 登録に掛かる)。

## 実装内容 (裁定 §4 の逐語を正とし、ここは要約)

### `reflux_result_evidence.py`

1. `ResultEvidenceIssuanceRefused(ResultEvidenceError)` を 1 型追加。理由文字列は設計 §3.4 の行を人が識別できる内容。reason code の閉集合は作らない。
2. consumer の `_valid_witness_anomaly` (`reflux_formal_consumer.py:1155-1235`) と `_witness_class_sha256` (同 1237-1241) の**本体と定数** (`_ANOMALY_KEYS`、`_EDGE_KEYS`、`_REASON_REQUIRED_KEYS`、`_REASON_OPTIONAL_KEYS`、`_REASON_TYPES`、`_REASON_VERSION_KEYS`、`_PHENOMENA`、必要なら `_VERIFY_KEYS` 系) を `reflux_result_evidence.py` へ**逐語移動**し、public 名 `validate_witness_anomaly(anomaly) -> bool` と `witness_class_sha256(anomaly) -> str` (canonical_json_bytes の sha256、整列・重複排除・domain prefix を加えない。`ArtifactError` はそのまま伝播) にする。`RW/WR/WW` は `orchestrator.verifier.model` から import。
3. `DerivedPhysicalResult` (frozen dataclass: `build_attempt_id: str`, `outcome: Literal["accepted","rejected"]`, `constraint_sha256: str | None`)。
4. `derive_physical_result(*, ordered_wal_records: Sequence[Mapping], build_attempt_id: str, ordered_verifiers: Sequence[str], verify_result: VerifyResult | None = None) -> DerivedPhysicalResult`。**3 方向:**
   - **accepted:** `ordered_wal_records[-1]` の `stage == STAGE_COMMIT` (import は `orchestrator.campaign.model`)、payload の `build_attempt_id == build_attempt_id`、`tuple(payload["verify_configs"]) == tuple(ordered_verifiers)` (exact、空 tuple 不可)。`verify_result` は不要 (渡されたら `None` でないことを拒否するのではなく無視せず、**渡された場合は `certified is True` と `verdict == "serializable"` を要求**)。出力 `outcome="accepted", constraint_sha256=None`。
   - **rejected:** `verify_result` は exact `VerifyResult` (`type(...) is VerifyResult`) 必須。`vr.verdict == "non-serializable"`、`vr.serializable is False`、`vr.certified is False`、`vr.integrity.clean() is True`、`vr.total_cycles == len(vr.anomalies) == 1`。wire snapshot = `result_to_dict(vr)` から `trace_dir` を除いた dict。この snapshot に対し consumer `_validate_wal_outcomes` (1283-1394) と**同じ exact 検査** (key 集合、exact int、非負、counter 和、clean の 11 counter が exact int の 0、`anomaly_count == len(anomalies)`) を掛ける。`validate_witness_anomaly(snapshot["anomalies"][0])` 必須。terminal (`ordered_wal_records[-1]`) は `stage == STAGE_ABORT`、payload `build_attempt_id` 一致、`payload["reason"] == vr.verdict`、`canonical_json_bytes(payload["verify"]) == canonical_json_bytes(snapshot)` (**byte 同値**)。出力 `outcome="rejected", constraint_sha256=witness_class_sha256(snapshot["anomalies"][0])`。
   - **発行拒否:** 上記いずれにも該当しなければ `ResultEvidenceIssuanceRefused`。indeterminate、dirty integrity、切詰め (`total_cycles > len(anomalies)`)、空 anomaly、複数 anomaly、terminal 不一致 (stage / reason / verify の byte 不一致 / attempt)、非 production 構造、exact 型不一致 (bool/float) をすべて拒否。**複数 class から 1 件を選ぶな。cardinality を digest 計算より先に検査せよ。**
   - 裁定 A-3: `anomaly_count == len(anomalies)`、key 集合、`certified`/`serializable` の派生は **drift assertion** であり防護ではない。コード comment にその旨を 1 行書け (docs ではない)。
5. `assemble_result_evidence_record(*, origin_binding, trial_binding, ledger_member, p6_plan, trigger_binding, derived: DerivedPhysicalResult, ordered_wal_ref, execution_provenance_ref) -> dict`: 9 key exact record を組み、必ず `validate_result_evidence()` を通して返す。issuer/schema literal は caller に書かせない。
6. `issue_result_evidence_record(*, evidence_root: Path, record: Mapping) -> Path`: `resolve_content_addressed_ref` で `ordered_wal_ref` と `execution_provenance_ref` を**先に**解決 (不在・digest 不一致なら `ResultEvidenceError` 系で拒否、record は書かない)、その後に既存 `write_result_evidence_record()` を呼ぶ。
7. **S3 (ordered WAL projection producer) は書くな。** 裁定で scope 外。

### `reflux_formal_consumer.py`

- `_valid_witness_anomaly` と `_witness_class_sha256` を shared 呼び出しの wrapper にする。`_witness_class_sha256` の `ArtifactError → _ContractFailure(FC07)` 変換は wrapper に残す。定数は shared から import (名前は既存 test が参照する `C._ANOMALY_KEYS` 等が引き続き属性として解決できるように、module 属性として再 export せよ)。
- **判定式・reason code・受理集合を 1 bit も変えるな。** 差分は import と wrapper 本体だけ。

### tests (`test_reflux_result_evidence.py`)

- synthetic Silo source helper: `orchestrator/tests/test_verifier.py:41-63` と同型のものを **この file 内に複製** (test_verifier を import するな。module import 時に tmp を作る副作用がある)。`tmp_path` 配下に `cc/silo/CMakeLists.txt` と `transaction.cc` を書き、`verify_trace_dir(trace_dir, protocol="silo", ccbench_root=...)` で呼ぶ。fixture root は `orchestrator/tests/fixtures/<name>`。
- terminal WAL records の組立は `reflux_origin_fixture_builder._wal_records` の形 (`{variant, stage, env_tag, ts, payload}`、abort payload = `{reason, build_attempt_id, build_admission_receipt_sha256, verify, workload}`) を**手元で作る** (fixture builder は編集しない。import して使うのはよい)。commit の terminal payload は `pipeline.py:1818-1837` の形 (`verify_configs`、`build_attempt_id`、`build_admission_receipt_sha256`、`fitness_tps`、`note`)。
- 正例: accepted (commit terminal + exact `verify_configs`、`verify_result=None`)。rejected = `r9_dense_cycle4`・`r3_cycle3`・`r1_write_skew` を実走し、**同じ run の** snapshot を terminal abort payload に載せる。digest が `witness_class_sha256(result_to_dict(vr)["anomalies"][0])` と一致し、独立に `hashlib.sha256(canonical_json_bytes(...))` で再計算した値とも一致。
- 発行拒否負例 (すべて `pytest.raises(ResultEvidenceIssuanceRefused)`、**record も path も生まれない**ことを assert): `integrity_orphan`・`m2_version_dup` (indeterminate)、`r4_mixed_cycle` (non-serializable かつ dirty)、r9 `max_report=0` (切詰め)、`r8_silo_broken_norw` (4 class) と r8 `max_report=1` (capped: `total_cycles=4 > 1`)、terminal 不一致 3 種 (abort だが `verify` が別 run [r3] の snapshot / `reason="indeterminate"` で verify は r9 / accepted で `verify_configs=["wrong"]`)、exact 型負例 3 件 (typed `VerifyResult` の `n_txns=True`、`anomalies[0].cycle` に `True`、reason version に `1.0` — `dataclasses.replace` や直接構築で作る)、非 production 構造 3 種 (unknown phenomenon / ring 不一致 / unknown reason type — 実 r9 の anomaly dict を 1 箇所だけ壊す)。
- assembler / issuer: validate 迂回負例 (欠 key の入力で `ResultEvidenceError`)、参照先不在で record path が存在しない、正常系で create-only path に 9 key record が書かれ `parse_result_evidence_bytes` で読める、二重発行が拒否される。
- **test 名・docstring は「synthetic Silo source 束縛下」「formal-consumer contract」に限定し、production 到達性を主張しない** (裁定 B-5)。
- 期待値へ揮発 payload (tmp path、working tree hash) を焼き込むな。

### tests (`test_reflux_formal_consumer.py`)

- 端から端 1 本: r9 を 1 度だけ実走し、その snapshot を terminal abort payload に載せた records で `reflux_origin_fixture_builder` の override 経路 (`build_ordered_wal_projection` / `build_execution_provenance` / `build_result_evidence_record` の `**overrides`、`write_evidence_tree`、`build_fixture_repository` 等。現物を読め) から **新しい tmp の evidence tree** を組む。33 record の `physical_result` は producer (`derive_physical_result` + `assemble_result_evidence_record`) が作る (全 33 で同じ r9 class。FC09 は class 集合の一致を要求する)。sealed member は `map_result_evidence_to_sealed_member` (または既存 `_sealed_member`) で raw bytes から写す。`evaluate_formal_origin` が `FormalContractRejected(FC07)` でなく `P6Unavailable` を返すことを assert。**fixture の既存 physical root へ追記・上書き・削除をするな** (裁定 B-1)。docstring に「salts は不変・未行使、ledger replay は要求しない」(B-2) と書け。
- 既存 `test_fc07_converts_witness_canonicalization_artifact_error` (1874) の monkeypatch owner を shared module (`reflux_result_evidence.canonical_json_bytes` 相当) へ変え、FC07 変換が保たれることを維持。**既存 test の期待値を変えるな** (反転・緩和・skip・削除禁止。赤なら実装が誤り)。
- 既存 `test_consumer_source_has_no_nonaborted_construction_or_success_variant` (2088) は 15 file の AST 走査。新 module を作らなければ影響しない — 実走で確かめよ。

## 検査・報告 (すべて必須)

- 実走: `PYTHONPATH=. python3 -m pytest orchestrator/tests/test_reflux_result_evidence.py orchestrator/tests/test_reflux_formal_consumer.py orchestrator/tests/test_reflux_origin_fixture_builder.py orchestrator/tests/test_plain_runner_coverage.py orchestrator/tests/test_verifier.py -x -q -p no:cacheprovider` を通し、**緑には実走 nodeid の範囲と件数を併記**せよ。sandbox で pytest が走らない場合は「実装済み・未実走」と書き、`closed` と申告するな。`python -m pytest` が guard に拒否されるなら `PYTHONPATH=. python3 orchestrator/tests/<file>` の自走 harness を試せ。
- `git diff --stat` と、`git diff --exit-code -- orchestrator/tests/reflux_origin_fixture_builder.py orchestrator/tests/reflux_origin_fixture_baseline.json orchestrator/campaign/wal.py orchestrator/campaign/pipeline.py orchestrator/verifier` が rc=0 であることを報告せよ (不変条件)。
- 新規 test nodeid を **collection 名で** 全列挙せよ (親が受入所要台帳へ `--add-only` で足す)。parametrize の ID は明示せよ。
- 完了報告に、所有外 caller・共有 fixture・consumer test への波及可能性を静的列挙せよ (`grep -rn "_witness_class_sha256\|_valid_witness_anomaly\|_ANOMALY_KEYS"` の全 hit)。
- 現行の受理・拒否挙動 (consumer) を変えていないことを、既存 FC07 test 全件の緑で示せ。指示外の受理集合変更をするな。
- テストを甘くして緑にするな。fixture への現行 hash 差し込み禁止。機構の正例・負例は実 fixture・実 verifier を名指しし、依存先を stub するな。
- 裁定 §5 の変異 M1〜M14・M-C1 を**自分でも 1 件ずつ静的に**辿り、各変異を殺す nodeid が実在することを表にせよ (実走は親)。殺せない変異があれば test を足すか、等価変異の理由を書け。
- 予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。無出力が最悪である。

## 出力形式

H2 見出しで「編集面 (file:line)」「実走結果 (nodeid 範囲・件数・rc)」「不変条件の検査結果」「新規 nodeid 一覧」「変異×nodeid 表」「波及の静的列挙」「未完・未実走」を順に書き、最後に `## 総括` (5 行以内) を必ず置け。出力へ結合文字 U+0300〜U+036F を使うな。
