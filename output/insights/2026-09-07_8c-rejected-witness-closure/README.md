# 8c formal consumer の rejected 枝を production の実在 field へ合わせ、witness を verifier が生成できる形だけに閉じた

**種別:** 読み手 (consumer) の修理。dev-wave `dev-wave-rejected-witness-closure` (2026-09-07〜09-08)。
設計判断は {{D:fc07-rejected-witness-from-verify}} (fold 後は実番号)。起点は D1715 が
「rejected 側 witness 系 field の producer を新設する — 名指し外。別項として起票した」と
明示的に送った項目である。

**この wave が閉じたのは WAL 側の不整合だけである。** result-evidence record 全体の
production producer は依然存在しない (`OriginProducerInputs` の構築は repo 内で test 1 箇所のみ)。
record を発行する側が同じ規則で `physical_result.constraint_sha256` を導かない限り、
rejected の本番 projection は端から端まで通らない。本番 projection が端から端まで通るようになった
とは書かない。

## 1. 何が食い違っていたか

| | 変更前 | 変更後 |
| --- | --- | --- |
| consumer が読む field | `candidate_attributable` / `truncated` / `witness_class_sha256s` | `reason` と `verify.*` |
| その producer | **0 件** (`orchestrator/campaign/` 全走査) | `orchestrator/campaign/pipeline.py` の verifier reject 経路 |
| token 表 (`reflux_source_closure.py`) | `wal.abort.payload.witnesses` (**存在しない第 3 の別名**) | `wal.abort.payload.verify.anomalies` |
| 同表の commit 側 | `wal.commit.payload.verify_configs` (実在) | 変更なし |

**表は半分だけ実在していた。** commit 側の token は `pipeline.py:1821,1836` が実際に書くが、
abort 側の `witnesses` はどこにも書かれない。source-closure 成果物は
「`verifier_policy_sha256` は runtime でこの field に束縛される」と宣言しており、
proof chain の成果物が**指示対象の無い束縛**を主張している状態だった。

## 2. 方向の決め方 — producer を書くか、consumer を合わせるか

実測した現物の field 名で決めた。

- verifier reject の abort payload は
  `{reason, build_attempt_id, build_admission_receipt_sha256, verify, workload}` で、
  `verify` は `orchestrator/verifier/report.py` の `result_to_dict()` から `trace_dir` を除いたもの。
- `reason` は `vr.verdict` そのもの。abort reason は repo 全体で 30 種あり、
  candidate 起因になりうるのは verifier reject 経路の verdict だけである。
- record 層の producer は存在しない。producer 方向は record 層 producer の新設まで連鎖し、
  「不整合の解消だけ」という scope を超える。

**consumer を実在 field へ合わせる**方向を採り、3 つの述語を実 verifier 証拠から導く形にした。

## 3. 親の裁定の根拠 3 件が、子の実測で否定された

この wave の中心的な出来事である。3 件とも親が受け入れて裁定を訂正した。

| 親が書いた前提 | 実測した現実 | 誰が |
| --- | --- | --- |
| producer が書く boolean は必ず恒真になる | producer は untyped JSON へ潰れる前の `VerifyResult` を持つので偽になりうる値を書ける | 段 3 レンズ A |
| `canonical_json_bytes()` は float を拒否する | 有限 float を許す。`2.0 == 2` により型検査を素通りする | 段 6 レンズ A |
| verifier の出力は決定的なので正規化は不要 | `dsg.py` の `_reasons()` が集合を未整列で走査し、理由順が process 間で変わる | 段 6 レンズ B |

1 件目は方向の理由を狭めるだけで済んだ (方向自体は維持)。2 件目は**実際に受理集合を広げており**、
段 6 で修理した。3 件目は FC07 の検査自体は壊さない (digest は記録された bytes に対して取るので
1 record 内では一貫する) が、class の意味が run 依存になる。producer 側の変更なので裁定へ返した。

いずれも**関数を 1 本呼べば 10 秒で確かめられる事実**だった。
{{F:unmeasured-runtime-premise-as-ruling-ground}} に記録した。

## 4. 段 6 の敵対レビューが見つけた受理穴

2 レンズが独立に、**具体的に通る入力**を伴う所見を出した。すべて規律 2 に触る。

- `anomalies=[{}]` が witness class として通る。構造検査が無かった。
- `integrity.clean=False` の cycle を candidate 起因と誤認する。verifier 自身の契約は
  「dirty integrity の cycle は CC variant の anomaly でない可能性が高い」としている。
