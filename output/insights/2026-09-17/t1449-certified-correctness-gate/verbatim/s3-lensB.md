## 凍結 vector の期待値

以下、`V`＝`orchestrator/submission_gate/_semantic_validator.py`、`U3`／`U5`＝`orchestrator/tests/test_t338_submission_gate_unit3.py`／`test_t338_submission_gate_unit5.py`、`C`＝`orchestrator/tests/fixtures/t338_submission_gate/conformance/`、`P`＝指定の `s2-plan-2.md`、`B`＝指定の `s1-brief.md`。すべて静的検査であり、テストは実行していない。

**所見**：対象4配列への直接 mutation は7本ではなく14本で、plan は phase 5本・rehash 2本を個別検算から落としている。
**分類**：real
**根拠**：各 `C/negative-*.json:1` の recipe を照合すると、`7.1-08-reason-branches`→actual が残り `reason`、`7.1-08-raw-marker-route`→同じく `reason`、`7.1-16-create-only`→専用入口で `intent`、`6.8-reference-graph`→slot 9で `allocation`、`7.1-09-allocation-slot`→同じく `allocation`、`6.5-schedule-derivation`→stat 不一致で `a03`、`7.1-10-stat-recompute`→同じく `a03`、追加の `6.9-phase-budget`→deadline 1で `phase`、`7.1-06-phase-closure`→phase 重複で `phase`、`7.1-15-monotonic-order`→時刻順違反で `phase`、`7.1-18-time-cap`→deadline 1で `phase`、`6.9-phase-order`→reverse で `phase`、`7.1-03-uniqueness`→rehash 対重複で `cardinality`、`7.1-07-rehash-reach`→digest 不一致で `cardinality`。
**影響**：期待値変更は静的には見つからないが、fixture 依存の監査対象を半数しか列挙していない。
**推奨**：P:118 の表を14本へ拡張し、独自 payload が correctness／liveness を重複させる `7.1-01-liveness-pairs` を別枠で明記する。

**所見**：plan の46本の内訳は誤っており、通常 receipt mutation と phase vector の数が過大である。
**分類**：real
**根拠**：`C/index-v2.json:4` 以降の集計は receipt 33、writer_authority 5、preregistration 2、その他6入口各1；指定7本を除く通常 receipt 負例は26本で、P:132 の「28本」「phase の6本」はそれぞれ26本・5本が正しい。
**影響**：P:130 の残り39本の内訳で、sealed writer 正例と safe_io を数え落としたまま合計だけ一致している。
**推奨**：残り39本を「receipt 負例26＋専用 semantic 4＋その他専用6＋receipt 正例1＋writer 正例1＋safe_io 1」へ訂正する。

**所見**：`negative-6.6-correctness-raw` が stock/W1 raw を差し替えるという点検前提は現物で反証された。
**分類**：refuted
**根拠**：`C/negative-6.6-correctness-raw.json:1` は `"path":["planned_execution","schedule_seed"]`、期待値は `"schedule"`；raw anomaly の実試験は U3:1011 で、V:1821 の `... or anomaly` は1件の異常を残り5件の正常値で消さない。
**影響**：この vector の通過を correctness raw 検出の証拠として報告すると、実効性を誤帰属する。
**推奨**：plan v2 に名前と実 mutation の相違を記録し、raw 検出の根拠を U3:1011・1037 に限定する。

**所見**：fixture 拡張で既存 recipe のファイル解決が壊れるという懸念は、指定された変更内容では成立しない。
**分類**：refuted
**根拠**：U5:104 の resolver は実ファイルを読み、U3:247 以降には `build/failure-verification` が残る；replace_file 対象は `build/compile_commands.json`、`build/CMakeCache.txt`、`build/run-w1.log` で、P:104 の追加11ファイルと衝突しない。
**影響**：nit；failure raw を削除した場合だけ2本の reason vector が semantic 検査以前に壊れる。
**推奨**：P:70 の failure raw 維持を、上記2 vector の参照維持として明記する。

## fixture 改修の波及

**所見**：指定された既存 unit3 test と phase／rehash 検査に、completed 化だけで発生する破壊は見つからない。
**分類**：refuted
**根拠**：U3:1011・1037 は先頭出力だけを変更、U3:1100 は `allocations[1]` を変更、U3:685 は独立 payload；U3:358・390・569 は verification の phase 開始100、区間100..120、submitted 100、U3:152 の生成時刻は100..111；V:197 の cap 合計2640秒、V:2110 は reason 非依存、V:2453 は verification rehash を禁止し fixture は空のまま。
**影響**：配列順と各 entry の独立性を維持すれば、既存拒否理由・study digest 比較の対象は変わらない。
**推奨**：plan v2 の変更範囲に「allocation 順序維持・stock/W1 先頭維持・entry の可変オブジェクト非共有」を明示する。

