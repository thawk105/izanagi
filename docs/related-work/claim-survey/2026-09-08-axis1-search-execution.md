# 2026-09-08 — 軸 1 検索の実行記録 — 新 epoch `AX1-20260902-E1` の OpenAlex 4 窓目 (打ち切り)

**これは実行記録であって、登録でも改訂でもない。** 登録の正本は
`2026-09-02-axis1-search-amendment.md`、query program の正本は
`2026-09-02-axis1-search-catalog.json`、1 窓目の実行記録は
`2026-09-03-axis1-search-execution.md`、2 窓目は `2026-09-05-axis1-search-execution.md`、
3 窓目は `2026-09-07-axis1-search-execution.md` である。
本文書は凍結物であり、後から上書きしない。内容を更新したいときは新しい日付の実行記録を足す。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。**

**本走行をもって、窓ごとの継続取得を打ち切った。** 打ち切りはユーザー裁定であり、
理由と射程は decisions 台帳の該当エントリが正本である。以後の窓は回さない。
既存の生証拠は破棄せず、同じ登録 commit から再開できる状態で残す。

## 0. この走行の身元

| 項目 | 値 |
|---|---|
| 作成日 | 2026-09-08 (JST) |
| 登録 epoch | `AX1-20260902-E1` |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` (1〜3 窓目と同じ。main の祖先を detach した木を cwd にした) |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| 文献 cutoff | `2026-12-31` |
| run ID | `t2090-openalex-20260908a` |
| 索引 | OpenAlex のみ (arXiv / DBLP は本 epoch でまだ 1 request も出していない) |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (1〜3 窓目と同じ root、207 MB) |
| bundle manifest SHA-256 (走行後) | `f3aeb91f823d2820d289668cbc85b8a3a0b51ca44608d46fc135847b48da0035` |
| bundle manifest SHA-256 (走行前) | `7fd6a7a2c95056e93e999a03dd331c6e5e53ca3b0a703f768863f9f68efbf462` |
| 逐語と部分 mirror | `output/insights/2026-09-08_t2090-axis1-openalex-window4/` |

登録検査 (`tools/check_axis1_search.py registration`) は detach した木で `passed: true` を返した。

## 1. 何を起動したか

**本走行は「4 窓目」ではなく、3 窓目の窓に残っていた無償枠の消化である。**
3 窓目は残量 189 で停止しており、その窓のリセットは 2026-09-08 09:00 JST だった。
リセットを待たずに残量を使い切り、リセット後の窓は回さずに打ち切った。

| 区分 | 起動 | request | 結果 |
|---|---|---|---|
| 初回取得 (`--query-id`) | 4 | 12 | 2 本 `pass_complete`、1 本 `blocked_on_ruling`、1 本 `paused_quota` |
| 中断 pass 1 の再開 (`--checkpoint`) | 1 | 2 | 1 本 `blocked_on_ruling` |
| 独立 2 走目 | 0 | 0 | 起動していない |
| 合計 | 5 | 14 | 残量 189 → 57 で停止 |

起動は 00:46:54〜00:59:34 JST。生死確認の直接取得が別に 3 request (`per-page=1`、各 1 credit)。

| 段 | leaf | state | reason_code | request |
|---|---|---|---|---|
| 初回 | `Q6-SY2014` | `blocked_on_ruling` | `declared_total_drift` | 3 |
| 初回 | `Q6-SY2015` | `paused_quota` | `http_status_429` | 2 |
| 再開 | `Q6-SY2015` | `blocked_on_ruling` | `declared_total_drift` | 2 |
| 初回 | `Q6-SY2016` | `pass_complete` | — | 3 |
| 初回 | `Q6-SY2017` | `pass_complete` | — | 4 |

新しい checkpoint は `000060`〜`000062` の 3 本。

## 2. `declared_total_drift` — 本 epoch で初めて出た落ち方

窓 1〜3 で観測された条件 5 の不成立は `distinct_work_id_total_mismatch` であり、
**申告総数は 1 走の全頁で動かないのに distinct がそこへ届かない**という形だった。
本走行で出た `declared_total_drift` は**形が逆**である。

| leaf | 頁ごとの申告総数 | 返却 occurrences | distinct | 重複 | 結果 |
|---|---|---|---|---|---|
| `Q6-SY2014` | 418 → 417 → 417 | 417 | 417 | 0 | `blocked_on_ruling` |
| `Q6-SY2015` | 492 → (429) → 491 → 491 | 491 | 491 | 0 | `blocked_on_ruling` |
| `Q6-SY2016` | 554 → 554 → 554 | 554 | 554 | 0 | `pass_complete` |
| `Q6-SY2017` | 678 → 678 → 678 → 678 | 678 | 678 | 0 | `pass_complete` |

- **申告総数そのものが、1 leaf の取得 (数十秒) の最中に 1 件減った。** 落ちた 2 本とも減り幅は 1 である。
- **返却データ自体は最終の申告総数と完全に整合している。** 重複 0、不足 0、distinct == 最終 `declared_total`。
  不整合は頁 0 の header だけにある。
- 対照として、同じ枝の隣接年 (`SY2016` / `SY2017`) は申告総数が全頁で一定であり `pass_complete` になった。
  **走行時刻も枝も同じで、年 shard だけが違う。**
- D1331 の (a)「返却されなかった別 ID が実在するか」に対して、本件は**否**の側の材料である
  (返却は最終申告総数を満たしている)。ただし snapshot 識別子が無いので機序は確定しない。
- **条件は緩めていない。** 取得器は 2 本とも `blocked_on_ruling` にしており、本走行はその判定を
  そのまま記録している。
- 検査器の leaf 診断はこの 2 本を `leaf_page_evidence_missing` と報告する。独立 2 走を要する
  shard leaf なので `expected_passes` が `[1, 2]` になり、「pass 2 の証拠が無い」が先に立つ。
  走行時の理由 `declared_total_drift` は台帳側にしか残らない (窓 3 と同じ構造)。

## 3. HTTP 429 は枠の枯渇ではなく一過性だった

`Q6-SY2015` の 1 回目の起動は残量 158 で 429 を受けた。取得器が保存した応答本文は次のとおり。

```json
{"error":"Rate limit exceeded",
 "message":"Anonymous search is temporarily rate-limited while the search cluster is under
            elevated load. Please retry in 10s, or use a free API key for uninterrupted
            access: https://openalex.org/rest-api.",
 "retryAfter":10}
