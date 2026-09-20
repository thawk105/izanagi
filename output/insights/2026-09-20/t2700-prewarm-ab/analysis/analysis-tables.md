## 判定

成功走で早期起動が最遅 shard の wall を短縮 (探索閾値 15 秒以上) + 腕別失敗件数 E=3, L=0

未達

成功走に条件付き。15 秒は便宜的探索閾値であり母効果 ≥15 秒の証明ではない。

H は worker collection-finish 最大時刻（E の待ち込み）、D は最初の test 開始。D−H は純解決所要ではない。

必要対数は効果・分散・裾の仮定に依存し確定できない。

## 走表

| run | condition | pair_slot | classification | W_max | used_in_pair | over_budget | post_cutoff | sequence_violation | reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | E | 1 | success | 386.304 | True | False | False | False | [] |
| 02 | L | 1 | success | 508.613 | True | False | False | False | [] |
| 03 | L | 2 | success | 505.187 | True | False | False | False | [] |
| 04 | E | 2 | success | 481.871 | True | False | False | False | [] |
| 05 | E | 3 | success | 481.021 | True | False | False | False | [] |
| 06 | L | 3 | success | 503.015 | True | False | False | False | [] |
| 07 | L | 4 | success | 511.599 | False | False | False | False | [] |
| 08 | E | 4 | red |  | False | False | False | False | ["pytest/report failures"] |
| 09 | L | 4 | success | 533.868 | True | False | False | False | [] |
| 10 | E | 4 | success | 494.465 | True | False | False | False | [] |
| 11 | E | 5 | success | 495.09 | True | False | False | False | [] |
| 12 | L | 5 | success | 536.853 | True | False | False | False | [] |
| 13 | L | 6 | success | 478.046 | False | False | False | False | [] |
| 14 | E | 6 | red |  | False | False | False | False | ["pytest/report failures"] |
| 15 | L | 6 | success | 517.861 | True | False | False | False | [] |
| 16 | E | 6 | success | 484.368 | True | False | False | False | [] |
| 17 | E | 7 | red |  | False | False | False | False | ["pytest/report failures"] |
| 18 | E | 7 | success | 484.545 | True | False | False | False | [] |
| 19 | L | 7 | success | 513.617 | True | False | False | False | [] |
| 20 | L | 8 | success | 521.725 | False | False | False | False | [] |

## 対表

| slot | E | L | delta_W | r | delta_D_0 | delta_H_0 | delta_O_0 | delta_tail_0 | shard_delta_W |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 01 | 02 | 122.30900000000003 | 0.3166133407886018 | 24.871543407440186 | 0.4393165111541748 | 98.39795678600001 | -0.00016929244992525128 | [122.30900000000003, 0.7709999999999866, -2.741000000000014] |
| 2 | 04 | 03 | 23.31600000000003 | 0.04838639386889859 | 26.744195461273193 | -0.022641897201538086 | -3.43722586399997 | 0.0073001537323307275 | [23.31600000000003, 3.1200000000000045, 39.97399999999999] |
| 3 | 05 | 06 | 21.99399999999997 | 0.045723575477993626 | 40.68772888183594 | -2.357016086578369 | -22.102407130000017 | 0.2899549427032184 | [21.99399999999997, -0.6409999999999911, -1.3220000000000027] |
| 4 | 10 | 09 | 39.40300000000008 | 0.07968814779610302 | 37.06484389305115 | -0.258624792098999 | 2.692666315999986 | 0.008288028717117868 | [39.40300000000008, 0.7179999999999893, 3.8310000000000173] |
| 5 | 11 | 12 | 41.76299999999998 | 0.08435435981336722 | 32.77427268028259 | -1.1718051433563232 | 6.903128639999977 | 0.2925734405517346 | [41.76299999999998, -6.197000000000003, -47.56700000000001] |
| 6 | 16 | 15 | 33.492999999999995 | 0.06914783800746539 | 34.63461422920227 | -0.7029232978820801 | -0.7019339290000062 | -0.004889041900639768 | [33.492999999999995, -1.9579999999999984, -0.1869999999999834] |
| 7 | 18 | 19 | 29.071999999999946 | 0.05999855534573661 | 30.19896936416626 | -0.09315013885498047 | -1.5902313760000197 | 0.0045766563414986194 | [29.071999999999946, -1.460000000000008, -3.837999999999994] |

## 中央値・検定

{
  "medians": {
    "paired_difference": 33.492999999999995,
    "paired_ratio": 0.06914783800746539,
    "difference_of_condition_medians": 29.248999999999967
  },
  "wilcoxon": {
    "m": 7,
    "W_plus": 28.0,
    "one_sided": 0.0078125,
    "two_sided": 0.015625,
    "method": "exact sign enumeration, average ranks, zeros removed"
  },
  "t": {
    "statistic": 3.3503951910930834,
    "df": 6,
    "critical_5pct_two_sided": 2.447,
    "note": "SD=0: descriptive only; critical table available for df 1..19"
  },
  "sigma_d": 35.12398745803759
}

## 失敗集計

{
  "analysis_cutoff": 20,
  "failures": {
    "E": {
      "attempts": 10,
      "counts": {
        "success": 7,
        "red": 3
      }
    },
    "L": {
      "attempts": 10,
      "counts": {
        "success": 10
      }
    }
  },
  "post_cutoff": {
    "E": {
      "attempts": 0,
      "counts": {}
    },
    "L": {
      "attempts": 0,
      "counts": {}
    }
  },
  "failure_sign_sensitivity": {
    "wins": 7,
    "losses": 3,
    "one_sided_p": 0.171875,
    "note": "Each failed attempt is an arm loss; unknown/both-arm failures retained in counts. Not a paired speed estimate."
  }
}

## 感度

正規成分 SD σ + 両腕独立の遅延 (各 15 %、+30〜90 秒 / −30〜90 秒) の対称 model。σ は対差全体の SD ではない。

| model | delta | sigma_d | n | R | seed | power |
| --- | --- | --- | --- | --- | --- | --- |
| normal | 15 | 35.12398745803759 | 7 | 2000 | 20260920 | 0.185 |
| normal | 20 | 35.12398745803759 | 7 | 2000 | 20260920 | 0.2925 |
| normal | 27 | 35.12398745803759 | 7 | 2000 | 20260920 | 0.47 |
| normal + independent 15%/15% tails | 15 | 35.12398745803759 | 7 | 2000 | 20260920 | 0.1365 |
| normal + independent 15%/15% tails | 20 | 35.12398745803759 | 7 | 2000 | 20260920 | 0.217 |
| normal + independent 15%/15% tails | 27 | 35.12398745803759 | 7 | 2000 | 20260920 | 0.335 |

## 記述的対照 (射影)

{
 "sessions": 42,
 "W_median": 491.35400000000004,
 "W_min": 353.767,
 "W_max": 636.772,
 "D_median": 60.79226052761078,
 "D_min": 59.029196977615356,
 "D_max": 94.5134265422821,
 "timestamps": [
  "2026-09-20T10:16:57.726633+09:00",
  "2026-09-20T17:44:54.901118+09:00"
 ],
 "hooks": [
  "configure_node"
 ]
}
