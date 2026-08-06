---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t244-p3-u4-candidate-count
seq: 1
---

## {{D:u4-member-rows-vs-candidates}}. origin ledger の member 行数と候補数を別 field へ分ける — 実行候補の相異数だけを下限 gate に掛け、tombstone 行で下限を満たせないようにする

**決定:** origin ledger の記録形を次の 3 count へ分ける。いずれも ledger が導出し、
producer の申告 field を `BatchSealed` の入力へ足さない。

- `member_row_count` — batch の member 行数。旧 `cardinality` の意味をそのまま引き継ぐ。
- `distinct_candidate_count` — 全 member (tombstone 含む) の候補平文の相異数。
  凍結された候補集合の大きさであり、記録専用で gate には使わない。
- `sealed_distinct_candidate_count` — `tombstoned` でない member の相異数。実行候補の相異数。

`BudgetPolicy` へ `batch_distinct_candidate_count_min` (最小 1、既定 1) を足し、
certifiable な `OriginSealed` の受理で **sealed batch ごとに** `sealed_distinct_candidate_count` が
下限以上であることを検査する。aborted seal には掛けない。

- **下限 gate は実行候補の側に掛ける。** tombstone 行は未実行行である (D166 決定 5)。
  含めて gate すると `A, A, B(tombstoned)` が下限 2 を満たし、**実行していない候補 1 点で**
  候補多様性を名乗れてしまう。これは本 D が閉じたい誤読そのものである。
- **実行候補が 0 の batch (全 member が tombstone) は gate の対象外とする。**
  対象にすると既定の下限 1 でも従来受理されていた origin を拒否し、受理集合が
  authority の指示なしに狭まる。全 tombstone batch は `sealed_queries` に寄与しないため
  query floor を満たせず、gate の抜け道にはならない。
- **`batch_distinct_candidate_count_min <= batch_member_row_count_min` を parse 時に検査する。**
  batch の相異候補数は member 行数を超えられないので、超える policy は自己矛盾であり、
  受理すると certifiable terminal へ到達できない authority を作れる。
  codec feasibility の実効行数下限も `max(member_row_min, candidate_min)` として明示する。
- **`OriginSnapshot` の origin 全体の count は `origin_distinct_candidate_count` /
  `origin_sealed_distinct_candidate_count` と scope を名前へ焼く。** `SealedBatch` の
  batch-local count と同名にすると、同じ識別子が 2 つの意味を持つ (D75)。
- **候補数として参照してよいのは `SealedBatch` の batch-local count と authority の下限だけである。**
  `member_row_count` / `sealed_member_row_count` / `sealed_queries` / `queries_used` /
  `len(SealedBatch.members)` はいずれも行数であり、候補数として読んではならない。
- **旧 `cardinality` key は exact-key 検査で拒否し、alias を作らない。** alias を残すと
  同じ試行状態を 2 つの event hash で表せる。
- **count は codec 段と semantic 受理枝の双方で導出し、decode 時に再計算して照合する。**
  片側だけで導出すると、event payload の count を書き換えた stream を受理してしまう。
- **preseal projection から 3 つの origin 集計 count を除く。** seal 前の durable head から
  候補数を推測できないようにする。

**schema ID・domain・runtime path の版は上げない。** 再解釈される既存 stream が存在しない
(追跡された runtime store は 0 件、production 初期化は明示禁止、fixture store は毎回新規)。
D189 が同じ前提で同じ判断をしている。版を上げると authority 側だけが旧版に残り、
同じ bytes の受理集合が版境界を跨いで分裂する。

**既定では受理集合を変えない。** 下限 1 のままなら、単一候補 × R replicate の batch は
従来どおり certifiable seal まで受理される。狭まるのは authority が 2 以上を明示した場合の
certifiable `OriginSealed` だけである。

**予算 codec の包絡線がさらに狭まる。** 1 batch あたりの frame が count 3 つ分の十進桁を持つため、
origin 上限 bytes の見積りが増える。境界テストへ literal で固定した。**予算値を決める裁定は、
この新しい包絡線を前提にする必要がある。** 本番 authority は entry 0 件のままで、
予算 feasibility 自体が走らないため影響を受けない。

**前 wave の fixture liveness probe を新 API へ追随させた。** この probe は
`output/insights/` 配下にあるが、追跡されたテストが subprocess で実行しており、
歴史記録として凍結されていない。追随させないと受入全走が赤くなる。

**この決定が保証しないこと。**

- **候補が実際に別物であること**は保証しない。相異は候補平文の bytes 相異であり、
  意味等価な別 bytes を 2 点と数える。
- **物理 provider query 数**は保証しない。D166 決定 5 の限定をそのまま継承する。
- **P4 / 軸 (iii) の充足**は保証しない。ledger 外に formal consumer が存在しないため、
  本 D が閉じるのは certifiable `OriginSealed` の受理までである。

**却下した選択肢:**

- **count を 1 つにして tombstone を含める** — 未実行候補で下限を満たせる。
- **count を 1 つにして tombstone を除く** — 凍結された候補集合の大きさが記録から失われる。
- **`QueryFloorConstraint` へ候補数下限を持たせる** — query 数の式に直交する条件を混ぜることになり、
  複数 constraint に同じ下限を書いたときの実効値が暗黙に最大値になる。
- **候補数を producer の申告 field として `BatchSealed` の入力へ足す** — 自己申告を信じる恒真な
  記録になる。ledger は seal 時に候補平文を持つので導出できる。
- **候補数下限に IR 候補空間の大きさ (32) の上限を課す** — 候補空間の大きさは IR emitter の
  preimage 区間の内側にある private 定数であり、公開すると checkout 限定の変更検出 ID が動く。
  到達不能な下限の害は fail-closed 側 (certifiable seal に到達できないだけ) に留まるため、
  ledger から IR 候補空間サイズへの結合を新設しない。
- **旧 `cardinality` key を alias として受理する** — 受理集合が旧形へ広がり、同じ試行状態を
  複数の event hash で表せる。
- **記録だけして下限を強制しない** — 散文で「反 oracle 性は満たさない」と断るのと同じで、
  機械的な誤読を防げない。
