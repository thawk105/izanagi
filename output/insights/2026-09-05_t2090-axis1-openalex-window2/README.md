# [T-2090] 軸 1 OpenAlex — 新 epoch の 2 窓目の取得 (2026-09-05)

新 epoch `AX1-20260902-E1` の OpenAlex 取得を 2 窓目で再開した記録。
**独立 2 走目 8 本のうち 7 本が完走し、初回取得を 22 leaf 足した。未走は 44 leaf。**
2 走目で 1 leaf (`Q3-SY1992`) が「2 日後の 2 走目で索引に 1 件増えて不一致」になった。

凍結した実行記録は `docs/related-work/claim-survey/2026-09-05-axis1-search-execution.md`。
1 窓目の記録は `output/insights/2026-09-03_t2090-axis1-openalex-window1/` と
`docs/related-work/claim-survey/2026-09-03-axis1-search-execution.md`。

## 中身

| file | 中身 |
|---|---|
| `fetch-window2.jsonl` | 起動した 30 本の台帳 (key、state、reason_code、request_count、起動前残量、開始時刻)。1 行目は親の手動起動 |
| `launch-order.txt` | 起動順の key (checkpoint 8 本 → leaf ID 22 本) |
| `driver.py.txt` | 駆動 loop の逐語 (repo 外の使い捨て script。実装面ではない) |
| `driver-stdout.txt` | 駆動 loop の stdout |
| `liveness-probe.txt` | 取得前の生死確認 1 request の応答 header (per-page=1、1 credit) |
| `second-pass-comparison.txt` / `.py.txt` | 2 走目 8 leaf の pass 1 と pass 2 の work ID 集合と順序の比較 |
| `bundle-check.json` | 取得後の `tools/check_axis1_search.py bundle` の出力全文 |
| `mirror/` | 生 bundle の部分複製 (`pages` / `checkpoints` / `state` / `wal` / `manifest.json` / `MANIFEST.sha256`) |

## 生 bundle の所在

live bundle root (再開と検証はここで行う):
`/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (143 MB)

`manifest.json` の SHA-256 = `99f06ae73f9749fc1d0b32cf92ae0a989c0abe3a5e6805fd98004369e00e3057`
(1 窓目終了時は `ff25f09a…`。2 窓目の取得で更新された)。

`mirror/` は `raw/` と `ledgers/` を除いた複製で、**単独では `verify_bundle` を通らない**
(理由は 1 窓目の README と同じ: checkpoint の `bundle_root` は上の絶対 path であり、
manifest の path 集合は raw と ledgers を含む)。取得完了時に bundle 全体を commit する方針は変えていない。

## 何をしたか

### 1. 起動の条件

- cwd は登録 commit `4ec3eba04` を detach した木 (`git worktree add --detach`、repo 外の job dir)。
  登録検査 `tools/check_axis1_search.py registration` は `passed: true`。
- 生死確認: `GET /works?per-page=1` を 1 本 (12:49 JST)。`x-ratelimit-remaining=999`、
  `x-ratelimit-reset=72643` (翌 09:00 JST)、`credits-used=1`。**per-page=1 の request は 1 credit、
  per-page=200 は 10 credit で、消費は頁の大きさに比例する** (前窓の記録は 200 頁の値だけを見ていた)。
- 重複除去は **台帳 (jsonl) ではなく bundle の証拠**で行った。初回取得は
  `pages/<ID>_p0.a01.json` の実在、2 走目は `ledgers/<ID>.pass2.*` の実在で「済み」とする。
  1 窓目の台帳には `Q3-SPRE1991` (5 頁、checkpoint 000001) が無かった (loop の前に手動起動されていた) ので、
  台帳だけで除去すると再走する。dry-run で 74 起動 (2 走目 8 + 未走 66) を確認してから走らせた。
- 残量は起動と起動の間に `state/runtime.json` から読み、200 未満で新規起動を止めた。

### 2. 駆動 loop の 1 回目は前窓の観測で止まった

1 回目の起動は 1 本も投げずに停止した。`runtime.json` の持続観測は前窓 (9/3 02:43 JST) の
`remaining=60` のままで、今窓の実値 (999) は runner が 1 request 出すまで更新されないためである。
閾値検査を緩めずに解くため、**正規 runner で checkpoint 000001 の 2 走目を 1 本だけ手動起動**して
観測を今窓の値 (949) に更新し、閾値検査はそのままの loop を再起動した。
runner 自身の発行規範 (`remaining - 30 >= cost`) はこの間も変えていない。

### 3. 結果

| 区分 | 起動 | request | 結果 |
|---|---|---|---|
| 独立 2 走目 (checkpoint 000001〜000008) | 8 | 12 | 7 本 `branch_complete`、`Q3-SY1992` が `blocked_on_ruling` / `second_pass_digest_mismatch` |
| 初回取得 (`Q3-SY1997`〜`Q3-SY2018`) | 22 | 69 | 全部 `pass_complete` (checkpoint 000009〜000030) |
| 合計 | 30 | 81 | 停止時の残量 189 (`Q3-SY2019` の手前) |

1997 年以降の年 shard は 1 頁に収まらず、2002 年以降は 3〜4 頁 (3〜4 request) ある。
未走 44 leaf (`Q3-SY2019`〜`SY2026` の 8、`Q6-SY1991`〜`SY2026` の 36) は次の窓へ持ち越す。

### 4. 独立 2 走目の照合 — 登録第 2 走の安定性の初観測

| leaf | pass 1 distinct | pass 2 distinct | 集合 | 順序 | 判定 |
|---|---|---|---|---|---|
| `Q3-SPRE1991` | 951 | 951 | 一致 | 不一致 | `branch_complete` |
| `Q6-SPRE1991` | 53 | 53 | 一致 | 不一致 | `branch_complete` |
| `Q3-SY1991` | 117 | 117 | 一致 | 不一致 | `branch_complete` |
| `Q3-SY1992` | 187 | 188 | **pass 2 に 1 件増** | 不一致 | `second_pass_digest_mismatch` |
| `Q3-SY1993` | 175 | 175 | 一致 | 不一致 | `branch_complete` |
| `Q3-SY1994` | 166 | 166 | 一致 | 不一致 | `branch_complete` |
| `Q3-SY1995` | 182 | 182 | 一致 | 不一致 | `branch_complete` |
| `Q3-SY1996` | 194 | 194 | 一致 | 不一致 | `branch_complete` |

- pass 1 は 9/3 02 時台、pass 2 は 9/5 13 時台で、**2 日の間隔**がある。
- 8 leaf すべてで返却順序が変わっている。順序は条件 1 が非依存にしているので判定に影響しない。
- `Q3-SY1992` だけ集合が変わった。増えたのは `https://openalex.org/W7208063655`
  (`publication_date` 1992-01-01) で、pass 1 に無く pass 2 にある。**申告総数 (`declared_total`) も
  187 → 188 に動いた。** `2026-09-03b-axis1-cond5-confirmations.md` は同日内の 2 走で
  「申告総数は動かない、動くのは順序」と確かめ (§4)、「登録された独立第 2 走の安定性は未観測」と
  書いていた (§7.1)。本走行はその未観測点を初めて埋める: **2 日を隔てた登録第 2 走では、8 leaf 中
  7 leaf で集合が安定し、1 leaf で申告総数ごと 1 件増えた。** 索引に後から追加された work と読むのが
  自然だが、snapshot 識別子が無いので機序は 9/3b と同じく確定しない。
