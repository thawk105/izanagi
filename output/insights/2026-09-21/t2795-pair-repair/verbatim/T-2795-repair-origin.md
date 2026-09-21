# [T-2795] 修復 wave の依頼 (ユーザー、/dev-wave 引数の逐語、2026-09-21 08:2x JST)

[T-2795] (D2187、D2194 項 2、控え /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full27-verdicts.md 項 2) K2 同
  job pair launcher と claim の整合を直す修復 wave。着手直前の local main から fresh worktree。一次資料
  output/insights/2026-09-20/t2795-k2-pair-attempt/README.md と D2183。修復方向 = 1 回の認可・claim の所有期間で候補と stock を両評価する
  driver 設計 (orchestrator/campaign/campaign_claim.py の claim leaf は不変、orchestrator/campaign/p3_s4_loop.py の run_campaign
  の認可契約または --stock-control の呼出し形を変える。D553 の sink-local single_process と D2183 の CLI 排他への影響を段 1 で明示)。却下済み =
  同 identity path の DEAD 再取得、claim の rename / 退避、別 out_root、stock 未測定の捏造判定。同 durable root・Pegasus 契約
  (single_process=True、reservation → 認可 → claim) での候補→stock 連続起動の結合検査 (F1019 再発の恒久対応) を必ず含める。Codex author (D95) +
  敵対検証子 + 変異負例。修復後の pair 再投入 (1 job) と 4 巡目 (択 A、1 job) はユーザーの予算再提示なので本 wave
  では投入しない。submit-tree-pair (/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/、lock 済み、原本 5 file) は触らない。[T-2830] /
  [T-2632] が同じ p3_s4_loop.py / tools/pegasus/p3_s4_loop_pegasus.sh を編集するので本 wave を先に land する。規律 2
  を緩めない。本題だけ。gate・台帳・一般化の追加は scope 外。

(途中のユーザー発話: 2026-09-21 08:4x JST「どう？」— 進捗確認。方針の変更なし)
