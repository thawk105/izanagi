## 受理集合の変化

**新規の過剰拒否という疑いは refuted。** 固定された同一履歴・同一 registry を比較すると、新たに拒否される履歴を consume の共有認可関数が受理する反例はありません。

以下、現物を A / T と略記します。

- A = [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/campaign/s8b_holdout_admission.py)
- T = [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_s8b_holdout_admission.py)

旧 query が認可を返す履歴のうち、判定が変わる集合は、**旧コードが legacy 分岐へ到達し、選択した trigger に対する追加 helper 呼出しが次のいずれかになるもの**です。

| helper の結果 | 新 query | consume の共有認可関数 |
|---|---|---|
| recovery 候補が1件以上 | A:5886で拒否 | 完了1件＋候補1件以上なので A:5765で拒否 |
| helper 自体が例外 | その例外で終了 | A:5759の同一 helper で例外 |
| 正常終了・候補0件 | 従来どおり認可 | 完了1件と canonical 判定で受理 |

これで変更集合を尽くします。recovery 分岐、従来の例外、`None` は変更されていません。

候補ありの場合、選択 trigger は既存 retry に使用済みです。未使用なら旧コードでも A:5853で候補を数え、legacy と合わせて A:5860で拒否するためです。対象には正しい候補、不正な候補、両者の複数併存がすべて含まれます。

helper 例外には読取・framing エラーや型不正も含みます。ただし、**旧 query の先行 helper 呼出しで既に落ちる履歴は変更集合に含みません**。

## 閉じ損ねた非対称

**本題の「選択された legacy 完了＋recovery 候補」の漏れは refuted。** 新 query の legacy 返却時には、同じ trigger の完了が1件、候補が0件、canonical 判定が真であり、A:5755以降の共有認可関数も受理します。

**公開 query の認可返却を「実際に追加 consume できる」という意味まで広げると、残存差は real です。** 具体例は追加正例の終了直後です。

```text
retry_slots_per_cell = 2
journal:
  planned start P
  session P: kind=planned, valid=false, 同じcell・round
  retry1 start: ordinal=1, trigger=P
  retry2 start: ordinal=2, trigger=P
registry: 不在
consume marker / attempt ledger: P・retry1・retry2 が消費済み
terminal: なし
```

この状態でも query は A:5890で P の認可を返します。しかし、retry3 は A:4357で frozen ticket 外として拒否され、retry1/2 の再消費は A:4384で拒否されます。

これは**既存の予算・再消費境界との差**です。共有 trigger 認可関数の XOR 漏れではなく、本 wave の修正対象外です。成果物への追加影響は確認できないため、must-fix にはしません。

## テストの恒真性

**(a) 追加負例が恒真という疑いは refuted。**

T:3547の3 parameter は、新条件を削除すると query が認可を返し、T:3599の `pytest.raises` が失敗します。その後の consume／inspection の拒否だけでテストが通る構造ではありません。

**(b) 同文言の既存経路との取り違えは refuted。**

T:3591の retry1 が P を使用済みにするので、P は A:5851で recovery 探索から除外されます。retry1 自身に対応する recovery はありません。したがって `recoveries` は空で、A:5866の既存経路には入りません。期待文言は新設 A:5888から出ます。

**(c) journal 不変 assert は限定的に有効です。**

T:3598–3606は「query が例外を返すまでに journal の bytes を変更しない」を守ります。ただし、旧コードでも journal は不変なので、**この assert 単独では新条件の欠落を検出しません**。registry・marker・ledger の不変性も保証しません。

**(d) 正例が過剰拒否を検出しないという疑いは refuted。**

T:3632は2回目にも認可の完全一致を要求します。legacy から使用済み trigger を除外する変異では、2回目に P が消え、ここで失敗します。consume 側へ同じ除外を入れるなら T:3642で失敗します。

新条件を丸ごと削除しても正例は通ります。これは保存すべき旧受理集合の正例として正常です。欠落は負例、過剰拒否は正例が検出します。

