## 前提の検算

### (P1-a) 第 2 部品は純増ゼロ

**支持する。** 既存経路は D1244 の launcher 要件をすでに満たす。

- job body は `backoff_sweep.py <workload>` を screening option なしでちょうど 1 回呼ぶ: `tools/pegasus/a5_second_boot_backoff_sweep.sh:589-592`。
- job body の受理 workload は `write-heavy|balanced` に閉じる: 同 `:202-206`。
- login 側投入器は同じ 2 workload を固定 fan-out する: `tools/pegasus/submit_a5_second_boot_backoff_sweep.sh:92-101,169-190`。
- 契約テストは呼出し回数 1、`--screening` 不在、workload 集合を固定する: `orchestrator/tests/test_a5_second_boot_job_contract.py:177-187,273-299,332-371`。
- job body と投入器は登録済み: `tools/pegasus/admission_registry.json:10-15,304-309`。

ただし A-5 の名前と受理集合は D1100 用である。`a5-second-boot-*` の schema、boot evidence、2 workload fan-out に束縛される: `tools/pegasus/a5_second_boot_backoff_sweep.sh:434-449,770-794`、`tools/pegasus/submit_a5_second_boot_backoff_sweep.sh:85-92,109-130`。T-1998 への束縛は launcher の改造ではなく、第 3 部品の専用 consumer と後続の人間による preregistration で行う。これなら A-5 側の受理集合を 1 bit も変えない。

### (P1-b) 独立 consumer が必要

**支持する。** A-5 finalizer は固定 pair の選択だけは正しいが、T-1998 consumer そのものではない。

finalizer の入力は次のとおり。

- argv: job repo、output root、workload、PBS job/node/boot、repository commit、CCBench gitlink: `tools/pegasus/a5_second_boot_backoff_sweep.sh:593-607`。
- campaign の `campaign.lock` と `runs/wal.jsonl`: 同 `:620-647`。
- 8 genome 全部の `build_start.genome`、`bench_done.tps/median_tps/perf_observation`、`commit.fitness_tps`: 同 `:649-701`。
- 各 attempt の `build_done.toolchain`: 同 `:703-721`。
- `reservation.json.node_boot_evidence` と `.source_binding`: 同 `:753-768`。

出力は `result.json` 1 個で、次を持つ。

- fixed pair の samples、median、ratio、improvement: 同 `:770-780`。
- campaign ID、WAL/lock SHA、node/boot/source identity: 同 `:781-790`。
- toolchain、perf preflight、counter status: 同 `:791-794`。
- temporary file、hard link、directory fsync による publish: 同 `:795-816`。

固定選択は `BACK_OFF=0,BACKOFF_FIXED=-1` と、balanced では `BACK_OFF=1,BACKOFF_FIXED=5`: 同 `:615-618,735-749`。argmax は使わない。一方で `:681-721` は全 8 点の TPS を読み、次が不足する。

- `CertifiedCampaignView` を通さず、直接 `wal.replay()` を使う: 同 `:639-643`。
- persisted verifier receipt の public admission を呼ばない。
- `BACKOFF_NOINLINE=1` 用の専用拒否署名がない。
- `unstable=True` を inconclusive にする分岐がない。
- workload が `write-heavy` なら target が 10 us になるため、T-1998 の balanced 固定 5 us consumer ではない。

既存 report はさらに static 点の argmax を使い、unstable が届かないことを自認する: `orchestrator/campaign/backoff_sweep_report.py:66-89,141-158`。

### (P1-c) producer schema の拡張は不要

**条件付きで支持する。** consumer は `result.json` 単体ではなく、同 root の reservation、campaign lock、WAL を public certified admission 経由で読む必要がある。

