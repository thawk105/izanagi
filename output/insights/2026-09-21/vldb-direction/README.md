# VLDB 投稿へ向けた研究方針 — 差分分析・Codex 見解・ユーザー裁定の写し (2026-09-21)

- authority: none
- default_effect: no-state-change
- 役割: 協議改訂 (roadmap) と決定台帳・worklog の新規 T が参照する一次資料を、repo 内で引けるように逐語で写したもの。
  裁定の正本は決定台帳 (本 wave の decisions fragment が fold された D)、実験項目の可変状態の正本は worklog 末尾の「次の一手」である。
  この dir は可変状態を持たない。
- 記録した wave: branch `worktree-dev-wave-vldb-direction-revision` (基準 main `36fb14a3d`)。

## 1. 収録物

| file | 原本 (repo 外) | 原本の更新時刻 (JST) | sha256 (写し = 原本) |
|---|---|---|---|
| `gap-analysis.md` | `/work/1/SFC/tanab/dev-wave-jobs/vldb-gap-analysis-20260921/README.md` | 2026-09-21 21:17:07 | `611cf4a7f192064ac851c6a3b5d2b7ca2d4120bf51603c5b01be4fdf3cbf86a4` |
| `codex-consult-1.md` | 同 dir の `codex-consult-1.md` | 2026-09-21 21:04:19 | `65d211d04f99da713b69adca8f9f7893bbe60ee113ab5b45cdcaf9595977f5ec` |
| `verdicts.md` | `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-vldb-direction-verdicts.md` | 2026-09-21 21:34:24 | `ef13c3a76694c3ec57663b3f8549b2af442dcc06b1ec74fd8363d59f3bed7d61` |

- 写しは `cp` による bytes 一致で、上表の sha256 を写しと原本の両方で計算して一致を確かめた。
- `verdicts.md` は 21:1x の受領後、21:3x に項 4 へユーザーの追補 (計算の確認ラインを「1 タスクの job 合計 2 node 時間以上」とする) が入った版である。
- 差分分析 (`gap-analysis.md`) の §0〜§9 は裁定前の提案で、§10 が裁定と TPC-C の改訂を書く。§7 項 2 (TPC-C 後回し) の推奨は §10 で改訂されている。
- Codex 見解 (`codex-consult-1.md`) は裁定前の独立見解で、TPC-C を「最初の必須項目から外す」と書く。この点はユーザーの疑義を受けて採らなかった (`verdicts.md` 項 2)。
- **写しの訂正 1 件 (写しの bytes は変えず、ここに記す):** `gap-analysis.md` §9・§10 の `orchestrator/pipeline.py` は現物に無い path で、
  YCSB 以外を拒否しているのは `orchestrator/campaign/pipeline.py` (trace 取得の前に `ycsb_` で始まらない binary を allowlist 方式で拒否する、
  main `36fb14a3d` で確認)。取引比「NewOrder 45% / Payment 43% / 他 3 取引 各 4%」は `external/ccbench/include/tpcc/tpcc_common.hh` の
  既定値 (Payment 43、OrderStatus・Delivery・StockLevel 各 4、NewOrder は残り) と一致する。

## 2. 同時刻の /rulings 第 30 回との重なり

`verdicts.md` 項 5 (21:1x) は「旧系列の再開 (T-2812 の択一、8b / 8c の official 系列) を論文の必須経路から外し、凍結 chain を新設しない。
T-2812 の択一そのものは保留」とする。一方、/rulings 全件 第 30 回 (job dir `/work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921d/`) の索引 15 行に
ユーザーは 21:3x に「推奨通りで」と答え、その索引 2 は T-2812 (1)(4) の g1 live launch に S' を採る推奨、索引 1 は T-2795 + T-2812 (2) の
K2 pair 再投入 1 job と 4 巡目 1 job の認可を含んでいた。第 30 回の記録側がこの食い違いをユーザーに 1 問で確認し、ユーザーは 21:37 頃
「codexと相談して決めて」と答えた。T-2812 の択一と K2 の認可は第 30 回側が決めて記録する。本 wave はその決定を覆さず、裁定 5 のうち
「論文の必須経路から外す」「凍結 chain を新設しない」だけを記録する。

第 30 回側から本 wave が受けた結論 (cross-session message、正本は第 30 回側の決定台帳): g1 の S' / O' / N は保留を継続。K2 は委任による解決として
K2 に限り保留を解き、D1777 の経路で pair 再投入 1 job → 成立時のみ 4 巡目 1 job (2 node 時間以上ならユーザー確認、論文の必須経路には戻さない)。
A-1 sized v3 の 3 本目は走らせない。T-2812 / T-2795 の carry は第 30 回側だけが更新し、本 wave は触れない (base の衝突を避ける合意)。
