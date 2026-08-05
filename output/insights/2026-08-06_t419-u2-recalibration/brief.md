# 段 1 brief — [T-419] U-2 較正の再取得

branch `worktree-dev-wave-t419-u2-recalibration`、起点 main `cfda4abe`。
前提実測 6 件は handoff `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t419-u2-recalibration.md` に記録。

## 確定済みユーザー裁定 (この wave の入力)

- 着手条件 (i) = 方式 α の本番結線は D181 / worklog (240) で成立済み。
- 本 wave の所有 = accepted publish receipt・独立 self-comparison・例外集合の空化・凍結 bytes と pin の更新。
- 同梱裁定: [T-443] (CMake argv へ verified cache projection、単独実施せず本サイクルへ同梱)、
  [T-444] (取得経路の proof chain 束縛 = acquisition receipt、同サイクル同梱)、
  [T-506] (loader への canonical 述語 self-pass を新較正の登録と同時に課す)、
  [T-531]/[T-533]/[T-534] ([T-478] A′ 世代移行への統合、U-2 チェーン所有)。

## brief 前実測が覆した前提 (段 4 で再裁定する)

**登録 (pin 更新・例外集合空化) は D176 の bootstrap fuse が機械拒否する。**
`env_contract.validate_generations` は各 env の世代列長が 1 でなければ `EnvContractError` を送出し、
D176 は「活性化権限 (activation record / activation receipt) が実装されるまで 2 世代目の登録を
fail-closed で拒否する」と明記する。その活性化権限 = **[T-529] は P1・新規・未裁定**。
g1 の `calibration_ref` を上書きする迂回は D176 の眼目 (正規 publish を通らない較正の活性化を防ぐ) を
壊すため採らない (規律 2)。よって登録は本 wave では実装せず、択一を裁定パッケージで返す。

## scope (P = 親の provisional 裁定。攻撃対象)

- **(P1) 本 wave = 取得サイクルまで。** 実装 = 取得経路の自己整合 gate + 計算ノード生死 driver。
  計測 = certify job 1 本。登録・pin 更新・例外集合空化・loader self-pass は次 wave (T-529 依存)。
- **(P2) [T-443]/[T-444] は本 wave に同梱する。** ただし [T-443] は「certify が過去に成功していた
  機序の検証」を先に行い、certify の build が外部 network に依存しないと実測できたら
  campaign argv への projection 追加は次サイクルへ送る (campaign 再走は本 wave の scope 外)。
- **(P3) [T-506] は取得側半分だけ入れる。** loader 側 self-pass を今入れると現行 g1 較正
  (自己不整合) が読めなくなり、承認外の受理縮小になる。裁定文も「新較正の登録と同時」である。
- **(P4) 生死実験を certify より先に置く (DW-G01)。** 計算ノードで `ea.probe()` を 1 回走らせ、
  tolerance 2% 帯内 (帯外 0 件) を確認してから 2 時間の certify を投入する。
  login node では帯外 1/96 だった (共有負荷)。計算ノード専有での帯内化は未実証。

## 不変条件

- 受理述語 (全位置が帯内)・`tolerance_pct = 2.0`・`effective_clock` の schema key 集合を変えない。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS == 1`、`EXPECTED_GENERATION_HASHES`、`contract_sha256`、
  `FROZEN_MANIFEST` (23 件) を本 wave では動かさない。
- D176 の fuse を緩めない。既存 test の削除・緩和をしない。
- 取得側 gate は「publish される新 artifact」にだけ効かせ、既存 artifact の読み取り経路を狭めない。

## 既存被覆と純増検出力 (性質で検索した結果)

`_acquisition_reasons` (`orchestrator/calibrator/cli.py:400`) は job-id / host / node 数 / binary hash /
walltime / known-values しか見ず、**effective_clock の自己整合を一切見ない**。
test 層の `_registry_clock_self_passes` (`test_env_contract.py:834`) は registry 経由の
既登録較正にだけ効き、取得時には発火しない。
純増 = 「自分の median に対して自分の samples が帯を外れる較正を accepted として publish できる」
穴を production gate で閉じること。実在の反例が `calibration-753f535a8d024727.json` (CPU 40 = 3080.935)。

## 成果物影響 (DW-G05)

- 取得側 gate を入れない場合: 2 時間の certify が再び自己不整合な較正を accepted で publish しうる。
  その較正を登録すれば `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は空にならず、
  certified 選択・材料レポート・試行台帳は閉鎖のまま (現在も閉鎖) だが、
  再取得サイクルが 1 周まるごと無駄になる。
- 生死 driver を置かない場合: 帯外が残る環境で 2 時間 × 共有 queue を空費する。
- 登録を本 wave で行わない影響: certified 受理集合は**閉鎖のまま変わらない** (現状と同じ)。
  live probe と g1 較正は `effective_clock.method` で必ず不一致になるため campaign は開かない。

## 成果物の形

新 artifact = `output/env/pegasus/calibration/registered/calibration-<digest16>.json` と
attempts 配下の receipt 群 (取得が帯内なら)、取得側 gate のコードとテスト、変異台帳、
逐語 `output/insights/2026-08-06_t419-u2-recalibration/`、裁定パッケージ (登録経路の択一)。

## 分割方針

段 2 = codex read-only プラン 1 本 (file:line 粒度)。段 3 = 敵対 2 レンズ
(A: 正しさ境界と恒真化、B: 射程・pin 閉包・運用整合)。段 5 = 実装子 1 本
(gate + 生死 driver は同一面のため分割しない)。段 6 = 敵対レビュー 2 本 + fix。
計測 (生死 driver / certify job 投入 / 受入全走) は親が行う。
