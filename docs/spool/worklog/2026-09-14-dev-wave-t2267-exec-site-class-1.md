---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2267-exec-site-class
seq: 1
title: [T-2267] 実行場所分類の対象・入力・実行条件を確定し、経路不足を実測で特定した (docs のみ、branch worktree-dev-wave-t2267-exec-site-class)
---

## 本文

- **D1938 の委任を実行し、対象・入力・実行条件を現物で確定した。** 対象は
  `tools/t2216_backoff_walk_model.py`。明示入力は 5 files / 297,814 bytes。記録は
  `output/insights/2026-09-14/t2267-exec-site-classification/README.md`。
- **本走の分類はできていない。** T-2216 model の凍結入力・本走 argv を受け取れる認可済みの
  login dedicated-scope 経路が、調査した現行実装には無い。分類は `unknown` のまま据え置く。
  不足の成立条件を仕様化し、{{D:exec-site-classification-route-gap}} で裁定へ返した。
- **親の断定 2 件を段 3 が refuted にし、親が採用した。** (1) 無限定な「login dedicated-scope 経路は
  存在しない」は誤りで、pytest と履歴監査の認可済み scope は実在する。限定形だけを使う。
  (2) 「凍結 `measured.json` は不在」は走査範囲の誤りだった。範囲外に完全一致 2 本
  (各 269,108 bytes) があり、親・段 2・段 3 が独立に sha256 を照合した。本走 argv は再現可能である。
- **メモリ観測は §7.0 手順による実測ではない。** 既存 runner の sampler は scope 起動後に開始し
  ループ待機が 5 ms で、§7.0 の先行 sampler・間隔 ≪1 ms とは異なる。したがって certified peak を
  計算せず、class も変更しない。提示 cap は付与予算であって実効 `memory.max` の逐語観測ではない
  (未取得)。cap が走ごとに違うため「3 反復」とも書けない (cap 別に 1 走 / 2 走)。
- **参考観測として残した値。** `tools/run_tests.py` の bounded scope で
  `orchestrator/tests/test_t2216_backoff_walk_model.py` を走らせた観測ピークは、
  xdist 32 worker で 2,834,767,872 bytes、serial で 159,653,888 / 156,565,504 / 161,529,856 bytes。
  test は合成入力・pin 差替え・`predict_all` の fake 化を使うので、対象 model の footprint を bound しない。
- **hook 拒否を 2 件実測した。** raw `systemd-run` は LOGIN/SUSPECT で拒否される。
  admission registry の JSON path を含む python heredoc の読み取りも拒否された — こちらは
  不透明構文と防護パスの同居を分類不能として落とす**設計どおりの fail-closed** であり、欠陥ではない。
  registry は `cat` / `jq` か Read ツールで読む。迂回は一切していない。
- **wave 中に local main の commit が同内容・別 SHA へ差し替わり、`DW-O20` の `--ff-only` 追従が
  不能になった** ({{F:ff-only-fails-when-main-commit-is-replaced}})。branch を作り直して復旧した。
- **棄却した攻撃 (段 3 と親が同意)。** 内部 seam の転用・compute の `generic`・namespace 隔離・
  `--help` の通過・dispatcher の `legacy-admitted` は、いずれも認可済み login scope の反例にならない。
  凍結 pin 一致 JSON の repo 複製は一律禁止ではないが、本 wave では複製せず保全先を裁定へ回した。
- 段 4 で「実装しない」と裁定したので段 5・6 を飛ばした。実装面の差分はゼロで、変異 matrix は免除。
  受入全走は免除せず実走した。

## 次の一手差分

### 更新

- [T-2267] **P2・AI 実測継続 / 裁定待ち 3 件**: 対象・入力・実行条件は確定し、既存の認可経路で
  取れる参考観測まで取った。残るのは本走の分類で、login dedicated-scope 経路が無いために未実測。
  {{D:exec-site-classification-route-gap}} の裁定 3 件 (対象限定経路の可否 / 非 `tools/pegasus/`
  path の class の扱い / 凍結入力 bytes の保全先) が要る。記録は
  `output/insights/2026-09-14/t2267-exec-site-classification/README.md`。
  base: 87be9dfa75733c99fdbc2be4107ce9997609db3c5f820996cd5b423a728d9db1
