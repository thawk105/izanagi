# [T-2090] 軸 1 OpenAlex — 新 epoch の 3 窓目の取得 (2026-09-07)

新 epoch `AX1-20260902-E1` の OpenAlex 取得を 3 窓目で進めた記録。
**未走 44 leaf のうち 31 本を起動し、29 本が pass 1 を終えた。未走は 13 leaf まで減った。**
最近年の 2 leaf (`Q3-SY2025`、`Q3-SY2026`) が条件 5 で落ち、再開点を持たない未完走が 2 件増えた。
独立 2 走目は 1 本も起動していない (無償枠が初回取得で尽きた)。

凍結した実行記録は `docs/related-work/claim-survey/2026-09-07-axis1-search-execution.md`。
2 窓目の記録は `output/insights/2026-09-05_t2090-axis1-openalex-window2/`、
1 窓目は `output/insights/2026-09-03_t2090-axis1-openalex-window1/`。

## 中身

| file | 中身 |
|---|---|
| `fetch-window3.jsonl` | 起動した 31 本の台帳 (key、state、reason_code、request_count、起動前残量、開始時刻)。1 行目は親の手動起動 |
| `launch-order.txt` | 起動順の key |
| `leaf-order.txt` | catalog の登録順の OpenAlex leaf 78 本 (aggregate 2 本を除いたもの) |
| `driver.py.txt` | 駆動 loop の逐語 (repo 外の使い捨て script。実装面ではない) |
| `driver-stdout.txt` | 駆動 loop の stdout |
| `manual-first.py.txt` | 観測更新のための手動 1 本起動の逐語 |
| `liveness-probe.py.txt` / `liveness-probe.txt` | 取得前の生死確認 (per-page=1、1 credit) の script と応答 header |
| `cond5-detail.txt` | 条件 5 で落ちた 2 leaf の頁ごとの申告総数と最終 distinct |
| `bundle-check.json` | 取得後の `tools/check_axis1_search.py bundle` の出力全文 |
| `mirror/` | 生 bundle の部分複製 (`pages` / `checkpoints` / `state` / `wal` / `manifest.json` / `MANIFEST.sha256`) |

## 生 bundle の所在

