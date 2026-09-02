# 実測値 — [T-2098]

正本は親が 2 回目に走らせた結果 (`verbatim/summary.json`)。1 回目は fix 前の script による走行で、
別 snapshot なので**中央値の比較に使わない**。

## 走行の provenance

| 項目 | 値 |
|---|---|
| 解析対象 root | `/work/SFC/tanab/.izanagi-acceptance-shards` (read-only) |
| inventory 開始 (UTC) | 2026-09-01T22:15:56.959206+00:00 |
| inventory 終了 (UTC) | 2026-09-01T22:16:11.981821+00:00 |
| snapshot か | いいえ (`is_snapshot: false`) |
| 母集合 session | 739 |
| 主集合 (complete case) | 680 |
| 除外 | 59 |
| 解析 script sha256 | `d81870c6af38f3ebc0eb4af159a12294bfd82c37529997f756da55cc142aaa22` |
| 実行時の repo checkout | `cab0a265f86811ab507a47e69cdd08b9f3b08c46` (実行後 `1359b8a57b075b91f22c1aa639726b8670158bbe` へ ff) |
| 新規の受入走行 | 0 本 |
| 計算ノードへの投入 | 0 本 (受入全走を除く) |
| scheduler 時刻の解釈 | `Asia/Tokyo`、入力分解能 1 秒 |
| quantile | nearest-rank、1 始まり rank `ceil(p*n)` (偶数 n では下側中央) |

## 推定量の定義

session `s`、shard `j`。`F` `H` はログインノードが書く mtime、`C` `E` は NQSV の会計時刻。

| 記号 | 定義 | 時計 |
|---|---|---|
| `S` | `max_j H_j − min_j F_j` | ログインノード内で閉じる |
| `Jmax` | `max_j (E_j − C_j)` | scheduler 内で閉じる |
| `Env` | `max_j E_j − min_j C_j` | scheduler 内で閉じる |
| `Skew` | `Env − Jmax` | scheduler 内で閉じる |
| `Rout` | `S − Env` | 期間どうしの差。静的な時計 offset は相殺する |
| `Rpair` | `S − Jmax` | 同上 |
| `head` | `min_j C_j − min_j F_j` | **時計を跨ぐ生値。offset を含む** |
| `tail` | `max_j H_j − max_j E_j` | **時計を跨ぐ生値。offset を含む** |

`Rpair = Rout + Skew` と `Rout = head + tail` はいずれも代数の恒等式であり、
680 行すべてで ns 差 0 である。**恒等式は検証ではない。**

## 主集合の分布 (n = 680、秒)

| 量 | 最小 | p25 | 中央値 | p75 | p90 | 最大 |
|---|---:|---:|---:|---:|---:|---:|
| `S` | 25 | 292 | **339** | 486 | 640 | 3909 |
| `Jmax` | 12 | 279 | **327** | 472 | 626 | 3844 |
| `Env` | 14 | 280 | **328** | 472 | 626 | 3844 |
| `Skew` | 0 | 0 | **1** | 2 | 3 | 6 |
| `Rout` | 8 | 11 | **13** | 14 | 15 | 66 |
| `Rpair` | 9 | 12 | **14** | 15 | 16 | 67 |
| `head` | −2 | 0 | **0** | 0 | 0 | 0 |
| `tail` | 8 | 11 | **13** | 14 | 15 | 66 |

負の `Rout` は 0 件、負の `Rpair` は 0 件、負の `head` は 20 件。

## 全 shard の job span (pooled、n = 1720、秒)

主集合 680 session に属する全 eligible shard の `E_j − C_j`。
K=2 が 320 session、K=3 が 360 session で `320 × 2 + 360 × 3 = 1720` と整合する。

| 最小 | p25 | 中央値 | p75 | p90 | 最大 |
|---:|---:|---:|---:|---:|---:|
| 11 | 171 | **259** | 341 | 516 | 3844 |

## 中央値どうしの差

| 式 | 値 |
|---|---:|
| `median(S) − median(全 shard の job span)` | 80 秒 |
| `median(S) − median(Jmax)` | 12 秒 |
| `median(Jmax) − median(全 shard の job span)` | 68 秒 |
| `median(Rpair)` (対の残差) | **14 秒** |

`12 + 68 = 80` は中央値の値の間の算術であって、session ごとの分解ではない。
**`median(S) − median(Jmax) = 12` と `median(S − Jmax) = 14` は一致しない。**
中央値は項別に足し引きできない。

## 除外の内訳 (排他理由、n = 59)

| 理由 | 件数 |
|---|---:|
| `marker_missing_or_invalid` | 34 |
| `missing_dispatch_intents` | 13 |
| `accounting_missing` | 12 |
| `accounting_ambiguous` | 0 |
| `accounting_unparseable` | 0 |
| `missing_created` / `missing_ended` | 0 / 0 |
| `scheduler_order_invalid` / `login_order_invalid` | 0 / 0 |
| `shard_count_invalid` | 0 |
| `path_component_symlink` | 0 |
| `unreadable_session_directory` | 0 |

`680 + 59 = 739` で母集合が閉じる。読めなかった session 0 件、parse 失敗 0 件。

**complete-case であることの限界:** timeout・qdel・共有 deadline・遅い会計で marker や
`Created` / `Ended` が欠けると、長時間側が選択的に落ちうる。除外の counter を出すだけでは補正できない。

## auxiliary の欠測 (主集合を落とさないもの)

