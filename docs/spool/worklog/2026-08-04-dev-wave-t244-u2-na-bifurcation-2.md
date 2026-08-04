---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t244-u2-na-bifurcation
seq: 2
title: [T-244] U2 を新 D で確定した — 択一 3 の既裁定により P4 は無条件義務へ移り、非適用の二分は P6 だけに効く (docs のみ、branch worktree-dev-wave-t244-u2-na-bifurcation)
---

## 本文

- **U2 (D121 決定 (7) の「非適用」の二分) を {{D:t244-u2-na-bifurcation}} として記録した。**
  ユーザー裁定の正本は本 worklog の (153) U2、軸 (iii) 必須化の裁定の正本は
  `docs/archive/worklog-phase3-0803-125-126.md` (126) の択一 3 の項である。本 wave の裁定 =
  `output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md`。同 dir の `brief.md` は
  誤った前提の erratum を含む履歴であり規範ではない。
  承認上限 `MAX_APPROVED_GENERATIONS = 1` は変えず、cap-lift も結線していない。実装差分はゼロ
- **段 3 の敵対 2 レンズが独立に、親 brief の前提実測を反証した。** 親は「択一 3 (軸 (iii) の
  必須前提化) は未裁定」と書いたが、2026-08-03 (126) で「必須にする」と裁定済みであった。
  原因は `docs/decisions.md` だけを grep し、worklog archive を引かなかったこと。D121 決定 (2) の
  「裁定へ返す」をそのまま「未裁定」と読んだ (F31 と同型 — 裁定要約でなく一次記録を開くべきだった)
- **この訂正が本 wave の設計を単純化した。** 択一 3 が採用済みなら D121 決定 (7) が P4 に付けた
  発火条件は恒真であり、P4 は無条件義務へ移る。よって条件付き義務は P6 だけになり、親が
  provisional で用意していた第三の非適用状態語 (先行裁定による非発火) は不要になった。
  U2 の裁定文どおりの二分で足りる。ユーザー再裁定は求めない — 新事実は U2 を覆さず、
  適用先を P6 だけへ狭めるからである
- **親が提案した「還流の実効性 > 0 を cap-lift の必要条件に加える」案は撤回した。** 証拠となる
  field が存在せず自己申告か永久 FAIL になり、前提条件 10 件の集合を変え、ユーザー裁定が明示的に
  残した `NOT_CLAIMED` の免責を実質無効化するためである。同じ論点は V1 として裁定へ返す
- **段 6 の敵対レビュー 2 本が blocker 5 件を出した。** 主なもの: (a) supersede 対象が
  1 文では足りず、無条件義務の列挙文も同時に置き換えないと「7 件」と「8 件」が矛盾する、
  (b) 意味的充足契約も receipt も無い以上、現時点で `NOT_CLAIMED` を認定できる判定入力は存在せず、
  fail-closed の既定として P6 は未実装と判定すべき、(c) P4 の無条件化は cap-lift の規範上の受理
  集合を狭めるので D96 の位置づけを書くべき、(d) runbook が旧 D121 だけを参照しており、新規則を
  逐語で書かないと承認者の経路が閉じない
- **焦点再レビューが親の fix のうち 1 件を回帰と判定し、再 fix した。** 親は (b) の fix で
  「意味的充足契約と receipt が未裁定である間は P6 を `NOT_IMPLEMENTED` と判定する」と書いたが、
  これは D138 の `NOT_IMPLEMENTED` 定義 (実装要素の有無) に receipt を混ぜ、ユーザー裁定が
  残した `NOT_CLAIMED` の免責経路を未裁定事項で塞ぐ**新しい条件**だった。**状態の分類 (事実) と
  承認の可否 (判断) を分離**し、基準が無い間は状態を再分類せず承認を保留する形へ直した。
  対応表は closed 10 / partial 4 / regressed 1 で、regressed 1 件と partial 4 件を再 fix した。
  3 巡目 (`DW-O16` の上限) は closed 4 / partial 1 / regressed 0 で、残る 1 件は決定 (4) の
  「状態を決められない場合は失敗側に倒す」が決定 (4-b) の分離と競合するという文言整合のみ
  だったため、指摘どおり「状態を再分類せず承認を保留する」へ直して閉じた
