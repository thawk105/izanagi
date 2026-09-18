# 既裁定の逐語 (dev-wave-t2724-t080-defer-active-v2、親が 2026-09-18 に抜粋)

## 裁定控え末尾「裁定」節 (rulings-inbox/2026-09-18-t2724-freeze-g1-chain-land-blocked-by-t080-receipt-live-scan.md)

## 裁定 (2026-09-18、ユーザー委任、read-only codex 2 レンズ一致)

択 A、設計候補 **A-3** + 4 経路 45 node の test の実 root 切り離しを **1 つの実装 wave** (Codex author、新 D + 境界 test + 変異 matrix +
段階別 preflight 文書) に収め、chain の無い main へ先に land する。receipt の履歴・静的検証・epoch 束縛・refusal 集約・invalid 拒否は
維持し、承認済み active v2 の full launch validation が同一 root / HEAD / 世代で成功した場合に限り未知性層 2 (zero-hit 判定) をその
完全一致検証へ委譲。未発効の木と official clean scan は従来どおり拒否。走査除外・hold・chain と G の bytes は不変。順序: 整合 wave →
G wave が保存 branch の X2 と fold 後 main を固定 SHA で merge し X1' + X2 + G を 1 wave で land → 人間 A / X → W-4 spec → W-5。
却下: A-1 (C2-4 二重実装)、A-2 (置換範囲が広い)、E (走査免除拡大)、B 単独、C、D。記録: wave branch の decisions fragment
(slug `t080-receipt-defers-unknownness-to-active-v2`、commit `229982652`)、`package.md` 末尾、相談逐語 `evidence/consult-{a,b}-*.md`。
台帳への反映は G wave の land 時 (整合 wave の後)。次 wave: `/dev-wave` で整合 wave を起票 (brief は G wave の最終報告)。

## G wave の decisions fragment (branch worktree-dev-wave-t2724-freeze-g1-gen tip 229982652、未 land)

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

## D2120 項 2 (docs/decisions.md、main 24ede1d11)

### 項 2 — 凍結 v2 g1 候補を発効へ進める: 床を採用し、chain を main へ取り込み、承認と pointer は人間 commit

対象: T-2724、T-750 の残余、T-1851 の後段。

**決定:**
- (c) 両 holdout とも配線下限 0.03 × stock 中央値で決まった 1 走行の床を、現行 formula v2 と protocol に従う
  候補充填として g1 の床に採用する (択 1)。「科学的に十分な床」とは主張せず、候補文書に配線下限の事実を明示する
  (D2104 項 1 の条件を維持)。追加観測 (択 2) は出所を差し替えない (D1311) ため判断材料にしかならず、下限 0.03 の
  再検討 (択 3) は protocol の変更と再測定を伴う別件。
