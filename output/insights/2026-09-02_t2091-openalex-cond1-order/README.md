# 2026-09-02 — OpenAlex の完走条件 1 を順序非依存へ改め、新 epoch を発行した

- **wave:** dev-wave-t2091-openalex-cond1-order (T-2091)
- **入力 commit:** `2fa13a262a53b7f4e610a40a7a7af7f86fc9d621` (local main)
- **実装 commit:** `e143c67a84e73e2020bba62822ce0cb5fa353ba7`
- **HTTP 発行数:** 0。**本 wave は 1 件も取得していない。**
- **軸 1 の成熟度:** `RW1` のまま動かない。**record を 1 件も判定していない。**

## 1. 何を閉じたか

索引が `or` グループ内の語順とグループの順序を正規化して返すのに対し、登録値は登録順のままだった。
このため条件 1 の構造比較は全枝で落ち、`runner.py` が最初の失敗で `blocked_on_ruling` を返して
後継 checkpoint を書かないため、**継続取得の経路が存在しなかった** (T-2090 の一次資料)。

条件 1 の OpenAlex 節を、`filter_rows` を暗黙の論理積とみなす再帰的な正規化比較へ改めた。
無視するのは**論理積・論理和として結合される兄弟の順序だけ**で、次はすべて保存する。

- 同一要素の多重度
- 入れ子の境界と深さ (グループを平坦化しない)
- グループの `join` の値
- 各 field の有無と型 (欠落・`null`・空文字列・数値・文字列を区別する)
- `get_rows` の値

`and` / `or` 以外の `join`、登録していない key、想定外の型は、**両側が同じ形であっても不一致**にする。

## 2. 段 3 が実測で出した規律 2 の穴

素朴な JSON 読み取りは同一 object 内の重複 key を後勝ちで潰す。実測で

```text
{"join":"xor","join":"or","filters":[A]}  →  {"join":"or","filters":[A]}
```

となる。これを放置すると、上の fail-closed 条項が**生応答経由で迂回され、
謳うだけで発火しない保証**になる。live (`runner.py`) と offline (`validator.py`) の
両抽出経路で重複メンバを拒否して閉じた。**射程は OpenAlex の `oqo` を取り出すこの 2 経路に限る。**

## 3. 変異による裏取り

固定 commit `e143c67a8` に対し、事前登録した 10 変異を走らせた。

| 結果 | 件数 |
|---|---:|
| KILLED (期待 node 完全一致) | **10** |
| MISMATCH / SURVIVED / TIMEOUT | 0 |

baseline は `PASSED`。**各変異はちょうど 1 つの test node を殺した** (M8 のみ 2 node で、
resume 経路の test も同じ比較を通るため)。単一理由性は probe 段で実測して確認した。

| ID | 変異 | 殺した node |
|---|---|---|
| M1 | 兄弟の整列を削除 | `test_openalex_condition1_compares_structured_oqo_not_oql_text` |
| M2 | 兄弟を集合化 (多重度を潰す) | `..._rejects_every_non_order_difference[multiplicity-difference]` |
| M3 | 同一 join の group を平坦化 | `...[same-join-flatten-difference]` |
| M4 | canonical 値から `join` を落とす | `...[join-difference]` |
| M5 | 未知 `join` を `and` へ丸める | `...[unknown-join-on-both-sides]` |
| M6 | 欠落 field を空文字列へ寄せる | `...[missing-vs-empty-string]` |
| M7A | live 側の重複メンバ拒否を外す | `test_runner_openalex_oqo_rejects_duplicate_raw_response_members` |
| M7B | offline 側の重複メンバ拒否を外す | `test_validator_openalex_structure_rejects_duplicate_raw_response_members` |
| M8 | 期待値側だけ正規化する | 上記 M1 の node と `test_resume_merges_digest_verified_prefix_with_real_openalex_parser` |
| M9 | 整列キーを定数化 | 上記 M1 の node |

**M5 と M7A / M7B が殺されたことが、fail-closed 条項が飾りでないことの実測である。**

**M2 は素の集合化だと `TypeError` で赤になり単一理由性を欠く。** 段 6 のレビューが指摘したので、
要素の型を保つ集合化として登録した。