## pointer 実在

**所見**：追加11ファイルに pointer 不足や性能 binary の再利用があるという懸念は、現物の既存資産で反証できる。
**分類**：refuted
**根拠**：U3:234 以降に correctness compile_commands／CMakeCache、U3:263 以降に correctness binary 3本と stock/W1 出力があり、binary 内容は `correctness-stock\n` 等、性能側は `performance-{arm}\n`；V:2319 は build／outputs、V:2328 は liveness raw、V:1149 は binary digest 不一致を検査する。
**影響**：不足は出力5本と liveness 6本で尽きるが、未実装なので実ファイル生成済みとは扱えない。
**推奨**：plan v2 では11本の作成を `_make_git_fixture.tree_files` に限定し、`_full_receipt` の pointer 生成より前に実体を用意すると明記する。

## 変異 matrix の帰属

**所見**：M4 は編集位置が曖昧で、既存の性能重複検査を壊す変異と新 gate だけを無効化する変異を区別できない。
**分類**：plausible
**根拠**：P:169 は「gate が見る `performance_slots` を常に空」、V:2021 は同じ辞書を `"more than one completed performance attempt"` の検査にも使う。
**影響**：loop 内の収集処理を消す実装では、新 gate 以外の拒否能力の低下を同じ変異へ混入させる。
**推奨**：M4 は「loop 後、新 gate の条件評価だけを空集合へ置換」と exact diff を事前登録する。

**所見**：既存 matrix は被覆集合検査の必要性を試す一方、件数検査だけが失われる過剰受理を検出できない。
**分類**：real
**根拠**：P:147–151 の入力は0・1・5件、6件重複、完全6対のみ；P:43 の `len(evidence) != 6` を削除しても、これらは集合検査だけで同じ結果になる；V:1510 は ordinal を検査するが、verification 非 completed 時の重複対を禁止しない。
**影響**：完全6対に重複1件を足した7件が受理されても、新規テスト群が検出しない。
**推奨**：verification pre failure・ordinal 1..7・完全6対＋同 arm/workload 重複1件の負例と、件数比較だけを削除する変異を追加する。

**所見**：M2 の証明には「既存 test では殺されない」という対照結果が必要だが、plan は killer 指定だけに留まる。
**分類**：real
**根拠**：P:167 は新負例 `[0]`・`[1]` のみを列挙；改修後の既存正例は6対で、U3:685 の検証 completed 不足は V:2010 の既存 `reason` が拒否するため、新 gate 削除に依存しない。
**影響**：単に KILLED と記録すると、先行する別条件による test 破綻と gate の必要性を区別できない。
**推奨**：M2 は既存焦点集合が維持され、新負例が期待例外未発生で落ちることを別々に記録する。

静的な帰属予測は、M0＝SURVIVED、M1＝指定不足負例に加え失敗 stage 正例も KILLED、M2＝新不足・重複負例のみ、M3＝失敗 stage 正例、M4＝上記限定なら指定単体負例、M5＝指定 reason assertion、M6＝重複対負例、M7＝1・5件負例、M8＝modeX/W2 欠落5件負例、M9＝既存完全正例、M10＝検証 attempt 不在の局所正例。実測結果ではない。P:150 に失敗 stage の0件受理正例が登録されているため、承認外の無条件拒否を検出する対照自体は欠けていない。

## 単一理由性・観測可能性

**所見**：性能 completed＋検証失敗＋証拠0件が先行層で必ず拒否され、top-level では gate を観測できないという懸念は反証できる。
**分類**：refuted
**根拠**：V:1424 以降の evidence 参照検査、V:1117 の build、V:1803 の raw は空配列を走査せず、V:1853 は残された性能36-run／36 observations を検査する；P:147 は verification allocation と性能 facts を残し、検証 completed の V:2010 を迂回する。
**影響**：指定変換なら top-level で新 gate の拒否を識別でき、単体入口だけへ試験を後退させる必要はない。
**推奨**：同一入力について gate ありで `correctness`、M2 で受理、を組にして示す。

**所見**：同じ `correctness` を返す先行検査があるため、reason 一致だけでは新 gate の実効性を証明できない。
**分類**：real
**根拠**：V:1133 は source 不一致、V:1780 付近は比較対象のない raw、V:2034 は anomaly を同じ `correctness` で拒否する；P:149 の重複対負例もこれらより後に到達する必要がある。
**影響**：fixture の source／raw 作成ミスが新 gate 成功に見えてしまう。
**推奨**：不足負例と重複対負例の双方で M2 による受理への反転を必須証拠にする。

## 焦点テスト集合と受入時間