live bundle root (再開と検証はここで行う):
`/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (198 MB)

`manifest.json` の SHA-256 = `7fd6a7a2c95056e93e999a03dd331c6e5e53ca3b0a703f768863f9f68efbf462`
(2 窓目終了時は `99f06ae7…`)。

`mirror/` は `raw/` と `ledgers/` を除いた複製で、**単独では `verify_bundle` を通らない**
(checkpoint の `bundle_root` は上の絶対 path であり、manifest の path 集合は raw と ledgers を含む)。

## 何をしたか

### 1. 起動の条件

- cwd は登録 commit `4ec3eba04` を detach した木 (`git worktree add --detach`、repo 外の job dir)。
  登録検査 `tools/check_axis1_search.py registration` は `passed: true`。
- 生死確認: `GET /works?per-page=1` を 1 本 (11:35:29 JST)。`x-ratelimit-remaining=999`、
  `x-ratelimit-limit=1000`、`x-ratelimit-reset=77071` (翌 2026-09-08 09:00 JST)。**今窓は丸ごと空いていた。**
- 重複除去は台帳ではなく bundle の証拠で行った。初回取得は `pages/<ID>_p0.a01.json` の実在、
  2 走目は `ledgers/<ID>.pass2.*` の実在で「済み」とする。
- 優先順位は D1624 の「無償枠の窓は未走 leaf の初回取得に使う」に従い、未走 leaf を leaf 順で先に、
  2 走目 checkpoint を後に置いた。

### 2. 駆動 loop を回す前の 2 件の是正

**(a) 2 走目の重複除去が 1 件も効いていなかった。** 2 窓目の driver は checkpoint の `query_id` で
`ledgers/<ID>.pass2.*` を glob していたが、`query_id` は shard 親 (`AX1-20260902-E1-Q3@openalex`) で、
台帳の file 名は shard の leaf ID (`AX1-20260902-E1-Q3-SY1997@openalex`) で付く。正しい field は
`leaf_query_id`。2 窓目の時点では pass2 台帳が 1 件も無かったので実害が出ず、本窓の dry-run が
74 件 (正しくは 66 件) を計画したことで露見した。放置すれば完了済み 8 leaf の 2 走目を回し直していた。

**(b) 本窓で取ったばかりの leaf が同じ走行の 2 走目計画に入る。** 初回取得が checkpoint を書くので、
`second_pass.state` が `not_started` の新しい checkpoint が即座に 2 走目の候補になる。これは
**同日内の 2 走目**であり、間隔の可否は [T-2258] の未裁定事項なので、checkpoint の
`quota.observed_at_jst` が当日なら 2 走目の計画から外した。

**(c) `runtime.json` の持続観測は前窓 (9/5 13:11 JST、`remaining=189`) のまま**で、今窓の実値は
runner が 1 request 出すまで更新されない。2 窓目と同じく、閾値検査を緩めずに**正規 runner を 1 本だけ
手動起動**して観測を今窓の値 (959) に更新し、同じ loop を起動した。runner 自身の発行規範
(`remaining - 30 >= cost`) はこの間も変えていない。

### 3. 結果

| 区分 | 起動 | request | 結果 |
|---|---|---|---|
| 初回取得 (`Q3-SY2019`〜`Q3-SY2026`) | 8 | 51 | 6 本 `pass_complete`、2 本 `blocked_on_ruling` (条件 5) |
| 初回取得 (`Q6-SY1991`〜`Q6-SY2013`) | 23 | 30 | 全部 `pass_complete` |
| 独立 2 走目 | 0 | 0 | 予算が尽きて 1 本も起動していない |
| 合計 | 31 | 81 | 停止時の残量 189 (`Q6-SY2014` の手前) |

起動は 11:38:01〜11:44:07 JST。新しい checkpoint は `000031`〜`000059` の 29 本。

頁数は年と枝で大きく違う。`Q6` の年 shard は 1 頁 (2006 年まで) か 2 頁 (2007 年以降)、
`Q3` の最近年は `SY2019`〜`SY2023` が 4 頁、`SY2024` が 6 頁、`SY2025` が 9 頁、`SY2026` が 16 頁。
**`Q3-SY2026` 1 本だけで 16 request (160 credit) を使う。**

### 4. 条件 5 で落ちた 2 leaf — 申告総数は動かず、重複と欠落が同時に出た

`Q3-SY2025` と `Q3-SY2026` は `distinct_work_id_total_mismatch` で
`blocked_on_ruling` になり、**後継 checkpoint が書かれない** (条件 5 で落ちた既存 3 leaf と同じ)。

| leaf | 頁数 | 申告総数 (全頁で一定) | 返却 occurrences | distinct | 重複 | 申告に届かない分 |
|---|---|---|---|---|---|---|
| `Q3-SY2025` | 9 | 1678 | 1681 | 1676 | 5 | 2 |
| `Q3-SY2026` | 16 | 3034 | 3035 | 3031 | 4 | 3 |

- **申告総数は 1 leaf の取得 (数十秒) の全頁で 1 度も動かなかった。** 2 窓目の `Q3-SY1992` は
  2 日を隔てた 2 走目で申告総数ごと動いたが、本件は同一走行内なので別の現象である。
- 形は U11 (同じ work ID を頁境界で 2 回返しつつ総件数では 1 回と数える) に一致する。
  ただし**重複を除いても distinct が申告総数に 2〜3 件届かない**。重複だけでは説明が付かず、
  申告されながら 1 度も返らない ID が残る。D1331 の (a)「返却されなかった別 ID が実在するか」に
  関わる観測だが、snapshot 識別子が無いので機序は確定しない。
- D1623 は U11 に免除を与えず現契約どおり `未完走` とすると裁定済みであり、本走行はその裁定のとおりの
  結果になっている。**条件 5 は緩めていない。**
- **検査器の leaf 診断はこの 2 leaf を `leaf_page_evidence_missing` と報告する。** 独立 2 走を要する
  shard leaf なので `expected_passes` が `[1, 2]` になり、「pass 2 の証拠が無い」が先に立つ。
  走行時の理由 `distinct_work_id_total_mismatch` は台帳側にしか残らない。
  非 shard の `Q1` / `Q4` / `Q5` は `expected_passes` が `[1]` なので条件 5 が leaf 診断に出る。

### 5. 無償枠

| 項目 | 値 |
|---|---|
| `x-ratelimit-limit` | 1000 |
| 生死確認 | 1 request (per-page=1、1 credit) |
| 取得 | 81 request (per-page=200、810 credit) |
| 停止時の残量 | 189 (11:44 JST 台、reset → 翌 2026-09-08 09:00 JST) |
| 自己施錠 | 入っていない (`remaining >= 40` で終えた) |

駆動 loop は起動と起動の間に `state/runtime.json` の残量を読み、200 未満で新規起動を止めた。

## 検査器の出力 (取得後)

`tools/check_axis1_search.py bundle` は `bundle_validation_complete: true` /
`exact_identity_map: true` / `passed: false` / `reason_code: leaf_not_run` を返した (rc=2)。
`leaf_state_counts` は `complete: 8` / `incomplete_with_evidence: 4` /
`incomplete_without_complete_pass: 251`、`incomplete_checkpoint_counts` は
`present: 51` / `missing: 200` / `not_run: 198`。OpenAlex 78 leaf の内訳:

| 状態 | 件数 | 内訳 |
|---|---|---|
| `complete` | 8 | 2 窓目から変わらない (2 走目を 1 本も回していないため) |
| pass 1 完了・2 走目待ち (再開点あり) | 51 | checkpoint `000009`〜`000059` |
| 条件 5 で未完走 (再開点なし) | 3 | `Q1`、`Q4`、`Q5` |
| 2 走不一致で未完走 (再開点なし) | 1 | `Q3-SY1992` |
| 条件 5 で pass 1 が落ちた (再開点なし) | 2 | `Q3-SY2025`、`Q3-SY2026` |
| 未走 | 13 | `Q6-SY2014`〜`Q6-SY2026` |

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。**

## この wave が実装していないこと

1 窓目・2 窓目と同じ。窓またぎ設計 (U12、[T-2259])、証拠時点の束縛 (U13、[T-2260])、条件 5 の扱い
([T-2258]、D1564 / D1623 で現状維持)、`axis_complete` の production 経路 ([T-2323]) はいずれも触っていない。
repo の実装面の差分は 0。

## 次の窓の再開情報

- **未走 13 leaf:** `--query-id AX1-20260902-E1-Q6-SY2014@openalex` 〜 `Q6-SY2026@openalex`。
  1 leaf 2 頁前後なので約 26 request で終わる見込み。
- **2 走目 51 本:** `--checkpoint <bundle>/checkpoints/0000{09..59}.json`
  (各 checkpoint の `canonical_runner_argv` が逐語の argv)。1 窓には収まらないので複数窓に分かれる。
  **`000031`〜`000059` は本窓 (9/7) に pass 1 を取ったものなので、次の窓 (9/8 以降) なら同日内にならない。**
- 重複除去は bundle の証拠で行う。checkpoint 側の key は `query_id` ではなく **`leaf_query_id`** (本 README §2a)。
- 駆動 loop を最初に走らせる前に `runtime.json` の観測が前窓のものであることを織り込む (§2c)。
  生死確認は per-page=1 なら 1 credit。
- 再開点の無い 6 leaf (`Q1`、`Q4`、`Q5`、`Q3-SY1992`、`Q3-SY2025`、`Q3-SY2026`) は再取得しか経路が無い。
  `Q3-SY2026` は 16 request、`Q3-SY2025` は 9 request かかり、再取得しても索引が同じ形なら再び落ちる。
