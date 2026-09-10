## 1. 方向の確認

1. WAL 側は現行 consumer が production abort の `reason` と `verify` のみを検査しており、旧 3 field は campaign 内に存在しない。[reflux_formal_consumer.py:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1283) [pipeline.py:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:1601)
2. record の `constraint_sha256` は ledger member と FC04 で一致し、WAL anomaly digest と FC07 で一致し、class 集合と FC09 で一致する。[reflux_formal_consumer.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:856) [reflux_formal_consumer.py:1391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1391) [reflux_formal_consumer.py:1398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1398)
3. これらの等式を保ったまま consumer 側へ寄せる余地はない。反証は見つからず、record 層 producer 新設を支持する。

ledger 自体も rejected には constraint digest を必須、accepted と tombstoned には不在を要求するため、consumer 緩和では解決できない。[reflux_origin_ledger.py:703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_origin_ledger.py:703)

## 2. 編集面のアンカー表

| file / 現行アンカー | 種別 | 計画する変更 | 見込み |
|---|---:|---|---:|
| [reflux_result_evidence.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:14), [同:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:35) | 変更 | `VerifyResult`、`result_to_dict`、layout 型の import と新 API の `__all__` 登録 | 15〜20 行 |
| [reflux_result_evidence.py:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:138) | 追加 | `ResultEvidenceIssuanceRefused`、`DerivedPhysicalResult`、`ResultEvidenceRecordInputs` | 30〜45 行 |
| [reflux_result_evidence.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:236) の前後 | 追加 | `witness_class_sha256()`、rejected wire/anomaly の producer 側 exact 検査、`derive_physical_result()` | 180〜230 行 |
| [reflux_result_evidence.py:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:444) の前後 | 追加 | `assemble_result_evidence_record()` と referent read-back 後に既存 writer を呼ぶ `issue_result_evidence_record()` | 55〜80 行 |
| [reflux_result_evidence.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:618) の近傍 | 追加 | `write_ordered_wal_projection()`。`ordered_attempt_frames()` を用いた S3 | 60〜85 行 |
| [reflux_formal_consumer.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:69), [同:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1237) | 変更 | P1 の shared digest import と既存 wrapper 内の式の差し替えだけ。`ArtifactError -> FC07` 変換は残す | 4〜7 行 |
| [test_reflux_result_evidence.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:1), [同:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:374) | 追加 | synthetic Silo helper、S1/S2/S3 の実 fixture 正負例、直接負例 | 220〜280 行 |
| [test_reflux_formal_consumer.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:1404) | 追加・小変更 | producer 由来 record/projection の FC07 端から端正例。P1 の canonicalization error test は monkeypatch 対象を shared helper 所有 module へ変更 | 90〜125 行 |
| [acceptance_duration_ledger.json:11780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/acceptance_duration_ledger.json:11780) | 追加 | 実測 JUnit から新 nodeid のみ `--add-only` 追加 | 約 22 行 |

削除する file/function はない。`wal.py`、fixture builder、fixture baseline、golden literal は変更しない。総差分はおよそ 650〜790 行を見込む。

## 3. S1 の署名と 3 方向の分岐

提案署名は次とする。

```python
def derive_physical_result(
    *,
    verify_result: VerifyResult,
    build_attempt_id: str,
) -> DerivedPhysicalResult:
    ...
```

```python
@dataclass(frozen=True, slots=True)
class DerivedPhysicalResult:
    build_attempt_id: str
    outcome: Literal["accepted", "rejected"]
    constraint_sha256: str | None
```

入力は exact `VerifyResult` に限定し、abort payload dict 用の public 経路は置かない。発行不能時は `ResultEvidenceIssuanceRefused(ResultEvidenceError)` を送出し、record は返さない。

