**共通参照点** `reference_tps` は、その block の precursor から祖先方向へ辿って最初に現れる
certified snapshot の session-level throughput とする。**参照点はこれ 1 つとし、
arm 内前後の別基準を使わない。** 該当する祖先が無い、複数の候補が同着で並ぶ、
対応する throughput の receipt が `PerfConfig` と `env_tag` の一致で特定できない場合は、
その block を適格でないとする (実走前に判明するため `design_not_feasible` の対象であり、
実走後に判明したら protocol violation とする)。**代替基準へ切り替えない。**
参照点の出所 (`reference_snapshot_hash` と `reference_receipt_hash`) は
`analysis_manifest` に固定し、分析時に差し替えられないようにする。
