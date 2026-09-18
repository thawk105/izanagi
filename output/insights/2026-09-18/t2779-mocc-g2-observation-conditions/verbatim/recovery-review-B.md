## must-fix

0件。集計値・分母・参照を変更すべき不整合、根因同定・certifying・一般化の過剰主張は認めませんでした。

## should

0件。

## nit

0件。

## 総括

**must-fix 0 / should 0 / nit 0。GO（非certifyingの観測記録として）。**

独立検算で以下が一致しました。

- **360走**：各 `result.json.runs` と個別 `run.json` が一致。保存ディレクトリ集合も一致し、未収載・未開始なし。全 `verifier.json` の判定・終了コード・commit数・integrity と集計が整合。failure・indeterminate は0。
- **回転順**：全4 blockで ABC / BCA / CAB、各armの各位置への出現は10回。
- **binding**：runner・arms JSONの実ファイルSHA、patch SHAと適用順、pin・define・witness・source SHA・policy SHA・toolchainのblock間照合が一致。BACK_OFFの変更はbo1だけ。
- **収集**：dispatchログのrequest・時刻・終了結果が本文と一致。4本とも `.done=0`、締切内完了。
- **集計**：通常5/120、診断0/120、backoff 2/120。CP両側95%区間は本文・summaryと一致。介入側低下方向の片側Fisherはそれぞれ **0.0299507441343、0.223086475541**。
- **7正例**：全て `phenomenon=G2`、長さ2、両辺rwの1 cycle。本文のblock/ordinalと一致。各退避manifestのroot・pin・binary SHA・workload、48ファイルの集合とサイズが保存物と一致。
- **参照**：insightの `summary.json` と `recovery-summary.json` は同内容。入力4本の記録SHAも実ファイルと一致。

**未検査**：大量trace本文の再解析・内容SHA再計算、削除済み一時source/binaryの再検証、実行時環境の独立実測。manifestの内容SHAは検証済みとは扱いません。pytest・再計測・ファイル書込みは行っていません。

陰性の不在証明化、非有意の同等性証明化、family全体への有意性拡張はありません。規律2の即reject、certified昇格・pin前進・変異探索の制限も維持されています。