| 設計 §3.4 | producer 条件と出力 | consumer との対応 |
|---|---|---|
| accepted | `verify_result.certified is True`、`verdict == "serializable"`、`serializable is True`。`outcome="accepted"`、`constraint_sha256=None` | record schema の accepted/null 条件は [reflux_result_evidence.py:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:304)。production commit は certified を前提にする [pipeline.py:1805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:1805)。terminal commit と verifier 順序は FC07 が引き続き検査する [reflux_formal_consumer.py:1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1275)。 |
| rejected + 単一 class | `verdict == "non-serializable"`、`serializable is False`、`certified is False`、`integrity.clean() is True`。`result_to_dict()` から `trace_dir` を除いた値を consumer と同じ exact schema/type/構造条件で検査し、`anomaly_count == len(anomalies) == total_cycles == 1`。`constraint_sha256=witness_class_sha256(anomalies[0])` | production abort は verdict を `reason` とし、同じ report dict を `verify` に載せる [pipeline.py:1594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:1594)。consumer の wire/schema、clean、cardinality、digest 条件は [reflux_formal_consumer.py:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1283)〜1394 に対応する。 |
| 発行拒否 | 上記 2 枝以外。indeterminate、dirty integrity、空・切詰め・複数 anomaly、unknown kind、構造不整合、report schema/type 不整合をすべて拒否 | §3.4 の「record を発行しない」。ledger へは既存 tombstone mapper [reflux_result_evidence.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:820) を使う。 |

`result_to_dict()` は `anomaly_count` を `len(res.anomalies)` から作るため [report.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/report.py:96)、P2 の typed 経路では両者の不一致は構築不能である。それでも producer 内で wire 化後に exact equality を assert し、consumer 契約との drift を検出する。

塞ぐべき隙間は次のとおり。

- `total_cycles` を見ず最初の anomaly を選ぶ: `type(total_cycles) is int` と `total_cycles == anomaly_count == len(anomalies) == 1` で拒否。
- `max_report=0` の空 list: `len(anomalies) == 1` で拒否し、`anomalies[0]` へ進まない。
- 複数 class から 1 件を選ぶ: cardinality を digest 計算より先に検査する。
- dirty な non-serializable: `VerifyResult.verdict` は cycle を先に見て non-serializable になりうるため [model.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/model.py:503)、`integrity.clean() is True` を独立条件にする。
- wire counter だけが 0 だが非 wire proof surface/commit witness が dirty: typed `Integrity.clean()` は両者も検査するため、consumer より強い条件になる。[model.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/model.py:445)
- unknown phenomenon/reason、ring 不整合、version shape 不整合: consumer の `_valid_witness_anomaly()` [reflux_formal_consumer.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1155) と同じ閉集合・導出関係を producer 側でも検査する。
- forged stats/integrity shape: wire 化した report に対し consumer の exact key、exact int、非負、counter sum 条件を同じ順序で検査する。

## 4. (P1)〜(P4) の裁定案

### P1: 支持

`witness_class_sha256(anomaly)` を `reflux_result_evidence.py` に置き、式を次の 1 箇所へ寄せる。

```python
hashlib.sha256(canonical_json_bytes(anomaly)).hexdigest()
```

consumer の `_witness_class_sha256()` は削除せず、shared helper を呼ぶ wrapper として残す。現在の `ArtifactError` を `_ContractFailure(FC07)` へ変換する境界 [reflux_formal_consumer.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1237) は変えない。

受理集合不変の根拠は以下で示す。

- helper 本体は現行式の逐語移動で、整列・重複排除・domain prefix を加えない。
- `test_fc07_converts_witness_canonicalization_artifact_error` [test_reflux_formal_consumer.py:1874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:1874) の monkeypatch 対象だけ shared module へ変え、FC07 変換を保持する。
- FC07 の全既存正負例と、実 r9 anomaly に対する独立 canonicalizer の digest 一致を走らせる。

### P2: 支持

exact `VerifyResult` を第一かつ唯一の public 入力にする。理由は `Integrity.clean()` が wire にない `proof_surfaces` と commit witness まで検査するためである。[model.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/model.py:450)

