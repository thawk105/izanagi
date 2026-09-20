## 対応表

必読10ファイルは読取可能でした。patch の全42 hunk の適用後内容は現物と一致し、provenance の稿・生成器・入力 JSON の SHA-256 も一致しました。以下は静的検査であり、pytest・描画・変異の実測結果ではありません。

参照略号は次のファイルを指し、`G:221` のように現物の行番号を付けます。

- G：[生成器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/plot_k2_loop_flow.py)
- J：[入力 JSON](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/k2_loop_flow_2026-09-20.json)
- T：[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/orchestrator/tests/test_plot_k2_loop_flow.py)
- P：[生成済み provenance](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/scratch/fig12_k2_manual_loop_dataflow.provenance.json)
- D：[caption_source の稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md)
- A：[段6裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s6-adjudication.md)
- F：[fix1報告](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-fix1.md)

採用仕様の実装と残存欠陥を合わせて判定しました。親の目視項目の closed は、指定された変更がコードに存在する意味であり、画像の再目視を意味しません。

| 所見 | 判定 | 現物の根拠・引用 |
|---|---|---|
| A-M1 | **partial** | G:221「`report['form'] == form`」、G:302「`data boundary: detected`」、G:396「`marker='X' if … else 'p'`」。T:441 の反転検査も存在。ただし G:639 の caption は検出なし固定のまま。must-fix 2。 |
| B-M1 | closed | G:275–276「`(job log)`」「`(per round records)`」。P:134 の proposal 日と evaluation 日にそれぞれ留保が付いた。 |
| B-M2 | closed | T:165–169「`kind']='round'`」「`c['critic']=None`」「`date_evaluation']=None`」「`has_diagnosis']=True`」。前段の evaluated 整合を壊さず G:200 の制約へ到達する。 |
| B-M3 | closed | T:219「`text.set_position(...)`」、T:226「`assert PLOT._drawn_items(...)==...`」。文字列変更はなく、publisher は T:261 で呼ばれる。 |
| A-S1 | closed | G:643「`rest on each round's records; saved prompts and inputs are not proof of delivery.`」。P:373 に実在、T:385 で照合。 |
| A-S2 | closed | J:18・27「`structural blockade of tool use`」、G:644「`does not judge whether B-6 is met`」。tool access 限定と未完備の留保を保持。 |
| A-S3 / P1 | closed | G:290「`synthesizes one backoff literal`」、G:292「`backoff literal {cell['value']}`」。値は proposal のみ。J:188・286 で集合外説明の重複を削除。語義の改善余地は should 2。 |
| A-S4 / B-S3 | **partial** | G:560「`arrows=_drawn_arrows(data,layout)`」、G:536「`actual == expected`」。artist 束縛は追加されたが、caption の回数語に問題。T:397 の期待も JSON 自体からは独立していない。 |
| B-S1 / A-nit2 | closed | T:238–253 の T5 から空 tmp assertion を削除。T:256「`['overlap','escape','arrow-crossing']`」の全ケースが T:261 の publisher を通る。 |
| B-S2 | **partial** | G:311 に「`coder: structured field data_boundary_report.instruction_like_content_detected`」。ただし集約は G:309 の全 role の `any(...)` であり、coder の結果と他 role の結果を混同する。must-fix 2。 |
| B 表の負例不足 | closed | T:146–169 に「`schema mismatch`」「`unused reference_ids`」「`duplicate job`」等の列挙された負例を追加。T:174 → T:36 で実 loader を呼ぶ。 |
| A-nit1 | closed | G:492「`for artist, owner in layout["markers"]:`」。neutral 要素・専用分岐は削除済み。 |
| A 削除候補：role/lane 重複 | closed | J:47–53 は「`id`」「`source_anchor`」だけ。G:271「`roles.get(lane['id'], lane)['sublabel']`」から表示を導く。 |
| B-nit1：変異母数 | closed | A:42「`10 群 12 変異`」、F:154「`11群14変異`」。M11 の2変異を加えた算術は正しい。 |
| B：M1 の mask / M8 の位置 | closed | A:46「`[direction]`」、A:55「`内部述語を常に受理`」。対応現物は G:104・253、T:97・469。 |
| 親目視：列見出し | closed | G:274「`Round {col['number']}`」「`After round … (not a round)`」。G:178 が番号を固定する。 |
| 親目視：括弧の空白 | closed | G:84・242「`strip('()[].:')`」、J:146「`(R0)`」、J:363「`(T-2795)`」。 |
| 親目視：a3 の上昇 | closed | G:423「`points=[start,(start[0]+.02,start[1])]`」、G:366「`'x' if kind=='absent'`」。T:407–409 が水平終点と cross を検査。 |
| 親目視：R6 marker | closed | G:395–397「`y+h-.009`」「`markersize=7`」。T:462–465 が形・色・大きさ・高さを検査。 |
| 親目視：副題 | closed | G:267「`Source: frozen results note`」「`figure created`」。P:59 に指定 template が存在。 |
| 親目視：round-1 evaluation | closed | J:141、P:124「`legacy verify condition`」。`bnode host` は消えている。 |
| 親目視：parent 説明 | closed | J:44、P:69「`builds the planner and coder input JSON, sends the full JSON inline`」と記録依存の留保。 |
| 親目視：lane の空白 | closed | G:380 の高さは parent `.115`、proposal `.068`、evaluation `.083`、critic `.079`。G:409・427–430 に label bank・凡例・脚注配置。 |

