静的照合と算術の再計算による所見です。テスト・計測・書込みは行っていません。以下「草稿」はレビュー対象、「insight」は改版 insight を指します。

1. **must-fix — 構造化された失敗理由が、現行の対照経路では coder まで届かない**

   **場所:** 草稿 §3.2・§13・§16、insight §2・§4(P2)。

   **主張:** 自系列履歴が verifier digest と拒否理由を critic と独立に運ぶため、critic を外すだけで規律3を保てる。

   **根拠:** `make_policy_coder_input` の出力 schema だけを見ると成立して見えますが、その上流で欠落しています。

   - [p3_s4_loop_policy.py:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/p3_s4_loop_policy.py:509) は `verifier_digest` を生成する一方、`_slot_observation`（687行以降）はそれを返しません。系列履歴への転記も [同ファイル:906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/p3_s4_loop_policy.py:906) の `outcome`・`variant`・`logical_slot`・`measurement_campaign_id` だけです。初期点も845行で同様です。[278行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/p3_s4_loop_policy.py:278) の `out.get('verifier_digest')` は、これらの経路では `None` になります。
   - [silo_policy_contrast_round.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/tools/silo_policy_contrast_round.py:51) の schema 拒否は `opportunity-end` にだけ記録されます。[76行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/tools/silo_policy_contrast_round.py:76) も `proposal-schema`・`auditor-gate`・`auditor-digest` を `--record-reject` の対象から除外しています。coder 入力はこの台帳を読まず、`policy_history.jsonl` だけを読みます。

   **放置した場合:** C-off で構造化された失敗理由の返却まで失われ、登録した不変条件と推定対象が誤ります。

   **直し方:** 「現状で届く」を撤回し、初期点・評価結果・投入前拒否を系列履歴へ接続する修復を §13 の発効前提に明記してください。新しい台帳を作る必要はありません。

2. **must-fix — 全 arm の K に対して、IR の骨格比較を定義できていない**

   **場所:** 草稿 §9.2・§9.3・§13(5)。

   **主張:** K は T-2867 の全 arm の方策を含み、候補と K の「IR の定数を置換した骨格」を機械的に比較する。

   **根拠:** [p3_s4_loop_policy.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/p3_s4_loop_policy.py:151) は C++ 形を `implementation, ir = coder['implementation'], None` と読みます。[silo_policy_ir.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/silo_policy_ir.py:4) も “Rendering is a subset of policy-C++ v1” と明記しています。C++ 方策一般について、対応する IR 木は存在するとは限りません。

   **放置した場合:** K の一部に比較対象の骨格がなく、「既知の骨格の新しい定数／新しい骨格」の分類が実装者の事後判断になります。

   **直し方:** 全 arm の本文照合用集合と、IR が存在する方策の骨格照合用集合を分け、分類の射程を明記してください。C++ も骨格比較するなら、その変換・比較規則を発効前に定義する必要があります。

3. **should — 「全 cell に同じ bytes」は baseline と評価材料には成立しない**

   **場所:** 草稿 §3.4 冒頭、insight §2 結論。

   **主張:** write-heavy の情報を全 cell に同じ bytes・同じ値で運ぶので、cell 間の差の偏りにはならない。

   **根拠:** [T-2867 登録:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/silo-policy-generator-contrast-preregistration.md:220) は「各系列の job 1 で 1 session」。[round tool:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/tools/silo_policy_contrast_round.py:160) は、その系列の `stock["fitness_tps"]` と `stock["abort_rate_pct"]` を渡します。候補の観測も系列ごとに異なります。

   **直し方:** 同一 bytes といえる段階Dの射影と、同じ生成規則で系列ごとに測る baseline・評価材料を区別してください。「同じ値だから偏らない」という根拠も削除してください。

4. **should — 「一度も表示されていない」は棚卸しの範囲を超える**

   **場所:** 草稿 §3.1、insight §1・§2・§7。

   **主張:** 現行 S3 の LLM×IR は正しい workload 名を一度も表示されていない。

   **根拠:** 保存された走査は [inventory-commands.txt:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/verbatim/inventory-commands.txt:12) の6ファイルと、[22行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/verbatim/inventory-commands.txt:22) の `llm-ir-1/a1` の一部です。一方、[make_policy_coder_input:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/p3_s4_loop_policy.py:359) は任意の6文字列からなる `critic_diagnosis` を載せ、その語彙を制限していません。

   **直し方:** 「確認した固定入力には正しい名前・読み比率の明示欄がない」「確認した1機会では該当語0件」と限定してください。全系列・全機会の診断まで走査した結果とは書けません。F727・F985 型の走査範囲／量化の問題です。

5. **should — 単価の継承元に算式と値の不一致がある**

   **場所:** 草稿 §7.2、insight §3。問題の出所は T-2867 実装 insight §5。

   **主張:** 参照3 job の換算単価は 1.74〜2.00時間。

   **根拠:** [実装 insight:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md:115) の式は  
   `3 × (5 × 166〜203 + 5 × 255〜265 + 33)`  
   ですが、再計算は **6,414〜7,119秒＝1.782〜1.978時間**です。同じ行の **6,264〜7,194秒**とは一致しません。

   **直し方:** P5 の転記自体は依頼された登録単価どおりです。その値を維持する場合も、改版 insight に「継承元の換算式と値に不整合あり」と注記し、独立に再導出済みとは扱わないでください。

6. **nit — n=5、ln(1.05) の参考上限の丸め**

   **場所:** 草稿 §7.2、252行。

   **主張:** `s_d` 上限は `0.0276`。

   **根拠:** 同節の定義を再計算すると、`k(5)=1.771317564`、`ln(1.05)/k(5)=0.0275445607` です。小数第4位への四捨五入は **0.0275**です。

   **直し方:** `0.0275` に訂正してください。

照合して一致：

- 指定単価からの費用表・契約上限・LLM時間の計算
- k(3〜5)、δ＝ln(1.03) に対する s_d 上限、最小片側 p＝1/16
- rr50 の固定文脈、指定6ファイルの検索語0件、空の workload 見出し
- projection の binary・scope、baseline abort率12.56%
- 段階Dの abort0 abort率約0.78
- 自系列履歴に throughput を載せない構造と、候補性能の critic 経由の伝達
- verify tag、初期点、固定16点、degenerate_policy
- D2212項4、D2272項5、D2283、D2305項3、D2322項5
- T-2867 登録の指定節番号と継承内容
- coder の tool なし・任意の critic_diagnosis の入力契約

HARKing の開示と保存された棚卸し出力には矛盾を見つけませんでした。ただし、保存出力だけでは「他の結果を開いていない」という閲覧履歴全体は証明できません。

## 総括

**NO-GO — must-fix 2件。** 失敗理由の返却経路と、K の骨格比較の定義を直す必要があります。