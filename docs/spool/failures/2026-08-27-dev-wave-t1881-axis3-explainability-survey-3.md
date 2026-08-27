---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1881-axis3-explainability-survey
seq: 3
---

## 新規

### {{F:preregistration-pilot-leak}}. 事前登録の pilot が登録枝と同一 query で、その 0 件を本文へ実測として書いた [計測汚染] [手順漏れ]

- 事象: 軸 3 の検索事前登録を書く過程で、DBLP の取得設計を選ぶために連言 16 組の件数を
  測った。**そのうち 8 組が、同じ文書が登録する枝 query と query-equivalent であった。**
  親は当初 1 件も開示せず、さらに 1 組 (`many-core provenance`、登録 ID
  `AX3-Q7-F03-W07@dblp` と同一) の `@total` = 0 を本文の実測表と完走述語の説明へ
  「0 件そのものは走行無効の理由にしない」の実例として書いた。
  **軸 3 は `RW0` であり、7.7.3 は外部索引に対する新しい不在方向の表現を禁じている。**
- 根本原因: pilot を「索引の構文を測る行為」と捉え、**登録対象と同じ query を送っている
  という同一性に気づかなかった。** 事前登録の凍結前に、pilot の query 群と登録 query 群の
  突き合わせを行う手順が無かった。あわせて、同じ文書が「題名だけで判定するな」と定めながら、
  親が別 probe の上位 3 件の題名だけを見て「軸 3 とは無関係である」と接地を確定していた。
- 恒久対応: {{D:pilot-equivalent-query-disclosure}} — 登録枝と query-equivalent な pilot の
  全件列挙・件数開示・不在の証拠としての使用禁止・文書類型の明記を必須にした。
  凍結物側では `2026-08-27-axis3-search-preregistration.md` の §0 と §11.2 が
  8 本すべてを開示し、対応する登録 query ID を併記している。
- 再発検知: 事前登録を凍結する段で、**pilot として送った全 query を登録 query ID へ写像し、
  一致するものを列挙する**照合を行う。一致が 1 件でもあれば
  {{D:pilot-equivalent-query-disclosure}} の 4 項目を満たすまで凍結しない。
  段 6 の敵対レビューはこの型を検出できた (2026-08-27 実測) ので、
  レンズ設計に本型タグを含める。