drawn_items 全50件も照合しました。新しい表現を含む照合範囲と結果は次のとおりです。

| 対象・件数 | 稿との照合 |
|---|---|
| title / subtitle：2 | P:54・59 ↔ D:8・51。三巡・凍結稿は一致。作図日と provenance の案内は作図者のメタデータであり、研究上の新命題ではない。 |
| knowledge：1 | P:64 ↔ D:111–128・204。source bytes 同一、別機体の WAL、受領証の意味は一致。 |
| lane-*：6 | P:69–94 ↔ D:51–54・144–155・161–164・202・214・235。役割・型・評価条件と記録依存の留保は整合。 |
| 列見出し：4 | P:99・134・169・204 ↔ D:193・209・224・301–322。提案日と評価日の証拠区分を保持。 |
| planner/coder/critic の実在 cell：11 | P:109–234 ↔ D:199–237・254–263。方向・大きさ・帰属・literal 合成は一致。`data boundary: none detected` の検出対象は曖昧。should 1。 |
| proposal cell：4 | P:119・154・189・224 ↔ D:161–162・201・206・221・234。20/25/20/10 と評価有無は一致。`known / not known` の集合が省略された。should 2。 |
| parent cell：4 | P:104・139・174・209 ↔ D:144–150・197・206・220・228・246。入力 key、同一実測、診断追加は一致。 |
| evaluation cell：4、no critic：1 | P:124・159・194・199・229 ↔ D:64–65・203・215–216・221・236・271–283。拒否 job と評価 job、未評価の区別を保持。 |
| arrow-*：7 | P:239–269 ↔ D:55–56・206–207・220–230・246。各経路の転記は整合。3本を「3回」と表す問題は caption 側。 |
| stock_control：1 | P:274 ↔ D:26–27・238。未達・裁定待ちは一致。 |
| legend：2 | P:279・284。線種・記号は作図上の定義。現データの全 false は D:36–38 と一致するが、反転時の集約に欠陥。 |
| footnote：3 | P:289・294・299 ↔ D:25–41・279–280。非比較・非性能認証・自己申告・非因果の留保は整合。 |

caption 固定文7は D:155–157・230・308–322・389–390、固定文8は D:12・335 に対応し、稿にない実施保証や B-6 充足の主張を足していません。

## caption の回数語の判定

**must-fix。数値自体は説明可能ですが、実文には「還流3回」と読める余地があります。**

P:373 の実文は次のとおりです。

> Measurement reflux occurred twice when counted by distinct source evaluation.
> Measurement reflux paths are drawn three times …

J:312–330 の measurement-reflux は m1 / m2a / m2b の3本で、異なる `from` は2件です。G:543–545 はこの2種類の数を生成しています。

一方、D:55–56 は還流を「次の提案の型付き入力に入ったこと」と定義し、巡1→巡2、巡2→巡3の**実測還流2回、診断還流1回**を述べています。D:220・246 により、巡2実測を未評価提案と巡3提案の両方へ描くことは妥当です。

問題は **`three times` が本数ではなく回数の表現**であり、その直後の `diagnosis reflux once` と同じ系列に並ぶことです。また、`when counted by distinct source evaluation` は、稿の巡間の定義を別の集計規則に読み替えています。

還流の実施回数と図の矢印本数を別文で明示すべきです。例えば：

> Measurement reflux occurred twice between the recorded rounds, and diagnosis reflux occurred once. Three measurement-flow arrows are shown because the second evaluation feeds both the unevaluated proposal and the third-round proposal.

3本の経路を2本に減らす必要はありません。

## 所見 (must-fix)

