# 2026-09-17 (b) — 軸 1 検索の実行記録 — 新 epoch `AX1-20260902-E1` の OpenAlex 6 窓目 (未走 2 leaf の初回取得)

**これは実行記録であって、登録でも改訂でもない。** 登録の正本は
`2026-09-02-axis1-search-amendment.md`、query program の正本は
`2026-09-02-axis1-search-catalog.json`、1 窓目の実行記録は
`2026-09-03-axis1-search-execution.md`、2 窓目は `2026-09-05-axis1-search-execution.md`、
3 窓目は `2026-09-07-axis1-search-execution.md`、4 窓目 (残量消化と打ち切り) は
`2026-09-08-axis1-search-execution.md`、5 窓目 (打ち切り後の再開) は
`2026-09-17-axis1-search-execution.md` である。同日 2 件目なので file 名に `b` を付けた
(`2026-09-03b-axis1-cond5-confirmations.md` と同じ規約)。
本文書は凍結物であり、後から上書きしない。内容を更新したいときは新しい日付の実行記録を足す。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。**

**本走行は、D2095 項 3 (未走 2 leaf の初回取得は、独立 2 走目の扱いの裁定と独立に取得できる) に従う 6 窓目である。**
D1760 の残余射程 (「`RW1` 据え置き・世界の不在を主張しない・既存証拠の bytes 不変・同じ登録 commit と
epoch を引き継ぐ・arXiv / DBLP へ request を出さない」) はそのまま維持している。

## 0. この走行の身元

| 項目 | 値 |
|---|---|
| 作成日 | 2026-09-17 (JST) |
| 登録 epoch | `AX1-20260902-E1` |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` (1〜5 窓目と同じ。5 窓目が detach した木を cwd にした) |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| 文献 cutoff | `2026-12-31` |
| run ID (初回取得) | `t2035-openalex-20260917b` (同日 2 窓目) |
| 索引 | OpenAlex のみ (arXiv / DBLP は本 epoch でまだ 1 request も出していない) |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (1〜5 窓目と同じ root、399 MB) |
| bundle manifest SHA-256 (走行後) | `06fbef369ed0bfb071e896d65ee1c1a2321709f5cb8cc787374da7aafbed21dd` |
| bundle manifest SHA-256 (走行前) | `a6a42514e6d52c4e90243e706295f3ce215f4f5c91c0ad100a7d90f32d22e2a4` (5 窓目の走行後値と一致) |
| 逐語と部分 mirror | `output/insights/2026-09-17/t2035-axis1-openalex-window6/` |

登録検査 (`tools/check_axis1_search.py registration`) は detach した木で `passed: true` を返した。

## 1. 何を起動したか

5 窓目終了時の残りは未走 2 leaf (`Q6-SY2025` / `Q6-SY2026`) と独立 2 走目 53 本、裁定待ち 4 leaf
(`Q6-SY2014` / `SY2015` は `declared_total_drift`、`Q6-SY2021` / `SY2024` は条件 5) だった。本走行は
未走 2 leaf だけを対象にし、駆動 loop を使わず、親が正規 runner (`tools/run_axis1_search.py`) の argv を
5 窓目の dry-run の逐語で 1 本ずつ起動した (`--run-id` だけ本窓の値)。2 走目 53 本と裁定待ち 4 leaf は
起動していない。

| 区分 | 起動 | request | 結果 |
|---|---|---|---|
| 初回取得 (`--query-id`)、親の手動 | 1 | 51 | `Q6-SY2025` が `blocked_on_ruling` (条件 5) |
| 初回取得、起動せず | 0 | 0 | `Q6-SY2026` は 106 頁で 1 窓に収まらない (§3) |
| 合計 | 1 | 51 | 残量 999 → 489 |

起動は 21:36:00〜21:39:35 JST。生死確認 (無 filter、`per-page=1`) が別に 1 request (1 credit)、
`Q6-SY2026` の件数 probe (登録 filter、`per-page=1`) が別に 1 request (**10 credit**) で、走行後の残量は 479。

| 段 | leaf | 頁 | state | reason_code |
|---|---|---|---|---|
| 初回 (手動) | `Q6-SY2025` | 51 | `blocked_on_ruling` | `distinct_work_id_total_mismatch` |
| (起動せず) | `Q6-SY2026` | 106 (件数 probe) | — | — |

新しい checkpoint はない (`blocked_on_ruling` は再開点を残さない)。

## 2. `Q6-SY2025` — 申告総数は一定、頁境界の重複 25、不足 12 件

| leaf | 申告総数 (全 51 頁一定) | 返却 occurrences | distinct | 頁内重複 | 頁境界を跨ぐ重複 | 不足 | 結果 |
|---|---|---|---|---|---|---|---|
| `Q6-SY2025` | 10065 | 10078 | 10053 | 0 | 25 | **12** | `blocked_on_ruling` |

- 申告総数は 51 頁すべてで一定であり、`declared_total_drift` は出ていない。
- 5 窓目の `Q6-SY2021` / `SY2024` (不足 1 件) と同じ条件 5 の形で、規模が大きい。申告総数は 2024 年の
  4669 の 2.2 倍、頁境界を跨ぐ重複は 25 occurrence、不足は 12 件。5 窓目の見込み「20 頁前後」は外れた
  (最近年の伸びは 2024 → 2025 で頁数 24 → 51)。
- **条件は緩めていない。** 取得器は `blocked_on_ruling` にしており、本走行はその判定をそのまま記録している。
- 検査器の leaf 診断は窓 3〜5 と同じく `leaf_page_evidence_missing` と報告する (`expected_passes` が `[1, 2]` で
  pass 2 の欠落が先に立つ)。走行時の理由 `distinct_work_id_total_mismatch` は台帳側にしか残らない。

## 3. `Q6-SY2026` — 106 頁で 1 窓に収まらず、起動すると bundle が自己施錠する

`Q6-SY2025` が見込みを大きく超えたため、`Q6-SY2026` は起動前に頁数を実測した。登録 filter と同じ request を
`per-page=1` で 1 本投げる (証拠外、取得器を通さない) と `meta.count = 21040` → 200 件/頁で **106 頁 = 1060 credit**。

- 取得器の発行規範は各 request の前に「持続観測の残量 − 30 ≥ 10」を見るだけで、`x-ratelimit-reset` を見ない
  (登録文書の U12 が「1 つの bundle が枠を使い切ると二度と request を発行できない」と登録した既知の穴)。
  残量 R から施錠せずに出せるのは ⌊(R − 40) / 10⌋ request (満量 1000 で 96、生死確認後の 999 で 95) であり、
  106 頁の leaf は**どの窓からでも**途中で `paused_quota` (`continue_cursor`) に入り、持続観測が 40 未満のまま
  固定される。以後は窓がリセットしても観測を更新する 1 本が出せず、**bundle 全体が request を発行できなくなる**。
  残量 479 から起動しても同じ (44 頁で止まり残量 39)。CLI に頁数上限はない。
- したがって本走行は起動していない。取得には窓またぎ設計 (U12、取得器 = 登録 tool の変更) か catalog 側の
  再分割 (amendment、新 epoch) が要り、どちらも本走行の範囲外である。**D2095 項 3 の「1 窓で収まる」は
  見込みであり、本走行の実測で覆った。** 扱いは D2095 の裁定パッケージへ新事実として返す (§7)。
- 件数 probe は 10 credit だった (`x-ratelimit-credits-used: 10`)。無 filter の生死確認 (1 credit) と違い、
  filter 付き検索は `per-page` に関係なく 10 credit である。

## 4. 無償枠の扱い

| 項目 | 値 |
|---|---|
| `x-ratelimit-limit` | 1000 |
| 走行開始時の残量 | 999 (生死確認 1 本の後。5 窓目以降 1 request も出しておらず、窓は満量だった) |
| 生死確認 | 1 request (無 filter、`per-page=1`、1 credit) |
| 取得 | 51 request (`per-page=200`、各 10 credit) |
| 件数 probe | 1 request (登録 filter、`per-page=1`、10 credit) |
| 停止時の残量 | 479 (取得器の持続観測は runner の最終値 489。件数 probe は取得器の外なので載らない) |
| リセット | 2026-09-18 09:00:00 JST (実測 header で 2 度確認: 21:35 の `reset=41063`、21:41 の `reset=40721`) |
| 自己施錠 | 入っていない |

残量 479 で止め、次の窓で持続観測を更新する手動 1 本が出せる状態を残した。HTTP 429 は本走行では 1 度も出ていない。

## 5. この走行が実装していないこと

窓またぎ設計 (U12)、証拠時点の束縛 (U13)、条件 5 の扱い (D1564 / D1623 で現状維持)、
`axis_complete` の production 経路はいずれも触っていない。repo の実装面の差分は 0 である。駆動 loop も
書いていない。証拠の射影に使った読み取りのみの使い捨て script は repo 外で実行し、逐語を insight に
`.txt` で置いた。

## 6. 検査器の出力

`tools/check_axis1_search.py bundle` は
`bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
`reason_code: leaf_not_run` を返した (rc=2)。全文は
`output/insights/2026-09-17/t2035-axis1-openalex-window6/bundle-check.json`。

