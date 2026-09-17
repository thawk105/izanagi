---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2724-freeze-g1-gen
seq: 1
title: [T-2724] 凍結 v2 g1 の世代導入 commit G を Codex author が作り X1' の子として wave branch へ merge したが、X1' を含む木では受入の非 held test 45 node が赤になり oracle gate も閉じると実測して land せず正式停止した (docs + 凍結記録、branch worktree-dev-wave-t2724-freeze-g1-gen、G は branch freeze-g1-gen-t2724、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2724] (D2120 項 2 (b)、ユーザー裁定 2026-09-17) 凍結 v2 g1 の世代導入 commit G を Codex author (D95) が作る — 非 merge・親 == X1' (`cc82edc8c`、`frozen_at_head`)・`AI-Agent` trailer 付き。着手直前の local main から fresh worktree を作り、G は新 branch `freeze-g1-gen-t2724` として X1' の上に置き、wave branch へ merge して land する (`_immutable_introductions` が成立する形、D2098 理由節)。承認 A と active pointer X (逐語 `AI-Agent: none` の人間 commit、X^ == A) は本 wave に含めず、ユーザーが打つ commit の手順を insight に 1 節で残す。T-750 の P-1 / P-3 は別管理のまま触らない。[T-2724] (a)(d)(e) の wave と並行可 (branch 名を分ける)。規律 2 を緩めない。本題の G 作成だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **G は作った (依頼の本題は完了)。land はしていない (正式停止)。** 一次資料は `output/insights/2026-09-18/t2724-freeze-g1-gen/README.md`、裁定パッケージは同 `package.md`。G = `32ba8cae45001697f050bee377413153e6d798a5` (branch `freeze-g1-gen-t2724`、親 X1' `cc82edc8c` ちょうど 1、`output/s8b-freeze/holdout_freeze.v2.g1.json` 1 file の追加、bytes は候補 X2 `4d8fb93b7` の blob `15861416…` / sha256 `7e1114…` / 20,737 bytes と同一、trailer は Codex author (`gpt-6-astra` / `medium`) + Claude manager)。wave branch の merge commit `88d020466` (親 = base main `d2ebef7a4` + G)。批准側の構造検査 (`_immutable_introductions` 一意 / `_assert_candidate_commit`) と内容検査 (V1a〜V1d / floor 投影 / V2 / V3 層 1) を wave 木 H で個別関数の probe として実測し全項目 ok (診断であって批准成功ではない)、production 入口は `no-active` (A / X 待ち)。三軸走査は世代文書を除外内で非 hit。
- **新事実 (D2120 項 2 (a)(d) の裁定時に未見):** X1' (official 床値 result の run_dir) を含む木で焦点走 6 file を計算ノードで実走すると **45 failed / 967 passed / 11 skipped** (`test_s8b_oracle_driver.py` 40 + `test_s8b_floor_campaign.py` 5、いずれも growth hold 外)。原因は 4 経路すべて run_dir 3 file の三軸 hit: T-080 fixture の実 root output 複製 + draft live scan (10)、実 committed HEAD の clone + official clean scan (5)、driver `run_block(root=ROOT)` の T-080 receipt 解決 (memo 共有) が `state=invalid` で `_campaign_t080_value` が拒否し `status: refused` で戻る (29)、公開 gate の v1 verify 混入 (1)。確認した走査 refusal はすべて X1' 由来 (G の世代文書は除外内、対照走なし)。production でも runbook §2 P3 `gate-check` が rc=2 で `holdout-freeze-verify: [holdout.unknownness_layer2]` を含む refusals 4 件 (前 wave は `floor-null` / `budget-null` の 2 件 exact) となり、`_make_gate_decision` が receipt の refusal を無条件 merge し `run_block` が `_campaign_t080_value` で invalid receipt を拒否するため **A / X を作っても X1' を含む checkout では oracle は refuse される** (v2 `launch_validate` は closure hit を期待集合にするが T-080 の live scan は zero-hit を要求し矛盾)。前 wave の insight §8 / package (d) は held 2 本を記録したが非 held と production への波及を列挙していなかった (F862 の再発として failures 台帳へ記録、memory `chain-consequence-enumerate-real-root-consumers` を作成)。
- 親の処置: test・hold・走査除外・批准側を 1 byte も変えず (規律 2)、受入全走を投入せず (赤が確定、赤の受領証は取らない)、G と merge を branch に保全して正式停止。裁定パッケージの択: (A) T-080 receipt live scan と v2 closure の整合を production 側で先に設計・裁定・実装 (A-1 承認済み世代の artifact から occurrence 検証で期待集合を導出 / A-2 active v2 なら receipt 不要 (置換範囲の定義が要る) / A-3 receipt の静的検証と epoch 束縛は維持し未知性層 2 だけ full launch validation へ委譲) してから chain + G を載せる (親の推奨)、(B) test 側だけ直す (oracle は動かないまま)、(C) 45 node を hold (弱体化)、(D) (a) 撤回 (X1' を含む checkout なら branch を問わず同じ)。並行 wave (a) `worktree-dev-wave-t2724-freeze-g1-chain-land` (tip `b227d0d91`、未 land) の session へ同じ事実を data として 1 回送った (07:26 JST)。
- 段 2 plan は親 brief を 5 点補正 (既存 G worktree の再利用、焦点走は `tools/run_tests.py` 経由、批准側の G 検査は `none` 混在を必ず拒否せず provenance checker と併用、X2 が入ると走査 hit は holdout ごと 4 path、親 trailer は manager / integrator)。段 3 レンズ A (正しさ境界) must-fix 0 / should 3、レンズ B (整合・実効性) must-fix 3 (B-1 並行 wave と旧 main から独立 merge → land の merge-base 2 つで rc=23、B-2 非 held の赤、B-3 fragment base は先発 fold 後 main の現物)、全採用。B-1 / B-3 は本 wave が land しないため未発火だが、再開時の手順として insight §6 に残した。段 6 レビュー A (正しさ) must-fix 3 / should 2 (45 本の内訳と (iii) の停止箇所、択 A-1 / A-2 の gate 緩和リスクと裁定順序、G 無影響の断定、probe の性質)、レビュー B (記録) must-fix 3 / should 3 (内訳、新規 F は F862 の再発、§5 検証 script の掲載、着手条件、前 wave の引用、memory の所在)、すべて採用して docs を訂正 (insight §9)。
- 実走: worktree 開始 gate / midflight gate rc=0、author 自己検証、provenance preflight 3 回 + range 監査 1 回 (request 4992.nqsv)、probe、三軸走査 (wave 木 rc=1 / insight + fragment のみ hit 0)、焦点走 (request 5001.nqsv、422.9 秒)、T-080 receipt 解決 probe (login、407 秒)、P3 gate-check (login、log 末尾 07:25 JST)、`check_docs.py` rc=0、`spool_fold.py --dry-run` rc=0。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra` / `medium`)。親の実測は上記。

## 次の一手差分

### carry

- [T-750]

### 更新

- [T-2724] **P1・G 済み → 裁定待ち (chain + G の land 可否、T-080 receipt live scan と v2 closure の整合) → A / X の人間手番**: 世代導入 G `32ba8cae4` (branch `freeze-g1-gen-t2724`、親 X1' `cc82edc8c`、候補 bytes と同一) は作成済みで wave branch `worktree-dev-wave-t2724-freeze-g1-gen` (merge `88d020466`) に保全、未 land。X1' を含む木では受入の非 held 45 node が赤になり oracle gate (P3) も `holdout.unknownness_layer2` で閉じる (T-080 receipt の live scan と v2 closure の矛盾、A / X では解消しない) ため、`output/insights/2026-09-18/t2724-freeze-g1-gen/package.md` の裁定 (推奨 A = production 側の整合を先に設計・裁定・実装、{{T:t080-receipt-live-scan-vs-v2-closure}}) を待つ。裁定後: 並行 wave (a) の land / fold 完了を確認し、後発側は先発 fold 後の main を固定 SHA で merge して再受入 (merge-base 2 つの rc=23 回避)、A / X はユーザーが README §5 の手順で commit。(d) の帰結記録には held 2 本 (`test_s8b_holdout_freeze.py` の verify CLI 2 node) と非 held 45 node を足す。T-750 P-1 / P-3 は別管理。
  base: 0e9776de69cc561e014b042bc484d76a6f318f3d12c66fee2e3dd86b59bdbeaa

### 新規

- {{T:t080-receipt-live-scan-vs-v2-closure}} **P1・ユーザー裁定待ち → (択 A 系採択後) 設計案の起草 (AI) → 候補の裁定 → Codex author 実装**: T-080 (v1 移行 receipt) の live scan (`t080_freeze_migration._verify_holdout_live_scan`、zero-hit 要求) と、v2 世代の closure 由来 hit を期待集合として照合する `launch_validate` (C2-4) の矛盾を production 側で解く。設計案の候補は `output/insights/2026-09-18/t2724-freeze-g1-gen/package.md` の A-1 (承認済み世代の artifact から occurrence 検証で期待集合を導出。候補 data は使わない) / A-2 (active v2 なら receipt 不要。置換範囲の定義が要る) / A-3 (receipt の静的検証と epoch 束縛は維持し未知性層 2 だけ full launch validation へ委譲)。受理集合が変わるので新 D + 境界 test (D96) + 変異 matrix、除外集合の拡大・hold 追加・test 弱体化はしない (規律 2)。着地後に test 経路 (T-080 fixture の実 root output 複製 / 実 HEAD clone) を追随させ、chain + G の land を再開する。人間が package.md の択 A 系を採るまで着手しない。
