静的読取と算術の再計算による結果です。書込み・テスト実行・委任は行っていません。以下の closed は文書上の対応完了を意味します。

## 1. 所見ごとの対応表

参照：[草稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md)、[改版 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md)。

| 所見 | 判定 | 根拠と残件 |
|---|---|---|
| A-1 失敗理由の履歴への接続 | **partial** | 草稿 §3.2 は「この欄が埋まっていない」と撤回し、§13(2) に「既存の自系列の履歴の欄」に書く前提を追加。insight §4(P2) も修正済み。ただし「auditor…履歴に入らない」「検疫・構文・compile…だけ」はコードに反例がある。後述 F1。 |
| A-2 K の C++ 方策に骨格がない | **closed** | 草稿 §9.3 が「K_本文」「K_骨格」を分離し、「C++ から IR への変換は定義しない」。§9.2・U8 に分類の限界を明記。insight §6 の処置と一致。 |
| A-3 全 cell が同じ bytes・値 | **closed** | 草稿 §3.4 は「baseline…系列ごとに測る値」「critic…ありの cell だけ」と分離し、「偏らせないとは言えない」。insight §2・草稿 U2 も整合。 |
| A-4 「一度も表示されていない」 | **partial** | 草稿 §3.1 の「確認した固定の入力」「critic prompt と coder 入力の固定部分」は適切。しかし insight §2 の「その機会では該当語 0 件」は範囲が曖昧で、§7 の「正しい workload 名を表示されていない」も無限定のまま。後述 F3。 |
| A-5 参照 job の換算不一致 | **closed** | 草稿 §7.2 に「独立に導いた値とは扱わない」、insight §3 に「6,414〜7,119 秒」を追記。登録単価を維持した理由も明示されている。 |
| A-6 0.0276 の丸め | **closed** | 草稿 §7.2 は「0.0275」。insight §6 の訂正と再計算が一致。 |
| B-1 K と骨格の定義 | **closed** | 草稿 §9.3 は「整数型…の定数」を置換し、「bool・abort 要因・lock の action…はそのまま残す」と固定。K の分離と合わせ、元の未定義部分は解消。 |
| B-2 露出の同一性 | **closed** | 草稿 §3.4 の経路別記述と「弱めるとは限らず」が所見に対応。insight §2 も「cell 間の差を偏らせないとは言えない」。 |
| B-3 却下案・追加介入の再提示 | **partial** | 草稿 §6 から 6 cell 対比を削除し、§14 の確認事項を n・評定者に縮小。追加介入は §15 の「射程外」へ移した。ただし発効束には「規模 (4 cell / 6 cell、n)」が残る。後述 F4。 |
| B-4 fallback・固定 δ の意味 | **closed** | 草稿 §6 に「fallback を含む運用 score」「生成の力が同等だという意味ではない」と両方向の閾値効果を追記。insight §4(P4) も対応。 |
| B-5 最初の提案の分類・欠測 | **closed** | 草稿 §8(1) が「採否に応じて…(i) または (ii)」「全機会で読み取れる IR が無ければ欠測」と規定。insight §6 の処置どおり。 |
| B-6 地図の「族 3」 | **closed** | docs/README.md は「3 対比の Bonferroni 同時区間」。草稿 §6 の 1 族・3 対比、insight §6 の訂正と一致。 |

**closed 9 件、partial 3 件。regressed・not-addressed はありません。**

## 2. 派生値と量化の照合

**履歴の集計：すべて一致。**

許可された `llm-*/a*/coder-input.json` の `self_history` に限定して再集計しました。

| 項目 | 再集計値 |
|---|---:|
| coder 入力 | 249 件 |
| llm-cpp／llm-ir | 121／128 件 |
| 延べ履歴行数 | 1,638 行 |
| certified・digest なし・reject_subtype なし | 1,626 行 |
| rejected・digest なし・reject_subtype あり | 12 行 |

