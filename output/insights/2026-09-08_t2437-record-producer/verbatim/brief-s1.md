# 段 1 brief — dev-wave-t2385-t2437-record-producer

wave: `dev-wave-t2385-t2437-record-producer` / branch `worktree-dev-wave-t2385-t2437-record-producer`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer` (base = local main `34af5a571`)
依頼: [T-2385] と [T-2437] を 1 wave で扱う。producer を書くか consumer を合わせるかを段 2 で決め、段 4 で裁定してから実装する。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。Codex author = D95。

## 0. 依頼の前提を覆す新事実 (brief 前の実測、段 4 で再裁定)

- **N1: [T-2385] の前提は既に main 上で解消済み。** 依頼文の「consumer が rejected 側で `candidate_attributable` / `truncated` / `witness_class_sha256s` を要求する」は D1768 (2026-09-08、wave `dev-wave-rejected-witness-closure`、着地済み) が廃止した。現行 `orchestrator/campaign/reflux_formal_consumer.py:1264-1396` `_validate_wal_outcomes()` の rejected 枝は WAL terminal の `reason` と `verify.*` だけを読む。`orchestrator/campaign/` で 3 field の出現は `reflux_source_closure.py:370,381` の `candidate_attributable_rejected` (verifier-policy の別 field) だけ。**WAL 側の「producer を書くか consumer を合わせるか」は裁定済み (consumer 側) であり、本 wave で再度開かない。**
- **N2: 残る鎖は [T-2437] だけ。** result-evidence record (`result-evidence/v1`) の production producer は 0 件。`OriginProducerInputs` の構築は `orchestrator/tests/test_p3_autonomous_workload_trial.py:10899` の 1 箇所。record の evidence 参照先 (`ordered-wal-projection/v1`、`execution-provenance/v2`) の production 生成器も 0 件 (`orchestrator/campaign`・`tools` 全走査)。`run_origin_trial` (`p3_autonomous_workload_trial.py:5282`) の production 呼び手も 0 件。
- **N3: 「producer が書く boolean」は現行契約に存在しない。** record の `physical_result` は `{build_attempt_id, outcome ∈ {accepted, rejected}, constraint_sha256}` (`reflux_result_evidence.py:111-113,300-310`)。依頼の「boolean が恒真にならないことを正例・負例で示す」は、`outcome` と `constraint_sha256` の導出が VerifyResult の値で 3 方向 (accepted / rejected+class / 発行拒否) に分岐することの実証として読み替える。
- **N4: 設計正本は `docs/phase3-8c-wiring-design.md` §3.3 (issuer の位置・create-only 順序) と §3.4 (outcome 対応表)。** §3.4 は「witness class が 0 件または複数、切詰め、attempt 帰属曖昧 → record を発行しない (tombstone)」を既に定める。producer の導出規則はここに従い、新しい規則を発明しない。
- **N5: 同名 wave の重複起動 (session dd877a、job b9b34a70) があったが後発が降りた。** 共有 path は未作成との返信あり。

## 1. scope (確定主目的)

record 層 producer を production module `orchestrator/campaign/reflux_result_evidence.py` (record 契約の所有 module) へ新設する。

- **S1 physical_result の導出 (本題の核):** 入力は verifier の terminal 事実 (`VerifyResult` または production の abort payload `verify` = `result_to_dict()` から `trace_dir` を除いた dict) と `build_attempt_id`。出力は §3.4 のとおり 3 方向: (a) `certified is True` かつ verdict `serializable` → `outcome=accepted, constraint_sha256=None`; (b) verdict `non-serializable`、`integrity.clean is True`、`anomaly_count == len(anomalies) == total_cycles == 1` → `outcome=rejected, constraint_sha256 = sha256(canonical_json_bytes(anomalies[0]))` (consumer `_witness_class_sha256` `reflux_formal_consumer.py:1237` と同じ式); (c) それ以外 (indeterminate、dirty integrity、切詰め、class 0 件または複数) → **発行拒否** (typed error、record を作らない)。
- **S2 record 組立 + create-only 書込み:** 既存 `write_result_evidence_record()` (`reflux_result_evidence.py:444`) を使い、9 key exact schema を `validate_result_evidence()` で通す typed な組立関数。fixture builder (`orchestrator/tests/reflux_origin_fixture_builder.py`) の bytes と test golden (`test_reflux_result_evidence.py:24-27`) は 1 byte も変えない。
- **S3 ordered WAL projection の producer:** production `wal.jsonl` (`layout.wal_file`) の 1 build_attempt 区間から `ordered-wal-projection/v1` を作る。受理規則は consumer 側 `_canonical_wal_interval` / `_resolve_ordered_wal` (`reflux_result_evidence.py:618-690`) が exact に定めており、その逆関数を書く。
- **正例・負例 (実体を名指し、synthetic Silo source 束縛は `orchestrator/tests/test_verifier.py:41-63` の作法):** accepted 正例 = `fixtures/g4_rw_no_cycle`・`g1_serial`・`p1_phantom_skew` (実測: serializable, certified=True, clean=True)。rejected 正例 = `fixtures/r9_dense_cycle4`・`r3_cycle3`・`r1_write_skew` (実測: non-serializable, clean=True, total_cycles=1, anomalies=1)。発行拒否の負例 = `fixtures/integrity_orphan`・`m2_version_dup` (実測: indeterminate, clean=False)、`verify_trace_dir(..., max_report=0)` の r9 (切詰め: total_cycles=1, anomalies=0)。**複数 class の負例は実 fixture に見つかっていない** (走査した 8 件はすべて total_cycles ≤ 1) — 段 2 で実 fixture を探し、無ければ typed `VerifyResult` の合成 1 件を明記付きで許す。
  **追補 (06:58、全 22 fixture 走査で上の一般化を訂正):** `fixtures/r8_silo_broken_norw` = non-serializable, clean=True, **total_cycles=4, anomalies=4** → 複数 class の**実 fixture が存在する**。合成は不要。`fixtures/r4_mixed_cycle`・`r5_nonlatest_transitive` = non-serializable, **clean=False**, total_cycles=1 → 「cycle はあるが dirty integrity」の実負例。`m1_commit_at_genesis`・`m3_mocc_lock_coverage`・`m4_mocc_permutation` = indeterminate, clean=False (追加の発行拒否負例)。`g5_silo_real_prefix`・`g6_silo_serial_1thread`・`g7_mocc_minimal_2thread`・`g2_rmw_chain`・`g3_readonly` = serializable certified (追加の accepted 正例)。
- **端から端の正例:** producer が実 verifier 走から作った rejected record を consumer の `_validate_wal_outcomes` 経路 (fixture の origin 一式へ差し替え) が FC07 で通すこと。fixture の手書き dict では代用しない。

## 2. scope 外 (裁定パッケージ候補として返すだけ)

- `execution-provenance/v2` の issuer、`run_campaign()` 最終化点への配線、`run_origin_trial` の production 呼び手、`_initialize_locked()` の production 拒否解除、33 attempt topology の再批准 (設計 §9 V-8/V-9)。**発火条件を満たす既存 artifact path が無い** (DW-G04) ため本 wave では実装しない。
- witness の構造同値類・`dsg.py` の理由順決定性 ([T-2436])・bool 型厳密性 ([T-2438])・terminal 外枠 ([T-2384]、D1730 裁定済み別項)。
- consumer の判定式・reason code・受理集合の変更。**consumer は触らない** (P1 を除く)。

## 3. 不変条件

- 規律 2: producer は consumer より緩い形を発行しない。発行拒否は消さない。`outcome=rejected` を class 無しで、または複数 class から 1 件を選んで発行しない (§3.4)。
- 既存 record / fixture / golden bytes 不変。凍結成果物・proof chain の bytes に触れない (DW-O09: path pin は `test_reflux_result_evidence.py` の golden 4 個と受入所要台帳の nodeid だけ。producer が書く file 種 = caller 指定 evidence_root 配下の record JSON と projection JSON、DW-O10)。
- 新規 test node は受入所要台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) の被覆率 gate に掛かる。実測値を `--add-only` で足す (前 wave と同じ)。

## 4. 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) class の式を 1 箇所へ寄せるか。** provisional: `_witness_class_sha256` を `reflux_result_evidence.py` へ移し consumer が import する (consumer の bytes は変わるが受理集合は不変)。反対案: producer 側に同じ式を複製し、テストで一致を pin する。
- **(P2) S1 の入力型。** provisional: `VerifyResult` (typed) を第一入力とし、abort payload dict からの経路は置かない。反対案: WAL terminal の `verify` dict を入力にして consumer と同じ bytes を読む。
- **(P3) S3 を本 wave に含めるか。** provisional: 含める (record の evidence 参照が production から作れないと S2 の正例が fixture 依存になる)。反対案: S1+S2 だけに絞り S3 は carry。
- **(P4) 発行拒否の表現。** provisional: `ResultEvidenceError` の派生 1 型 + 理由文字列 (規則 §3.4 の行に対応)。新しい reason code 体系は作らない。

## 5. 成果物・分割・環境

- 成果物: `reflux_result_evidence.py` の追加関数群、`orchestrator/tests/test_reflux_result_evidence.py` (または新 file) の正例・負例、端から端 test、変異 matrix、insight、worklog/decisions fragment。
- 分割: 実装子 1 本 (所有 = 上記 2 file + 必要なら consumer の import 差し替え)。段 6 レビュー 2 レンズ (A: 規律 2 / 受理集合、B: 導出の同一性と bytes 不変)。
- 受入・実測環境: login node での焦点走 + 計算ノード dispatch の受入全走 (所在は worklog 末尾の作法)。CCBench build は不要 (synthetic proof source)。
