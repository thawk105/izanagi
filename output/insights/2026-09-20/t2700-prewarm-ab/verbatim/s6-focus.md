## 判定と範囲

**測定開始は NO-GO です。** 診断検出・解析締切・統計処理は改善されていますが、系列制御と最終集計の不整合、および request の束縛検算に残件があります。

静的読解と `bash -n` のみ実施しました。pytest・selftest・測定は実行せず、ファイルも変更していません。

以下の略称を使います。

- `analyze`：[probe/t2700_ab_analyze.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab/probe/t2700_ab_analyze.py)
- `history`：[probe/t2700_history_estimate.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab/probe/t2700_history_estimate.py)
- その他の launcher・裁定・ログは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab/` 配下。

## 全所見の対応表

| 所見 | 判定 | 根拠・残余と最小是正案 |
|---|---|---|
| A1 診断検出 | **closed** | `analyze:143–157` が stdout・stderr・child.log を検索し、両 memo prefix と `publication-timeout` を扱う。実生成箇所は receipt memo `69,100–117,687–699`、oracle memo `51,82–102,740–752`。実形式 fixture は `analyze:668–685`。witness は対応 stderr 限定を維持（`251–273`）。裁定 `53` の「stderr」限定記述は docs の nit。 |
| A2 解析締切 | **closed** | `analyze:350–403` が目標対数到達／上限到達で cutoff を固定。失敗件数・符号検定・結論は窓内だけ（`410–432`）。締切後追加による不変性を `615–629` で検査。 |
| A3 slot 進行順 | **closed** | `analyze:378–399` が slot と次腕を追跡し、飛越し・逆戻り・順序違反を拒否。正常取り直しと第一腕失敗を `573–614` で検査。ただし launcher との有効性共有は B1 に残る。 |
| A4 selftest の独立性 | **closed** | 未採用 slot の非隣接負例（`594–608`）、shard-1/2 consumer・正規化（`636–645`）、witness 欠損・重複・hook 違い（`646–651,700–708`）、offset 同一瞬間の H/D/tail 一致（`728–738`）を追加。固定数値期待値の追加は補強 nit。 |
| A5 probe 隔離範囲の説明 | **not-applicable (docs へ)** | レビュー A の根拠は `test_real_repo_serialization.py:6438–6452,6472–6485`。今回の集計器・launcher 修正対象外。「実 repo lock／resolver の統合検査ではない」と記録に残す。 |
| B1 取り直し・終了条件 | **regressed** | 通常の取り直しと停止は `run-series.sh:28–49` で固定された。しかし投入前 abort でも走番号を消費する（`35–41`）ため、新しい連番検算 `analyze:357,380` と衝突する。また単走有効性だけで対成立を数える（series `39–45`）ため、系列検算で無効となる対でも次 slot へ進む。下節の修正が必要。 |
| B2 超過走の混入 | **closed** | A2 と同じ。`post_cutoff` 件数を別枠保存し（`402–419,472–473`）、最終文言にも窓内失敗件数だけを使う（`428`）。 |
| B3 同一走・session の束縛 | **partial** | v2 field、hash、receipt 終端・child_rc・job、開始時刻 ±300 秒は検査（`190–262`）。ただし request の必須引数が**存在すること**を検査しない（`238–250`）。両 request から同じ引数を削除すれば通る。最小修正：session/count/index の存在と一意性、repo_root の存在を必須化し、双方同時欠落の負例を追加。 |
| B4 複製失敗と不発行の分類 | **closed** | `run-measure.sh:105–127` が原本なし／copy失敗／hash不一致／成功を記録。`analyze:138–175` が receipt 複製失敗→artifact、原本不発行→infrastructure、非正常終了で診断欠損→unknown を分離。実診断が残れば treatment-failure を優先。負例は `654–667`。 |
| B5 裾モデル・SD の説明 | **closed** | `analyze:327–336,432,474` が両腕独立15%の対称モデル、σは正規成分SDと明記。裁定 `10` の「L側」の旧説明だけ docs の nit として訂正が必要。 |
| B6 warm 前提 | **closed** | `run-warm.sh:10–19` が完了rc・tipを記録し、`run-series.sh:19–22` が投入前に照合。単走も `analyze:194–195` で検査。これは series 経由の起動契約であり、`run-measure.sh` 単独には投入前拒否がない。 |
| B7 履歴の scheduler／SHA | **closed** | `history:57–69,105–120,138–140` に構成・取得不能件数を追加。request payload hash を repo SHA と誤認しない。適合前N件の規則は `90–91,120` に維持。 |
| B8 予算外の近似 | **closed** | `analyze:300–301` が非ゼロ差20件超を拒否。`739–744` に負例。登録予算内の exact 計算を維持。 |
| B9 機序・exact の説明範囲 | **not-applicable (docs へ)** | `analyze:463–465` は一部説明済み。join後の witness の限界、ΔD₀とΔW_maxの相違、非無作為割付、符号対称性・独立性は README に残す。数値処理の残件ではない。 |
| B10 非landing・再現資料 | **not-applicable (docs へ)** | `s4-ruling.md:94` の docs-only 方針を維持する事項。最終SHA、逐語・hash、consumer抽出元、全attempt／abort索引、解析出力の保存完了は今回の指定資料だけでは閉鎖判定しない。 |

## GO を止める具体的な残件

**B1：投入前 abort が、新しい系列検算を壊します。**

`run-measure.sh:39–40,72–77` は lock取得失敗・門番不成立・tip不一致などで、run directory を作る前に終了します。一方、`run-series.sh:38` は終了理由によらず `NEXT` を増やします。

例えば01が投入前に abort、02-Eと03-Lが正常終了すると、launcher は1対成立として slot 2へ進みます。しかし集計器には01の行がなく、02以降は `number != index+1`（`analyze:380`）で順序違反になります。**予算消費・採用対・判定が変わる新しい不整合です。**

最小修正は、投入前 abort では系列を停止し、走番号を消費しないことです。投入後の記録生成失敗は別扱いとし、番号の再利用で実投入を消さないようにします。

**B1：単走成功を、系列としての有効対成立と同一視しています。**

`--check-run` は `inspect_run` の結果に対して rc 0/1 を返します（`analyze:772–775`）。全走の selected digest 一致、時刻非重複、worktree 一致は `analyze:357–375` にだけあります。この分離自体は契約として明示されています。

しかし launcher は rc=0が2回なら対を数えます。実際、selftest `709–727` には「単走は成功だが系列では無効」のケースがあります。これが実系列で起きると、launcher は次 slot へ進み、集計器は未完了 slot の取り直しを要求します。

最小修正は、**各走後に系列検算も行い、その結果から次腕・slot・有効対数を決めること**です。単走判定の想定外終了も、通常の無効走として反復せず停止すべきです。

**B3：request の欠落検算が空振りします。**

`analyze:240–248` は見つかった引数の値だけを比較します。receipt.request.args と request.args がともに空なら、比較もループも通過します。既存負例 `657` は片方だけを変更するため、引数欠落ではなく両者不一致で落ちます。

repo_root も `249` の既定値に期待値を使うため、欠落を受理します。必須引数・repo_root を必須化し、両複製を同じように欠落させた負例が必要です。これは別session／worktreeの成果物を誤採用し得るため nit ではありません。

## 維持できている機能と検証限界

- **20走目が第一腕の場合：** series `32` が第二腕を投入せず、集計器 `387–401` は第一腕を pending のまま締切にします。対には入らず、窓内の走件数には残り、未達となります。
- **Wilcoxon：** `analyze:290–306` の平均順位・ゼロ除外・符号全列挙は維持。反例5件と m=0 は `480–486` に残っています。
- **witness／hash：** job対応stderr、腕別hook数、consumer検算は `251–273`、SHA256SUMS の実再計算は `110–121`、必須掲載検査は `258–262` に残っています。これらに新しい退行は見つかりませんでした。
- **複製：** receipt/request/result/stdout は `run-measure.sh:132–139` でhash対象になります。`COPY_OK` は必須ファイルの保存・照合とログ数の成否であり、子の成功や解析上の有効性を意味しません。ログ数異常には4状態とは別に `count=N` を記録します（`141–142`）。
- **時刻：** JUnit開始timestampを外側区間±300秒で検査します（`analyze:226–227`）。JUnit終了時刻までの包含検査ではありません。
- **Bash：** 3 launcher の `bash -n` は rc=0。`"$(basename "$f")"` の引用と配列を使わない `for` は妥当です。現環境では `/usr/bin/realpath` が存在します。
- **dogfood：** `focus/fix2-dogfood.log:1–4` は selftest PASS／rc=0、dump-consumers rc=0を記録しています。check-run は selftest内で実行する構造です。独立した実成果物へのcheck-run結果や、launcher連続運転の証拠まではありません。

## 派生値の原出力照合

`s4-ruling.md:10` の数値は保存された原出力と一致します。

| 条件 | 裁定値 | 原出力 |
|---|---|---|
| 正規、δ=27・SD=22、6／8／10対 | 0.76／0.85／0.91 | `verbatim/power_rule-output.txt:16` と一致 |
| 裾モデル、同条件、8対 | 0.50 | 同 `33` と一致 |

ただしモデル名は同 `19` の **15%/15%の正負の裾**が正しく、裁定の「L側15%」は訂正が必要です。今回は保存済み原出力との照合であり、MCの再実行ではありません。

## 総括

A1〜A5・B1〜B10の15件は、**closed 10件、partial 1件、regressed 1件、not-applicable (docs へ) 3件**です。

**GO不可。** B1の系列制御不整合は投入予算・採用対・停止時点を変え、B3の必須引数欠落受理は成果物の誤対応を通し得ます。この2件を修正してから測定開始してください。診断検出、締切後の推論不変性、登録範囲の統計処理については閉鎖を支持します。