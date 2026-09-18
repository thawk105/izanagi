---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2724-freeze-g1-gen
seq: 3
---

## {{D:t080-receipt-defers-unknownness-to-active-v2}}. 凍結 v2 g1 の chain + G の取り込みは、T-080 receipt の未知性層 2 を承認済み active v2 の full launch validation へ委譲する整合修正 (A-3) と 4 経路の test 修正を 1 つの実装 wave で先に着地させてから行う

**決定 (ユーザー委任「codex に相談して決めて」2026-09-18、read-only codex 2 レンズの一致に基づき親が裁定):**
D2120 項 2 (a) の chain 取り込みは維持するが、実行順序に前提を足す。

1. **production の整合 (設計候補 A-3)。** T-080 (v1 移行 receipt) の解決 `t080_freeze_migration.verify_receipt` が持つ
   receipt の履歴・静的検証 (artifact bytes / closure / derivation / ccbench gitlink)・epoch 束縛、oracle driver の
   `_make_gate_decision` による refusal 集約と `_campaign_t080_value` による invalid 拒否は**維持**する。そのうえで、
   **承認済み active v2 世代の full launch validation (`s8b_ratified_freeze.launch_validate`) が同一 root・同一 HEAD・
   同一世代で成功した場合に限り**、receipt 検査列の未知性層 2 (`_verify_holdout_live_scan` の zero-hit 判定) を、その
   validation の closure 由来 hit との完全一致検証 (C2-4) へ委譲する。候補集合・候補 ID・検索式・照合規約の凍結文書との
   束縛は失わない。active v2 が無い木 (未発効、A / X 前) は従来どおり拒否し、`never-issued` / `active-valid` の意味は変えない。
   official 床値の起動証明 (`clean_scan_digest`、D2077 step 7) は変えない。走査除外集合・growth hold・G と入力 chain の
   bytes と履歴・人間 A / X の境界は変えない。`static_gate_adapter` と campaign-start 前の receipt 再解決にも同じ条件を適用する。
2. **test の実 root 切り離し (4 経路 45 node)。** T-080 fixture の実 root output 複製 (draft の live scan)、実 committed
   HEAD の clone (official clean scan)、`run_block(root=ROOT)` の receipt 解決を共有する契約 test、公開 gate の exact refusal
   集合を、実 checkout の現在の成果物に依存しない合成履歴 / fixture へ移す。「official 成果物を持つ tree では clean scan が拒否
   する」「未発効 + hit は拒否」「active v2 + 期待 hit 完全一致だけ受理」の負例・正例を残し、既存テストの期待値を緩めない。
3. **変更単位。** 1 と 2、新 D、境界 test (発効境界・receipt 境界・走査境界・束縛境界・経路境界)、変異 matrix (完全一致を
   包含へ、receipt refusal 無視、承認前委譲、検索規約照合削除、開始前再検査削除を負例が捕まえる)、段階別 preflight (runbook §2
   P3 の「拒否 2 件 exact」は chain 導入後の oracle 段階に適用できない) の文書を、Codex author の 1 つの実装 wave に収める
   (D96)。設計 wave と再裁定を分けない。A-3 の同等性を境界 test で確認できることを着地条件とし、不一致なら検査を省略して
   通さず停止する。
4. **順序。** (i) 上の実装 wave を chain の無い main へ land → (ii) 世代導入 G の wave が保存 branch の候補 commit X2 と
   fold 後の main を固定 SHA で通常 merge し、X1' + X2 + G を 1 wave で受入・land (merge-base を 1 つに保つ) →
   (iii) 人間が A → X を連続 commit して批准を検証 → (iv) W-4 の spec 承認 (別管理) → (v) W-5。

**理由:**
- 実測 (世代導入 G の wave): X1' を含む木では受入の非 held 45 node が赤、runbook P3 `gate-check` が
  `holdout-freeze-verify: [holdout.unknownness_layer2]` で refuse。A / X を作っても消えない (driver は v2 処理に先立って
  receipt を解決し、`_make_gate_decision` が refusal を集約する)。v2 の `launch_validate` は closure 由来 hit を期待集合と
  して完全一致を要求するのに対し、T-080 の live scan は zero-hit を要求する — 段階間の整合欠落であり、D2077 が意図した拒否は
  official 床値の再起動であって批准後の oracle までではない (レンズ B)。
- A-3 は receipt の fail-closed と epoch 束縛を残し、衝突する live scan の責務だけを既存の full validation へ移すので、
  変更範囲が最小で検出力を保てる (両レンズ)。委譲先は「承認・出所・occurrence・完全一致」を検証済みの経路であり、gate を
  緩めない (規律 2)。候補 data を期待集合の authority にしない (規律 6)。
- 過去の裁定 (D2120 項 2 (a)) は撤回しない。未認識だった実行上の前提を満たしてから取り込む順序の補足である (規律 7)。
- test 修正を同じ wave に入れないと、未発効の木 (A / X 前) では受入が成立せず、chain + G を land できない (レンズ B CB-2)。

**却下した選択肢:**
- A-1 (承認済み世代の artifact から occurrence 検証で期待集合を導出) — `launch_validate` の C2-4 と二重実装になり、
  検証ロジックの乖離を招く。安全に共有単位を広げると A-3 に近づく。
- A-2 (active v2 なら receipt を要求しない) — receipt 履歴・欠落・改変検出・campaign epoch の代替まで設計対象が広がる。
- E (bytes 束縛した official run_dir を `exempt_exact` で免除) — 走査免除の拡大であり、occurrence と消失検出を継承しない。
- B 単独 (test 側だけ) — production の拒否が残り oracle に届かない。
- C (45 node を growth hold) — 検出力の削除。DW-O18 は再赤でも hold 登録しないと定める。
- D (chain を main に載せず別 branch で oracle) — X1' を含む checkout なら branch を問わず同じ拒否が出る。既裁定の変更も要る。
- 設計 wave → 再裁定 → 実装 wave の分離 — 余分な直列工程と発効前の受入問題を残す (レンズ B)。
