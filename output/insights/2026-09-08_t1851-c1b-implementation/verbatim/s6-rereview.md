## 対応表

| 所見 | 判定 | 現物根拠と判断 |
|---|---|---|
| R-1 | `closed` | certified wrapper だけが private capability を生成する (`orchestrator/campaign/s8b_floor_attempt_launcher.py:1181-1196`)。test seam は明示的に `None` を渡す (`同:1230-1244`)。capability は reserve state の fingerprint に identity で含まれ (`orchestrator/campaign/s8b_attempt_registry.py:267-286`)、発行時に state と draft の同一性まで検査される (`同:3141-3155`)。公開 `reserve_attempt_slot()` の引数自体は呼び手が選べるが、正当な値は private issuer の直接呼出しなしには作れない (`同:78-101`)。これは契約 6.4 の除外内であり、`_launch_floor_attempt_for_test()` からは到達できない。 |
| R-2 | `closed` | certified 経路では reservation snapshot が registry genesis、reserve、capture、builder より前に作られる (`orchestrator/campaign/s8b_floor_attempt_launcher.py:605-618,962-977`)。builder は `:1116`、sealer は事前取得済み snapshot だけを受け取る (`:1127-1145`)。公開 3 引数の legacy 分岐は呼出時に snapshot を取るため、それ単体では builder 後の mutation を防がない (`orchestrator/campaign/s8b_terminal_evidence.py:1008-1025`)。ただしその draft の origin は `None` であり、公開 adapter 発行経路は正当な origin を必須とする (`orchestrator/campaign/s8b_attempt_registry.py:3149-3155`)。legacy 呼出しから publish するには private issuer 直呼びまたは reflection が必要で、契約 6.4 の除外内である。 |
| R-3 | `partial` | 発行時の builder 攻撃は閉じた。probe、failure、launch failures、rep sink、measurement throughput は builder 前に canonical snapshot へ入る (`orchestrator/campaign/s8b_terminal_evidence.py:503-571`)。builder には復元した別 tree が渡る (`orchestrator/campaign/s8b_floor_attempt_launcher.py:1080-1113`)。分類 receipt の external digest も発行時には照合される (`orchestrator/campaign/s8b_attempt_registry.py:3157-3169`)。しかしこの照合値は canonical evidence に保存されず、durable replay で再照合されない。詳細は新規所見 1。 |
| R-4 | `closed` | builder の `campaign_record` は一度だけ `dict` 化して canonical bytes へ固定される (`orchestrator/campaign/s8b_terminal_evidence.py:578-602`)。launcher facts はその bytes の復元値を見る (`orchestrator/campaign/s8b_floor_attempt_launcher.py:895-923`)。sealer も同じ `_campaign_record_bytes` を読む (`orchestrator/campaign/s8b_terminal_evidence.py:1029-1030,1141-1143`)。したがって `get()` と iteration が異なる stateful `Mapping` で launcher と leaf に別値を見せる攻撃は閉じた。canonical 復元による exact-type 消失は別の新規所見 2。 |
| R-5 | `closed` | 実 slot に対する `holdout_id`、`configuration_id`、`retry_ordinal` の三検査がある (`orchestrator/campaign/s8b_attempt_registry.py:1356-1368`)。発行 transition でも呼ばれ (`同:3244-3250`)、durable replay loader でも呼ばれる (`同:1461-1497`)。片側だけではない。 |
| R-6 | `closed` | `failure.stage == "capture"` なら `launch_failures_count == 0` を要求する (`orchestrator/campaign/s8b_terminal_evidence.py:719-748`)。発行時は `seal_terminal_evidence()` から同検査へ入る (`同:1080-1084`)。replay も `_validated_document()` から同検査へ入る (`同:827-850`)。 |
| R-7 | `closed` | v2 だけ `TimeoutExpired`、`OSError`、`RuntimeError` の順で基底カテゴリへ正規化する (`orchestrator/campaign/s8b_floor_attempt_launcher.py:431-453`)。capture と open の双方が `qualify_timeout=policy.is_v2` を渡す (`同:1000-1003,1038-1046`)。v1 では flag が偽なので具体名を維持する。v1 profile は retryable reason 空集合 (`orchestrator/campaign/s8b_attempt_profile.py:539-552,671-688`) と既定 `retryable_reason_field="failure_reason"` (`orchestrator/campaign/attempt_registry_core.py:214-219`) のままである。 |
| R-8 | `closed` | 座標検査は `capture_executed and failure is None` に限定された (`orchestrator/campaign/s8b_floor_attempt_launcher.py:990-1005,1047-1053`)。`capture_executed` が偽になるのは pre-probe competing で capture を省いた場合だけであり、本来通すべき枝だけが追加受理される。capture/open failure は以前から `failure is None` 条件の外で、ほかの正常 capture の座標検査は維持されている。 |

