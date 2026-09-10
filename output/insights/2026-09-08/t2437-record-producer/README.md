# result-evidence record の producer core API を新設し、rejected の witness class を consumer と同じ規則で導いた — production issuer への配線は含めない

**種別:** 書き手 (producer) の新設。dev-wave `dev-wave-t2385-t2437-record-producer` (2026-09-08)。
設計判断は {{D:result-evidence-producer-core-api}} (fold 後は実番号)。起点は D1768 の限界節と
[T-2437] (「result-evidence record 全体に production producer が無い」)。

**閉じたのは record 層の producer core API までである。** production issuer
(`run_campaign()` の最終化点) への配線、ordered WAL projection を `wal.jsonl` から作る producer、
`run_origin_trial` の production 呼び手は依然として存在しない。rejected の本番 projection が
端から端まで通るようになったとは書かない。

## 1. 依頼の前提のうち、着手前に覆っていたもの

| 依頼文の前提 | 実測 | 扱い |
| --- | --- | --- |
| consumer が rejected 側で `candidate_attributable` / `truncated` / `witness_class_sha256s` を要求する ([T-2385]) | D1768 (2026-09-08 着地) が 3 field を廃止し、consumer は WAL の `reason` と `verify.*` を読む。`orchestrator/campaign/` に producer 側の 3 field 出現は無い | [T-2385] は解消済み。WAL 側の「producer か consumer か」は再度開かない |
| producer が書く boolean が恒真にならないことを示す | 現行契約に boolean は無い。`physical_result` は `outcome ∈ {accepted, rejected}` と `constraint_sha256` | 3 方向分岐 (accepted / rejected+class / 発行拒否) が VerifyResult の値で決まることの実証として読み替えた |
| 2 件は同じ鎖 | record 層 producer の不在 ([T-2437]) だけが残る鎖 | 本題を [T-2437] にした |

## 2. 方向 — record 層で consumer を合わせる余地は無い

record の `constraint_sha256` は FC04 (record と ledger member の一致)、FC07 (record と WAL の
witness class の一致)、FC09 (rejected class 集合の一致) の 3 等式で束縛され、ledger 自体が rejected に
digest を必須とする (`reflux_origin_ledger.py` の member 検証)。これらを緩めずに consumer 側で
不整合を閉じる方法は無く、producer を書く以外に無い (段 2 が file:line で裏取り)。

## 3. 実装した producer (`orchestrator/campaign/reflux_result_evidence.py`)

- `derive_physical_result(*, ordered_wal_projection_bytes, build_attempt_id, ordered_verifiers, verify_result=None)`
  - 入力は **ordered WAL projection の canonical bytes** (record が参照するのと同じ bytes)。
    parse → exact key → schema → attempt 一致 → records 非空 → terminal の外枠が production の
    5 key `{variant, stage, env_tag, ts, payload}` と exact 一致、を経て terminal を読む。
  - **accepted:** terminal が `commit`、`verify_configs` が verifier policy の順序付き集合と exact 一致
    (空・prefix・逆順・重複は拒否)。`verify_result` は不要 (渡されたら certified かつ serializable を要求)。
  - **rejected:** `verify_result` は exact `VerifyResult`、`verdict == "non-serializable"`、
    `serializable is False`、`certified is False`、`integrity.clean() is True` (typed 層は proof surface と
    commit witness まで見る)、`total_cycles == len(anomalies) == 1`。wire snapshot
    (`result_to_dict()` から `trace_dir` を除いたもの) に consumer と同じ exact 検査を掛け、terminal の
    `reason == verdict`、terminal の `verify` が snapshot と **canonical bytes で同値**。
    `constraint_sha256 = witness_class_sha256(snapshot["anomalies"][0])`。
  - **発行拒否 (`ResultEvidenceIssuanceRefused`):** それ以外すべて。indeterminate、dirty integrity、
    切詰め、複数 class、空 anomaly、非 production 構造、root shadow、別 attempt、非 canonical projection。
    **複数 class から 1 件を選ばない** (cardinality を digest 計算より先に検査する)。
- `DerivedPhysicalResult.ordered_wal_sha256` (projection bytes の content-addressed digest) を持ち、
  `assemble_result_evidence_record()` は record の `ordered_wal_ref.sha256` との一致を要求する。
  導出に使った projection と record が参照する projection は同じ bytes である。
- `issue_result_evidence_record()` は両参照先を解決してから既存の create-only writer を呼ぶ。
- witness の構造検査と class digest は `validate_witness_anomaly()` / `witness_class_sha256()` として
  同 module に置き (consumer からの逐語移動)、consumer は wrapper で呼ぶ。`ArtifactError -> FC07` の
  変換は wrapper に残る。**consumer の判定式・reason code・受理集合は変えていない。**

