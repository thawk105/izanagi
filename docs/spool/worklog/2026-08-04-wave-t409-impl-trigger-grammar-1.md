---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t409-impl-trigger-grammar
seq: 1
title: [T-409] 受理文法 v1 の実装は完成したが land しない — 並行 [T-428] の 5-bit wire 化が裁定前提を覆した (コード + docs、branch worktree-wave-t409-impl-trigger-grammar、変異 = 未実走)
---

## 本文

- **実装は全緑で完成したが、`DW-STOP` に従い land しなかった。** 走行中に並行 wave [T-428] が
  main へ着地し (`dbc0968` ほか)、trigger 軸の受理経路を固定 5-bit wire + 32 正準述語の閉集合へ
  置き換えていた。T-409 の裁定 5 件はいずれも「coder が自由文字列を hole へ書く」攻撃面を前提と
  しており、その面が構造的に消えた。親は不採用にせず、新事実付きでユーザー再裁定へ返す
  ({{T:t409-supersession-ruling}})。判断材料と逐語は
  `output/insights/2026-08-04_t409-impl-superseded/`
- **受理集合の関係を親が現物で確認した。** 32 正準述語 ⊊ 文法 v1 適合式 (無限) であり、main の
  membership 検査は本 wave の recognizer より厳密に強い。加えて main は build 境界で実 source の
  hole 1 行を読み、束縛 mask の正準述語と byte 完全一致を要求する。両方を置けば実効 gate は
  main 側になり、弱い方が「gate 済み」を名乗る経路だけが増える
- **二重化していない残余は 3 点だけだった。** (i) freeze 由来 literal 述語経路 (`system_gate` /
  `ident_all`) には membership が未適用で旧 blacklist のみ、(ii) 材料レポートの主張境界
  (finite-policy-selection / headline=false) は main に 0 件、(iii) 旧 artifact の再検査は main に
  相当機構なし。いずれも T-428 の閉集合を権威にすれば安く閉じる
- **段 6 で得た知見は [T-428] の設計にも効く** (再利用のため記録): 旧 WAL terminal を標準 attempt へ
  再発行するのは実測の捏造になる / `render_hole` の indent 前置で proposal 文字列と実 source bytes は
  一致しない / `parse_template_file` は text-mode 読みで CR を落とすため source 検査は binary で行う /
  protocol violation の診断を落とすと確定的な correctness-red を隠す / 歴史的 campaign ID は
  identity 束縛の追加で動くので束縛は materialize 経路に限定する / 汎用 diff 検疫の既定 scope に
  質の検査を足すと D48 決定 2 の分担 pin が壊れる
- **敵対レビュー 2 本で must-fix 15 件 (重複 3 組)、fix 3 巡で対応した。** 子の自己申告は 3 巡すべて
  「全 closed」だったが、親の実測は 27 failed + 48 errors → 12 failed → 0 failed と動いた。
  子の静的検査だけを緑と数えない規律が 3 回連続で効いた
- **焦点再レビューは closed 22 / partial 4 / regressed 0、残 must-fix 3 件と判定した。** うち 2 件
  (S8A sweep の grammar 未束縛・quarantine opt-in 未伝播) は `s8a_trigger_sweep.py` が
  `known_axes_freeze.json` の live sha pin 対象 (同 freeze 内 18 箇所) のため**本 wave の scope では
  閉じられない**。T-409 の設計は凍結 pin された producer に触れないと自身の scope を閉じきれない。
  残る 1 件 (marker 外側の条件分岐が未検査) は **main の `_require_materialized_trigger_predicate` にも
  同型で存在する** ため T-428 側の所見としても有効
- **fix 第 3 巡の子は 1 度成果ゼロで異常終了した。** `.done` 未生成・出力なし・repo の全 mtime が
  前巡どまりで編集ゼロを確認し、`DW-O01` に従い未完了と判定して再投入した。fix を重ねた実回数は
  3 巡で `DW-O16` の上限内
- **Pegasus scheduler の停止で wave を一度中断した。** gen_S が `INA` (229 QUE / 0 RUN) となり
  dispatch が queue-wait-timeout。ユーザー指示で停止し、回復後に指示で再開した。テスト実測は
  request 885111 / 887753 / 887759 / 887767 / 888336 / 888402 / 888420 / 888536
- **受入 (branch 48ec948、未 land):** 関連 20 ファイル `1285 passed, 12 skipped, 0 failed`。
  `check_docs.py` / `check_codex_agents.py` / `check_ai_provenance.py` (1057 件) は緑。
  **変異 matrix は未実走** — land しない判断のため事前登録 (M1-M18 + 正例 P1-P9) のまま凍結した
- 失敗として {{F:parallel-wave-premise-supersession}} を起票した

## 次の一手差分

### 更新

- [T-409] **P1・実装完了だが land せず・ユーザー再裁定待ち**: 実装は branch
  `worktree-wave-t409-impl-trigger-grammar` の 48ec948 に留置 (関連 20 ファイル全緑)。並行 [T-428] の
  5-bit wire + 32 正準述語で受理経路が置き換わり、裁定 5 件の前提が覆った。択一 3 件
  (実装の扱い / 受理権威の一本化 / 旧 artifact 再検査の要否) を
  `output/insights/2026-08-04_t409-impl-superseded/` §裁定パッケージ で返す。親の推奨は
  「実装を破棄し、二重化していない残余 3 点だけを小さい別 T で実装する」
  base: e667b5f91e264f0b26fea3c63d15894f71bca5f19ecaf5a3142a7fb68a146f6d

### 新規

- {{T:t409-supersession-ruling}} **P1・新規**: [T-409] の実装を破棄するか T-428 の上へ再統合するかを
  裁定する。材料は `output/insights/2026-08-04_t409-impl-superseded/`。裁定後、採用分の実装 T を起票する
- {{T:trigger-literal-membership}} **P2・新規**: freeze 由来 literal 述語経路 (`s1_direct_comparison` の
  `system_gate` / `ident_all`、`s1_verify_extime_calibration`) に T-428 の
  `trigger_gate_binding.is_canonical_predicate` を適用する。現状は旧 blacklist のみ
- {{T:layer3-claim-boundary}} **P2・新規**: 材料レポートに trigger の主張境界 (有限 policy 選択であり
  headline synthesis evidence ではない) を固定する。凍結 README の must-fix B-6 が未対応のまま
- {{T:trigger-legacy-artifact-classification}} **P3・新規**: 旧 trigger campaign artifact を 32 集合
  membership で再検査するか、`legacy-unclassified` のまま扱うかを決めて実装する
- {{T:aba-swap-window}} **P3・新規**: receipt 発行から compile までの間に source を差し替える ABA 窓を
  閉じる (build 専有 snapshot からのみ compile)。既存 build admission が既知未閉鎖と明記する軸横断の穴で、
  [T-409] 段 3 レンズ A が具体手順を構成した