## 新規所見 1

- (a) 発行時だけ検査される `external_evidence_sha256` が canonical terminal evidence から消えるため、durable replay では分類 receipt と terminal source digest の結び付きを改竄できる。
- (b) `SealedTerminalEvidenceDraft` の external digest は canonical bytes 外の private 属性である (`orchestrator/campaign/s8b_terminal_evidence.py:762-769,1170-1181`)。canonical outer keys に同 field は無い (`同:168-199`)。promotion は canonical bytes だけをコピーし、属性を validated capability へ移さない (`orchestrator/campaign/s8b_attempt_registry.py:1197-1210`)。照合は発行時の `record_sealed_attempt_terminal()` にしかない (`同:3157-3169`)。replay loader は binding と durable identity を検査するが external digest を読まない (`同:1437-1498`)。
- (c) 正当な terminal evidence file の `probe_before_sha256` だけを偽 digest へ変更し、canonical bytes と新 digest を作る。最後の terminal row の `terminal_evidence_sha256` と `event_sha256` を更新する。probe summary、E1 projection、11 個の row/file 等値、attempt binding、durable slot identity は変えない。replay は新 file を受理するが、classification receipt の `external_evidence_sha256` は元の観測を指したままであり、proof chain に観測していない source digest が入る。private issuer は不要である。
- (d) canonical evidence に `external_evidence_sha256` を含めるだけでは、component digest 改変との関係を再導出できない。pre-output evidence の canonical bytes を external digest 名の create-only file として保存し、replay 時にそれを読み直して classification receipt、probe/failure/launch-failure の各 digest を再導出して照合する。代案は、永続化済み component digest から再導出可能な別の composite digest を追加することである。発行時と replay 時の同一検査を対で置く。
- (e) 重大度: `blocker`

## 新規所見 2

- (a) rep sink と campaign record を検査前に JSON 往復させるため、以前の exact-type gate が source object に対して発火せず、v2 の受理集合が広がった。
- (b) rep observations は値を検査する前に `_canonical_copy()` で JSON 復元される (`orchestrator/campaign/s8b_terminal_evidence.py:520-529`)。さらに opened source 全体が canonical bytes 化・復元され (`同:567-576`)、その後で `_derive_rep_integrity()` が呼ばれる (`同:918-949`)。同 validator が本来持つ `rep_index`、`returncode`、perf counter の exact-int 検査は `orchestrator/campaign/s8b_floor_stats.py:480-499,514-532` にある。terminal campaign record も値検査より先に canonical 化される (`orchestrator/campaign/s8b_terminal_evidence.py:578-602`)。
- (c) private rep sink の `rep_index` または `returncode` に `int` subclass や `IntEnum` を入れる。旧経路では `type(value) is int` が偽となり rep integrity failure だったが、新経路では JSON 復元により通常の `int` へ変換される。builder と sealer はどちらも正規化後の値を見て `rep_integrity_failures == 0` の `observed` terminal を作れる。元の private sink に対して必要だった exact-type 拒否が証拠へ反映されない。
- (d) stateful `Mapping` を再読せず一度 `dict` 化した直後、その exact dict の各 source field を型検査してから canonical 化する。rep observations は `_derive_rep_integrity()` が要求する exact scalar 型を snapshot 前に検査し、terminal record も `_campaign_plaintext()` 相当の source-shape 検査を canonical 化前に行う。`int` subclass、`str` subclass、`IntEnum` の負例を追加する。
- (e) 重大度: `must-fix`

## 新規所見 3

- (a) F1 と F3 のテストは、対象 gate を外しても後段 fake registry が必ず拒否するため、単一理由の mutation kill として帰属できない。
- (b) `_RecorderRegistry.record_sealed_attempt_terminal()` は無条件に例外を送出する (`orchestrator/tests/test_s8b_floor_attempt_launcher.py:191-201`)。F1 のテストは同 fake を使う (`同:1714-1746`)。F3 も同じ fake を使う (`同:1836-1901`)。
- (c) F1 で protocol 再読へ戻すと、意図した E1 拒否は消えるが、その後 fake registry の「validated evidence を発行できない」で拒否される。F3 で launcher/sealer の二重読みに戻して SplitRecord 攻撃が通っても、同じ後段拒否に達する。テストは期待例外の型または message が違うため赤になるだけで、攻撃入力が受理可能になったことを単独には示さない。依頼の「前後の冗長拒否を kill に数えない」に該当する。
- (d) この二テストでは sealed draft を保存して正常 return する accept-only fake recorder を使う。現実装では対象 gate で拒否し、F1/F3 mutant では最後まで return して偽 draft が観測できる形にする。F1 は private reservation snapshot を直接 sealer へ渡す純関数 test に分離する方法でもよい。
- (e) 重大度: `must-fix`

