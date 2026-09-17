---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t1170-run-start-schema-version
seq: 2
---

## {{D:run-start-consumer-owned-schema-generation}}. 自律試行 journal `run-start` の読める世代は完全性 consumer が独立に持ち、producer の現行版には追随しない

**決定 (1): D1898 の「版を上げる」は、role payload の key 改名で `SCHEMA_VERSION` を v4 へ上げた
4c6f03048 (2026-09-16、D2064 決定 2) で run-start 側にも実体化したものとして利用し、本件のために v5 へは上げない。**
理由は、v4 の run-start は一つの形 (無条件 key + trial_binding 条件付き key) しか持たず、v3 の記録と現行出力を
版だけで既に区別できること、および v4 に対する新たな形の変更が無いことである。D1851 は「版を上げる差分は
新機能を使わない構成の正例を持つ」と定めるが、形を変えない bump を禁じてはいない。v5 へ上げると role payload
(同じ定数) も v5 になって独立の role consumer (v4) と食い違い、09-16 以降の v4 記録が現行 consumer の対象外になる。
T-304 の wave が本件を完了したと宣言したわけではないので、そう遡って記録しない。

**決定 (2): 完全性 consumer (`autonomous_trial_completeness._check_run_envelope`) は、run-start の読める世代を
独立リテラル定数 `_RUN_START_SCHEMA_VERSION` (現行 v4) として所有し、producer の生きた `SCHEMA_VERSION` とは
照合しない。** role payload 側の `_ROLE_SCHEMA_VERSION` (D2064 決定 2 の独立二重定義) と同型である。
これにより、記録済み artifact の世代の判定が producer の改版から独立する。同期は「現行 producer の実走出力が
consumer を通る」既存の統合正例と、producer 定数を別値にしても v4 記録の判定が変わらない独立性の正例で担保し、
import 比較などの同期 gate は足さない。

**決定 (3): 旧 record は記録された版のまま世代を分類して fail-closed にし、変換も alias も decoder も足さない。**
拒否理由は記録の版・世代分類 (`legacy` は実在を確認した v3 の文字列だけ、それ以外は `unknown`)・consumer の対応版を
文言で名指す (規律 3)。機械可読な属性や report field の追加ではない。v3 の歴史 decoder は D1669 の条件
(実在成果物 + 読み手) のうち読み手を今回の直接参照の検索で確認できていないため作らない。受理集合は v4 のみで不変であり、v4 の形は
従来の field 検査が担う (exact-key 契約の新設ではない)。世代診断は版 gate に到達した記録に対する保証であり、
report 版・journal の hash・event 順序の検査が先行する。

**理由:**
- 直接の原因は consumer が producer の可変定数を受理条件に使っていたことである。producer が版を上げるたびに
  記録済み run の判定が黙って変わり、記録済み artifact の世代と現行 producer の世代を区別できなかった
  (F332 の副次的所見)。run-start と role payload が 1 定数を共有していることは波及要因であり、
  その分離 (新 schema 名) は本件の局所修正では扱わない。
- v3 の記録には 13 key の旧形と field が増えた後の形が混在しうるが、版値だけでは区別できない。
  本決定は双方を `legacy` として拒否し、この歴史的混在を遡って解消しない (規律 7: 記録は書き換えない)。

**却下した選択肢:**
- v5 へ上げる — 形の変更が無く、role consumer との不一致と v4 記録の対象外化を招く。
- consumer が producer 定数を参照し続け、文言だけ直す — 依存そのものが残る。
- v3 decoder / alias を足す — 本件の依頼範囲外であり、歴史 decoder は D1669 の読み手確認条件も満たしていない
  (D2064 決定 3 の alias 禁止は role payload の旧 throughput 名を対象とするもので、本件の直接の根拠ではない)。
- trial_registry / s8c_acceptance_receipt (run-start の field を読むが版を見ない) へ版 gate を足す —
  具体的な破れが示されておらず、仮想リスク向けの gate に当たる。
