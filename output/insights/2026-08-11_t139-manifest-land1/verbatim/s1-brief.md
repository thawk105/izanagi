# 段 1 brief — [T-139] 第 2 波 (2 段 land: 文書承認 → manifest + producer + pilot)

wave `dev-wave-t139-manifest-w2` / branch `worktree-dev-wave-t139-manifest-w2` /
base = 第 1 波 tip `9c630e53` + local main `3a03d920` の merge (`4f9cbca4`) / 2026-08-10

## 0. 確定済みユーザー裁定 (一次資料で照合済み)

fragment seq 42 (branch `worktree-rulings-20260806-a`、未 land) と一次控え §71
(`rulings-inbox/2026-08-04-rulings-session-5rulings.md`) の両方を読み、逐語一致を確認した。

- **R1 = (a) 2 段 land。** land 1 = 新 blob 承認 decision + 再発行 record-items + schema blob +
  第 2 erratum の**文書承認 fold のみ。コード・gate を一切含めない。**
  land 2 = manifest (land 1 の fold commit `F_r` を literal 参照) + producer 本体 + pilot 投入・測定を同一 land。
- **R2 = (a)** 第三分岐の残余捏造余地は非保証として明記して引き受ける。
- **R3 = (a)** `a13` 予約台帳は append-only 全履歴検査を課し、運用境界を manifest / report / resolver で
  同一 wording に固定して採る。
- **R4** 名指しされた未実装層 (submit_pilot + durable intent / PBS preflight・driver・collector /
  receipt writer / iteration 毎 correctness verifier / certified consumer) は第 2 波 scope。
- **R5 = (a)** `verify_receipt` 同名衝突は T-139 側を `verify_prereg_receipt` へ改名。
- pilot = 追補 A `a09` の schedule seed と `a01` の時間予算どおり **8 本 + 予備 2 (非合算)**。
  第 2 erratum の起草承認までの機械停止 gate を尊重。測定は単独性確認 + `a03` 静穏 preflight。

## 1. 実測した前提 (親が一次資料から独立に算出。既存 docs を根拠にしない)

| 対象 | 実測値 |
|---|---|
| `F_e` (D262 の fold commit) | `dce4ae4fed6f4fb33747165c5b92c16d01822850`、HEAD の祖先 (rc=0) |
| 凍結 core (450 行) | `ac939af4…d60e9` (D262 申告と一致) |
| core §7 221 行 | `225268a9…8e89`、逐語 `事前 simulation で較正する。` 出現ちょうど 1 件 |
| composed (erratum-1 のみ) | `d1782b04…de82` (D262 申告と一致) |
| **composed (erratum-1 + erratum-2)** | **`dfb821a5ff0b085f7092bbd5536772a8c6728ec946291a6e6eb61da9fbef678c`**、適用順に不変 |
| 現行 record-items (承認済み) | `1957026c…8fd3` (D262 が pin) |
| 草案 record-items 再発行版 | `5f07e917…3d54` (未承認、299 行) |
| 草案 第 2 erratum | `9eb96f88…885c` (未承認、166 行) |
| `DW-O09` pin 閉包 | `record_items` を pin する `.py` は **0 件**。pin は `docs/decisions.md` D262 のみ。
  `FROZEN_MANIFEST` に T-139 事前登録族の key なし |
| pilot 1 割当ての予算 (`a01` A) | 非余裕小計 2400 / internal deadline 3300 / 要求 walltime 3600 (36 run × 15 秒) |
| pilot 規模 (`a10`) | 検証割当て 1 + 適格 pilot 8 + 予備 2 (非合算)。**計算ノード実測 9 割当て以上が前提** |

新事実による裁定の覆りは無い。local main 側の T-139 項は (382) からの持ち越しで、seq 42 が最新。
並走中の `dev-wave-t139-publication-core` は新 core 起草で現 core を 1 byte も変えず、本 wave と非競合。

## 2. 不変条件 (破ったら停止)

1. **land 1 に実装面を 1 行も含めない** (R1 の literal 要件)。第 1 波のコードは land 2 側で land する。
2. **凍結 core の bytes を変えない。** erratum は one-off replacement 記述であり core を編集しない。
3. 承認済み blob の identity は**台帳 → manifest** が権威。caller 引数・受領証の自己申告を trust root にしない。
4. 規律 3 — `verify_prereg_receipt` は pass/fail でなく構造化理由を返し fail-closed を既定にする。
   correctness verifier は iteration 毎に回す (後付けゲートにしない)。
