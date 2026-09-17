## 所見 (must-fix / nit、根拠付き)

**must-fix 1 件**

- **D2071 が確定済みの `n` の制約を、後続 wave の設計択へ戻している。** [insight:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-delta-min-connection/output/insights/2026-09-17/b2-delta-min-connection/README.md:125) は「`n` を holdout 別に許すのか共通に固定するのかは、その wave が…決める」と記す。しかし **D2071** (`docs/decisions.md:63558`) は「6 cell すべてで同一」「holdout ごとに異なる `n` は受理しない」と確定し、異なる値を許す案を明示的に却下している。既存被覆表にも D2071 と `output/insights/2026-09-16/t1957-manifest-replicates/README.md:40` が欠けている。設計メモを「D2071 の全 cell 共通 `n` を維持して結線する」に修正し、被覆表へ追記すべき。
  
  **放置時に何が誤るか:** 後続 wave が、却下済みの holdout 別 `n` を裁定不要の実装選択として再導入できると誤読する。

**nit 2 件**

- **worklog が insight の技術的説明を再掲しすぎている。** [fragment:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-delta-min-connection/docs/spool/worklog/2026-09-17-dev-wave-b2-delta-min-connection-1.md:17) の受口・適用経路・validator・呼び手の説明、および同 :30–41 の詳細は insight と重複する。`docs/worklog.md:22` の契約は「git に入り得ない情報だけ」、監査記録は最重要 1〜3 件と一次資料ポインタを中心とした 10〜15 行としている。親 brief の訂正、採番への追随、相談の採否は残し、技術的根拠は insight 参照へ縮めるのが適切。
- **段 7 用の記入待ちが残る。** fragment:44 と insight:184 の工数・受入結果は未記入。段 6 時点では想定内だが、最終成果物では実績または未実施の明示へ置換すること。これは spool の遅延採番 placeholder ではなく、fold 文法違反とは判定しない。

## T-2743 完了の可否

**確認手番としては完了にしてよい。成果物の確定前に上記 must-fix を直す必要がある。**

D2104 項 12 (a) と main の `docs/worklog.md:2956` が求めるのは、検査を追加せず現物で接続を確認すること。接続の実装までは要求していない。insight:119 の閉じる条件 5 点はこの射程に合い、「未接続」という結論でも確認手番を閉じられる。T-1874 / T-1875 の実装・測定手番は残る。

その他の確認結果：

- D1481 の「方向を確定」「具体的な `_ContrastParams` 改変方法までは指定しない」という読みは逐語と整合する。D1326・D649・D2049・D2104 の引用にも矛盾は見つからない。
- fragment の frontmatter、ファイル名、H2 ちょうど 2 個、既存 active ID を扱う `title:`、末尾で連続する `remaining: none` / `base:` は規則に合う。base は提示された digest と完全一致。UTF-8・LF・末尾改行を確認し、`{{` / `}}` は存在しない。
- `/rulings` は主題照合で既裁定を除外し、AI 手番を収載しない。今回の「裁定へ返す事項は無し」と完了差分はその規則に合う。D2071 の所見も既裁定への記述修正で解消でき、新規裁定待ちを作る必要はない。

## GO / NO-GO と理由

**現在の bytes は NO-GO。** D2071 に反する設計メモが 1 件あるため。

同箇所と既存被覆表を修正すれば、本レンズでは T-2743 を完了とすることに異議はない。pytest・spool_fold・受入検査は実行しておらず、それらの成否は本レビューの判定に含めない。

## 総括

**must-fix 1、nit 2。** 未接続という中心結論と T-2743 の完了方針は妥当。確定済みの全 cell 共通 `n` を後続 wave の自由な設計択へ戻している点を修正する必要がある。