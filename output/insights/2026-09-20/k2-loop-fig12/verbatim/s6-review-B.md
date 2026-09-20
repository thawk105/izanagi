## 逐語照合表

必読射影はすべて読取可能でした。統合 patch の追加内容は現物 3 ファイルと一致しています。以下は指定 provenance の `drawn_items` **50 件全部**、`arrows` の label **7 件全部**、caption 全文の照合です。英訳・要約は「言い換え」とし、日付の値とその証拠の留保を区別しました。

| 表示文字列 | 稿の出所（節・表の行） | 判定 |
|---|---|---|
| K2 manual loop: data flow over three recorded rounds (schematic; no performance values) | §0.1、§0.3 | 言い換え |
| 2026-09-20-k2-manual-loop-three-rounds.md \| 2026-09-20 | 稿のファイル名・表題日付。後半は作図日の表示 | 一致 |
| K2 knowledge source (identical source bytes in all rounds) a measurement WAL from another machine; manifest receipt verified inside the job; declared as data, not instructions | §1.2、§2.2 巡1「受領証」、§5.1 | 言い換え。source bytes と入力 JSON bytes を混同していない |
| Parent session: typed projection builds input JSON; full inline sending and login preflight checks according to round records | §1.4末尾、§2.2各巡「投入前検査」、§4.3 | 言い換え。「記録による」を保持 |
| planner-v4 tools: [] (structural blockade); outputs direction and magnitude, no value, no mechanism | §1.4 planner 行、role frontmatter `tools: []` | 言い換え・frontmatter一致 |
| coder-v4-autonomous-k2 tools: [] (structural blockade); outputs a backoff literal and self-reports knowledge use and data boundary | §1.4 coder 行、role frontmatter `tools: []` | 言い換え・frontmatter一致 |
| Proposal file a backoff hole literal; known-value re-proposals are recorded, not counted as new values | §1.1「編集面」、§1.5「既知値の再提案」 | 言い換え |
| Evaluation: Pegasus compute-node job separate trace-enabled verify and trace-disabled bench builds and runs; campaign WAL terminal record | §0.1、§2.1注記、§2.5 | 言い換え。別 build・別 run を保持 |
| critic legacy role with Bash; reads digest and WAL; not B-4 material | §1.4 critic 行、冒頭限定3、role frontmatter | 言い換え・Bash実在 |
| Initial round proposal: 2026-09-16 evaluation: 2026-09-16 | §2.2 巡1、§2.7 巡1 | 日付一致。提案日の証拠区分は下記所見1 |
| planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context current_perf from the knowledge source's last bench record; whiteboard empty | §1.4、§2.2 巡1「入力」 | key一致・説明は言い換え |
| planner-1 decrease / medium | §2.2 巡1「planner-1」 | 一致 |
| coder-1 value 20 | §2.2 巡1「coder-1」 | 一致 |
| proposal-1 value 20 known value evaluated known value re-proposal, evaluated under the round authorization | §1.3 巡1、§2.2 巡1「判定」「評価」 | 言い換え |
| job 1216 verdict serializable; certified; no anomaly; stop: continue bnode host; legacy verify condition | §2.1 巡1、§2.5 巡1 | 一致・言い換え |
| critic-1 not attributable to any design choice same-campaign stock control first ( R0 ) | §2.2 巡1「critic-1」 | 言い換え。親下書きの same-job からの訂正は妥当 |
| Next round proposal: 2026-09-16 evaluation: 2026-09-18 | §2.7「proposal-2保存」、巡2 job | 日付一致。ただし **不一致：提案日は「記録による」の留保が脱落** |
| planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context current_perf and whiteboard from the previous evaluation | §1.4、§2.2 巡1「還流」 | key一致・説明は言い換え |
| planner-2 decrease / small | §2.2 巡1「還流」 | 一致 |
| coder-2 value 25 | 同上 | 一致 |
| proposal-2 value 25 outside the known set evaluated outside the known set | §2.2 巡1「還流」、巡2「入力」「投入2本目」 | 言い換え。巡1では未評価、巡2で評価という日付との組合せは正しい |
| job 4954 refused at preflight: job 4947 verdict serializable; certified; no anomaly; stop: continue the refused submission did not reach the campaign | §2.2 巡2「投入1本目」「投入2本目」、§2.1 | 一致・言い換え。拒否 job と評価 job は正しい |
| critic-2 not attributable; runs are not contemporaneous decrease, large; same-job stock control first ( R0 ) | §2.2 巡2「critic-2」 | 言い換え |
| After evaluation (not a round) proposal: 2026-09-18 evaluation: none | §0.1、§2.2 巡2「判定」、§2.7「proposal-3保存」 | 未評価は一致。**不一致：提案日の「記録による」が脱落** |
| planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context same measurement as the next column; no diagnosis key (typed path not yet implemented) | §1.4、§2.2 巡2「還流」、§2.3「変えた」行 | key一致・説明は言い換え |
| planner-3 decrease / medium | §2.2 巡2「還流」 | 一致 |
| coder-3 value 20 | 同上 | 一致 |
| proposal-3 value 20 known value not evaluated known value re-proposal; not evaluated by ruling | §2.2 巡2「判定」 | 言い換え |
| not evaluated | 同上 | 一致 |
| no critic | §0.1の巡の定義、§2.2 巡2の未評価 proposal-3 | 言い換え |
| Final round proposal: 2026-09-19 evaluation: 2026-09-19 | §2.7「診断入力の組立て→proposal-4」、巡3 job | 日付一致。ただし **不一致：生成日は記録依存という留保が脱落** |
| planner: current_perf, leading_indicators, whiteboard, knowledge_input + k2_critic_diagnosis coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context + k2_critic_diagnosis same measurement as the previous column, plus diagnosis from the previous critic verbatim | §1.4、§2.2 巡3「診断入力の組立て」「送付」、§2.3 | key一致・説明は言い換え。指定された実入力2本とも一致 |
| planner-4 decrease / large | §2.2 巡3「planner-4」 | 一致 |
| coder-4 value 10 | §2.2 巡3「coder-4」 | 一致 |
| proposal-4 value 10 outside the known set evaluated outside the known set; matches diagnosis candidate (self-reported advice, not causation) | §2.2 巡3「判定」、§2.3「一致した」 | 言い換え |
| job 10761 verdict serializable; certified; no anomaly; stop: continue same-job stock control not achieved | §2.1 巡3、§2.2 巡3「未達」 | 一致・言い換え |
| critic-3 not attributable again same-job stock control first ( R0 ) | §2.2 巡3「critic-3」 | 言い換え。R1以下の省略はあるが矛盾なし |
| m1: round-1.evaluation → round-2.parent measurement reflux: current_perf and whiteboard | §0.1、§2.2 巡1「還流」 | 一致・言い換え |
| m2a: round-2.evaluation → after-round-2.parent measurement reflux | §2.2 巡2「還流」 | 一致・言い換え |
| m2b: round-2.evaluation → round-3.parent measurement reflux: current_perf and whiteboard | §0.1、§2.3「変えた」行 | 一致・言い換え |
| d1: round-2.critic → round-3.parent diagnosis reflux: typed path, identical for planner and coder k2_critic_diagnosis: attribution, recommend, avoid, uncertainty, data_boundary, source_sha256 | §1.4、§2.2 巡3「診断入力の組立て」 | 一致。実 diagnosis の6 keyと一致し、両入力の診断内容も同一 |
| a1: round-1.critic → round-2.parent no typed path: diagnosis not delivered | §2.2 巡1「閉じていないもの」 | 言い換え |
| a2: round-2.critic → after-round-2.parent no diagnosis key | §2.2 巡2「還流」「判定」 | 言い換え |
| a3: round-3.critic → no destination no further proposal in the recorded scope | §0.1、冒頭「成立範囲」 | 言い換え |
| same-job stock control not achieved; ruling pending ( T-2795 ) | §2.2 巡3「未達」、§3項2 | 一致・言い換え |
| Solid: measurement reflux; dashed: diagnosis reflux; dotted with cross: absent path; thin: within-column flow; dashed box: not a round. | 経路の意味は§0.1・§2.2。線種の対応は作図者が定義 | **稿に無い：線種の凡例。表示上の定義として妥当** |
| R6: no instruction-like content (self-reported). data-boundary check: role self-report that external input contained no instruction-like strings; coder as a structured field, planner in uncertainty prose, critic in a trust-boundary section; not a mechanical gate | 冒頭限定4、§1.4、§2.4 | 言い換え。構造化 field の正確な名前は省略 |
| Read from the frozen results note 2026-09-20-k2-manual-loop-three-rounds.md; no performance values are drawn and the three runs are not compared. | 冒頭凍結宣言、§0.3、§2.1注記 | 言い換え。「数値を描かない」は本図の方針 |
| Certified means the trace-enabled verify run found the trace serializable with no anomaly; it is not a performance certification. | 冒頭限定5、§2.5 | 言い換え |
| Discipline-six marks are role self-reports, not a mechanical gate; causal effects of knowledge or diagnosis are not claimed. | 冒頭限定2・4、§2.3・§2.4 | 言い換え |