OpenAlex 78 leaf の内訳 (5 窓目終了時 → 本走行終了時):

| 状態 | 5 窓目 | 本走行 |
|---|---|---|
| `complete` (独立 2 走まで完了) | 8 | 8 |
| pass 1 完了・2 走目待ち (再開点あり) | 53 | 53 |
| 条件 5 で未完走 (再開点なし、`Q1` / `Q4` / `Q5`) | 3 | 3 |
| 2 走不一致で未完走 (再開点なし) | 6 | 6 |
| 条件 5 で pass 1 が落ちた (再開点なし) | 4 | **5** (+`Q6-SY2025`) |
| `declared_total_drift` で pass 1 が落ちた (再開点なし、裁定待ち) | 2 | 2 |
| 未走 | 2 | **1** (`Q6-SY2026`、1 窓に収まらない) |

## 7. 次の窓に残るもの

再開するなら次が出発点になる。**本文書はそれを予定として書くものではない。**

- 未走 1 leaf: `Q6-SY2026@openalex` (106 頁、1060 credit)。**現行の取得器では起動できない** (§3)。扱いは D2095 の
  裁定パッケージへ足す — (a) 未走のまま置き、軸 1 の材料は 77 leaf 分で「限定付き」とする (成熟度は元々 `RW1`)、
  (b) U12 の窓またぎ設計を実装する (取得器 = 登録 tool の変更、D1207 の意味的 amendment に当たるかの判定を含む)、
  (c) catalog 側で `SY2026` を半期などに再分割する (amendment、新 epoch)。本走行の推奨は (a)。
- 条件 5 で落ちた `Q6-SY2025` は、D2095 項 2 の「落ちた leaf」に加わる (据え置きの推奨は変わらない)。
- 独立 2 走目 53 本と裁定待ち leaf は 5 窓目 §7 のまま。
- 大きい leaf は起動前に件数 probe (登録 filter、`per-page=1`、10 credit) で頁数を確かめる。「残量 ≥ 40 + 10 × 頁数」
  の頁数を見込みで置くと、U12 の自己施錠を踏む。

## 8. 母集合の外

窓 1〜5 と同じ。`docs/related-work/README.md` 7.7.4 の「母集合の外にあるもの」をそのまま引き継ぐ。
