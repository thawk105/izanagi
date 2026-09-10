# 段 4 裁定 — [T-2107] 着手前実測 + [T-1851] 実装単位 B1

親裁定。base = worktree HEAD `6ff06800de0e2a0a8ac261d2e20320e68db8ebb3`。
材料 = 段 2 plan、段 3 レンズ A (所見 A-1〜A-10)・レンズ B (所見 B-1〜B-17)、親の独立実測。
裁定 inbox の再走査: 着手後に local main が `8a2ccac7f` へ進み D1488〜D1492 が増えたが、
いずれも本件と無関係で、変更 file も B1 の編集面と重ならない。承認済み裁定の前提は覆っていない。

## 結論 1 — [T-2107] の分岐は「機械導出できる」。ユーザーへ返す値は無い

**D1380 の分岐は (i) 機械導出できる = AI が閉じる、で確定する。止めてユーザーへ返す必要はない。**

決め手はレンズ A の A-5 で、親も plan も見落としていた。D1380 の対象は逐語で
**「計測の起動層が『出力前に成否を分類する方針』を名乗るための production 定数」**である。
現物にはその面がちょうど 1 つ実在する。

- `orchestrator/campaign/s8b_floor_attempt_launcher.py:105-110` の `ClassificationAuthority` は
  docstring で自らを "Pinned identity for the launcher's **pre-output** classification policy" と
  名乗る。起動層 (launcher) の出力前 (pre-output) 方針であり、D1380 の語と一致する。
- その方針を実行する純関数は同 file `:378-385` の `_pre_observation_failure_reason` で、
  結果は `POST_PROBE_COMPETING_REASON` / `MEASUREMENT_LAUNCH_FAILURE_REASON` / `None` の
  **ちょうど 3 つ**。自由選択は無い。
- したがって policy document の値は、この 2 つの reason 定数、probe の意味、precedence、
  authority id と schema version だけから機械導出できる。**人間が新しく決める値はゼロ。**
- 既存の同型権威 `s8b_scheduler_accounting.authority_policy_document()` (`:65-102`) と
  同じ形 (module 定数を canonical document へ射影し bytes の digest を取る) がそのまま使える。

### 親と plan の読みの訂正

- **親 (P1-a) は結論だけ当たっていたが、面を取り違えていた。** 親は campaign の最終
  `excluded_reason` ラダー (`s8b_floor_campaign.py:6147-6162`) を分類面だと読んだ。これは
  **出力後**の面であり、D1380 の「出力前」ではない。
- **親 (P1-b) は refuted。** `session_cv_max` は launcher の出力前方針の面に**入らない**。
  埋めるか否かという問い自体が、面の取り違えから生まれていた。
- **plan の (i) も面を混ぜていた** (A-5)。plan は campaign の 4 理由すべてを一つの authority に
  入れる前提で「閾値 `"0.10"` と `reps` も policy へ入れる」としたが、これは D1380 の対象では
  ない別の権威になる。

### 記録する条件と、単位 C への要件

- **もし将来 campaign の 4 理由すべてを名乗る権威を作るなら、答えは (iii) 条件付きになる。**
  レンズ A の A-10 が数値で示した — reps 5 の `[90,95,100,105,110]` は閾値 `0.10` で valid、
  `0.05` で performance anomaly になる。4 理由を名乗るなら閾値の収録は必須であり、さらに
  導出主体を campaign から launcher へ移す作業 (単位 C) が要る。**本 wave はその権威を作らない。**
- **単位 C への要件 (B-4、real、採用)**: policy document を手で組み立てるだけでは、
  ラダーだけを変えたときに権威 digest が旧値のまま残り「旧 policy を名乗って新規則で分類する」
  状態を作れる。分類の実行と canonical bytes を**同一の宣言 object から生成する**こと。
  これは単位 C の設計要件であり、D1380 の分岐の答えを変えない (AI が閉じられる作業のまま)。

## 結論 2 — B1 の scope を狭める。adapter は単位 A へ戻す

**親 brief の (P1-c) は refuted (A-4)。** 前 wave の終端裁定は逐語で
`B1 (claim/marker capability) → A (core/profile/adapter)` と書いており、**adapter は単位 A の所有**である。
親は P1-c で adapter を B1 へ引き込んだが、これは承認済みの分割裁定を親が覆す行為であり、
DW-S04 が禁じる。**戻す。**

