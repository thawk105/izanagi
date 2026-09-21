# 依頼の逐語 (2026-09-21 08:2x JST、/dev-wave 引数)

[T-2812] (entry 1747、D2150 項 1 ②③⑤、D2184、一次資料 output/insights/2026-09-20/t2304-pin-advance/README.md §4) 新 pin e9e477ca の
  main から旧系列 (K2 の巡・A-1 sized・凍結 v2 g1 の launch・B-4 床値の binary 再利用)
  を再開・再投入する前に要る整合を系列ごとに設計し、裁定パッケージにする: ② 新登録と identity、③ driver の pin (p3_s4_loop.py の D1936 独立
  full OID 等)、⑤ successor floor protocol (AI reseal)、source / admission (policy epoch db6bc9ea…)。凍結 v2 g1 の live launch_validate が段階
  4 の policy 照合で manifest-invalid のまま止まる (entry 1776、output/insights/2026-09-20/t2810-g1-launch-validation/README.md §5)
  のを解く経路を含める。設計と login の read-only 実測 (各系列の現状の拒否内容) が本体で、実装は裁定後の別 wave。旧 binary の再 admission
  だけでは解消しない (D2184) を前提に置く。それまで旧系列は pin 前進前の固定 checkout (submit-tree) から走る、を変えない。着手直前の local main
  から fresh worktree。規律 2・7 を緩めない (旧系列の記録済み判定は不変)。本題だけ。gate・台帳・一般化の追加は scope 外。

(途中のユーザー発話 2026-09-21: 「どう？」 = 進捗の問い合わせ。scope の変更なし)
