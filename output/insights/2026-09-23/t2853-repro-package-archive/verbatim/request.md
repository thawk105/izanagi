# 依頼の逐語 (2026-09-23、ユーザー直接起動の `/dev-wave` の引数)

[T-2853] 再現パッケージの残り (2)(3) (計算なし・実装差分ゼロ)。正本は insight
  output/insights/2026-09-22/t2853-repro-package-estimate/README.md §7・§8・§11 と canonical worklog の [T-2853] 項 (entry 1822)。(2) job dir
  にだけある論文根拠の実験データ (B-5 試走の台帳・入力素材・LLM 入出力・報告、D2160・B-8 の保全 trace と runner、K2 pair
  (/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/originals-copy-20260922 を含む)、A-1 の attempt データ) を cleanup
  の対象外の保存先へ写し、sha256 manifest で bytes を照合してから完了にする (F1034 = 退避 tar が空のまま撤去して K2 原本を失った前例)。既存の
  proof chain は移動・編集せず、写しを official の正本へ昇格させない。locked の submit-tree は HEAD を進めず、削除もしない。大きい写しは login
  の資源上限を確かめてから行う。(3) 実験系列ごとの実行手順書と、R1 (再判定) の入力一式 (trace・当時の関連入力・verifier の版) を insight
  にまとめる。(1) の trace 保全口は同時に投げる [T-2849] の wave が持つ (分担済みなので譲り合わない)。同時に投げる [T-2860] も同じ r4
  原本を読むので、本 wave は読むだけで動かさない。本題の保全と手順書だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope
  外。着手直前の local main から fresh worktree を作る。
