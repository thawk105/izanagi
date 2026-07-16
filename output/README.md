# output — 全成果物

探索の全成果物をここに置く。**二軸構成 (D13)**: 成果物は「入力 (workload spec) に依存するか」で置き場を分ける。

```
output/
├── campaigns/<campaign-id>/      入力ごとの探索 (= 入力依存。campaign スコープ)
│   ├── campaign.lock             同一性の正準 pre-image
│   ├── spec/                     凍結した入力 spec
│   ├── runs/wal.jsonl            評価の WAL (env tag・測定値・gate結果 = forensic binding)
│   ├── variants/                 variant source/patch と build identity
│   ├── reports/                  report・plot・provenance の決定論的射影先
│   └── insights/                 campaign 固有 insight / whiteboard
├── env/<env-tag>/                環境ごと・入力非依存 (= 測定の物差し。env スコープ)
│   ├── calibration/              レコード数飽和点 + noise floor (within-run / between-run, A2)
│   └── profile/                  perf 機序プロファイル (spin 分離・有用 IPC 等, P2-4)
├── insights/                     CCBench 還元すべき発見 / calibrator・探索の妥当性文書
├── s1-freeze/                    S-1 の known-axes / measurement freeze (両者とも生成済み)
├── s1-budget/                    S-1 計測の時間台帳 (time_ledger.json)
├── s6-rounds/                    S-2/S-3 提案ラウンドの匿名化・採点・集計 provenance
├── s8b-freeze/                   段 8b holdout freeze (holdout_freeze.json)
└── reports/                      campaign 横断の材料レポート (s_prime_final_report.md, s1_direct_comparison/)
```

`<campaign-id>` = `<spec-slug>-<search-tag>-<cfg-hash8>` (内容ハッシュ、D13)。`<env-tag>` = `linux-baremetal` 等。

`s1-freeze/`・`s1-budget/`・`s6-rounds/`・`s8b-freeze/`・`reports/` は campaign をまたぐ登録済み主実験の
補助成果物である。`s1-freeze/` には `known_axes_freeze.json` と `measurement_freeze.json` (freeze v2、
18 セル・比較対・schedule・実装 hash) が生成済みで、後者は S-1 計測開始 gate を閉じる時点で凍結した。
`s6-rounds/` は独立セッションの提案・匿名化・採点を結ぶ記録であり、通常の campaign 出力ではない。

## なぜ二軸か (D13)

- **campaign スコープ (入力依存)**: fitness・材料レポートは入力 workload ごとに変わる。campaign-id は spec の**中身** + ccbench-commit + 探索 config のハッシュなので、入力が変われば別 campaign になる (honest-by-construction)。
- **env スコープ (入力非依存)**: calibration (レコード数・noise floor) と profile は「測定の物差し」であって variant の fitness ではない。(env, thread数, 代表 workload) ごとに決まり入力非依存なので campaign と分ける。

## proof chain の扱い

- `campaign.lock` と `campaigns/*/runs/` は proof chain の保護対象である。COMMIT/fitness を記録する唯一の
  経路は `pipeline.evaluate()` であり、直接編集・削除・移動しない。
- `reports/` と `insights/` は生成物・散文を置く射影先で、機械防護の対象外である。ただし WAL や source
  identity と矛盾する根拠を後から書き換えてよい意味ではない。report は入力証拠を参照可能に保つ。
- throwaway な生 trace・一時バイナリ・ローカルの実行残骸は追跡しない。必要な再現根拠は WAL、lock、凍結
  spec、report/provenance、または insight に構造化して残す。

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
