## 所見

なし。

## 破れなかった箇所

- chain 検査は裁定どおりの条件・例外型・文言で実装されている。読み直し `paper_story_a2_certification.py:4531-4532` の直後、再導出 `:4538-4541` の前にあり、partial 側 `:4388-4395` と同型である。
- この検査は canonical full chain では通過し、再読結果が partial chain の場合だけ materialize の成果物作成前に拒否する。既拒否入力の例外分類が変わる場合はあるが、受理集合を拡大する経路はない。
- 正例 `test_paper_story_a2_certification.py:3010-3034` は、生成 bytes が canonical evidence と一致し、supplied forged evidence と不一致であることを両方 assert している。manifest SHA も canonical bytes に固定している。`return canonical_full_evidence` を `return evidence` に変えると、`paper_story_a2_certification.py:4552,4572-4577,4602-4604` へ forged bytes が流れ、byte assert が赤になる。
- 負例 `test_paper_story_a2_certification.py:3037-3055` は partial evidence の表層 schema と manifest fields だけを full 相当に偽装する。fix 前相当では初期 schema 検査を通り、nonzero driver が raw-manifest 分岐より先に同一の indeterminate report を生成するため、再導出比較も一致する。authority gate にも実 receipt 由来の有効な raw evidence が渡るため、追加 chain 検査以外の先行拒否理由はない。
- M01〜M04 の対象は `paper_story_a2_certification.py:4531-4543` に残り、各 old 逐語は一箇所だけに定まる。M05 の return と M06 の文言も各一箇所だった。
- 現物2ファイルの差分は `diff-after-fix1.patch` と byte-for-byte 一致した。test 差分は追加のみ（112 additions、0 deletions）で、既存期待値の変更はない。既存正例には canonicalizer 同値 assert が追加されただけである。

## 総括

fix 1 の chain 検査と新規2 node は、段6裁定の逐語・意味に一致している。  
新規正例は M05、新規負例は M06 をそれぞれ単一理由で識別できる。  
段5の M01〜M04 対象と既存 test の期待値は維持されている。  
指定どおり静的検査のみを行い、pytest・編集・commit は実施していない。