- `verdict=non-serializable` と `certified=true` の相互矛盾を検査していない。
- `anomaly_count == len(anomalies)` を consumer 境界で検査していないため counter を偽装できる。
- `stats` を丸ごと欠いた payload、`clean=true` と `orphan_reads=1` が同居する payload が通る。
- `stats["txns"]="bad"`、`counts={}`、`sample="bad"` が通る (fix 後の再レビューが検出)。

fix 2 巡で閉じた。fix 後の焦点再レビューは closed 4 / partial 4 / regressed 0 で、
「新たに落ちるようになった正当な production 入力は無い」ことを
`_reasons()` の全分岐・`_classify` の導出・`_shortest_cycle` の最小長・clean な run の
11 counter を個別に辿って確認している。

## 5. 実装した判定式

production の生成器から導ける関係だけを要求する。逐語 literal は閉集合の宣言だけに留め、
`WW` / `WR` / `RW` は `orchestrator.verifier.model` から import した。

- candidate 帰属: `reason` と `verify["verdict"]` がともに `"non-serializable"`。
  `"indeterminate"` は数えない。`serializable is False`、`certified is False`、
  `integrity["clean"] is True`、wire へ射影された 11 counter がすべて exact int の 0。
  **counter 条件は `Integrity.clean()` の必要条件であって十分条件ではない** —
  `proof_surfaces` と commit witness は wire へ射影されない。
- 非切詰め: `anomaly_count == len(anomalies)` かつ `total_cycles == anomaly_count`。
- witness class: `anomalies` はちょうど 1 件。その anomaly の canonical JSON の sha256 が
  `physical_result.constraint_sha256` と exact 一致。**list の順序は正規化しない。**
- 構造: key 集合の exact 一致、`phenomenon` が全 edge type からの再導出値と一致、
  `cycle` が長さ 2 以上の相異なる exact int 列、`length == len(cycle)`、
  edge が `cycle` の ring 位置に対応、reason type が閉集合の要素、
  `types` が reasons の type の出現順重複除去と一致、version の有無が reason type と対応、
  version が exact int 2 要素。`verify` / `stats` / `integrity` /
  `permutation_violation_details` の key 集合と値の型も production の形に閉じる。

**正規化を置かない理由:** `cycle` は最短 cycle の順序付き節点列で、`edges` はその ring 順に
対応している (`dsg.py` の `ring = list(zip(nodes, nodes[1:] + nodes[:1]))`)。整列すると
同じ節点集合上の異なる cycle が同じ digest へ落ち、受理集合が広がる。

## 6. 正例は実体を名指しする

`test_real_dense_cycle4_anomaly_passes_witness_structure_validator` は
`orchestrator.verifier.core.verify_trace_dir` を `orchestrator/tests/fixtures/r9_dense_cycle4` へ
実走させ、`result_to_dict()` の anomaly が構造検査を通ることを assert する。
性質を満たす手書き dict では代用していない。

key 集合の literal drift は `test_real_dense_cycle4_report_schema_matches_consumer_key_sets` が
同じ実 callee の出力と consumer 側 frozenset を突き合わせて塞ぐ。

到達可能性 (DW-O13) は `orchestrator/tests/test_verifier.py::test_dense_cycle4_clean_g2` が
実測している — clean integrity + `non-serializable` + `total_cycles == 1` + anomaly 1 件。

## 7. 変異 matrix (B-060)

probe 走 (全件 SURVIVED 登録で観測 node を集める) → 本走の 2 段。baseline は全走で PASSED (rc=0)。

| spec | runner | 登録 | 結果 |
| --- | --- | --- | --- |
| A | `test_reflux_formal_consumer.py` | 22 | KILLED 20 / SURVIVED 2 / MISMATCH 0、期待 node 完全一致 |
| B | 焦点走 12 file | 2 | KILLED 2 / MISMATCH 0、期待 node 完全一致 |

各変異は**狙った単一理由の負例だけ**を落とした。例:

| 変異 | 落ちた node |
| --- | --- |
| reason allowlist を `True` に | `test_fc07_rejects_non_candidate_reason_with_valid_verify` |
| `integrity.clean is True` を落とす | `test_fc07_rejects_dirty_integrity_with_valid_cycle` |
| clean の 11 counter 検査を落とす | `test_fc07_rejects_clean_integrity_with_nonzero_wire_counter` |
| ring 位置対応を落とす | `test_fc07_rejects_ring_position_mismatch_with_matching_digest` |
| token 表を旧名へ戻す | 125 node |
| baseline の digest を 1 文字壊す | `test_baseline_schema_and_every_entry_match_independent_recalculation` |

