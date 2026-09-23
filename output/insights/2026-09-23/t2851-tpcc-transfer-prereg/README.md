# [T-2851] の残り (4) TPC-C の留保条件の事前登録 — 起草の経緯 (2026-09-23)

- 成果物: `docs/tpcc-unseen-condition-transfer-preregistration.md` (TPC-C 版の事前登録 v1) と `docs/README.md` の 1 bullet。
- 依頼: ユーザー直接起動の `/dev-wave` (逐語 = `verbatim/request.md`)。v1 (`docs/unseen-condition-transfer-preregistration.md`) §14 が必須の未完項目とした
  TPC-C の留保を、TPC-C の生成・探索・選択が始まる前に別の登録で固定する (D2212 項 2)。T-2850 の選択結果・測定の発効・runner 実装・計算・
  gate / 検査 / 台帳の追加は scope 外。
- 起点: local main `cadaf3805` から作った fresh worktree (開始 gate rc 0、08:36 JST)。CCBench submodule `e9e477ca`。job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2851-tpcc-prereg` (prompt・launcher・log)。

## 1. 段ごとの経過

| 段 | 内容 | 所在 |
|---|---|---|
| 1 | 事実調査 (読取り専用の Claude 調査子 1 本、sonnet) と親の現物検算、brief と攻撃対象 (P1)〜(P9) | `verbatim/facts.md`、`verbatim/s1-brief.md` |
| 2 | 軽量版で省略 (brief が plan を兼ねる) | — |
| 3 | read-only Codex 相談 2 本 (A = 条件設計の妥当性、B = 留保の漏洩・不使用義務・解禁・HARKing・v1 との整合・過剰)。08:49 起動、08:53 / 08:54 完了 | `verbatim/s3-consult-A.md`、`verbatim/s3-consult-B.md` |
| 4 | 全 17 所見を real・採用、plan v2 | `verbatim/s4-ruling.md` |
| 5 | 親が本文を書いた (実装面なし) | 本文 |
| 6 | read-only Codex review 1 本 (NO-GO)、親の裁定と修正、焦点再レビュー | `verbatim/s6-review.md`、`verbatim/s6-ruling.md`、`verbatim/s6-focus-1.md` |

## 2. 相談で変わったこと (brief → 本文)

- **指標の意味 (A1):** 1 走の値を「同じ生成規則の下で、abort 後の取引種別の再抽選・commit 構成の変化を含む全取引 commit throughput」と定めた。
  CCBench の TPC-C は abort した取引を再試行せず `query.generate` から引き直すので、候補によって commit された構成が変わる。tpmC・取引別の改善は主張しない。
- **段 2 の構成の因子 (A2):** 範囲読み 3 取引を各 10 にすると、未配送注文の表が 3 s の間に減る向きに変わる (1 倉庫で約 12,300 commit の粗い目安)。
  水準は維持し、「3 取引の生成比率を同時に変える複合変更」として報告する規則にした。
- **検索の射程 (A5・B1):** 「TPC-C の性能測定 0 件・生成は未開始」を「検索範囲で見つからなかった」に限定し、[T-2854] の構造検査 (TRACE=1、thread 2・extime 1 s・
  倉庫 1) の出力に throughput 36,156 があることを開示した。
- **v1 の継承 (A6・B3・B4):** v1 を commit `da869768d` の版 (SHA-256 `ae8b2c32…`) で固定し、後日の追補・Erratum を自動で波及させない。TPC-C 固有の置換表
  (binary・job・cell・順序の鍵・比較範囲・強い参照・主要族・集約・欠測) を本文 §5 に置いた。
- **不使用義務 (B2):** v1 §3.1 の義務を TPC-C に明示適用し、留保を見て作った近傍条件・短縮版・較正の禁止と、段 1 → 段 2 の還流禁止を足した。
- **解禁 (B5):** 認定経路の条件を「印を外すこと」でなく「発効対象の protocol・emitter と pin・登録した取引構成を扱える既存の認定経路」にした。
- **強い参照 (B6):** TPC-C に既知最良が無いので、protocol ごとに 3 択とし、固定できなければ記述専用を既定にした。参照の選定用と評価用の錨の測定を分けた。
- **費用 (A3・B9):** 1 倉庫の一次表は約 529,011 行 (48 倉庫で約 2,549 万行) で、ロードの秒数は未測定なので、試算の数値を置かず式の形だけを固定した。

## 3. 既知結果の検索

親の検索式と出力は `verbatim/known-scan.md`。本文 §7 の「見つからなかった」はこの範囲に限る。

## 4. 段 6 review

- read-only Codex review 1 本 (HEAD `8ea43a680`、09:06〜09:09、`verbatim/s6-review.md`): NO-GO、must-fix 1・should 2・nit 1。一次資料の事実
  (CCBench の引数・行数・再抽選・home 割当て、[T-2854] の数値、v1 の sha256 と節) と算術は全て照合が取れ、段 4 の 17 件は全て反映済みと判定された。
- must-fix R1: §8 の「発効の決定で cell を外せる」が §9.2 の凍結と衝突する。削り、予算不足は段の発効の延期、縮小配置は別の登録とした。
- should R2 (検索の射程の言い方)・R3 (thread は錨より低い 2 水準だけ、OFAT の定義)・nit R4 (extime の合計の意味) も直した (`verbatim/s6-ruling.md`、commit `79d52f990`)。
- 焦点再レビュー: 後述 §6。

## 6. 焦点再レビュー

- 1 巡目 (read-only Codex、HEAD `79d52f990`、09:12〜09:13、`verbatim/s6-focus-1.md`): **GO、must-fix 0**。R1〜R4 は全て closed、新しい所見なし。
  修正文の量化 (cell・cohort を減らさない、thread は 12・24 だけ、74 file = 62 + 6 + 3 + 2 + 1、116 = 74 + 42) を本文と検索記録から検算した。

Codex の出力 4 本 (相談 2・review・焦点再レビュー) は、行末空白 (計 7 行) を除き末尾に LF を足す可逆な正規化をして写した。原本の sha256・byte 数・
除いた文字列は `verbatim/NORMALIZATION.json` にある (原本は job dir)。

三軸語の走査器 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc 1 で、hit は main に既存の
`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file だけ (本 wave の file は 0 件)。

## 5. 本 wave がしなかったこと

- 計算投入、runner の実装、発効の決定、R* の選定、TPC-C の探索の設計、v1 の本文の変更、段 1・段 2 の認定経路の実装。
- 並走中の [T-2850] 試走の事前登録 wave (`t2850-trial-prereg`) の作業木を読取りだけで確かめ、同書が TPC-C を扱わず v1 だけを参照していることを見た
  (本書との衝突なし)。
