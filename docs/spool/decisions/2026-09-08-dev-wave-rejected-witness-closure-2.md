---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-rejected-witness-closure
seq: 2
---

## {{D:fc07-rejected-witness-from-verify}}. FC07 の rejected 枝は production の abort payload だけを読み、witness class を verifier 証拠から導く

**決定:** `orchestrator/campaign/reflux_formal_consumer.py` の `_validate_wal_outcomes()` の
rejected 枝から `candidate_attributable` / `truncated` / `witness_class_sha256s` の 3 field を
**廃止する**。代わりに production の abort payload (`orchestrator/campaign/pipeline.py` の
verifier reject 経路が書く `reason` と `verify`) だけを読み、3 つの述語を導く。

- **candidate 帰属:** `reason` と `verify["verdict"]` がともに `"non-serializable"` であること。
  `"indeterminate"` (空 trace または integrity 不成立) は candidate 起因に数えない。
  併せて `verify` の内部整合 (`serializable is False`、`certified is False`、
  `integrity["clean"] is True`、wire へ射影された 11 個の integrity counter がすべて exact int の 0)
  を要求する。counter 条件は `Integrity.clean()` の**必要条件であって十分条件ではない** —
  `proof_surfaces` と commit witness は wire へ射影されない。
- **非切詰め:** `anomaly_count == len(anomalies)` かつ `total_cycles == anomaly_count`。
  verifier は切詰め前の全 SCC 数と切詰め後の witness 列を別々に持つ
  (`orchestrator/verifier/dsg.py` の `anomalies(max_report)` が両方を返す)。
- **witness class:** `anomalies` はちょうど 1 件で、その anomaly の canonical JSON の sha256 が
  `physical_result.constraint_sha256` と exact 一致すること。**list の順序は正規化しない。**

witness anomaly は production の生成器から導ける形だけを受理する — key 集合の exact 一致、
`phenomenon` が全 edge type からの再導出値と一致、`cycle` が長さ 2 以上の相異なる exact int 列、
`length == len(cycle)`、edge が `cycle` の ring 位置に対応、reason の `type` が
`orchestrator.verifier.model` の `WW` / `WR` / `RW` の閉集合の要素、edge の `types` が reasons の
type の出現順重複除去と一致、version field の有無が reason type と対応、version が exact int 2 要素。
`verify` / `stats` / `integrity` / `permutation_violation_details` の key 集合と値の型も
production の `result_to_dict()` の形に閉じる。

`reflux_source_closure.py` の token 表の `wal.abort.payload.witnesses` を、consumer が実際に読む
`wal.abort.payload.verify.anomalies` へ改める。`_wal_field()` の root→payload fallback、
FC07 以外の判定式、reason code、他の gate、terminal record の外枠は変えない。

**理由:**
- 廃止した 3 field には production producer が 1 つも存在しなかった (`orchestrator/campaign/`
  全走査で 0 件)。token 表が挙げていた `witnesses` も存在せず、同じ表の commit 側
  `wal.commit.payload.verify_configs` だけが実在していた。成果物が**指示対象の無い束縛**を
  主張している状態であり、この束縛を信頼して producer を書けば虚構に対して実装することになる。
- producer が書く boolean は自己申告であり、consumer はそれを検算する独立の証拠を持たない。
  consumer 側で導けば、record が主張する `constraint_sha256` を WAL 上の実 verifier 証拠と
  突き合わせる形になり、入力の 2 つの部分が互いを検算する。
- 正規化 (整列・重複排除) を置かないのは、`cycle` が最短 cycle の**順序付き**節点列で、
  `edges` がその ring 順に対応しているためである。整列すると同じ節点集合上の異なる cycle が
  同じ digest へ落ち、受理集合が広がる。
- `indeterminate` を除くのは、verifier 自身の契約が「integrity が unclean な run は辺が落ちて
  real cycle を隠している恐れがあるため serializable を認証できない」としているためである。
  同じ理由で `integrity["clean"] is True` を要求する — 壊れた trace 由来の cycle を
  candidate-attributable として受理するのは正しさ防壁の直接的な拡張である。
- 構造検査を置くのは、置かないと `anomalies=[{}]` のような production verifier が生成できない
  任意の dict が witness class として通るためである。段 6 の敵対レビュー 2 本が独立に、
  通る入力を具体的に示した。

**却下した選択肢:**
- producer 側に 3 field を新設する — record 層の producer が repo に 1 件も無いため
  (`OriginProducerInputs` の構築は test 1 箇所だけ)、この方向は record 層 producer の新設まで
  連鎖し「不整合の解消だけ」を超える。なお「producer が書くと必ず恒真になる」という
  起草時の理由は誤りで、段 3 のレンズが反例を示した。方向の選択理由は上記へ狭めた。
- 旧 3 field と production 形の両受け — 受理集合が広がり、fixture 由来の形が本番へ紛れ込む
  経路を残す (規律 2)。D1665 と D1715 が同じ理由で却下したのと同型である。
- witness class の正規化で anomaly の list 順序を吸収する — 上記のとおり受理集合を広げる。
  加えて吸収すべき非決定性が同一 bytes に対しては存在しない。
- terminal record の外枠を同じ変更単位で閉じる — D1730 が裁定済みの別項であり、
  本 wave の名指し外である。
- `orchestrator/verifier/dsg.py` の理由順を整列して決定的にする — producer 側の変更であり、
  verifier の出力 bytes を変える。別項として裁定へ返す。

**限界:**
- 本決定が閉じたのは **WAL 側の不整合だけ**である。result-evidence record を発行する
  production producer は依然存在しないため、rejected の本番 projection が端から端まで通るように
  なったわけではない。record 側が同じ規則で `constraint_sha256` を導かなければ FC07 で止まる。
- witness class は occurrence identity (txid) を含む。同じ構造の違反が別 txid で 2 回現れると
  cardinality 2 で拒否される。構造同値類の定義は新しい一般化であり scope 外とした。
- 同じ理由で、`dsg.py` の理由順が process 間で変わるため、同一 trace の 2 回の run が
  別の class を生みうる。FC07 の検査は記録された bytes に対して行うのでこの決定は壊れないが、
  class の意味は run 依存である。
- `Integrity.clean()` の `proof_surfaces` と commit witness の条件は wire へ射影されないため、
  consumer 単独では十分条件を再計算できない。
- D338 のとおり consumer は全検査通過後も `P6Unavailable` を返す。certified 選択集合と
  測定 cell、`OriginSealed` event payload は変わらない。変わるのは fixture 由来の record /
  source-closure digest と、そこから連鎖する receipt・`formal_receipt_sha256` /
  `evidence_root_sha256`、および report artifact・lifecycle terminal・acceptance receipt の bytes である。
- 受理集合の変化は単調ではない。旧 3-field 形は除外され、production `verify` 形が追加される。