**登録 SURVIVED 2 件は実測に基づく。** `type(x) is not int` を `isinstance` へ緩める変異は
`isinstance(2.0, int)` が False であるため、float を使う既存の負例に対して**等価変異**だった。
開くのは bool の穴だけで、それを突く負例が集合に無い。`DW-M02` に従い型検査そのものを
取り除く形へ再照準して KILLED を得た (`b060.m23-length-exact-int-removed` /
`b060.m24-endpoint-exact-int-removed`)。isinstance 版は「型の**厳密さ**が負例で pin されていない」
ことの実測として登録 SURVIVED のまま残した。初回の SURVIVED は F245 への再発として記録した。

spec B の本走 HEAD は `2d6b8c673` で spec A の `becaf2a6b` より 1 commit 古いが、
両者の差分は spec A の JSON 1 file だけで、spec B の対象 3 file の blob は同一である (実測)。

## 8. pin の同期

fixture の `verify` payload は production `result_to_dict()` の key 集合と**元から完全一致**して
いたため、段 6 の 2 巡の厳格化では fixture を 1 byte も変えていない。したがって pin が変わったのは
段 5 の 1 回だけである。

段 6 レンズ B が baseline の 7 entry すべてを**別 canonicalizer で独立に導き直し**、
変わるべき 5 entry が変わり、変わるべきでない 2 entry (`build_authority_manifest` /
`build_execution_provenance`) が不変であることを確認した。第三の pin が無いことは
4 経路 (64 桁 hex literal 走査 / 長さ literal 走査 / 生成関数の全 caller 追跡 /
`orchestrator/tests` 外の走査) で独立に確かめている。

## 9. 段 5 の実装子は最終報告を出していない

job-id `s5-author-20260907a` は model call 上限 100 に達して SIGTERM で打ち切られた
(`limit_trigger=max_model_calls`、`failure_class=f45_missing_output`、wall 2629 秒)。
編集は所有 7 file すべてに完了しており、内容は段 4 裁定と一致していた。

**この wave には段 5 の子の自己申告が存在しない。** 段 6 の 2 レンズへ
「子の主張として信じてよいものは何も無い」と明示して投げ、pin の再計算と単一理由性を
独立に検算させた。実走はすべて親が行った。詳細は `verbatim/codex/s5-author-NOTE.md`。

## 10. 実走した検査

- 焦点走 12 file を 3 回: 765 → 785 → 799 passed、いずれも rc=0 (計算ノード dispatch)。
- 変異 probe 走 2 本・本走 2 本: baseline すべて PASSED。
- AI provenance 全史監査: rc=0。
- `tools/check_docs.py`: rc=0。
- 受入全走 1 回目: 21591 passed / 1 failed / 68 skipped。赤 1 件は受入所要台帳の被覆率 gate で、
  実測で本 wave 起因と確定した (main 単独 90.0120% -> 本 wave 89.7415%)。新規 65 node を
  単独走させた JUnit の実測値だけを `--add-only` で足し、既存 entry を変えずに 90.0416% へ戻した。
- 受入全走 2 回目: **child-green**、21592 passed / 68 skipped / 0 failed、
  tested_main = 240ee63602ee17334b28780b70587f345b2e0495。

## 11. 残る限界

- 閉じたのは WAL 側だけである。result-evidence record の production producer は不在
  ({{T:result-evidence-record-producer}})。
- witness class は occurrence identity (txid) を含む。同じ構造の違反が別 txid で 2 回現れると
  cardinality 2 で拒否される。構造同値類の定義は scope 外とした。
- `dsg.py` の理由順が process 間で変わるため、同一 trace の 2 回の run が別の class を生みうる
  ({{T:verifier-reason-order-determinism}})。
- 型検査の厳密さ (bool の拒否) は負例で pin されていない
  ({{T:witness-type-exactness-not-pinned}})。
- terminal record の外枠・重複・root shadow は閉じていない。これは D1730 で裁定済みの
  [T-2384] が持つ項目であり、本 wave では触れていない。
- `Integrity.clean()` の `proof_surfaces` と commit witness の条件は wire へ射影されないため、
  consumer 単独では十分条件を再計算できない。
- D338 のとおり consumer は全検査通過後も `P6Unavailable` を返す。certified 選択集合、
  測定 cell、`OriginSealed` event payload は変わらない。変わるのは fixture 由来の digest と、
  そこから連鎖する receipt・report artifact・lifecycle terminal・acceptance receipt の bytes である。
- **受理集合の変化は単調ではない。** 旧 3-field 形は除外され、production `verify` 形が追加される。
