# [T-1851] 単位 C3b — 段 1 brief (2026-09-09)

branch `worktree-dev-wave-t1851-unit-c2` を継承 (tip `8fbcb70a5`)。**land しない (D1341)。**
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`。local main `61171ddf0` 包含済み。

## 研究前進

C3a が campaign → certified launcher → attempt registry → result v5 の配線を実装したが、
**その経路を実環境で 1 度も通していない。** `DW-O13` は「field の実在では足りない。その field が
実環境で取りうる値を実測し、要求する値が到達可能か確かめてから述語を採用する」と定める。
C3b の最小差分は **Pegasus で fresh production campaign を 1 本走らせ、gate 入力の実観測値を
receipt にすること**。完了判定 = official 走行 1 本が `job-result.json` を残し、その run の
attempt registry から gate 入力の列挙値と min/max を限界文言つきで記録できたこと。

## 確定済みユーザー裁定と既裁定

- 本 wave の指示 (逐語)「単位 C3b — Pegasus で fresh production campaign を 1 本走らせ、
  gate 入力の実値域 receipt を作る」「裁定が必要そうなところはcodexと相談して決めてください」。
  これで C3a 裁定パッケージの裁定 1(a) (7 単位化) と裁定 4(a) (C3b をこの設計で進める) は確定。
- D926: official 実投入は submission nonce へ束ねた `--confirm-official-floor-run` が必須。
- D1124: 測定の反復そのものに承認は要らない。freeze へ昇格させる予算承認 (D1161/D1398) は別物。
- D811: pilot 値は freeze へ発効しない。official 経路は別 source commit と script blob で開く。
- D1341 / D1703: land しない。持ち越し裁定は単位が揃うまで個別に裁定しない。

## scope (純増のみ)

1. wave tip の code で official floor campaign を Pegasus へ 1 本投入し完走させる。
2. その run の artifact から gate 入力の実観測値 (列挙値・min/max) を抽出し receipt にする。
3. receipt に「1 run の標本極値であって母集合の許容 bound ではない」限界文言を載せる (B-11)。

## 不変条件

- 正しさゲートを緩めない。fake registry・injected `measure_fn`・pilot 値を実値域の代替にしない。
- 凍結 23 件の bytes を変えない。`FORMULA_ID` 据え置き。`attempt_registry_core.py` に触れない。
- 成果物を repo へ commit しない。使い捨ての detached submit-tree で走らせ repo 外へ退避する
  (run directory / binary store / submission receipt / job staging の 4 点 bundle)。
- `submit_floor.sh` の投入インタフェースを自分で発明しない。raw `qsub` は D926 の保証範囲外。

## (P1) 親の provisional 裁定 = 段 3 の攻撃対象

- **(P1-1) official 走行を wave branch の未 land commit で行う。** 投入 receipt は `source_commit` を
  pin する。D811 は「別の source commit と script blob hash で再投入して official 経路を開く」と
  述べるだけで、その commit が main に着地済みであることは要求していない — と親は読む。
- **(P1-2) receipt は `output/insights/` の `.md` 1 本とし、抽出 producer を新設しない。**
  1 run 限りの記録であり、`DW-G04` の「発火条件を満たす既存 artifact path を書けなければ設計メモに
  留める」と `DW-G03` の「族一般化は独立 2 例から」に従う。実装面の差分 0 を狙う。
- **(P1-3) gate 入力の集合は C3a が新設した述語の消費 field に限る** — 封印 pre-probe
  (`competing` / 実 raw `rc`・`stdout`・`stderr`)、attempt registry の ordinal 三軸
  (`attempt_ordinal` / `retry_ordinal` / `measurement_ordinal`)、`slot_id`、`repetition`、
  consumption marker の有無、result `schema` と `attempt_registry` prefix の `row_count`。
- **(P1-4) 1 job・1 ノード直列でよい。** pilot 実績で 12 セル × 8 session の完走に約 48 分
  (job Elapse 2894 秒)。条件分割による多ノード同時投入は sanctioned wrapper に受け口が無い。

## 実測アンカー (現物)

| アンカー | 実測 |
|---|---|
| `tools/pegasus/submit_floor.sh` | main 側 `admission_registry.json` に実在 (F660 不発火)。`local-ok` |
| `tools/pegasus/floor_campaign.sh` | 固定 `--mode official`。`#PBS -q gen_S`、`elapstim_req=10:00:00` |
| `orchestrator/campaign/s8b_floor_campaign.py:6816` | `attempt_registry is not None` のとき result v5 |
| `orchestrator/campaign/s8b_floor_contract.py:30-31` | comment「現 producer は v4 のまま」は C3a 後に陳腐化 |
| `orchestrator/campaign/s8b_floor_attempt_launcher.py:687,709,1576,1605` | probe / read / 旧入口 / 新入口 |
| `/work/1/SFC/tanab/izanagi-thirdparty-cache` | 実在 76 MB |
| `qstat` (2026-09-09 21 時台) | 他 session の `988492.nqsv` が 1 本 QUE。混雑なし |
| official 走行の履歴 | **0 件。** 実投入は 2026-07-28 の `873200`/`873225` (どちらも rc=2)。pilot は `945229` |

## 成果物の形

`output/insights/2026-09-09_t1851-unit-c3b-floor-range/README.md` + 値域 receipt + 退避 bundle の
構成 manifest。台帳 fragment は `docs/spool/` へ。

## 並列分割方針

実装面の差分を狙わないので段 5 の実装子は原則ゼロ。段 2・3 は本 brief と (P1) 4 件の検査へ充てる。
job の待ちは 1 本だけ張り、待つ間に receipt の抽出経路の静的設計を進める。
