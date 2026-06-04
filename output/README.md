# output — 全成果物

探索の全成果物をここに置く。

```
output/
├── variants/   生成された CC (パラメータ設定 / diff)
├── runs/       ベンチ結果の生ログ (.gitignore 対象)
├── reports/    層3が吐く説明レポート (新CC + 理由 + 試行ログ)
└── insights/   CCBench に還元すべき発見、calibrator の妥当性文書
```

## insights の使い方

探索中に CCBench 自体の問題を見つけたら、ここに構造化レポートを吐く。例:

```
output/insights/YYYY-MM-DD_invisible-reads-anomaly.md
  - 発見: invisible reads + early validation の組み合わせで G2 anomaly
  - 再現条件: 10thread, 4m records, write-ratio 0.5, seed 42
  - 該当コード: ccbench/silo/validation.cc:142 付近
  - 仮説: early validation時に read set の version 再チェックが漏れている
  - CCBench論文との関係: I2 の invisible reads の前提を破っている可能性
  - 還元判断: ユーザー確認待ち
```

**必ず「還元判断: ユーザー確認待ち」を付ける。** AI は発見を構造化するところまで。上流 CCBench へ PR を出すかは人間 (ユーザー) が判断する。誤検出 (verifier のバグを CCBench のバグと誤認) を防ぐ関所。

calibrator もここにレコード数決定の妥当性を文書化する。