`arrows[].label` も個別に照合しました。

| 表示文字列 | 稿の出所（節・表の行） | 判定 |
|---|---|---|
| m1: measurement reflux: current_perf and whiteboard | §2.2 巡1「還流」 | 言い換え |
| m2a: measurement reflux | §2.2 巡2「還流」 | 言い換え |
| m2b: measurement reflux: current_perf and whiteboard | §2.3「変えた」行 | 言い換え |
| d1: diagnosis reflux: typed path, identical for planner and coder | §1.4、§2.2 巡3「診断入力の組立て」 | 言い換え |
| a1: no typed path: diagnosis not delivered | §2.2 巡1「閉じていないもの」 | 言い換え |
| a2: no diagnosis key | §2.2 巡2「還流」 | 一致・言い換え |
| a3: no further proposal in the recorded scope | 冒頭「成立範囲」、§0.1 | 言い換え |

実測矢印は描画上3本ですが、m2a・m2bは同じ巡2実測からの分岐です。稿の「実測還流2回」と矛盾しません。親 brief の「2本」は段4下書きで3本に具体化されており、caption はこの数え方を説明しています。

| caption の各文 | 稿の出所 | 判定 |
|---|---|---|
| Figure 12. | 図番号は今回の追加物 | **稿に無い：図番号。問題なし** |
| Data flow of the K2 manual synthesis loop over three recorded rounds, read from the frozen results note 2026-09-20-k2-manual-loop-three-rounds.md. | 表題、凍結宣言、§0.1 | 言い換え |
| In each round the parent session projects typed JSON inputs (planner: current_perf, leading_indicators, whiteboard, knowledge_input; coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context) to planner-v4 and coder-v4-autonomous-k2; the proposal is one backoff literal evaluated by one Pegasus compute-node job with separate trace-enabled verify and trace-disabled bench builds and a campaign WAL terminal record; critic reads the digest and the WAL. | §0.1、§1.1、§1.4 | 言い換え。別runは図のlane説明で補われる |
| Measurement reflux occurred twice (the first evaluation into the second proposal inputs; the second evaluation into the inputs of an unevaluated proposal and of the third round) and diagnosis reflux once (the second critic into the third-round inputs as the typed key k2_critic_diagnosis with fields attribution, recommend, avoid, uncertainty, data_boundary, source_sha256, identical for planner and coder). | §0.1、§2.2 巡2・3、§2.3 | 言い換え。分岐・回数・exact 6 fieldが一致 |
| The unevaluated proposal, generated without a diagnosis key, re-proposed a known value. | §2.2 巡2「判定」 | 言い換え |
| The planner and coder role definitions declare no tools (structural blockade); critic is a legacy role with Bash access, so these rounds are not material for the B-4 leak-control ablation. | §1.4、冒頭限定3 | 言い換え。3 roleのfrontmatterとも一致 |
| Certified means only that the trace-enabled verify run found the observed trace serializable with no anomaly; it is not a performance certification and not a choice among candidates. | 冒頭限定5、§2.5 | 言い換え |
| Discipline-six marks are role self-reports that external inputs contained no instruction-like strings; their form differs by role and they are not a mechanical gate. | 冒頭限定4、§2.4 | 言い換え |
| No causal effect of the knowledge source or of the diagnosis on the proposed values is claimed: each condition was launched once, without a control. | 冒頭限定2、§2.3 | 言い換え |
| The same-job stock control was not achieved and awaits a ruling; proposal values are backoff literals, not results. | §2.2 巡3「未達」、§1.1、§3項2・6 | 言い換え |
| This is a schematic of recorded data flow; no performance values are drawn and the three runs are not compared. | §0.3、冒頭限定1 | 言い換え＋本図の表示方針 |