```

- 予備枠 (30) をはるかに上回る残量で起きており、**枠の枯渇ではない**。
  70 秒後に同じ endpoint が HTTP 200 と残量 147 を返した。
- 取得器は 429 を受けた attempt を捨てず、`_p1.a01.json` (`actual_count=0`、
  `failure.reason_code=status_not_200`) として証拠に残し、再開後の成功を `_p1.a02.json` に置いた。
- 取得器は登録された `Accept: application/json` のみを送る (`only the registered Accept header is
  permitted`)。**匿名アクセスである。**応答が案内する無料 API key は、送信 request を変えるため
  意味的 amendment (新 epoch・全枝の再実行) を伴う。本走行では採らなかった。

## 4. 無償枠の扱い

| 項目 | 値 |
|---|---|
| `x-ratelimit-limit` | 1000 |
| 走行開始時の残量 | 189 (3 窓目の残り) |
| 生死確認 | 3 request (`per-page=1`、各 1 credit) |
| 取得 | 14 request (`per-page=200`、各 10 credit) |
| 停止時の残量 | 57 |
| リセット | 2026-09-08 09:00:00 JST (実測 header で 2 度確認) |
| 自己施錠 | 入っていない |

**残量 57 で意図的に止めた。** 残量が 40 を切ると取得器自身の発行規範 (`remaining - 30 >= cost`)
により 1 request も出せなくなり、次の窓で持続観測を更新する手動 1 本すら拒否されて自己施錠に入る。
57 ならその手が使える状態で残る。

## 5. この走行が実装していないこと

窓またぎ設計 (U12)、証拠時点の束縛 (U13)、条件 5 の扱い (D1564 / D1623 で現状維持)、
`axis_complete` の production 経路はいずれも触っていない。repo の実装面の差分は 0 である。
駆動 loop は repo 外の使い捨て script であり、逐語を insight に `.txt` で置いた。

## 6. 検査器の出力

`tools/check_axis1_search.py bundle` は
`bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
`reason_code: leaf_not_run` を返した (rc=2)。全文は
`output/insights/2026-09-08_t2090-axis1-openalex-window4/bundle-check.json`。

OpenAlex 78 leaf の内訳:

| 状態 | 件数 |
|---|---|
| `complete` (独立 2 走まで完了) | 8 |
| pass 1 完了・2 走目待ち (再開点あり) | 53 |
| 条件 5 で未完走 (再開点なし) | 3 |
| 2 走不一致で未完走 (再開点なし) | 1 |
| 条件 5 で pass 1 が落ちた (再開点なし) | 2 |
| **`declared_total_drift` で pass 1 が落ちた (再開点なし)** | **2** |
| 未走 | 9 |

## 7. 打ち切り後に残るもの

再開するなら次が出発点になる。**本文書はそれを予定として書くものではない。**

- 未走 9 leaf: `Q6-SY2018@openalex` 〜 `Q6-SY2026@openalex`。
- 独立 2 走目 53 本: `--checkpoint <bundle>/checkpoints/<ID>.json`
  (各 checkpoint の `canonical_runner_argv` が逐語の argv)。
- **checkpoint の argv は逐語で渡す。** 検査器は証拠を checkpoint 自身の `run_id` へ束縛するため
  (`validator.py` の `request["target_run_id"] != checkpoint["run_id"]` と
  `ledger.get("run_id") != checkpoint["run_id"]`)、`--run-id` を差し替えてはならない。
- 重複除去は bundle の証拠で行う。checkpoint 側の照合 key は `query_id` ではなく `leaf_query_id`。
- `resume_action` が `continue_cursor` の checkpoint は、初回取得でも独立 2 走目でもない
  **第 3 の再開経路**である。page 証拠と `start_independent_pass` の 2 条件だけで計画を組むと
  この leaf が計画から落ちる。

## 8. 母集合の外

窓 1〜3 と同じ。`docs/related-work/README.md` 7.7.4 の「母集合の外にあるもの」をそのまま引き継ぐ。
