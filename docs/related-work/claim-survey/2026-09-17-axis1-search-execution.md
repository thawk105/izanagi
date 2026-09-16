# 2026-09-17 — 軸 1 検索の実行記録 — 新 epoch `AX1-20260902-E1` の OpenAlex 5 窓目 (打ち切り後の再開)

**これは実行記録であって、登録でも改訂でもない。** 登録の正本は
`2026-09-02-axis1-search-amendment.md`、query program の正本は
`2026-09-02-axis1-search-catalog.json`、1 窓目の実行記録は
`2026-09-03-axis1-search-execution.md`、2 窓目は `2026-09-05-axis1-search-execution.md`、
3 窓目は `2026-09-07-axis1-search-execution.md`、4 窓目 (残量消化と打ち切り) は
`2026-09-08-axis1-search-execution.md` である。
本文書は凍結物であり、後から上書きしない。内容を更新したいときは新しい日付の実行記録を足す。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。**

**本走行は、4 窓目で打ち切った窓ごとの取得を、ユーザーの直接指示で再開したものである。**
再開は decisions 台帳の打ち切り決定 (D1760) の部分的な supersede であり、その射程と理由は
decisions 台帳の該当エントリ (本 wave の記録から採番) が正本である。打ち切り決定のうち
「`RW1` 据え置き・世界の不在を主張しない・既存証拠の bytes 不変・同じ登録 commit と epoch を引き継ぐ・
arXiv / DBLP へ request を出さない」はそのまま維持している。

## 0. この走行の身元

