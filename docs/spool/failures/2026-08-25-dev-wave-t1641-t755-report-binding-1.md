---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1641-t755-report-binding
seq: 1
---

## 新規

### {{F:redundant-gate-looks-like-coverage}}. 冗長な照合層を検出力として数えた [恒真ゲート]

- 事象: 段 6 の fix が受領証 SHA の照合を 3 点へ増やし、対応する変異を事前登録した。親が変異を
  実走すると、3 点のうち 2 点は単独で取り除いても **SURVIVED** した。shell 側の照合は job-result
  writer 側が包含していたため冗長で、sidecar 照合は既存の負例がすべて受領証本体も一緒に
  書き換えていたため手前の照合が先に拒否しており、単独の拒否理由になる入力が 1 つも無かった。
- 根本原因: 「その入力が拒否される」ことを「その述語が拒否した」ことの証拠として数えた。
  防壁を足した数と、単独で発火する述語の数が一致すると暗黙に仮定していた。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M03` (fixture が単一理由か確認し、過剰決定なら
  単一理由へ差し替えるか冗長 gate と明記して単独変異の証拠から外す) を、**自分が同じ wave で
  足した防壁にも適用する**。本 wave では sidecar 照合に単一理由の負例
  (`orchestrator/tests/test_mocc_trace_job_contract.py::test_mocc_trace_binding_h1_rejects_sidecar_only_tamper`)
  を足し、shell 側は SURVIVED 期待として冗長 gate と明記して登録した。
- 再発検知: 変異 spec で新設した各述語を単独で取り除く変異を必ず登録する。SURVIVED は等価変異と
  して片付けず、`DW-M02` に従い実効 gate へ再照準して両層同時変異まで裏取りする。

### {{F:transcription-mistaken-for-proof-chain}}. 受領証へ値を写すことを証拠の鎖と取り違えた [恒真ゲート]

- 事象: 裁定 (D779) が名指した 4 項目 (report の path・SHA-256・schema・guarantee) を受領証へ
  写す設計を段 2 で起草した。段 3 の敵対相談 2 本が独立に「report が自分で名乗った値を写しても、
  その検査がその保証を与えた証拠にならない」と反証した。所定 path に偽の report を置けば内容述語は
  すべて通り、SHA-256 は偽の自己申告を含む bytes を正確に束縛するだけになる。
- 根本原因: 裁定の**条項**だけを読み、裁定の**理由節**を実装要件へ落とさなかった。D779 の理由は
  「どの検査が何を保証したかを証拠の鎖として辿れない」ことであり、求められていたのは鎖である。
- 恒久対応: {{D:bind-report-to-invocation}} — report の自己申告を producer の実引数
  (commit の新旧・repo・compiler・対象 path) と照合する。実装は
  `tools/pegasus/mocc_trace_pilot.sh` の受領証 writer にあり、変異 M06〜M10 が各述語を単独で守る。
- 再発検知: 受領証・台帳へ「検査を通った」と書く field を足す wave では、その値が producer の
  実行と結合していない経路を敵対レンズの必須攻撃面に含める。