## 所見 (must-fix)

1. **提案日の表示が、記録依存という稿の留保を落としている。**
   箇所：`tools/plotting/plot_k2_loop_flow.py:269`、`tools/plotting/k2_loop_flow_2026-09-20.json:156`。段4下書きにも同じ不足があります。

   > `add(cid, 'column', col['label'], 'proposal:', col['date_proposal'], 'evaluation:', col['date_evaluation'] or 'none')`

   稿§2.7はproposal-2・3の同日性、proposal-4の生成日を明示的に「各巡の記録による」と限定しています。図の親laneにある `according to round records` はinline送付・preflightに係り、日付の留保にはなっていません。
   影響：図・provenance上で、提案日と機械ログで確認した評価日が同じ証拠強度に見えます。
   推奨fix：列見出しを `proposal date (reported)` とするか、日付に明確に係る脚注を追加し、独立期待文字列にも反映する。

2. **`not-a-round` 固有制約を負例が踏んでいない。**
   箇所：`orchestrator/tests/test_plot_k2_loop_flow.py:129`、生成器`:201`・`:202`。

   > `elif case=='not-a-round-evaluation': raw['columns'][2]['cells']['evaluation']=copy.deepcopy(c['evaluation'])`
   > `_require(cells['proposal']['evaluated'] == evaluated, 'evaluated mismatch')`

   この負例は `evaluated=false` を残したままevaluationだけを追加するため、`:201`で停止します。`:202`のkind制約を検証していません。critic/dateとの整合にも専用負例がありません。
   影響：未評価列の制約が弱まっても、該当テストは緑を維持し、段4の受入根拠になりません。
   推奨fix：evaluation・evaluated・critic・dateを相互整合させた未評価列を作り、kindだけを違反させる。critic/date整合も独立した負例を追加する。

