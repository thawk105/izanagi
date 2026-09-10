```text
- **[blocker] 6 層 scope が列挙されていない**
  - 反する逐語: 「完成条件を『consumer』一語にせず、producer / resolver / validator / selector / 材料 report / 試行台帳 sink を層ごとに列挙する」 (materials/t139-v1-v5-package.md:214-217)
  - 実装面のアンカー: s2-plan.md:92-104,233-296
  - **成果物影響**: producer、selector、材料 report、台帳 sink の caller と参照が無いため、certified 選択の受理集合は変わらず、T-139 verdict は材料 report / 試行台帳へ到達しない。

- **[blocker] 実際の consumer が 0 件で、未結線 leaf を完成扱いしている**
  - 反する逐語: 「必須 kill を 1 件も達成せず消費者も 0 件である」 (materials/D500.md:63-66)。「leaf 単体では『P3 充足』と名乗らない」 (docs/decisions.md:7202-7206)
  - 実装面のアンカー: s2-plan.md:181-184; orchestrator/preregistration/__init__.py:3-5,17-28; orchestrator/publication/report.py:214-231
  - **成果物影響**: `verify_receipt` は直接 vector からしか呼ばれず、必須 kill 数は 0 件のまま、certified 選択・材料 report・試行台帳の受理値は生成されない。

- **[blocker] producer → pilot → validator/consumer → 本走の順序が実行経路として保存されていない**
  - 反する逐語: 「着手順序は `producer → pilot → validator/consumer → 本走`」 (materials/D229.md:43-49)。「receipt の照合は投入後に置く」 (materials/D234.md:64-65)
  - 実装面のアンカー: s2-plan.md:150-184,296
  - **成果物影響**: 正例は producer / pilot を経ない synthetic vector だけで、`attempts[]`・`actual_runs[]` と実 qsub の因果参照が無いまま受理を主張するか、実 producer が gate に到達できず受理集合が空のままになる。

- **[blocker] D320 を根拠にした P1/P2 の切り直しは、承認済み admission 要件の緩和である**
  - 反する逐語: 「既存機構の撤去・緩和は個別裁定で行う」および「正しさゲート (verifier / admission / 変異検査)」は「対象外 (不変)」 (materials/D320.md:7-13)。「これらは semantic validator の必須責務として実装 wave が持つ」 (materials/record-items-v2-s4-s10.md:615-618)
  - 実装面のアンカー: s1-brief.md:61-75; s1-parent-classification.md:23-34; s2-plan.md:1-3,57-60,300-306
  - **成果物影響**: 現 tip だけの検査は H0 で使った `(family_root, ordinal)` を削除・再導入した H2 と別 `parent_series_id` を受理し、累積有意水準をリセットした試行を certified 候補・材料 report・台帳の受理集合へ混入させる。これはユーザー裁定なしに land できない。

- **[blocker] 独立再見積りでも 1 wave 完成の範囲に収まらない**
  - 反する逐語: 「堅牢化投資は、絶対規律と科学的妥当性に直接効くものだけを採る」 (materials/D205.md:3-8)。「部品だけが先に存在すると、部品を組み合わせただけの経路が gate を通ったように見える」 (materials/D264.md:10-15)
  - 実装面のアンカー: orchestrator/preregistration/approval_payload.py:1-587; orchestrator/preregistration/blobref.py:1-410; orchestrator/qualification/artifacts.py:1-1186; orchestrator/qualification/collector.py:1-1883; s2-plan.md:202-231,250-296
  - **成果物影響**: 静的再計算は、3 段 gate だけで production 2,750〜4,600 行、6 層接続込みで約 3,550〜6,200 行、tests 除外となり、親の 1,500〜3,000 行を支持しない。今 land できるのは `receipt_io.py` + `receipt_schema.py` の shape-only 非 gate 単位 (s2-plan.md:250-257) までで、D264 の 4 API を export して gate 完成とは記録できない。

- **[blocker] ユーザー裁定が必要な authority が残っている**
  - 反する逐語: 「解除条件の中身は本決定では定めない」および解除は「canonical decision」とする (materials/D292.md:3-8)。「どの段の受入条件に置くかはユーザー裁定へ返す」 (materials/D500.md:36-42)
  - 実装面のアンカー: s2-plan.md:177,202,312-314; s1-brief.md:12-13
  - **成果物影響**: `series_id` / `parent_series_id` authority、canonical registry root、intent discovery、manifest の exact grammar/path、`submit_pilot` の latch、Q2 の必須 kill 帰属、B1 の CMakeCache 解釈、6 層の所有 caller が未確定で、`attempts[]` の exact 被覆と `PreregBinding` を再導出できないため、certified 選択・材料 report・台帳参照を信頼できない。
```

## 総括

NO-GO — scope・consumer・authority が未結線で、承認済み admission 要件を落とした完成申告は実体と一致しない。pytest/build/run_tests.py は実走していない。