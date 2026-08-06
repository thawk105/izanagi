# 実装プラン

以下の行番号は変更前の checkout を基準とする。

## 変更前の受理・拒否挙動

現状は次のとおり。

- `BatchReserved.cardinality`、event payload の `cardinality`、`BudgetPolicy.batch_cardinality_min` は、いずれも候補数ではなく member 行数を表す。
- `BatchCommitted` は commitment の重複を拒否するが、commitment preimage は候補 wire に query/replicate ordinal を加え、さらに salt 付きである。このため同一候補を複数行にした batch も合法である。
- `BatchSealed` は候補 wire、salted commitment、origin-wide replicate ordinal、outcome/evidence matrix を検証するが、distinct candidate 数は記録しない。
- `OriginSealed(aborted=False)` は `sealed_queries` による query floor、exact rejected class、`Kmax` を検査するだけで、候補数を検査しない。
- したがって、同一候補 `A,A` の2行 batch は `batch_cardinality_min=2` と floor=2 を満たし、ほかの条件が正しければ certifiable seal まで受理される。
- `OriginSealed(aborted=True)` は query floor と候補数を検査せず、counter と空 constraint class が正しければ受理される。

変更後も、authority の候補数下限が既定値1ならこの意味上の受理集合を維持する。意図して狭めるのは「authority が2以上を明示した場合の certifiable `OriginSealed`」だけとする。

## 推奨する field と gate

推奨名は D179 に合わせる。

```text
member_row_count
distinct_candidate_count
batch_member_row_count_min
batch_distinct_candidate_count_min
reserved_member_row_count
```

`BatchSealed` の入力 dataclass に count を追加して producer に申告させてはならない。入力は従来どおり `batch_id + members` とし、永続 event payload にだけ ledger 導出値を加える。

### P1 の評価

| 案 | 既存の発火路 | 恒真を避けられるか | I3 | 判断 |
|---|---|---|---|---|
| `BudgetPolicy.batch_distinct_candidate_count_min` を certifiable `OriginSealed` で検査 | 現在の floor/Kmax 枝に載る | 明示値2と `A,A` の負例で発火 | 既定値1なら維持 | **推奨** |
| `QueryFloorConstraint` ごとに候補数下限を追加 | 同じ枝に載る | 同じ負例で発火可能 | 既定値1なら維持 | 実装可能だが非推奨 |
| `BatchSealed` 時点で拒否 | 発火する | 発火可能 | 既定値1なら維持 | aborted 記録まで拒否し、「証拠として不受理」より広い |
| 記録だけして拒否しない | 発火しない | 恒真 | 表面上維持 | scope 3 と I5 を満たさず却下 |

`QueryFloorConstraint` は query 数の式であり、候補集合の性質とは直交する。また複数 constraint に同じ候補数下限を複製すると、実効値が暗黙に最大値になる。したがって `BudgetPolicy` の単一 field の方が明確である。

gate は origin-wide aggregate ではなく、次の per-batch 判定にする。

```python
any(
    batch.distinct_candidate_count
    < budget.batch_distinct_candidate_count_min
    for batch in state.sealed_batches.values()
)
```

origin-wide count だけを見る案は、`A,A` と `B,B` の2 batchで aggregate=2となり、候補2点を同一 batch で事前凍結していない記録を通すため却下する。候補数は tombstone を含む全 member から数える。凍結された候補集合の大きさであり、outcome 数ではない。

この gate は `OriginSealed(aborted=False)` のみで発火させる。明示値2でも `BatchSealed` と aborted seal は受理し、count=1を正直に記録できるようにする。

## `reflux_origin_ledger.py` の編集点

