# 2026-08-30 — 軸 1 の文献検索 改訂契約による実行記録 (凍結)

- **作成日:** 2026-08-30
- **入力 commit:** `2617eee02` (本 wave の最終 tip)
- **登録 commit (`C_reg`):** `d0ba65c01` — この commit の bytes を要求する preflight を通した後にだけ
  HTTP を発行した。
- **入力 digest:** 取得した値は repo の外にあり、
  `output/insights/2026-08-29_t2033-axis1-retake/bundle/manifest.json` が file ごとの SHA-256 で
  束縛する。同 manifest の SHA-256 は §2 に置く。
- **入力 path:** `docs/related-work/claim-survey/2026-08-29-axis1-search-amendment.md` (契約) /
  `docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json` (query program) /
  `docs/decisions.md` の D1155・D1183・D1207・D1208
- **文献 cutoff:** 契約 §2 の暦年境界 2026-12-31。取得日は 2026-08-29 と 2026-08-30 である。
- **契約の正本:** `docs/related-work/claim-survey/2026-08-29-axis1-search-amendment.md`。
  **本文書は契約を 1 byte も変えていない。**

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 総合判定

> **軸 1 は `未完走` である。成熟度は `RW1` のまま動かない。**

改訂した契約でも、`RW3` の条件は論理積である。登録 leaf 263 本のうち完走したのは **183 本**で、
control・補助探索・感度監査・record 判定・work-family 統合は 1 つも実行していない。
**未実装の schema 層が 5 つある以上、検査器が導出する `axis_complete` は必ず偽になる。**

**本文書は世界の不在を一切作らない。** 取得した record について**内容を 1 件も判定していない。**
取得件数を「調べ終えた件数」へ読み替えてはならない。

## 1. 母集合と除外 — 1 行

> **軸 1 の母集合は、共有暦境界 2026-12-31 を各索引固有の日付欄へ当てた登録 epoch
> `AX1-20260829-E1` の query 群 (固定・非重複の日付 shard を含む) が返した、索引固有 work ID
> レコードの和である。境界の外、登録した query と登録した 3 索引の外は母集合の外であり、
> `AX1-20260829-E1-Q6-EXCLUSION@dblp` の 1 枝だけが D1155 の構文能力を理由とする宣言的除外である。
> 取得失敗・無償枠切れ・未実行は除外ではなく `未完走` である。**

**本走行で除外に当たるのは `AX1-20260829-E1-Q6-EXCLUSION@dblp` の 1 枝だけである。**
それ以外の未完走 80 枝は、すべて `未完走` であって除外ではない。

## 2. 証拠 bundle

`output/insights/2026-08-29_t2033-axis1-retake/bundle/`。

| 項目 | 値 |
|---|---|
| page evidence | 593 |
| 生応答 (gzip) | 593 |
| 再開点 (checkpoint) | 169 |
| occurrence ledger | 580 |
| bundle 内の file 総数 | 2,124 |
| bundle の bytes 合計 | 98,570,351 |
| `manifest.json` の SHA-256 | `e74deb222df4f04899029e07bc771ed77d1cfc66bfea188f01c17f8293368214` |

**page evidence と生応答は 593 対 593 で一対一に対応する。** 検査器はこの対応を双方向で
exact に要求する (`missing` も `extra` も許さない)。

本 wave は判定に使わない診断走行を 3 本行い、**いずれも削除した** (合計 371 MB)。
§7 で何が起きたかを書く。**本記録が引く 2 つの発見の根拠は
`output/insights/2026-08-29_t2033-axis1-retake/findings/` へ抜き出してある。**
生応答そのものは残していない — 判定に使わない走行の bytes を repo へ残さない判断である。

## 3. 登録 263 leaf の実行結果

検査器 (`tools/check_axis1_search.py bundle`) が bundle 全体を最後まで検証し、
登録 ID 集合との完全一致 (`exact_identity_map = true`) を確認したうえで返した状態である。

| 索引 | 登録 leaf | 完走 | 未完走 (evidence あり) | 未完走 (完了 pass なし) |
|---|---:|---:|---:|---:|
| arXiv | 173 | **171** | 0 | 2 |
| DBLP | 12 | **12** | 0 | 0 |
| OpenAlex | 78 | 0 | 1 | 77 |
| 合計 | 263 | **183** | 1 | 79 |

これに宣言的除外の `AX1-20260829-E1-Q6-EXCLUSION@dblp` が 1 本加わる (HTTP を発行しない)。

### 3.1 取得量

| 索引 | distinct な索引固有 work ID |
|---|---:|
| arXiv | 31,500 |
| DBLP | 4,479 |
| OpenAlex | 200 |
| 3 索引の和 (work-family 統合をしていない索引固有 ID の和) | **36,179** |

occurrence の行数は全 pass 合わせて 150,885 である。
**この和は work-family 統合前の索引固有 work ID の和であり、研究数ではない** (契約 §5.3)。

### 3.2 旧走行との対比 — 条件 3 の改訂が実際に効いた