A-4 が示した実質的な理由も成立する。adapter を B1 へ入れても production caller は生えない —
現 campaign は `_wrap_admission_aware_measure()` から直接 ticket を consume し
(`s8b_floor_campaign.py:5795`)、attempt registry launcher を呼ばない (A-7 で実測)。
つまり「adapter を含めれば恒真 API ではなくなる」という P1-c の理由は偽だった。

### 狭めた B1 の編集面 — 2 file

| path | 内容 |
|---|---|
| `orchestrator/campaign/s8b_holdout_admission.py` | claim digest の read-only 射影、`FloorAttemptConsumptionMarker`、`validate_floor_attempt_consumption_marker` |
| `orchestrator/tests/test_s8b_holdout_admission.py` | 正例・負例 |

- **`s8b_attempt_registry.py` は触らない** (単位 A)。
- **`s8b_floor_evidence_fixture.py` も触らない。** 親が実測したところ
  `test_s8b_holdout_admission.py` は既に `consume_attempt_ticket` を 39 箇所で使い、
  reservation → finalize → consume の完全な流れを持つ。新 fixture は不要である
  (これによりレンズ B の B-9 と、fixture の 10 consumer 波及が消える)。

### 狭めた帰結

- **意図的な赤はゼロになる。** レンズ B の B-2 / B-7、plan の「直接赤 14 + transitive 赤 7」は
  すべて adapter 差し替えに由来するので消える。受入全走は緑を要求できる。
- **規模が収まる。** レンズ B の B-12 が見積もった 550-850 LOC / 45-65 node は adapter と
  fixture を含む値。2 file へ狭めた B1 はその半分以下になる。
- **A-6 も消える。** adapter の書込み到達集合を変えないので、DW-O10 は本 wave では成立しない。

## 結論 3 — B1 の API 設計に課す 4 つの不変条件

B1 は API の**形**を決める段なので、後続の単位 A が正しく使わざるを得ない形にする。
呼び手が居ないことを理由に、守れない約束を返す API を作らない。

1. **(A-1、real、blocker、採用) 発行後の改竄を見逃す再利用可能 capability を作らない。**
   plan は capability を再利用可能にし、利用側では seal と identity の等値だけを検査する形を出した。
   これだと正しい marker で capability を得た後に marker を消す・key を足す・claim や主台帳を
   改竄してから使える。**capability は admission root lock の内側で発行と使用が閉じる形にするか、
   使用時に durable evidence を同じ lock 内で再検証する形にする。** どちらを採るかは plan v3 が
   file:line で決める。「発行時に検査したから使用時は要らない」は採らない。
2. **(A-2、real、blocker、採用) slot の 4 軸すべてへ束縛する。**
   registry の slot identity は `_SLOT_IDENTITY_KEYS` = freeze_holdout_key / configuration_id /
   **repetition** / **attempt_ordinal** の 4 軸 (`s8b_attempt_profile.py:272-277`)。
   一方、現行 `_consumption_identity()` は cell の等値と attempt_id の prefix しか見ない
   (`s8b_attempt_registry.py:139-147`)。capability の identity に後 2 軸を入れないと、
   同一 cell の別 slot へ移植できる。**4 軸を入れる。**
3. **(A-3、real、blocker、採用) capability は現行世代専用であると正直に書く。**
   `_cell_state()` (`s8b_holdout_admission.py:4151-4156`) は `_cell_states[id(admission)]` に
   登録された token しか受けない。inspector が作る legacy token は局所の `inspection_states` に
   置かれるだけで登録されない (`:6229`)。**したがって legacy token では capability を発行できない。**
   plan の「v1 と current を dispatch する」という記述は成立しない。B1 は
   **現行世代専用の capability** として実装し、legacy の扱いは単位 A の課題として明記する。
   親 brief の不変条件「legacy v1 validator を残し受理形を減らさない」は、adapter を scope 外に
   戻したことで本 wave では**そもそも受理集合を変えない**形に落ちる。
4. **(B-6、real、採用) 引数の出所表を plan v3 に要求する。**
   capability が持つ identity ごとに「どの権威 field から取るか」を表にする。
   registry の classification claim digest と admission の measurement-generation claim digest と
   legacy の cell-effect digest は別 domain であり、取り違えると全 capability が拒否されるか、
   逆に世代を跨いだ capability が通る。

## 所見の real / refuted と採否

### レンズ A (コードを実測している。親が全件検算した)