| 現在位置 | 対象 | 変更 |
|---|---|---|
| [ledger.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:98) | codec 定数 | `_MAX_BATCH_CARDINALITY` を `_MAX_BATCH_MEMBER_ROW_COUNT` へ改名する。constraint class の数学的 cardinality は別概念なので `_MAX_CLASS_CARDINALITY` はそのままでもよい。 |
| [ledger.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:212) | `QueryFloorConstraint` | 候補数 field は追加しない。query floor 専用型を維持する。 |
| [ledger.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:228) | `BudgetPolicy` | `batch_cardinality_min` を `batch_member_row_count_min` へ改名し、`batch_distinct_candidate_count_min: int` を追加する。候補数下限は最低1。 |
| [ledger.py:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:263) | `_BUDGET_KEYS`、`_budget_from_object`、`_budget_object` | JSON key を新名へ置換し、新候補数下限を厳密 parse/serialize する。旧 key との alias は作らない。 |
| [ledger.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:289) | `_floor_from_object` | 引数 `batch_min` を `member_row_min` 等へ改名するだけで式の意味は変えない。 |
| [ledger.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:504) | `BatchReserved` | dataclass field `cardinality` を `member_row_count` へ改名する。 |
| [ledger.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:559) | `OriginSnapshot` | `reserved_cardinality` を `reserved_member_row_count` へ改名し、origin 全体で既に開示済みの wire の distinct 数として `distinct_candidate_count` を追加する。 |
| [ledger.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:581) | `SealedBatch` | `member_row_count` と batch-local `distinct_candidate_count` を追加する。 |
| [ledger.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:752) | `_event_payload` | `batch-reserved` / `batch-committed` の payload key を `member_row_count` へ改名する。`batch-sealed` では正規化済み member object の `candidate_wire_b64` 集合から `distinct_candidate_count` を導出し、`member_row_count` とともに payload へ追加する。 |
| [ledger.py:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:833) | `_event_from_payload` | 新しい exact key 集合を要求する。sealed payload の両 count を member list から再計算し、個別 mismatch を拒否する。 |
| [ledger.py:1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1044) | `_SemanticState` | authority は既存 `replicate_counts: dict[bytes,int]` の key 集合と `sealed_batches` に保持する。重複する可変 scalar は持たず、`distinct_candidate_count` を `len(replicate_counts)` の read-only property としてよい。 |
| [ledger.py:1078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1078) | `_semantic_object` | `open_batch["cardinality"]` を `member_row_count` へ変更し、origin-wide `distinct_candidate_count` を追加する。 |
| [ledger.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1118) | `_preseal_semantic_sha` | `distinct_candidate_count` を projection から必ず `pop` する。seal 前の durable head から候補数を推測できないようにする。 |
| [ledger.py:1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1130) | partition 検査 | local、label、拒否理由を member row count 用語へ変更する。等式自体は不変。 |
| [ledger.py:1207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1207) | reserve/abandon/commit/prepare 枝 | `cardinality` local、open-state key、budget field、codec ceiling、forfeit 加算をすべて member row count 名へ変更する。 |
| [ledger.py:1350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1350) | `BatchSealed` 受理枝 | 全 member の canonical IR、replicate ordinal、salted commitment の照合が完了する [ledger.py:1439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1439) の直後に `len(normalized)` と `len({m.candidate_bytes for m in normalized})` を計算する。`len(event.members)`、`len(next_replicates)`、replicate ordinal の個数を候補数に使わない。 |
| [ledger.py:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1450) | `SealedBatch` 構築 | 上記2値を `SealedBatch` へ格納する。`replicate_counts` は従来どおり origin-wide candidate identity の authority とする。 |
| [ledger.py:1476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1476) | `OriginSealed` 枝 | query floor 検査直後、exact class/Kmax より前に per-batch candidate minimum を検査する。理由は例として `sealed batch distinct candidate count is below minimum` に固定する。aborted 枝には入れない。 |
| [ledger.py:2042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2042) | `_feasibility_*` | event key 改名と sealed count field を worst-case frame に反映する。5-bit canonical wire を最大32種循環させ、candidate count の2桁上限も包絡する。 |
| [ledger.py:2110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2110) | `_affine_batch_bytes` | member count の十進桁 reserve を reserve/commit/seal の3 field 分へ増やし、candidate count の1→2桁分も1 byte/batch確保する。現行6 bytes/batch相当を10 bytes/batch相当へ変更する。 |
| [ledger.py:2152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2152) | `_check_budget_codec_feasibility` | 改名した member minimumを使う。head transaction 数は変わらないが、completed-batch frame 包絡線は新サイズを使う。 |
| [ledger.py:2871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2871) | `_prepared_payload_projection` | `batch-sealed` projection に新 count を入れない。予約/commit は通常 projection なので新しい `member_row_count` key が反映される。 |
| [ledger.py:3256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:3256) | `_read_origin_locked` | 新 snapshot field を `len(state.replicate_counts)` から設定し、予約 binding を新名で返す。 |

### 計算と保持の流れ

