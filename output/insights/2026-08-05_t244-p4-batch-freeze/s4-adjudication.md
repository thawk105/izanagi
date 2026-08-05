# 段 4 裁定 — [T-244] P4 batch freeze (W2/W3 適合 + P4 充足判定、2026-08-05)

親 = Claude (dev-wave manager)。対象 = `out/s2-plan.md` と敵対 2 レンズ (`out/s3-lensA.md` /
`out/s3-lensB.md`、いずれも **NO-GO**)。base main = `f009da3`。

## 裁定: 実装する (段 5 へ)。ただし Δ1〜Δ14 でプランを訂正する

両レンズが NO-GO を返したが、**所見はすべて本 wave の編集面内で閉じられる**か、
名乗りの訂正 + 起票で正直に扱える。先例 = (186) [T-244] P3 再設計 wave も段 3 の 2 レンズが
NO-GO 相当を返した後、段 4 で Δ1〜Δ15 を確定して実装へ進んでいる。NO-GO は停止指示ではなく
プラン v2 の入力である。

**実装しない裁定を採らなかった理由。** D153 が実装を差し戻した 3 根拠のうち、
(1) 実装先 (独立 leaf は誤り) と (2) member identity 未裁定は、W1/W2 のユーザー裁定と
(186) の第一級 batch FSM 実在により**両方とも解消済み**である。残る (3) `DW-G04` の発火 gate は、
本 wave が**新規の条件付き機構を作るのではなく、既に land 済みの prototype (D159、
production caller ゼロで land 済み) を採用済み裁定 W2〜W5 へ適合させる保守**であるため、
D153 当時とは適用が異なる。ただし発火 path が今も書けない事実は変わらないので、
名乗りは prototype に留める (下記)。

**名乗りの制限。** 本 wave が名乗るのは
**「D153 W1〜W5 の ledger 側契約に適合する P4 batch-freeze prototype」**までである。
「P4 実装完了」「P4 充足」は名乗らない。P4 は依然 FAIL、cap-lift は FAIL、
`MAX_APPROVED_GENERATIONS = 1` (D114) は不変。根拠は D159 決定 4 の U-G 会計と同型
(下記「P4 充足判定」)。

## 所見別裁定

| 所見 | real/refuted | 採否・処置 |
|---|---|---|
| A-1 (同一 wire・同一 evidence で floor 水増し) | **real** | **一部採用 = Δ10。** ledger は物理 query を観測しない。名乗りを訂正し境界をテストで固定する。evidence digest の origin 内 distinct 強制は**採らない** (false reject の risk が未実測で、裁定なき設計決定になる) → 起票 |
| A-2 / B-4 (evidence 束縛が digest claim に留まる) | **一部 refuted** | W3 の裁定文は「P3 旧設計の `result_ref_sha256` 相当の evidence digest へ束縛」であり、bare digest の commitment 束縛は**裁定どおり**。referent 解決を W3 の要件に読み込むのは裁定の拡大解釈。名乗り訂正 = Δ11、resolver 契約の設計は起票 |
| A-3 (head-prepared が実行済み prefix の oracle) | **real** | 採用 = Δ3。プランが counter を seal 前 state に入れたことで**新規に生じる漏洩**であり、実装で閉じる |
| A-4 (public replicate ordinal が重複構造を漏らす) | **real** | 採用 = Δ2。W2 は ordinal を identity に含める裁定であって平文公開は要求していない |
| A-5 / B-2 (W4 の固定長が未裁定のまま row 数へ弱化) | **real** | 採用 = Δ4。設計本文 §4③-5 の目的から terminal event 形の統一まで要求する。byte 長は明示的受容残余 |
| A-6 (codec 上限 golden が実装由来で自己参照) | **real** | 採用 = Δ6 |
| A-7 (`member_sequence_commitment` に kill node なし) | **real** | 採用 = Δ5 (削除)。恒真な保証を増やさない |
| A-8 / B-8 (brief の受理集合方向が逆) | **real** | 採用 = Δ12 (erratum-2)。親の誤りを訂正記録する |
| A-9 / B-9 (brief の「任意 outcome 素通り」は誤り) | **real** | 採用 = Δ13 (erratum-1)。親が一次確認済み |
| B-1 (replicate が batch-local へ縮退) | **real** | 採用 = Δ1。W2 の目的節 (予算下限式は origin-total) と設計本文 §4③ の origin 単位予算から **origin-wide** と確定する。新たな設計決定ではなく裁定文の正しい読解である |
| B-3 (並行 producer wave と API 契約が衝突) | **real、scope 外** | 本 wave では解決しない。interface delta を handoff へ書いて引き渡し、landing closure の再編可否はユーザー裁定へ返す。向こうの branch は commit ゼロ・段 2 プランも NO-GO で設計流動中であることを実測済み |
| B-5 (v1 authority の意味を無言で変更) | **real** | 採用 = Δ9。schema ID を v2 へ bump し registry file も v2 へ改名する |
| B-6 (per-batch frame 上限と origin-total 予算の混同) | **real** | 採用 = Δ8 |
| B-7 (salt 無制限で「最長 frame」が定義不能) | **real** | 採用 = Δ7 |

