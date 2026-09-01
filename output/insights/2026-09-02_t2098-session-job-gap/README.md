# [T-2098] 受入 session の合計と job の合計の差を分解する

D1320 が「未分解であり、分解したかのように書かない」と明記した **session 合計 338 秒 −
job 合計 263 秒 = 約 75 秒**を、保存済みの timing 記録だけで分解した。新規の受入走行は 0 本で、
すべて既存成果物の事後解析である。

一次資料は本 directory。実測値の正本は `measurements.md`、解析結果の生 JSON は
`verbatim/summary.json`、解析 script の逐語は `verbatim/analyze_t2098_session_job_gap.py`。

## 結論 1 — 75 秒はほぼ全量が「数え方の違い」であって費用ではない

D1320 の 75 秒は、**549 session の中央値 338 秒**から**1297 job の中央値 263 秒**を引いた値である。
前者は session を 1 単位に数え、後者は job を 1 単位に数えている。**単位も母集合も違う。**
session は K 本の shard のうち**最も遅い 1 本**が終わるまで待つので、
「全 job の中央値」は session が待つ量ではない。

現在のコーパスで同じ形の量を計算すると **80 秒**になる。これは中央値どうしの差なので、
中央値の引き算として 2 つに割れる。

| 項 | 値 | 意味 |
|---|---:|---|
| `median(最長 shard の job) − median(全 shard の job)` | **68 秒** | 数え方の違い。費用ではない |
| `median(session の包絡) − median(最長 shard の job)` | **12 秒** | 中央値どうしの差 |
| 合計 | 80 秒 | 歴史的な 75 秒と同じ形の量 |

**この 2 分割は中央値の値の間の算術であって、session ごとの分解ではない。**

## 結論 2 — session が job の外で実際に払っているのは 14 秒である

session ごとに対にして引いた残差の中央値は **14 秒**で、上表の 12 秒とは別の量である
(中央値は項別に足し引きできない)。分布は非常に締まっている。

| 量 | 中央値 | p25 | p75 | p90 | 最小 | 最大 |
|---|---:|---:|---:|---:|---:|---:|
| 対の残差 `Rpair` | **14 秒** | 12 | 15 | 16 | 9 | 67 |
| scheduler の外 `Rout` | 13 秒 | 11 | 14 | 15 | 8 | 66 |
| shard 間のずれ `Skew` | 1 秒 | 0 | 2 | 3 | 0 | 6 |

680 session すべてで `Rpair = Rout + Skew` が ns 単位で成立する。
**ただしこれは代数の恒等式であって検証ではない。**

## 結論 3 — 残差はどの session でも「最後の Ended から最後の handled まで」の 2 秒以内にある

`Rout` は行ごとに `head + tail` に等しい。

- `head` = 最初の `Created` − 最初の `confirm`。680 行すべてで **−2 秒以上 0 秒以下**。
- `tail` = 最後の `handled` の mtime − 最後の `Ended`。中央値 13 秒。

`confirm` は qsub が返った後に書かれる (`tools/pegasus/dispatch_compute.py` の qsub 呼出しと
`_confirm_dispatch_intent` の順) ので、`Created` は必ず `confirm` 以前であり `head` は 0 以下になる。
実測でも下限は −2 秒だった。したがって**どの行でも `Rout` は `tail` 以下で、`tail` より最大 2 秒小さい。**
投入前の帳簿処理は残差の内訳にならない。

**`tail` の中身はこれ以上分けていない。** 保存された記録には、poll の粒度・成果物収集・
receipt 永続化・scheduler log の中継を分ける測点が無い。測っていないものを分解したと書かない。

## 結論 4 — ログインノードの全件 collection は候補から外れる

`login-collection.log` の mtime が最後の `handled` の mtime より後だった session は **0 件**
(主集合 680 件すべてが `off_path`、母集合でも `on_path_candidate` は 0 件、判定不能 47 件)。
比較した 2 つの marker はどちらもログインノードが書くので、時計が揃っている。

**ただし「collection の寄与は 0 秒」とは言えない。** 2 つの理由がある。

1. `login-collection.log` の mtime は collection の subprocess が返った後の log 書込み時刻であり、
   collection の終了そのものではない。
2. 親は collection が返ってから worker の結果を読み始める
   (`tools/acceptance_shards.py` が全 worker を `start()` した後に `collect_login` を呼び、
   その後に結果を待つ)。順序が先でも、既に ready だった worker を待たせた可能性は残る。

言えるのは marker の順序までである。

## 結論 5 — D1320 の cohort は再現しなかったが、338 秒は再観測された

