# 段 6 裁定 — レビュー 2 本 (review-a.md RV-1〜3、review-b.md B1〜B5) の採否 (2026-09-29 06:12 JST、date 実測)

| ID | 裁定 | 内容 |
|---|---|---|
| RV-1 / B1 帰属未証明 | real (must-fix) | 全件出力の再走 j1-c・j2-c を親が raw (verifier JSON の witness・trace の C/R/W 行・stderr の事象行) で照合し、帰属した witness を 1 つずつ実例で示す。3 本中 2 本以上が R4 の「期待した経路で検出」を満たさなければ、判定を緩めず段 4 へ戻る (照合範囲を witness に関係する事象へ絞る局所修正を裁定する)。 |
| RV-2 stale-read の READ_WTS_MISMATCH 43 | real (観察) | 判定・帰属の値を変えない: R 行は読んだ時点の保存 wts、帰属の a_wts も同じ時点の値で、両者は同じ源から来る。機序は「壊し patch が GC の回収対象になりうる古い版を読み、版 object が再利用された」と推定するが未検証と一次資料に書く。stock では 0 であり、C1 (読んだ時点の保存) が要った実例として記録する。txid・key の特定は後続の backlog (成果物の値を変えないので本 wave では足さない)。 |
| RV-3 TRACE=0 の比較範囲 | real | 主張を「YCSB target (ycsb_cicada.exe) の transaction.cc・ycsb_cicada.cc・util.cc の 3 TU」に限る。tpcc / bomb / sbomb の TU (同じ header を include) は未比較と一次資料・README に書く。 |
| B2 壊し run 自身の健全性 | real (should) | 分類の受理に、壊し run 自身の integrity 数値項目 0・C 行 = commit 数を親が raw で確認して加える (値は result JSON に記録済み、起動器は変えない)。違反があれば「期待した経路で検出」に数えない。 |
| B3 README・一次資料・fragment | real | 段 7 で親が書く (予定どおり)。 |
| B4 全件出力と焦点 job | refuted (現状維持) | 帰属に必要な分だけ使った。88.5 MiB 程度の stderr は起動器で扱える量。焦点 job は未使用なら実行しない。 |
| B5 凍結 hash | 採用 (保持) | 登録簿が完全一致を要求するため保持。 |

変異 (DW-M08): dispatch final は最終実装 commit で M-V1 だけ (期待 = s4-ruling R6 erratum の新 HEAD 4 node で KILLED)。旧 HEAD の観測は login self-run (同 erratum) を使い、dispatch では繰り返さない (B 観点 5 の指摘を採用)。