5. 追補 A の値 (schedule seed、時間予算、`a03` 許容範囲、8 + 予備 2 非合算) を 1 文字も変えない。
6. D264 の 4 名前非 export は、実際に gate を実装して正例を通す時点までは維持する。
7. 測定は単独性確認 + `a03` 静穏 preflight を経た値のみ採用する。

## 3. 親の provisional 裁定 (攻撃対象)

- **(P1) land 1 は local main から切った docs-only の専用 branch で行う。** wave branch の tip は
  第 1 波のコードを含むため、tip を land すると R1 の「コード・gate を一切含めない」に反する。
- **(P2) 受領証 schema は 1 枚の JSON Schema blob** (draft 2020-12) として発行し、record-items 再発行版と
  exact key で 1:1 対応させる。`PreregBinding` への digest 束縛は land 2 (land 1 では読む実装を置かない)。
- **(P3) 承認 payload は D262 を置換せず前向きに supersede する。** `record_items` の承認先を再発行版へ移し、
  旧 `1957026c…8fd3` を非承認と名指しする。`target_core` / `addendum_a` / `derivation_map` / erratum-1 は不変。
  `erratum_application_order = [t139-core-s15-exactkey-v1, t139-core-s7-stresscheck-v1]`、
  `composed_sha256 = dfb821a5…678c`。
- **(P4) `b03` 公表台帳は本 wave の scope 外。** 追補 B は段階 1 に留め置かれ公表 core は別 wave が起草中で、
  記録要件が未凍結。`a13` primary 台帳のみ実装する (R3 (a))。
- **(P5) R4 の全層 + pilot 測定が 1 wave に収まるかは未確定。** 前 wave の独立見積りは production
  4,900〜6,000 行 + test 2,550〜3,200 行、pilot は 9 割当て以上の PBS 実測を要する。
  **段 2 は単位別行数と「pilot 1 本を投げるための最小集合」を必ず出す。**段 3 が 1 wave 不可と判定したら、
  land 2 の分割は R1 の「同一 land」の再解釈にあたるため親が裁定せずユーザーへ返す。
- **(P6) pilot の 8 slot は `a09` の決定論的導出に従い、置換 attempt は同一 schedule を使う。**
  並列投入の可否と単独性確認の作法は段 2 で runbook から確定する。

## 4. scope と成果物影響 (`DW-G05`)

| 単位 | 実装しないと成果物がどう変わるか |
|---|---|
| **A1** record-items 再発行版の承認 | preflight で `a03` が落ちた正当な attempt が記録できず、core §7 の全 attempt 保存が破れる |
| **A2** 受領証 schema blob の承認 | 2 実装が未知 field・null・参照整合性を違えても適合し、同じ受領証が validator A で適格・B で拒否になる |
| **A3** 第 2 erratum の承認 | core §7 の較正義務が未達のまま、保証していない型 I 誤り制御を保証したことになる |
| **A4** 承認 decision (`F_r`) | manifest が pin できる trust root が生まれず、**land 2 が構造的に着手不能**のまま |
| **B1** 承認 manifest | resolver の trust root が caller supplied のままで、適格 cluster 集合が偽造可能 |
| **B2** resolver / binding / `verify_prereg_receipt` | 受領証と承認三つ組の照合経路が無く pilot は永久に投入不可 |
| **B3** `a13` 予約台帳 | 同じ根に複数 study が `k=1` を主張でき全体誤り率 0.0731 > 0.05 |
| **B4** submit_pilot・PBS・driver・collector・receipt writer・correctness verifier・consumer | gate が `accepted` を返しても certified 選択・レポート・試行台帳の値が 1 つも変わらない |
| **B5** pilot 8 本の実測 | `J` が導出できず本走が起動できない (`d⁻` gate も評価不能) |

## 5. 並列分割方針

- docs (A1〜A4、裁定パッケージ) は**親が単独で書く** (所有二重化の再発防止)。
- 段 5 の実装は所有素集合で最大 4 系統 — (I) manifest + resolver + `PreregBinding`、
  (II) 受領証 writer + `verify_prereg_receipt`、(III) `a13` 台帳 + land lock 配線、
  (IV) submit_pilot + durable intent + PBS driver + collector。correctness verifier 配線と
  certified consumer は (I)〜(IV) の確定後に段 4 で割り当てる。
- 段 3 の敵対レンズは **land 1 の 3 文書 (凍結される) を最重要の攻撃面**とする。

## 6. 受入・実測環境

受入全走は計算ノード (`docs/pegasus-runbook.md` の dispatch recipe、`--force-dispatch` を argv に入れる)。
lease = `IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease`。
**land 1 / land 2 でそれぞれ受入全走と lease 取得を行う** (2 回)。pilot 測定は別 job (PBS 割当て)。