| 項目 | 件数 |
|---|---:|
| `report.json` の無い shard | 155 |
| shard `junit.xml` の無い shard | 153 |
| `receipt.json` の無い shard | 92 |
| root `junit.xml` の無い session | 73 |
| `login-collection.log` の無い session | 15 |
| `queue-wait-timeout` の outcome を持つ shard | 18 |
| request ID を読めず prefix 検索へ落ちた shard | 87 |
| `Created` / `Started` / `Ended` / `Request Name` の欠落 shard | 0 / 0 / 0 / 0 |
| `stat` に失敗した path | 0 |

## login collection の marker 比較

| 分類 | 主集合 (680) | 母集合 (739) |
|---|---:|---:|
| `off_path` (collection log の mtime <= 最後の handled) | 680 | 692 |
| `on_path_candidate` | **0** | **0** |
| `indeterminate` (どちらかの marker が無い) | 0 | 47 |

比較する 2 つの marker はどちらもログインノードが書く。計算ノードが書く `report.json` や
`junit.xml` とは比較していない (時計が違う)。

**limitation:** log の mtime は collection の subprocess が返った後の書込みであって collection の
終了そのものではない。`off_path` は「collection が親を遅らせなかった」を含意しない。

## D1320 の再現 (cutoff 2026-08-29)

| 版 | 母集合 | intents なし | marker 欠落 | 集計 | 中央値 `max H − min F` | 中央値 `max_j(H_j − F_j)` |
|---|---:|---:|---:|---:|---:|---:|
| 目標 (D1320) | 568 | 1 | 18 | 549 | 338 | — |
| fallback あり | 586 | 1 | 26 | 559 | **338** | **338** |
| fallback なし | 559 | 0 | 0 | 559 | **338** | **338** |

いずれも `reproduced = false`、`formula_identification = not_identified`。
両候補式が同じ 338 秒を出すため、D1320 がどちらを使ったかは同定できない。
cutoff を動かして件数を合わせることはしていない。

## 診断値 (合否条件は付けない)

| 量 | n | 最小 | p25 | 中央値 | p75 | p90 | 最大 |
|---|---:|---:|---:|---:|---:|---:|---:|
| receipt `queue_wait_s` − 会計 `Started − Created` | 1737 | −789.75 | −14.58 | −2.99 | −2.69 | −1.77 | **−1.41** |
| `Elapse` − (`Ended` − `Started`) | 1740 | 1 | 4 | **4** | 5 | 5 | 10 |

- 前者は**比較できた全 shard で負**である。receipt 値は「qsub 復帰から qstat が初めて `RUN` と
  解釈するまで」、会計値は「`Created` から `Started` まで」で、起点も終点の意味も違う。
  照合 session の shard-0 では 5.34 秒 対 208 秒だった。
  **どちらが正しいかではなく、別量である。** 差の原因 (NQSV の staging か、qstat の表示仕様か、
  state の解釈か) はこの資料からは断定できない。
- 後者は全行で正であり、`Elapse` と表示時刻の差は同値ではない。差を作っている要因
  (1 秒分解能・丸め・scheduler 内部の包含区間) は断定できず、この差を起動費用・終了費用と呼べない。

## 独立検査

| 検査 | 種別 | 結果 |
|---|---|---|
| `Rpair = Rout + Skew` の全行 ns 差 | 恒等式 | 0 差 / 680 行 |
| `Rout = head + tail` の全行 ns 差 | 恒等式 | 0 差 / 680 行 |
| 母集合 = 主集合 + 排他除外、1 session 1 行 | 自己整合 | pass (739 = 680 + 59) |
| NQSV の `Created <= Started <= Ended` | 自己整合 | pass、違反 0 / 1740 shard |
| 照合 session の 8 値の完全一致 | **反証可能** | pass |
| D1320 cohort の再現 | **反証可能** | **fail** (両版) |
| receipt `queue_wait_s` と会計 queue の差 | 診断 | 報告のみ |
| `argmax(job span)` と `argmax(handled mtime)` の一致 | 診断 | 報告のみ |
| `Elapse` と `Ended − Started` の差 | 診断 | 報告のみ |

**照合 session** `00e791819b6e2fd7908f1c2261f35e0a` (K=3、2026-09-02) の期待値は会計値と marker mtime から
独立に導いたもので、実装から逆算していない。`Ended` を 1 秒ずらすだけで落ちる (恒真ではない)。

| 量 | 期待 | 実測 |
|---|---:|---:|
| `S` | 457 | 457 |
| `Jmax` | 442 | 442 |
| `Env` | 443 | 443 |
| `Skew` | 1 | 1 |
| `Rpair` | 15 | 15 |
| `Rout` | 14 | 14 |
| `head` | 0 | 0 |
| `tail` | 14 | 14 |

## 段ごとの経過

| 段 | 子 | 結果 |
|---|---|---|
| 2 プラン | codex plan | 主推定量を対の残差に固定。時計 anchor は誤り (段 3 で反転) |
| 3 レンズ A | codex consult | BLOCKER 2 / MAJOR 7 / MINOR 2 |
| 3 レンズ B | codex consult | BLOCKER 2 / MAJOR 7 / MINOR 2 |
| 4 裁定 | 親 | 21 所見すべて real。20 件採用、1 件部分採用 |
| 5 実装 | codex author | 解析 script 1 本。oracle 8 値一致 |
| 6 レビュー C | codex review | BLOCKER 1 (全 shard の分布が無い) / MAJOR 4 / MINOR 1 |
| 6 レビュー D | codex review | BLOCKER 1 (出力の追従書込み) / MAJOR 5 |
| 6 fix | codex fix | 7 件すべて実装。oracle と中央値は不変 |
| 6 焦点 | codex focus | 7 件すべて `closed`、回帰なし、親の算術を検算 pass |