3. **M7用fixtureがlayout以外の拒否理由を同時に作っている。**
   箇所：`orchestrator/tests/test_plot_k2_loop_flow.py:178`・`:223`、生成器`:540`・`:541`。

   > `first.set_text('planner-1')`
   > `check_figure_layout(fig, layout)`
   > `_drawn_items(data, layout)`

   `collision` は元Textを短縮するので、layout検査を削除しても `_drawn_items` がJSONとの差で拒否します。現テストは例外型の違いによって赤になりますが、「検査を外すと公開される」という登録された単一理由ではありません。
   影響：M7のKILLEDをpublisherのlayout検査の実効性だけに帰属できません。
   推奨fix：元Text・期待文字列を維持し、別の登録済みTextの座標移動など、文字列照合を通るlayout衝突を使う。

## 所見 (should)

1. **T5の「fileを残さない」assertは出力経路を通らず恒真。**
   箇所：`orchestrator/tests/test_plot_k2_loop_flow.py:187`・`:194`・`:206`。

   > `PLOT.check_figure_layout(fig,layout)`
   > `assert not list(tmp_path.iterdir())`

   `tmp_path`を検査関数に渡しておらず、その関数は保存もしません。
   影響：escape・arrow-crossing時の公開抑止を検証したように読めますが、実際のpublisher負例はoverlapのみです。
   推奨fix：T5は幾何検査に限定し、publisherについて3種類の衝突を通す負例を別途置く。

2. **規律6のcoder自己申告の正確なfield名が表示されない。**
   箇所：`tools/plotting/plot_k2_loop_flow.py:300`、JSON末尾 `discipline6.definition`。

   > `coder as a structured field, planner in uncertainty prose`

   意味は稿と整合しますが、親brief P3の `instruction_like_content_detected=false` までの展開は満たしていません。
   影響：図だけから実入力・出力のどのfieldを確認するか追いにくくなります。
   推奨fix：固定templateかcaptionに `data_boundary_report.instruction_like_content_detected=false` を明記する。自由文の `=` 禁止を緩める必要はありません。

3. **受理する矢印構造と固定captionの回数が束縛されていない。**
   箇所：`tools/plotting/plot_k2_loop_flow.py:224`・`:595`。

   > `_require(type(d['arrows']) is list and d['arrows'], 'arrows array required')`
   > `'Measurement reflux occurred twice ... and diagnosis reflux once ...'`

   実在endpointを持つ矢印の削除・kind変更をschemaは許し、captionは固定の回数を述べます。既定入力は正しいため、現成果物の不一致ではありません。
   影響：別の受理JSONでは図・arrowsとcaptionが食い違います。
   推奨fix：この凍結図用の矢印ID・kind・from/to集合を検証するか、captionが依存する構造を明示して検証する。稿からの再計算は不要です。

