## 所見

1. **must — 事前無作為化の確認根拠が参照先にありません。**
   [README:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:38) と [D fragment:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/docs/spool/decisions/2026-10-01-dev-wave-b4-floor-adopt-2.md:38) は、事前無作為化を前 wave の確認記録に依拠させています。しかし、参照先の [証拠確認:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-09-29/t2288-floor-pair-w2/README.md:99) にあるのは分離・標本数・欠測・上限・probe・rep・環境の確認です。無作為化を確認した一次資料を示すか、この項目も未確認と明記してください。無作為化違反を発見したという意味ではありません。

2. **should — commit 時刻から「その時点に結果が無かった」とは断定できません。**
   [README:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:40) の表現は確認範囲を超えています。照合できたのは、spec 追加 commit の記録時刻 `2026-09-17T21:58:18Z` が、提供された w1 の最初の `started_at`、`2026-09-19T12:32:19.917452Z` より前という順序です。この事実に限定してください。[事前登録:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/docs/phase3-b4-reflux-ablation-preregistration.md:297) も、結果を見る前の選定を機械保証していません。

3. **should — 「抜粋11件だけ」は failure digest 内の件数に限定してください。**
   [README:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:52) の `11件・省略25件` は [digest 集計:987](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:987) と一致します。ただし、ログ本体には digest 外の `test_outputs_contain_no_combining_diacritic_codepoints` の詳細も残っています（[ログ:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:22)）。

   また、digest の10件に共通するのは binary の `lstat` 失敗です。`authoritative_floor_rejected` まで伴うのは9件で、resolver を直接呼ぶ1件は `B4FloorArtifactError: spec_rejected_by_producer` です（[ログ:573](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:573)）。

## 総括

**NO-GO — must 1件。**

集約・spec 3本の SHA-256 は自計算して一致しました。floor_exact、6窓の終端件数、分離時間（rr5／rr50／rr95＝231.640457／231.765984／231.756478時間）、追加 commit、焦点走の集計とファイル別内訳、基準走259 passedも一致しています。

consult 2本の正規化表は、行番号・byte数・原文hash・復元結果すべて一致しました。floor の三分岐と§11.0の不一致指摘、fragment文法、「更新」と依頼未完の明記も整合しています。

D2138表原文、base digestの対象本文、実行argv・相談モデル等の実行記録、binary実体、submit-treeの開始時点の状態は射影外のため独立照合していません。テスト・書込み・委任は行っていません。