- (a) 当該 holdout 集合 (rr20 / rr80、v1 freeze) の official 走行を打ち切ると決め、保存 branch
  `freeze-g1-chain-t2724` の chain (X1' `cc82edc8c`、X2 `4d8fb93b7`) を main へ取り込む (択 1)。隔離して候補を
  作った実施形を D2077 の例外として追認する (択 3)。帰結: 以後 main とそれを継承する checkout では official 床値の
  起動証明 (clean scan) が赤になる (D2077 step 7 の設計どおり)。後続の official 床値 wave (非 sort 単独構成など) は
  main からは起動できず、別 branch から起動する。走査除外は広げない。
- (b) 世代導入 G (非 merge・親 == X1'・`AI-Agent` trailer 付きの AI commit、Codex author の別 wave) を作り、承認 A と
  active pointer X (いずれも逐語 `AI-Agent: none` の人間 commit、X^ == A) をユーザーが commit する。A / X は
  provenance 規約上 AI が作れない人間手番であり、本決定はその手番を確定する (commit の実行は本決定に含まれない)。
- (d) chain が main に載ると growth hold 2 本 (`test_s8b_repo_scan_invariant.py`、
  `test_s8c_preregistration_invariant.py` の holdout 走査) が解除時に設計どおり赤になる。帰結を記録して現行 hold の
  まま (択 1)。除外集合の拡大は D2077 が却下しており規律 2 に触れるため採らない。
- (e) 失敗 run 3 件 (`journal.jsonl` + `launch_certificate.json` のみ、`dev-wave-t1851-c3c-official-floor` worktree) は
  AI が固定退避先へ evacuate して worktree を撤去する (可逆な掃除、裁定不要)。
- (f) T-750 package の P-1 (承認 authority の pinned literal の恒久形) と P-3 (批准 proof chain の budget authorization
  field) は未解決のまま別管理とし、本決定では決めない。

**理由・採らない案:** D2104 項 1 は候補生成を人間承認の受領証発行まで授権し、人間承認そのものを含めなかった。
現行 oracle は床の数値を勝敗判定に使わず (D1985 / D2024)、g1 発効が変えるのは driver の `floor-null` /
`budget-null` 拒否が解けることだけなので、手続的充填として採用する。一次資料の親推奨「(a) 択 1 を急がない」は
(b)(c) の意思が固まるまでの保留であり、本回で (b)(c) を決めた以上 (a) 択 1 が整合する (相談も同意)。

## D96 (docs/decisions.md)

## D96. [T-110] 受理集合を変える改修の手続義務 — 新しい設計判断の記録と境界テストの同時更新を義務化し、機械検査は新設しない (2026-07-29)

**決定 (2026-07-26 ユーザー裁定 [T-110] = 択 (a) の規約化):** 受理集合 (入力を受理/拒否する判定集合。
一次の対象は D90 (1) が唯一の正本と定めた raw 受理集合 = `orchestrator/campaign/s8b_selector_output.py`
module 全体) を変える改修は、次の 2 点を同じ変更単位で満たす。

1. **新しい設計判断の記録を起こす。** 既存 D の追随編集や worklog 記載で代用せず、変更の理由・射程・
   却下案を新しい D として本ファイルへ残す。
2. **境界テストを同時に更新する。** その受理集合を固定している境界テスト (parser 受理集合では
   `test_selector_parser_classification_boundary_at_ratified_launch`) を同じ変更単位で新しい受理集合へ
   追随させ、緑を確認してから land する。

**機械検査は新設しない (裁定の明示部分)。** consumer 閉集合の AST 固定は構文形状しか固定できない
(`if False`・alias・`getattr`・例外握り潰しを見逃す一方、無害な refactor で偽赤になる) ため不採用済み。
到達意味論の機械固定は DW-G03 の独立 2 例が無い。本義務は手続き規律であり、発見経路は decisions の
索引 (受理集合 / parser module 名での grep) と本 D とする。

**D90 (6) との関係:** D90 (6) は段 3 相談の判定に従い「全受理集合変更に新 D を必須とする」を当時の
ユーザー裁定 2 件の射程外の新設統治として削除した。本 D はその後の [T-110] ユーザー裁定 (2026-07-26)
により、この手続義務だけを明示採用したものである。D90 (6) が併せて退けた「新 consumer は必ず
`verify_prediction_freeze` を経由させる」「consumer 閉集合を恒久的に更新する」は引き続き導入しない。

**却下した案:** (b) parser 感応 consumer の閉集合を機械的に固定する — 上記のとおり AST 案の限界により
裁定時点で不採用済み。機械固定を再提案するには DW-G03 の独立 2 例を示して別途裁定を得る。


## D95 (docs/decisions.md、冒頭)

## D95. dev-wave の実装面は Codex author 必須とし、親直接実装と review 代替を認めない (2026-07-29)

**背景 (実測):** 直近 50 commit の `AI-Agent:` は Claude `role=author` 47、Codex
`role=author` 1、author なし 2。さらに直近 30 commit のうち実装面を含む 15 件は Claude author
14、Codex author 1 だった。Git の Author / Committer 自体は人間アカウントであり、ここでいう
author は provenance trailer 上の実作業帰属を指す。原因は、軽量版が段 5 を省略できたこと、
workers 契約が親の直接実装・直接 fix を許したこと、provenance checker が trailer の形式だけを
検査して変更面との組合せを検査しなかったことにある。

**決定 (1): 実装面がある wave は、軽量版でも段 5 の Codex `role=author` 実装子を必須とする。**
親は brief、裁定、統合、全走、記録、commit、local main 取り込みを担当し、実装面を直接編集しない。
段 6 の review 子は従来の条件で省略できるが、review を author の代替にはしない。レビュー後の
cross-cutting fix も Codex 実装単位へ戻す。docs-only は親が本文を直接編集でき、子ゼロでよい。

**決定 (2): 実装面は所在と拡張子で機械判定する。** `orchestrator/`、`tools/`、`hooks/`、
`.github/`、`.codex/`、`external/` 配下の非 Markdown/RST、patch/diff、場所を問わない