## 所見 (nit)

1. **M4の枝を含めると実行対象は12変異。**
   箇所：`s4-adjudication.md`「変異事前登録」の「登録10件」。M4a/b/cを別々に実走するため、集計は「10群・12変異」と書くと明確です。影響は台帳集計のみ。推奨fix：母数表記を統一する。

2. **既知集合外の説明が重複。**
   箇所：`tools/plotting/plot_k2_loop_flow.py:285`、JSON`:180`。固定語とsublabelがともに `outside the known set` を出します。図の文字量だけが増えます。推奨fix：sublabelの重複を除く。

## 拒否条件の実装・test 対応表

以下、`G`＝`tools/plotting/plot_k2_loop_flow.py`。nodeidの共通接頭辞は `orchestrator/tests/test_plot_k2_loop_flow.py::` です。

| 裁定の拒否条件 | 実装の関数:行 | 負例testのnodeid | 恒真・不足の判定 |
|---|---|---|---|
| 未知key | `_keys` G:52、各descriptive呼出し | `test_t3_unknown_key_is_rejected[各15位置]` | 実関数経由。充足 |
| 不足key | `_keys` G:52 | `test_t3_invalid_json_without_drawing[missing-key]` | planner.direction欠落のみ。共通関数は踏むが全階層の不足は未網羅 |
| 重複key | `_pairs` G:61、load G:133 | `test_t3_json_parser_rejects_noncanonical_values[duplicate]` | 充足。parser全階層へ適用 |
| NaN・±Infinity | `_constant` G:69 | 同上 `[nan/infinity/negative-infinity]` | 充足 |
| schema固定 | `load_flow` G:135 | 専用なし | 実装あり・負例不足 |
| ISO日付 | `_date` G:106 | 専用なし | 実装あり・負例不足 |
| reference_ids形式・重複・未使用 | `load_flow` G:142・143・238 | 専用なし | 実装あり・負例不足 |
| roles件数・順序・name・definition_path | `load_flow` G:156–160 | frontmatter `[missing-file]` はfile不在のみ | 固定path不一致・順序等の負例不足 |
| tools_none bool | `_bool` G:111、G:161 | 専用なし | 実装あり・型負例不足 |
| tools_none ⇔ frontmatter | `_tools_none` G:115、load G:163 | `test_t2_tools_none_mismatch_is_rejected[0/1/2]` | 充足 |
| tools行なし・重複・不正配列・file不在 | `_tools_none`、load G:162 | `test_t2_role_frontmatter_binding[missing-line/missing-file/non-array/duplicate-line/changed-tools]` | 実関数経由。充足 |
| lanes件数・順序・role表示一致 | `load_flow` G:165–171 | 専用なし | 実装あり・負例不足 |
| planner_keys完全一致 | `load_flow` G:144 | `test_t3_invalid_json_without_drawing[planner_keys]` | 末尾欠落で検証 |
| coder_keys完全一致 | 同上 | 同上 `[coder_keys]` | 同上 |
| diagnosis_fields完全一致 | 同上 | 同上 `[diagnosis_fields]` | 同上。実物のkey集合とも一致 |
| columns件数・順序 | `load_flow` G:175–178 | 専用なし | 実装あり・負例不足 |
| direction enum | `_enum` G:102、G:190 | `test_t3_invalid_enum_is_rejected[direction]` | 充足 |
| magnitude enum | `_enum`、G:191 | 同上 `[magnitude]` | 充足 |
| column kind enum | `_enum`、G:179 | 同上 `[column-kind]` | 通常は踏む。変異後は後段整合検査がmask |
| arrow kind enum | `_enum`、G:231 | 同上 `[arrow-kind]` | load_flowでは独立に踏む |
| verdict enum | `_enum`、G:207 | 同上 `[verdict]` | 充足 |
| stop enum | `_enum`、G:208 | 同上 `[stop]` | 充足 |
| value int・1..1000 | `load_flow` G:194–196 | `test_t3_invalid_json_without_drawing[non-int/bool-value/low-value/high-value]` | coder側だけ変更。coder/proposal一致検査も拒否するため原因非独立 |
| coder-proposal値一致 | `load_flow` G:197 | 同上 `[value-mismatch]` | 単独理由で踏む |
| known_value/evaluated bool | `_bool`、G:198 | 専用なし | 実装あり・型負例不足 |
| evaluated ⇔ evaluation非null | `load_flow` G:200–201 | 同上 `[evaluated]` | 片方向を検証 |
| not-a-roundのevaluation禁止 | `load_flow` G:180・202 | 同上 `[not-a-round-evaluation]` | **不足：G:201で先に拒否** |
| evaluationとcritic/dateの整合 | `load_flow` G:202–203 | 専用なし | **負例不足** |
| 巡3だけhas_diagnosis | `load_flow` G:187–188 | 専用なし | 実装あり・負例不足 |
| certified/anomalies_noneがtrue | `load_flow` G:209 | 専用なし | 実装あり・負例不足 |
| job数字列・重複 | `load_flow` G:210–214 | 専用なし | 実装あり・負例不足 |
| instance形式・重複 | `load_flow` G:216–222 | 専用なし | 実装あり・負例不足 |
| arrow from実在 | `load_flow` G:232 | 同上 `[arrow-from]` | 充足 |
| arrow to実在 | `load_flow` G:233 | 同上 `[arrow-to]` | 充足。non-absentのnull専用負例はない |
| arrow id重複 | `load_flow` G:228–230 | 専用なし | 実装あり・負例不足 |
| anchor形式・実在 | `_anchor` G:88 | 同上 `[anchor/absent-anchor]` | 充足 |
| anchor一意 | `_anchor` G:98 | `test_t3_non_unique_anchor_is_rejected` | 実稿copyの見出し重複。充足 |
| 自由文数量 | `check_display_text` G:73、load G:235 | T3 `[percent/throughput/latency/assignment]`、`test_t4_free_text_rejects_quantities[...]` | 充足。NFKC・ID全token照合あり |
| caption_source固定path | `load_flow` G:137 | T3 `[caption-source]` | 充足 |
| prefix | `_figure_number` G:246 | `test_t8_cli_rejects_invalid_prefix` | 充足。同じ関数をCLIとpublisherで呼ぶ |
| Text相互交差 | `_intersection` G:435、check G:464 | `test_t5_overlap_is_a_layout_error` | 実Figure。幾何検査は有効 |
| Text内包 | `_contains` G:439、check G:461 | `test_t5_escape_is_a_layout_error` | 実Figure。幾何検査は有効 |
| 矢印線分×Text | `_segment_intersects_box` G:419、check G:489 | `test_t5_arrow_crossing_text_is_a_layout_error` | slab clippingで実交差を計算。bbox同士の近似ではない |
| 保存前layout検査 | `_publish_outputs` G:540 | `test_t6_publish_runs_layout_check` | 呼出しあり。ただしM7 fixtureが複数理由 |
| drawn_itemsとJSON一致 | `_drawn_items` G:500、publish G:541 | `test_t7_drawn_items_match_flow` | JSONから独立期待を組立て。描画後JSON変更も拒否 |
| 入出力・生成器・role hash | `build_provenance` G:513 | `test_t7_cli_outputs_and_independent_hashes`、`test_t7_caption_source_hash_is_independent` | 独立hashlib照合あり |
| 既存出力拒否 | `_destinations` G:530、publish G:557 | `test_t7_cli_outputs_and_independent_hashes` | 再実行rc・bytes不変を検証 |
| 保存途中失敗時のcleanup | `_publish_outputs` G:560–566 | 途中I/O失敗の専用負例なし | 実装あり・fault injection不足 |
| 着地bundle・caption・README hash | test側:358以降 | `test_landed_fig12_bundle_when_present` | 欠落は失敗。role現hashを要求しない設計も裁定どおり |

