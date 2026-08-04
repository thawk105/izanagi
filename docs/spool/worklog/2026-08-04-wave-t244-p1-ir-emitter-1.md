---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t244-p1-ir-emitter
seq: 1
title: [T-244] D121 P1 の機械部品を実装した — 独立 golden を「順序」で担保し、旧実装と全 32 点一致した (コード + docs、branch worktree-wave-t244-p1-ir-emitter)
---

## 本文

- **scope はユーザー引数で確定**した — T-244 本体のうち D121 P1 のみ、新規 leaf に閉じ、
  P3 (origin ledger) と P5 (provider/session/token) の面には触らない。並行 wave
  `wave-t244-p3-origin-ledger` が P3 を所有する
- **段 3 の敵対 2 レンズが独立に、段 2 プランの「独立 golden 四層」が一本の系譜であると指摘した**
  (合議ではない)。親が実測で裏取りした系譜は
  `predicate_for` → campaign provenance → freeze → `s1_expected_goldens` であり、
  **campaign 9 点と freeze 3 点は独立な期待値ではない**。単一実装子が golden と emitter を
  同時に書けば監査は恒真になっていた
- 段 4 で実装子を**所有分離 2 体・直列**へ変えた。子 G が規範仕様と骨格 patch だけから
  golden を起草 → **親が emitter 実装前に sha256 を凍結** → 子 E が golden 非参照で emitter を実装。
  golden の hash は fix 後も不変だった。**主張するのは「完全 blind」ではなく順序保証**である
- 子 E は consumer 検索の `rg` が golden を走査した可能性を自己申告したが、**親が実測して
  露出ゼロと確定した** — その rg パターンに一致する行は golden に 0 行存在しない
- **段 6 の敵対 2 レビューも両方 NO-GO** で、must-fix 6 件を返した。うち 1 件は
  **親が事前登録した変異 V8 が現状のテストでは生存しうる**という指摘で、
  空白の負例が strip 後も長さ 4 のままだったことによる。fix で「正規化すると正準になる」
  負例を追加して閉じた。F1〜F7 はすべて closed、regressed なし
- **検出力は水増ししない** — 独立な証拠系譜は 2 系譜だけ (別所有・実装前 hash 固定の literal
  golden 32 点と、旧実装との全 32 点差分)。freeze 6 record と campaign 9 mask は旧実装から
  materialize された歴史 artifact なので独立 oracle の純増は 0 である
- **親の誤りを 2 件訂正した** — 既存被覆は 8 点でなく 9 predicate (`candidates(EFF3)` は
  8 subset + `ident_all`)。`s8a_trigger_sweep.py` は freeze の changed 12 側であり、
  pin と一致する変更不可ファイルは `axis_trigger_gating.py` だけである
- **変異 matrix は 19/19 KILLED、生存ゼロ** (`output/insights/2026-08-04_t244-p1-ir-emitter/mutation-matrix.md`)。
  うち 17 件は harness、2 件 (golden への Call / 非 `__future__` import 注入) は
  **AST 防壁が module 冒頭で発火して collection error になり harness が分類できない**ため、
  親が手動注入して rc と診断文言を実測し、hash 照合で復元した。**初回走行の 8 件 MISMATCH は
  「期待の上位集合」であって検出力不足ではない** — 親の事前登録が狭かったための erratum で、
  判定は 1 件も変わっていない
- 受入: land 直前の全走は **5470 passed / 2 failed / 19 skipped**。**赤 2 件はいずれも
  本 wave の差分に帰属しない** — (a) `test_ruleops.py::test_real_checkout_...` は
  `tools/ruleops.py inventory` が非 UTF-8 blob で rc=2 になる既存条件で、
  **ユーザーの元 checkout でも同一 rc・同一 blob で再現する**。(b)
  `test_codex_worker_launch.py::test_check_receipt_rechecks_all_manifest_header_fields[base_commit]`
  は**単独再走で 3 passed となり再現しない**フレークで、`reflux_ir` への参照はゼロ (DW-O18)。
  provenance 監査は 963 件・違反なし