121＋128＝249、1,626＋12＝1,638。保存された `history-fields-log.md` と一致します。「なし」は **値が null** という意味で、対象 key 自体は全行に存在しました。延べ行数であり、一意な候補数ではありません。

**参照 job の換算：修正後の注記と一致、継承元の数値とは不一致。**

原資料の算式から、

- 下端：3 × (5 × 166＋5 × 255＋33)＝**6,414 秒＝1.7816667 h**
- 上端：3 × (5 × 203＋5 × 265＋33)＝**7,119 秒＝1.9775 h**

したがって **1.78〜1.98 h** は正しい値です。継承元記載の 6,264〜7,194 秒とは一致しません。依頼された登録単価 1.74〜2.00 h を使い続ける現在の注記は、この不一致を適切に開示しています。

**草稿 §7.2 の費用表：全行一致。**

下表は丸める前の値です。契約上限は `系列数 × 3.75＋3`、LLM 時間は `機会数 × 5.7〜8.0分` で再計算しました。

| 配置 | 系列／B 上限 | node 時間 | 契約上限 | 原提案機会 | LLM 直列 h | 4 親の理想 h |
|---|---:|---:|---:|---:|---:|---:|
| 4 cell・n＝3 | 12／120 | 16.50〜19.04 | 48 | 120〜360 | 11.4〜48.0 | 2.85〜12.0 |
| 4 cell・n＝4 | 16／160 | 21.42〜24.72 | 63 | 160〜480 | 15.2〜64.0 | 3.8〜16.0 |
| 4 cell・n＝5 | 20／200 | 26.34〜30.40 | 78 | 200〜600 | 19.0〜80.0 | 4.75〜20.0 |
| 6 cell・n＝4 | 24／240 | 31.26〜36.08 | 93 | 240〜720 | 22.8〜96.0 | 5.7〜24.0 |

草稿の小数第1位への丸めも一致します。これは登録単価による換算の照合であり、将来費用の実測ではありません。

**係数・感度値：一致。**

t 分布の自由度 2・3・4 の CDF を使い、分位点を独立に再計算しました。

| n | t 分位点 | k(n) | ln(1.03)/k(n) | ln(1.05)/k(n) |
|---:|---:|---:|---:|---:|
| 3 | 7.648803938 | 4.416039013 | 0.006693510 | 0.011048400 |
| 4 | 4.856657273 | 2.428328636 | 0.012172488 | 0.020092076 |
| 5 | 3.960786483 | 1.771317564 | 0.016687466 | **0.027544561** |

小数第4位では **0.0275**。他の表記値も一致します。n＝4 の最小片側 p＝1/16＝0.0625 も一致します。

**fallback とその他の量化：**

| 主張 | 照合 |
|---|---|
| 比較する両 cell の全組が fallback なら区間 [0,0] | **一致。** 共通の有効な stock median を S とすると、全対差が ln S−ln S＝0。平均・標本標準偏差とも 0。欠測優先に該当せず全 score が得られた条件で、登録式は [0,0] を返す。 |
| 評価・初期点の verifier digest が系列履歴に入らない | **一致。** `_append_seed_history` と `run_contrast_unit` の評価転記は digest を渡さず、`_append_history` の `out.get('verifier_digest')` は None。 |
| auditor の拒否は履歴に入らない／検疫・構文・compile だけが入る | **不一致。** `auditor-violation`・`auditor-uncertain` が反例。F1。 |
| 履歴に現れた評価結果は全部 certified | **確認した入力履歴の範囲では一致。** 本走全体で評価失敗がなかったという結論には拡張できない。F2。 |
| 固定入力の検索語 0 件 | **一致。** 指定6ファイルと a1 の critic prompt、指定された coder 固定欄で再確認。rr50 の2行・baseline abort率12.56%・projection一致も再現。 |
| 確認した1機会で該当語 0 件 | **入力全体については不一致。** 同じ a1 の `critic_diagnosis.avoid` に `read-heavy` がある。F3。 |

## 3. 修正で生じた／残った所見

**F1 — must-fix：失敗理由の返却経路を、依然として一括りにしている。**