正しさ境界は維持されています。稿本文は `source_anchor` の見出し数確認とSHA-256記録に使われ、提案値・性能・正しさ判定を再計算していません。`certified` の意味はcaptionで性能認証・候補間選択から明確に分離されています。

layoutは自前polylineなので曲線近似の粒度問題はありません。全線分をpixel座標へ変換して全Text bboxと照合し、自矢印のlabelも除外しません。labelは格子下に配置されています。layoutと表示文字列の検査はmkdir・一時file作成より前で、保存途中例外では作成済み公開fileと一時fileを削除します。

provenanceの入力5本・生成器のhashは現bytesと一致し、scratchのPNG/PDFも記録hashと一致しました。`outputs.path` は生成時の `probe-k2fig12/` を記録しており、scratchへの移動先ではありません。最終着地時には最終prefixで再生成する必要があります。

meta-testは静的に適合しています。`:374`の `__main__` 以下に `pytest.main` があり、plain-runner検出条件を満たします。subprocessは唯一の `_cli` に `PYTHONDONTWRITEBYTECODE: '1'` が直書きされています。新test名は `test_*.py` の収集対象で、verifier/oracle除外表の条件には該当せず、skip/xfailもありません。追加探索したskip分類検査にも新たに抵触する呼出しはありません。pytest・変異の実測は行っていません。

