## 閉包表の判定 (closed / partial / regressed、根拠付き)

以下、`insight` は指定 README、`fragment` は指定 worklog fragment を指す。

| 所見 | 判定 | 修正後の根拠 |
|---|---|---|
| B must-fix：共通 `n` を設計択へ戻している | **closed** | insight:110、126–131 は全 cell 共通 `n` の維持と holdout 別 `n` の却下を明記。D2071（docs/decisions.md:63560–63578）と一致し、後続 wave の選択余地を残していない。 |
| A nit 1：manifest の `n` は任意欄 | **closed** | insight:52 に「manifest に `n` があれば」と条件を明記。共通 `n` による反復集合検査の参照も正しい。 |
| A nit 2：束縛図の対象・保証範囲 | **closed** | insight:51、59、70–71 で trials と runtime report の cell を区別。:84 は正規 manifest の場合に限定し、:90 は registry の導出・検査範囲に限定した。 |
| A nit 3：検索結果の要約 | **closed** | insight:159–170 の修正は検索結果と一致。判定器自身の定義等、`def judge` 2 件、テストコード 2 ファイルと ledger JSON を区別している。 |
| B nit 1：worklog の技術説明再掲 | **partial** | 一次資料への参照はあるが、fragment:17–19、27–31 に技術説明が残る。本文は :12–39 の 28 行・7 項目で、レビュー B が求めた重要事項中心の縮約にはまだ届いていない。 |
| B nit 2：工数・受入結果の記入待ち | **partial** | insight:190、fragment:39 が段 7 の記入待ち。閉包表の partial 判定どおり。 |

## 新規記述の検算

- **対応表 5・13 行目、鎖 A：整合。** registry:780–781 が holdout の閉集合、:796–799 が直積、:800–801 が共通 `n` を検査する。:1678–1688 は trial の凍結束縛から workload を照合する。runtime report は空 cell 集合も許すが、修正文は cell の存在を必須とは述べていない。
- **対応表 6 行目：整合。** judge:392 の条件付き一致と、:400–442 の共通 `n` による完全反復集合検査を正確に記述している。
- **再現手順の修正注記：整合。** ただし閉包表末尾の s4-ruling.md:61 にある core テスト「6 hit」は、今回の検索では **7 hit**。テストファイル数が 2 という結論には影響しない。
- **fragment の段 6 段落：一部 regressed。** [fragment:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-delta-min-connection/docs/spool/worklog/2026-09-17-dev-wave-b2-delta-min-connection-1.md:35)–36 の「nit 5 件…も反映した」は不正確。列挙は A nit 2 を分割して数えており、未完了の B nit 2 を含まない。「nit は修正を反映、工数・受入結果は段 7 待ち」と区別する必要がある。D2071 の説明自体は正しい。
- **fragment 文法：適合。** H2 は :10 と :41 のちょうど 2 つ。`完了` item の `remaining: none` と `base:` は :48–49 で連続し、`{{`・`}}` は存在しない。

## GO / NO-GO と理由

**段 7 への進行は GO。最終成果物の確定は修正・記入後。**

中心の must-fix は解消し、実装との新たな矛盾は見つからない。確定前に fragment の nit 完了表現を訂正し、技術説明の再掲を縮め、工数・受入結果を記入する必要がある。

## 総括

**閉包表 6 件は closed 4、partial 2。新規記述には完了状況の過大表現が 1 件ある。** D2071 準拠と fragment の指定文法は確認済み。編集・実測・受入検査は実施していない。