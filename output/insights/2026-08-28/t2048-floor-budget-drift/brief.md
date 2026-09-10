# 段 1 brief — [T-2048] floor 予約予算 drift

- scope: `tools/pegasus/floor_campaign.sh` 冒頭の予約算術コメントと `tools/pegasus/README.md` §5 の同じ説明を、現行 calculator と scheduler authority に合わせる。
- authority: scheduler request の wire source は job script の PBS directive 36000 秒。policy の同値は期待値・submit receipt 値で、job が qstat の実効 limit 36000 秒との一致を検査する。
- authority: driver の `_floor_reservation_budget()` は現行 protocol / 12 cell / 8 session / retry 2 / sort_best を入力に、共有 dependency prebuild 1800 秒を含む `required_s=30000` と finalize 600 秒を返す。
- drift: shell コメントと README は共有 dependency prebuild 導入前の `required_s=28200`、合計 28800 秒を残している。
- 原因: [T-1128] が sort_best の configure / target 各 900 秒を reservation 式へ加えたが、説明側 2 箇所が追随しなかった。
- (P1) provisional 裁定・攻撃対象: scheduler の canonical 予約値 36000 秒と、driver が検査する最小 envelope 30000 + 600 = 30600 秒は役割が異なる。値を同一化せず、前者を「予約値」、後者を「導出 envelope」として同じ算術へ揃える。
- (P2) provisional 裁定・攻撃対象: 本番ロジック・policy・protocol・凍結成果物は変更せず、stale な説明だけを最小修正する。既存の exact calculator test と policy-over-envelope test を関連受入に使い、新 gate は作らない。
- 凍結境界: R33 は `s8b_oracle_n_pilot.py` / `oracle_n_pilot.sh` を pin し、今回の floor 2 ファイルは pin 対象外。floor job script は submit 時の source commit / blob hash へ動的に束縛される。
- 不変条件: D87 の scheduler walltime 36000、qstat 実値束縛、driver の preflight、finalize reserve 600、official 空集合、規律2を一切変更しない。
- 成果物影響: 放置すると operator 向け手順と実行 script が 1800 秒小さい envelope を表示し、予約余裕を 6300 秒と誤記する。修正後は scheduler request 36000、driver minimum 30600、raw headroom 5400、prologue 約900秒を仮定した estimated residual 約4500 の関係が一致する。
- 成果物: 2 ファイルの説明差分、既存焦点テスト、shell syntax、docs / Codex agents / provenance、T-2048 完了 fragment、逐語 plan/review と変異記録。
- 分割: 段 2/3 は read-only planner と異なる敵対レンズ 2 本。段 5 は D95 Codex author 1 本が shell コメントのみを編集し、親が docs 本文を統合する。
- 変異候補: 共有 dependency 1800 秒を説明から落として旧 28200 / 28800 / 6300 を復活させる。既存 calculator/policy test と literal scan の組合せで検出可能性を段 4 で確定する。
- scope 外: 一般 budget framework、新 schema、自動調整、余裕率再設計、周辺 budget の掃除、過去 D87 の歴史本文改稿、正式測定値の変更。