| 項目 | 値 |
|---|---|
| 作成日 | 2026-09-17 (JST) |
| 登録 epoch | `AX1-20260902-E1` |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` (1〜4 窓目と同じ。main の祖先を detach した木を cwd にした) |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| 文献 cutoff | `2026-12-31` |
| run ID (初回取得) | `t2035-openalex-20260917a` |
| run ID (独立 2 走目) | 各 checkpoint の `canonical_runner_argv` の値をそのまま (`t2090-openalex-20260903`) |
| 索引 | OpenAlex のみ (arXiv / DBLP は本 epoch でまだ 1 request も出していない) |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (1〜4 窓目と同じ root、296 MB) |
| bundle manifest SHA-256 (走行後) | `a6a42514e6d52c4e90243e706295f3ce215f4f5c91c0ad100a7d90f32d22e2a4` |
| bundle manifest SHA-256 (走行前) | `f3aeb91f823d2820d289668cbc85b8a3a0b51ca44608d46fc135847b48da0035` (4 窓目の走行後値と一致) |
| 逐語と部分 mirror | `output/insights/2026-09-17/t2035-axis1-openalex-window5/` |

登録検査 (`tools/check_axis1_search.py registration`) は detach した木で `passed: true` を返した。

## 1. 何を起動したか

打ち切り時点 (4 窓目) の残りは未走 9 leaf (`Q6-SY2018`〜`SY2026`) と独立 2 走目 53 本だった。
打ち切り時点で裁定待ちになっていた 2 leaf (`Q6-SY2014` / `Q6-SY2015`、`declared_total_drift`) は
本走行でも走らせていない。駆動 loop の除外集合に明示的に置き、`Q6-SY2015` が残した
`resume_action=continue_cursor` の checkpoint `000060` が再開経路に乗らないようにした。

| 区分 | 起動 | request | 結果 |
|---|---|---|---|
| 初回取得 (`--query-id`)、親の手動 1 本 + loop 6 本 | 7 | 84 | 5 本 `pass_complete`、2 本 `blocked_on_ruling` |
| 中断 pass 1 の再開 (`continue_cursor`) | 0 | 0 | 該当 checkpoint なし (除外した `000060` を除く) |
| 独立 2 走目 (`--checkpoint`)、loop 停止後に親の手動 5 本 | 5 | 9 | 5 本 `blocked_on_ruling` |
| 合計 | 12 | 93 | 残量 999 → 69 で停止 |

起動は 00:59:19〜01:11:13 JST。生死確認の直接取得が別に 2 request (`per-page=1`、各 1 credit)。

| 段 | leaf | 頁 | state | reason_code |
|---|---|---|---|---|
| 初回 (手動) | `Q6-SY2018` | 5 | `pass_complete` | — |
| 初回 | `Q6-SY2019` | 7 | `pass_complete` | — |
| 初回 | `Q6-SY2020` | 9 | `pass_complete` | — |
| 初回 | `Q6-SY2021` | 11 | `blocked_on_ruling` | `distinct_work_id_total_mismatch` |
| 初回 | `Q6-SY2022` | 12 | `pass_complete` | — |
| 初回 | `Q6-SY2023` | 16 | `pass_complete` | — |
| 初回 | `Q6-SY2024` | 24 | `blocked_on_ruling` | `distinct_work_id_total_mismatch` |
| 2 走目 | `Q3-SY1997` | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 2 走目 | `Q3-SY1998` | 1 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 2 走目 | `Q3-SY1999` | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 2 走目 | `Q3-SY2000` | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |
| 2 走目 | `Q3-SY2001` | 2 | `blocked_on_ruling` | `second_pass_digest_mismatch` |

新しい checkpoint は `000063`〜`000067` の 5 本 (完走した pass 1 の 2 走目の再開点)。

駆動 loop は初回取得を登録順に進め、残量 159 で `Q6-SY2025` の前に止まった (閾値 200)。
`Q6` の年 shard は 2018 年の 5 頁から 2024 年の 24 頁 (申告総数 4669) まで単調に増え、
初回取得 7 本だけで 84 request を使った。**1 窓 (約 80 request) では初回取得が終わらず、独立 2 走目は
loop からは 1 本も起動できなかった。** 残量 159 は、loop の閾値を下げると計画順で先に来る `Q6-SY2025`
(20 頁超の見込み) が起動して取得器の自己施錠 (残量 40 未満で発行不能) を招くため、loop を使わずに
独立 2 走目の先頭 5 本 (各 1〜2 頁) を checkpoint の argv どおりに 1 本ずつ起動した。残量 69 で止め、
次窓の手動更新 1 本が出せる状態を残した。

## 2. 初回取得 — 申告総数は一定、頁境界の重複が常態、落ちた 2 本は 1 件不足

| leaf | 申告総数 (全頁一定) | 返却 occurrences | distinct | 頁境界の重複 | 結果 |
|---|---|---|---|---|---|
| `Q6-SY2018` | 888 | 889 | 888 | 1 | `pass_complete` |
| `Q6-SY2019` | 1242 | 1242 | 1242 | 0 | `pass_complete` |
| `Q6-SY2020` | 1598 | 1600 | 1598 | 2 (終端頁は 0 件) | `pass_complete` |
| `Q6-SY2021` | 2043 | 2044 | **2042** | 2 | `blocked_on_ruling` |
| `Q6-SY2022` | 2251 | 2255 | 2251 | 4 | `pass_complete` |
| `Q6-SY2023` | 3183 | 3187 | 3183 | 4 | `pass_complete` |
| `Q6-SY2024` | 4669 | 4671 | **4668** | 3 | `blocked_on_ruling` |

- 申告総数は 7 leaf すべてで全頁一定であり、4 窓目の `declared_total_drift` は本走行では出ていない。
- **頁内の重複は 0 だが、頁境界を跨ぐ重複が 7 leaf 中 6 leaf にある。** cursor 分頁の最中に並びが動き、
  同じ work が 2 頁に現れる。通った leaf も同じ現象を持ち、通るか落ちるかは、押し出された work が別の
  頁に再出現するか (重複だけで済む) 消えるか (distinct が 1 件足りない) の差である。
- 落ちた 2 本はどちらも不足 1 件。3 窓目の `Q3-SY2025` / `SY2026` (2〜3 件不足) と同じ条件 5 の形。
- **条件は緩めていない。** 取得器は 2 本とも `blocked_on_ruling` にしており、本走行はその判定を
  そのまま記録している。
- 検査器の leaf 診断は、これらを 4 窓目までと同じく `leaf_page_evidence_missing` と報告する
  (独立 2 走を要する shard leaf なので `expected_passes` が `[1, 2]` になり、pass 2 の欠落が先に立つ)。
  走行時の理由 `distinct_work_id_total_mismatch` は台帳側にしか残らない。

## 3. 独立 2 走目 — 12 日を隔てた 5 本は 5 本とも不一致

pass 1 は 2026-09-05 (2 窓目)、pass 2 は 2026-09-17。数値は
`output/insights/2026-09-17/t2035-axis1-openalex-window5/evidence-detail.txt`。

| leaf | pass 1 申告 / distinct | pass 2 申告 / distinct | 2 走目で増えた ID | 消えた ID | 共通 ID の順序 |
|---|---|---|---|---|---|
| `Q3-SY1997` | 233 / 233 | 234 / 234 | 2 | 1 | 変化 |
| `Q3-SY1998` | 185 / 185 | 184 / 184 | 3 | 4 | 変化 |
| `Q3-SY1999` | 220 / 220 | 216 / 216 | 3 | 7 | 変化 |
| `Q3-SY2000` | 225 / 225 | 225 / 225 | 2 | 2 | 変化 |
| `Q3-SY2001` | 222 / 222 | 220 / 220 | 0 | 2 | 変化 |

- **申告総数が同じ `Q3-SY2000` でも中身は 2 件入れ替わっている。** 総数の一致は同一性の証拠にならない。
- 5 本すべてで共通 ID の並び順が変わっている。
- 2 窓目の独立 2 走目 (2 日を隔てて 8 本中 1 本不一致) より格段に高い不一致率である。残る 2 走目待ち
  48 本の pass 1 は 9/5・9/7・9/8 であり、**同じ運命になる見込みが強い。** 「同じ登録 request を日を隔てて
  2 度投げて同じ集合が返る」という完走条件は、生きた索引に対して日数が経つほど成立しなくなる。
- 不一致 leaf には後継 checkpoint が無く、再取得しか経路が無い (2 窓目と同じ)。
- **条件は緩めていない。** 取得器の `blocked_on_ruling` をそのまま記録している。

## 4. 無償枠の扱い

| 項目 | 値 |
|---|---|
| `x-ratelimit-limit` | 1000 |
| 走行開始時の残量 | 999 (生死確認 1 本の後。9/8 以降 1 request も出しておらず、窓は満量だった) |
| 生死確認 | 2 request (`per-page=1`、各 1 credit) |
| 取得 | 93 request (`per-page=200`、各 10 credit) |
| 停止時の残量 | 69 (走行後の header 観測は 68) |
| リセット | 2026-09-17 09:00:00 JST (実測 header で 2 度確認: 00:36 の `reset=30190`、01:13 の `reset=27968`) |
| 自己施錠 | 入っていない |

**残量 69 で意図的に止めた。** 残量が 40 を切ると取得器自身の発行規範 (`remaining - 30 >= cost`)
により 1 request も出せなくなり、次の窓で持続観測を更新する手動 1 本すら拒否されて自己施錠に入る。

HTTP 429 は本走行では 1 度も出ていない。

## 5. この走行が実装していないこと

窓またぎ設計 (U12)、証拠時点の束縛 (U13)、条件 5 の扱い (D1564 / D1623 で現状維持)、
`axis_complete` の production 経路はいずれも触っていない。repo の実装面の差分は 0 である。
駆動 loop は repo 外の使い捨て script (4 窓目の逐語に path 定数と除外集合だけ変えたもの) であり、
逐語を insight に `.txt` で置いた。

## 6. 検査器の出力

`tools/check_axis1_search.py bundle` は
`bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
`reason_code: leaf_not_run` を返した (rc=2)。全文は
`output/insights/2026-09-17/t2035-axis1-openalex-window5/bundle-check.json`。