abort payload dict 経路は、自己申告の `integrity.clean` を producer が再認証できず、typed 経路より受理集合が広くなるため採らない。必要な production wire bytes は内部で `result_to_dict()` を一度だけ呼び、pipeline と同じく `trace_dir` を除いて得る。[pipeline.py:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:1601)

### P3: 条件付きで支持

S3 は完全な全域逆関数ではなく、単一連続区間に限る fail-closed な逆関数として本 wave に含める。

既存 `wal.ordered_attempt_frames()` は物理行の `byte_start`、終端 LF を含む `byte_end`、raw bytes を返す。[wal.py:1671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/wal.py:1671) producer は次のように境界を決める。

- `byte_start = frames[0].byte_start`
- `byte_end = frames[-1].byte_end`
- 全隣接 frame について `previous.byte_end == current.byte_start`
- `source_wal_bytes[byte_start:byte_end]` を `_canonical_wal_interval()` に通した値が projection の `records` canonical bytes と一致
- `source_wal_ref.sha256` は区間でなく、`layout.wal_file` 全 bytes の sha256
- source と projection path は `evidence_root` 配下に限定し、projection は既存 create-only writer と read-back を使う

production WAL は compact JSON 1 record + LF で追記される。[wal.py:1266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/wal.py:1266) `layout.wal_file` は `<campaign>/runs/wal.jsonl` である。[layout.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/layout.py:207)

現行 test は attempt A、B、A の interleave が起こりうる API 形を固定している。[test_reflux_result_evidence.py:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:374) この場合、単一区間では foreign record が混ざり `_resolve_ordered_wal()` の exact comparison [reflux_result_evidence.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:677) を満たせないので、producer は projection を発行しない。schema の一般化はしない。

### P4: 支持

`ResultEvidenceIssuanceRefused` という派生型 1 個と説明文字列にする。文字列は §3.4 の行を識別できる内容にするが、stable reason code の閉集合は新設せず、test も原則として例外型と発行物不在を pin する。

## 5. 正例・負例の設計

実 verifier 呼出しは [test_verifier.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_verifier.py:41)〜62 と同じ synthetic Silo source を tmp 配下に構築して束縛する。

| 新 nodeid | 分岐 / 殺す不具合 |
|---|---|
| `test_derive_physical_result_accepts_real_fixture[g4_rw_no_cycle]` | accepted。RW edge の存在だけで rejected にする誤りを殺す。 |
| `...[g1_serial]` | accepted。通常 serializable の基本枝。 |
| `...[p1_phantom_skew]` | accepted。別 trace 形でも certified を読むことを固定。 |
| `test_derive_physical_result_derives_rejected_real_single_class_fixture[r9_dense_cycle4]` | rejected。実 4-cycle の digest を導く。 |
| `...[r3_cycle3]` | rejected。cycle 長を 2 に固定する誤りを殺す。 |
| `...[r1_write_skew]` | rejected。実 G2 2-cycle の基本枝。 |
| `test_derive_physical_result_refuses_real_indeterminate_fixture[integrity_orphan]` | 発行拒否。serializable graph だけを accepted にする誤りを殺す。 |
| `...[m2_version_dup]` | 発行拒否。別 integrity 軸でも同じ。 |
| `test_derive_physical_result_refuses_max_report_zero_truncation` | r9 + `max_report=0`。空 anomaly から class を捏造する実装を殺す。 |
| `test_derive_physical_result_refuses_real_multiple_witness_classes` | `r8_silo_broken_norw` の 4 anomaly。先頭 1 件選択を殺す。 |
| `test_derive_physical_result_refuses_capped_multiple_witness_classes` | r8 + `max_report=1`。`len(anomalies)==1` だけで非切詰めとみなす誤りを殺す。 |
| `test_derive_physical_result_refuses_dirty_nonserializable_result` | r9 の typed result に integrity 違反を加える。verdict だけを見る誤りを殺す。 |
| `test_derive_physical_result_refuses_nonproduction_witness_shape[unknown-phenomenon]` | unknown kind の digest 発行を殺す。 |
| `...[ring-mismatch]` | edge と cycle の ring 不一致を殺す。 |
| `...[unknown-reason-type]` | reason 閉集合の欠落を殺す。 |
| `test_shared_witness_class_sha256_matches_independent_real_report` | r9 report を独立 canonical JSON + sha256 と比較し、式 drift を殺す。 |
| `test_assemble_and_issue_result_evidence_uses_derived_result_create_only` | S1→S2→既存 writer。9 key、参照解決、deterministic path、二重発行拒否を固定。 |
| `test_assemble_result_evidence_validates_every_input_before_write` | assembler が `validate_result_evidence()` を迂回する変異を殺す。 |
| `test_issue_result_evidence_resolves_referents_before_creating_record` | missing referent 時に final record が残らないことを固定。 |
| `test_ordered_wal_projection_producer_round_trips_nonzero_contiguous_range` | prefix frame 後の nonzero start、LF 込み end、source digest、resolver round-trip を固定。 |
| `test_ordered_wal_projection_producer_refuses_interleaved_attempt` | A/B/A を連続区間として偽装する実装を殺す。 |

