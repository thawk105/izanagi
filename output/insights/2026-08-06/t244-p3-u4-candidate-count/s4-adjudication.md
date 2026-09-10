# 段 4 裁定 — [T-244] P3 U-4 候補数 field 分離

段 2 プラン (`s2/plan.md`)、段 3 レンズ A (`s3/lensA.md`)、レンズ B (`s3/lensB.md`) を受けた親の裁定。
両レンズとも NO-GO。must-fix は A-1〜A-4 / B-1〜B-5 の 9 件 (うち 2 組は同一所見)。

**「実装しない」とはしない。** 所見はいずれも設計の欠落であって、scope 自体の否定ではない。
plan v2 として下記を確定し、段 5 へ進む。

## 所見の裁定

| # | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A-1 | real | **一部採用** | 下記 T2 |
| A-2 | real | **採用** | 下記 T3 |
| A-3 / B-1 | real (同一) | **一部採用** | 下記 T4 |
| A-4 / B-2 | real (同一、方向が逆) | **採用 (親が設計を決める)** | 下記 T1 |
| A-5 | 疑い | **採用 (明示 assertion で refute)** | 下記 T5 |
| B-3 | real | **不採用 (歴史記録として固定)** | 下記 T6 |
| B-4 | real | **採用** | 下記 T7 |
| B-5 | real | **採用** | 下記 T8 |
| A nit 2 件 / B nit 2 件 | — | 実装子が現物で確認 | 記録のみ |

## T1 — tombstone の扱い (両レンズが逆を指した論点。親が決める)

レンズ A は「tombstone を含めて数える」前提で境界テストを要求し、レンズ B は
「tombstone は D166 で未実行行だから、含めると未実行候補で下限を満たせる」と警告した。
**レンズ B の危険の方が U-4 の目的に直結する。** ただしレンズ A の「凍結された候補集合の大きさを
正直に記録する」も正しい。両立させる。

**裁定: count を 2 つ記録し、gate は非 tombstone の側に掛ける。**

- `distinct_candidate_count` = batch の**全 member** (tombstone 含む) の候補平文の相異数。
  凍結された候補集合の大きさ。記録専用で gate には使わない。
- `sealed_distinct_candidate_count` = **outcome が `tombstoned` でない member** の相異数。
  実際に実行された候補の相異数。**下限 gate はこちらに掛ける。**
- 語彙は既存 ledger と整合する — `sealed_queries` が既に「tombstone を除く member 行数」の意味で
  使われている。

**理由:** tombstone を含めて gate すると `A, A, B(tombstoned)` が下限 2 を満たし、
**実行されていない候補 1 点で反 oracle 性を名乗れる**。これは U-4 が閉じたい誤認そのものである。
一方 count を 1 つに減らして非 tombstone だけにすると、凍結候補集合の大きさが記録から失われる。

**境界テスト (必須):** `A(accepted), A(accepted), B(tombstoned)` で
`distinct_candidate_count == 2` かつ `sealed_distinct_candidate_count == 1` を固定し、
下限 2 の certifiable `OriginSealed` が**拒否される**ことを固定する。
下限 1 なら受理されることも対で固定する。

## T2 — A-1 (誤読経路が別 field に残る)

**採用する部分:**

- `OriginSnapshot` の origin 全体の count は **`origin_distinct_candidate_count`** と名前に scope を
  焼き込む。`SealedBatch` の batch-local count と同名にしない (同名識別子の二義化を禁じる `DW-O13` / D75)。
- 新 D に**参照規則**を書く: 候補数として参照してよいのは `SealedBatch` の batch-local count と
  authority の下限だけである。`member_row_count` / `sealed_queries` / `queries_used` /
  `len(SealedBatch.members)` を候補数として読んではならない。

**不採用にする部分 (scope 外、裁定パッケージへ返す):** `sealed_queries` →
`sealed_member_row_count` などの origin-level counter 群の改名。
理由: (a) 本 wave の scope 2 は `cardinality` 名の是正であり、`queries` 系 counter は含まない。
(b) D166 決定 5 と D189 が意味を明記済みで、`OriginSealed` / `OriginSnapshot` / `_SemanticState` に
docstring が既にある。(c) 改名すると `OriginSealed` payload が変わり event hash golden の
更新範囲が倍近くになる。real 所見として裁定パッケージに残す。

## T3 — A-2 (`any` の全 batch 検査をテストが束縛していない)

**採用。** 3 batch の負例を必須にする。`good(A,B) → bad(C,C) → good(B,D)` を同一 origin へ seal し、
下限 2 の certifiable `OriginSealed` が**中央 1 件だけを理由に**拒否されることを固定する。
これで `all` / first-only / last-only / 「適格 batch が 0 件のときだけ拒否」の 4 誤実装を一度に殺す。

