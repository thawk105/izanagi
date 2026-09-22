# [T-2851] 未知条件への転移の事前登録 v1 — 起草の経緯 (2026-09-22)

- 成果物: `docs/unseen-condition-transfer-preregistration.md` (事前登録 v1) と `docs/README.md` の 1 bullet。
- 依頼: ユーザー直接起動の `/dev-wave` (逐語 = `verbatim/request-t2851.md`)。計算投入・選択結果を使う評価走・gate/検査/台帳の
  追加は scope 外。一次資料 = `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P4 (と §3、同 dir の
  `codex-consult-1.md` 優先 3)。裁定 = D2212。
- 起点: local main `8fd2a2f5c775954d6a32cee019ac7ce276298e4d` から作った fresh worktree。

## 1. 段ごとの経過

| 段 | 内容 | 所在 |
|---|---|---|
| 1 | 事実調査 (調査子 sonnet 2 本: workload 引数・比較対象・対測定、既知結果の棚卸し) と親の検算、brief と攻撃対象 (P1)〜(P10) | `verbatim/facts.md`、`verbatim/s1-brief.md` |
| 2 | 軽量版で省略 (brief が plan を兼ねる) | — |
| 3 | read-only codex 相談 2 本 (A = 統計設計と推論、B = 留保の漏洩・HARKing・凍結契約・実行可能性と過剰) | `verbatim/s3-consult-A.md`、`verbatim/s3-consult-B.md` |
| 4 | 全 22 所見を real・採用、plan v2 | `verbatim/s4-ruling.md` |
| 5 | 親が本文を書いた (実装面なし) | 本文 |
| 6 | read-only codex review 1 本 | §4 |

相談 2 本の出力は行末空白を可逆に除去して写した (`verbatim/NORMALIZATION.json` に原文の sha256・byte 数・除去した行と文字列)。

## 2. 相談で変わったこと (brief → 本文)

- **n = 8 → 32。** n = 8 では同等をほぼ宣言できない (相談 A3 の算術)。δ = ln(1.03) は据え置いた。
- **多重性:** brief は「cell 単位は無補正、全 cell の追試を防壁にする」だった。相談 A4 が、追試一致は補正の代わりにならない
  (比較数百で偶然一致の上界が 0.39) と示したので、cohort ごとの Bonferroni 同時区間 + 両 cohort 一致に変えた。
  本文 §6.3 の誤り率は、θ が割当てに条件付きで cohort 間で違いうることを親が自己点検で足し、「θ₁ または θ₂ について
  10% 以下、θ が割当てに依らなければ 5% 以下」とした。
- **既知別枠:** Silo の balanced × read-modify-write は既存の性能測定があるので主要族から外した (相談 B3)。
- **不使用義務と解禁:** 対象を値・結果・派生した指示と設定に広げ、解禁を「全手法・全独立探索の凍結後」にした (B1・B2)。
- **改訂契約:** 着地から発効までも本文を書き換えず、結果閲覧後の変更は発効前でも事後改訂とした (B6)。
- **TPC-C:** 登録期限を「TPC-C の生成・探索・選択の開始前」にした (B8)。
- **R2 の名前:** 「正式 protocol の格子最良」を「学習錨で事前に選んだ既知の静的設定」に改めた (A6)。
- **主張の範囲:** 登録点での局所転移、別日・別割当てでの再現確認までに限定した (A1・A5)。

## 3. 既知結果の検索

親の検索式と生出力は `verbatim/known-scan.md`、調査子の報告の要点は `verbatim/facts.md` の 9。
本文 §10 の「この検索範囲では見つからなかった」はこの 2 つの範囲に限る。

## 4. 段 6 review

(段 6 の review 後に追記する。)

## 5. 本 wave がしなかったこと

- 計算投入、runner の実装、発効の決定、MOCC の参照の選定、TPC-C の留保。
- 8b の holdout 機構への変更。三軸走査の出力を本 insight へ写すこと (F1013 の再発防止)。
