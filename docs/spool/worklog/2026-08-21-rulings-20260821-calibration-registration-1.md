---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: rulings-20260821-calibration-registration
seq: 1
title: ユーザー裁定を記録し、rr80/rr20 calibration の dev-wave 実行経路を準備する
---

## 本文

- `/rulings all` に対するユーザー裁定を反映した。推奨方針は受け入れるが、rr80/rr20 calibration の
  取得・検証・登録を人間の手作業に残すことは受け入れない。AI/ツールが計算ノードで実測し、既存の
  schema、acquisition receipt、自己比較、hash binding、create-only publish を通過した場合に登録する
  dev-wave 経路を正規化する。rulings session 自身は実測を起動しない。
- 現在の `output/env/pegasus/calibration/registered/` には rr50 の2件だけがあり、rr80/rr20 は未登録。
  `submit_certify.sh` と `certify_calibration.sh` が workload を rr50 に固定していたため、投入時の
  rr80/rr20 選択を20/50/80の whitelist として実装し、submission receipt・compute job の再照合・
  job-result へ同じ workload を束縛する tooling の変更を行った。実際の起票・実測・登録は別 dev-wave
  で行う。
- この session が誤って直接投入した rr80=`930578.nqsv` / rr20=`930579.nqsv` は、実行前の Queued
  状態でキャンセルした。これは calibration の成果・受入証跡ではなく、将来の dev-wave で再利用しない。
- この経路の追加は、正式 H1/H2 launch、g1→g2 activation、D145 の再訪、T-424/T-272 の要求閉包を
  代行しない。較正登録が成立しても、それらの別 gate が未成立なら正式実験は起票しない。
- T-1461 の当初の二ファイル限定案は dead wiring だったため、実効的な依存解決・hash・build前 gate
  まで含む scope expansion を許可する裁定を記録する。
- T-1472 は provider-init failure を C04 の crash/indeterminate 対象へ含める方針を採用する。
  実装・受入は別の wave で行い、この記録だけで完了とは扱わない。
- handoff に残っていた改善候補は採用候補として保持する。reasoning pin の multi-unit split、
  detached mutation の実 detach 契約、mutation cascade の事前 probe、Wave C 完了報告の fenced
  block 外総括、mutation/acceptance clean-tree 順序、ListAgents の補助的 liveness 証拠を次の
  self-improvement wave の入力にする。

## 次の一手差分

### 更新

- [T-1461] **P1・ユーザー裁定反映**: floor driver が実際に読む `_prepare_floor_oracle_dependency()`/
  buildcache 経路、preverified payload、独立 expected hash、CMake前 pin 検査、compute-node offline
  transport→no-refetch→build test まで含めて実効 scope を実装する。
  base: bf97bb36202b75093dd8979c544ce66a63b67012ad9aa3eff1c668015402ee1f
- [T-1472] **P1・ユーザー裁定反映**: provider-init failure を C04 の indeterminate/crash 処理へ
  含める実装 wave を起票する。既存 `_finish_trial` の実装だけで完了とは扱わない。
  base: 35f7c080a8a08fa552888dd39954b01508fdbcfcb56d6a28937498bd6662893f
- [T-425] **P1・条件更新**: 正式 H1/H2 launch は T-424/T-272 の要求閉包または D145 decision 5 の
  明示的再訪と、必要な別 gate が揃うまで閉じる。ただし rr80/rr20 calibration の取得・検証・登録は
  人間 lockstep を要求せず、今回の AI/ツール経路を使えるものとする。
  base: 0e3997c331a5f91a4bbabee55b3e75688999980078145bb9473bb1ec93504526

### 新規

- {{T:ai-calibration-registration}} **P1・dev-wave 起票待ち**: rr80/rr20 の計算ノード certification、
  collector、成功 attempt の final receipt と registered artifact の確認を別 dev-wave で行う。rejected
  attempt は修正再利用せず、新しい allocation として扱う。rulings session から直接投入しない。
- {{T:rulings-improvement-candidates}} **P2・候補採用**: reasoning-pin の authority/admission 分割、
  detached mutation の実 detach、mutation cascade probe、Wave C 総括位置、clean-tree gate 順序、
  ListAgents 補助証拠の6候補を次の self-improvement wave で評価する。