旧走行 (2026-08-27) では arXiv の 6 枝と OpenAlex の 4 枝が条件 3 で落ちていた。原因は、
`itemsPerPage` と `meta.per_page` が要求値のエコーであって実要素数ではないのに、契約が
両者の一致を要求していたことである。

**改訂後、同じ形の応答が通った。** 例として `AX1-20260829-E1-Q1@arxiv` は
宣言 64 件・容量エコー 200・実要素数 64 で、6 条件すべて `可` で完走した。
旧契約ならこの数値で条件 3 が `否` になる。

## 4. DBLP — 2 つの判定を併記する (契約 §10.3)

契約 §3.5 は、登録する期待 echo を「登録句を英数字 token へ分割し (ハイフンも区切り)、
各 token に `*` を付け単一空白で連ねた文字列」と定めた。旧契約は「語の各単語に `*` を付けて
空白で連ねた文字列」で、ハイフンを区切りとしていなかった。

| 枝 | 登録語 | 登録した期待 echo | 実際の echo | 旧の逐語期待 |
|---|---|---|---|---|
| `AX1-20260829-E1-T05@dblp` | `two-phase locking` | `two* phase* locking*` | `two* phase* locking*` | `two-phase* locking*` |
| `AX1-20260829-E1-T07@dblp` | `multi-version concurrency control` | `multi* version* concurrency* control*` | `multi* version* concurrency* control*` | `multi-version* concurrency* control*` |

- **`completion_under_registered_tokenizer`:** DBLP 12 枝すべて `完走`。
- **`completion_under_legacy_literal_echo`:** `T05` と `T07` は条件 1 で `未完走`、他の 10 枝は `完走`。

**どちらを正とするかは人間の裁定に委ねる** (§8 の U7)。軸 1 はどちらでも `未完走` であり、
下流の値は変わらない。

## 5. 未完走の内訳

### 5.1 OpenAlex 78 枝 — 解釈照合の順序 (**新しい面**)

`AX1-20260829-E1-Q1@openalex` は条件 1 だけが `否` で、**条件 2〜6 はすべて `可`** である。
残り 77 枝は日次の無償枠に阻まれて未実行である。

**原因を精確に測った。** 先行する診断走行 (2 回目、削除済み) で OpenAlex の 78 leaf を
取得し、その **92 頁**について、登録した `expected_openalex_oqo` と実応答の
`meta.x_query.oqo` を突き合わせたところ、

> **92 頁すべてで、両者は順序を除いて完全に同一だった (92/92)。順序だけが違う。**

抜粋は `output/insights/2026-08-29_t2033-axis1-retake/findings/openalex-oqo-ordering.json`。

OpenAlex は `or` グループ内の語順とグループの順序を正規化して返す。本改訂の登録値は
登録順のままであった。**正しい query が実行されており、取得は成功している。**
落ちたのは順序つきの構造比較だけである。

これは旧走行の DBLP ハイフン問題と同じ族の、**登録側の欠陥**である。
**結果を見た後なので述語は緩めない** (契約 §8)。78 枝は `未完走` として記録し、
可否は人間の裁定へ返す (§8 の U10)。

**親の事前 probe では露見しなかった。** 契約 §4.4 に載せた中立語の複合 filter probe は、
使った語 (`alpha beta` / `gamma delta` / `epsilon zeta` / `eta theta`) がたまたま
アルファベット順だったため、正規化による並べ替えを起こさなかった。**測定の不備である。**

### 5.2 arXiv 2 枝 — 完了した pass が無い

| 枝 | 検査器の状態 | 検査器の理由ラベル | runner が記録した理由 |
|---|---|---|---|
| `AX1-20260829-E1-Q6-SM202511@arxiv` | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `distinct_work_id_total_mismatch` |
| `AX1-20260829-E1-Q6-SM202605@arxiv` | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `distinct_work_id_total_mismatch` |

**検査器の状態判定は正しい** (完了した pass が無い)。**理由ラベルは不正確である** —
この 2 枝には page evidence が実在する (それぞれ 4 頁と 3 頁)。ラベルの是正は次の一手へ送る。
**受理判断は変わらない。**

**内容は先行する診断走行 (2 回目、削除済み) で精確に測った。** `AX1-20260829-E1-Q6-SM202510@arxiv` は
pass 1 の終端 ledger で、宣言 835 件・返却 835 行に対し
**distinct な索引固有 work ID が 834** だった。arXiv が頁境界で 1 件 (`2510.27489v2`) を
重複して返しつつ、`totalResults` では 1 回しか数えないためである。
旧走行が `AX1-Q6@arxiv` 全体で 295 件の重複を観測したのと同じ性質である。
抜粋は `output/insights/2026-08-29_t2033-axis1-retake/findings/arxiv-duplicate-work-id.json`。

**ledger は attempt ごとの累積 snapshot である。** pass を跨いで、あるいは attempt を跨いで
合算した行数は取得完全性の指標にならない。上の数は pass 1 の終端 snapshot から取っている。

