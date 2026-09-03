---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-f813-cmake-identity
seq: 2
---

## 新規

### {{F:sink-scanner-loses-target-on-path-variable}}. 実体を絶対 path 変数へ固定したら、検査対象の走査がその file を静かに見失った [恒真ゲート] [テスト代表性]

- 事象: `certify_calibration.sh` の `build_argv=(cmake --build ... --target ycsb_silo.exe)` を
  `build_argv=("$CMAKE_PATH" --build ...)` へ変えた。`test_ccbench_spawn_sites.py` の
  build sink 走査は `\bcmake\s+--build\b` にしか一致しないため、**同 script が
  `_benchmark_build_sinks()` の集合から脱落した。** 集合を消費する
  `test_define_sink_cross_product_has_no_unreviewed_ungated_member` は**赤にならず**、
  縮んだ集合に対して通った。段 6 の敵対レビューが検出し、親が実測で確認した。
- 根本原因: 走査が実体を**literal の command 名**で認識していた。実体を PATH 依存から
  絶対 path へ固定する変更は、まさにその literal を消す。**安全にする変更が、
  その安全性を検査する側の対象集合を縮める**という向きの結合だった。
  集合の要素数・特定要素の在否を検査する positive control が無かったため、脱落が黙って通った。
- 恒久対応: 走査を `$CMAKE_PATH` / `${CMAKE_PATH}` 経由の呼び出しへ広げ
  (`--target` と `ycsb_` の要求は維持)、`_benchmark_build_sinks()` の集合が
  `tools/pegasus/certify_calibration.sh` を**含む**ことを実体名指しで assert する
  `test_production_build_sinks_include_certify_calibration_script` を置いた。
  性質だけの assert にすると同じ脱落を再び見逃す ({{D:record-validator-is-the-acceptance-authority}} と同じ、
  「機構の正例は実体を名指しする」原則)。
- 再発検知: 対象集合を走査で組み立てる検査を持つ file で、走査対象側の command・path・
  識別子の書き方を変えるとき、**集合の要素が減っていないか**を先に確かめる。
  集合を消費する検査が緑であることは、集合が正しいことの証拠にならない。
  要素の在否を名指しする positive control を集合ごとに 1 本持つ。

## supersede 追記

- F813 **supersede: 2026-09-03** — 恒久対応の「gate 側に wrapper hash と configure argv を束縛する変更が要るが、それは本 wave の編集面の外であり、未実装である」は実装した。green record は gate が実行した CMake の実 path・内容 SHA-256・stat identity・実効 configure argv を保存する。**ただし「機械的な検出器は無い」は依然として正しい** — 束縛は記録であって拒否ではなく、安定した wrapper は今も受理される。狭まった受理集合と残る限界の正本は {{D:cmake-identity-bound-to-green-record}}。
