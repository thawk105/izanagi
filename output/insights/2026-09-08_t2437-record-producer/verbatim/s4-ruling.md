# 段 4 裁定 — dev-wave-t2385-t2437-record-producer (2026-09-08 07:43 JST)

裁定 inbox 再走査: wave 開始後に main へ入った D1792〜D1794 は本件と無関係。[T-2385]/[T-2437] の持ち越し本文に変更なし。
main は 6172ea26b まで進んだが、本 wave の編集面に触れるのは受入所要台帳だけ (land の merge で吸収)。

## 1. 依頼の前提の再裁定 (brief §0 N1〜N3)

- **N1 採用:** [T-2385] (WAL 側の 3 field) は D1768 で解消済み。本 wave は WAL 側を再度開かない。段 2 §1 が FC04/FC07/FC09 と ledger の必須条件 (`reflux_origin_ledger.py:703`) から「record 層で consumer を合わせる余地は無い」を裏取りした。
- **N2 採用:** 本 wave の本題は [T-2437] = record 層 producer。**producer を書く。**
- **N3 採用:** 「boolean が恒真にならない」は `physical_result` の 3 方向分岐 (accepted / rejected+class / 発行拒否) が VerifyResult の値で決まることの実証として読み替える。

## 2. 所見の裁定

| 所見 | 判定 | 採否 | scope | 裁定 |
|---|---|---|---|---|
| A-1 typed 単独導出は terminal WAL と結合されない | real (親が `pipeline.py:1594-1605`、`reflux_formal_consumer.py:1274-1281` で確認) | 採用 must-fix | 内 | S1 の入力を **ordered WAL projection の records + VerifyResult (rejected 時) + ordered_verifiers** にする。accepted = terminal stage commit かつ `verify_configs` が ordered_verifiers と exact 一致 (VerifyResult 不要)。rejected = terminal stage abort かつ `reason == vr.verdict == "non-serializable"` かつ terminal `verify` が `result_to_dict(vr)` から `trace_dir` を除いた wire snapshot と **canonical bytes で同値**、かつ `build_attempt_id` 一致。成果物影響: これが無いと producer 由来 record が FC07 で落ち origin 全体が不受理 |
| A-2 total_cycles は SCC 数で class 数でない | real (親が `dsg.py:481-502,569-596` で確認) | 不採用 (実装せず) | **外 → 裁定パッケージ** | class の定義は D1768 が「verifier が報告した単一 anomaly の canonical JSON の sha256」と定めており、producer は同じ定義に従う。1 SCC 内の複数 simple cycle を verifier は代表 1 件へ縮約するため、class = **SCC ごとの代表 witness** である。uniqueness の証明は producer 単独では不可能。D1768 限界 (occurrence identity / 構造同値類) と同族の限界として insight・decision に明記し、class 定義の再裁定をユーザーへ返す |
| A-3 恒真条件の混在 | real | 採用 | 内 | producer の wire 検査のうち `anomaly_count == len(anomalies)`、key 集合、`certified` と `serializable` の派生は **drift assertion と明記** (防護に数えない)。実防護として exact 型の直接負例 3 件 (`n_txns=True`、cycle 節点 `True`、version `1.0` を持つ typed VerifyResult) を足す |
| A-4 shared digest は snapshot 同一性を保証しない | real | 採用 | 内 | (P1) を広げる: 共有単位は **構造検査 + digest** (`validate_witness_anomaly()` + `witness_class_sha256()`) とし `reflux_result_evidence.py` に置く。新 module は作らない (`WAVE_PRODUCTION_FILES` 15 件 pin、B-6/B-7)。consumer の `_valid_witness_anomaly` / `_witness_class_sha256` は shared を呼ぶ wrapper に差し替え、`ArtifactError → FC07` 変換は wrapper に残す。snapshot の同一性は A-1 の terminal `verify` 同値検査が担う |
| A-5 / B-4 S3 は WAL の追記寿命を閉じない | 要実測 | 採用 (S3 を落とす) | **S3 は外 → carry** | (P3) 反証。S3 (ordered WAL projection producer) は issuer 配線 (B-3) と同じ carry へ送る。端から端 test は fixture builder の canonical-list 経路で projection を作る (B-1 も同時に解消) |
| A-6 P4 は局所 API | real | 採用 | 内 | (P4) を局所 API として採用。「§3.4 の tombstone / origin aborted 写像を実装した」とは書かない。caller 配線は carry |
| A-7 fixture 一般化 | real | 採用 (文書化のみ) | 内 | insight に「fixture 到達性は synthetic Silo source 束縛下の値」と「SCC 内複数 cycle は代表 1 件」を書く。合成 graph test は足さない (A-2 の裁定待ち) |
| B-1 fixture の既存 WAL が正例を止める | real | 採用 must-fix | 内 | 端から端 test は fixture の physical root へ追記しない。real r9 走の `verify` を terminal abort payload に載せた records を fixture builder の override 経路で組み、projection / source bytes / provenance / record を **新しい tmp evidence tree** に materialize する。既存 fixture file の除去や上書きをしない |
| B-2 salts は未行使 | real | 採用 | 内 | test 名と docstring を「formal-consumer contract integration」に限定し、salts 不変・未行使と明記。ledger replay は要求しない |
| B-3 typed 入力は production issuer へ届かない | real | 採用 | 内 (格付け) / 配線は外 | 成果物を **producer core API** と明記する。`EvalResult` への VerifyResult 保持・`run_campaign()` 最終化点への配線・`run_origin_trial` の production 呼び手は 1 つの carry ([T-2437] の残余) にする。裁定パッケージ候補あり (§4) |
| B-5 synthetic 値は production へ一般化できない | real | 採用 | 内 | test 名・docstring・insight を synthetic source 束縛へ限定。production 到達性は主張しない (限界として記す) |
| B-6 golden / P1 は静的に閉じる | real | 採用 | 内 | 実装後に `git diff --exit-code` で fixture builder・baseline・golden 不変を検査 |
| B-7 pin 閉包に 2 件不足 | real | 採用 | 内 | checklist に `test_plain_runner_coverage` と `test_consumer_source_has_no_nonaborted_construction_or_success_variant` を追加。新 test file・xdist group・role・gate・台帳は足さない |

