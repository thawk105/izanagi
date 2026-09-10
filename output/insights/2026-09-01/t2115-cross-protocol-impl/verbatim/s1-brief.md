# 段 1 brief — [T-2115] 段 7 cross-protocol の実装残余

## scope

実測済みの 3 残余を protocol 対応にし、公式成果物 (層 3 material report) へ接続する。
(1) genome 空間の protocol 登録が silo 1 件だけ、(2) between-run floor の baseline が silo 固定
(出力 path にも protocol 軸が無い)、(3) 層 3 の floor 照合キーに protocol の軸が無い。
本題の実装だけを行う。仮想リスク向けの gate・検査・台帳・一般化は作らない。

## 確定済みユーザー裁定 (覆さない)

- **D1360 / 2026-08-11 裁定 Q1〜Q3 全問 (a):** trace v2 化を単独 wave で先行、初手は mocc、
  **stock 専用計測経路は偵察としても解禁しない**。残るのは裁定でなく実装。
- stock 専用計測経路で得た値は公式 report・selector・比較表・順位・headline のいずれにも入れない (規律 2)。
- D87/D86(3): AI は qsub しない。protocol 別 floor の**実測そのものは本 wave の成果物ではない**。

## 不変条件

- 規律 2 を緩めない。verify を経ない値が certified 経路・公式成果物へ入る path を新設しない。
- submodule pin 511c9538 に mocc の TRACE hook は無い (実測: `cc/mocc/transaction.cc` の TRACE 出現 0)。
  よって現行 pin から mocc を build して測る経路は certified にならない。**この事実に fail-closed で従う。**
- 既存 silo floor JSON (`output/env/*/calibration/between_run_noise_*.json`) の bytes を変えない。
  既存 layer3 report の再生成を要求しない (歴史的 report は現行 schema で読めたまま)。
- `screening_driver.load_between_run_floor` の「workload 一致で matches はちょうど 1 件」契約を壊さない。
- 凍結 bytes への影響なし (`FROZEN_MANIFEST` 23 件・`s8b_oracle_manifest._GENERATOR_SOURCES` 5 件に
  編集面 4 file はいずれも不在。layer3_report.py の自 sha を pin する箇所も repo 内に無い)。

## 成果物の形

コードとテストだけ (docs 記録は段 7)。protocol を第一級の軸として持つ 3 面 +
それに追随する consumer。新規の測定・build・qsub は行わない。

## 実アンカー表

| # | anchor | 現状 |
|---|---|---|
| A1 | `orchestrator/campaign/genome.py` `SPACES` / `space_for()` | `{"silo": SILO_SPACE}` の 1 件 |
| A2 | `orchestrator/campaign/between_run_floor.py` `BASELINE` / `_write_out` の `stem` | silo 固定・stem に protocol 無し |
| A3 | `orchestrator/campaign/layer3_report.py` `_calibration_floors` の照合条件 | (records, threads, workload) のみ |
| A4 | `orchestrator/campaign/layer3_schema.json` `definitions.floor_result` / `noise_floor` | `additionalProperties:false` |
| A5 | `orchestrator/campaign/screening_driver.py` `load_between_run_floor` | glob + workload 一致で一意必須 |
| A6 | `external/ccbench/cmake/Options.cmake` / `cc/mocc/CMakeLists.txt` | mocc の live 軸 = `BACK_OFF` + `TEMPERATURE_RESET_OPT` + `KEY_SORT` |

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** protocol 別 genome 空間の登録それ自体は certified 経路を緩めない。`space_for()` に
  本番 caller は無く (現 consumer は test のみ)、pipeline の verify 必須は不変だから。
  mocc の軸は A6 の 3 ブール (2^3=8)。`RWLOCK` は bare define で直交トグル不可、
  `INSERT_*_DELAY_MS` は計測撹乱ノブとして除外する (silo の死にフラグ除外と同型、規律 4)。
- **(P1-b)** between-run floor の protocol 対応は「baseline を protocol から導く」+
  「protocol が現行 pin で trace-hook を持つときだけ admit する」の対で入れる。今日 silo が正例、
  mocc が負例になる。これなら D1360 が禁じた stock 専用計測経路を開かない。
- **(P1-c)** floor の照合キーに protocol を足す既定の取り方は、floor JSON が既に持つ `genome`
  (`"silo|BACK_OFF=0,…"`) の protocol 部を読むこと。既存 file の bytes を変えずに後方互換で軸が立つ。
  campaign 側の protocol は WAL/lock のどこから取るかを段 2 で file:line で確定する。
- **(P1-d)** A5 (screening_driver) は編集面 4 file の外だが、protocol 軸を入れる変更の**整合部品**である。
  同一 workload の第 2 protocol floor が置かれた瞬間に既存 screening が全部落ちるため、
  照合キーを揃えないと変更自体が不整合になる。段 4 で scope 内/外を裁定する。

## DW-G05 成果物影響

放置すると、別 protocol の campaign に silo の floor が黙って一致し、
層 3 material report の `noise_floor` が誤った provenance で確定する (= 採否閾値が別 protocol の値になる)。
これは公式成果物の値と受理集合を直接変える。

## 分割方針

軽量版ではなく段 2・3 を回す — 受理集合 (floor 照合) と正しさ防壁 (規律 2 の境界) に触るため。
実装は D95 Codex author。編集面が producer (A2) と consumer (A3/A4/A5) にまたがるので、
producer/consumer 契約を 1 子に持たせる (並行 fix で契約を割らない)。

## 受入・実測環境

pytest を login node で実走 (Python のみ、build/bench なし)。計算ノード job は投入しない。