```text
BatchSealed members
  ├─ _event_payload: ledger導出 countを event bytes/hash へ載せる
  ├─ _event_from_payload: countを再計算して改竄を拒否
  └─ _apply_event: 全 opening 検証後に再計算
       ├─ SealedBatch.member_row_count / distinct_candidate_count
       ├─ _SemanticState.sealed_batches
       ├─ replicate_counts keys → origin-wide count
       ├─ _semantic_object → state commitment
       └─ OriginSealed gate
```

`_event_payload` は reducer より先に event frame を組み立てるため、親 brief の「受理枝で計算」だけでは event payload に載せられない。codec 段と、全 opening 検証後の semantic 段で同じ導出を行い、replay 時に一致を検査する必要がある。

## commitment・hash・preseal への影響

| 面 | 変更 | 境界固定 |
|---|---|---|
| State commitment | **変わる。** `_semantic_object` に count=0を含めるため genesis 以後の semantic SHA が変わり、予約中は open key 改名も効く。manifest変更による origin ID/authority hashも連鎖する。 | V01/V13/V16 の独立 semantic preimage、snapshot commitment の再計算。 |
| Event hash | **変わる。** reserve/commit の key 改名と sealed の2 field追加が直接効き、previous hashを通じて後続 event 全体へ連鎖する。 | 独立 canonical frame/hash golden を更新する。 |
| Batch-seal prepared payload projection | 候補数追加によっては**変えない**。countを投影しない。 | single-candidate と distinct-candidate の完成状態で `_preseal_semantic_sha` が同じになる負例を置く。 |
| Reserve/commit projection | **変わる。** payload keyが `member_row_count` になる。 | exact request/binding の独立再計算を更新する。 |

固定 literal では、V01 の event SHA は論理値としてちょうど2件が変更対象になる。

- batch-sealed の `89cd…`：新しい sealed count field により変更。
- batch-reserved の `1839…`：`cardinality` 改名により変更。

各 SHA は frame、`replace`、expected digest の3箇所に重複しているため、テキスト上は6個の64-hex literalを更新する。standalone abandoned hash `3d6b…` と head hash `1a76…` は payloadを変えないため据え置ける。

## P2 改名の実測波及

静的 `rg` の結果は以下。

- production file：単独語 `cardinality` 52件、`batch_cardinality_min` 7件、`reserved_cardinality` 5件、`_MAX_BATCH_CARDINALITY` 9件。
- test file：単独語 `cardinality` 43件、`batch_cardinality_min` 3件、`reserved_cardinality` 6件、`_MAX_BATCH_CARDINALITY` 9件。
- event codec の `"cardinality"` key は production の6 key site、テストの独立 payload/goldenで5 site。
- rejection は5 call site・4 unique literal：
  - `candidate cardinality mismatch`
  - `open batch cardinality mismatch`
  - `batch cardinality exceeds codec feasibility`（2箇所）
  - `reservation cardinality is below batch minimum`
- 現名称を含む既存 test function は15本：V01、V03、V04、V06、V07、V08、V09、V13、V16-salt、V21、V24、V25、V26、V27、V33。
- `docs/` の単独語 `cardinality` は33件。そのうち ledger の経緯を記録する canonical history は decisions 13件＋worklog 1件。既存 D/worklog は歴史記録なので置換せず、新 D で新語彙を確定する。残りは他用途または archive である。

policy JSON は次の置換になる。

```json
{
  "batch_member_row_count_min": 2,
  "batch_distinct_candidate_count_min": 1
}
```

この改名と新 field により canonical manifest は約44 bytes/entry伸び、fixture origin IDも変わる。production authority は entry 0件なので、`reflux_origin_authority_v2.json` の bytesは変更しない。

旧 payload keyを互換 aliasとして残す案は、用語の二重性を残し、canonical serializerで一意化できないため却下する。旧 keyは exact-key検査で拒否し、新 keyだけを受理する。これは scope 2 が明示した raw codec 受理集合の置換であり、新 D と境界テストへ記録する。

## codec feasibility への影響

推奨 payload では completed batch の最大サイズ増分は次のとおり。

- reserve の key長増分：5 bytes
- commit の key長増分：5 bytes
- seal の `member_row_count=2248`：24 bytes
- seal の `distinct_candidate_count=32`：30 bytes
- 合計：最大64 bytes/completed batch

静的な byte 算術による更新見込みは以下。実装時は独立 helperで再計算して literal化する。

