---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t822-c02-receipt-v2
seq: 1
title: 条件 2 を評価器 table へ載せ、受領証 v2 が実 bytes から arm 束縛を再導出する — 「3 者一致で足りる」を段 6 が反証した (コード + テスト + 規範文書 + 凍結世代、branch worktree-dev-wave-t822-c02-receipt-v2、変異 matrix = baseline PASSED・13/13 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **段 2 プランの「3 者一致」を段 6 レビューが反証し、親が採用した。** 当初案は受領証・report・
  run-start の `arm_execution` が一致することを見る形だった。3 者はいずれも producer が書いた
  要約であり、相異なる 6 digest を捏造して binding digest を正しく再計算した bundle が全部通る。
  最終形は権威ある chain と同じく **hash 済み report の cell descriptor から content digest を
  再計算**する。理由落としの根拠が「自己申告の一致」から「名指して hash した bytes からの再導出」へ
  変わった。詳細は {{D:receipt-v2-rederives-from-named-bytes}}。
- **負の対照が守るべき関数を monkeypatch していた。** 段 5 の受領証側の対照は
  `_arm_execution_authorizes_reason_drop` を `False` へ差し替えて赤を作っており、実装を
  `return True` へ変える変異を 1 件も殺せなかった。段 6 レビュー A が見つけ、実データで実関数を
  通す形へ作り直した。変異 `t822.m14` がこの是正の直接の検定であり、本走で KILLED である。
- **充足可能集合が防壁として機能していなかった。** `SATISFIABLE_CONDITION_IDS` は宣言されるだけで
  dispatch 後に照合されておらず、評価器が 1 行の退行で充足を返せば受理されていた。実行時の
  関門にした。段 6 レビュー A の指摘。
- **問 3 の実名整備は判定結果を 1 bit も変えないことを親が実測した。** 実名
  `assert_trial_registry_acceptance` は `assert_campaign_layer3_chain` も
  `verify_s8c_cross_binding` も呼んでおらず、両名は `trial_registry.py` に 0 回しか出現しない。
  受理集合は広がらない潜在バグ修正である。非機械条件 C03/C07/C08 に残る同じ誤名は scope 外と裁定した。
- **並行 wave が先に第 6 世代を land させ、凍結世代の衝突が起きた。** merge では解けない型だった —
  凍結の不変検査は全祖先 commit を走るため、「契約を変えたが tip の世代 record は古いまま」の
  commit が祖先に残ると、後から正しい世代を足しても永久に拒否される。合成監査の子が見つけ、
  親が裏取りした。作業内容を main 基準の patch へ退避し branch を main tip へ戻して再適用し、
  契約変更・実装・規範文書・世代 record を単一 commit に入れた。{{F:frozen-generation-ancestor-mismatch}}
- **変異 probe で 1 件が生存した。** report の `arm_execution` が受領証と一致することを要求する
  検査に、負の対照が無かった。対照を足して本走で殺した。あわせて受領証 verifier の拒否点
  22 箇所を棚卸しし、直接対照を持つのは 6 箇所だと実測した。残る 15 箇所の整備は `DW-G03` の
  族一般化に当たるため見送り、裁定パッケージ候補として記録する。
- **変異 harness と xdist の node 名前空間が衝突した。** group marker を持つ test は失敗行で
  `@<group>` 接尾辞が付くが collection には現れず、期待 node として登録できない。
  xdist を切る案は実測 1 run 7 分 21 秒 (14 run で約 103 分) だったため、`--deselect` で
  当該 1 件を外した。`t822.m11` の killer は 5 → 4 になったが他 12 変異の期待 node は不変である。
- **親自身の前提を 2 件反証した。** (a) 「additive schema なら凍結 golden を保てる」は誤りで、
  producer が v2 を出す以上 golden は割れる。既存射影へ値付き消費を足すのが正規経路だった。
  (b) 「新世代の hash が受領証側の source bytes に依存する」は誤りで、protected preimage は
  証拠契約 hash と規範文書の 3 hash だけである。
- **親の作法違反 2 件を自己申告する。** (a) 段 6 レビューの初回投入で `--stage review` に
  `--lane` を渡し両子が rc=2 で即死した (token 消費ゼロ、新 artifact 名で再投入)。
  (b) 変異 harness の走行中に insight package を tree へ書き untracked 検出で中止させた
  (一次資料を先に commit して再走)。どちらも既知型を踏んだものである。
- **段 3・段 6 とも 2 レンズが独立に NO-GO を返した。** 段 3 は所見 21 件・must-fix 13 件、
  段 6 は所見 11 件・must-fix 8 件。親が refuted / 格下げしたのは 2 件 (逆射影が 3 者不一致を
  隠すという所見は、production の chain が既に 3 者一致を強制しているため格下げ)。
- **エージェント工数**: codex 子 12 本 (plan 1・consult 2・author 2・fix 4・review 2・merge 監査 1)。
  段 3 レンズ A は上流 websocket の 401 で 1 度失敗し (28 model call / 429 秒消費後、成果物ゼロ)、
  新 artifact 名で再投入した。codex 子は本 wave でも pytest を 1 件も実走できず、測定は親が
  毎巡引き受けた。
- 正本 = `output/insights/2026-08-18_t822-c02-receipt-v2/README.md`

## 次の一手差分

### 更新

- [T-822] **P2・(ii) は閉じた。(i) は [T-1310] 待ちのまま**:
  証拠契約の条件 2 を機械検査対象へ載せ (機械検査対象 6 → 7 条件、判定器の版を v3 へ)、
  受領証 v2 が**名指して hash した bytes から digest を再導出**して arm 束縛を確かめる形にした。
  必須理由から `c02-arm-binding-unproven` を落とせるのはその再導出が通ったときだけで、
  `certifying` は構造的に false のまま、`t468-approval-authority-absent` は必須で残る。
  問 3 の実名不整合も 3 面 (契約 JSON・評価器 literal・fixture) で解消した。
  **certified 選択の値と proof 参照は 1 件も変わっていない。**
  (i) は正式 holdout の producer profile が要るため [T-1310] 待ちのまま。
  base: 8d5af8f70f75db8337b6edb544d75f808d409fc069f3edd44b1fdbc978e33092

### 新規

- {{T:receipt-fail-site-controls}} **P3・新規**: 受領証 verifier の拒否点 22 箇所のうち、
  直接の負の対照を持つのは 6 箇所である。残る 15 箇所へ対照を整備するかを裁定する。
  `DW-G03` の族一般化に当たるため本 wave では見送った。
- {{T:mutation-xdist-node-namespace}} **P3・新規**: 変異 harness の期待 node と xdist の
  group marker が別名前空間になり、group を持つ test を期待 node に登録できない。
  本 wave は `--deselect` で回避した。harness 側で正規化するかを裁定する。
- {{T:c03-c07-c08-stale-names}} **P3・新規**: 非機械条件 C03 / C07 / C08 の証拠契約に
  実在しない関数名 `accept_trial` が残る (C03 の `load_manifest` も同型)。現時点で判定結果は
  変わらないが、将来それらを機械化する wave が同じ穴を踏む。
