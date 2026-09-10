# 親の実物照合

checkout: d85bbb21196f503440ef9641e3dec095e3b43844、T-2527専用worktree。

- `python3 -B -m orchestrator.campaign.s1_known_axes_freeze verify`: rc=1。
  理由はgenerator SHA不一致のみ。recorded=1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0、actual=8fea2bf2038d09498a5f0c235087ed1f6e86c16f36a29ade6953587ccc872940。
- `build_document`へ旧documentのfrozen_at_head/ccbench_pin/python_version/generator_shaを既存引数として渡し、結果と旧documentを再帰比較した。rc=0。
- 差分はentries配下のsource SHA24箇所だけ。重複を除くpathはaxis_trigger_gating.py、s8a_trigger_sweep.py、genome.py、backoff_sweep.py、s6_sort_sweep.py、p3_s4_loop_sort.pyの6ファイル。
- flags、述語、comparator、参考値、選定、source path/key/lines/順序/件数、その他のfieldに差はない。
- 正規引数で当時の記録fieldを保持して比較した読取検査であり、現行verify_documentが旧文書を受理したという実測ではない。
- 旧sourceを現行hashへ書き換えたり、実物artifactを書き換えたりしていない。