- **走行中に別 wave の裁定が land し、新 D の事実記述を 1 箇所直した。** 予算値 (択一 1) の裁定で
  P10 (予算値・origin authority・軸 (iii)) の 3 点が揃い、D121 決定 (7) が凍結していた
  「無条件の義務は現時点で 1 件も満たされていない」が偽になった。supersede 後の文からは
  **充足件数そのものを落とし** (件数は裁定の進行で変わるため)、現況は決定 (5) の事実記録と
  worklog が持つ形へ直した。living docs 2 箇所の同じ記述も「満たされているのは P10 の 1 件だけ」
  へ更新した
- **親の base digest 算出が誤っていたのをレビューが是正した。** carry stub
  (`変わらず ((N) 参照)`) の `base:` は stub 自身の digest ではなく、carry 鎖を遡った
  substantive digest である (`spool_fold._extract_latest_active`)。親は stub の digest を
  採ろうとしていた。fold は不一致で停止するため、land 前に気づいて実害はない。
  **段 8 の自己改善として `docs/spool/worklog/README.md` へ carry stub の解決規則を明記した**
- **裁定パッケージ (ユーザーへ返す 4 件)。**
  - **V1 = `NOT_CLAIMED` 構成の還流は限界効果がゼロである。** D138 決定 (1) より、generalized cut を
    主張しない運転の禁止集合は exact-mask cut と一致し、受理集合を 1 点も狭めない。「実装済みで
    主張しない」構成に多世代を許してよいかは U2 (免責) と U3 (帰納段を踏む) の境界であり、
    親は決めない。選択肢は (a) `NOT_CLAIMED` を global な cap-lift 免責に使わず per-run gate に
    限る、(b) `NOT_CLAIMED` 構成では cap を開けないと明示する、(c) U2 のまま許す。
    **P6 が未実装である現在は発火しない**ので、P6 実装の裁定と同時に決めるのを推奨する
  - **V2 = P6 の意味的充足契約が無い** ({{T:t244-p6-semantic-contract}} として起票)。
    空の handler と恒真な assert でも D138 決定 (5) の列挙は形式的に埋まる
  - **V3 = cap-lift receipt が無い** ({{T:t244-cap-lift-receipt}} として起票)。
    判定結果を runbook・事前登録・proof chain・試行台帳・機械 gate のどこからも再検証できない
  - **V5 = dev-wave 改善候補が予算に入らない (段 8)。** 本 wave は「ユーザー裁定の一次記録は
    worklog と `docs/archive/` にあり、decision が『裁定へ返す』と書いたままでも既に裁定済みの
    ことがある」を `DW-S01` へ足そうとしたが、`docs/dev-wave/**` は集約上限 25,200 bytes に
    張り付いており (追記後 25,427) 入らなかった。**上限引き上げは提案せず、追記を戻した。**
    既存義務を削って空けるのは安全義務の弱化にあたるため採らない。ユーザー裁定へ返す
  - **V4 = 段 8c 事前登録文書が stale** ({{T:t244-prereg-refresh}} として起票)。
    多世代化の条件を「還流設計の裁定」とだけ書いており、裁定が完了した現在は曖昧である。
    再事前登録の手続を持つ文書なので専用の裁定と変更単位で扱う