複数 class の実 trace は存在する。`fixtures/r8_silo_broken_norw` について既存 test が clean integrity、`len(anomalies) == total_cycles == 4` を固定している。[test_verifier.py:1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_verifier.py:1663) よって synthetic `VerifyResult` 合成は不要である。

## 6. 端から端の正例

新 nodeid は次とする。

`test_real_dense_cycle4_producer_record_and_projection_pass_fc07_to_p6_unavailable`

既存 `case` fixture は 33 record、sealed member、physical root、recovery envelope を組み上げる。[test_reflux_formal_consumer.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:350)

test の組立は以下とする。

1. synthetic Silo source へ束縛して `r9_dense_cycle4` を一度だけ実 verifier 走する。同じ run の `VerifyResult` と report dict を WAL と digest の両方へ使い、process 間の reason 順序差を持ち込まない。
2. 33 個の各 physical root 内に live JSONL WAL を作る。既存 trigger binding を `wal.log_trigger_binding()` で書き、その直後に pipeline `_abort()` と同じ `{reason, build_attempt_id, build_admission_receipt_sha256, verify, workload}` terminal を `wal.log()` で書く。[pipeline.py:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:1249)
3. 各 WAL に S3 producer を呼び、physical root 配下へ新しい projection を create-only で書く。source/projection が planned root 配下である条件は [reflux_formal_consumer.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1027) が検査する。
4. 各元 record の origin/trial/ledger/p6/trigger binding を保ち、S1 の `DerivedPhysicalResult` と新 projection ref を S2 assembler に渡す。execution provenance は fixture の既存 v2 referentを使う。
5. raw record bytes から `map_result_evidence_to_sealed_member()` を呼び直し、33 member の `evidence_digest`、`outcome`、`constraint_sha256` を更新する。[reflux_result_evidence.py:800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:800)
6. `evaluate_formal_origin()` を呼び、`FormalContractRejected(FC07)` ではなく `P6Unavailable` を assert する。[reflux_formal_consumer.py:1579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1579) [同:1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1610)

必要な束縛は次のとおり。

- `constraint_sha256`: 全 33 member で同じ r9 anomaly digest。record/member 等式は FC04 [reflux_formal_consumer.py:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:875)、集合等式と `kmax=1` は FC09 [同:1398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1398) が要求する。1 record だけ差し替える方法では二 class となるため不可。
- `evidence_digest`: 各 raw record bytes の sha256。fixture helper の現行写像は [test_reflux_formal_consumer.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:179)。
- WAL trigger binding: record/provenance/WAL の 3 者を同値に保つ。FC05C は [reflux_formal_consumer.py:1046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1046)〜1105。
- `build_attempt_id`: record、projection records、terminal payload、execution provenance を同じ値に保つ。[reflux_result_evidence.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:668) [reflux_formal_consumer.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:899)