| evidence | producer 成果物と field | consumer 側の再検証 |
|---|---|---|
| repository commit / gitlink | `result.json.repository_commit`、`.ccbench_commit`: A-5 job `:789-790`。`reservation.json.source_binding.repository_commit`、`.ccbench_gitlink_commit`: 同 `:443-446` | result と reservation を一致させ、preregistration から渡された期待 commit/gitlink と exact 比較する。job 自身も HEAD を `A5_EXPECTED_HEAD` と比較し、gitlink を `ls-tree` から取る: 同 `:242-247,363-376` |
| CCBench source evidence | WAL `build_start.payload.genome/src_token/build_admission.source`: `orchestrator/campaign/pipeline.py:1234-1247` | certified admission が genome SHA、src token、lock の `ccbench_commit`、variant ID を再検証する: `orchestrator/campaign/artifact_admission.py:1399-1427` |
| environment contract digest | `campaign.lock.authority.environment_contract_sha256` と各 COMMIT の `payload.contract_sha256`: `orchestrator/campaign/pipeline.py:1845-1855` | WAL topology が lock、COMMIT、`env_tag` の一致を検証する: `orchestrator/campaign/wal.py:2044-2117` |
| trace-disabled 性能 build | WAL `build_done.payload.perf_configure_cmd`、`.perf_bin_sha256`: `orchestrator/campaign/pipeline.py:1400-1412`。`bench_done.payload.run_cmd`: 同 `:838-874` | configure argv の `-DCCBENCH_TRACE=0`、build directory、bench executable の対応を検査する。producer は trace/perf を別 build し、性能側を `trace=False` で作る: 同 `:1317-1348` |
| `BACKOFF_NOINLINE=0` | WAL `build_start.payload.genome` と `build_done.payload.perf_configure_cmd` | exact genome に `BACKOFF_NOINLINE=1` がなく、configure override もないことを確認する。preregistered repository commit の patch default は 0: `patches/silo-backoff-fixed.patch:13-15,52-57`。`1` が現れたら診断 build として専用 reject |
| toolchain manifest | WAL `build_done.payload.toolchain`、`.toolchain_record_sha256`: `orchestrator/campaign/pipeline.py:1361-1399`。result の `.toolchain`: A-5 job `:791` | 2 arm の manifest と record digest の exact 一致、result への投影一致を検査する |
| verifier receipt | WAL COMMIT の `payload.commit_verification_receipt` | `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` が全 COMMIT を検証する: `orchestrator/campaign/artifact_admission.py:733-834,1472-1513`。選んだ 2 COMMIT にはさらに public `admit_replay_evidence()` を通す: `orchestrator/verifier/commit_receipt.py:387-445` |

到達性の限界は二つある。

- full `--version` 本文は公式 output に残らず、WAL には短い `toolchain` manifest と full record の digest だけが残る。2 arm の identity 一致には足りるが、full 本文の後日再ハッシュまではできない。
- `BACKOFF_NOINLINE=0` は単一 field ではなく、exact genome、configure command、記録 commit にある default の組合せで導出する。

今回の受理条件には両方とも足りるため schema は拡張しない。full toolchain 本文や明示的な `backoff_noinline: 0` を単独 field として要求する裁定へ変わる場合だけ、限定拡張が必要になる。

### (P1-d) 実環境で現物へ到達できる

**現行の 2026-09-07 balanced run については反証する。** WAL は存在し、8/8 COMMIT と anomaly 0 まで到達したが、driver 終了処理の rc=1 により finalizer が走らず `result.json` がない: `a5-measured.md:14-29`。したがって現在記録された 3,803,883 / 4,294,095 TPS は新 consumer の正例にならず、`producer-artifact-missing` で reject する。

コード上は、将来の正常終了した A-5 balanced root なら全入力 field へ到達できる。既存値を D1100 の充足へ読み替えない条件も維持する: `a5-measured.md:44-46`。

## 第 1 部品 — producer evidence の read-only 到達性監査

新規 `output/insights/2026-09-08_t1998-stock-inline-evidence/README.md` を次の構成で追加する。

- 予定 `:1-14`: scope、D1244/D20/D1137、測定未実走を明記。
- 予定 `:15-48`: 上記 6 evidence の artifact/field 対応表。
- 予定 `:49-65`: A-5 finalizer が全 8 点を読むが fixed pair だけを選ぶという境界。
- 予定 `:66-78`: full toolchain 本文と明示的 noinline field の限界。
- 予定 `:79-90`: 2026-09-07 balanced root は `result.json` 欠損につき非受理、schema 拡張不要という結論。

既存の成果物 bytes は変更せず、新しい insight だけを足す。

## 第 2 部品 — 薄い sanctioned launcher

