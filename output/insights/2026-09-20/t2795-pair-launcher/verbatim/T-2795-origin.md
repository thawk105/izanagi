# 依頼文の逐語 (/dev-wave 引数、2026-09-20 12:32 JST 起動)

[T-2795] (i) + [T-2797]/[T-1872] (α): K2 手動 loop の「同 job pair」launcher と B-5 事前登録 §10 の共有部品を
Codex author (D95) で段階実装し land まで。裁定 = 第 24 回 /rulings 項 3 (i)・項 4 (α)、控え
/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-20-rulings-full24-verdicts.md (記録 wave rulings-all-20260920 の fold
後は canonical の D 番号を引く)。内容 = (1) 同 job pair: job body (tools/pegasus/p3_s4_loop_pegasus.sh) に stock
step、driver (orchestrator/campaign/p3_s4_loop.py、value 受理域 1..1000) に stock genome の評価口、pipeline
(orchestrator/campaign/pipeline.py) 自身が発行する stock WAL、identity への影響の整合 — 設計メモ
output/insights/2026-09-19/k2-loop-round3/reviews/s2-plan.md 項 6; (2) 較正動作点 CLI: default_perf()
の無条件使用を承認済み PerfConfig の指定に差し替える口 (docs/b5-generator-contrast-preregistration.md §5.2 / §10、[T-2632]
の「委任だけでは実走可能にならない」経路); (3) exact correctness 経路: pipeline.evaluate の correctness 引数の指定・記録と
performance_correctness_workload() の接続 (§5.5)。内部は (1)→(2)→(3) の順に区切り、既存の correctness 拒否・anomaly 即
reject を保存する (規律 2 を緩めない)。候補 10 + stock の pair 投入 (認可済み)・4 巡目 (項 3 (iv))・B-5 試走 (β) は land
後の別 wave、B-5 本走は未認可。着手直前の local main から fresh worktree、起動時に稼働 wave との編集面重複検査 (現在 3 file
とも非占有)。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

(canonical は D2172 項 3・項 4 に fold 済み。verbatim/D2172-items3-4.md を参照。)
