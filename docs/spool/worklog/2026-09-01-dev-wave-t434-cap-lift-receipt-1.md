---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t434-cap-lift-receipt
seq: 1
title: [T-434] cap-lift 受領証は今は実装できないと確定した — 受理枝が発火せず、正式系列は manifest が世代数を 2 に固定している (docs のみ、branch worktree-dev-wave-t434-cap-lift-receipt)
---

## 本文

- D841 (択 (a)) に従って受領証と consumer 結線を単一変更単位で実装する wave として起動したが、
  段 4 で**実装しないと裁定した**。独立に成立する 3 本の理由があり、1 本でも成立すれば実装は不可である。
  (i) 前提条件の合接が P6 の 1 件だけで閉じており、受理枝の正例を実体の差し替え無しに置けない。
  (ii) registered manifest が `generations` を整数 2 だけ受理するため、受領証があっても正式系列の
  上限は開かない。(iii) 発効 topology だけで開くと D121 決定 (7) / D150 決定 (4) / D156 を迂回する。
  **D841 とは矛盾しない** — D841 が定めたのは実装するときの不可分性であって実装時期ではない。
  正本は `output/insights/2026-09-01_t434-cap-lift-receipt-v3/design-v3.md`。
- 設計 v2 (2026-08-04) の前提のうち 4 件が失効していた。承認上限は 1 ではなく 2 (D410)、
  層 3 の版上げは D828 が禁止、前提条件の機械再導出は裁定済み択一 1〜10 に含まれない設計判断、
  充足済みは P10 だけでなく P1 も (D160)。
- **条件 11 を scope から外した。** 受領証の runtime consumer ではなく (成功末尾も
  `EVIDENCE_UNDEFINED`)、D882 決定 (3) が `required_evidence` と評価器を変えないと定め、
  証拠契約の内容 hash は `test_s8c_preregistration_core.py` が literal で凍結している。
- 段 2 プランと段 3 の 2 レンズが数えていなかった consumer を確定した —
  `trial_registry` の manifest generation 契約と、supervisor report の
  `_budget_indeterminate_report` 経路。実装時の閉包は design-v3 §3 に置いた。
- 実装前に解く必要のある設計の穴を 5 件確定した (申請束縛 preimage の循環、manifestless 経路に残る
  定数だけの引き上げ、hardened git 面が HEAD 捕捉にしか掛かっていないこと、層 3 編集による
  `meta.generator.sha256` 変化と fresh rebuild 比較の非正規化、`_run_workload` scope が
  generation を束縛しないこと)。design-v3 §4。
- 段 3 の 2 レンズが親の実測を 3 件反証し、親が現物で追認した。うち 1 件は F165 と同一型の再発
  (参照検索の 0 件を機構の不在へ一般化した) であり、failures へ再発として記録した。
- エージェント工数: codex 子 3 本 (段 2 プラン 1・段 3 敵対相談 2)。いずれも rc=0、
  `check_codex_output.py` rc=0。実装子・fix 子は裁定 0 により起動していない。
- 実装面の差分ゼロのため変異 matrix は免除 (DW-S04)。受入全走は免除せず、本エントリの記録 commit の
  tip を land gate として投入する (`tools/dev_wave_land.py` は docs のみの wave でも受領証を
  構造上必須要求し、免除経路がコードに無い)。
- 段 8 の自己改善候補は 1 件 (DW-S01 の既存被覆検索に「同型機構の既存実装」を明記する) だったが、
  **実施しないへ落とした**。D782 / D730 の手順を適用した — L1 unique footprint は予算
  10625 bytes に対し現状ちょうど 10625 bytes で、意味を保つ追記は 1 byte も入らない。
  意味等価な削減先が同層に見つからず、例外収容の要件 (独立 3 例) も本 wave の 1 例では満たさない。
  上限引き上げには至っていない。なお本件の再利用漏れは `DW-S03` の既存義務が実際に発火して
  段 3 の 2 レンズが独立に検出しており、機械的防壁の新設は要らない。

## 次の一手差分

### 更新

- [T-434] **P1・裁定済み (D841、択 (a)) だが実装は 3 本の理由で不可 → ユーザー裁定待ち**:
  2026-09-01 の実装 wave が段 4 で実装しないと裁定し、3 択の裁定パッケージを返した
  (`output/insights/2026-09-01_t434-cap-lift-receipt-v3/design-v3.md` §7)。
  択 A (推奨) = WAIT を維持し解除条件を確定する — (i) P6 の意味的充足契約の実装と実認定記録、
  (ii) registered manifest と 8c 事前登録の generation 契約を受領証条件付き `3..10` へ改訂する裁定
  (T-435 の変更単位との順序を含む)、(iii) design-v3 §4 の設計の穴 5 件の解消。
  択 B = 前提条件の機械再導出要求を外し人間発効 commit を状態判定の権威にする
  (D121 決定 (7) / D150 決定 (4) / D156 の明示 supersede が必要、かつ (ii) も同時に要る)。
  択 C = 到達不能を承知で fail-closed な将来の入口として land する
  (先例はあるがその正例は封印型の差し替えで作られており、実体を stub しない正例とは両立しない)。
  実装時の consumer 閉包・再利用方針・変異事前登録の候補は design-v3 §3 / §5 / §6 に確定済み。
  base: dfb28fd96900f66b69e5dfc81c0cad9357c9a2ac037fed619ee2ae616225011c