- **受入 (2026-08-04、worktree `dev-wave-t244-u2-na-bifurcation`、fc8f070 取り込み後):**
  `python3 tools/check_docs.py` = 違反なし。`python3 tools/run_tests.py` の全走 =
  **1 failed / 5430 passed / 19 skipped**。赤は
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  の 1 件だけで、**[T-407] の既知赤である** — `ruleops.py inventory` が非 UTF-8 blob
  (`output/insights/2026-08-03_t361-t362-cluster-probes/` 配下の probe 生出力、commit 9b0f044 で land)
  を strict decode して停止する。本 wave の差分は docs だけで同 blob に触れておらず、
  変更のない main checkout でも `ruleops.py inventory` は同じ rc=2 と同じ path で落ちることを実測した。
  よって repo 状態由来であり本差分の回帰ではない。
  `python3 tools/check_ai_provenance.py` は pre-commit HEAD (fc8f070) まで違反なし。
  wave commit を含む完了監査は commit 後に行う。**変異 matrix は対象外** —
  変更面が docs だけでコード・テスト・機械設定の差分がゼロであり、変異させる位置が存在しない。
  B-057 の述語 `validator_or_rejection_gate_changed` も成立しない

## 次の一手差分

### 更新

- [T-244] **P1・U2 を新 D で確定 → V1〜V4 と本体は未解決**: {{D:t244-u2-na-bifurcation}} が
  「実装が無いゆえの非適用」を cap-lift の失敗と定め、択一 3 の既裁定により P4 を無条件義務へ
  移した (無条件義務は 8 件)。状態の分類 (事実) と承認の可否 (判断) を分け、認定基準が無い間は
  状態を再分類せず承認を保留する。**V1 (`NOT_CLAIMED` の射程 = global 免責か per-run gate か) は
  ユーザー裁定待ち**で、P6 実装の裁定と同時に決める。
  V2={{T:t244-p6-semantic-contract}}、V3={{T:t244-cap-lift-receipt}}、V4={{T:t244-prereg-refresh}}
  を前提として追跡する。予算値は `Q >= 1 + 32R + E_min` の下限式から再導出する
  (R=1 でも Q は 33 以上、候補値 2 とは 1 桁違う)。**U3 (帰納段を踏む) の代償として
  accept/reject 漏洩が origin あたり 2 bit → 33 bit 超へ広がることを明示的に受け入れる。**
  据え置きは P6 が永久に発火せず U3 を実質無効にするため採らない。
  **P10 (予算値・origin authority・軸 (iii)) の 3 点は確定済みで、前提条件 10 件のうち
  満たされているのは P10 の 1 件だけである。**
  **本体は未解決** — `reflux-control` stage・origin ledger・5-bit IR・正準 emitter・
  witness normalizer・validation runner・enforcer・非干渉検査はすべて未着手で、
  D114 の承認上限 1 も変わらない。
  base: 77e62bdb00cb45d240921e41f62a190abacd7e4bdfb1ee3dc08a43304a344dbf

### 新規

- {{T:t244-p6-semantic-contract}} **P1・ユーザー裁定待ち (V2)**: P6 の「実装済み」を認定する
  意味的充足契約を定義する。正負 calibration の具体反例、非空の限界効果を示す変異、独立検査者を
  要求しない限り、空 handler と恒真 assert が列挙を満たす。P6 実装 wave の前提条件になる
- {{T:t244-cap-lift-receipt}} **P1・ユーザー裁定待ち (V3)**: 対象 revision・前提条件 10 件の
  status・裁定参照・witness hash を束縛する cap-lift receipt と、その consumer 結線
  (runbook / 事前登録 / journal / report / 層 3 / producer + completeness gate) を裁定する
- {{T:t244-prereg-refresh}} **P2・専用裁定待ち (V4)**: 段 8c 事前登録文書の generation 予算条項が
  stale である。凍結・再事前登録の手続に従い、改訂の可否と変更単位を決める
- {{T:t244-cap-lift-doc-pointer}} **P3・新規**: {{D:t244-u2-na-bifurcation}} の採番後に、
  `docs/phase3-s8c-autonomous-trial-runbook.md` と `docs/phase3.md` の cap-lift 記述へ実 D 番号の
  参照を入れる。本 wave では規則を逐語で書いたが、番号は fold 後にしか確定しないため入れられない
