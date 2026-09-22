## 判定

NO-GO

## 前巡所見の対応表

今回の対象3件は **closed 3・partial 0・regressed 0**。

| 前巡所見 | 状態 | 照合結果 |
|---|---|---|
| partial 1：初回 must-fix 1、V03 の分類・集計 | closed | lockskip 4 thread を「別の層で検出」1 run として独立計上。原出力の X＝1,213,194、巡回＝5,510、version dup＝6,692 と段4の分類定義に一致。 |
| 新しい must-fix：期待一致8件を「検出8」と呼ぶ | closed | README §1・§3.4 と fragment が「検出7＋到達しない条件のS 1＋盲点S 4」に修正された。highkey legacy を検出に含めていない。 |
| 新しい should：run数列へのpatch数の混在 | closed | README §3.4 の「その他」は0 run。未実走のsort-nonswo 1 patchは表外に別記され、加算可能になった。 |

前巡でclosedだった発火範囲の限定、差し替え説明、emitterへの帰属、opswapの限界、参照節にも後退は認めない。

## 新しい所見

- **must-fix：fragment の見積り式で、実測とwalltime上限の区別が不正確。**
  [fragment 15行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2847-patch-verify/docs/spool/worklog/2026-09-23-t2847-patch-verify-1.md:15) の「walltime 上限で既消費＋残り＋受入 ≈1.8 node時間」は、そのまま全jobの上限を足すと成立しない。ログの上限は20＋20＋30＋40＝110分、段4の受入見積り15分を加えると **125分＝2.0833 node時間**。
  **≈1.8が成立するのは、既消費のpilotを実測140秒に置き換えた場合**である。次のように明記すれば解消できる。

  > pilotの既消費140秒（実測）＋残り3 jobのwalltime上限90分＋受入見積り15分＝約1.789 node時間＜2。

  確認不要という判断自体の誤りを示すものではないが、その根拠となる計算式は正確に残す必要がある。

- **should：レビュー完了の記録が参照先と一致しない。**
  [fragment 16行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2847-patch-verify/docs/spool/worklog/2026-09-23-t2847-patch-verify-1.md:16) は「焦点再レビューで閉じた」とするが、指定された前巡結果はNO-GO・partial 1。本巡で既存3件は閉じたため、「焦点再レビュー2巡目で既存所見を解消、本巡の追加所見は対応中」と区別するのが正確。また18行の「focusの巡数はinsightの冒頭」は、現README冒頭に巡数がなく参照先が不足している。

- **nit：なし。**

## 再計算した値

verifier全18出力の判定・取引数・書き込み数・巡回・integrity・P理由別件数をsummaryと照合した。報告G2件数も原出力のanomaliesから確認し、不一致は認めなかった。

| 対象 | 原データからの再計算 |
|---|---|
| 変異run | s2＝4、s3＝3、s5＝2、t152＝4。**計13**。対照等5 runを除外。 |
| 期待した層で検出 | norw 2＋highkey S2 1＋lockskip単独1＋early-unlock 1＋permutation 2＝**7** |
| 到達しない条件のS | highkey legacy＝**1**。巡回・違反0、certified=true。 |
| 盲点のS | write-intent 4変異＝**4**。全件certified=true、I行0。 |
| 期待どおり | 7＋1＋4＝**12** |
| 別の層で検出 | lockskip 4 thread＝**1** |
| 未発生／その他 | 実走分はいずれも**0**。12＋1＋0＋0＝13。 |
| patch単位 | **10本**すべてに少なくとも1条件の期待一致あり。sort-nonswo **1本**は未実走で別記。 |
| job Elapse | s3＝140、s5＝134、t152＝185、s2＝209秒 |
| 実測単価の範囲 | 最小134、最大209。fragmentの **134〜209秒／driver job** と一致。patch単価ではない。 |
| 実使用合計 | 140＋134＋185＋209＝**668秒＝0.18556 node時間**。READMEの約0.19と一致。 |
| pilot後の見積り | 140/3600＋90/60＋0.25＝**1.78889 node時間** |
| 全jobをwalltime上限で集計 | 110/60＋0.25＝**2.08333 node時間** |

取引あたり書き込みも再計算した。

| 条件 | writes / txns |
|---|---:|
| stock | 1,176,794 / 133,991＝8.7826 |
| erase | 1,094,995 / 140,714＝7.7817 |
| forge | 1,269,833 / 129,883＝9.7767 |
| opswap | 6 / 1＝6.0 |
| ptrswap | 1,190,447 / 135,589＝8.7798 |

fragmentのタイトル・25行の実走数と分類、write-intentの観測はREADME・一次資料に一致する。「約1少ない／多い」という平均差も正しい。

なお、fragmentに継承された過去の設計件数、mainの取り込み、実装差分ゼロなどは、今回の指定一次資料だけでは独立に確証できない。

## 総括

前巡の3件はすべて解消し、実走結果と分類集計は整合している。残る必須修正は、**fragmentの約1.8 node時間を、pilot実測＋残り上限＋受入見積りとして明記すること**。追加実走は不要。静的照合のみを行い、ファイルは変更していない。