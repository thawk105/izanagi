# 段 4 裁定 — [T-2265] cohort 2 の図のための観測長 6 秒 perf 測定

段 2 plan (GO 判定) と段 3 の 2 レンズ (レンズ A = 正しさ境界と凍結、レンズ B = 整合と実効性) の
所見を裁定する。裁定後の plan を v2 とする。

## 0. 裁定の要 — 名乗りを 1 つに固定する

両レンズが同じ根に当たっている。**extime 6 の 7 腕格子を「事前登録済みの確認的判定」と呼ぶのか、
「未認証の記述的な別測定」と呼ぶのか**が決まっていなかった。

**裁定: 後者に固定する。** 本 wave が作る performance 成果物と、そこから出る H1–H7 の値は
**未認証・記述的な companion 測定**である。凍結された extime 3 の判定を、置き換えも再確認も
反証もしない。

この 1 つを固定すると、レンズ A の所見 1・2・4 とレンズ B の所見 8・9 が同時に解ける。
「確認的」と名乗らないので、成果物へ束縛できない登録文書は要らなくなる。

## 1. 所見の裁定

### レンズ A

| # | 判定 | 採否 | 裁定 |
|---|---|---|---|
| 1 | real | 採用 | §0 のとおり名乗りを「記述的な別測定」に固定する。H1–H7 を確認的判定と書かない |
| 2 | real | 採用 | 登録の束縛が外付けになるのは事実。**(P1) を縮める** (§2) |
| 3 | real | **採用 (最重要)** | legacy `cw-as-dyn` は `count_cap_us = 10240`、cohort 2 cell は `9223372036854775807`。**performance 側は cohort 2 の腕の trace 無効版ではない。** 別 CC 設定である。insight の冒頭に置く |
| 4 | plausible | 一部採用 | correctness gate 未充足 (A+B+C の legacy 腕は未認証) は insight に書く。環境 probe の新設は scope 外 |
| 5 | real | 採用 | brief の「detached checkout からしか成立しない」は誤り。正しくは「`8bdf173cc` を指す tracked-clean な checkout」。detached かどうかは `repo_head` に符号化されない (§3) |
| 6 | plausible | 採用 | 1245 秒は見積りであって上限ではない。walltime を上げる (§4) |
| 7 | real | 採用 | `clocks_per_us = 2100` は Pegasus contract の固定値。identity 一致は物理クロック一致の証拠ではない。insight に書く |
| 8 | real | 採用 | 5 と同じ |
| 9 | real | **採用 (実行手順を変える)** | fixture が通ることは実物が通ることを意味しない。かつ parser は 1〜168 row を許す。**親は作図前に 7 本すべてが 168 点の完全格子であることを実測する** (§5) |
| 10 | real | 採用 | 主張の上限を insight に列挙する。特に 3 の断絶を落とさない |
| 11 | real | 記録のみ | 作図器は入力どうしを比べるだけで実 repo と照合しない。本 wave は自分で投入した成果物だけを入れるので実害は無いが、限界として insight に書く。新 gate は作らない |
| 12 | real | 採用 (表現を直す) | (P2) は事前凍結ではない。12 本は既に存在し主判定の解析も済んでいる。「結果非依存の規則を、診断図を 1 枚も描く前に固定した」と正確に書く |

### レンズ B

| # | 判定 | 採否 | 裁定 |
|---|---|---|---|
| 1 | plausible | 採用 (軽微) | 検査順は `hostname` が先。投入直前に submit tree の canonical 性と tracked-clean を**実測**する |
| 2 | real | 記録のみ | extime 3 の成果物を混ぜても identity 検査が fail-closed で止める。良い知らせ。新 gate 不要 |
| 3 | real | **採用 (投入 argv を変える)** | performance 分岐に外側 watchdog は無い。1 点 180 秒 timeout だけで、7 build に deadline が無い。→ `-l elapstim_req` を **01:00:00** へ上げる (§4) |
| 4 | real | 記録のみ | build 木の分離は driver の実コードで裏が取れた (`/scr/${PBS_JOBID}-t2187` と `$TMPDIR`)。7 本同時投入は妥当 |
| 5 | plausible | 採用 (記録で閉じる) | ノード分散も同時性も保証できない。**hostname と `started_utc` / `finished_utc` を insight に記録し、重複や大きなずれがあればそのまま書く。** anti-affinity 機構の新設は scope 外 |
| 6 | real | 記録のみ | 待ち方は fail-closed。journal は別名で、最終 JSON は全 loop 後に `open("x")`。良い知らせ |
| 7 | plausible | 記録のみ | login node での作図は裁定と資源制限の両方を満たす |
| 8 | real | 採用 | A2 と同じ。§2 で解く |
| 9 | real | **採用 (brief を訂正)** | 「図に明記する」は生成器を触らない限り不可能。→ **限定は insight の本文とキャプションに書く。図単体では言えないことも insight に書く** |
| 10 | plausible | 採用 (停止条件) | 実データで bbox が落ちたら、生成器を触らずに停止し、error 全文を添えてユーザー裁定へ返す |

