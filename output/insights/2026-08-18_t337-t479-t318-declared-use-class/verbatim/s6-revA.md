## 所見

### 1. AST 閉包の直接形 — refuted / nit

`test_p3_exploration_namespace.py:92-105` は `campaign/*.py` を `glob` で動的走査している。現在の 6 producer は全て検出され、宣言欠落なら `:500-508` が落ちる。

成果物影響: 現行の直接呼出し形では certified 選択・材料レポート・proof chain は変わらない。

### 2. AST 閉包の実効性 — real / must-fix

`test_p3_exploration_namespace.py:540-562` の負例は `_discover_campaign_drivers()` を通らず、ローカル関数で判定している。固定 tuple へ戻す変異に落下 node はない。また `:40-72` は `layout_module.exploration_campaign_layout()` や別名呼出しを検出しない。

成果物影響: 宣言なしの新規 producer が meta-test 外へ漏れ、未監査の campaign が official/exploration の受理・台帳・材料レポートへ入る。

### 3. 既存 producer の再束縛 — real / backlog

`test_p3_exploration_namespace.py:75-89,527-534` は最初の module-level 宣言と AST 上の `Name` しか検査しない。後続の再代入や local shadowing は検出しない。`declared_use_class="official"` の自己申告自体も `loop.py:142-149` で受理される。

成果物影響: 将来の探索 producer が official root へ誤配線され、下流の受理集合と proof chain の所在を誤らせる。

### 4. 受理集合と拒否順 — refuted / nit

`loop.py:142-182` は `official` / `exploration` のみを受理し、`qualification` / `dry` / 未知値を cid 計算・`layout.ensure()` より前に拒否する。`test_campaign.py:8501-8532` が cid 呼出しなしと出力未生成を固定している。

成果物影響: 本差分による受理集合の拡大はなく、従来の省略時 official はむしろ拒否へ縮小する。

### 5. `campaign_namespace` 迂回 — refuted / nit

`loop.py:132-149` に旧引数・shim はなく、実行コードの検索でも残るのは負例 assertion `test_campaign.py:8429` だけである。

成果物影響: 旧 selector による宣言・実配線の二重化は発生しない。

### 6. 既存テストの弱体化 — real / must-fix

`test_p3_exploration_namespace.py:509-515` は layout 呼出しを「1 件以上」としか見ず、`:527-537` も全 run 呼出しの個数や余分な official path を検査しない。差分で旧来の個数・集合 assertion が削除されている。

成果物影響: 既存 producer の余分な root/WAL/run が緑になり、certified 選択、材料レポート、proof chain の試行集合が増えうる。

### 7. path 不変 — refuted / nit

`layout.py:222-225,479-487` は無変更で、8c の `exploration_campaign_layout` / trial-local `CampaignLayout` も `p3_autonomous_workload_trial.py:2831-2836` のままである。runtime root 検査は `test_p3_exploration_namespace.py:444-450,493-497` にある。

成果物影響: 既存 6 producer の出力 root、freeze bytes、output 配下に本差分による変化はない。

### 8. campaign-id 不変 — refuted / nit

`loop.py:169-182` では宣言値を config へ入れず、`:181` で従来どおり cid を計算する。`test_campaign.py:8535-8558` が official/exploration の cid 一致を固定している。

成果物影響: certified 選択、材料レポート、proof chain の campaign-id は変わらない。

### 9. caller 移行 — refuted / nit

独立 AST 集計は production 15 件中 15 件が宣言付き、test は 30 件中 29 件が宣言付きだった。残る `test_campaign.py:8440-8447` は省略時 `TypeError` を検査する意図的負例である。production の未移行は 0 件。

成果物影響: production caller の実行時 `TypeError` は残っていない。

### 10. 実装子報告の数値 — real / nit

`s5-author.md:8` の production 15、test 30、6 producer、別 API の floor caller 1 件と test 9 件は再測値と一致する。floor API は `s8b_floor_campaign.py:5585-5593` で別署名である。ただし `s5-author.md:4` の「公式 caller 8 file」は誤りで、正しくは 8 call / 7 file。pytest 未実走の記載 `:11,24` は妥当で、緑とは数えていない。

成果物影響: caller file 数の誤記だけで、成果物 bytes や受理集合は変わらない。

## 総括

- 現行の直接形では 6 producer 全てを検出し、production caller 15 件に欠落はない。
- qualification / dry の拒否順と cid 不変は実装・静的検査とも成立している。
- `campaign_namespace` の実行経路は消えている。
- must-fix は AST 閉包の固定 tuple 退化・別名経路と、削除された個数 assertion。
- 自己申告の official 化は既存の scope 外残余であり backlog とする。
- path、campaign-id、freeze/output の差分はない。
- pytest は実走していない。編集・commit も行っていない。