typed 層と wire 層の重複検査は意図的な二重化である。typed 層は `Integrity.clean()` の proof surface まで
見る強い条件、wire 層は consumer parity。`anomaly_count == len(anomalies)`・key 集合・
`certified`/`serializable` の派生は `result_to_dict()` が生成するため恒真 (drift assertion) であり、
防護に数えない。`total_cycles == anomaly_count` は切詰めを拒否する実防護である (code comment に分けて書いた)。

## 4. 親の provisional 裁定のうち、子の実測で覆ったもの

| 親が書いた前提 | 実測した現実 | 誰が |
| --- | --- | --- |
| typed `VerifyResult` から単独で導出できる | terminal WAL と結合しないと consumer が FC07 で落とす record を発行できる。accepted は単一 pass でなく全 pass 通過後の commit で成立する | 段 3 レンズ A |
| `total_cycles == anomaly_count == 1` は class が 1 件であることを示す | `total_cycles` は SCC 数。1 SCC 内の複数 simple cycle は verifier が代表 1 件へ縮約する (`dsg.py` の `_shortest_cycle` / `anomalies`) | 段 3 レンズ A (親が現物で確認) |
| 走査した 8 fixture に複数 class は無い → 実 fixture は無い | 全 22 fixture 走査で `r8_silo_broken_norw` (clean、total_cycles=4、anomalies=4) が存在 | 親の再走査 |
| S3 (ordered WAL projection producer) を含める | source WAL の追記寿命を本 wave 単独で閉じられない。issuer 配線と同じ束 | 段 3 レンズ A / B |
| 導出結果は typed 入力で consumer と結合している | 導出結果と record が参照する projection は独立で、同 attempt の別 projection を参照する record を正常発行できた | 段 6 レンズ A / B (独立に同じ穴) |
| producer は payload を読めばよい | consumer の `_wal_field()` は同名 top-level を優先する (D1715/D1768 で維持)。root shadow で乖離 | 段 6 レンズ A |
| 変異 M2〜M5 は単独で殺せる | typed 層と wire 層の重複検査に mask される | 段 6 レンズ A |

いずれも fix 1 巡で閉じ、焦点再レビューは closed 10 / partial 0 / regressed 0 / pending-parent 1 (台帳、親)。

## 5. 正例・負例は実体を名指しする (synthetic Silo source 束縛下)

`orchestrator/tests/test_verifier.py` と同型の synthetic Silo source を tmp に作り、
`verify_trace_dir(fixture, protocol="silo", ccbench_root=...)` で実走した。**この束縛無しでは全 fixture が
indeterminate になる** (親が実測)。

| 分岐 | fixture | 実測 |
| --- | --- | --- |
| accepted | `g4_rw_no_cycle`, `g1_serial`, `p1_phantom_skew` (+ g2/g3/g5/g6/g7) | serializable, certified, clean |
| rejected + class | `r9_dense_cycle4`, `r3_cycle3`, `r1_write_skew` | non-serializable, clean, total_cycles=1, anomalies=1 |
| 発行拒否 (indeterminate) | `integrity_orphan`, `m2_version_dup` (+ m1/m3/m4) | indeterminate, clean=False |
| 発行拒否 (dirty で cycle あり) | `r4_mixed_cycle` (+ r5) | non-serializable, clean=False |
| 発行拒否 (複数 class) | `r8_silo_broken_norw` | clean, total_cycles=4, anomalies=4 |
| 発行拒否 (切詰め) | r8 `max_report=1`、r9 `max_report=0` | total_cycles > len(anomalies) |
| 発行拒否 (terminal 不一致) | r9 typed + r3 snapshot / reason=indeterminate / verify_configs 空・prefix・逆順・重複 | — |
| 発行拒否 (root shadow) | top-level に reason / verify_configs / verify / build_attempt_id | — |
| 発行拒否 (exact 型) | `n_txns=True`、cycle 節点 `True`、version `1.0` | — |
| 発行拒否 (非 production 構造) | unknown phenomenon / ring 不一致 / unknown reason type | — |

端から端: r9 を 1 度実走し、その snapshot を terminal abort に載せた 33 record を producer
(`derive` → `assemble` → **実 issuer**) で新しい tmp evidence tree へ発行し、`evaluate_formal_origin()`
が FC07 でなく `P6Unavailable` に到達する (`test_synthetic_silo_source_producer_passes_formal_consumer_contract`)。
salts は不変・未行使、ledger replay は要求しない。**production 到達性は示さない** — production の verifier
呼び出しは build に封印された source snapshot と commit witness を検証するため、同じ trace でも
`integrity.clean()` が変わりうる。

## 6. 変異 matrix

probe 走 (全件 SURVIVED 登録で観測 node を集める) → 本走の 2 段。runner は
`tools/run_tests.py --force-dispatch test_reflux_result_evidence.py test_reflux_formal_consumer.py -q -rf`
(計算ノード dispatch)。spec と台帳は `mutation/` (probe-spec.json / probe-out.json / final-spec.json / final-out.json)。

