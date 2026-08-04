---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t433-p6-contract
seq: 1
title: [T-433] P6 意味的充足契約の案を起草し裁定パッケージで返した — 敵対 2 レンズの 18 所見を全採用し認定要件を admission 結線まで拡張、V1 は申請単位 (a′) を推奨 (docs のみ、branch worktree-dev-wave-t433-p6-contract)
---

## 本文

- **依頼はユーザー command 引数 `/dev-wave [T-433]` (背景 job)。** 裁定 = (175) の V2 項。
  設計択一が割れるため軽量版でも段 2・3 は省かず、codex read-only 3 本 (プラン起草 1 +
  敵対レンズ 2、いずれも gpt-5.6-sol / reasoning=max)。段 4 で「実装しない」(裁定文言
  「設計と裁定パッケージまで」のとおり) を裁定し遷移は `4→7→8→9`。実装差分が無いため
  変異事前登録・変異 matrix・受入全走は対象外。
- **両レンズ NO-GO (A: B5+M2+m1、B: B4+M5+m1)、計 18 所見を全件 real・全件採用、refuted 0。**
  中心所見は両レンズの独立再現 (A#1 ≡ B#1): 期待される集合値を返すだけで候補 admission に
  一度も作用しない実装が、段 2 案の calibration・全変異・独立再計算をすべて通過できる —
  D138 決定 (1) の「限界効果ゼロ」が認定手続そのものに再発した形。契約案 v2 は end-to-end の
  admission A/B 対 (P6 有効時に禁止候補が generalized cut を唯一の理由に reject され、無効時に
  通る) を中心条項に据えた。設計判断は {{D:p6-sufficiency-contract}}、逐語と契約案本文 =
  `output/insights/2026-08-04_t433-p6-sufficiency-contract/`
- **裁定パッケージ 4 件をユーザーへ返す** (s4-adjudication §4): U1 契約案の採否 (推奨 = 採用)、
  U2 V1 の射程 = 量化を明示した (a′) 「判定は cap-lift 申請単位・run 単位は receipt との
  conformance、standing な global 免責にしない」を推奨 (3 択は run の量化が未定義でそのままでは
  判定可能でないという両レンズ一致の所見を前提に置く)、U3 adapter 正例要件 = (b) 推奨、
  U4 calibration 新鮮性 = (b) 推奨。親 provisional のうち (P2) V1 の定式化と (P3) 恒真条項の
  排除規則は段 4 で訂正 (コア条項は削除でなく認定不可の fail-closed)。
- 契約採用時に変わるのは cap-lift の**規範上の**受理集合だけで、本 wave では certified 選択・
  レポート・台帳の値・機械受理集合・参照はいずれも不変 (実装差分ゼロ)。承認上限 1 (D114) 不変。

## 次の一手差分

### 更新

- [T-433] **P1・裁定パッケージ返却済み → ユーザー裁定待ち (U1〜U4)**: 意味的充足契約の案
  (認定対象・入力実在台帳・必須条項 SC-01〜SC-12・正負 calibration C-01〜C-13・偽物棄却集合・
  変異排除規則・独立検査者 attestation・認定記録と失効照合・発火イベント) を
  `output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md` に起草した。
  V1 (`NOT_CLAIMED` の射程) の裁定案 = 精密化 (a′) も同 README §9 で返却済み。
  裁定は U1 契約案の採否 / U2 V1 / U3 adapter 正例要件 / U4 calibration 新鮮性の 4 件
  (s4-adjudication §4)。採用時は新 D として記録し cap-lift の規範上の受理集合が狭まる。
  機械実装は将来の P6 実装 wave と cap-lift receipt 設計 (V3) の所有
  base: 8958749fec333c8bb8c670a8c470f740ba3f0b56dbe730a5b892772886de7ac0

### 新規

- {{T:run-tests-queue-wait-passthrough}} **P3・新規**: `tools/run_tests.py` の Pegasus dispatch が
  queue 待ち timeout を `dispatch_compute.DEFAULT_QUEUE_WAIT_TIMEOUT_S` (900 秒) 固定で渡しており、
  gen_S 混雑時に受入テストが infrastructure failure (queue-wait-timeout) で落ちる (2026-08-04 の
  本 wave で実測。回避は dispatch_compute.py 直接投入)。timeout の指定経路 (CLI flag または環境変数)
  を追加する。実装面なので Codex author の軽量 wave