| # | 判定 | 採否 |
|---|---|---|
| A-1 発行後改竄の TOCTOU | **real / blocker** | 採用。不変条件 1 |
| A-2 slot 4 軸へ未束縛 | **real / blocker** | 採用。不変条件 2。`_SLOT_IDENTITY_KEYS` と `_consumption_identity` を親が検算 |
| A-3 legacy 受理形は維持されない | **real / blocker** | 採用。不変条件 3。`_cell_state` の登録要求を親が検算 |
| A-4 P1-c は境界を越え caller も生えない | **real / blocker** | 採用。結論 2。前 wave 終端裁定の逐語と一致 |
| A-5 二つの分類面を混ぜている | **real / blocker** | 採用。結論 1。`ClassificationAuthority` の docstring と `_pre_observation_failure_reason` の 3 分岐を親が検算 |
| A-6 書込み到達集合は変わる | **real** | 採用するが、adapter を scope 外に戻したので本 wave では発火しない |
| A-7 DW-G05 の現在形は再現しない | **real** | 採用。brief の DW-G05 を「単位 C で launcher を接続した後に発火する将来の欠陥」へ訂正する |
| A-8 親の hit 数と field 参照が誤り | **real / nit** | 採用。訂正は下記 |
| A-9 field 追加から bytes への流出 | 反証材料なし | 記録 |
| A-10 深い再導出と閾値 pin | 反証材料なし | 記録。閾値の数値例は結論 1 の条件として引く |

### レンズ B (射影 4 資料だけを読み、全所見を自ら `[推測]` と宣言している)

| # | 判定 | 採否 |
|---|---|---|
| B-1 pre-probe failure と必須 marker が両立しない | **refuted** | 不採用。`begin_attempt_observation` と `begin_classified_failure_observation` は**どちらも** `_begin_attempt_observation` (`s8b_attempt_registry.py:1521`) へ合流し、`:1539` が `_assert_consumed_marker` を無条件に呼ぶ。marker 必須は main に既にある。B1 は要求を新設しない |
| B-2 通常 launcher が即座に壊れる | **real** | 結論 2 で消滅。adapter を触らない |
| B-3 legacy 受理形を削っている | **real** | A-3 として採用。ただし B-3 が挙げた「claim も主台帳も無い legacy marker」は `test_s8b_attempt_registry.py:174-194` の `_write_marker` が合成で置くテスト専用状態であり、production の `consume_attempt_ticket` (`s8b_holdout_admission.py:4228-4271`) では作れない |
| B-4 機械導出が未証明 | **real** | 採用。単位 C の要件として結論 1 に記録。D1380 の答えは変えない |
| B-5 crash recovery の caller 不在 | **real** | scope 外 (単位 C)。裁定パッケージへ |
| B-6 引数 provenance が未定義 | **real** | 採用。不変条件 4 |
| B-7 launcher 分の赤が不足 | **refuted** | 不採用。launcher test の 6 呼出し (`test_s8b_floor_attempt_launcher.py:317,393,436,486,626,664`) は全て `registry=fake_registry` を注入し、1 つは `registry=pytest.fail`。実 adapter を通さない |
| B-8 dataclass 調査の軸が不足 | **real (指摘は正当)** | 軸を広げて親が再検査した。`replace(` / `pickle` / `hash(` / set・dict の要素としての token 利用は 0 件。`orchestrator/campaign/` 全体に `pickle` の hit 0。`s8b_floor_campaign.py:5784,6278` の `set(admissions)` は cell_id の集合。**結論は変わらない** |
| B-9 current 正例は既存 fixture で書けない | **real だが本 wave では消滅** | `test_s8b_holdout_admission.py` が既に完全な流れを 39 箇所持つ。新 fixture 不要 |
| B-10 node 数が parametrize 未計上 | **real** | 採用。狭めた scope で再見積もりする |
| B-11 M4/M6/M7/M9 の単一理由性 | **real** | 採用。下記の変異事前登録で再照準した |
| B-12 規模が収まらない | **real** | 結論 2 の scope 縮小で解消 |
| B-13 「pin 閉包 0 件」は一般化できない | **real** | 採用。「指定語 (schema 定数名・directory literal) による**可視 pin** は 0 件」へ限定して記録する |
| B-14 DW-O10 の限定 | **nit** | 採用。durable producer bytes に限定して記録 |
| B-15 T-2107 は B1 を前提にしない | **nit** | 反証材料なしを確認 |
| B-16 constructor 2 箇所 | **nit** | 親が検算済み。2 箇所、いずれも keyword、位置引数 0 件 |
| B-17 残る 5 層 | **real** | 採用。裁定パッケージへ |