**純増ゼロ byte、実装しない。**

根拠は次のとおり。

- non-screening の `backoff_sweep.py <workload>` を 1 回だけ起動済み: `tools/pegasus/a5_second_boot_backoff_sweep.sh:589-592`。
- balanced は job body の閉じた受理集合に含まれる: 同 `:202-206`。
- job body と投入器の契約、登録簿、静的正例が既存テストで固定済み: `orchestrator/tests/test_a5_second_boot_job_contract.py:273-371`。
- T-1998 consumer は balanced の 2 点だけを読むため、A-5 の write-heavy arm や D1100 判定を受理しない。

A-5 shell、投入器、登録簿、既存契約テストには 1 byte も加えない。T-1998 専用 qsub wrapper は既存 sanctioned 経路の重複になるため作らない。

## 第 3 部品 — 事前登録固定 2 点だけを読む consumer

新規 `orchestrator/campaign/t1998_stock_inline_pair.py` を追加する。

### 署名

予定 `:1-55`:

```python
@dataclass(frozen=True, slots=True)
class T1998PreregisteredIdentity:
    repository_commit: str
    ccbench_gitlink_commit: str
    environment_contract_sha256: str

def consume_balanced_stock_inline_pair(
    producer_root: str | Path,
    *,
    preregistered: T1998PreregisteredIdentity,
) -> T1998StockInlineDecision:
    ...
```

比較点は module 内の immutable 定数に固定し、`backoff_sweep._BASE`、`SWEEP_US`、`genomes()`、argmax には依存させない。

- baseline: `NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0, BACK_OFF=0, BACKOFF_FIXED=-1`
- target: 同じ base で `BACK_OFF=1, BACKOFF_FIXED=5`
- workload: `balanced` のみ

### 読む入力

予定 `:56-205`:

1. `producer_root/result.json`
   - schema/status/workload/target_fixed_us
   - pair samples、median、ratio
   - campaign/lock/WAL SHA
   - source、node、toolchain identity
2. `producer_root/reservation.json`
   - `node_boot_evidence`
   - `source_binding`
   - `binding.script_sha256`
3. `producer_root/campaigns/<result.campaign_id>/campaign.lock`
   - CCBench commit
   - environment contract digest
4. public admission から得る `CertifiedCampaignView.records`
   - exact pair の `build_start`、`build_done`、`verify_done`、`bench_done`、`commit`
   - それ以外の点は stage/abort の有無だけを見て、TPS、median、順位を読まない

### 受理条件

予定 `:206-300`:

- result は `a5-second-boot-result/v1`、`status=complete`、`workload=balanced`、`target_fixed_us=5`。
- result の lock/WAL SHA は `CertifiedCampaignView.decision` と一致。
- preregistered source commit、gitlink、environment contract digest が result、reservation、lock、WAL で一致。
- baseline と target がそれぞれちょうど 1 attempt。
- 両 arm は同じ environment contract、env tag、repository/gitlink、source patch identity、toolchain manifest/digest。
- performance configure は trace-disabled、bench executable は `perf_bin_sha256` を持つ build receipt と対応。
- `BACKOFF_NOINLINE=1` を含まない。effective default は 0。
- 各 arm の COMMIT は public certified admission と `admit_replay_evidence()` を通る。
- bench samples、median、COMMIT fitness、result の pair projection が一致。
- どの variant にも abort/anomaly がない。
- 両 arm が `unstable is False` のときだけ `status="accepted"` とし、ratio と improvement を返す。

### 拒否条件と正例

`T1998PairRejected(code: str)` を予定 `:35-55` に置く。