| 境界 | 現在 | 更新見込み |
|---|---:|---:|
| V21 sealed frame、2248行 | 1,048,246 | **1,048,300** |
| V21 sealed frame、2249行 | 1,048,712 | **1,048,766** |
| V24 exact batch bytes、10行 | 11,957 | **12,019** |
| V24 exact batch bytes、100行 | 93,769 | **93,832** |
| V24 exact batch bytes、1000行 | 911,871 | **911,935** |
| V24 conservative、10行 | 11,961 | **12,025** |
| V24 conservative、100行 | 93,771 | **93,835** |
| V24 conservative、1000行 | 911,871 | **911,935** |

2248行は依然1 MiB以内、2249行は依然超過なので、member row ceiling 2248自体は変えない。

origin-total は33 batchの場合に `33 × 64 = 2,112` bytes増える。現在の `qmax=73,721` は新包絡線では超過する見込みで、独立境界は次へ移る。

- 正例：`imax=33, qmax=73,718, kmax=4`、約 **67,108,224 bytes**
- 負例：`imax=33, qmax=73,719, kmax=4`、約 **67,109,133 bytes**

shared runtime-head は event payloadを保持せず transaction 数も変わらないため、V23 の `67,103,806 / 67,111,042` は変更しない。

## `test_reflux_origin_ledger.py` の編集点

| 現在位置 | 変更 |
|---|---|
| [test.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:60) | `_manifest_object` の `batch_min` を member 名へ改め、candidate minimum既定値1を追加する。 |
| [test.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:193) | independent batch frame に新 key/countを追加し、最大32種の5-bit wireを使用する。 |
| [test.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:264) | origin-total独立包絡線の decimal reserve を6から10 bytes/batchへ更新する。 |
| [test.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:517) | `_reservation_event` の引数と `BatchReserved` attributeを `member_row_count`へ変更する。 |
| [test.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:583) | V01 の manifest bytes、sealed/reserved frame、2 event SHAを更新する。abandon/head goldenは維持する。 |
| [test.py:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:844) | V03 で改名後のpolicy fieldとcandidate minimumの双方がorigin identityへ効くことを固定する。 |
| [test.py:911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:911) | subprocess fixture の `BatchReserved` attributeを新名へ変更する。 |
| [test.py:1239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1239) | V06 の `dataclasses.replace` を新 field名へ更新する。 |
| [test.py:1323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1323) | V07/V08 の名称、keyword、拒否理由を member row表現へ更新する。 |
| [test.py:1383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1383) | crash subprocess と V09 snapshot bindingを新名へ更新する。 |
| [test.py:1787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1787) | V13 の独立 semantic objectへ `distinct_candidate_count: 0` を加え、open keyを改名する。 |
| [test.py:2020](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2020) | V15 で新 policy/event keyの round-trip、旧 key拒否、sealed countの片方ずつの mismatch拒否を固定する。 |
| [test.py:2345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2345) | V16 の独立 committed semantic objectへ count=0と新 open keyを反映する。prepared seal projectionにはcountを足さない。 |
| [test.py:2579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2579) | V17 の同一候補 replicate 正例を、公開 countの中心境界へ拡張する。 |
| [test.py:2960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:2960) | V20 で preseal projectionに候補数が無いこと、distinct/repeated候補状態のpreseal SHAが同じことを固定する。 |
| [test.py:3032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:3032) | V21 のmax/max+1 frame literalを更新する。ceiling=2248は維持する。 |
| [test.py:3132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:3132) | V24 のexact/conservative/origin-total literalと qmax境界を更新する。 |
| [test.py:3165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:3165) | V25 の名称、helper引数、拒否理由をmember row countへ更新する。 |
| [test.py:3212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:3212) | V26/V27 のsnapshot binding名を更新する。 |
| [test.py:3441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:3441) | `_recovery_script`、V29、V33を `reserved_member_row_count`へ更新する。 |
| [test.py:3810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:3810) | `_run` より前へ新しいD96境界テスト群を追加する。 |

## D96 の正負境界テスト

最低限、次を同一 commit に置く。

1. **I3 default 正例**

   `batch_distinct_candidate_count_min=1`、members=`A,A`、member rows=2、distinct=1、sealed queries=2で、`BatchSealed` と certifiable `OriginSealed` の双方を受理する。