## 親 brief の訂正

| brief の記述 | 訂正 |
|---|---|
| (P1-b) 閾値を埋めると凍結 policy に束縛される | **refuted。** 閾値は D1380 の対象面 (launcher 出力前方針) に入らない |
| (P1-c) adapter の consumer 差し替えを B1 に含める | **refuted (A-4)。** adapter は単位 A。B1 から外す |
| 「repo 全体で 22 hit、全て同 file」 | **誤り (A-8)。** production file の hit は 26 行。加えて `:1727` の `state.token.protocol_sha256` は `_ReservationState.token: FloorHoldoutReservation` (`:369-371`) であって `CellHoldoutAdmission` ではない。親の「唯一の field 参照」という記述は成立しない |
| 「pin 閉包 0 件」 | **限定 (B-13)。** 「指定語による可視 pin は 0 件」 |
| DW-G05 の現在形 | **訂正 (A-7)。** 現 campaign は adapter を通らないので、放置しても現時点の certified proof は誤束縛されない。単位 C で launcher を接続した時点で発火する将来の欠陥である |
| 不変条件「受理形を減らさない」 | adapter を scope 外に戻したので、**本 wave は受理集合を一切変えない** |
| DW-O10 不成立 | 維持。ただし「durable producer bytes に限る」と限定して記録する (B-14) |

## 変異事前登録 (DW-M01)

狭めた B1 (2 file) に対して事前登録する。B-11 の指摘に従い、単一理由性が成立しない候補は
再照準した。各変異は「同じ入力を拒否する層が前後に無い」ことを実装後に確認してから本走する。

| ID | 変異位置 | 期待 KILLED node の向き |
|---|---|---|
| M1 | `CellHoldoutAdmission` の新 field を `str \| None` から落として構築側 2 箇所のうち inspector 側を `""` にする | inspector 射影の負例が落ちる |
| M2 | capability 発行時の `_cell_state()` 呼出しを削り、渡された token をそのまま信じる | 未発行 token の負例が落ちる |
| M3 | capability の identity から `repetition` を落とす | slot 移植の負例 (repetition 違い) だけが落ちる |
| M4 | capability の identity から `attempt_ordinal` を落とす | slot 移植の負例 (ordinal 違い) だけが落ちる |
| M5 | 使用時の durable 再検証を削る (不変条件 1 の実装点) | 発行後改竄の負例が落ちる |
| M6 | marker の exact key 集合検査を `>=` へ緩める | extra key の負例だけが落ちる |
| M7 | claim からの完全再導出をやめ marker の自己申告 field を権威にする | claim 改竄の負例が落ちる |
| M8 | 主台帳の「ちょうど 1 行」要求を「1 行以上」へ緩める | 重複行の負例が落ちる |
| M9 | `_measurement_generation_claim_identity()` の再導出呼出しを削る | generation ID 改竄の負例が落ちる |
| M10 | capability の exact type 検査を `isinstance` へ緩める | 偽造 subclass の負例が落ちる |

- **B-11 に従い分割した点**: plan の M7 (exact type と seal を一括) は M10 (type) と M2 (発行元) へ、
  plan の M9 (root と generation を一括) は M3 / M4 (軸ごと) へ割った。
- **受理集合を縮小しない wave なので、過剰拒否の正例を必ず 1 つ登録する** —
  正しい現行世代の token と正しい marker で capability が**返る**こと。

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

いずれも scope 外の real 所見であり、親は実装せず設計択一として返す。

1. **単位 C: 分類権限を宣言 object 駆動にするか** (B-4)。手で組み立てる policy document は、
   規則だけ変えたときに権威 digest が追随しない。分類の実行と canonical bytes を同一 source から
   生成する案を採るか、追随を別の機構で保証するか。
2. **単位 A: legacy token の capability 発行入口を作るか** (A-3)。現状 legacy token は
   `_cell_states` へ登録されないため capability を発行できない。legacy 受理を保存する
   admission 所有の再検証入口を設けるか、legacy 受理を前向きに廃止するか。後者は受理面の縮小なので
   親だけでは選べない。
3. **単位 C: pre-probe 除外の権限層** (B-5、前 wave の A2-4 の具体化)。marker 無しで
   正当に terminalize する経路が要る。
4. **単位 C: crash recovery が admission token と capability を再取得する層** (B-5)。
5. **残る層の全体像** (B-17): 上記に加え、単位 A の世代別 namespace、B2/D の全単射被覆・
   prefix proof・consumer verification。