| code | reject | その拒否を通り抜ける正例 |
|---|---|---|
| `producer-artifact-missing` | result、reservation、campaign、lock、WAL の欠損 | 正常終了した A-5 root に 5 成果物がそろう |
| `producer-artifact-binding-mismatch` | result の lock/WAL SHA、campaign ID、reservation node/source が不一致 | result の SHA が admitted view と一致し、reservation の source/node が result と一致 |
| `pair-cardinality` | baseline または fixed-5 が 0 件、2 件以上 | full 8-point WAL 内に exact baseline と fixed-5 が各 1 件 |
| `pair-identity-mismatch` | source commit/gitlink、contract、env tag、toolchain の不一致 | 両 arm が同一 campaign lock、contract、toolchain record を共有 |
| `diagnostic-build` | `BACKOFF_NOINLINE=1`、または診断 override | current `backoff_sweep.genomes()` 由来で diagnostic key がなく、記録 commit の default が 0 |
| `performance-build-not-trace-disabled` | configure が `CCBENCH_TRACE=1`、または bench binary が性能 build receipt と不一致 | `CCBENCH_TRACE=0` の configure と、その build directory 内 executable を使う |
| `producer-rejected-variant` | abort、anomaly、非 serializable、receipt 不正 | `verify_done.verdict=serializable`、`certified=True`、`anomalies=0`、有効 receipt |
| `pair-value-mismatch` | samples、median、commit fitness、result projection の不一致 | 5 samples の median が WAL COMMIT と result の両方に一致 |

不安定は例外にしない。どちらかの `bench_done.unstable` または `commit.unstable` が true なら、`status="inconclusive"`、`reason="unstable-arm"`、`ratio=None`、`improvement_percent=None` を返す。

### 返す構造

予定 `:301-345`:

- `status`: `"accepted"` または `"inconclusive"`
- `reason`
- `baseline` / `target`
  - exact flags、variant ID、samples、median、CV、unstable
  - performance binary SHA
  - COMMIT receipt ID
- `identity`
  - repository commit、CCBench gitlink、environment contract digest
  - toolchain manifest と record digest
  - campaign ID、lock SHA、WAL SHA
- `ratio`、`improvement_percent`
  - accepted の場合だけ有限値
  - inconclusive の場合は `None`

D1137 の IPC 帯・散布・0.044 bar は入力にも判定にも使わない。あれは機序 profile の別命題であり、headline を説明しない: `d1137.md:3-24`。診断 throughput の拒否は D20/D1244 に直接対応する: `d20.md:3-7`、`d1244.md:7-9`。

## 変更 file 一覧と所有分割

| 所有 | file | 変更 |
|---|---|---|
| A: consumer | `orchestrator/campaign/t1998_stock_inline_pair.py` | 新規。fixed pair consumer、型、拒否署名 |
| A: consumer tests | `orchestrator/tests/test_t1998_stock_inline_pair.py` | 新規。実 admission/receipt 経路による正負テスト |
| B: evidence audit | `output/insights/2026-09-08_t1998-stock-inline-evidence/README.md` | 新規。read-only 到達性表と限界 |
| B: launcher | なし | 純増ゼロ |

次は変更しない。

- `orchestrator/campaign/backoff_sweep.py`
- A-5 job body / submitter
- `admission_registry.json`
- `test_hooks.py`
- 既存テストの期待値
- 既存 frozen artifact

## テスト計画

新規 `orchestrator/tests/test_t1998_stock_inline_pair.py` に以下を置く。

- `test_real_certified_admission_accepts_the_preregistered_balanced_pair`
  - production の v2 campaign lock、WAL sink、verifier capability、COMMIT receipt、`require_admitted_campaign`、`admit_replay_evidence` を実際に使う。
  - baseline/fixed-5 が accepted になり ratio が 2 点からだけ計算されることを固定。

- `test_larger_off_grid_tps_cannot_replace_fixed_five`
  - fixed-2 に fixed-5 より大きい TPS を入れても結果が fixed-5 のままであることを固定。
  - post-result argmax 不在の正例。

- `test_missing_preregistered_arm_is_pair_cardinality_reject`
  - baseline 欠損、target 欠損を parameterize。
  - 片側欠損が `T1998PairRejected(code="pair-cardinality")` になることを固定。

- `test_pair_identity_drift_is_rejected`
  - source/gitlink、contract、toolchain をそれぞれ片 arm だけ変える。
  - `pair-identity-mismatch` を固定。

- `test_backoff_noinline_one_is_diagnostic_build_reject`
  - target genome に `BACKOFF_NOINLINE=1` を置く。
  - `diagnostic-build` を固定。

- `test_trace_enabled_command_is_not_performance_evidence`
  - target の configure receipt を `CCBENCH_TRACE=1` にする。
  - `performance-build-not-trace-disabled` を固定。

