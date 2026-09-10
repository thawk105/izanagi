## 対応表

所見 1: closed

- 凍結項目表は、D1266 により記入者・レビュー者がともに `thawk105` に固定済みで、再裁定しないと明記した。[事前登録:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:901)
- これは §5.1 の役割定義および D1266 の決定と一致する。[事前登録:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:174)、[D1266:41167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/decisions.md:41167)

所見 2: closed

- §11 は、材料レポートが文書を読まず floor 不在を渡し、floor 行だけを埋めても経路が変わらないと正しく説明した。[事前登録:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:846)、[実装:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_material_report.py:224)
- 4 分類の必要条件にも、材料レポート側の floor 接続の裁定・実装が追加された。[事前登録:994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:994)、[事前登録:997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:997)

所見 3: closed

- §11.2 の直下で、本節は測定を許可も要求もしないと再宣言し、各項を事実と案に区分した。[事前登録:914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:914)
- driver / adapter は案とされ、本節は実装を要求せず、実装可否をユーザーが決めると明記された。[事前登録:984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:984)

所見 4: closed

- 記述は「各 campaign で n=59、2 campaign 合計 n=118」に修正され、236 セッション、3,540 秒、追加1,770秒と整合する。[事前登録:955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:955)

## 新しい所見

所見 5: must-fix — 「事実」と「案」の包括分類が本文内で矛盾している。

- §11.1 は「以下はすべて案」と宣言する一方、その直下でD1383、D1060、D1377による決定を「案ではない」としている。[事前登録:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:858)、[事前登録:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:862)、[事前登録:871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:871)
- §11.2 も「以下はすべて案」とした直後に `*事実*` を列挙している。[事前登録:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:916)、[事前登録:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:919)

所見 6: must-fix — D1383が定めた範囲を事実として過大引用している。

- 本文は「AIは測定実行者・証拠承認者・floor記入者にならない」全体をD1383の既決事項とする。[事前登録:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:860)
- D1383が明示するのは、AIが案と計画を用意すること、担当者と証拠はユーザーが決めること、AIが値を既成事実として埋めないことまでである。測定実行者・証拠承認者からAIを一律排除する決定は書かれていない。[D1383:44017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/decisions.md:44017)

## 検算した数値

- 各 campaign の n: `ceil(log(0.05) / log(0.95)) = 59`。本文の59と一致。
- 2 campaign 合計: `59 × 2 = 118`。本文の118と一致。
- 候補側: `118個のD × 2セッション/D = 236セッション`。本文と一致。
- 名目 bench: `236 × 5反復 × 3秒 = 3,540秒`。本文と一致。
- 参照点追加: `118 × 5反復 × 3秒 = 1,770秒`。本文と一致。[本文の数値:956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:956)

## 総括

- 前回の must-fix 4 件はすべて closed。
- ただし、新しい must-fix 2 件があるため、このまま記録してはならない。
- §5.1.1 の抽出範囲はH4から次のlevel 4以下の見出し直前までである。[consumer:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301)
- 現行とHEADの抽出結果はともに21,833 bytes、SHA-256はpinと同じ `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`、byte比較も一致した。[pin:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)
- §5の表もHEADとbyte単位で一致し、値セルの変更は0件、floorは `未記入` のままである。[事前登録:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:156)
- テストは実走しておらず、静的読解、diff、hash、byte比較、算術検算のみを行った。