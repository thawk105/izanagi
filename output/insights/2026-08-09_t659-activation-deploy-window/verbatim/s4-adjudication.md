# 段 4 親裁定 — [T-659] activation 発行→配備の分裂窓

wave = `dev-wave-t659-activation-deploy-window` / 起点 main = `ee2da0bf` / 2026-08-09。
段 3 は 2 レンズとも **NO-GO** (A = sol / must-fix 8 + nit 1、B = luna / must-fix 9 + nit 1)。
本裁定は **`4→7→8→9`** を確定する — 実装差分ゼロ、変異 matrix 免除 (`DW-S04`)、受入全走は実施。

## 1. 所見の real / refuted

### real・採用 (親が一次資料で裏取りしたもの)

| 所見 | 親の裏取り | 処置 |
|---|---|---|
| A-1 issuer の source head 自己更新は「発行」を未 commit の「有効化」へ変える | runtime は Git を見ず working tree の record と定数の一致だけを見る (`env_contract.py:519-530`)。probe (B) が dirty tree での受理を実測済み | **親案 P1 を取り下げ**。R1 の選択肢から「issuer の source edit」を落とす |
| A-3 新 record は untracked | `git ls-files orchestrator/campaign/env_contract_activations/` = `00000001.json` の 1 件のみ。発行 tool は次 serial の**新しい filename** を create-only で作る | 窓の表に index / partial staging / stash 状態を追加。手順へ `git add` 対象の明示を要求 |
| A-4 一 commit 二 record を co-commit gate が受理し、未配備世代が ever-active になる | `env_contract_activation.py:394` が chain 中**全行**の hash を `ever_active` へ入れる。head pin は terminal record としか照合しない (:406-416) | gate 条件に「追加 record exactly 1 / head serial exactly +1」を追加 (1 record 内の複数 env 同時 +1 とは別問題) |
| A-6 / B-1 据置 env の activation lineage は durable receipt で識別不能 | `_validate_activation_transition` (:274-297) は「変化 env が 1 つ以上」だけを要求し据置を許す (D245)。durable receipt は `contract_sha256` のみ (`execution_guard.py:204-222`) | brief の成果物影響を訂正。並行 [T-657] がまさに linux-baremetal 据置・pegasus g1→g2 のため**今回そのものが該当例** |
| A-5 / B-6 deployment domain は列挙も fence もできない | `_repository_root()` (:465-483) は自 root の sentinel 確認だけで worktree を列挙しない。generic dispatch request に source commit がない | R0 を「実在する launcher / path の閉集合」へ縮める。全 process roster は入力不在 (`DW-O13`) で提案しない |
| A-7 probe は leaf validator の実測であって production fresh-process の実測ではない | probe は `_load_authority_snapshot()` を通さず leaf `load_activation_state()` へ expected 値を直接注入している。`UNEXPECTED` 分岐は非 0 終了しない | 親の主張を「leaf validator が split 両方向を拒否した」範囲へ縮める |
| A-2 P1-D の `trusted-main` は呼出し点で成立していない | `dev_wave_land.py` は自 `__file__` から code root を取り、runbook は相対 path しか固定していない。「checker 導入 commit」は実在 field でない | D を選ぶ場合の必須条件として明記 (caller も trusted-main へ束縛、適用開始を実在値で定義) |
| B-2 P3 の確定事実と未裁定を混在させている | 追補 2 が確定するのは「serial 2 は [T-657] の手動、[T-659] は serial ≥ 3 対象」まで。「serial ≥ 3 を許可しない」は**未裁定** | 総括の断定を撤回し R3 の問いに戻す |
| B-3 P1-D は runtime 受理集合を変えない大型 hardening | plan 自身が「runtime exact pin は変更しない」と記載。差分は checker 130-200 行 + land 改修 + テスト 160-240 行 | **推奨を D から B へ変更** (下記 §2) |
| B-4 手順型 quiesce に abort 条件と証跡がない | 既存受入 lease は campaign process / PBS job を排除しない (runbook §7.3)。issuer は window を受け取らない | 手順に「どこで止めるか」を書けることを R2 採用条件にする |
| B-5 SIGKILL 後の回復経路が未定義 | publish 後に SIGKILL されると record-only が残り、次回 issuer も head 不一致で発行できない | **回復手順は untracked 削除で足りる** (A-3 の実測より、未 commit の record は tracked でない)。runbook に 3 行で書ける — R2 の必須要素にする |
| B-7 設問が独立択一になっていない | R2-A 手順 5 が P1 gate を必須扱い、R3-A が P1/P2 land を前提にしている | 本パッケージで設問を組み直した (§3) |
| A-8 issuer の 2 つの repository root が束縛されていない | tool は `__file__` の parents[1]、書込み先は module の `_repository_root()`。exact 一致 assert なし | 実装弾での 2 行 assert として記録 (通常 CLI では一致するため優先度は低い) |

### 親が範囲を訂正したもの (partially refuted)

- **B-8 の byte 予算**: `docs/dev-wave/**` の予算は本件で**消費しない** — 置き場は `docs/pegasus-runbook.md` であり、`tools/check_docs.py` に runbook の byte 上限は存在しない (`PROVENANCE_REFERENCE_LIMITS` は provenance 2 文書のみ、現状 `check_docs: 違反なし`)。**節境界と重複配置の指摘だけが real** で、予算超過の懸念は当たらない。
- **A-9 / B-10 は nit**。fork child は snapshot を捨てて再 load するため「旧 cache のまま続走」は不正確 (説明精度の問題で受理集合は不変)。推奨根拠が静的推論であることは本パッケージ冒頭で明示する。

## 2. 親の方針転換 — P1 推奨を D から B へ

段 2 プランは P1-D (trusted-main の同一 commit land gate) を推奨した。**親はこれを採らない。**

- 判断基準は `DW-G05`。D が変えるのは **land 可能な Git 履歴の集合だけ**で、certified 選択・レポート・試行台帳のどの値も受理集合も変えない。runtime は split の両方向を既に fail-closed で拒否しており (probe A / C、leaf 検証で実測)、**D が防ぐのは「壊れた履歴が main に残る」ことであって、壊れた状態で成果物が出ることではない**。
- 費用は checker 130-200 行 + land 改修 + テスト 160-240 行 = 概算 300-500 行。研究最優先 (D205、「科学的妥当性に直接効かない堅牢化は見送り」) に照らして正当化できない。
- さらに A-2 が示すとおり、D を正しく作るには caller の trusted-main 束縛という**追加の設計問題**を開く。最小形ではない。
- したがって推奨は **B (runbook の手順 + 発行 tool の handoff 文の補強)**。ただし D は選択肢として残し、ユーザーが機械強制を望む場合の条件 (A-2 / A-4 の必須修正込み) を明記する。

## 3. scope 内 / scope 外

- **scope 内 (本 wave の成果物)**: 裁定パッケージ `package.md` と逐語一式。実装差分ゼロ。
- **scope 外 (実装弾へ)**: runbook 節の執筆、発行 tool の handoff 文、(D 採用時) checker と land 配線、A-8 の root assert。いずれも [T-657] land 後に別 wave で起票する。
- **本 wave では扱わない**: [T-658] (receipt の全書込み口配線、見送り済み)、全 process roster / fencing token (入力不在、別設計)、[T-660] (head=2 の検出力、並行 wave が担当)。

## 4. 変異事前登録

`DW-S04` の免除条項どおり **実装差分ゼロのため変異 matrix は免除**。受入全走は免除せず実施する。
