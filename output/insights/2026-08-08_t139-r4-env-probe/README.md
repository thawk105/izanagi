# [T-139] R4 環境 probe — 逐語 (dev-wave 2026-08-08/09)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-139] R4 環境 probe` の逐語成果物である。可変状態の正本は
worklog 末尾、採用済み判断の正本は decisions であり、ここには凍結した逐語を置く。
**本文書は可変状態の正本ではない。**

## 結論 (先に読むこと)

- **裁定 R4 (a) が要求した 3 測定をすべて取得した。** gen_S の非 study probe
  (request `0:896504.nqsv`、node `bnode028`、633 秒)。
  - (i) 待機後の `/proc/stat`: **13 窓すべて `valid`、すべて `[0, 1.0]`、最大 `0.0791`
    core-equivalents** (上限の 7.9%)。窓長も全窓が `10.000 ± 0.100` 秒以内。判定 **`feasible`**。
  - (ii) **`CCBENCH_TRACE=1` の build が通った** (`stock`)。witness ゼロの状態が解消。
  - (iii) **compiler の realpath・`--version`・bytes SHA-256 を取得**。
- **`a03` の許容範囲 `[0, 1.0]` は初版から変えていない。閾値を観測から作っていない。**
  判定写像は probe の実行より前に commit してある (`derivation-map.md` と契約 blob)。
- **敵対検証が親の設計を 2 度倒した。**
  1. 段 3: 親の導出写像 `max(1.0, ceil(U) + 0.5)` は `U ≤ 3.5` の全域で観測を必ず含み、
     core §14 の「実現値を必ず含む許容範囲」の禁止に該当した。
  2. 段 6: 差し替えた梯子 `{1.0, 2.0}` も成功域で `T(U) ≥ U` となり**同型**だった。
     `U = 1.01` は `[0,1.0]` を否定する証拠なのに、その観測自身が `[0,2.0]` への拡大を
     発火させ即受理される。「`2.0` = 他テナント 1 thread」という物理的説明も誤り
     (1 thread 100% の寄与は `1.0`)。
  → 最終形は「閾値を作らず、事前登録された `[0,1.0]` の成否を 3 値で返す」。
- **実測が既存の追補 A の誤りを 2 件確定させた。**
  `a04` の「予備 2 本が吸収する」は core §9 に照らして**偽**。
  `a08` の「唯一の差は `-DCCBENCH_TRACE`」も**偽** (compiler の渡し方が異なる)。
- **`load1` を判定に使わない選択が実データで裏付けられた。** `post-03` は
  `load1 = 3.33` に対し実測 busy は `0.0150` core-equivalents で 2 桁以上乖離する。
- **凍結していない。**承認は `package.md` の Q1〜Q5 でユーザーへ返す。段階 1 で終端。
- **凍結 core の bytes は 1 byte も変えていない** (`ac939af4…`)。

## 一次資料

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (親の provisional 裁定 P1〜P6 を含む) |
| `s4-adjudication.md` | 段 4 裁定 (段 3 の 16 blocker を real/refuted 判定。梯子案はここで導入され、段 6 で倒れた) |
| `derivation-map.md` | **判定写像 (probe より前に凍結)。倒れた 2 案とその理由を逐語で残す** |
| `submission-receipt.md` | 投入前 receipt + append-only の submission 台帳 (2 attempt) |
| `addendum-a-reissue.md` | **追補 A 再発行版** |
| `package.md` | **凍結承認パッケージ (Q1〜Q5)** |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 7 件の事前登録と結果 (7/7 検出、SURVIVED 0) |

段 2 プラン・段 3 の 2 レンズ・段 6 の 2 レビュー・焦点再レビュー・fix 8 巡の逐語は
repo 外の job artifact (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-r4-probe/`) にある。

## 実測成果物

`output/env/pegasus/t139-r4-env-probe/` に 2 attempt 分を残す。
attempt 1 (`0:896500.nqsv`) は窓 0 件の `incomplete` で、原因は環境ではなく自作 validator の
1 行 (`compile_commands.json` の `command` 文字列形式を拒否) である。
**窓 0 件なので再走 gate に該当せず、規律上も再投入が許される場合だった。**