## T4 — A-3 / B-1 (到達不能な candidate 下限を authority が受理する)

**採用する部分:**

- parse 時に **`batch_distinct_candidate_count_min <= batch_member_row_count_min`** を検査する。
  batch の相異候補数は member 行数を超えられないので、超える policy は自己矛盾である。
  B-1 の反例 (member 下限 2 / candidate 下限 3 / `qmax=2`) はこれで parse 時に拒否される。
- feasibility の実効行数下限を `max(member_row_min, candidate_min)` として明示する
  (上の検査により値は `member_row_min` に一致するが、式として意図を残す)。
- 境界テストは `candidate_min == member_row_min` の正例と `candidate_min == member_row_min + 1` の
  負例を対で置く。

**不採用にする部分 (裁定パッケージへ返す):** 「candidate 下限 <= 32 (IR 候補空間の大きさ)」の検査。
理由: 候補空間の大きさは `reflux_ir._WIRE_WIDTH` (private) であり、この定数は
`CHECKOUT_IR_EMITTER_PREIMAGE_BEGIN`〜`END` の**内側**にある
(`reflux_ir.py:34`〜`:142`)。公開定数を足すと P2 wave が production 定数として置いた
`CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID` が動き、`test_reflux_ir.py:319` の変更検出が発火する。
ledger → IR 候補空間サイズという新しい結合を作る費用が、到達不能性の害を上回る。
**害は fail-closed 側である** — 到達不能な下限を持つ authority は certifiable seal に到達できないだけで、
不正な受理は起きない。

## T5 — A-5 (origin-wide union の期待値)

**採用。** V17 (同一候補 A を 2 batch に跨って反復) を拡張し、
`snapshot.origin_distinct_candidate_count == 1`、各 `SealedBatch.distinct_candidate_count == 1`、
各 sealed event payload の count == 1 を**明示 assertion で**固定する。
これで「snapshot が batch-local count の総和を返す」誤実装が赤くなる。

## T6 — B-3 (liveness probe が旧 API を使う)

**不採用 (歴史記録として固定する)。** `output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` は
過去 wave の使い捨て probe であり、insights は逐語の歴史記録として書き換えない規律である。
現行 API では再実行できなくなる事実を新 D に 1 行で明記する。
`output/insights/**` は受入テストの対象外であり、緑を割らない。

## T7 — B-4 (名乗りが発火路の上限を超えている)

**採用。** 親 brief の「P4 証拠の受理」という表現を撤回し、
**「certifiable `OriginSealed` の受理 (= ledger terminal acceptance)」**まで弱める。
新 D・テスト名・docstring でも「P4 evidence」「anti-oracle」「候補 batch」を名乗らない。
名乗ってよいのは次まで。

> ledger の記録形における member 行数・凍結候補数・実行候補数の分離と、
> authority が下限を明示したときの certifiable `OriginSealed` 受理での per-batch 強制。

## T8 — B-5 (テスト編集 closure の不足)

**採用。** 対象 test function は 15 件でなく**少なくとも 16 件** (V14 が `_MAX_BATCH_CARDINALITY` を
参照)。加えて `test_reflux_origin_ledger.py:248` の独立 abandoned-frame helper が旧 `"cardinality"`
payload key を持ち、改名後は reserve frame を 5 bytes 過小評価する。実装子が機械走査で closure を
取り直し、取り残しゼロを報告すること。

## plan v2 (確定仕様)

段 2 プランを次の点で上書きする。それ以外は段 2 プランのとおり。

1. count は 3 つ: `member_row_count` / `distinct_candidate_count` (全 member) /
   `sealed_distinct_candidate_count` (非 tombstone)。gate は 3 つ目に掛ける (T1)。
2. `OriginSnapshot` の origin 全体の count は `origin_distinct_candidate_count` (T2)。
3. `BudgetPolicy` に `batch_distinct_candidate_count_min` (既定 1) を追加し、
   `<= batch_member_row_count_min` を parse 時に検査する (T4)。
4. gate は certifiable `OriginSealed` の per-batch 検査。aborted 枝には掛けない。
5. 名乗りは T7 の上限まで。
6. 境界テストは段 2 プランの 8 群に T1 / T3 / T4 / T5 の 4 群を足す。
7. `QueryFloorConstraint` は変更しない (親 provisional P1 を撤回し、段 2 の推奨を採る)。
8. count はいずれも ledger 導出とし、producer 申告 field を `BatchSealed` 入力へ足さない。
   codec 段 (`_event_payload`) と semantic 受理枝の両方で導出し、`_event_from_payload` で再計算照合する。
