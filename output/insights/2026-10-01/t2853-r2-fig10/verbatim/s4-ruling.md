# 段 4 裁定 — [T-2853] R2 fig10 (2026-10-01 JST、親)

段 4 直前の裁定 inbox 再走査: 開始後に T-2853 / fig10 / B-7 に関わる新裁定は land 調整役の連絡だけ (計算超過の継続承認 10:53 頃、CCBench pin の main 更新 10:54 の通知、lock 修正は別 wave へ回す判断)。ListAgents に fig10 の並走なし。

| ID | 事項 | 判定 | 処置 |
|---|---|---|---|
| (P1) | R2 の「記録された判定」は親が jq で別計算し `r2-record.json` に記録、wrapper は読むだけ | 採用 | 実施済み (10:57)。生成器の判定計算と一致 (不一致なら生成器が拒否) |
| (P2) | R2 の期待 hash は collect 後に親が record に書き、wrapper は自己計算しない | 採用 | 実施済み。前例 fig11 の A-F1 (自己照合) を避ける |
| 段 2・3 | 省略 (軽量版) | 採用 | 形は前例 fig11/fig6 と §0 で固定済み。設計択一は (P1)(P2) だけで、段 6 レビューで攻撃させる |
| s5 懸念 1 | provenance が描画時点の insight README hash を束縛 | real (記述で処置) | 束縛値は §0 だけの版 (commit e92aeea8f) と一致することを親が確認し insight §5.1 に明記。wrapper は変えない |
| s5 懸念 2 | caption 置換 2 が冗長 | 段 6 へ | レビューの判断を待つ |
| 計算超過 | 3.40 → 6.39 node 時間 | land 調整役の承認済み | 原因 (共有 bench lock) を insight §7 に記録。driver 修正は範囲外 (調整役が別 wave の投げ文へ) |
| 変異 matrix | repo の実装面差分 0 (wrapper は repo 外、repo 変更は insight・phase 行・spool のみ) | 免除 | DW-S04 |
| 受入 | 全走 1 回 | 必須 | CCBench pin 更新を含む local main を取り込んでから取る (調整役の助言) |
| 段 6 | read-only レビュー 2 本 (一次資料照合・正しさ境界 / 過剰・削除) | 採用 | 対象 commit 068f664dd |
