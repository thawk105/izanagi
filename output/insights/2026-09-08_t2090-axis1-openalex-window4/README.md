# [T-2090] 軸 1 OpenAlex — 3 窓目の残量を消化し、窓ごとの継続取得を打ち切った (2026-09-08)

新 epoch `AX1-20260902-E1` の OpenAlex 取得の記録。
**5 起動 / 14 request で 2 leaf の pass 1 を足し、そこで窓ごとの継続取得を打ち切った。**
打ち切りはユーザー裁定であり、理由と射程は decisions 台帳の該当エントリが正本である。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。以後の窓は回さない。**

凍結した実行記録は `docs/related-work/claim-survey/2026-09-08-axis1-search-execution.md`。
3 窓目は `output/insights/2026-09-07_t2090-axis1-openalex-window3/`、
2 窓目は `output/insights/2026-09-05_t2090-axis1-openalex-window2/`、
1 窓目は `output/insights/2026-09-03_t2090-axis1-openalex-window1/`。

## 中身

| file | 中身 |
|---|---|
| `driver.py.txt` | 駆動 loop の逐語 (repo 外の使い捨て script。実装面ではない)。Codex `role=author` の実装子が書き、親のレビューで 2 巡 fix した |
| `driver-dryrun.txt` | 打ち切り前に親が実 bundle へ通した `--dry-run` の全文 (計画 63 件: 再開 1 / 未走 11 / 2 走目 51) |
| `driver-stdout-a1.txt` / `driver-stdout-a2.txt` | 駆動 loop の stdout (1 回目は 429 で停止、2 回目が本番) |
| `fetch-window4a.jsonl` | 起動 5 本の台帳 (key、段、state、reason_code、request 数、起動前残量、時刻) |
| `launch-order-a.txt` | 起動順の key |
| `leaf-order.txt` | catalog の登録順の OpenAlex leaf 78 本 |
| `declared-total-detail.txt` | 起動した 4 leaf の**頁ごとの申告総数・実要素数・重複数** |
| `http-429-body.json` | OpenAlex が 429 で返した応答本文の逐語 |
| `liveness-probe-1.txt` / `liveness-probe-2.txt` | 取得前後の rate limit header の逐語 |
| `bundle-check.json` | 打ち切り時点の `tools/check_axis1_search.py bundle` の出力全文 |
| `mirror/` | 生 bundle の部分複製 (`checkpoints` / `state` / `manifest.json`) |

## 生 bundle の所在