- `test_real_commit_receipt_rejection_dominates_pair_values`
  - receipt 欠損または terminal payload mismatch を作る。
  - public certified admission が pair TPS を読む前に拒否することを固定。

- `test_unstable_either_arm_is_inconclusive`
  - baseline/target の各ケースを parameterize。
  - 例外ではなく inconclusive、ratio が `None` になることを固定。

- `test_result_reservation_and_admitted_hashes_must_match`
  - result の WAL SHA、lock SHA、reservation source を個別に変える。
  - `producer-artifact-binding-mismatch` を固定。

fixture は `orchestrator/tests/commit_receipt_support.py:106-150,193-208` の実 verifier/receipt 発行経路を使う。`require_admitted_campaign`、WAL parser、receipt admission を monkeypatch や stub に置き換えない。build、benchmark、性能測定は行わない。

親が実装後に行う検査は、対象 test を `tools/run_tests.py` 経由で実行し、その後に通常の docs/Codex-agent/provenance 検査を行う。本段では一切実走しておらず、緑とは報告しない。

## 凍結・登録簿への波及

`git grep` で次の語を棚卸しした。

- `backoff_sweep._BASE`
- `backoff_sweep.SWEEP_US`
- `_BASE and SWEEP_US`
- `backoff_sweep.genomes(`
- `a5_second_boot_backoff_sweep`
- `submit_a5_second_boot_backoff_sweep`
- `run_campaign`

brief 記載分に加え、次の pin が見つかった。

- `orchestrator/tests/test_s1_known_axes_freeze.py:546-549` が `SWEEP_US` を `EXPECTED_SWEEP_US` に直接 pin。
- `orchestrator/tests/test_official_perf_closure.py:44-92` が A-5 job body を official perf surface として列挙。
- `orchestrator/tests/test_official_perf_closure.py:516-551,888-891` が production の perf predicate file 集合を完全一致検査。
- `orchestrator/tests/test_official_perf_closure.py:585-607` が `test_campaign.py` の evaluate inventory を参照。
- `orchestrator/tests/test_a5_second_boot_job_contract.py:321-371` が A-5 job/submitter/registry の合同正例。
- `orchestrator/tests/test_hooks.py:3032-3103,3926-3960` が Pegasus file 集合と 4-field registry を完全一致検査。

今回の計画では以下の理由で pin 更新は不要。

- `_BASE`、`SWEEP_US`、`genomes()` を変更しないため s1 freeze/golden は不変。
- consumer は `run_campaign`、`evaluate`、測定 API を呼ばないため `test_campaign.py:5346-5426` の caller inventory は不変。
- `tools/pegasus/` に file を追加しないため registry と `test_hooks.py` は不変。
- consumer は producer-recorded commandを読むだけで perf を起動しない。official perf authority の既存 predicate/caller 集合は増えない。
- `output/campaigns/**` や既存 insight の bytes は変更しない。

## 残る不確実性

- 2026-09-07 balanced run には `result.json` がないため、新 consumer の現物正例にはできない。既存の 3,803,883 / 4,294,095 TPS は reject のまま残る。
- full toolchain `--version` 本文は公式 output から再構成できない。現在の pair identity は短い manifest と full record digest の一致まで。
- `BACKOFF_NOINLINE=0` は明示 field ではなく、exact genome、configure override 不在、preregistered repository commit 内の default 0 の組合せで証明する。
- A-5 balanced の checkout cleanup rc=1 が再発する可能性はこの 3 部品では直さない。正式測定の可否と再投入は land 後の人間手番。
- preregistered commit/gitlink/environment digest の実値は本 wave では確定しない。consumer の入力 seam だけを land し、値の固定と正式測定認可は D1244 どおり人間へ返す。

## 総括

実装差分は新規 3 file に限定する。

1. producer evidence の到達性監査を insight に保存する。
2. launcher は既存 A-5 経路で充足済みのため純増 0 byte。
3. balanced の no-backoff と fixed-5 だけを読む専用 consumer と、実 admission/receipt 経路を使うテストを追加する。

producer schema、A-5 受理集合、既存テスト期待値、凍結成果物は変更しない。現行の result 欠損 run は受理せず、測定・build・benchmark も本 wave では行わない。