refuted は A-2/B-4 の一部 (W3 要件の拡大解釈) のみ。他はすべて real。

## Δ (プラン v2 の訂正指示)

- **Δ1** `replicate_ordinal` は **origin-wide** の「同一 canonical wire がその origin でそれ以前に
  出現した回数」とする。batch-local リセットは却下。
- **Δ2** `replicate_ordinal` は **commitment preimage のみ**に置き、`batch-committed` payload には
  出さない。`query_ordinal` は `queries_used` から導出可能で新情報を漏らさないので payload に置く。
  replicate の canonicality は terminal opening 時に検査する。
- **Δ3** 実行依存 counter (`sealed_queries` / `tombstoned_queries`) を **seal 前の public projection に
  出さない**。`_preseal_semantic_sha` の除外集合へ加える。open batch 中の prospective public state から
  実行済み prefix 長が推定できないことを負例テストで固定する。
- **Δ4** W4 = **全 terminal path を `BatchCommitted → BatchResultsPrepared → BatchSealed` の 3 event に
  統一**する。全 tombstone 専用の 2 event 終端 (プラン 162-170 行) は**破棄**。`BatchTombstoned` event 型は
  削除し、未実行 member は `outcome="tombstoned"` の member row として `BatchSealed` に載せる。
  member row 数 = committed cardinality で固定。**JSON byte 長の同一化は保証しない**ことを
  明示的な受容残余として docstring と記録に書く (設計本文の「上界が未定義 → 明示的に受容残余とする」に従う)。
- **Δ5** `member_sequence_commitment` を**削除**する。
- **Δ6** codec 上限は **production helper を使わない独立 oracle** で worst-case JSON を組み、
  `max` と `max+1` の両方を literal で pin する。二分探索の出力を期待値にしない。
- **Δ7** `_salt()` を **exactly 32 hex** に固定する (現行は下限のみで上限なし)。受理集合を狭めるので、
  32hex が通る正例と 31/33/34hex・非 hex・全 0 が落ちる負例を登録する。
- **Δ8** feasibility は **per-batch frame 上限**と **origin-total 予算**を分離する。
  `qmax` / `floor.required_queries` を単一 batch として serialize するのをやめ、
  (a) per-batch = worst-case frame から `_MAX_BATCH_CARDINALITY` を導出、
  (b) origin-total = partition 可能性 (`qmax <= imax * _MAX_BATCH_CARDINALITY`) と ledger-total 上限で検査する。
- **Δ9** `MANIFEST_SCHEMA_ID` / `AUTHORITY_SCHEMA_ID` を **/v2** へ bump し、registry file を
  `reflux_origin_authority_v2.json` へ改名する (中身は `origins: []` のまま)。
  同一 schema ID の意味を黙って変えない。**編集面が 2 file を超えるため brief の scope を訂正する**
  (改名は削除を伴うので `DW-O11` に従い受入前に `git add -A` する)。
- **Δ10** floor の名乗りを訂正する。ledger は物理 query を観測しない。`sealed_queries` は
  「evidence を伴う sealed member row 数」であり実 query 数の代理ではないことを docstring と
  テスト名に明記し、境界テストで固定する。恒真な「query 一対一」検査は**作らない**。
- **Δ11** W3 の名乗りを「outcome と evidence digest **claim** の commitment 束縛」とする。
  referent の実在・完全性検証は W5 の分界どおり formal consumer の義務であることを docstring に書き、
  ledger が dereference しないことを境界テストで固定する (これを consumer 実装済みと数えない)。
- **Δ12** 親 brief の受理集合方向の誤り (erratum-2) を記録する。
- **Δ13** brief-erratum-1 (outcome 素通しの記述誤り) を記録する。
- **Δ14** 並行 producer wave への interface delta を handoff へ書く。

## scope 外の real 所見 (実装せず、裁定パッケージ / 起票へ)

1. **物理 query と member row の束縛** (A-1 の本体)。ledger 単体では閉じない。producer/driver が
   member ごとに 1 実 query を実行したことの receipt を要求する設計は W1 と P7 の面。
   → 新 T 起票 + ユーザー裁定へ。
2. **evidence digest の resolver 契約** (A-2/B-4 の本体)。authority-backed evidence receipt か
   content-addressed resolver か。→ 新 T 起票 + ユーザー裁定へ。
3. **並行 producer wave との landing closure** (B-3)。同一 closure に再編するか、
   ledger 先行 + producer 追随か。→ ユーザー裁定へ。

## 変異事前登録 (`DW-M01`、実装前)

実装後に `tools/mutation_harness.py` で本走する。各変異は単一理由性をコードで確認してから登録する。
登録案は下記 18 件 + 正例 2 件。実装子の完了報告を受けて anchor を確定し、段 6 の fix 後に
`DW-M07` で anchor を再検証してから本走する。