## 変異の単一理由性

nodeidの接頭辞は前表と同じです。以下は静的判定で、実測のKILLED/SURVIVEDではありません。

| 変異 | 現物の位置 | kill対象nodeid | 単一理由性 |
|---|---|---|---|
| M1 | `_enum` G:102 | `test_t3_invalid_enum_is_rejected[direction/magnitude/arrow-kind/verdict/stop]` | この5種はload_flow内に同値拒否層なし。`[column-kind]` はG:202にも拒否される。例外文言変更で赤にはなるが単独の受理拡大検知ではない |
| M2 | `_keys` G:52 | `test_t3_unknown_key_is_rejected[top]`等 | 余分なkeyは後段で使われず、完全一致を緩めれば受理される。変異は `expected <= actual` と明記すること。逆向きの部分集合化は未知keyを引き続き拒否し、目的を検証しない |
| M3 | `check_display_text` G:73 | `test_t4_free_text_rejects_quantities[...]` | 単一関数の直接呼出し。早期returnを他層がmaskしない |
| M4a | `_intersection` G:435 | `test_t5_overlap_is_a_layout_error` | fixtureの同座標Text交差が主理由。Text短縮はこの直接layoutテストでは表示内容検査を呼ばないのでmaskしない |
| M4b | `_contains` G:439 | `test_t5_escape_is_a_layout_error` | figure外へ移したText。外側では他Text・矢印と交差しないため独立性あり |
| M4c | `_segment_intersects_box` G:419 | `test_t5_arrow_crossing_text_is_a_layout_error` | Text所有領域をcanvasへ変更して内包違反を回避。m1縦線を横切るため狙う拒否面は明確 |
| M5 | `build_provenance` G:520 | `test_t7_caption_source_hash_is_independent` | caption_sourceのsha値だけを変更すれば独立hashで不一致。inputsを別途検査してもこの誤記録を隠さない |
| M6 | `load_flow` G:163 | `test_t2_tools_none_mismatch_is_rejected[0/1/2]` | bool反転後に同じ宣言を再検査する層なし。単独理由 |
| M7 | `_publish_outputs` G:540 | `test_t6_publish_runs_layout_check` | **不適合。G:541が同じfixtureを表示文字列不一致で拒否。現testは例外型差で赤になり得るが、登録された「検査なしで公開」の理由ではない** |
| M8 | `_figure_number` G:247–248 | `test_t8_cli_rejects_invalid_prefix` | 同じ述語をCLI・publisherが共有するため、関数内述語の変異なら両方に効く。CLI側呼出しだけを消す変異はpublisherでmaskされる |
| M9 | `_anchor` G:98 | `test_t3_non_unique_anchor_is_rejected` | `==1`を`>=1`へ変えると複製見出しが受理される。他の意味検査はない |
| M10 | `_drawn_items` G:502 | `test_t7_drawn_items_match_flow` | test末尾は描画後にJSONを変え、`build_provenance`を直接呼ぶ。照合削除を別層がmaskしない。publisherとprovenanceの二重呼出しは同じ関数なので関数内変異なら問題なし |

M1のcolumn-kindとM7について、**再拒否される＝必ずSURVIVEDではありません**。このtest群は例外文言・例外型も検査するため、別理由の拒否でも赤になります。変異台帳では「受理拡大を検出したkill」と「拒否理由が変わっただけのkill」を区別する必要があります。

## 総括

**NO-GO。must-fix 3件。**
提案日の証拠留保、未評価列制約の独立負例、M7の単一理由性を修正してください。
値・判定・還流先・role遮断・正しさ境界は稿と整合し、hashも現物と一致しました。
線分交差検査と保存前検査は実装されています。
判定は静的レビューによるもので、pytest・変異実測の緑は主張しません。