OpenAlex 78 leaf の内訳 (4 窓目終了時 → 本走行終了時):

| 状態 | 4 窓目 | 本走行 |
|---|---|---|
| `complete` (独立 2 走まで完了) | 8 | 8 |
| pass 1 完了・2 走目待ち (再開点あり) | 53 | 53 (−5 不一致、+5 新規) |
| 条件 5 で未完走 (再開点なし、`Q1` / `Q4` / `Q5`) | 3 | 3 |
| 2 走不一致で未完走 (再開点なし) | 1 | **6** |
| 条件 5 で pass 1 が落ちた (再開点なし) | 2 | **4** |
| `declared_total_drift` で pass 1 が落ちた (再開点なし、裁定待ち) | 2 | 2 |
| 未走 | 9 | **2** (`Q6-SY2025` / `SY2026`) |

## 7. 次の窓に残るもの

再開するなら次が出発点になる。**本文書はそれを予定として書くものではない。**

- 未走 2 leaf: `Q6-SY2025@openalex` / `Q6-SY2026@openalex` (それぞれ 20 頁前後の見込み)。
- 独立 2 走目 53 本: `--checkpoint <bundle>/checkpoints/<ID>.json`
  (各 checkpoint の `canonical_runner_argv` が逐語の argv)。ただし §3 のとおり、日を隔てた 2 走目は
  不一致になる見込みが強い。**2 走目を続けるかどうかは裁定事項**であり、本走行は方針を変えていない。
- 裁定待ち: `declared_total_drift` の 2 leaf (`Q6-SY2014` / `Q6-SY2015`、4 窓目) と、本走行で増えた
  `second_pass_digest_mismatch` 5 leaf、条件 5 の 2 leaf。
- **checkpoint の argv は逐語で渡す。** `--run-id` を差し替えてはならない (4 窓目 §7)。
- 重複除去は bundle の証拠で行う。checkpoint 側の照合 key は `query_id` ではなく `leaf_query_id`。
- `resume_action` が `continue_cursor` の checkpoint は第 3 の再開経路である (4 窓目 §7)。
- loop の閾値を下げて残量を使い切るときは、計画順で先に来る初回取得の大きい leaf が自己施錠を
  招かないか、頁数で確かめる。

## 8. 母集合の外

窓 1〜4 と同じ。`docs/related-work/README.md` 7.7.4 の「母集合の外にあるもの」をそのまま引き継ぐ。
