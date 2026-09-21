# 依頼の逐語 (/dev-wave 引数、2026-09-21 14:02 JST)

[T-2797] B-5 生成器対照の発効束のうち Tier0 を実装する (D2200 項 1 の (2) 5「Tier0 未実装は受容せず実装する」)。対象は
  orchestrator/campaign/b5_generator_contrast.py の共通 Tier0 (コンパイル + 固定スモーク) で、現行の tier0_status="not-implemented"
  を実処理・結果記録・通過/失敗の検証に置き換える。事前登録 docs/b5-generator-contrast-preregistration.md §3.1 のとおり、文法・検疫・Tier0
  の不通過は A だけを消費して B は消費せず、A/B の分離は Tier0 通過で決まる。同じ wave で LLM arm の親運用 (並列本数と 1 機会 2,700 s
  の期限の整合) と全 arm 同一の job walltime (§3.3) の設計を決める。§12 の hash 採取と、倍率・発効 commit の 1 行再提示は、T-2830 と本 wave の
  land 後の別段で行う。起動時に稼働中の T-2830 (tools/pegasus/p3_s4_loop_pegasus.sh / b5_contrast_launch.py) と T-2632
  (orchestrator/campaign/p3_s4_loop.py / p3_b4_prerun_caller.py) の編集面を照合し、共有 file に触る箇所は相手の land 後に当てる。一次資料は
  output/insights/2026-09-20/t2797-b5-contrast/README.md §6 / §8。実装は Codex author (D95)。規律 2 は緩めない。B-5
  本走は未認可なので投入しない。着手直前の local main から fresh worktree。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外。