## 3. (P1)〜(P4) の確定

- **(P1) 採用 (拡張形):** 共有単位 = 構造検査 + digest、置き場 = `reflux_result_evidence.py`。consumer は wrapper 経由。受理集合不変は既存 FC07 正負例全件 + 変異 M-C1 で示す。
- **(P2) 採用 (修正形):** rejected の第一入力は exact `VerifyResult`。ただし S1 は単独では導出せず、A-1 の terminal WAL 結合を必須にする。abort payload dict からの public 経路は置かない。
- **(P3) 反証:** S3 は本 wave から外す (carry)。
- **(P4) 採用 (局所 API):** `ResultEvidenceIssuanceRefused(ResultEvidenceError)` 1 型 + 理由文字列。reason code 体系は新設しない。理由文字列は機械分岐に使わず、test は例外型と発行物不在を pin する。

## 4. プラン v2 (編集面)

| file | 変更 |
|---|---|
| `orchestrator/campaign/reflux_result_evidence.py` | 追加: `ResultEvidenceIssuanceRefused`; `validate_witness_anomaly(anomaly) -> bool` と `witness_class_sha256(anomaly) -> str` (consumer `_valid_witness_anomaly` 1155-1235 と `_witness_class_sha256` 1237-1241 の逐語移動。定数 `_ANOMALY_KEYS` 等も移す); `DerivedPhysicalResult` dataclass; `derive_physical_result(*, ordered_wal_records, build_attempt_id, ordered_verifiers, verify_result=None) -> DerivedPhysicalResult` (A-1 の結合込み、3 方向); `assemble_result_evidence_record(...)` (9 key exact、`validate_result_evidence` 必須) と `issue_result_evidence_record(...)` (参照先 resolve → 既存 create-only writer)。**S3 は書かない** |
| `orchestrator/campaign/reflux_formal_consumer.py` | 変更: `_valid_witness_anomaly` / `_witness_class_sha256` を shared 呼び出しの wrapper へ。`ArtifactError → _ContractFailure(FC07)` 変換は wrapper に残す。定数は shared から import。**判定式・reason code・受理集合は不変** |
| `orchestrator/tests/test_reflux_result_evidence.py` | 追加: synthetic Silo source helper (test_verifier.py:41-63 と同型、import せず複製); 正例 accepted (terminal commit + exact verify_configs、VerifyResult 無し) と rejected (`r9_dense_cycle4`・`r3_cycle3`・`r1_write_skew` の実走 + 同じ wire snapshot を載せた terminal abort); 発行拒否負例 (`integrity_orphan`・`m2_version_dup` の indeterminate、`r4_mixed_cycle` の dirty non-serializable、r9 `max_report=0` の切詰め、`r8_silo_broken_norw` の複数 class と `max_report=1` の capped、terminal 不一致 3 種 [stage abort だが verify が別 run の snapshot / reason ≠ verdict / accepted で verify_configs 不一致]、exact 型負例 3 件 [A-3]、非 production 構造 3 種 [unknown phenomenon / ring 不一致 / unknown reason type]); shared digest の独立再計算一致; assembler の validate 迂回負例; issue の参照先不在で record 不在 |
| `orchestrator/tests/test_reflux_formal_consumer.py` | 追加: 端から端 (r9 実走 → producer record → 新 tmp evidence tree → `evaluate_formal_origin` が FC07 でなく `P6Unavailable`)。B-1/B-2 の条件付き。既存 `test_fc07_converts_witness_canonicalization_artifact_error` の monkeypatch owner を shared module へ |
| `orchestrator/tests/acceptance_duration_ledger.json` | 親が実測 JUnit から `--add-only` で新 nodeid を追加 (実装子は触らない) |