| # | 変異 | 落ちるべき node (期待) |
|---|---|---|
| M-1 | member preimage から wire を除く | v17 member identity |
| M-2 | member preimage から query ordinal を除く | v17 |
| M-3 | member preimage から replicate ordinal を除く | v17 |
| M-4 | origin-wide replicate 出現回数の検査を削除 | v17 cross-batch |
| M-5 | query ordinal の連続性検査を削除 | v17 |
| M-6 | duplicate candidate commitment 拒否を削除 | v17 |
| M-7 | seal 時の wire canonicality 検査を削除 | v17 negative |
| M-8 | prepared member identity 一致検査を削除 | v16 改訂 |
| M-9 | cardinality 全件 opening 要求を緩める | v18 |
| M-10 | reducer の outcome 閉包を削除 | v18 direct `_apply_event` |
| M-11 | accepted/rejected の evidence 必須を削除 | v18 |
| M-12 | tombstoned の evidence-null 要求を削除 | v18 |
| M-13 | result/evidence commitment 照合を削除 | v18 tamper |
| M-14 | tombstone を `sealed_queries` に加算 | v14 改訂 (floor) |
| M-15 | seal 前 projection へ実行依存 counter を戻す | v20 pre-seal oracle |
| M-16 | payload へ replicate ordinal を出す | v20 |
| M-17 | `_salt` の上限を外す | v21 salt 幅 |
| M-18 | feasibility の per-batch / origin-total 分離を戻す | v21 codec |
| P-1 (正例) | 変異なし・同一 wire の R 回 replicate が seal できる | v17 positive |
| P-2 (正例) | 変異なし・partial tombstone suffix が seal できる | v18 positive |

**恒真 residual (kill 不能と事前に明記する。KILLED に数えない)**
- 「実 query より先に receipt を得た」— driver 不在のため壊す production 行が無い。
- 「producer が seal 前に別ログへ outcome を漏らさない」— ledger file だけでは証明不能。
- 「evidence / class digest の referent が実在する」— formal consumer 不在。
- 現行 V08 の `"provider" not in source` は consumer 義務の証拠ではなく ledger が provider を持たない pin。

## P4 充足判定 (依頼の中心)

**P4 は充足しない。** 本 wave が到達するのは「D153 W1〜W5 の ledger 側契約に適合する
P4 batch-freeze prototype」までである。会計は D159 決定 4 の U-G と同型で、残るのは次の 6 点。

1. producer が全 member commitment を先に commit し、receipt 後にだけ query を実行する結線。
2. driver が 1 member を 1 実 query / 1 evidence artifact に対応させる結線。
3. 実 authority manifest の登録 (D121 P10 = ユーザー裁定待ち) と authority receipt の伝播。
4. seal 前の外部漏洩を防ぐ producer / storage 契約 (並行 wave の段 2 が
   「`drive_iteration` は seal 前に provenance/WAL/checkpoint を書く」と実測済み)。
5. formal consumer が evidence / class referent を解決し、不在・不完全・policy 不一致を拒否する
   受理集合変更 (D96 手続)。
6. proof chain / 材料レポートがその consumer 判定を必須にする結線。

加えて、並行 wave が独立に実測した **「現行 production caller はどれも合法 batch (cardinality >= 2) を
作れない」** は、P4 の発火 path が今日時点で存在しないことの一次証拠である。

## W1〜W5 の適合判定 (依頼の中心、実装後の目標状態)

| 裁定 | 実装前 (`55c2e84` 実測) | 本 wave 実装後の目標 |
|---|---|---|
| W1 | 部分適合 (ledger 面のみ、結線ゼロ) | 変わらず部分適合。結線は scope 外 |
| W2 | **非適合** | 適合 (Δ1・Δ2) |
| W3 | **非適合** | 適合 = 「outcome ↔ evidence digest claim の commitment 束縛」(Δ11 の名乗りで) |
| W4 | 部分適合 | 適合 = row 数固定 + terminal event 形統一 (Δ4)。byte 長は受容残余 |
| W5 | 部分適合 | 適合 (層分界を docstring と境界テストで明示、Δ11)。consumer 実在は scope 外 |

## erratum (親 brief の訂正、履歴として凍結)

- **erratum-1**: brief の「`outcomes` は自由文字列で素通し」は**誤り**。`:634` が codec 層で
  `accepted`/`rejected` に閉じ、commit 経路は必ず `_event_payload` を通る (`:2408`)。
  fail-open は `_apply_event` の直接呼び出しのみ。W3 非適合の結論は変わらない。
- **erratum-2**: brief の DW-G05 で「W2 非適合を放置すると certifiable 集合が**広くなる**」と書いたのは
  **方向が逆**。floor は下限であり過少計数は seal を難しくする = 狭める (false reject)。
  実際に広がるのは ordinal 導入**後**に生じる A-1 の水増し経路である。Δ10 でその境界を固定する。
- **erratum-3**: brief が設計材料 `output/insights/2026-08-04_t244-p4-batch-freeze/` と
  設計本文 `output/insights/2026-08-01_t244-reflux-design/README.md` §4③ を入力に挙げていなかった。
  段 4 で読み、W4 の規範定義 (§4③-5) を裁定根拠に加えた。
