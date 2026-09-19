## 総括

**GO（静的レビュー範囲）。must 0／should 0／nit 0。**
指定baseから現在checkoutまでのproduction・test・docs差分を確認しました。成果物の受理・参照・検査回収を損なうrealな欠陥は確認できませんでした。実走完了の判定ではありません。

攻撃した点と判定は以下です。いずれも **refuted、修正不要** です。

| 攻撃点 | 根拠・確認例 |
|---|---|
| collection gateの緩和（F891/F932） | `tools/mutation_harness.py:1569` は元specを渡す。Q=1800/G=600で2399は起動前拒否、2400は通過して実効6330。 |
| 区間欠落・caller配線漏れ（F185/F901） | 同`:1452` はP+Q+W+G+A+C。collection`:1571`、baseline`:2175`、mutation`:2292`すべてhelperを使用。既定5130、Q3600/G600で8130。 |
| W overrideの取り違え | 同`:1440`。collectionは既定W、実行はoverrideを使用。W=2時間なら実行8730、collection5130。 |
| dispatch/local hangの混同 | 同`:1430`。localは短いhang値を維持し、dispatchは通常specと全区間予算のmax。 |
| in-band rc=16による残存jobの見落とし | 同`:365` の`job_may_remain`／`hold_error`判定を維持。mutationのhold時残置・通常時復元も`:2355`以降で維持。 |
| kill判定・resume束縛の弱化（F33） | 同`:2132`以降の失敗node集合完全一致、`:2690`以降のresume照合は変更なし。rc=16はKILLEDにならない。 |

親brief・裁定のP1は既存拒否集合を維持しており妥当です。P=180秒は全遅延の保証にはなりませんが、裁定・実装・docsとも暫定的な運用余裕として明示しています。この限界を理由に追加gateを要求しません。

追加テストは独立した数値期待と最終`communicate(timeout=…)`の観測を組み合わせ、算術とcaller配線を分離しています。既存テストの期待値変更・削除はありません。

**検証済み:** `git diff --check`通過。
**未実走:** pytest、M1–M15/P0変異、実dispatcherでの回収、既存hold・復元・resume回帰、受入検査。これらの成功や期待失敗node完全一致は、親の実測で確認する必要があります。