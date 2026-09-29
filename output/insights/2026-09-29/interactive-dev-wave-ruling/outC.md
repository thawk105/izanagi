**結論:** 日々の wall 時間を縮める主候補は、削除件数ではなく、受入前の待ち、無活動の時間、変異検査、受入の最長 shard です。ただし待ちの上限設定と変異検査の限定は、現案のまま採用しない方がよいです。

### 1. 実効性の順序

平均 154 分の内訳から見ると、まず門番待ち（約 15%、docs wave では平均 48 分）と無活動残差（28%）が大きいです。後者は原因が未確認なので、その全量を短縮可能とは見積もれません。次が変異 probe と final（12〜24%）、受入走行（13%）です。受入は worker 時間の総和ではなく**最長 shard の実 wall**で判断すべきです。直近の全走約 14 分に対し、T-080 群の 3,566 秒をそのまま短縮額にはできません。共有 base の局所複製案も、事前登録した短縮条件を満たさず land されていません。[D2242](/work/1/SFC/tanab/izanagi/docs/decisions.md:72110)

`check_docs.py` の 68〜98 秒は改善余地がありますが、上記より規模が小さいです。単発 tool、文書、保留 test、安い test の削除は、通常の受入 wall を縮める根拠がありません。D1990 の否定的結論が再び当てはまります。削除には整理上の価値があっても、高速化の主施策としては数えない方が正確です。[D1990](/work/1/SFC/tanab/izanagi/docs/decisions.md:60257)

### 2. wave の切り方

- **並列可:** md_1 と、共有の README・テスト目録・所要台帳を編集しない範囲の md_2。記録先を分けるだけでなく、実際の編集ファイルを分ける必要があります。
- **直列:** md_1 → md_5。文書地図、README、phase3 の参照を同時に動かすと衝突します。
- **直列で統合:** md_2 と md_3 のテスト削除部分、および md_6。`test_ccbench_spawn_sites`、所要台帳、`growth_test_holds`、`orchestrator/tests/README.md` の allowlist、`REAL_REPO_SERIAL_NODES` は、各削除の結果を見て一つずつ更新するのが安全です。対象 module が別でも、この共有面は並列編集に向きません。
- **依存後:** md_4 は予定どおり cleanup-enforce の land 後。md_7 もその後に置き、`check_docs` の性能改善、変異検査の契約、門番運用を別件に分けます。

md_2 の `t1434_t1222_science_slice` は特に再考が必要です。D2179 は、派生値 pin を残す裁定との重なりを理由に、science-slice の対削除を採っていません。「一回限り」という分類だけで再投入できません。[D2179](/work/1/SFC/tanab/izanagi/docs/decisions.md:68990)

### 3. 削除記録

新しい `pruned/` と wave ごとの JSONL は勧めません。Git にある blob・サイズ・削除時点を別台帳へ重複記録し、毎回の編集と整合確認を増やします。**削除 commit の本文に対象、理由、関連 D を記し**、文書には既存の墓標、`output/` には既存の `PRUNED-INDEX.jsonl` を使う方が簡単です。復元案内が必要なら既存の文書地図に `git log --diff-filter=D -- <path>` と、最後に存在した commit への `git show <commit>:<path>` を短く載せれば足ります。

### 4. R1〜R3

| 裁定案 | 判定 |
|---|---|
| **R1: T-080 E2E を削除** | **反対。** D700 は直接 helper 検査と public driver を通る E2E の受理集合が異なると確認し、削除を明示的に却下しています。今回の「約 20 関数」と D700 の「6 関数・11 nodeid」も範囲が一致しません。重複 setup の共有化は別案として検討できますが、削除推奨の根拠にはなりません。[D700](/work/1/SFC/tanab/izanagi/docs/decisions.md:27653) |
| **R2: B-4 と T-189 を削除** | **根拠不足。** B-4 は研究本流との関係と現役 consumer を関数単位で確認する必要があります。T-189 の held node は削っても受入時間の節約はゼロです。両者とも D1989 の参照分類と D2179 の専用 test 条件を満たしたものだけ、整理目的で削除する判断が妥当です。[D1989](/work/1/SFC/tanab/izanagi/docs/decisions.md:60226) |
| **R3: 変異 matrix 限定・門番待ち上限** | **両方とも現案には反対。** matrix の免除は「実装しない」裁定と実装差分ゼロの連言に限る既裁定です。「test・gate を変更した wave だけ」は、verifier や producer の変更を検査から外し得ます。[D301](/work/1/SFC/tanab/izanagi/docs/decisions.md:13963) 門番上限も、後続裁定は leader 判定の修正を先行し、待ち・受入 wall・赤率を対照してから再提示する順序を選んでいます。単純な「10 分で投入」はその判断を飛ばします。[D2211 項4](/work/1/SFC/tanab/izanagi/docs/decisions.md:70758) |

論文を早く進める目的なら、まず研究 wave を止めている待ちの実因と受入最長 shard の短縮効果を測り、効果が示せた一件だけを採るのがよいです。大規模な削除 wave は、現時点では日常の wall 短縮策として優先しません。