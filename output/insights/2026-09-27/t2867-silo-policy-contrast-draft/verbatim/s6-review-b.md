## 所見

1. **[real候補] [must-fix] endpoint 選択関数の流用可否を過大評価** — 草稿 `docs/silo-policy-generator-contrast-preregistration.md:350` は `select_endpoint` の同値規則を流用候補とする一方、草稿同 `:248-249` は「同値は slot の早い方」と定める。実コード `orchestrator/campaign/b5_generator_contrast.py:450-454` は `(-fitness_tps, value, b)` で選び、先に候補値で同値を破る。— **放置時の成果物影響:** 同点の系列で選ばれる endpoint と score が登録規則から変わる。— **推奨: 訂正。** 同値規則はそのまま流用できないと明記する。

2. **[real候補] [must-fix] n = 10 案に report の固定系列数が反映されていない** — 草稿 `docs/silo-policy-generator-contrast-preregistration.md:409,425` は n = 10 を選択肢にするが、起草 insight `output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md:37` は `pair_differences` を「系列 1..12」と正しく記す。実コード `orchestrator/campaign/b5_generator_contrast_report.py:103-110,572` は12系列を結合し、12件未満を欠測とする。— **放置時の成果物影響:** n = 10 を選ぶと、報告判定が欠測による判定不能になる。— **推奨: 訂正。** n = 10 案の発効前変更事項に report の系列数も明記する。

3. **[real候補] [must-fix] 「週上限が律速」と断定している** — 草稿 `docs/silo-policy-generator-contrast-preregistration.md:397-400` は57機会／週を仮定した直後に「律速は LLM の週上限である」と断定する。一次資料 `output/insights/2026-09-26/t2797-b5-cost-options/README.md:169-173` は「1週間で何機会回せるかは測れていない」と明記し、114 M token は429までの**使用量**である。— **放置時の成果物影響:** ユーザーが4〜13週を実証された所要期間に近い値として発効判断に使う。— **推奨: 訂正。** 「週上限が律速になりうる」に戻し、57機会／週は使用量を枠と仮置きした試算と示す。

4. **[real候補] [must-fix] 原提案1の node 上の待ちの引用元に算術矛盾がある** — 起草 insight `output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md:59` は24系列で「3.0〜6.1 h」と引用する。引用元 `output/insights/2026-09-26/t2797-b5-v2-prep/README.md:104` もその値を「実測の待ち × 系列数」と記すが、元の実測範囲 `output/insights/2026-09-26/t2797-b5-cost-options/README.md:52` は255〜1,021秒であり、24倍は**1.7〜6.8時間**。— **放置時の成果物影響:** job 1 を分ける費用上の利点を、根拠の異なる範囲でユーザーに示す。— **推奨: 訂正。** 3.0〜6.1時間の別の計算根拠を示すか、元実測の単純な24倍として直す。

5. **[real候補] [nit] job 準備費の出所表示が混在する** — 草稿 `docs/silo-policy-generator-contrast-preregistration.md:376` は「1 job 29〜35 s × 12 job」全体を実測と表示する。一次資料 `output/insights/2026-09-26/t2797-b5-cost-options/README.md:36-50` が実測したのは旧系列の**1 job あたりの差**で、12 job への適用は換算である。— **放置時の成果物影響:** 1系列の node 時間に含む348〜420秒を直接実測済みと誤読する。— **推奨: 訂正。** 「単価は実測、12 job 分は換算」と分ける。

6. **[real候補] [nit] 既知結果と過大主張の再掲が長い** — 草稿 `docs/silo-policy-generator-contrast-preregistration.md:316-333,335-341,435-457` は一次資料の点 ID・比、失敗条件、主張の限界を、草稿の§1・§7・§12とも重ねて記す。依頼の中心は事前登録、見積り、流用可否である。— **放置時の成果物影響:** 発効時に選ぶ規模と費用、実行規則の差分が読み取りにくくなる。— **推奨: 縮小。** §8は「既知結果を見て設計した」という開示と出所に絞り、§9・§13・§14の重複文を削る。判定規則と開示自体は残す。

7. **[refuted候補] [nit] 主表の算術と LLM 直列時間に数値誤りがある** — 起草 insight `output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md:78-86,94-98` の式を検算すると、1系列は4,270.92〜5,035.2秒、48系列と参照jobの合計は58.60〜69.09時間で、草稿 `docs/silo-policy-generator-contrast-preregistration.md:377-380` の丸めと一致する。240〜720機会×平均599秒も39.9〜119.8時間で、同 `:395` の40〜120時間と一致する。236〜513秒、407秒、510秒、251〜265秒、29〜35秒、×0.51〜0.60、22機会、255〜1,021秒、114 M・2.0 M・0.45 M token、偵察428〜564秒・小比較平均772秒、比0.836〜1.069と別jobの5〜7%も指定の一次記録と整合した。— **放置時の成果物影響:** これらの値と主表の score・発効判断は変わらない。— **推奨: 維持。**

## 総括

**must-fix:** endpoint の同値規則、n = 10 案の report 固定数、週上限の断定、3.0〜6.1時間の根拠を訂正する。

**削除・縮小:** 既知結果の詳細な再掲と、§1・§7・§12と重なる§9・§13・§14を縮める。LLM 直列時間の見積りの形は既にあり、追加不要。ファイル変更・テスト・計算投入は行っていない。