**これは D1207 が列挙していない新しい面である。** D1207 の条件 4・5 の改訂は
「OpenAlex が同じ研究に別々の work ID を持つ」件であり、
「索引が同じ work ID を 2 回返しつつ総件数では 1 回しか数えない」件ではない。
**述語は緩めず未完走として記録する。** 可否は人間の裁定へ返す (§8 の U11)。

### 5.3 OpenAlex 77 枝 — 無償枠 (再開点あり / 未実行)

`AX1-20260829-E1-Q1@openalex` は予約を割った時点で `paused_quota` の再開点
(`checkpoints/000084.json`、`resume_action = continue_cursor`) を発行した。
残り 77 枝は着手していない (`not_run`)。

**契約 §8 の credit 会計に従い、応答ごとの `x-ratelimit-remaining` を読み、
予約 30 credit を割る前に停止した。枠切れを除外へ読み替えていない。**

## 6. 実行していないもの

| 項目 | 状態 | 契約の節 |
|---|---|---|
| control | `not_run` (本 epoch は実行可能 request を登録していない。CLI は fail-closed) | §6 |
| 補助探索 | `not_run` | 旧契約 §6.3 を引き継ぎ |
| 感度監査 | `not_run` | 旧契約 §6.2 を引き継ぎ |
| record ごとの判定 | `not_run` | §10 |
| work-family 台帳 | `not_run` | §5.2 |

**検査器が導出した最上位 status。**

```text
axis_complete = false
retrieval_complete = false
controls_valid = false
supplemental_complete = false
sensitivity_complete = false
classification_complete = false
family_ledger_complete = false
unimplemented_schema_layer_count = 5
exact_identity_map = true
bundle_validation_complete = true
```

**検査器は bundle が申告した値を読まない。** 未実装層数は実装側の固定値である。

## 7. 本 wave で捨てた走行と、その理由

**判定に使った走行は 1 つだけである** (§2 の bundle)。次の 3 つは判定に使わず、
生応答も残していない。**発見の根拠だけ `findings/` へ抜き出してある。**

1. **1 回目 (削除済み)** — 最初の実走。arXiv 168/173 と DBLP 12/12 を完走させたが、
   その後 runner と validator に field 名の食い違い (`expected_openalex_oqo` を読めない) が
   見つかった。**修正前の検査器が出した判定を流用しないため捨てた。**
2. **2 回目 (削除済み)** — 親が catalog を絶対 path で渡したため、
   schema が要求する repo 相対の形と食い違い、検査器が page evidence を拒否した。
   **§5.1 の OpenAlex 92/92 の順序一致は、この走行の生応答から測った。**
3. **3 回目 (削除済み)** — 応答を保存した後に失敗した attempt (DBLP の
   再試行 3 件) の page evidence が書かれず、検査器が `raw_path_set_mismatch` を出した。
   **検査器を緩めず writer を直した。**

**2 と 3 はいずれも検査器が実機で捕まえた欠陥である。** 記録として残す。

## 8. 人間の裁定へ返す項目

| ID | 問い |
|---|---|
| U7 | DBLP の期待 echo を §3.5 の実測トークン化規則にするか、旧の逐語期待を保って `T05` / `T07` を `未完走` に残すか。**本記録は両方の判定を併記しており、決めていない。** |
| U8 | D1208 の README 導線を、軸 3 側の着地後にどの変更単位で閉じるか (契約 §12)。 |
| U9 | `axis_complete=false` の bundle から論文 §3 へ値が流れる経路を report checker と `docs/paper-story/` 側でも塞ぐか。 |
| U10 | **新規。** OpenAlex の条件 1 を、`oqo` の順序非依存な比較へ改めるか。索引が `or` グループ内と グループ間の順序を正規化する以上、順序つきの比較は構造的に充足不能である。改めるなら新しい amendment・新しい epoch・新しい query ID を要する。 |
| U11 | **新規。** 索引が同じ work ID を頁境界で 2 回返しつつ総件数では 1 回しか数える場合の条件 5 の扱い。現契約では `未完走` になる。 |

## 9. この記録の限界

- **軸 1 の成熟度を動かしていない。`RW1` のままである。**
- **不在について何も言っていない。** 網羅率も未検出率も出していない。
- **record を 1 件も判定していない。** work-family 統合もしていない。
- **control・補助探索・感度監査を実行していない。**
- **OpenAlex の 78 枝は 1 枝を除いて着手していない。** 契約上の完走には無償枠で 5 日以上かかる。
- **arXiv の重複と OpenAlex の順序正規化は、本走行と先行する診断走行が観測した範囲の事実である。**
  API 仕様の恒久契約としては断定しない。
- **検査器の理由ラベルに 1 件の不正確さがある** (§5.2)。状態判定と受理集合には影響しない。
- **本実装は独立監査を受けている** — 段 3 の敵対相談 2 本、段 6 の敵対レビュー 2 本、
  焦点再レビュー 1 本が検査した。事前登録した 12 変異は最終 commit に対して 12/12 が
  期待 node 完全一致で KILLED だった。