9. `_preseal_semantic_sha` から 3 count をすべて `pop` する。

## 変異事前登録 (`DW-M01`、B-057)

実装前に 13 件を登録する。各変異は単一理由であること (同じ入力を拒否する層が前後に無いこと) を
実装後に harness で確認し、mask されていた場合は `DW-M02` に従い再照準して erratum を残す。

| # | 変異位置 | 変異内容 | 期待して赤くなる検査 |
|---|---|---|---|
| M01 | seal 受理枝の count 導出 | `sealed_distinct_candidate_count` を `len(normalized)` (member 行数) で埋める | T1 負例 / A,A 下限 2 の拒否 |
| M02 | `OriginSealed` の gate | `any(...)` を `all(...)` にする | T3 の 3 batch 負例 |
| M03 | `OriginSealed` の gate | 最初の sealed batch だけ検査する | T3 の 3 batch 負例 |
| M04 | `OriginSealed` の gate | gate 対象を `sealed_distinct_candidate_count` から `distinct_candidate_count` へ変える | T1 の tombstone 負例 |
| M05 | `OriginSealed` の gate | aborted 枝でも gate を発火させる | T1/plan の aborted 正例 |
| M06 | `OriginSealed` の gate | `<` を `<=` にする (off-by-one) | `distinct == min` の正例 |
| M07 | `_event_from_payload` | count の再計算照合を落とす | 改竄 payload 拒否テスト |
| M08 | `_preseal_semantic_sha` | count を `pop` しない | preseal 等価性テスト |
| M09 | `_budget_from_object` | `candidate_min <= member_row_min` 検査を落とす | T4 の負例 |
| M10 | `_event_from_payload` の exact key | 旧 `cardinality` key を alias として受理する | 旧 key 拒否テスト |
| M11 | `_read_origin_locked` | `origin_distinct_candidate_count` を batch-local count の総和にする | T5 の V17 union テスト |
| M12 | `_affine_batch_bytes` | decimal reserve を旧値 (6 bytes/batch) へ戻す | V24 の境界 literal |
| M13 | `OriginSealed` の gate | 既定 (下限 1) でも `distinct == 1` を拒否する **(過剰拒否の検出)** | plan の I3 default 正例 |

M13 は受理集合を縮小する wave における「承認外の過剰拒否を検出する正例」である (`DW-M01`)。

## 実装単位

**1 単位** (Codex `role=author`、`reasoning=high`、`sandbox=workspace-write`)。
編集面は `orchestrator/campaign/reflux_origin_ledger.py` と
`orchestrator/tests/test_reflux_origin_ledger.py` の 2 file で、実装と golden が密結合しているため
並列分割しない (段 2 プランの判断を採用)。

## 裁定パッケージ候補 (本 wave では実装しない real 所見)

1. **origin-proofs sidecar と report v3 は wiring 待ちで実装不能** (親 M1)。
2. **`sealed_queries` 等の origin-level row counter の改名** (A-1 の不採用部分、T2)。
3. **candidate 下限の IR 空間上限 (<= 32) 検査** (A-3/B-1 の不採用部分、T4)。
4. **`output/insights` の使い捨て probe が現行 API で再実行不能になる** (B-3、T6)。
5. **予算 codec 包絡線がさらに狭まる** — U-10 の予算値裁定はこの新包絡線を前提にする必要がある。

---

## T6 の再裁定 (段 5 完了後、未見の新事実により撤回)

**撤回する。** T6 は「`output/insights/**` の probe は歴史記録なので書き換えない」と裁定したが、
これは裁定時点で親が見ていなかった次の 2 事実に反する。

1. `orchestrator/tests/test_t244_p3_liveness_probe.py` は **tracked なテスト**であり、
   subprocess で `output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` を実行して
   6 検査すべての PASS を assert する。probe が旧 API のままだと受入全走が赤くなる。
2. 前 wave (reservation FSM) の実装 commit `2dc107ce` が**この probe を実際に更新している**。
   probe は凍結された逐語ではなく、ledger の API 変更に追随させる対象として運用されている。

**新裁定:** probe を新 API へ最小限で追随させる。編集は段 6 の fix 子 (Codex `role=author`) が行い、
親は編集しない。probe の意味 (6 検査が何を確かめるか) は変えず、policy key と snapshot field 名の
追随だけに限る。新 D には「本 wave で probe を追随させた」と 1 行記録する。

裁定パッケージ候補 4 (「probe が再実行不能になる」) は**取り下げる** — 実際には追随させたため。
