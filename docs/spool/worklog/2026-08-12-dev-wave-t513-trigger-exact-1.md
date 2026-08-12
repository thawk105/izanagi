---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t513-trigger-exact
seq: 1
title: trigger predicate の build admission を raw bytes exact にした — CRLF 迂回まで閉じ、binding 省略経路は裁定へ返す (コード + docs、変異 4/4 KILLED、branch worktree-dev-wave-t513-trigger-exact)
---

## 本文

ユーザー裁定「exact 比較へ ([T-515] と同時、影響実測つき)」に従って実装した。設計判断は
{{D:trigger-admission-exact-bytes}}。

**brief 前実測で裁定の素朴な読みが本番破壊になると判明した。** 正規の materializer
(`render_hole`) は骨格 hole 行のインデントを前置して書くため、materialized source の hole は
`"  " + emit_predicate(mask)` である。「hole が emitter 出力と一致すること」を素直に実装すると
正規経路が全拒否になる。期待値に骨格インデントを含める形へ具体化して段 4 で裁定した。
既存テストの fixture はインデント無しで hole を書いており実 materializer と乖離していたが、
旧 `.strip()` 比較が両方を救っていたため乖離が見えていなかった。

**敵対相談で real 5 件。** 採用 2・不採用 3。

- 採用: CRLF 迂回 — 共有 parser は text mode で開くため universal-newline 変換が `\r` を
  比較前に落とす。raw bytes 比較にしないと exact を名乗れない。
- 採用: 骨格 drift 検査の位置特定が非一意 — `+#if BACKOFF_TRIGGER_GATING` は patch 内に 11 箇所ある。
  EVOLVE-BLOCK の BEGIN/END が各 1 回であることを assert し、その閉区間内でだけ探す形へ直した。
- **不採用 (scope 外)**: exact 検査は `trigger_gate_binding` を渡した評価でしか発火しない。
  binding を省く 5 経路 (s8a sweep / S-1 direct comparison / S8b oracle / S8b floor /
  S-1 extime calibration) は検査に到達しない。閉じるには全 consumer への binding 結線か
  build gateway での必須化が要り、裁定が認可した受理集合変更の範囲を超える。
  新規項目として起票し、**成果物の主張を「binding を伴う lane」へ狭めた**。
- 棄却: mask=20 の実測は全 32 mask へ一般化できないのでは — 32 mask 全ての emitter 出力に改行が無く、
  最長 379 bytes であることを子が独立に確認して refuted。
- 棄却: fixture を実 materializer 由来にすると自己参照で緑のままになるのでは — 独立 literal の錨
  (骨格 patch の実バイト、`"  "` literal assert) があるため連動破損は捕捉される。nit として
  空白族 4 種 (`\v` `\f` NBSP 全角空白) の未検査は fix で閉じた。

**変異 4/4 KILLED、MISMATCH 0・SURVIVED 0。** 期待 node の完全集合が初回で一致した。
受理集合を縮める wave なので、承認外の過剰拒否を検出する正例 (インデント pin を 4 空白へ変える
positive control) も登録し、正例・drift・4 空白攻撃・crossed の 4 node で KILLED を確認した。

段 5 と段 6 の実装子はいずれも計算ノードの dispatch preflight (`qstat -Q` rc=1、runner rc=16) で
止まり、テストに到達できなかった。両者とも「実装済み・未実走」と正しく申告し、親が焦点走
(13 nodeid pass) と変異本走を実行した。

## 次の一手差分

### 完了

- [T-513] build admission の hole 比較を raw bytes exact へ狭め、CRLF / CR-only / 外周空白 /
  tab / 任意インデント / 空白族 4 種を閉じた。変異 4/4 KILLED。
  binding 省略経路は scope 外として別項へ分離した。
  remaining: none
  base: 520eecbb2b05b86034ca15426abbdb3541ff8d43a0a4948fd68307a0725f28fc

### 更新

- [T-515] **P3・影響実測済み・ユーザー再裁定待ち**: `diffq_variant_id` が raw implementation を
  hash するため、外周空白付きの綴りが別 reject variant として台帳に残りうる問題。
  **現行では到達不能**と実測した。trigger 軸で `quarantine` を呼ぶ本番 caller は 8 箇所あり
  (`p3_s4_loop_trigger_gating` 3、`p3_autonomous_workload_trial` 1、`s8a_trigger_sweep` 2、
  `s1_verify_extime_calibration` 1、`s1_direct_comparison` 1)、いずれも wire→`emit_predicate`、
  combination→`predicate_for`、freeze の `gate_predicate` を経て正準 bytes になる。
  自由文字列が `diffq_variant_id` へ届く経路は無い。到達可能になるのは、trigger quarantine の
  正準化を迂回する変更か、producer が自由文字列をそのまま `record_diff_reject` へ渡す変更のとき。
  択一: (a) 現行到達不能なので実装せず、正準化迂回を禁じる不変条件テストだけ置く /
  (b) `diffq_variant_id` を正準化後の値で hash する形へ変える (`load_diff_rejections` と
  critic 参照の consumer を持つため WAL の reject key 導出が変わる) / (c) 見送り。
  **親の推奨は (a)** — 実害が現存せず、(b) は既存 WAL キーの導出を変えて過去の台帳と
  非互換になる一方、守りたい性質は「正準化を迂回させない」ことに尽きるため。
  成果物影響: 直さない場合、将来 raw text producer を足したときに同一の正準述語が
  複数の reject variant として試行台帳に残り、critic の rejection 参照が重複する。
  base: eaff1debd0bfbd5e4d6ed67d137915a97b6b07734699af90061dfbc088fdd33d

### 新規

- {{T:trigger-admission-binding-optional}} **P2・新規・ユーザー裁定待ち
  ([T-513] 段 3 レンズ A の scope 外 real)**: materialized trigger predicate の exact admission は
  `trigger_gate_binding` を渡した評価でしか発火しない。binding を省略する 5 経路
  (s8a trigger sweep / S-1 direct comparison / S8b oracle / S8b floor / S-1 extime calibration) は
  この検査に一度も到達せず、build へ進む。現行の producer はいずれも quarantine 内で述語を
  正準化してから書くため既存の走行が汚染されている所見ではないが、「既 materialize 済みの
  source 木を直接渡す」という脅威モデルに対しては binding 省略がそのまま迂回路になる。
  択一: (a) 5 経路すべてへ expected mask/binding を結線する /
  (b) build gateway 側で trigger axis (`BACKOFF_TRIGGER_GATING`) を検出して semantic admission を
  必須化する (floor/calibration の直接 build には共有 validator が要る) /
  (c) 結線せず、成果物の主張を「binding を伴う lane のみ」に狭めたまま運用する。
  **親の推奨は (b)** — (a) は 5 経路それぞれに同じ結線を重複させ、6 個目の経路が足されたときに
  また漏れる。(b) は「trigger 軸を使う build は必ず semantic admission を通る」という
  単一の不変条件になる。ただし (b) は新規の受理要件であり、裁定が認可した範囲を超えるため
  ユーザー裁定を要する。
  成果物影響: (c) のままなら、外周空白・tab・CRLF を保持した source が別 consumer から
  build・verify を経て certified 判定・レポート・session ledger・oracle/floor manifest へ到達しうる。