- 逐語・実測の正本 = `output/insights/2026-08-04_t244-p1-ir-emitter/`。設計判断は {{D:reflux-ir-p1-component}}
- **dev-wave の運用事故を 2 件記録した** — {{F:dev-wave-child-dies-with-tool-call}} と
  {{F:pgrep-matches-parallel-wave-child}}。合わせて約 45 分を失った

## 次の一手差分

### 更新

- [T-244] **P1・機械部品を実装 (P1 未充足)。P5 は 2/3 実装済み、P3 は差し戻し**:
  **P1**: `orchestrator/campaign/reflux_ir.py` (固定 5-bit IR・正準 wire codec・正準 C++ emitter) と
  独立 golden 32 点、テストを land した。**production へ wiring しないため候補表現は閉じておらず、
  受理集合は任意の 1 行 C++ のまま**で production 到達性はゼロである。次段は wiring wave
  (自由 `implementation` の拒否、wire→mask→predicate の唯一経路化、raw mask と source digest /
  variant ID の束縛、WAL/provenance/report での同束縛、binding 欠落 artifact の proof chain からの拒否)
  で、**受理集合の縮小なので D96 手続が要る**。
  **P5**: provider 注入の拒否 (実 Claude 試行に限る) と role 間 session 共有の拒否 (実行時 +
  成果物再検証の 2 層) を実装し D148 に記録した。**P5 全体は未充足**で、
  **U-1** `drive` / `preview` 注入も塞ぐか (塞ぐなら既存 2 テストの注入手段を別 seam へ移す設計が要る)、
  **U-2** 未予約 token を P3 の予約 receipt に依存させるか P5 の第 3 要件を origin ledger の
  充足条件へ移すか、**U-3** provider executable の真正性 (許可 digest registry) を要求するか、の
  3 件が裁定待ち。U-2 は P3 の裁定が先行する。
  **P3**: (165) の U-A〜U-D 裁定待ちのまま。
  **cap-lift は依然 FAIL** で D114 の上限 1 も不変。P2 / P7 / P9 は未着手。
  逐語は `output/insights/2026-08-04_t244-p1-ir-emitter/` と
  `output/insights/2026-08-04_t244-p5-injection-gate/`
  base: 9544907e9fc9fb64dd21dc9f3d50b44d76a03c2e8dfd37cacca6a30b1ab3e472

### 新規

- {{T:reflux-ir-production-wiring}} **P1・新規**: `reflux_ir` を production の候補受理経路へ配線し、
  自由な 1 行 C++ を 5-bit wire へ閉じる。受理集合の縮小なので D96 手続 (新 D + 境界テストの
  同一変更単位) が要る。consumer 閉包 (`p3_s4_loop_trigger_gating.py`、proposal schema、
  materialize、build cache、replay) を一体で塞ぐこと。**P1 を充足と名乗れるのはこの wave の後**
- {{T:reflux-rejection-disclosure-closure}} **P2・新規**: 拒否理由の多面開示を閉じる。
  現行の gate / preview / attempt journal / whiteboard / critic digest は subtype・reason・
  禁止識別子・件数を公開しており、leaf 側だけ開示 0 bit にしても経路が残る。
  report と投影契約の変更を伴う
- {{T:ruleops-blob-blocks-full-suite}} **P2・新規**: `tools/ruleops.py inventory` が
  非 UTF-8 blob で rc=2 になり全走に赤 1 件を残している。[T-407] が同じ現象を所有していれば
  そちらへ寄せて本項は閉じる。**本 wave の差分とは無関係**で、ユーザーの元 checkout でも再現する
- {{T:codex-launch-receipt-flake}} **P3・新規**: 全走で
  `test_codex_worker_launch.py::test_check_receipt_rechecks_all_manifest_header_fields[base_commit]`
  が 1 度だけ落ち、単独再走 (3 passed) で再現しなかった。並列度の高い全走でのみ出る
  race の可能性がある。再発したら本項へ日付を足し、2 例目で調査する
- {{T:dev-wave-detach-contract}} **P2・新規**: `DW-O01` へ背景 job の detach 必須を、
  `DW-M05` の照合規則へ「並行 wave の子に一致しないこと」を足す。
  根拠は {{F:dev-wave-child-dies-with-tool-call}} と {{F:pgrep-matches-parallel-wave-child}}
