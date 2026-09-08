## 対応表

`closed` 11 件、`partial` 1 件、`regressed` 0 件。`partial` は本文の欠陥ではなく、B9 の段 7 記録成果物が今回の検算資料に含まれないためである。

|#|段 3 レンズ B 所見|状態|適用後の判定|
|---:|---|---|---|
|B1|逐語アンカー 7 件|closed|各 hunk は指定アンカーへ適用済み。適用後ファイルの blob は diff の新 blob `a3a87fbf9…` と一致する。|
|B2|124 pair-sample は 1 pair 前提|closed|「1 pair・1 セルあたり」と限定し、`124P / 248P / 496P` も追加済み。|
|B3|reference は pair-sample あたり 2、side あたり 1|closed|本文の 248 reference measurement と現物が一致。誤読の再導入なし。|
|B4|起草時と D1695 後の値の混同|closed|起草時 `236 / 3,540 / 118 / 1,770 / 5,310` と D1695 後 `248 / 3,720 / 124 / 1,860 / 5,580` を分離して保存。|
|B5|機構の実在範囲の言い過ぎ|closed|library-level の型・純関数・生成器・完全性検査と local create-only issuer までに限定し、権威 producer と正式 launcher 配線の不在も明記。|
|B6|`output/` の 0 件を B-4 固有名へ限定|closed|3 固定名を exact に列挙し、`output/` 配下という限定も入った。|
|B7|§7.2 / §10 以外の同型取り残しなし|closed|scope を広げる編集はない。|
|B8|living-doc 静的形式|closed|追加行に新見出し、他文書の行番号参照、問題の placeholder 形式はない。|
|B9|worklog と変更 file 数の矛盾|partial|適用差分が対象文書 1 件だけで、コード・テスト差分がないことは確認できる。insight / spool fragment は段 7 の記録成果物と裁定されたが、その将来内容は今回の資料外。対象本文の回帰ではない。|
|B10|bytes pin|closed|現在の 339–623 行相当の raw slice、§5 表、H5 見出し集合はいずれも不変。|
|B11|未授権の開始時刻値|closed|発明された値を使わず、D1649 の「`未記入` のままでよい」を逐語で反映し、発効時の解決は未裁定として返した。|
|B12|行番号・引用帰属|closed|`DIFFERENCE_FORMULA` は現物の 71 行開始。authoritative producer 不在の宣言元も `p3_b4_analysis_ledgers.py` と正しく記載。|

段 4 の扱いは[裁定表](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage4-adjudication.md:19)、実際の適用内容は[applied.diff](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/applied.diff:5)で確認した。

## 費用段落の全数値

結論は、列挙された数値がすべて正しい。条件は本文どおり「各 campaign の当該セルに P pair」「2 campaign」「名目 `reps=5`、`extime=3`」である。

|主張|導出|検算|
|---|---|---|
|124 pair-sample|`62 × 2 campaign × 1 pair`|正しい|
|248 side session|`124 × 2 side`|正しい|
|496 measurement|`248 × 2 measurement/session`|正しい|
|候補 248・参照 248|各 side session に candidate/reference 各 1 件|正しい|
|名目 7,440 秒|`496 × 5 reps × 3秒`|正しい|
|P pair の一般式|`124P / 248P / 496P`|正しい|
|起草時|`n=59 × 2 = 118` pair-sample。候補 `118×2=236`、参照 `118×1=118`|正しい|
|起草時秒数|候補 `236×15=3,540`、参照 `118×15=1,770`、計 `5,310`|正しい|
|D1695 後の旧構成|`n=62 × 2 =124`。候補 `124×2=248`、参照 `124×1=124`|正しい|
|D1695 後の秒数|候補 `248×15=3,720`、参照 `124×15=1,860`、計 `5,580`|正しい|
|候補側不変|旧・現構成とも候補 measurement は 248 件。`248×15=3,720`|正しい|
|参照側増加|旧 `124×15=1,860` → 現 `248×15=3,720`|正しい|

現物上の導出根拠は次のとおり。

- n=62 は[D1695](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:153)、2 campaign は同資料の D1641 と[対象本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1111)にある。
- driver は `pair_ids × range(sample_count)` を pair-sample とする。[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1347)
- `_SIDE_IDS = ("candidate_1", "candidate_2")`、`_MEASUREMENT_ROLES = ("candidate", "reference")` であり、pair-sample ごとに exact 2 session・4 measurement を検査する。[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:96) [floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1429)
- `REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE = 2` である。[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:70)
- 旧構成が `candidate_1 / candidate_2 / reference` の 3 role を別 session にしたものだったことは[D1699](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:209)に明記されている。
- 適用後本文の数値と履歴は[費用段落](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1123)に正しく反映されている。

5 reps・3 秒は driver の固定値ではなく、校正前の名目仮定である。driver は `reps` と `extime` を正整数の spec 値として受けるため、本文が 7,440 秒を「実時間の保証ではない」と限定しているのも正しい。[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:775)

## 単位の主張

「反復数は session ではなく測定ごとに掛かる」は現物どおりである。

各 `PlannedMeasurement` について `_run_planned_measurement()` が個別の `MeasurementRequest` を作り、`_measure_with_runner()` を呼ぶ。[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1970) その呼出しは `runner.measure_point(..., extime=request.perf_config.extime, reps=request.perf_config.reps, ...)` である。[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1590)

header の field 名も exact に一致する。

