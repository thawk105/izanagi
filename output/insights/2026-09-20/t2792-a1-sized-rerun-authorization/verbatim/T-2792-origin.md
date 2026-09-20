# 依頼文の逐語 (dev-wave 引数、2026-09-20)

[T-2792] A-1 balanced5 sized study (paper-story-a1-20260901-balanced5-sized-v1) の attempt-0002
  (認可済み独立再現、研究目的 = 同一配置の反復) を投入可能にする択 1 を Codex author (D95) で実装し land まで。裁定 = 第 24
  回 /rulings 項 2 (控え /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-20-rulings-full24-verdicts.md、D2156 項
  3「改めて認可」の機械化)。内容 = durable base に exact な認可 record (study_id・attempt 名・source sha・裁定日 / D 番号)
  を置き、orchestrator/campaign/paper_story_a1_paired.py の _assert_no_prior_v3_bench_start は record が名指す attempt-0002
  に限って bench 後の group 再投入禁止を解除、_exact_materialization_destination は attempt 別の公開先を受理、事前登録 §6.1 /
  §6.4 は既存凍結物と attempt-0001 の判定を保持したまま「将来の観測にのみ適用する追補 (別版)」として書く (erratum
  の名で正当化しない)。record の形式は本 wave で起草。敵対レビュー + 変異負例 (別 attempt 名・別 study・別 source sha・record
  不在は従来どおり拒否) を実装条件とし、既存の intent / attempt root 再使用拒否・先行証拠の完全性検査・公開先
  create-only・anomaly 即 reject を保存 (規律 2 を緩めない)、非認証 lane のまま。一次資料
  output/insights/2026-09-19/a1-sized-attempt2/README.md §7。投入そのものは land 後の fresh submit-tree による別 wave (本
  wave に含めない)。着手直前の local main から fresh worktree。本題の実装だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。
