---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2186-t2239-tuned-adaptive-control
seq: 1
title: [T-2186] 調整済み adaptive の実対照を論文側の台帳へ結んだ — 「同じ図に並べる」図は既にあり、欠けていたのは台帳への登録だった (docs のみ、branch worktree-dev-wave-t2186-t2239-tuned-adaptive-control、実装面の差分 0)
---

## 本文

- **依頼の前提が 2 つ、起動時の実測で覆った。** wave 引数は D1475 を正本と指したが、調整済み
  adaptive の定数は後続の D1505 / D1506 が置き換えており、現行は刻み 1 µs / 更新間隔 2560 µs /
  上限 1000 µs である。また [T-2239] の carry は「新規計測が要る」と書いていたが、それは旧
  `linux-baremetal` の図へ線を足す場合の話で、Pegasus 単一環境で 3 系列を同じ軸へ描いた図
  (`t2187_stage2_thread_axis`) は既に存在した。**carry は書かれた時点で正確であり、stale では
  なかった。** 変わったのは、本 wave では新規計測が要らなかったことだけである。
- **段 3 の敵対相談 2 本が、親の段 1 brief の前提を 4 つ実体で覆した。いずれも採用した。**
  (1)「論文側から図へ到達できない」は誤りで、一次資料の insight 経由の 2 段経路が既にあった。
  正しい欠陥は「図の台帳に調整済み対照が 1 行も登録されておらず、基準線の段落から直接選べない」
  である。(2) 親が brief に書いた検索コマンドは archive を除いておらず、示した件数と一致して
  いなかった。(3)「[T-2186] 完了済み、carry は stale」は完了の射程を混同していた。
  (4)「3 定数を出す producer が実在しない」は一般化しすぎで、正しくは「この v2 consumer surface
  に producer がいない」である。
- **親の provisional 裁定 3 件は結論として維持されたが、うち 2 件は根拠が差し替わった。**
  昇格しない理由は「未認証だから」ではなく、証拠の鎖が切れること・新図を検査する consumer が
  無いこと・既存 asset が凍結物であることの 3 点である。gate を拡張しない理由も「producer 不在」
  ではなく「この consumer surface に producer がいない」である。
- **三軸 conjunction の走査で、権威テストが hold されていることが分かった。**
  `orchestrator/tests/test_s8b_repo_scan_invariant.py` を焦点走したところ passed ではなく
  **1 skipped** で、成長 hold (`correctness_gate=true`、`release_condition=explicit-user-command-only`)
  に入っていた。hold の解除はユーザーの明示命令を要するので**解除していない。** 代わりに、同
  テストが検索 pattern を取得している production 側の CLI
  (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、書き込みなし) を直接走らせ、
  両 holdout とも hit 0、陽性対照 145 件の発火を確認した。**実走したのは走査であって hold された
  テストではない。**
- **codex 子は 3 本** (段 2 プラン 1 本、段 3 敵対相談 2 本、いずれも read-only / xhigh)。
  段 5・段 6 は実装面の差分が 0 のため飛ばし、`4 -> 7 -> 8 -> 9` とした。変異 matrix は
  DW-S04 の実装面差分ゼロ規定により免除した。
- **設計判断は D1505 / D1506 をそのまま適用しただけで、新しい裁定は起こしていない。**
  したがって decisions fragment は作らない。

## 次の一手差分

### 完了

- [T-2186] 既定 adaptive を単独基準線にしていた箇所の差し替えは前 wave で 10 単位すべて着地して
  おり、本 wave の独立再走査 (段 2 が 5 系統、段 3 が 13 系統の検索式) でも未差し替えは 0 件、
  成果物を変える新しい残余も 0 件だった。残っていた 1 点である「調整済み adaptive を正式な対照
  として論文側から参照できる状態」を、図の台帳への登録と論文入口からの名指しで閉じた。
  remaining: none
  base: 187099e671af0b161d8e913b105f2f65f3647497b2915a5a01c65ff837b2ecfd
- [T-2239] 調整済み adaptive を実際の対照として同じ図に並べる、を閉じた。図
  (`output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis`)
  は既に無 backoff・既定 adaptive・調整済み adaptive を同じ軸へ描いており、新規計測も新規作図も
  行わずに論文側から名指しした。前提条件 (1) の `BASELINE_BY_GENOME` 拡張は、この経路の生成器が
  既定セル以外へセル名を label として付け既定セルの一意性を構造的に要求するため当たらない。
  前提条件 (2) の correctness は [T-2189] の所掌であり、本項の終端はそれを含意しない。
  論文図への昇格も行っておらず、それは別途決着させる。
  remaining: none
  base: 98228cdb4dee253725c3c3b24002a7f898629cc3d3939f9c24ac64d729fd8b19

### 新規

- {{T:a1-legacy-default-adaptive-contrast}} **P2・ユーザー裁定待ち**: A-1 の
  `paper_story_a1_paired.py` の `submit --study-id` が既定で選ぶ旧 study の contrast は
  `static10` 対**既定** adaptive (`BACK_OFF=1, BACKOFF_FIXED=-1`) である。job body
  `tools/pegasus/paper_story_a1_paired.sh` も旧 study を既定にし、
  `orchestrator/tests/test_paper_story_a1_job_contract.py` がこれを固定している。
  同 policy は `formal=false` / `promotion_prohibited=true` / `result_authority=exploratory` を
  宣言しており、D1506 は既定 adaptive を測ること自体を禁じていないので**現時点で規律違反では
  ない**。しかし「既定で選ばれる実行経路の contrast が既定 adaptive を適応側に置いている」状態は
  残る。既定を動かすかどうかは凍結 policy と互換経路の別裁定であり、ユーザーの手番とする。
