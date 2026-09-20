## 所見

静的レビューのみ。以下、コードの相対パスは指定worktree内、`compare-summary.md` は指定jobの `run/` 内を指す。

1. **観点3・不足：read-heavyでの副作用を判断する実測が欠けている。重み：should。**  
   根拠：`orchestrator/verifier/dsg.py:392,415,447,449,481`、`compare-summary.md:7`。
   - `token_to_key` は48 file × 1M tokenなら約192 MB。二巡目は全tokenを**走査**するが、decodeするのは未解決tokenだけであり、「全tokenを再decode」ではない。それでもread-heavyでは対象が多い。
   - `order` と `rows` は同時生存し、一時記憶量は最大鍵のwrite数に比例する。鍵が偏れば全write数に近づくため、常に小さいとはいえない。さらに診断再生では全writeについてbisectする。
   - 裁定§1bの1.96 GB／69.8 s・1.04 GB／53.4 sは見積りprobeの値。統合版bal6のproducerは95 sであり、見積り値をそのまま実装性能とは扱えない。
   - bal10／wh10は478／297 s、node peak 32.4／15.2 GiBで完走しており、その入力での容量改善は支持される。一方rh6は`new-failed`、新版計測値なし。実装故障か計測側の失敗かも、この要約だけでは判別できない。  
   **修正案：** 予定済みD-9でrh6の失敗原因を確定し、統合版のphase wall・peak・全field一致をcompare要約へ補完する。現時点で追加の汎用化や構造変更を要求する根拠はない。

そのほかの指定観点は次のとおり。

- **scope超過なし。** 差分は指定3ファイルだけ。`dsg.py:70,98`のviewは3個の基本Mapping操作を実装し、`get`／`contains`等を継承する薄い構成。継承で得る操作のために独自の互換機構を追加してはいない。`dsg.py:492`のtuple builderは退避に必要で、task生成・pool・replayは`:529`へ共通化されている。診断文言の重複はあるが、そのためだけのhelper追加は不要。
- **§4(a)(1)〜(5)の実装欠落なし。** 安定整列と元入力の再走査でfirst-writer・notes順を保存し、範囲検査は状態構築前。signed biasは32 bit×2の全域と順序を保存する。fallback前の参照解放は`dsg.py:608`、`parse.py:671,819`にあり、parseにもSIGKILL→shutdownが入る。
- **§5の指定testは全件存在。** 追加は再集計で**8 test＝単位1の5件＋単位2の3件**、全体114件。不採用案(iii)〜(v)の追加testはない。`test_verifier.py:3274`に独立子process＋120秒timeout、`:3286`にprocess groupのSIGKILLがあり、hang検出は実装済み。`:3299`の参照解放検査は既存fallback結果比較では代替できない。
- **報告の件数と検査内容は整合。** `test_verifier.py:2896`の凍結hashは**22件**、workers=1/2で**44比較**。全field比較も`:2951`にある。run順序は`:3136`のread列と`:3156`のww列、既存`:2506,2576`で固定されている。「反実仮想4件」に対応するassertionは確認できるが、**実際に4件を実行して検出した事実は差分だけでは証明できない**。§5の変異に対する検査の欠落は見つからなかった。

## 段 3 B の所見の閉じ方

- **B-1 closed** — 採用は(i)+(ii)とpool修正に限定。CSR等の追加なし。
- **B-2 closed** — 裁定§1bで8／4 workerを比較し、D-3で16維持を明示。設定pinの変更なし。
- **B-3 closed** — freeze対照を踏まえ、packed配列とworker入力変更を一体化。freeze追加なし。
- **B-4 partial** — D-1で未保全rh10を除外したが、rh6回帰確認は`compare-summary.md:7`で未成立。
- **B-5 closed** — 隣接replay／SCC／前判定の新機構は差分にない。
- **B-6 closed** — 採用されたfallback解放をedge・parse双方へ実装。他の局所案は裁定上の必須事項ではない。
- **B-7 closed** — 裁定§1・§1bでfreeze／worker数の対照と帰属の限界を明記。page単位の証明とは扱っていない。
- **B-8 closed** — wh3見積りとwh10統合比較があり、write-heavyを評価対象に含めている。
- **B-9 closed** — viewと追加8 testは採用変更の境界に対応。不採用機構のtest追加なし。
- **B-10 partial** — D-9で600 sを別扱いとする裁定はあるが、compare要約には専用の観測欄がない。
- **B-11 closed** — 単位1／2に分割され、変更もその所有範囲に収まる。
- **B-12 closed** — 裁定§9へ研究・運用判断を分離。lock・校正規則・witness pinを変更する差分なし。

## 総括

**GO：実装のscope・削除・局所修正の観点でmust-fixは見つからない。**  
最大の懸念はrh6の新版実測欠落であり、容量wave全体の完了判断はまだできない。  
提示されたcompareは4行中3行成功で、D-1の12 verdict同一性も網羅していない。  
予定済みD-9で補完し、見積りprobeの数値を統合版の実測として扱わないこと。