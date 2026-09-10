# [T-2048] floor 予約予算 drift の解消

## 結論

現行実行経路の authority を追うと、値の役割は次のとおりだった。

| 値 | 役割 |
|---:|---|
| 28200 | 12-cell 本体の subtotal |
| 1800 | `sort_best` の共有 dependency prebuild (configure 900 + target 900) |
| 30000 | driver の `required_s` |
| 600 | finalize reserve (`safety_margin_s`) |
| 30600 | driver preflight の minimum envelope |
| 36000 | PBS scheduler request / policy 期待値 / qstat 実効 limit |
| 5400 | scheduler request と driver minimum の raw headroom |
| 約4500 | prologue 約900秒を仮定した estimated residual。保証値・実測値ではない |

`tools/pegasus/floor_campaign.sh` と `tools/pegasus/README.md` は [T-1128] の共有 prebuild
導入前の `required_s=28200` / 合計 28800 を現行値として残していた。shell コメントと README §5 を
上表へ揃え、同じ2領域を production calculator から導出して検査する focused test を追加した。

## authority dataflow

1. job script の `#PBS -l elapstim_req=10:00:00` が scheduler への要求宣言。
2. `floor_v1.json` の `floor_walltime_s=36000` は期待値と submit receipt 値。
3. job は qstat の `(Per-Req) Elapse Time Limit` と policy の一致を fail-closed で検査し、
   実効 36000 秒を reservation env へ渡す。
4. driver は現行 protocol / cells / schedule から `required_s=30000` と finalize 600 を導出し、
   合計 30600 が実効 reservation 内に収まることを検査する。

D87 の 28200 / 28800 は決定時点の歴史値なので改稿していない。scheduler 36000、policy、calculator、
protocol、freeze、official guard の値・受理集合も変更していない。shell bytes は変わるため、将来の
新規 submission は新しい source commit / script hash / receipt / 測定世代へ束縛される。既存 receipt は
再解釈しない。R33 の pin 対象は oracle/n-pilot driver/job であり、今回の floor 2ファイルではない。

## review と fix

- 段2 planner は「policy値をqsubの `-l` へ渡す」という親 brief の誤りを摘出した。実要求源は
  job script の PBS directive である。
- 段3は `28200` 自体が正しい subtotal であり全面禁止できないこと、4500が推定値であること、
  script comment変更も将来のproof-chain identityを変えることを摘出した。
- 段6 review A は説明変異を既存runtime testが観測しないことを real / must-fix とした。
  D95 fix worker が既存 floor-tools test fileへ2つのfocused oracleを追加した。
- 初回 baseline は shell block終端が後続実行行まで含むため1件赤。D95 fix round 2で一意な
  `set -Eeuo pipefail` anchorの直前へ終端を直し、値・regex意味は不変のまま閉じた。

plan / consult / author / review / fix / focus の逐語と launcher receipt は repo 外の耐久 job directory
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2048-floor-budget-drift/` にあり、各 output は
`tools/check_codex_output.py` rc=0。raw mutation JSONも holdout clean-scanを汚染しないよう同 directoryへ
置いた。

## 変異 matrix

固定 commit `57348d7a6`、spec SHA-256
`be96ae99e1b22bab9f670b2ca2d3fe6359c9e2ebdad9c99eec84f7ba4dec9c9c`。

| 変異 | 結果 | 失敗 node |
|---|---|---|
| M1 shared prebuildを落とし旧requiredへ戻す | KILLED | shell budget comment oracle |
| M2 raw / estimated residual headroomを入れ替える | KILLED | shell budget comment oracle |
| M3 READMEを旧28800 envelopeへ戻す | KILLED | README §5 oracle |

baseline 2/2 passed。KILLED 3、SURVIVED 0、MISMATCH 0、TIMEOUT 0。
raw result SHA-256 = `a1cfd187869bed328c9ecfb55b786c1c8d92626105afb7cc3041c0109c97d78e`。
共有 main の並行変更で初回 wrapper終端がrc=125になったが、結果を増やさない `--resume` がrc=0で
後検査・cleanupを完了した。失敗した旧baseline runは変異0件のまま保存した。

## 受入

- pre-record acceptance: 18248 collected、18187 passed、61 skipped、赤0、`child-green`。
- tested main = `254b0f50671175fa8d5e9b97db46897e01c786dc`。
- tested tip = `b6a3735756cbc1d07f35bababcad4177018d11cb`。
- receipt SHA-256 = `7dd96ceb68515a1b4c937975626266a53697def9805d41926147a800a7845652`。
- `tools/check_docs.py` rc=0、implementation/fix各commit後の全履歴 provenanceは新規違反なし。
- final acceptance、`check_codex_agents`、記録後 `check_docs` / provenance は記録commit後に実行する。

## dev-wave 改善候補

なし。今回の停止は既存契約が意図どおり検出したもので、手順正本の欠落・曖昧は実測していない。