## 新規所見 4

- (a) F2 の「builder へ元 sink を渡す」変異は、すでに builder 前 canonical snapshot が権威なので攻撃を成立させず、実効 gate の変異になっていない。
- (b) opened snapshot は builder 前に完成する (`orchestrator/campaign/s8b_floor_attempt_launcher.py:1080-1087`)。builder 呼出しはその後 (`同:1116`)。F2 対応テストは builder の mutation 後にも terminal mismatch を期待し、さらに元 sink が不変であることを assert する (`orchestrator/tests/test_s8b_floor_attempt_launcher.py:1798-1833`)。
- (c) builder に元 sink の dict を共有しても、sealer は事前 snapshot を読むため、builder が作った偽 terminal は現在と同じ terminal mismatch で拒否される。mutant が赤になる場合も、最後の「元 sink が変わっていない」という防御多重化の assertion によるもので、proof chain の受理可否は変わらない。
- (d) F2 を `_snapshot_opened_source()` の削除、builder 後への遅延、または sealer による builder-exposed sink の再読へ再照準する。その mutant では偽 terminal が accept-only recorder まで到達するようにする。元 sink 非共有自体は構造テストとして残してよいが、単一理由の security kill には数えない。
- (e) 重大度: `must-fix`

## 変異帰属

| 変異 | 単一帰属 | 静的判断 |
|---|---|---|
| F1 | 確認できず | protocol gate 消失後も fake recorder が必ず拒否する。新規所見 3。 |
| F2 | 確認できず | private pre-builder snapshot が残るため、元 sink 共有だけでは攻撃が通らない。新規所見 4。 |
| F3 | 確認できず | SplitRecord が launcher/sealer を通っても fake recorder が必ず拒否する。新規所見 3。 |
| F4 | 確認できた | 発行の三負例は実 slot 検査を直接狙う (`orchestrator/tests/test_s8b_attempt_registry.py:4213-4243`)。replay 側にも独立した三負例がある (`同:4246-4290`)。ほかの durable claim 検査は campaign record のこの三 field を拒否しない。 |
| F5 | 確認できた | leaf の capture/count 正負対が直接 `_assert_mutual_consistency()` を通る (`orchestrator/tests/test_s8b_terminal_evidence.py:631-652`)。後段 stub に依存せず、replay 負例もある (`orchestrator/tests/test_s8b_attempt_registry.py:4309-4367`)。 |
| F6 | 確認できた | helper を直接呼び、legacy 名と v2 基底名を別々に比較する (`orchestrator/tests/test_s8b_floor_attempt_launcher.py:1996-2029`)。下流拒否による見かけの kill ではない。 |
| F7 | 確認できた | test seam は全 method を real adapter へ転送する (`orchestrator/tests/test_s8b_floor_attempt_launcher.py:1904-1942`)。origin gate を外せば後段 fake 拒否はなく、real terminal publish へ到達する。 |

## 総括

- 判定: `no-go`
- R-1〜R-8: `closed` 7 件、`partial` 1 件、`regressed` 0 件
- 新規所見: `blocker` 1 件、`must-fix` 3 件、`nit` 0 件
- F1〜F7:
  - 単一帰属を確認: F4、F5、F6、F7
  - 確認できず: F1、F2、F3
- 攻撃したが破れなかった箇所:
  - legacy の公開 3 引数 sealer は遅い snapshot を許すが、正当な launcher-origin capability を持たず公開 adapter から publish できなかった。
  - stateful `Mapping` の `get()` と iteration を分離する R-4 攻撃は、同じ canonical campaign-record bytes を launcher と sealer が読むため再現しなかった。
  - launcher-owned な protocol/opened source の snapshot はすべて builder より前だった。builder 後に取られるのは builder 自身の候補 terminal の一回読みだけである。
  - R-8 の条件変更は pre-probe competing だけを追加受理し、通常 capture の座標検査や failure 条件を緩めていなかった。
  - v1 terminal key は既存 `_S8B_EVENT_KEYS["terminal"]` の exact 24 のまま (`orchestrator/campaign/s8b_attempt_profile.py:449-466`)。retryable reason は空、既定 reason field は `"failure_reason"` であり、R-7 の正規化も v1 へ漏れていない。
  - 3 commit 全体の既存 test 差分では、許可された二箜所以外の期待反転、緩和、skip、xfail、削除、golden 更新は見つからなかった。fix の既存行変更は fixture の sealed/capture-failure 対応と callback ABI 追随である。
- 制約どおり pytest は実行せず、静的検査だけで判定した。