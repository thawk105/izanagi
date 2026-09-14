## 所見

以下、`I/` は `output/insights/` を表す。

1. **対象：親 brief の P1-d／plan §6・§8・§9。主張：「残る限定は3つだけ」は不十分。**  
   新 attempt の認証取得は支持されるが、A-2 の条件関門について残る証拠上の限定が落ちている。保存されているのは `admitted=true`・`use_class=paper` の admission record と参照 ID であり、元の supply／meaning records ではない。`bound` や correctness `certified` から、関門の全検査内容を独立確認したとは言えない。  
   **一次資料：** `I/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json`、同 manifest が束縛する `receipts/condition-gate-{rr5,rr50}.admissions.jsonl`、F707。  
   **確度：高。** 外部の受領証2本を読み、manifest／図 provenance の SHA-256 と一致すること、記録本体ではなく ID を保持していることを確認した。  
   **是正案：** 「認証不在は新 attempt の範囲で解消した」と記し、条件関門は「通過を記録した受領証が束縛されている」までに限定する。

2. **対象：plan の前版訂正一覧／§6・§8 の旧 correctness 説明。主張：「指数」を「適応」に直すだけでは、旧4 cell の誤説明が残る。**  
   2026-09-05 版 §6 は、4 cell の認証対象をまとめて「内蔵指数 backoff 有効の build」としている。§8 exact claim にも同様の記述がある。しかし stock 2 cell は `BACK_OFF=0` であり、内蔵 backoff 有効なのは adopted 側についての導出である。plan は機構名の訂正を挙げるが、この母集合の誤りを明示していない。  
   **一次資料：** `I/2026-08-24_paper-story-a2-certification/certification.json` の `cells[].genome`、D1645、D1257。  
   **確度：高。** 旧原票の stock 2 cell が `BACK_OFF=0`、adopted 2 cell が `BACK_OFF=1` であることを確認した。  
   **是正案：** 旧 correctness は「4 cell とも certified、source routing から stock は無 backoff、adopted は内蔵適応 backoff と導出される」と役割別に訂正する。

3. **対象：親 brief の P1-a 改訂。主張：D1936 項21 の期限なし制限を、旧結論全体へ広げない。**  
   「旧 attempt の結論と fig5 の用途制限は D1936 項21 により期限なしで残す」は、旧結論全体の永久利用禁止とも読める。同項の対象は明示的に**古い図**である。訂正済みの旧結果を、その測定対象について歴史記録として説明することまで禁じていない。  
   **一次資料：** D1936 項21、D1645、`docs/paper-story/README.md` の旧 fig5 追補。  
   **確度：中。** 裁定の対象は明確だが、親文の「残す」が判定保持を意味するなら実質的な対立はない。  
   **是正案：** 「旧判定は保持し、旧 fig5 を採用静的 backoff の結論・図に使えない制限は期限なし」と分ける。

4. **対象：親 brief の P1-c／plan §8 B-7・§9。主張：正負の観測を、統合された性能判定へ昇格させない。**  
   A-2 の `observed-positive` は、必要条件を満たしたうえで2 workload の median 比がともに正だったという outer status である。A-6 は別 policy・別 attempt の `reject`。両原票とも `a4_noise_floor_status=open`、`global_minimality_established=false` で、効果の信頼区間や有意差判定を持たない。「3 workload で2勝1敗」は観測符号の列挙として成立するが、単一の横断実験や母集団への優越・退行判定ではない。  
   **一次資料：** 指定の A-2／A-6 `certification.json`、`orchestrator/campaign/paper_story_a2_certification.py` の `collect_results`、D12。  
   **確度：高。** 原票の field と status 計算分岐を照合した。plan の P1-c 対案はこの区別を守っている。  
   **是正案：** §9 でも attempt ごとの status と観測効果を分け、有意差・研究成功／失敗の宣告へ広げない。

5. **対象：親 brief の P1-b／plan の同項評価。主張：A-1 が残る理由は「別の事前登録」だけでは足りない。**  
   T-1998 の balanced 対は、物理的 contrast としては D1262 と同じ fixed5 対無 backoff である。違いは各 arm 5標本の median 比と、A-1 の均衡5-rep配置下の差という推定対象・配置にある。plan はこの点を正しく補正している。`accepted` を有意な改善の判定と呼ぶ根拠もない。  
   **一次資料：** `docs/t1998-balanced-stock-inline-preregistration.md` §2・§6、D1262・D1295、`I/2026-09-14_t2589-consumer-real-artifact-repair/README.md` §1。  
   **確度：高。** 対照・標本数・推定式と、記録された `accepted`／+11.225375361916456% が一致する。  
   **是正案：** plan の具体的な理由を採り、balanced の正式観測取得と A-1 未完了を併記する。

6. **対象：plan §2(f)・§4〜§9／「不変」項目。主張：主要な stale 修正は妥当だが、履歴保持と現在形の維持は区別する必要がある。**  
   A-2／A-6 の「認証なし」、fig6 不在、鍵のユーザー生成を根拠とする D906 成立、B-4 driver 不在、静的750／1000µs未取得を現在形で引き継ぐことはできない。plan はこれらを概ね拾っている。一方、「F707各例は不変」も文言の据置きではない。F707 自身の旧追記にも「内蔵指数」が残るが、pin の実装は固定幅の適応制御である。  
   **一次資料：** A-2／A-6原票、fig6 provenance、D1829、D1694、`I/2026-09-10_t2266-formal-1000us/README.md`、CCBench pin `511c9538` の `include/backoff.hh`。  
   **確度：高。** 認証原票・裁定本文・実装を直接確認し、正式1000µs取得の所在も README の追補で照合した。  
   **是正案：** 「不変」は歴史的事実と主張上限の保持に限り、機構名・現在形・未取得範囲を新版の文として導き直す。

## 親の暫定裁定への評価

- **(P1-a 改訂)：同意。** 新 attempt を論文素材に使うことは支持される。README の「未評価」は証拠不成立の裁定ではない。ただし旧判定の保持と、旧 fig5 の期限なし制限は所見3のとおり分ける。
- **(P1-b)：同意。** A-1 は残る。理由は plan が補正した推定対象・配置の違いで書く。
- **(P1-d)：不同意。** 「3 workload の認証不在が新 attempt の範囲で解消」は支持するが、「残る限定は3つだけ」は支持しない。所見1の条件関門の証拠範囲を追加し、workload 同一性は campaign lock／constructor による束縛であり独立 argv 観測ではないと明記する。旧利得への認証の遡及も不可。
- **(P1-e)：同意。** 各系列内の無 backoff 対照に対する符号が一致した、という記述的照合に限る。旧値と新値を pool せず、改善幅の増大・環境効果・再現性の成立を導かない。

## land 可否

**NO-GO。**
現状の brief／plan をそのまま執筆根拠にすると、限定の脱落と旧4 cell の誤説明が残る。
必要なのは所見1〜3の文書修正であり、新規測定や追加 gate ではない。

## 総括

最も重い所見は **1「残る限定は3つだけ」から条件関門の証拠範囲が落ちていること**。
新 A-2／A-6 の数値・status・correctness 認証取得は原票が支持する。
plan は性能文と correctness 欄を分けており、緑の直接的な混入は確認しなかった。
新事実を載せることと、独立観測・有意差・研究成功を主張することは別である。
指定6ファイルは読めた。追加探索した両新 attempt ディレクトリの `README.md` は不在だったが、原票等で照合を継続した。
書き込み・commit・push・pytest・build・測定は行っていない。