## 既存期待値の改変

**refuted。** 提示された `impl.diff` のテスト差分は追加のみです。既存 assert の反転・緩和・skip・削除はありません。

実装側の既存行の置換も、返却する trigger の式をローカル変数へ移したものです。

## F593 / F590 の再発

**F593 再発は refuted。**

- 完了候補は A:5826で全件取得し、A:5830で重複を拒否してから canonical 判定します。
- recovery 候補は A:5492の共有母集合をそのまま使います。
- 不正な座標でも start hash／receipt の参照が一致すれば候補に残ります。
- 新条件は検証済み候補だけへの絞り込みや replay 後の計数を行いません。

**F590 再発は refuted。** 新条件は候補の存在検査であり、「最新 retry」「未使用 trigger」を legacy の受理条件へ追加していません。consume／最終 inspection の時点分岐も変更していません。

## 変異の帰属 (実装後)

対象文字列 `if evidence.candidates:` は A:5886の**1箇所だけ**です。

| 変異 | 指名テストの失敗箇所・理由 | 静的判定 |
|---|---|---|
| `MUT-T2595-LEGACY-RECOVERY-OMIT` | 全3 parameter：query が返却し T:3599が失敗 | 帰属成立 |
| `MUT-T2595-LEGACY-RECOVERY-MULTIPLE-ONLY` | `valid-one`／`corrupt-one`：候補1件を拒否せず T:3599が失敗 | 帰属成立 |
| `MUT-T2595-LEGACY-RECOVERY-SINGLE-ONLY` | `valid-plus-corrupt`：候補2件を拒否せず T:3599が失敗 | 帰属成立 |
| `MUT-T2595-LEGACY-RECOVERY-EMPTY-REJECT` | 正例の最初の query：空 tuple も `is not None` なので T:3632で例外 | 帰属成立 |

`corrupt-one` の hash chain 不整合を replay が先取りすることもありません。ここでは候補抽出しか行わず、legacy 分岐から検証 replay は呼ばれません。

後続 consume／inspection に同じ履歴の拒否層はありますが、変異時にはその前の query 期待でテストが失敗します。**指名変異で帰属不成立のものはありません。実測による KILL 確認は未実施です。**

## must-fix と nit の分別

- **must-fix：なし。** 本差分による未承認の受理集合変更、既存期待値改変、変異の帰属失敗は見つかりませんでした。
- **backlog：** 予算枯渇後にも query が trigger 認可を返す既存挙動。追加 consume は拒否され、成果物への追加影響は未確認です。
- journal 不変 assert の保証範囲は限定的ですが、テスト欠陥とは判定しません。

## 裁定パッケージ候補 (scope 外の real 所見)

1. **real：完了行の round 不整合。**  
   入力は `start P(round=1)`、`session P(round=2, kind=planned, valid=false, 同じcell)`、registry 不在。query の round=1では A:5836により legacy 候補から外れます。一方、P を trigger とする retry の共有認可関数は A:5742–5746で round を検査せず受理します。裁定済みの既存差です。

2. **real：不正 hash 型の例外漏出。**  
   正しい target start 行に加え、別座標の recovery 行へ `start_event_sha256: []` を置くと、A:5485の集合 membership が `TypeError` を送出します。canonical JSON であることだけでは防げません。これも裁定済みの既存挙動です。

3. **real：予算枯渇後の query／consume 差。**  
   上記の2 retry消費済み履歴。trigger 認可と残存 ticket の保証範囲をどう扱うかという既存 API 契約の論点です。

いずれも本 wave での実装変更は提案しません。

## 総括

**本差分への real な must-fix はありません。** legacy 混在履歴の穴を閉じ、consume が受理する履歴への新たな過剰拒否は確認されません。追加負例・保存正例・4変異の帰属は静的に成立します。

必読5ファイルを読取確認しました。ファイル変更・commit・pytest・変異実測は行っていません。