場所：[草稿 §3.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md:133)、insight §2 の履歴表・§6 の A-1 裁定。

「schema と auditor…履歴に入らない」「検疫・構文・compile…だけ」「critic 診断だけ」には、次の反例があります。

- [auditor gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/auditor_gate.py:227) の通常の拒否・uncertain は `auditor-violation`・`auditor-uncertain`。
- この2種類は [round tool の除外集合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/tools/silo_policy_contrast_round.py:75) に入らず、`--record-reject` → `drive_contrast_record_reject` → `_append_history` を通り、拒否分類が coder に届きます。
- 逆に `_schema_reject` と、除外される `proposal-schema`・`auditor-gate`・`auditor-digest` は履歴に入りません。さらに `_new_results` は stock・seed・eval の `slot-result` だけを取るので、これらの `opportunity-end` は critic にも渡りません。

この混同は、規律3の欠落範囲と修復対象を誤って説明しています。

**直し方：** 通常の auditor veto／uncertain、schema・gate・digest エラー、評価・初期点の digest を分けて記述する。§13(2) は「初期点を含む評価結果」と不足する拒否経路の接続に限定する。評価転記の関数名も `_contrast_unit` ではなく **`run_contrast_unit`** に訂正する。

**F2 — should：入力履歴の集計から、本走全体の失敗不在を導いている。**

場所：[insight §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md:51)。

「評価の失敗が無かったので、欠落は本走の入力には表れていない」は集計範囲を超えます。coder 入力は提案前の履歴であり、最後の評価後に次の coder 入力が作られない場合、その評価は集計に現れません。schema 等の拒否も履歴から欠落します。また、digest が null という欠落自体は観測されています。

**直し方：** 「確認した coder 入力の履歴に現れた評価結果はすべて certified。評価失敗時の情報損失と本走全体の失敗有無は、この集計では確認していない」と限定する。禁止された結果を追加で読む必要はありません。

**F3 — should：露出の「0 件」の対象範囲が insight に引き継がれていない。**

場所：[insight §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md:60)・§7。

許可された [a1 の coder 入力](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/v1/rounds/llm-ir-1/a1/coder-input.json) の `critic_diagnosis.avoid` に、次の文字列があります。

> 「未測定の workload(ほかの skew や read-heavy など)へは一般化しません。」

これは実際の workload 名が正しく提示された証拠ではありませんが、「その機会では該当語0件」を入力全体に読むと反例です。§7 の「正しい workload 名を表示されていない」も、全機会の診断を調べた結論にはできません。

**直し方：** 草稿 §3.1 と同じく「critic prompt と coder 入力の固定部分」に限定し、§7 も「確認した固定入力には正しい名前・読み比率の明示欄がない」に揃える。

**F4 — should：発効束に却下済みの 6 cell が残っている。**

場所：[草稿 §14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md:418)。

「規模 (4 cell / 6 cell、n)」は、§3.3 の「本書の対比・確認事項には入れない」、D2322 項5、insight §6 の「確認事項を外し」と整合しません。対比定義を削除したため、この欄だけで6 cellを選んでも解析規則がありません。

**直し方：** 「規模 (4 cell、確定した n)」にする。6 cell は却下案の費用参考に留める。

**§13(2) と上位決定について：**

§13(2) は新しい gate・台帳には当たりません。既存の履歴欄はコードに実在し、T-2867 登録 §4.1 と D2256 項4 が約束した情報の接続修復です。新しい採否条件・検査機構・一般化は追加していません。後続実装では、D2256 の固定 reason code と bounded witness の契約も継承されます。

D2283、D2305 項3、D2212 項4の原決定とも照合しました。F4 の取り残しを除き、修正差分に n の確定・発効・実装・投入を既成事実にする変更はありません。

## 総括

**NO-GO — must-fix 1 件（F1）。**

数値は一致しています。残る修正は、失敗理由の経路の正確な記述と、集計・露出の量化範囲、発効束の6 cell表記です。