2. **I5 の必須負例**

   同じ `A,A` を candidate minimum=2のauthorityで実行する。`BatchSealed` は受理し、event payload、`SealedBatch`、`OriginSnapshot` が distinct=1を返すが、certifiable `OriginSealed` は候補数理由で拒否する。

   これは候補数を `len(members)==2` で埋める実装なら誤って緑になるため、その変異を確実に赤くする。

3. **candidate minimum=2 の正例**

   `A,B` の2行 batchで distinct=2を記録し、同じfloor/classのcertifiable sealを受理する。

4. **origin aggregate 誤用の負例**

   `A,A` と `B,B` の2 batchを同一originへsealする。origin-wide distinctは2だが各batchは1なので、candidate minimum=2のcertifiable sealを拒否する。

5. **aborted 分離の正例**

   candidate minimum=2、`A,A` の記録でも `OriginSealed(aborted=True)` は受理する。gateがcertifiable証拠だけを狭めることを固定する。

6. **codec導出の正負対**

   正しい payload `{member_row_count:2, distinct_candidate_count:1}` はround-tripする。各countを単独で2→1または1→2に変えたpayload、旧 `cardinality` key、count欠落をそれぞれ拒否する。

7. **公開時機の正負対**

   seal前のsnapshot/prepared headには今回の候補数が現れず、committed seal後だけevent、snapshot、`read_sealed_batch`から数が見えることを固定する。新しい面にcandidate bytesやsaltを増設しない。

8. **codec max/max+1**

   2248/2249 member frame、更新後origin-totalの73,718/73,719を正負対で固定する。V23 shared-head境界は不変であることも残す。

## 文書と同一変更単位

[D96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/decisions.md:4269) に従い、実装・境界テスト・新 D を同じ commit に含める。

canonical `docs/decisions.md` / `docs/worklog.md` は直接編集せず、次の spool fragmentを作る。

- `docs/spool/decisions/2026-08-06-dev-wave-t244-p3-u4-candidate-count-1.md`
- `docs/spool/worklog/2026-08-06-dev-wave-t244-p3-u4-candidate-count-1.md`

新 D には少なくとも以下を記録する。

- member row countとdistinct candidate countの定義と名前
- countはledger導出でありproducer申告ではないこと
- `BudgetPolicy` を選び `QueryFloorConstraint` を却下した理由
- default=1とexplicit=2の受理集合差
- per-batch gateでありorigin aggregateではないこと
- preseal projectionからcountを除くこと
- raw payload key、event/state hash、codec envelopeの変更
- D189と同じ理由でschema ID/domain/runtime pathを上げないこと
- P4/P3、物理query証明、production provisioningを名乗らないこと

既存の D166、D179、D189 は歴史的記録として書き換えない。production authority fileも一切変更しない。

## 規模と検証

概算は次のとおり。

- production：90〜120行を編集、純増35〜55行
- tests：180〜240行を編集、純増100〜150行
- spool docs：40〜60行
- 合計：およそ310〜420 touched lines、純増150〜220行

編集面とgoldenが密結合しているため、親 briefどおり1つのCodex実装子で収まる。並列分割はmerge時にevent shapeと独立goldenがずれる危険の方が大きい。

本起草は `pegasus02` のread-only環境で行い、pytestは実行していない。したがってテストを緑とは報告しない。実装時は計算ノードdispatch経由の対象テストに加え、`check_codex_agents.py`、`check_docs.py`、commit後のprovenance監査を行う。

## 総括

1. 推奨プランの3行要約  
   `cardinality` を一貫して `member_row_count` 系へ改名し、sealed event/batch/snapshotへledger導出の `distinct_candidate_count` を載せる。  
   候補数下限は `BudgetPolicy.batch_distinct_candidate_count_min` とし、既定1、明示2以上だけをcertifiable `OriginSealed`でper-batch検査する。  
   countはpreseal projectionから除外し、event/state hashとcodec包絡線の変更を独立goldenとD96境界テストで固定する。

2. 親 brief の誤りの有無  
   M1〜M7への事実上の反証はない。ただし provisional P1 の `QueryFloorConstraint` 案は実装可能ではあるものの、query式へ直交する候補集合条件を混在させるため最善ではない。またevent payloadへ載せるには、semantic受理枝だけでなく先行するcodec段でもledger導出が必要である。

3. ユーザー裁定が要る択一  
   **(A) `BudgetPolicy` のper-batch候補数下限（推奨）**か、**(B) 親 provisionalどおり各`QueryFloorConstraint`へ下限を持たせるか**。P2の改名はscope 2を維持する限り択一ではない。