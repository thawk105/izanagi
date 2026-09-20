## 検査結果

以下はすべて rc=0 でした。

```bash
python3 probe-t2802/t2802_ab_analyze.py --selftest
python3 probe-t2802/t2802_diff_probe.py --selftest --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe --base-module /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/verbatim/base-module/s8b_holdout_admission_base.py
bash -n probe-t2802/run-measure.sh
bash -n probe-t2802/run-series.sh
bash -n probe-t2802/run-warm.sh
```

集計器は既存検査と追加負例に PASS。差分 probe は **40/40 状態一致**、不一致なし、比較器の stub 正例対照は期待どおり rc=1 でした。

launcher の abort 検査結果：

|検査|rc|
|---|---:|
|引数不足|2|
|tips 不在（メモリ上で JOBDIR を置換）|2|
|仮想11走の件数計算・上限分岐|0|
|仮想12・13走の件数計算・上限分岐|各92|

dummy 走ディレクトリは作成していません。測定走・warm-up は未起動です。

## 総括

所有5ファイルを修正しました。変更後の行数は以下です。

|ファイル|行数|
|---|---:|
|`probe-t2802/run-measure.sh`|209|
|`probe-t2802/run-series.sh`|76|
|`probe-t2802/run-warm.sh`|71|
|`probe-t2802/t2802_ab_analyze.py`|513|
|`probe-t2802/t2802_diff_probe.py`|427|

|所見|状態|対応|
|---|---|---|
|A-M1|closed|全系列の隣接性・slot順序・対全体の再試行を検査。指定の非隣接例は有効0対|
|A-M2|closed|flock内の12走上限、再開時分類、固定終了、`series-invalid` 判定を実装|
|A-M3|closed|warmの前後状態・dispatch・pyc証跡を保存し、系列と集計器で照合|
|B-S1|closed|2 claim × 2 attempt、coverage不正、legacy v1/v2、正常→改竄→再呼出しを追加|
|nit|closed|Markdownから `F_long`・`r`・top10を除去し、JSONには保持|

差分 probe の状態数は **24 → 40**。closed は実装・指定検査の完了を示し、実測の成功を意味しません。