**M9 は fixture の代替である。** 整列キーの衝突する入力対は構成できない — 引用符・カンマ・
括弧・空文字列を含む敵対的な値で 29 通りの異なる canonical node を作ったところ、
キーも 29 通りすべて相異だった。キーはタグ付き tuple の JSON 表現で単射である。
したがって**性質を fixture でなく変異で縛った**。

## 4. 契約側

改訂される契約自身 (旧 amendment §8) が、意味的 amendment に対して
新しい日付の amendment 文書・新 epoch・新 query ID・**全枝の再実行**・独立レビューを要求している。
完走述語の変更は「非意味的修繕 = 正規化 request が同一である変更」に当たらない
(その構成要素に完走述語は含まれない)。

`docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md` を発行し、
登録 epoch を `AX1-20260902-E1` として全 ID を新規化した
(logical 267 / 実行可能 leaf 263 / aggregate 3 / 宣言的除外 1)。
**枝の論理式、shard 境界、DBLP の期待 echo、条件 2〜6、最上位の導出式は 1 文字も変えていない。**
旧 amendment・旧 catalog・旧実行記録・旧証拠 bundle の bytes は 1 byte も変えていない。

## 5. 閉じていないもの

- **証拠の時点を外部の事実へ束縛する仕組みが無い。** 検査器は catalog digest・再導出 request・
  生応答の内容を検証するが、「その生応答が登録 commit の後に取得された」ことを検証しない。
  旧生応答を新 epoch の証拠へ再包装する経路を機械的に拒否できない (新 amendment の U13)。
- **新走行が新規 bundle を使うことを実装が強制しない。** `--bundle` は任意の path を受け、
  無償枠の観測は渡された bundle 内の `state/runtime.json` から読まれる (U12 と §7 の限界)。
- **実行器が旧凍結 bundle を出力先に取れる。** 凍結検査は preflight 時点の検出であって
  書込みの防止ではない (U14)。
- **旧 epoch の bundle は現行の検査器では検証できない。** schema の epoch を更新したため、
  旧 bundle を検証したい場合は旧 commit を checkout する (§7 の限界)。
- **旧凍結物を登録 preflight の凍結集合へ加える案は費用で見送った** (U15)。
  追加分 2,130 file / 99,925,266 bytes に対し現実装が 1 file ごとに別 process で blob を読むため、
  既存 18 秒の検査が数百秒規模になり、実行器の起動ごとにも同じ費用がかかる。
  しかも同じレンズが「preflight 後に旧 bundle へ書ける」経路は塞がらないと指摘した。
- **無償枠の失効判定に `x-ratelimit-reset` を使わない問題は残る** (U12)。
  新 epoch の bundle は観測なしで始まるので初回窓は使えるが、恒久解ではない。

## 6. この記録の限界

- **本 wave は HTTP を 1 本も発行していない。** 条件 1 が実際に `可` を返すことは、
  新 epoch の走行が出るまで確認されない。
- **順序差の実測資料は内部に食い違いを持つ。** 計数 3 欄と旧実行記録は 92 頁、
  同 file の記述欄だけが 78 頁と書く。元の診断走行は削除済みで再導出できない。
- **変異 wrapper は 2 回とも rc=125 で終わった** (`共有木の事後検査に失敗`)。
  1 回目は親が走行中に作業ツリーを編集したためで、親のミスである。
  2 回目は作業ツリーに触れておらず、**共有 main checkout が並行 wave の land で変化したため**である。
  いずれも `child_rc = 0` で、変異 harness 自体は完走している。上の 10/10 KILLED は
  `mutation-result.json` の現物であり、wrapper の事後検査の失敗は成果物に帰属しない。

## 収録物

| file | 中身 |
|---|---|
| `mutation-spec.json` | 事前登録した 10 変異の spec (逐語) |
| `mutation-result.json` | 変異本走の結果 (10/10 KILLED、baseline PASSED) |
| `stage3-review-correctness.md` | 段 3 敵対相談・正しさ境界のレンズ (逐語) |
| `stage3-review-coherence.md` | 段 3 敵対相談・整合と実効性のレンズ (逐語) |
| `stage6-review-correctness.md` | 段 6 敵対レビュー・正しさ境界のレンズ (逐語) |
| `stage6-review-coherence.md` | 段 6 敵対レビュー・整合と実効性のレンズ (逐語、差し戻し) |
| `stage6-focus-review.md` | 段 6 焦点再レビュー (逐語、所見 7 件すべて closed) |