1. **caption が矢印本数を `three times` と表し、実測還流3回という誤読を生む。**
   箇所：G:543–545・634、P:373、T:418–420。
   根拠：上節の実文。T:419 は問題の文言そのものを期待値にしている。
   影響：図の中心命題である「実測還流2回・診断還流1回」が、caption 単独では曖昧になる。
   推奨 fix：実施回数は稿の巡間の定義で示し、描画数は `three arrows` と表す。対応する期待文も更新する。

2. **typed bool の true を正当に受理しても、caption は検出なしを断定し、凡例は他 role の検出を coder の field に結び付ける。**
   箇所：G:219–222・309–311・639、T:441–465。
   根拠：caption は固定の「`external inputs contained no instruction-like strings`」。`_caption` は discipline6 を参照しない。また凡例の `detected` は planner・coder・critic 全件の `any(...)` だが、末尾は `coder: structured field …; detected …` となる。planner だけ true、coder 全 false でも coder field の結果に見える。反転 test は caption を検査せず、coder 以外の単独反転も検査しない。
   影響：受理された入力から、赤 X・検出あり cell と「検出なし」caption が同居する成果物を公開できる。
   推奨 fix：caption を検出結果に中立な自己申告の説明へ変えるか bool に束縛する。coder 集約は coder の4出力に限定し、全 role 集約とは明確に分ける。true の受理は維持する。

## 所見 (should)

1. **`data boundary: none detected` は何を検出しなかったのか不明瞭。**
   箇所：G:302、P:109・114 等、D:36–38。
   根拠：稿が検出対象とするのは「指示めいた文字列」。新しい cell 文言は「data boundary が検出されない」とも読める。凡例と caption を読めば補えるが、cell 単独では主語が違う。
   影響：境界そのものの不在や、境界制御の成否と取り違えられる。
   推奨 fix：`instruction-like content: none detected (self-report)` など、対象と自己申告を明記する。

2. **`known / not known` が run-card の既知集合への所属であることを示していない。**
   箇所：G:292、P:154・224、D:161–162・352。
   根拠：稿の「既知」は run-card の集合 `{20,30,40}`。知識源の値集合や coder が知っていた値とは同一ではない。特に D:221 は coder-3 の入力に評価済み20が無いと明記する。
   影響：「coder が既知値を認識して再提案した」「25や10が一般に未知」と読まれ得る。
   推奨 fix：`in / outside the run-card known set` とするか、凡例で known の基準を一度定義する。

3. **T7 の期待は生成器実装から独立しているが、入力 JSON 自体からは独立していない。**
   箇所：T:396–397・415–418。
   根拠：「`expected=… for a in raw['arrows']`」「`counts=… raw['arrows']`」。artist の可視・始点・終点まで検査する点は有効だが、入力の経路を変えると期待も追従する。T1 の固定件数 `[3,1,3]` は接続先を固定しない。
   影響：同じ件数を保つ誤った還流先の転記を、T7 の経路・caption 照合では検出できない。
   推奨 fix：この凍結図の7経路と還流回数を、稿から手で確定した独立の期待表として置く。既存の artist 照合は維持する。

4. **caption の回数だけを可変にし、対応する経路列挙は固定のまま残している。**
   箇所：G:520–524・634、T:422–426。
   根拠：measurement の1～3本を扱う一方、括弧内は常に第一評価→第二提案、第二評価→未評価提案・第三巡を列挙する。T:426 は可変の短い回数句だけを検査する。
   影響：少ない矢印を受理した場合、caption が描画していない経路まで説明する。現 JSON の欠陥ではないが、B-S3 の整合性問題が残る。
   推奨 fix：凍結図の経路集合を検証するか、経路列挙も同じ入力に束縛する。

受理集合について、typed discipline6・number・role lane の簡略化・括弧付き宣言 ID の扱い以外に、fix1 が既存拒否を意図せず広げた箇所は見つかりませんでした。kind の位置制約は G:200 に移動して存続し、矢印件数検査は受理集合を狭めています。

test の既存期待値を不当に緩めた差分、skip、xfail はありません。T5 の空 tmp 検査の削除と表示期待の変更は裁定に対応しています。T9 は T:478 の通常 assertion として残り、未着地を失敗にします。

## 所見 (nit)

新規の nit はありません。

## 変異の単一理由性

**11群14変異。以下は位置・nodeid・拒否経路の静的判定であり、KILLED の実測報告ではありません。**
nodeid の共通接頭辞は `orchestrator/tests/test_plot_k2_loop_flow.py::` です。

