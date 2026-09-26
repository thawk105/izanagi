## 変更

- [t2273lc_run_series.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe/tools/t2273lc_run_series.sh)、[t2273lc_run_measure.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe/tools/t2273lc_run_measure.sh)：job dir・slug を T-2273 用に変更し、台帳 1 ファイル限定の差分検査を外しました。門番、flock、`submissions.log` との突合、HEAD・clean の前後照合、無効対の同順序再試行は維持しています。
- [t2273lc_run_warm.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe/tools/t2273lc_run_warm.sh)、[t2273lc_gate.conf](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe/tools/t2273lc_gate.conf)：前回の温め手順と門番設定を維持。両 tree の `warm-A.json`・`warm-B.json` を系列開始の前提とします。
- [t2273lc_ab_analyze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe/tools/t2273lc_ab_analyze.py)：台帳固有の集計を除き、走表、対差・対率の各中央値、`land_condition`、5 分目標、collection・selected 集合の照合を JSON と Markdown に出します。

## 実走

前回データを読み取り専用の Python inline コマンドで解析しました。W_0 は `482.215 / 334.439 / 310.663 / 511.326 / 374.494 / 344.931` 秒、対差は `147.776 / 200.663 / 29.563` 秒で README §6 と一致。03-B は infra 無効走として扱われました。`bash -n` は 3 本とも成功し、Python 構文検査も成功しました。実受入は投入していません。

## 使い方

親が 5 ファイルを job dir 外へ退避し、`measurement-tips.json` を用意した後に実行します。

```bash
bash t2273lc_run_warm.sh A
bash t2273lc_run_warm.sh B
bash t2273lc_run_series.sh
python3 t2273lc_ab_analyze.py --job /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy
```

既定系列は `01 A 1`、`02 B 1`、`03 B 2`、`04 A 2`、`05 A 3`、`06 B 3`。infra 無効走の分類後は、次の番号と同じ対順序を引数で指定して再開します。集計出力は job dir の `analysis/analysis.json` と `analysis/analysis.md` です。

## 総括

指定の 5 ファイルだけを作成し、docs 編集・commit はしていません。前回データでの抽出と対差を確認済みです。固定 2 tree は同一 node・同一 allocation ではなく、時刻の近さは隣接逐次投入によります。