| 走 | HEAD | baseline | 結果 |
| --- | --- | --- | --- |
| probe (18 変異) | 8b26f3246 | PASSED | 負例 16 件すべて観測 node あり、M14b と MP1 は SURVIVED |
| 本走 (18 変異) | 8b26f3246 | PASSED | **KILLED 16 / 16、期待 node 完全一致、MISMATCH 0**、登録 SURVIVED 2 |

各変異は狙った負例だけを落とした。例:

| 変異 | 落ちた node |
| --- | --- |
| M1 accepted の `verify_configs` exact 一致を落とす | `refuses_nonexact_accepted_verifier_order[empty/prefix/reverse/duplicate]` + `refuses_terminal_mismatch[wrong-verify-configs]` (5) |
| M2 clean 検査を typed 層 + wire 層 + counter の 3 箇所同時に落とす | `refuses_dirty_nonserializable_result` (1) |
| M3 単一 class 検査を両層で `>= 1` へ緩める | `refuses_multiple_witness_classes` (1) |
| M4 `total_cycles` 等式を両層で落とす | `refuses_truncated_multiple_witness_classes` (1) |
| M6 witness 構造検査を落とす | 構造負例 3 種 + exact 型負例 2 種 (5) |
| M7 class digest を canonical bytes 以外から計算 | 共有 digest を使う 19 node (consumer の fixture baseline・端から端・producer digest test) |
| M8 terminal `verify` == snapshot を落とす | `refuses_terminal_mismatch[different-run-snapshot]` (1) |
| M9 `reason == verdict` を落とす | `refuses_terminal_mismatch[wrong-reason]` (1) |
| M15 projection digest 照合を落とす | `assembler_rejects_different_projection_same_attempt` (1) |
| M16 terminal 外枠 exact 検査を落とす | `refuses_terminal_root_shadow[reason/verify-configs/verify/build-attempt-id]` (4) |
| M-C1 consumer wrapper の `ArtifactError -> FC07` 変換を落とす | `test_fc07_converts_witness_canonicalization_artifact_error` (1) |

**M2〜M4 を単層で当てると mask される** (段 6 レンズ A の指摘) ため、typed 層と wire 層を同時に変える
複合変異として登録した。M5 (空 anomaly の拒否) は M3/M4 と独立に帰属できない
(両層を外すと `anomalies[0]` で例外になる) ので登録しなかった。

**登録 SURVIVED 2 件は実測に基づく。** MP1 は拒否理由の文字列だけを変える正例 (test が診断文字列を
pin していないことの確認)。**M14b (cycle 節点の `type(x) is int` を `isinstance` へ緩める) は、
負例 `cycle-bool` が `cycle[0] = True` を置くが r9 の `cycle[0]` は txid 0 で、ring 位置検査
(`edge["from"] != cycle[index]`) が先に拒否する過剰決定だった。** cycle 節点の型の厳密さは
producer 側でも負例で pin されていない。前 wave の [T-2438] (bool の穴) と同族であり、同項へ追記した。
初回 probe の SURVIVED は erratum として残す (DW-M02)。

## 7. 実走した検査

- 焦点走 8 file (変更 4 file + 参照 consumer test 3 file + fixture builder + plain-runner + verifier) を
  計算ノードで 2 回: 853 passed (段 5 後、982983.nqsv) → 865 passed (fix 後、983113.nqsv)、いずれも赤 0。
  新規 36 node は JUnit に実名で存在。
- 子はどの段でも `tools/run_tests.py` を通せなかった (sandbox の `qstat -Q` preflight で rc=16)。
  実走はすべて親が行った。
- AI provenance 全史監査: 8786 件、新規違反なし。
- 受入所要台帳へは本 wave の 36 node だけを実測値で `--add-only` した。
- 受入全走: 本記録 commit の時点では未実施。本 commit の後に投入し、結果は追記 commit と受入再走で確定する。

## 8. 残る限界

- 閉じたのは producer core API まで。production issuer への配線 ([T-2437] の残余) が無い限り、
  rejected の本番 projection は端から端まで通らない。
- witness class = verifier が SCC ごとに報告する代表 witness の digest。1 SCC 内の複数 simple cycle は
  1 class に縮約される。設計 §3.4 の「複数 class から 1 件を選ばない」は SCC 単位でしか成立せず、
  uniqueness の再定義は裁定パッケージ ({{T:witness-class-scc-representative}})。
- fixture 到達性は synthetic Silo source 束縛下の値であり、production 到達性は主張しない。
- consumer 側の terminal 外枠 gate は D1730 ([T-2384]) の別項のまま。producer 側だけを閉じた。
- D338 のとおり consumer は全検査通過後も `P6Unavailable` を返す。certified 選択集合は変わらない。