cutoff 2026-08-29 で、目標 `(母集合 568 / dispatch-intents なし 1 / marker 欠落 18 / 集計 549)` に対し、

- fallback あり: `(586, 1, 26, 559)`、中央値 338 秒
- fallback なし: `(559, 0, 0, 559)`、中央値 338 秒

いずれも件数が一致しないので `reproduced = false` である。**合わせ込みはしていない。**
一方、中央値 338 秒は両版・両定義 (`max H − min F` と `max_j(H_j − F_j)`) で再観測された。
これは数値の限定的な頑健性を示すが、cohort・選択規則・集計式の同定ではない。
両候補式が同じ 338 秒を出すため、D1320 がどちらを使ったかは**同定できない**。

新たに出した全 shard の job span 中央値 **259 秒**は D1320 の job 中央値 263 秒に近い。
これは**同じ式・同じ観測単位に対する別 cohort 間の弱い数値的一致**であって、
cohort の再現でも 263 秒の更新でもない。

## 保存済み記録では測れないもの — 新しい観測点が要る項目

依頼の「新しい観測点が要るならそれを別項として返す」への回答である。**実装はしていない。**

| 測れない区間 | 必要な計装 |
|---|---|
| `tail` (最後の Ended → 最後の handled) の内訳 | terminal poll ごとの生 qstat 応答と観測時刻、成果物収集の開始・終了、receipt 永続化、scheduler log 中継、handled 書込みを同一 login monotonic clock で刻む |
| qsub 呼出し開始 → scheduler `Created` → qsub 復帰 → `confirm` 書込み | qsub 前後と confirm の同一 login monotonic clock marker、対応する scheduler event marker |
| ログインノードの時計と scheduler の時計の offset と drift | session の前後で scheduler server time と login node realtime を同時取得する calibration record |
| qstat の初回 `RUN` 解釈 → 会計 `Started` → job script の実開始 | request ID に束縛した生 qstat 応答と観測時刻、compute 側の job entry marker |
| `Elapse` と `Ended − Started` の差 (中央値 4 秒、範囲 1〜10 秒) | 高分解能の scheduler service 境界と、対応づけ可能な compute process の entry / exit marker |
| collection の session への因果的寄与 | collection の開始・復帰、各 worker の payload ready・送信、親の受信開始を同一 login clock で刻む |
| `handled` より後の親費用 (join・集約・merge・root junit) | 各境界の marker。現在の estimand はここを含んでいない |
| login collection の正確な開始時刻 | `_collect_login_universe` の呼出し直前・subprocess 復帰直後・log 書込み後の monotonic timestamp |

このうち**全 shard の job span の pooled 中央値だけは新しい計装が不要**で、
保存済みの `Created` / `Ended` から再集計できた (本 wave で実施済み)。

## 射程

- 走査は snapshot ではない。実測中もコーパスは増えた (親の 1 回目 737 session、2 回目 739 session)。
  **正本は 2 回目 (`verbatim/summary.json`)** で、inventory 窓は
  2026-09-01T22:15:56Z 〜 2026-09-01T22:16:11Z (UTC) である。
- 主集合は complete-case (680 / 739)。**timeout・qdel・共有 deadline・遅い会計で
  marker や `Created` / `Ended` が欠けると長時間側が選択的に落ちうる。** 偏りの向きと大きさは確定できない。
- 104 checkout 群・2 か月・K=2 と K=3 が混ざった集団である。**単一の「受入の姿」として語れない。**
  月別の `S` 中央値は 8 月 334 秒 / 9 月 369 秒、K 別は K=2 が 333 秒 / K=3 が 357 秒。
- D1420 (T-2097) が分解した約 51.7 秒の全 collection は**計算ノード上の 48 worker の collection**であり、
  本 wave が扱うログインノード親の `--collect-only` とは別物である。D1420 は自ら
  「pytest wall の層についてだけ述べ、job 層・session 層へ一般化しない」と書いている。
  内側は測り直していない。
- **短縮の実装・提案はしていない。** D1035 が指す排他閉包の細分化にも踏み込んでいない。

## 実装面

解析 script は Codex `role=author` が書き、親が実行し、**repo へ commit していない。**
逐語は `verbatim/analyze_t2098_session_job_gap.py` (sha256
`d81870c6af38f3ebc0eb4af159a12294bfd82c37529997f756da55cc142aaa22`)。
fix 前の版は `verbatim/analyze_t2098_session_job_gap.v1.py` (sha256
`953c085731fd63d5a8add1ae4335350e071881addf2b5e13df124fc883ff85a9`)。
repo の実装面の差分は 0 byte である。