**所見**：個々の新 test が軽いことから受入全体の5分以内を断定する根拠は不足している。
**分類**：plausible
**根拠**：`orchestrator/tests/acceptance_duration_ledger.json:21468` は raw anomaly 0.63秒、`:21475` は単体0.001秒、`:21499` は完全正例0.66秒、`:21500` は study 3.3秒；fixture 拡張は新規 node だけでなく U5 の既存 fixture 利用にも追加読取りを発生させる。
**影響**：新規 top-level 約10ケースは既存値の単純外挿で数秒級だが、全受入の残余時間・並列配置・既存 node 増分は未確認。
**推奨**：plan v2 に概算と未測定範囲を分け、焦点3ファイルと通常受入の実測で判定すると追記する。

**所見**：`test_mocc_trace_job_contract.py:3856` を semantic validator consumer とする点検前提は反証された。
**分類**：refuted
**根拠**：同ファイル:3856 は分類 enum の `"correctness_evidence"`；validator の呼出しは `_writer.py:17,73`、直接利用は U3／U5、間接 fixture 利用は `test_t139_submission_path.py:24,42,48`。
**影響**：Mocc trace 全件を追加しても、今回の gate の実効性を直接検証する集合にはならない。
**推奨**：plan v2 では当該行が単なる同名分類値であることを明記し、焦点集合へ追加しない。

## 親 brief 自身の点検

**所見**：「vector は test 名を参照するだけ」は、凍結束縛の全体説明として不十分である。
**分類**：real
**根拠**：B:33 に対し、U5:345 は vector bytes の SHA-256、U5:348 は metadata 一致、U5:352 は `getattr(_UNIT3, reference, None)` と `inspect.isfunction` を検査し、U5:267 は recipe を実際に適用する；approval manifest:20 と vector approval:21 は index-v2 を pin する。
**影響**：test 名を残しても recipe の前提を壊せば凍結期待値は維持できない。
**推奨**：brief／plan v2 を「unit3 ソース bytes は pin 対象ではないが、test 名の実在と recipe の実行結果は拘束される」へ訂正する。

**所見**：「変更 file の sha256 pin 0件」は今回確認した範囲では反証されないが、検索範囲を伴わない絶対表現は避けるべきである。
**分類**：plausible
**根拠**：現行 V の digest `0437a806…`、U3 の `54259c12…` は repo の通常検索で参照なし；指定 approval JSON が pin するのは index 等であり、B:35 には検索対象・除外範囲が書かれていない。
**影響**：nit；外部資料・無視対象・履歴を含む完全な非存在証明として読むと証拠範囲を越える。
**推奨**：「指定 approval 束縛と検索対象内でソース digest pin を検出せず」と範囲を限定する。

**所見**：brief の主要アンカーと `negative-7.1-08-*` の先行 `reason` 説明には実質的なずれを認めない。
**分類**：refuted
**根拠**：V:1953・1962・1993・1117・2596、U3:181・332・685 は現物と一致し、両 vector の recipe は attempts[0] を pre failure にして actual を残すため V:2036 が拒否する；細部では `_full_receipt` 終端は U3:646。
**影響**：nit；行末の1行差は実効性を変えない。
**推奨**：plan v2 では終端だけ646へ直し、2 vector は「gate 条件が偽」より正確な「loop 内で先行拒否」と記す。

## scope 外の層

**所見**：新 gate の拒否を直接示す計画は単体・top-level までで、writer／study の新負例拒否は直接試験されない。
**分類**：real
**根拠**：P:147–151 の新負例入口は単体／top-level；`_writer.py:73` と V:2651 は個別 validator を呼ぶが、U5:597 の writer 正例と U3:1065 の study test は新 gate 不足負例を投入しない。
**影響**：呼出関係からの適用推論を、writer／study で新拒否を実測した証拠と扱うと実効性を過大表示する。
**推奨**：成果物では「拒否の直接検証＝単体・top-level、writer／study＝既存統合回帰と呼出関係の確認」と区別する。

## 裁定パッケージ候補

追加 gate・台帳・一般化の提案はない。P1-b と凍結 §7.1(1) の解釈境界、および「成功・certified」の範囲はレンズAへ。本所見の7件負例追加は、plan 自身が要求する「合計6件」の検証補完であり、新条件ではない。

## 総括

修正優先は、**vector 対象14本への訂正、46本の内訳修正、7件過剰受理を検出する負例・変異追加、M4 の編集位置固定、M2 の反実仮想記録**。

fixture の pointer・phase・既存指定テストには静的な破壊を見つけなかった。新負例は top-level で観測可能と読める。ただし、46 vector の期待値維持・KILLED／SURVIVED・受入5分以内はいずれも未実測である。