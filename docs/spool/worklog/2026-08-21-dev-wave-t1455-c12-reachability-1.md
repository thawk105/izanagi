---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1455-c12-reachability
seq: 1
title: _c12_allocation_binding_verdictのname-only判定をC06と同型のidiomへ強化した (コード+テスト、branch worktree-T-1455-c12-reachability、変異matrix = baseline PASSED・M-A 4/4 KILLED・M-B 4/4 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 一次資料は [T-1442] (C06 reachability 強化 wave) の worklog entry 770・段3 lensB が独立に発見した
  「C12 の `_c12_allocation_binding_verdict` (行2313-2327付近) が C06 現行 (改修前) と同じ
  `_reachable_calls` 名前一致弱点を持つ」という指摘、および `docs/decisions.md` D599 の
  「C06 は本 wave では修正せず後続 wave へ送る」という決定。設計は {{D:c12-allocation-declared-call}}。
- 段1 brief で親が一時編集+即時復元 (DW-O19) により、旧実装が decoy 関数・import alias・return 後の
  dead code の3経路すべてで fail-open することを実測確認した。
- 段2 codex plan (rc=0) が file:line 粒度の具体案を起草し、親 brief が見落としていた3件を独立に
  発見した: 直接 helper 呼出しテストが2本でなく3本 (`:279-300` を追加)、独自 supervisor を使う
  `test_cross_module_import_forms_resolve_exact_bound_target` にも fixture 修正が必要、
  cache assertion (`graph_cache_hits`) が新規 graph walk 追加で不整合になる (段2時点では未確定)。
- 段3 敵対相談2レンズ (sol=正しさ境界、luna=整合・scope) はいずれも must-fix ゼロ。lensB が
  cache assertion の期待値を「候補」でなく `[False, True, False, True]` へ機械的に確定した
  (cache key の呼出し順序から導出)。lensA が3種 fail-open を独立に追試・再現し、1行複数 alias
  import の解決も含めて正しさを確認した。副産物として `output/insights/2026-08-17_t1167-c12-allocation-binding/`
  ([T-1167]、C12 の allocation 節そのものを新設した先行 wave) を発見し、競合する裁定が無いことを
  確認した。
- 段5 (role=author) は確定仕様どおり2ファイルのみ変更したが、Pegasus dispatch preflight の
  sandbox 制約で pytest を1度も実走できず、「緑とは申告しない」と正直に報告した (DW-S05-C 準拠)。
  親が焦点走 (5ファイル、DW-O26 拡張) を投入し、1回目は queue-wait-timeout で infra 失敗、
  2回目で 837 passed / rc=0 を確認した (837件の出力は server 側で末尾のみ残り truncate
  されていたため、C12 限定の40件再走でも別途緑を確認した)。
- 段6敵対レビュー2本 (reviewA=diff正確性、reviewB=回帰・mutation準備) とも must-fix ゼロ。
- 変異 matrix 事前登録 (DW-M01) は段4裁定時に親が一時編集で実測したが、実装後の正式
  `tools/mutation_harness.py` 本走で当初の expected_nodes には無い追加 kill を2回発見した:
  M-A は cache-hit テストも副次的に kill していた (`_ReachabilityExplorer.walk` 呼出し回数が
  変わるため)、M-B は契約の `negative_control_id` (`nc_c12_reservation_check_bypassed`) 専用
  テストも kill していた (M-B の変異内容そのものがこのシナリオを表すため)。いずれも spec を
  修正し4回目の本走で baseline PASSED・両変異 4/4 KILLED・SURVIVED 0・MISMATCH 0 の完全一致を
  得た。中間結果は `mutation-out-attempt1-erratum.json`/`mutation-out-attempt3-erratum.json`
  として保全した (DW-M02)。
- Pegasus 計算ノードの混雑が本 wave を通じて顕著だった (焦点走・変異harness本走・受入全走の
  いずれも複数回 queue-wait-timeout による infra 失敗を経験、受入 lease 自体も同時に14以上の
  並行 wave が取り合っていた)。すべてコード内容とは無関係な infra 要因と確認したうえで再試行し、
  最終的に全て解消した。
- 受入全走 (`tools/dev_wave_wait.py acceptance`) は `verdict: "child-green"` (13970 passed,
  96 skipped, red/flake ともに0件)。待ち手が自動で local main を取り込む merge
  (`2b4c6c5f`, AI-Agent trailer付き, conflict無し) を行った。

## 次の一手差分

### 完了

- [T-1455] `_c12_allocation_binding_verdict` の name-only `_reachable_calls` 判定を
  `_ReachabilityExplorer`+`_declared_call` へ強化し、negative control 3本と変異 A/B の
  完全一致検証を完了した。
  remaining: none
  base: 0ef571cd03caece6cdfe1d67c3e9228f8dffa4b6384ab0798d04c19abdec4ac4
