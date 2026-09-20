## 総括

`t2802_ab_analyze.py` の `analyze()`・`selftest()` のみ変更（+42／−5行）。系列文法違反を `series grammar: <NN-X> ...` として記録し、`series-invalid` にします。判定式・閾値・指標は不変です。

- 反例 `A1,B2,A1,B1,B2,A2,A3,B3` → `series-invalid`。
- infra 分類済みの正規取り直し・先頭走が赤の場合の再開 → 有効3対、判定可。
- 途中状態 `A1,B1,B2` → `insufficient-valid-pairs`、系列無効なし。
- 過去6走・skipped・hash改竄・分類・上限・warm の既存検査も維持。

`python3 probe-t2802/t2802_ab_analyze.py --selftest`：**rc=0、PASS**。