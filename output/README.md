# output — 全成果物

探索の全成果物をここに置く。**二軸構成 (D13)**: 成果物は「入力 (workload spec) に依存するか」で置き場を分ける。

```
output/
├── campaigns/<campaign-id>/      入力ごとの探索 (= 入力依存。campaign スコープ)
│   ├── runs/wal.jsonl            評価の WAL (生 tps + leading indicators + 実行コマンド = forensic binding)
│   └── reports/                  材料レポート (.dat[再現コマンド] + .plt + .png + report.md)
├── env/<env-tag>/                環境ごと・入力非依存 (= 測定の物差し。env スコープ)
│   ├── calibration/              レコード数飽和点 + noise floor (within-run / between-run, A2)
│   └── profile/                  perf 機序プロファイル (spin 分離・有用 IPC 等, P2-4)
├── insights/                     CCBench 還元すべき発見 / calibrator・探索の妥当性文書
└── runs/silo-sample/             参照用サンプル trace (verifier 用。throwaway な生 trace は置かない)
```

`<campaign-id>` = `<spec-slug>-<search-tag>-<cfg-hash8>` (内容ハッシュ、D13)。`<env-tag>` = `linux-baremetal` 等。

## なぜ二軸か (D13)

- **campaign スコープ (入力依存)**: fitness・材料レポートは入力 workload ごとに変わる。campaign-id は spec の**中身** + ccbench-commit + 探索 config のハッシュなので、入力が変われば別 campaign になる (honest-by-construction)。
- **env スコープ (入力非依存)**: calibration (レコード数・noise floor) と profile は「測定の物差し」であって variant の fitness ではない。(env, thread数, 代表 workload) ごとに決まり入力非依存なので campaign と分ける。

## insights の使い方

探索中に CCBench 自体の問題を見つけたら、ここに構造化レポートを吐く。例:

```
output/insights/YYYY-MM-DD_<topic>.md
  - 発見: 何が
  - 再現条件: thread/records/workload/seed
  - 該当コード: ccbench の file:line
  - 仮説: なぜそうなるか
  - CCBench論文/insight との関係
  - 還元判断: ユーザー確認待ち
```

**CCBench のバグ等を還元する判断には必ず「還元判断: ユーザー確認待ち」を付ける。** AI は発見を構造化するところまで。上流 CCBench へ PR を出すかは人間 (ユーザー) が判断する。誤検出 (verifier のバグを CCBench のバグと誤認) を防ぐ関所。

insights には CCBench 還元候補だけでなく、**探索の妥当性文書**も置く (calibrator のレコード数決定根拠、ケーススタディの機序分析・敵対的検証、measurement 汚染インシデント等)。「なぜそのレコード数/floor/結論か」を査読に先回りで答える材料。
