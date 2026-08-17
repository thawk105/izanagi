# 段 1 brief — pegasus 第 2 世代の活性化を現行 main で立て直す

wave: `dev-wave-t657-activation-rebuild` / 2026-08-17 / branch `worktree-dev-wave-t657-activation-rebuild`

## 由来と確定済みユーザー裁定

- **2026-08-17 ユーザー指示**: 旧 branch `worktree-dev-wave-t657-t660-g2-activation`
  (未着地 11 commit) を**破棄**し、現行 main の `reseal_protocol()` で**立て直す**。
- 2026-08-12 `{{D:freeze-verification-hold}}` — 凍結チェーン同一性検証 21 件を保留。
- 2026-08-16 **D444** — 床値 protocol の束縛の張り替えだけを AI へ開放。
  create-only の versioned namespace `output/s8b-freeze/floor-protocols/<contract>--<pin>.json`。

旧 wave (2026-08-09) の裁定パッケージ 3 択 (A/B/C) は上記 2 裁定により失効した。
本 wave は「B 案 = 検査を弱める」を**採らない**。D444 の追加のみ方式で衝突面そのものを回避する。

## 実測済み前提 (本段で取得。一次資料 = 判定器 library と index scan、docs ではない)

1. `GENERATIONS`: `linux-baremetal [1]`, `pegasus [1, 2]`。activation head = serial 1、
   pegasus は g1 が active (`lookup("pegasus") = e576e9cd…`)。
2. `_is_valid_activation_successor(pegasus g1, g2)` = **True**。
3. 較正 3 面 (`_validated_activation_successor_method`) = **緑**。
   method = `proc-cpuinfo-rotating-min/k5/interval-ns50000000/sysfs-affinity-intersection-evenly-spaced-v1`。
4. 登録済み較正 artifact は両世代分 (`calibration-753f535a8d024727.json`,
   `calibration-94a4b79fa31bba3c.json`) が実在。
5. anchor `output/s8b-freeze/floor_protocol.json`: `env_tag=pegasus`,
   `contract_sha256=e576e9cd…`, `ccbench_pin=d706650c…`。floor protocol index は 1 件。
6. 現行 ccbench gitlink = `511c9538…` (anchor の pin と**異なる**)。
7. g2 活性化後の reseal target pair = (`1346c20b…`, `511c9538…`)。**未発行**。
   導出 path = `output/s8b-freeze/floor-protocols/1346c20b…--511c9538….json`。
8. 旧 branch の `00000002.json` は今日の main でも整合する
   (predecessor state sha = main head の `activation_state_sha256`、linux-baremetal 行も一致)。

## scope と成果物影響 (DW-G05)

- **S1. activation record `00000002.json` を発行し head を 1 → 2 へ進める。**
  実装しない場合 → `lookup("pegasus")` は g1 のまま。g2 契約での床値 live admission が拒否され続け、
  certified 選択の受理集合が開かない。
- **S2. `reseal_protocol()` で versioned floor protocol を create-only 発行する。**
  実装しない場合 → g2 契約に対応する床値 protocol が存在せず、床値 campaign が起動できない
  (現行 anchor は g1 契約かつ旧 pin に束縛)。
- **S3. head=1 / g1-active を前提にしていた既存テストの追従。**
  実装しない場合 → 受入全走が赤になり land 不能。成果物の値は変わらないが着地しない。
- **S4. 旧 branch の破棄 (ref 削除)。** worktree 残骸は無いことを確認済み。
  実装しない場合 → 未着地 branch が残り、以後の棚卸しで毎回「実体のある残作業」として再浮上する。

## 不変条件 (緩めない)

- 既存凍結 bytes を 1 件も書き換えない。**追加のみ。** `floor_protocol.json` は anchor として不変。
- 履歴不変条件の検査 (`_immutable_introductions`) を**弱めない**。旧 wave の B 案は採らない。
- 正しさゲートと規律 1〜3 は不変。activation の較正 3 面検査も弱めない。
- 発行順序は不可逆: **activation 先 → reseal 後**。`reseal_protocol()` は `lookup()` 経由で
  active 契約を読むため、逆順では g1 の組が発行され、しかも create-only なので取り消せない。

## 攻撃対象の provisional 裁定 (親の暫定、段 3 の攻撃対象)

- **(P1)** scope は head 1 → 2 ちょうど。worklog [T-1289] の「第 4 世代へ来た」は
  env contract の世代ではないと判断した (pegasus は 2 世代しか宣言されていない)。
- **(P2)** 旧 branch の実装 (テスト追従 8 file) は**参考に留め**、現行 main 上で作り直す。
  8 日で main が動いており、blob 流用は stale な期待値を持ち込む。
- **(P3)** 本 wave は受理集合を変えるため `DW-C00` の軽量版に該当しない。
  段 2・3 と段 6 の敵対子を省かない。
- **(P4)** テスト追従の全容は**未測**。親は凍結境界により実装面を編集できず、
  DW-S01 の「実編集 + 即時復元」による fallout 計測を行っていない。
  代替として判定器 library で受理性だけを実測した (模擬ではなく本物の判定器)。
  fallout の全容測定は段 5 実装子が行う。

## 成果物の形

- 追加 (2 file): `orchestrator/campaign/env_contract_activations/00000002.json`,
  `output/s8b-freeze/floor-protocols/1346c20b…--511c9538….json`
- 変更: head=1 / g1-active を前提にする既存テスト
- 記録: `docs/spool/` の worklog fragment、旧 branch 破棄の記録

## 分割方針

実装面は S1 → S2 が順序依存の単一連鎖のため、段 5 の実装子は **1 本**。
段 3 の敵対相談と段 6 のレビューは **2 本並列** (異なるレンズ)。