不変: fixture builder・`reflux_origin_fixture_baseline.json`・golden 4 個・`wal.py`・`dsg.py`・verifier・pipeline は 1 byte も変えない。

## 5. 変異事前登録 (DW-M01、実装前)

| ID | 変異 (実装後の位置) | 殺す nodeid (見込み) |
|---|---|---|
| M1 | accepted 条件から `verify_configs == ordered_verifiers` を落とす | accepted の verify_configs 不一致負例 |
| M2 | rejected から `integrity.clean() is True` を落とす | `r4_mixed_cycle` dirty 負例 |
| M3 | `len(anomalies) == 1` を `>= 1` にし先頭を選ぶ | `r8_silo_broken_norw` 複数 class 負例 |
| M4 | `total_cycles == anomaly_count` を落とす | r8 `max_report=1` capped 負例 |
| M5 | 空 anomaly の拒否を落とす | r9 `max_report=0` 負例 |
| M6 | producer 側の witness 構造検査を落とす | ring 不一致負例 |
| M7 | class digest を canonical anomaly bytes 以外から計算 | 独立再計算一致 test |
| M8 | terminal `verify` == wire snapshot の検査を落とす | 別 run snapshot 負例 |
| M9 | `reason == verdict` の検査を落とす | reason ≠ verdict 負例 |
| M10 | rejected 枝の outcome を accepted に | r9 rejected 正例 |
| M11 | accepted 枝に非 null constraint | accepted 正例 |
| M12 | assembler の `validate_result_evidence()` 呼び出しを落とす | validate 迂回負例 |
| M13 | 参照先 resolve より前に record writer を呼ぶ | 参照先不在負例 |
| M14 | exact int 検査を `isinstance` に緩める | A-3 の bool 負例 (T-2438 の穴を producer 側で pin) |
| M-C1 | consumer wrapper の `ArtifactError → FC07` 変換を落とす | 既存 `test_fc07_converts_witness_canonicalization_artifact_error` |
| 過剰拒否の正例 | 端から端 test (r9 producer record が consumer で `P6Unavailable` に到達) と FC07 既存正例全件 | — |

登録しない等価変異: `anomaly_count == len(anomalies)` 単独削除 (result_to_dict が生成、恒真)。

## 6. 裁定パッケージ候補 (ユーザーへ返す)

1. **witness class の定義 (A-2):** 現行 (D1768) は「verifier が SCC ごとに報告する代表 witness 1 件の canonical JSON digest」。1 SCC 内の複数 simple cycle は代表 1 件へ縮約されるため、§3.4 の「複数 class から 1 件を選ばない」は SCC 単位でしか成立しない。選択肢: (a) 現行維持し設計 §3.4 に「class = SCC 代表 witness」を追記 (推奨、機構追加なし) / (b) verifier 出力へ SCC 内 cycle 数または uniqueness proof を追加 (verifier bytes が変わる) / (c) 構造同値類を定義。
2. **issuer 配線 (B-3/A-6/A-5):** `EvalResult` への VerifyResult 保持、`run_campaign()` 最終化点での issue 呼び出し、S3 (ordered WAL projection producer、per-query WAL の不変性を前提)、`run_origin_trial` の production 呼び手。設計 §9 V-8/V-9 と同じ束で、本 wave は core API まで。

## 7. 分割・投入

実装子 1 本 (Codex author、workspace-write、xhigh)。所有 = §4 の 4 file (台帳を除く)。段 6 は敵対レビュー 2 本 + fix + 変異 + 受入。
