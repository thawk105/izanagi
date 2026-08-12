# 段 1 brief — [T-139] 第 1 波 (承認 manifest + 受領証層 + producer 本体)

wave `dev-wave-t139-manifest-w1` / branch `worktree-dev-wave-t139-manifest-w1` / 2026-08-10

## 0. 確定済みユーザー裁定 (一次資料で照合済み)

- §58 (2026-08-10「推奨通りで」) = Q-A 第三分岐を**認める** / Q-B 第 2 erratum を本 wave が
  同梱起草し承認まで pilot を機械停止 / Q-C `a13` 台帳は **land lock 直列化 main 台帳**の方向 /
  Q-D **2 波・同一 land** (受理仕様のみの先行凍結はしない) / Q-E は [T-700] (b) 規範下で L2 か台帳。
  控え = `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §58、台帳 = worklog 367。
  選択肢集合は archive `worklog-phase3-0810-361.md` 84〜105 行で照合した (逐語要約だけに依らない)。
- §47 R2 (a) = core §7 の較正義務へ**第 2 erratum を当て「事前固定 stress check」へ置換**する。
  R1 (a) = approval manifest + exact set / R6 (a) = schema は producer wave が発行し digest 固定。
- [T-700] (b) = 新規 L2 節の admission に routing 3 の 3 条件を課す (Q-E の受け皿)。

## 1. 不変条件 (破ったら停止)

1. **本 wave は local main へ land しない。** Q-D の「同一 land・受理仕様のみの先行凍結はしない」に
   対し、第 1 波は受領証 schema digest 固定を含み `submit_pilot` を含まない。単独 land は
   裁定が名指しで禁じた形そのもの。段 9 は branch 確定で終え、land は第 2 波が両波を合わせて行う。
2. **core の bytes を変えない。** 第 2 erratum も one-off replacement 記述であり core を編集しない。
3. **`submit_pilot` は実装しない。** pilot は本 wave 終了時点でも投入不可のままにする。
4. 絶対規律 3 — `verify_receipt` は pass/fail でなく構造化理由を返す。fail-closed を既定にする。
5. 承認済み blob の identity は manifest 側が権威。caller 引数・受領証自己申告を trust root にしない。

## 2. 実測した前提 (一次資料。D262 / erratum §3 の申告値と全件一致)

| 対象 | 実測値 |
|---|---|
| `F_e` (D262 を fold した commit) | `dce4ae4fed6f4fb33747165c5b92c16d01822850`、HEAD の祖先 ✓ |
| core blob at `F` (450 行) | `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9` ✓ |
| core §7 の較正義務行 (221 行目) | `225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89` |
| 同行の逐語 | `事前 simulation で較正する。\n` (直前 220 行が「…同じ許容 schedule 集合を使う」) |
| `事前 simulation で較正する` の出現 | **1 件** (221 行のみ)。`較正する` は 2 件 (221 / 333 = §14 の a12 行) |
| erratum-1 の locator | 404 / 424 行。**erratum-2 の 221 行と重ならない** ✓ |
| 既存実装 | `orchestrator/preregistration/` 881 行 (`erratum_id` 別 validator registry = D263、gate API 非 export = D264) |

**`DW-O09` pin 閉包 (record-items を書き換える可能性があるため実施):**
`1957026c…8fd3` を pin するのは `docs/decisions.md` の D262 payload **のみ**。`.py` の pin は
`test_t139_preregistration_binding.py` の core / erratum / addendum_a / composed 4 値だけで
record_items を含まない。`FROZEN_MANIFEST` (23 件) に T-139 事前登録族の key は無い。
→ 機械 pin の破壊は起きないが、**D262 は record-items を承認済み blob として digest 固定している**。

## 3. 親の provisional 裁定 (攻撃対象)

- **(P1) Q-A の record-items 修正は in-place でなく「再発行」で行う。** 承認済み blob を
  後から書き換えると D262 の pin と実体が乖離する。先例 = `addendum-a-reissue.md` (旧版を
  非承認として名指しし新 path へ再発行)。manifest は再発行版を pin し旧版を非承認と書く。
- **(P2) 第 2 erratum は core 221 行に対する 1 operation。** `erratum_id =
  t139-core-s7-stresscheck-v1`。固有検査は D263 の registry へ新 validator として足す
  (erratum-1 の「len==2 / a01〜a12 出現 2 件 / 差分 1 token」は erratum-1 固有であり流用しない)。
- **(P3) 本 wave では第 2 erratum を承認しない。** manifest の承認 erratum 集合は
  `{t139-core-s15-exactkey-v1}` の 1 要素のままとし、`composed_sha256` は D262 の
  `d1782b04…de82` を保つ。第 2 erratum は「起草済み・未承認」として pilot 停止 gate の根拠になる。
- **(P4) Q-C の台帳は main tracked な create-only 追記ファイル**とし、書き込みは
  `tools/dev_wave_land.py` が保持する協調 wave lock の内側だけに限る。fold と同じ直列化点に乗せる。
- **(P5) 受領証 schema は 1 枚の JSON blob として発行**し、digest を `PreregBinding` に固定する。
  record-items 再発行版が要件、schema blob が実装。両者の digest を manifest が持つ。

## 4. scope と成果物影響 (`DW-G05`)

| 単位 | 実装しないと成果物がどう変わるか |
|---|---|
| U1 承認 manifest (`F_e` の子孫、literal `approval_fold_commit`) | resolver の trust root が caller supplied のまま。未承認の追補 A′ が exact-13 を満たすだけで gate を通り、**適格 cluster 集合が偽造可能**になる |
| U2 record-items 再発行 (Q-A 第三分岐) | preflight で `a03` が落ちた正当な attempt が `post_performance_failure` を記録できず、**全 attempt 保存 (core §7) が破れる**か、marker 捏造を促す |
| U3 受領証 JSON Schema + digest 固定 | 2 実装が未知 field・null・参照整合性を違えても適合でき、**同じ受領証が validator A で適格・B で拒否**になる (適格 cluster 集合と certified 判定が実装で分岐) |
| U4 第 2 erratum 起草 + 未承認 pilot 停止 gate | core §7 の「較正する」義務が未達のまま `submit_pilot` へ進める。**保証していない型 I 誤り制御を保証したことになる** (規律 3) |
| U5 `a13` 原子予約台帳 | 同じ根に対し複数 study が `k=1` を主張でき、**全体誤り率が 0.0731 > 0.05** になる (α₁=0.025 が守られない) |
| U6 `resolve_effective_preregistration` / `PreregBinding` / `verify_receipt` | 受領証と承認済み三つ組の照合経路が無く、**pilot は永久に投入不可**のまま |

## 5. 規模の懸念 (親が段 2 で潰す前提の申告)

前 wave の段 3 レンズ B は残り全体を production 4,900〜6,000 行 + test 2,550〜3,200 行と見積もった。
本 wave は `submit_pilot`・PBS 測定・driver・collector を除くが、それでも U3 の完全 schema だけで
相当量になる。**段 2 のプランには単位別の行数見積りと、削れない最小集合を必ず出させる。**
1 wave に収まらないと段 3 が判定したら、Q-D の「同一 land」を保ったまま第 1 波をさらに分けるか
どうかは親が裁定せずユーザーへ返す (Q-D の再解釈にあたるため)。

## 6. 並列分割方針

段 5 は所有素集合で 3 系統 — (A) manifest + resolver + `PreregBinding` (`preregistration/` 配下)、
(B) 受領証 schema + `verify_receipt`、(C) `a13` 予約台帳 + land lock 配線。
docs (manifest fragment / record-items 再発行 / 第 2 erratum) は**親が単独で書く** (前 wave の
所有二重化 F16 の再発防止)。

## 7. 受入・実測環境

受入全走は計算ノード (`docs/pegasus-runbook.md` の dispatch recipe)。lease は
`IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease`。
本 wave は land しないが**受入全走は免除しない** (実 repo を読むテストを追加するため)。
