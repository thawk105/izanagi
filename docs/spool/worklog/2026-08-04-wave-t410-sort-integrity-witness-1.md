---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t410-sort-integrity-witness
seq: 1
title: [T-410] sort 軸 witness の同値関係を観測同値として確定し、実装は evidence の source binding に塞がれた (docs のみ、branch worktree-wave-t410-sort-integrity-witness)
---

## 本文

- **段 4 で「この wave では実装しない」と裁定した。** 実装差分が無いため変異事前登録・変異 matrix・
  受入全走は対象外である。[T-410] は中止しない — 塞いでいるのは witness の必要性ではなく
  binding の射程である
- **止めた根拠は裁定時点で未見の新事実で、親が実測した。** `orchestrator/verifier/` 配下の
  全 Python が committed qualification evidence の runtime module binding に束縛されている。
  `orchestrator/verifier/report.py` にコメント 2 行を足すだけで
  `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` が
  `1 failed, 77 passed` になる (無変異時 78 passed)。worktree 内で実施し即時復元済み・差分ゼロ
- **D107 の先例は使えない。** 同型事故 (共有 policy が同じ evidence に束縛され同じテストが赤に
  なった) では「後から key を足す側が退く」と裁定したが、本件は verifier が witness の producer
  本体であり退避先が無い。binding を書くのは実 job の収集段だけで正規の再束縛経路も無く、
  evidence 記録後 verifier は 1 度も変更されていない
- **ユーザー裁定へ返す 3 択:** (a) rung-1 qualification campaign を実 job で再走し evidence を
  再発行してから実装する (先例あり)、(b) binding の射程を変える (proof chain の意味が変わるため
  D96 級の手続が要る)、(c) witness を束縛対象外 module に作る (実装は通るが、consumer が生 trace を
  再パースする問題を温存するため親は非推奨)
- **設計契約は確定して {{D:sort-witness-observation-equivalence}} に記録した。** D138 が
  「確定していないこと」に挙げた sort 軸の同値関係を、**因果同値でなく固定 origin 内の観測同値**
  として定義した。P 行の reason は comparator の壊れ方ではなく事後検査の分岐名であり、
  size を先に見て等しいときだけ multiset を見る短絡順のため、comparator 法則から reason への
  写像は関数ですらない
- **敵対相談で親 brief の誤りが 2 件出た (訂正済み)。** (1) integrity の exact-key 検査は
  role policy でなく silo ladder の evidence schema にある。(2)「`integrity.notes` の機械 consumer は
  0 件」は誤りで、rejection 描画が notes を 1 行ずつ LLM prompt へ出している。
  正しくは「sort 軸の reason 内訳が次手生成へ届く唯一の経路がこの自然文である」
- **プランの提案 1 件を実測で refute した。** 「role manifest と生成 adapter と hash pin を
  追随させる」は不要である。verifier role の integrity schema は `clean` のみ +
  additionalProperties 禁止の縮約射影で、`permutation_violations` は manifest に 0 件、
  射影を構築する非テスト経路も 0 件 (dormant)。提案どおり足すと role の可視範囲を広げる
  遮断設計の後退になる
- **実測で判明した規模の罠:** P 行は 1 run あたり最大 879,025 件に達する (既存 positive control)。
  1 行 1 object の無制限露出は verifier timeout・巨大 WAL 1 行・critic context 切詰めを招くため、
  露出は集約と bounded sample に限る
- **現行検査の被覆の狭さも記録した。** permutation 保存検査は size と rcdptr multiset しか見ず、
  **順序も key と rcdptr の対応も検査していない**。ただし非 strict-weak-order comparator の UB で
  対応だけが入れ替わる到達可能性は未実証であり、そう書かない
- **受入: 既知赤 waiver W1 を適用して land した。** 全走の実測は
  **1 failed / 5438 passed / 19 skipped**、赤 node は
  `orchestrator/tests/test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  の 1 件のみ。W1 の毎回検査を実施した — (1) 原因の同一性: `tools/ruleops.py inventory --repo .` が
  rc=2 で `blob が非 UTF-8:` を出力し、指す path が `output/insights/**/evidence/**` 配下である、
  (2) 帰属: 自 wave の差分 (docs/spool 3 件 + insights 6 件) が当該 path に触れていない、
  (3) 他の赤ゼロ、(4) [T-407] 未 land ゆえ waiver は有効。射程どおり docs・道具の衛生 gate への
  免除であり、本 wave は docs のみで正しさ防壁に触れていない
- **親は一度 W1 を見落として停止し、ユーザーの指摘で是正した。** W1 は本 wave が受入に使った
  main に既に存在しており参照可能だった。停止条件の適用前に「既知赤 waiver が成立しないか」を
  確認する手順が親の運用に無かったことが原因である
- **研究状態への影響は無い** — production 挙動・受理集合・certified 選択・材料レポート・
  proof chain・凍結 bytes はいずれも不変。`check_docs` rc=0、provenance full 監査 rc=0

## 次の一手差分

### 更新

- [T-410] **P2・ユーザー裁定待ち**: 設計契約は {{D:sort-witness-observation-equivalence}} で確定した。
  実装は committed qualification evidence の runtime module binding に塞がれている (実測)。
  3 択 (a) campaign 再走で evidence 再発行 / (b) binding 射程の変更 (D96 級手続) /
  (c) 束縛対象外 module へ実装 (非推奨) のいずれかの裁定が要る
  base: 6c15c7287ff68ca353376a184c66a95caad1b5ad262530e915954121a2d513cb

### 新規

- {{T:permutation-check-coverage}} **P2・新規**: permutation 保存検査の被覆を広げるか裁定する。
  現行は size と rcdptr multiset しか見ず、sort 後の順序も key と rcdptr の対応も検査していない。
  「順序が壊れた sort」と「対応だけが入れ替わった write_set_」は現行検査を沈黙で通過する。
  到達可能性は未実証であり、広げるには C++ producer (validationPhase の `#if TRACE` 枠) の改変が要る