fixture が valid な `execution-provenance/v2` を供給するため、test 到達に欠ける材料はない。ただし、これは execution-provenance の production issuer や 33 physical run の本番呼び手を証明しない。

## 7. 不変条件の維持

- 規律 2:
  - indeterminate、dirty non-serializable、r9 `max_report=0`、r8 full、r8 `max_report=1`、unknown/ring/reason 不整合をすべて producer 単体で `ResultEvidenceIssuanceRefused` にする。
  - consumer を呼ばない直接 test にすることで、FC07 が後段で拒否して変異を隠すことを防ぐ。
  - 複数 anomaly test は「例外型」「record/projection path 不在」を assert し、先頭選択を許さない。
- fixture/golden bytes:
  - fixture builder と baseline JSON は編集対象外。
  - 既存 `test_canonical_bytes_are_independently_pinned_without_a_trailing_lf`、hash layer 1〜3、wrong-domain test [test_reflux_result_evidence.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:150) を走らせる。
  - `test_baseline_schema_and_every_entry_match_independent_recalculation` [test_reflux_origin_fixture_builder.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_origin_fixture_builder.py:107) を追加の byte pin として走らせる。
  - fixture/baseline file に差分がないことを `git diff --exit-code --` で確認する。
- schema と ledger 写像:
  - 既存 exact 9-key、accepted/null、rejected digest、tombstone、§3.5 mapping test を保持する。
  - assembler は必ず `validate_result_evidence()` を通し、issuer/schema literal を caller に書かせない。
- create-only 順序:
  - S3 projectionの write/read-back、execution provenance の digest resolution、record write の順を test する。
  - referent 不在時には record final path が存在しないこと、二回目は overwrite されないことを assert する。
- S3 byte 不変:
  - nonzero prefix、各 LF、source whole-file digest、projection canonical bytesを独立計算する。
  - interleave と truncated tail は projection を残さず拒否する。
- consumer:
  - 判定式、reason code、受理集合は変更しない。P1 wrapper の例外変換を含む FC07 全 test を回す。

この段では test を実行しておらず、緑とは報告しない。

## 8. pin 閉包の裏取り

親 brief の暫定判断には 1 件見落としがある。

4 golden 定数のうち raw record digest と同じ値が、[reflux_origin_fixture_baseline.json:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/reflux_origin_fixture_baseline.json:23) にも固定されている。これは [test_reflux_origin_fixture_builder.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_origin_fixture_builder.py:107) が全 builder の digest と length を独立再計算して強制する。したがって executable pin は「golden 4 個 + fixture baseline entry + acceptance ledger nodeid」である。

その他の確認結果:

- 4 literal の別参照は、上記 fixture baseline の raw digestを除けば `test_reflux_result_evidence.py:24-27` のみ。
- `test_reflux_result_evidence.py` と `test_reflux_formal_consumer.py` は既に pytest-only allowlist に登録済み。[README.md:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/README.md:144) [README.md:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/README.md:151)
- 新 test file は作らないため、自走 harness や README への追加は不要。新 file を作る案は、メタテストが要求する harness/allowlist 更新 [README.md:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/README.md:114) を増やすだけなので採らない。
- coverage gate は実 collection node の 90% を要求する。[test_acceptance_schedule_order.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_acceptance_schedule_order.py:704)
- 台帳更新は既存値を byte exact に保つ `--add-only` を使う。[update_acceptance_duration_ledger.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/tools/update_acceptance_duration_ledger.py:83)
- 既存台帳には `test_execution_provenance_is_closed_and_nonempty[wrong-version]` が残る一方、現行 param ID は `v1` など 11 件である。[test_reflux_result_evidence.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:197) [acceptance_duration_ledger.json:11791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/acceptance_duration_ledger.json:11791) これは既存 drift であり、本 wave では cleanup せず、新 nodeid の add-only 追加だけを行う。

## 9. 変異候補の事前登録

すべて consumer を通さない producer 直接 test、または producer の成功を期待する round-trip testへ照準する。