| 変異 | 一箇所の変更位置 | kill 対象 nodeid／存在位置 | 単一理由性・mask |
|---|---|---|---|
| M1 | G:104 `_enum` の membership を恒真化 | `test_t3_invalid_enum_is_rejected[direction]`／T:97–105 | 適合。direction の `bogus` を再拒否する後段なし。column-kind は登録対象外。 |
| M2 | G:53 `_keys` の集合比較を expected ⊆ actual に | `test_t3_unknown_key_is_rejected[top]`／T:108–116 | 適合。未知の top key は後段で参照されず、他層に mask されない。dict 型検査は保持する。 |
| M3 | G:73 関数先頭で return | `test_t4_free_text_rejects_quantities[38%]`／T:200–203 | 適合。関数への直接入力で、他の loader 検査は通らない。 |
| M4a | G:453 `_intersection` を常に0 | `test_t5_overlap_is_a_layout_error`／T:238–241 | 適合と判断。a3 の Text を a2 の位置へ移す。canvas 内の label bank であり、文字列不一致・所有領域逸脱を伴わない。残る実 bbox の確認は変異実走で行う。 |
| M4b | G:457 `_contains` を常に True | `test_t5_escape_is_a_layout_error`／T:244–247 | 適合。Text は `(1.2,1.2)` へ移動し、他の Text・矢印から外れる。内包検査の別呼出しも同じ関数変異で無効になる。 |
| M4c | G:436 `_segment_intersects_box` を常に False | `test_t5_arrow_crossing_text_is_a_layout_error`／T:250–253 | 適合と判断。登録文字列は不変、所有者は canvas、m1 の線分へ移動。前段の文字列拒否はない。marker 非接触の最終確認は実走対象。 |
| M5 | G:557 `caption_source.sha256` を別64-hex定数に | `test_t7_caption_source_hash_is_independent`／T:306–309 | 適合。独立 hashlib と比較。`inputs` の hash が正しくても誤った caption_source hash は隠れない。 |
| M6 | G:164 tools 比較を恒真化 | `test_t2_tools_none_mismatch_is_rejected[0]`／T:77–81 | 適合。変更は bool の反転だけ。frontmatter は正常で、同じ対応を再検査する層なし。 |
| M7 | G:577 `check_figure_layout` 呼出し削除 | `test_t6_publish_runs_layout_check[overlap]`／T:256–262 | **旧 mask は解消。** T:226 が `_drawn_items` の通過を確認。矢印・caption は不変で G:578–580 も拒否理由を増やさない。保存後の provenance に layout 再検査はない。 |
| M8 | G:253 `_figure_number` の受理述語を恒真化 | `test_t8_cli_rejects_invalid_prefix`／T:469–472 | 適合。G:254 に match 不在時の fallback があり、別の例外で止まらない。CLI と publisher の両呼出しに同じ関数変異が効く。 |
| M9 | G:99 anchor 件数 `==1` を `>=1` に | `test_t3_non_unique_anchor_is_rejected`／T:190–197 | 適合。稿コピーに同じ見出しを追加するだけ。他の意味照合で再拒否されない。 |
| M10 | G:516 `_drawn_items` の照合削除 | `test_t7_drawn_items_match_flow`／T:312・369–372 | 適合。描画後に parent の説明だけを変更し、`build_provenance` を直接呼ぶ。矢印照合は独立で、変更した説明を検査しない。 |
| M11a | G:221 discipline6 form 比較を恒真化 | `test_t3_invalid_json_without_drawing[discipline6-form]`／T:122・142–143 | 適合。planner の form だけを変更。bool・key 集合は正常で、form を再検査する層なし。 |
| M11b | G:396 marker を常に `p` に | `test_t7_discipline6_flip_changes_marker_and_items`／T:441–465 | 適合と判断。色分岐は残し、形の式だけを変更する。T:462–463 の独立した bool→形・色表が不一致を検出する。caption 欠陥はこの test では検査されず mask しない。 |

M7 fixture は位置に加えて所有者も canvas に変えますが、これは内包違反を除くための措置です。登録変異自体は publisher の一呼出し削除であり、文字列を変更する旧来の二重拒否理由はありません。

## 総括

**NO-GO。must-fix 2件：caption の「3回」誤読と、検出 true 時の caption／凡例の不整合。**
裁定表全23行：**closed 20／partial 3／regressed 0**。partial の内側に fix1 の新しい不整合が残る。
実データの値・判定・経路、固定文7・8は稿と整合し、M7 の文字列 mask は解消した。
全14変異の nodeid は存在し、登録位置は一箇所に限定可能。幾何と公開の kill は親の実走で確定する。
本レビューは静的検査のみ。親報告の104 passed／未着地T9の1 failedを再実測したとは主張しない。