## 2. (P1) の再裁定 — 新規事前登録文書は作らない

**当初の provisional 裁定を取り下げる。** 新規登録文書は作らない。

理由は 3 つ。
1. §0 で名乗りを「記述的な別測定」に固定したので、確認的判定のための前向き登録は要らない。
2. 作っても成果物へ束縛できない。成果物の `prereg_sha256` は driver が常に
   `docs/dynamic-backoff-preregistration.md` の bytes から作り、図の provenance もその値しか出さない
   (レンズ A 所見 2、レンズ B 所見 8)。**発火しない保証を置くのは実装したふりであり、`DW-G04` で
   留めるべきものである。**
3. ユーザーは「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示している。

**代わりに置くもの (これは新設ではなく、本 wave が書く insight の一部を前倒しするだけ):**
投入の**前**に、`output/insights/2026-09-09_t2265-cohort2-figures/measurement-design.md` を
commit する。中身は次を固定した 1 枚だけとする。

- 腕 (legacy 7)、workload 3、threads 8、`extime 6`、block 数 7、rep 0..6 の巡回順
- 停止・欠測規則: 7 本投入。complete が 7 なら 7、6 なら 6 で描く。5 以下なら描かない。
  job ID を受け取った rep は自動再投入しない。値を見てから job を足さない
- 図に使う診断は `985851` (job ID 昇順の先頭)
- 名乗り: 未認証・記述的な companion。extime 3 の凍結判定を置き換えない
- 束縛が外付けであること (`prereg_sha256` は旧文書を指す) を明記する

この file の commit SHA と sha256 を `submitted-jobs.txt` へ書き、投入はその後に行う。
**`docs/` 配下の既存 2 事前登録文書は 1 byte も変えない。**

## 3. brief の訂正

- 「投入は `8bdf173cc` の detached checkout からのみ成立する」→ **誤り。**
  正しくは「`8bdf173cc` を指す tracked-clean な checkout であればよい。detached であることは
  `repo_head` に符号化されない」。本 wave は実務上 detached worktree を使うが、それは
  他 session と干渉しないためであって必要条件ではない。
- 「図に非置換を明記する」→ **不可能。** 生成器は触らない。限定は insight に書く。

## 4. 投入 argv の変更点 (plan v2)

plan の 7 行を採用する。ただし 1 箇所だけ変える。

- `-l elapstim_req=00:40:00` → **`-l elapstim_req=01:00:00`**。
  根拠: performance 分岐には内側の外側 watchdog が無く、1 点 180 秒 timeout と deadline 無しの
  7 build しかない (レンズ B 所見 3)。見積り約 1245 秒に対し 3600 秒で約 2.9 倍の余裕になる。
  walltime は測定値に影響しない。既存 extime 3 走の「40 分」は事前登録の**見積り段落**の記述で
  あって凍結条件表の項目ではないので、変更は凍結に触れない。

他の env var は plan の逐語どおりとする。`IZANAGI_T2187_STEP_POLICY_SEED` は指定しない。

## 5. 親が作図前に必ず実測すること (レンズ A 所見 9)

各 performance JSON について次を確認してから plot へ渡す。確認は親が行う。

1. `cells` の row 数が **168** であること。
2. 座標集合が `CELLS x WORKLOADS x THREADS` の**全体**と一致すること (部分集合ではない)。
3. `extime_s == 6`、`schema_version == izanagi-cicada-adaptive-3const-probe/v3`。
4. `cell_order` が rep index の巡回順であること。
5. `pbs_jobid` が 7 本で相異なること。
6. 15 個の identity field が診断 `985851` と一致すること。

1 つでも欠ければ、その rep を入力から外し、残りが 6 本以上なら描く。5 本以下なら描かず停止する。

## 6. 変異事前登録

**免除する。** 本 wave の repo 差分は docs (insight) と `output/` 配下の成果物だけで、
D95 決定 2 の実装面 (`orchestrator/`・`tools/`・`hooks/`・場所を問わない Python/shell 等) の
差分が 0 だからである (`DW-S04`)。qsub launcher `.sh` は Codex `role=author` が書くが、
親が job dir へ退避して実行し、**repo へ commit しない**。

免除の証拠は段 7 の commit 差分そのもの (実装面 path を 1 つも含まないこと) で示す。
**受入全走は免除しない。**

## 7. 段 5 の scope

1 unit。Codex `role=author` が qsub launcher `.sh` を 1 本書く。仕様は plan §F に
本裁定の §4 (walltime) と §5 (作図前検査は親が行うので launcher には入れない) を反映したもの。

## 8. 停止条件

- 投入直前の submit tree 実測 (canonical・tracked-clean・ccbench pin) が赤なら投入しない。
- complete な performance が 5 本以下なら作図せず停止する。
- bbox (layout) が実データで落ちたら、生成器を触らずに停止し、error 全文でユーザー裁定へ返す。