- `measurements_per_session`: `len(_MEASUREMENT_ROLES)`、現状 2
- `reps_per_measurement`: `{cell_id: cell.perf_config.reps}` の mapping

両 field は生成時 header と再検証用 expected header の双方に別々に存在する。[floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:2241) [floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:2694)

## 機構の実在範囲

§7.2 が列挙する 5 件はいずれも実在し、言い過ぎはない。

|本文の列挙|現物|
|---|---|
|issuer 束縛 batch receipt から封印する registry の型|`B4ScheduleReceipt`、`B4ScheduledAttemptRegistry`、`seal_scheduled_attempt_registry()` が実在。receipt と normalized batch の hash/count を照合する。[p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:113) [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:670)|
|prefix 保存の violation 追記純関数|`append_registry_violation()` が旧 canonical bytes を prefix とすることを明示検査して新しい frozen value を返す。[p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:772)|
|manifest 生成器|`generate_analysis_manifest()` が exact first 201 eligible rows を生成する。[p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:1050)|
|厳密再生成の完全性検査|`assert_analysis_manifest_complete()` が row 集合・順序、canonical bytes、binding/hash を再生成結果と照合する。[p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:1140)|
|create-only bundle の発行|issuer は新規 root を作り、`O_EXCL` で registry/manifest/temp receipt を作成し、最終 receipt を hard-link する。[p3_b4_prerun_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:525) [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:592)|

issuer は発行時だけでなく strict reload 時にも完全性検査を再実行する。これは本文の主張をさらに支える実装であり、本文の列挙に欠落した別の operational closure ではない。[p3_b4_prerun_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:1009)

また、本文は append 純関数を永続 operational append 台帳とは呼んでおらず、権威 producer・正式 launcher 配線・end-to-end file-drawer closure の不在を残している。[対象本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:709)

## 固定名と出所帰属

3 件はいずれも issuer の exact な最終成果物名である。

- `_REGISTRY_NAME = "scheduled-attempt-registry.jsonl"`
- `_MANIFEST_NAME = "analysis-manifest.json"`
- `_RECEIPT_NAME = "prerun-issuer-receipt.json"`

定義は[p3_b4_prerun_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:46)、発行 path への使用は[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:722)で確認した。

`rg --files --hidden --no-ignore` と `find -type f` の双方で、`output/` 配下の exact basename 件数はそれぞれ `0 / 0 / 0`。repo 全体でも `0 / 0 / 0` だった。

「`p3_b4_analysis_ledgers.py` が自らそう宣言している」という帰属も正しい。同 module の docstring が、receipt は normalized batch を束縛する一方、この module は authoritative producer を作成も同定もしない、と明記する。[p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:1)

## bytes pin

全項目が不変だった。

- 適用後ファイルの git blob: `a3a87fbf94375e546d33d20a20cd610a8d4aeec9`
- diff の新 blob: `a3a87fbf9…`
- 現在の凍結 slice: 339 行の `#### 5.1.1` 先頭から、624 行の `## 6.` 直前まで
- slice 長: 21,833 bytes
- 実測 sha256: `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`
- consumer pin: 同じ値。[p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)

旧 blob の 312–596 行 slice と適用後の 339–623 行 slice は、双方とも同じ sha256 だった。

§5 の値表 12 行についても、旧 blob と適用後の sha256 は双方とも `8ed1d274ea5d146bea45c2a814f9d449a32924b98e2c85f04228aa6058adbd74`。byte 単位で無変更である。[§5 表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:156)

凍結 slice 内の H5 見出しは旧・新とも 6 件。さらに applied diff 全体で追加見出し 0 件、削除見出し 0 件だった。

## 削除 9 行の保存状況

[diff の削除 9 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/applied.diff:120)に含まれた実質情報は、すべて逐語または等価に残っている。

|削除行|元の情報|適用後の保存先・形|
|---:|---|---|
|120|各 campaign n=62、2 campaign 合計124、候補側の算術|現行事実の 124 pair-sample と erratum の候補248に保存|
|121|候補248 session、3,720秒、約62分|erratum に exact な248・3,720秒。約62分は3,720秒と等価|
|122|参照124 session、1,860秒、約31分を加算|erratum に exact な124・1,860秒。約31分は1,860秒と等価|
|123|1セルあたり|現行本文の「1 pair・1セルあたり」と P 一般式に保存|
|124|D1695 が n=59/118 から変更、起草時236 session|erratum に日付・D1779付きで保存|
|125|起草時3,540秒・1,770秒、別 session 条件|erratum に exact 保存|
|126|D1699 が同一低水準 session へ変更|現行構成説明と erratum の双方に保存|
|127|「加算でなく組み替え」・実装確定後に書き直す|「同じ248 sessionの中身が1測定から2測定になる組み替え」と保存。将来形は実装確定・書換え完了により現在形へ更新|
|128|書換え待ち注記の終端|書換え済みであることを現行事実冒頭に明記|

保存先は[適用後の費用段落](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1123)。落ちた数値・構成条件・変更理由はない。

## 総括

**must-fix**

- なし。費用数値、単位、機構の実在範囲、固定名、出所帰属、bytes pin に事実誤認は見つからなかった。
- `regressed` は 0 件。

**nit**

- B9 だけは、段 7 で生成される insight / spool fragment の内容が今回の資料に含まれないため `partial`。これは適用後の対象本文の欠陥ではなく、今回の静的検算範囲の限界である。