| 変異候補 / 実装後の見込み位置 | 殺す nodeid |
|---|---|
| M1: `derive_physical_result` の accepted 条件を `serializable is True` だけへ緩和。現行 :236 後の新 S1 block | `test_derive_physical_result_refuses_real_indeterminate_fixture[integrity_orphan]` |
| M2: rejected から `integrity.clean()` 条件を削除 | `test_derive_physical_result_refuses_dirty_nonserializable_result` |
| M3: `len(anomalies) == 1` を `>= 1` にし先頭を選択 | `test_derive_physical_result_refuses_real_multiple_witness_classes` |
| M4: `total_cycles == anomaly_count` を削除 | `test_derive_physical_result_refuses_capped_multiple_witness_classes` |
| M5: zero anomaly の発行拒否を削除 | `test_derive_physical_result_refuses_max_report_zero_truncation` |
| M6: producer の witness 構造検査を削除 | `test_derive_physical_result_refuses_nonproduction_witness_shape[ring-mismatch]` |
| M7: class digest を canonical anomaly bytes 以外から計算 | `test_shared_witness_class_sha256_matches_independent_real_report` |
| M8: rejected branch の `outcome` を accepted に置換 | `test_derive_physical_result_derives_rejected_real_single_class_fixture[r9_dense_cycle4]` |
| M9: accepted branch に非 null constraint を設定 | `test_derive_physical_result_accepts_real_fixture[g1_serial]` |
| M10: assembler の `validate_result_evidence()` 呼出しを削除 | `test_assemble_result_evidence_validates_every_input_before_write` |
| M11: referent resolution より先に record writer を呼ぶ | `test_issue_result_evidence_resolves_referents_before_creating_record` |
| M12: S3 の `byte_start` を常に 0 にする | `test_ordered_wal_projection_producer_round_trips_nonzero_contiguous_range` |
| M13: S3 の `byte_end` から終端 LF を除く | `test_ordered_wal_projection_producer_round_trips_nonzero_contiguous_range` |
| M14: S3 の frame 隣接性検査を削除 | `test_ordered_wal_projection_producer_refuses_interleaved_attempt` |

`anomaly_count == len(anomalies)` を単独で削る変異は、P2 の `result_to_dict(VerifyResult)` が count を `len()` から生成するため等価変異になる。登録しない。`certified` と `verdict` の整合も exact `VerifyResult` の property から同時に導かれるため、単純な片方削除変異は避ける。

## 10. 事前予測

- 予測: r9 の class digest は一致する。producer と consumer が同じ run の `result_to_dict()["anomalies"][0]` を、同じ shared `canonical_json_bytes` 式で hash するためである。[report.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/report.py:134) 外れうるのは test が verifier を二度走らせ、scope 外の reason 順序非決定性を跨いだ場合なので、一回の結果を再利用する。
- 予測: golden 4 個と fixture baseline は不変。既存 fixture builderを変更せず、新 assemblerは既存 builderから呼ばれないためである。
- 予測: 台帳追加前の coverage gate は赤になる可能性が高い。現在値が 90%直上で、新規約 22 node が未登録のまま collection 母数へ加わるためである。
- 予測: 新 node の実測 JUnit を `--add-only` で加えれば 90%超へ戻る。外れうるのは param ID の実 collection 名が計画名と異なる場合、または同時に別 wave の未登録 node が着地した場合である。

## 総括

方向は D1768 を再開せず、`reflux_result_evidence.py` に record producer を新設する。  
編集面は production 2 file、既存 test 2 file、所要台帳 1 fileで、約 650〜790 行を見込む。  
P2 は exact `VerifyResult`、P3 は連続 WAL 区間だけを扱う fail-closed な逆関数、P4 は派生例外 1 型を支持する。  
最大の不確実点は S3 の source WAL が digest 採取後に追記されないという issuer 最終化時点の保証である。  
裁定パッケージ候補はなく、execution-provenance issuer と本番呼び手などは明示どおり scope 外に残す。