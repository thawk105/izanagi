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
- 逐語・実測の正本 = `output/insights/2026-08-04_t244-p1-ir-emitter/`。設計判断は {{D:reflux-ir-p1-component}}
- **dev-wave の運用事故を 2 件記録した** — {{F:dev-wave-child-dies-with-tool-call}} と
  {{F:pgrep-matches-parallel-wave-child}}。合わせて約 45 分を失った

## 次の一手差分

### 更新

- [T-244] **P1・機械部品は入った。ただし P1 は未充足**: `orchestrator/campaign/reflux_ir.py`
  (固定 5-bit IR・正準 wire codec・正準 C++ emitter) と独立 golden 32 点、テストを land した。
  **production へ wiring しないため候補表現は閉じておらず、受理集合は任意の 1 行 C++ のまま**で、
  production 到達性はゼロである。cap-lift は依然 FAIL で D114 の上限 1 も不変。
  P2 / P3 / P5 / P7 / P9 / P10 は本 wave では 1 件も充足しない。
  次段は wiring wave (自由 `implementation` の拒否、wire→mask→predicate の唯一経路化、
  raw mask と source digest / variant ID の束縛、WAL/provenance/report での同束縛、
  binding 欠落 artifact の proof chain からの拒否) で、**受理集合の縮小なので D96 手続が要る**。
  P3 は (165) の U-A〜U-D 裁定待ちのまま
  base: a7f609f9cacafc73e60462b33df8dad4ace97f115c85bdabf96abee224b1df1b

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
- {{T:dev-wave-detach-contract}} **P2・新規**: `DW-O01` へ背景 job の detach 必須を、
  `DW-M05` の照合規則へ「並行 wave の子に一致しないこと」を足す。
  根拠は {{F:dev-wave-child-dies-with-tool-call}} と {{F:pgrep-matches-parallel-wave-child}}
