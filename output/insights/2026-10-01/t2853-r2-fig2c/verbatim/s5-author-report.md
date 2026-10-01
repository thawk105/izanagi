wrapper を作成し、指定の実走を終えました。**control は `artist_series` 一致・`data` 不一致で rc=1**。不一致を除去して成功扱いにはしていません。

## 総括

作成物: [scratch/t2853_r2_fig2c_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/t2853_r2_fig2c_plot.py)

SHA256:
```text
652f6b5cbf080372b7e77e1bb9f2b8d653b91c24de4966ddbaaa87474db23c97
```

実走結果は次のとおりです。**全 argv・rc・ログ**を [results.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/out/final/results.json)、照合結果を [verification.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/out/final/verification.json) に保存しました。

| 実走 | rc | 結果 |
|---|---:|---|
| `control` | 1 | 9系列完全一致。`data` は下記3箇所だけ不一致 |
| `r2` 原 attempt 見立て | 0 | PNG・PDF・provenance JSON を生成。9系列は control と完全一致 |
| `table` 原 vs 原見立て | 0 | 29点 × 3 workload。1000 µs は「F718 除外」と明記 |
| SHA256 不一致生成器 | 2 | 図なし |
| 存在しない root | 2 | 図なし |
| 存在しない group | 2 | 図なし |
| DAT 1行改変 | 2 | `completion artifact digest mismatch: write-heavy/dat`。図なし |
| 追加負例: 上記 completion のハッシュも更新 | 2 | `dat throughput is not the WAL center at write-heavy/0us`。図なし |

control の不一致は、3 workload の `campaign_verifier_epoch` に現行依存が追加した次のフィールドだけです。全測定点・CI・描画系列は原 provenance と一致しました。

```text
verifier_assessment_basis:
  原図: フィールドなし
  現行: recorded-at-original-verifier-epoch
```

[R2 見立て PNG](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/out/final/r2-surrogate.png)・[PDF](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/out/final/r2-surrogate.pdf)・[provenance](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/out/final/r2-surrogate.provenance.json)では、caption と図中タイトルの両方が R2 の役割語になっています。既存のレイアウト検査も通過しています。

[対照表](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/out/final/comparison.md)の抜粋:

| workload / backoff | 原: M tps ± CI95 | R2見立て: M tps ± CI95 | abort fraction（両側） |
|---|---:|---:|---:|
| write-heavy / 0 µs | 2.393719 ± 0.088854 | 2.393719 ± 0.088854 | 0.789600 |

正しさ集計は、**両側それぞれ**次の結果です。参照2 variant も含みます。

| workload | variants | certified: true | anomalies | verdict |
|---|---:|---:|---:|---|
| write-heavy | 31 | 31 | 0 | serializable: 31 |
| balanced | 31 | 31 | 0 | serializable: 31 |
| read-heavy | 31 | 31 | 0 | serializable: 31 |

各 group の合計は93 variant、certified 93、anomalies 0です。

各サブコマンドの CLI は、実走した指定を変数で表すと以下です。

```bash
TASK_REPO=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author
WRAPPER="$TASK_REPO/scratch/t2853_r2_fig2c_plot.py"
GENERATOR="$TASK_REPO/tools/plotting/plot_b10_extended_backoff.py"
ORIGINAL=/work/1/SFC/tanab/b10-backoff-grid-runs5
GROUP=b10-backoff-grid-20260826T234647Z-783837
OUT="$TASK_REPO/scratch/out/final"

python3.10 -B "$WRAPPER" --generator "$GENERATOR" control \
  --measurement-root "$ORIGINAL" \
  --reference-provenance "$TASK_REPO/docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json" \
  --out-prefix "$OUT/control"

python3.10 -B "$WRAPPER" --generator "$GENERATOR" r2 \
  --measurement-root "$ORIGINAL" --group "$GROUP" \
  --out-prefix "$OUT/r2-surrogate"

python3.10 -B "$WRAPPER" --generator "$GENERATOR" table \
  --original-root "$ORIGINAL" --r2-root "$ORIGINAL" --r2-group "$GROUP" \
  --out "$OUT/comparison.md"
```

実データでは R2 側の root/group を指定値に変更し、新しい出力先を使います。既存出力への上書きは拒否します。

- **差し替え:** `GROUP_ID`、`SUBMIT_PATH`、`SUBMISSION_NONCE`、`WORKLOAD_SPECS` の job/host/campaign/identity、`CANONICAL_SHA256`、出力閉包用の `REAL_OUTPUT_PATHS`、caption・図中の役割語。control は入力定数・文言を変えず、出力閉包の宛先だけ変更します。
- **維持:** `REPOSITORY_COMMIT`、`CCBENCH_COMMIT`、`JOB_SCRIPT_SHA256`、既存 admission・DAT/WAL・固定条件・CV 関連検査、F718、CI 計算、`_validate_text_bboxes`、provenance 意味検査・external/closure 検査。全31 variant の正しさ確認を追加しています。
- **不変確認:** 生成器・依存の SHA256 は作業前後で一致。`git status --porcelain` は `?? scratch/` のみ。tracked file 編集・commit なし。
- **未実走:** 本物の R2 データによる描画・表生成。
- **懸念・制約:** wrapper 自体は repo 外へ移せますが、図の出力先は既存生成器のパス契約により generator の repo 内に限定します。また abort rate は生成器が照合する DAT/WAL の集約 fraction です。反復別データからの平均とは称さず、表にその限界を明記しました。