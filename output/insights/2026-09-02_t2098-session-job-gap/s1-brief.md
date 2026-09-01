# 段 1 brief — [T-2098] session 合計と job 合計の差の分解

## scope

D1320 が「未分解であり、分解したかのように書かない」と明記した **session 合計 338 秒 −
job 合計 263 秒 = 約 75 秒**を、**保存済みの timing 記録だけ**で分解する。新規走行 0 本。
実装面は解析 script 1 本だけ (Codex `role=author` が書き、親が実行し、repo へ commit せず
repo 外へ退避、逐語を insight の `verbatim/` へ sha256 付きで収める)。repo の最終差分は docs のみ。
短縮の実装・提案はしない。gate・検査・台帳・一般化の追加は scope 外 (ユーザー明示)。
分解しきれない部分は「新しい観測点が要る項目」として別項で返す。

## 確定済みの既裁定 (覆さない)

- **D1320** — 4 層 (queue 待ち 9 秒 / Elapse 191 秒 / job 合計 263 秒 / session 合計 338 秒)。
  75 秒は未分解。会計サマリを権威とし receipt の `queue_wait_s` は別量。
- **D1420** — T-2097 の内側分解。**pytest wall 層に限定し job 層・session 層へ一般化しないと
  明記している**ため本 wave と対象が重ならない。内側 (残差 約 58 秒・全 collection 約 51.7 秒) は
  測り直さず参照する。
- **D1035 / D1298 / D1019 / D820** — 短縮方向と律速の既裁定。本 wave は実装も提案もしない。

## 不変条件

1. 絶対規律 2 を緩めない。受入の判定・排他・選択・受理集合を 1 bit も変えない。
2. 既存成果物の**事後解析のみ**。受入 session を新規に走らせない。解析対象は read-only で開く。
3. 測っていないものを分解したと書かない (D1320 / D1420 の姿勢を継承)。
4. 加法分解は恒等式であって検証ではない。独立検査を別に置く。
5. 中央値だけで裾を語らず、裾だけで中央値を語らない (D1320)。

## 割れうる前提 — 親の provisional 裁定、段 3 の攻撃対象

- **(P1) 「75 秒」は対の残差ではない。** 338 は 549 session の中央値、263 は 1297 job の中央値で
  母集合も単位も違う。session は K=3 の**最大** shard を待つので、対で引くべき量は
  `session 合計 − max_shard(job Created→Ended)` である。差の中央値と中央値の差は一致しない。
- **(P2) ログインノードの全件 collection は設計上 job と並行であり、臨界経路に載るとは限らない。**
  `tools/acceptance_shards.py:1335` が dispatcher worker を全 shard 分 `start()` した**後**に
  `collect_login` を呼ぶ。`tools/run_tests.py:1402` の docstring も「compute shard と並行に」と書く。
  collection 終了が最終 job 終了より前なら residual に寄与しない。
- **(P3) 残差の主項は投入前後の 2 つの遅れである。** confirm→Created (投入受理から会計上の作成)
  と Ended→handled (dispatcher の約 5.1 秒 poll + 成果物収集 + merge)。
- **(P4) mtime と scheduler 時刻は別時計である。** 前者は Lustre 上の file 時刻、後者は NQSV の
  会計時刻。両者を引き算する項には時計 offset が乗る。offset の上下限を測って報告に載せる。

## 変更面 — 実アンカー表

| 種別 | path | 扱い |
|---|---|---|
| 解析対象 | `/work/SFC/tanab/.izanagi-acceptance-shards/<sid>/dispatch-intents/shard-N.{intent,confirm,handled}.json` | mtime だけ読む (中身に時刻は無い) |
| 解析対象 | `.../<sid>/shard-N/dispatch/shard-N/izdw-shard-N.e<req>` | 会計サマリの Created/Started/Ended/Elapse |
| 解析対象 | `.../<sid>/shard-N/dispatch/shard-N/receipt.json` | `state_history[].elapsed_s`・`queue_wait_s`・`outcome` |
| 解析対象 | `.../<sid>/login-collection.log`、`.../<sid>/shard-N/report.json`、`.../<sid>/junit.xml` | mtime と size |
| 新規 (子) | 解析 script 1 本 (worktree 内に書かせ、実行後 repo 外へ退避) | commit しない |
| 新規 (親) | `output/insights/2026-09-02_t2098-session-job-gap/` (README + measurements + verbatim) | commit する |
| 新規 (親) | `docs/spool/` の fragment (worklog / decisions) | commit する。fold は段 9 の land |

参照のみ: `docs/decisions.md` D1320 (42345 行)・D1420 (45015 行)、
`output/insights/2026-08-29_acceptance-speedup-tmpdir/`、`output/insights/2026-09-02_t2097-residual-breakdown/`。

## 成果物の形

per-session の対の残差分布 + 区間別の内訳 + 各区間の測点と時計の出所 + 独立検査の結果。
分解できない残りは「新しい観測点が要る項目」として、必要な測点を名指しで別項に書く。

## 分割方針

編集面が単一 (解析 script 1 本) なので Codex `role=author` は 1 単位。段 2 プラン 1 本、
段 3 敵対レンズ 2 本。実測環境はログインノード上の読み取り解析のみで計算ノードへは投入しない
(受入全走を除く)。