- `Q3-SY1992` には後継 checkpoint が書かれない (条件 5 で落ちた 3 leaf と同じ)。再取得しか経路が無く、
  再取得しても索引がさらに動けば同じ形で落ちる。**同日内の 2 走目**なら安定する可能性が高いが、
  本 wave はそれを試していない (2 走目の間隔は取得 program の裁定事項)。

### 5. 無償枠

| 項目 | 値 |
|---|---|
| 生死確認 | 1 request (per-page=1、1 credit) |
| 取得 | 81 request (per-page=200、810 credit) |
| 停止時の残量 | 189 (13:11:42 JST、reset 71299 秒 → 翌 09:00 JST) |
| 自己施錠 | 入っていない (`remaining >= 40` で終えた) |

## 検査器の出力 (取得後)

`tools/check_axis1_search.py bundle` は `bundle_validation_complete: true` /
`passed: false` / `reason_code: leaf_not_run` (arXiv の leaf が未走) を返した。OpenAlex 78 leaf の内訳:

| 状態 | 件数 | 内訳 |
|---|---|---|
| `complete` | 8 | `Q2`、`Q3-SPRE1991`、`Q6-SPRE1991`、`Q3-SY1991`、`SY1993`〜`SY1996` |
| `incomplete_with_evidence` (条件 5) | 3 | `Q1`、`Q4`、`Q5` (再開点なし) |
| `incomplete_with_evidence` (2 走不一致) | 1 | `Q3-SY1992` (再開点なし) |
| pass 1 完了・2 走目待ち (checkpoint 000009〜000030) | 22 | `Q3-SY1997`〜`SY2018` |
| 未走 | 44 | `Q3-SY2019`〜`SY2026`、`Q6-SY1991`〜`SY2026` |

## この wave が実装していないこと

1 窓目と同じ。窓またぎ設計 (U12、[T-2259])、証拠時点の束縛 (U13、[T-2260])、条件 5 の扱い
([T-2258]、D1564 で現状維持)、`axis_complete` の production 経路 ([T-2323]) はいずれも触っていない。
repo の実装面の差分は 0。

## 次の窓の再開情報

- 2 走目 22 本: `--checkpoint <bundle>/checkpoints/0000{09..30}.json` (各 checkpoint の
  `canonical_runner_argv` が逐語の argv)。
- 未走 44 leaf: `--query-id <ID>`。ID は `launch-order.txt` に無い leaf-order (1 窓目) の残り。
- 重複除去は bundle の証拠で行う (本 README §1)。台帳では不完全。
- 駆動 loop を最初に走らせる前に、`runtime.json` の観測が前窓のものであることを織り込む
  (本 README §2)。生死確認は per-page=1 なら 1 credit で済む。