live bundle root (再開と検証はここで行う):
`/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (207 MB)

`manifest.json` の SHA-256 = `f3aeb91f823d2820d289668cbc85b8a3a0b51ca44608d46fc135847b48da0035`
(走行前は `7fd6a7a2…`)。

`mirror/` は `raw/` `pages/` `ledgers/` を除いた複製で、**単独では `verify_bundle` を通らない**
(checkpoint の `bundle_root` は上の絶対 path であり、manifest の path 集合は除いた 3 つを含む)。
窓 3 の mirror が `pages` を含んでいたのに対し、本 mirror は含まない。

## 何をしたか

### 1. 窓はまだ開いていなかった

本 wave の起動時 (00:12 JST) の時点で、3 窓目の窓のリセットは **2026-09-08 09:00:00 JST** であり、
残量 189 が未使用のまま残っていた。**リセットで捨てられる残量なので、待たずに先に使い切った。**
リセットは header で 2 度確認した (00:46 の `reset=29613`、00:48 の `reset=29464`)。

### 2. 駆動 script は Codex の実装子に書かせた

窓 1〜3 は親が直接書き「[T-317] の凍結境界」を根拠にしていたが、**[T-317] は未裁定の択一**であり、
親自身の推奨は (b)「例外を作らず親は必ず子に書かせる」だった。D95 決定 2 は「場所を問わない
Python 資材」を実装面と定める。本 wave は (b) に従った。

**その結果、親が書いていたら入っていたはずの欠陥が 3 件出た。うち 2 件は実データで裏が取れた。**

| # | 所見 | 裏取り |
|---|---|---|
| 1 | 段 B が checkpoint の argv の `--run-id` を書き換えていた | 検査器が証拠を checkpoint 自身の `run_id` へ束縛する (`validator.py` の 2 箇所) ことと、既存 12 本の pass2 台帳がすべて元の run ID を持つことを現物で確認 |
| 2 | 429 で中断した leaf がどの段にも掛からず計画から消える | **実データで発火した。** `Q6-SY2015` が `continue_cursor` の checkpoint を残したが、段 A は page 証拠で飛ばし段 B は `start_independent_pass` しか見ないため、両方から落ちていた |
| 3 | 一過性の 429 で loop 全体が止まる | **実データで発火した。** 残量 158 で 429、その 70 秒後に同じ endpoint が HTTP 200 を返した |

所見 2 の修正 (段 A0 = `continue_cursor` の再開) は、直後の走行で実際に `Q6-SY2015` を拾って完走させた。
台帳の `A0` の行がその証拠である。

### 3. 結果

| 段 | leaf | state | reason_code | request |
|---|---|---|---|---|
| A | `Q6-SY2014` | `blocked_on_ruling` | `declared_total_drift` | 3 |
| A | `Q6-SY2015` | `paused_quota` | `http_status_429` | 2 |
| A0 | `Q6-SY2015` (再開) | `blocked_on_ruling` | `declared_total_drift` | 2 |
| A | `Q6-SY2016` | `pass_complete` | — | 3 |
| A | `Q6-SY2017` | `pass_complete` | — | 4 |

残量 189 → 57。**57 で意図的に止めた** — 40 を切ると取得器の発行規範 (`remaining - 30 >= cost`) で
1 request も出せなくなり、持続観測を更新する手すら塞がる。

### 4. `declared_total_drift` — 本 epoch で初めて出た落ち方

| leaf | 頁ごとの申告総数 | 返却 | distinct | 重複 | 結果 |
|---|---|---|---|---|---|
| `Q6-SY2014` | 418 → 417 → 417 | 417 | 417 | 0 | `blocked_on_ruling` |
| `Q6-SY2015` | 492 → (429) → 491 → 491 | 491 | 491 | 0 | `blocked_on_ruling` |
| `Q6-SY2016` | 554 で一定 | 554 | 554 | 0 | `pass_complete` |
| `Q6-SY2017` | 678 で一定 | 678 | 678 | 0 | `pass_complete` |

**申告総数そのものが、1 回の取得の最中に 1 件減った。**窓 1〜3 の条件 5
(`distinct_work_id_total_mismatch`、申告総数は動かず distinct が届かない) とは**形が逆**である。
返却データ自体は最終の申告総数と完全に整合しており (重複 0・不足 0)、
食い違うのは頁 0 の header だけである。同じ枝の隣接年は一定で完走した。

**条件は緩めていない。** 取得器の `blocked_on_ruling` をそのまま記録している。

### 5. 打ち切りの判断

**この観測は、打ち切りの判断そのものを補強する側の材料になった。**
完走条件は「cursor 終端までの distinct を `meta.count` と照合する」ことに依存しているが、
その `meta.count` が数秒の取得の最中に動く。「全件を取り切った」という土台が見た目ほど安定していない。

打ち切りの費用対効果の議論と却下した選択肢は decisions 台帳の該当エントリが正本である。
ここには書かない。

## 打ち切り時点の状態 (OpenAlex 78 leaf)

| 状態 | 件数 |
|---|---|
| `complete` (独立 2 走まで完了) | 8 |
| pass 1 完了・2 走目待ち (再開点あり) | 53 |
| 条件 5 で未完走 (再開点なし) | 3 |
| 2 走不一致で未完走 (再開点なし) | 1 |
| 条件 5 で pass 1 が落ちた (再開点なし) | 2 |
| `declared_total_drift` で pass 1 が落ちた (再開点なし) | 2 |
| 未走 | 9 (`Q6-SY2018` 〜 `Q6-SY2026`) |

検査器は `bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
`reason_code: leaf_not_run` を返した (rc=2)。

## この wave が実装していないこと

窓またぎ設計 (U12)、証拠時点の束縛 (U13)、条件 5 の扱い (D1564 / D1623 で現状維持)、
`axis_complete` の production 経路はいずれも触っていない。**repo の実装面の差分は 0。**

## 再開するなら

**予定ではない。**将来必要になったときの出発点として書き残す。

- 未走 9 leaf と 2 走目 53 本。生証拠は上の root にそのまま残る。
- **checkpoint の argv は逐語で渡す** (所見 1)。`--run-id` を差し替えると検査器に落とされる。
- **`continue_cursor` の checkpoint は第 3 の再開経路である** (所見 2)。page 証拠と
  `start_independent_pass` の 2 条件だけで計画を組むと落ちる。
- 重複除去の照合 key は `query_id` ではなく `leaf_query_id`。
- 一過性の 429 は再計画して待てば通る (所見 3)。
