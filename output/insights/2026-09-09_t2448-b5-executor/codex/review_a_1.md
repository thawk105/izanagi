## 受理集合を広げる経路

1. **[real] arXiv の日付 delimiter 正規化が hybrid delimiter を受理する。**

   根拠: 凍結文が許すのは角括弧と二重引用符の差だけである (`docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:530`)。ところが正規表現は開始側と終了側を独立した選択肢にしているため、`submittedDate:"1991 TO 2026]` や `submittedDate:[1991 TO 2026"` も正規形へ丸める (`orchestrator/axis_b5_search/runner.py:511`, `orchestrator/axis_b5_search/runner.py:515`)。

   影響: 登録値と異なる arXiv echo でも条件 1 が `可` になり、leaf の受理集合が広がる。

   最小是正: `[...]` と `"..."` の二つの balanced な形だけを別々に照合し、開始と終了が混在する形を不一致にする。

2. **[refuted] `capacity_echo`、短い非最終 page、総数 drift、cursor 終端に、別の受理拡大経路は見つからない。**

   根拠: 条件 2 は位置だけを検査する (`orchestrator/axis_b5_search/runner.py:704`)。条件 3 は `actual_count` を使い、offset 最終 page は `position + actual == total`、OpenAlex 終端は `next_cursor is None` を要求する (`orchestrator/axis_b5_search/runner.py:720`, `orchestrator/axis_b5_search/runner.py:730`, `orchestrator/axis_b5_search/runner.py:735`, `orchestrator/axis_b5_search/runner.py:738`)。条件 5 は全 page の総数安定性と distinct ID 数を照合する (`orchestrator/axis_b5_search/runner.py:776`, `orchestrator/axis_b5_search/runner.py:785`)。`capacity_echo` は証拠化されるだけである (`orchestrator/axis_b5_search/runner.py:150`)。

   影響: 現コードでは、短い非最終 page、早すぎる cursor 終端、総数不一致はいずれも `未完走` になる。

   是正: production 修正は不要。下記の OpenAlex 固有変異 test は追加が必要。

## 恒真な test

1. **[real] `test_openalex_ast_preserves_multiplicity_but_ignores_sibling_order` は期待 AST の実体を production builder から作っている。**

   根拠: `expected` と比較対象の双方を `build_expected_openalex_ast` から作り、正例は `expected` 自身との比較である (`orchestrator/tests/test_axis_b5_search_executor.py:643`, `orchestrator/tests/test_axis_b5_search_executor.py:654`, `orchestrator/tests/test_axis_b5_search_executor.py:657`)。例えば builder の cutoff 値を別 literal へ変えても、この test は赤にならない。

   影響: cutoff や term の誤転記が条件 1 の受理集合を変えても検出されない。実際に 2023 control の誤りが残っている。

   最小是正: `B5-CTL-AND2023@openalex` を使い、凍結文から独立に書いた `"2023-12-31"`、`"200"`、field、join、term を AST literal として照合する。

2. **[real] registration の正例 test は、実際の実行器本体を一つも含まない別 root を正当化している。**

   根拠: fake root の `orchestrator/axis_b5_search/` に置くのは `registered.py` だけである (`orchestrator/tests/test_axis_b5_search_executor.py:170`, `orchestrator/tests/test_axis_b5_search_executor.py:185`)。それでも `test_registration_accepts_exact_commit_tree_and_returns_schema_valid_seal` は成功を期待する (`orchestrator/tests/test_axis_b5_search_executor.py:294`, `orchestrator/tests/test_axis_b5_search_executor.py:299`)。

   影響: parser、preflight、runner の実行 bytes が seal から漏れても正例 test が緑になる。

   最小是正: 正例 fixture に実ファイル名の独立 literal 集合を置き、seal の `files[].path` が少なくとも実際に load される B5 module を含むことを検査する。

3. **[real] OpenAlex cursor 終端の production 判定に対応する test がない。**

   根拠: `test_contract_2_accepts_openalex_cursor_chain_verbatim` は parser の値だけを見る (`orchestrator/tests/test_axis_b5_search_parsers.py:54`)。`test_openalex_initial_cursor_is_literal_star_and_continuation_is_encoded` は request builder だけを見る (`orchestrator/tests/test_axis_b5_search_executor.py:614`)。`_condition3` の最終 page `next_cursor is None` 検査を削除しても両 test は緑のままである (`orchestrator/axis_b5_search/runner.py:738`)。

   影響: 変異後は未取得の次 page がある leaf を `完走` にできる。

   最小是正: `next_cursor` が残った最終 `PageEvidence` を `evaluate_leaf` へ渡し、条件 3 の `cursor_not_terminal` を literal で要求する。

4. **[real] live preflight の負例に `非収録` がない。**

   根拠: test は `不達` (`orchestrator/tests/test_axis_b5_search_executor.py:545`) と `unclassified` (`orchestrator/tests/test_axis_b5_search_executor.py:958`) を検査するが、exact 30 のうち 1 件だけ `非収録` の例がない。`非収録` も許すよう `all_recorded` を変える変異は既存 test を通る。

   影響: 変異後は member が非収録でも `may_start_run=True` になる。

   最小是正: 30 件を保ったまま 1 件だけ `非収録` にし、`passed=False` と `may_start_run=False` を要求する。

5. **[real] `test_main_run_issuance_fails_closed_with_all_six_unregistered_fields` は production 入口を通らない。**

   根拠: test は `issue_run_request` を直接呼ぶだけである (`orchestrator/tests/test_axis_b5_search_executor.py:905`, `orchestrator/tests/test_axis_b5_search_executor.py:909`)。`run_leaf` の preflight 配線や最終 call site は未検査である (`orchestrator/axis_b5_search/runner.py:963`, `orchestrator/axis_b5_search/runner.py:986`)。

   影響: `run_leaf` が別 issuer を呼ぶ、または live gate を省く変異が赤にならない。

   最小是正: durable record の正負例から `run_leaf` を直接呼び、成功側でも最後は `UnregisteredRunPolicyError`、失敗側では issuer 到達前に `PreflightError` になることを検査する。

## fail-closed の穴

1. **[real] public な record 注入 seam が `may_start_run=True` を生成でき、production loader も応答分類の整合を再検査しない。**

   根拠: `evaluate_live_preflight` は外部から `LookupResult` 列を受け取り、identity と文字列 `"収録"` だけで認可値を作る (`orchestrator/axis_b5_search/preflight.py:744`, `orchestrator/axis_b5_search/preflight.py:760`, `orchestrator/axis_b5_search/preflight.py:764`)。さらに `__all__` へ公開されている (`orchestrator/axis_b5_search/preflight.py:930`)。正例 test 自身が登録 request と異なる `/registered` URL と架空 ID を注入して `may_start_run=True` を要求する (`orchestrator/tests/test_axis_b5_search_executor.py:263`, `orchestrator/tests/test_axis_b5_search_executor.py:272`, `orchestrator/tests/test_axis_b5_search_executor.py:565`, `orchestrator/tests/test_axis_b5_search_executor.py:575`)。

   loader は exact URL と登録 W-ID field は確認するが、`classification="収録"` と `status=None`、`transport_error="timeout"` などの矛盾を確認しない (`orchestrator/axis_b5_search/runner.py:941`, `orchestrator/axis_b5_search/runner.py:952`, `orchestrator/axis_b5_search/runner.py:957`)。schema もこれらを独立 field として許す (`orchestrator/schemas/axis_b5_search_live_preflight.schema.json:193`, `orchestrator/schemas/axis_b5_search_live_preflight.schema.json:194`, `orchestrator/schemas/axis_b5_search_live_preflight.schema.json:200`)。

   影響: 捏造した schema-valid record により production の live gateを通過し、main-run issuer 境界まで到達できる。ただし現 issuer は後述のとおり必ず例外になる。

   最小是正: evaluator を test-only の private seam にし、production 生成経路だけから使う。加えて loader で、各 `収録` が少なくとも登録済み status、media type、transport error 不在、索引別 observed shape と整合することを確認する。

2. **[refuted] 現時点で main-run HTTP request を実際に出す公開経路はない。**

   根拠: 投影された二 module の `__all__` は 17 名と 26 名で計 43 名である。HTTP transport を使う公開関数は anchor lookup 用 `run_live_preflight` だけで、固定 30 lookup を発行する (`orchestrator/axis_b5_search/preflight.py:852`, `orchestrator/axis_b5_search/preflight.py:892`, `orchestrator/axis_b5_search/preflight.py:897`)。main-run の公開 issuer は無条件で `UnregisteredRunPolicyError` を上げる (`orchestrator/axis_b5_search/runner.py:900`, `orchestrator/axis_b5_search/runner.py:903`)。`run_leaf` も最終的にその issuer だけを呼ぶ (`orchestrator/axis_b5_search/runner.py:963`, `orchestrator/axis_b5_search/runner.py:986`)。

   影響: forged live record を使っても、現在の実装から main-run request は発行されない。

   是正: production 修正は不要。ただし上記の `run_leaf` 配線 test を追加する。

3. **[refuted] live preflight の正規生成経路では、`不達`、`非収録`、`unclassified` はすべて停止側になる。**

   根拠: exact 30 を満たした後も、全結果が逐語 `"収録"` の場合だけ `passed=True` になる (`orchestrator/axis_b5_search/preflight.py:763`, `orchestrator/axis_b5_search/preflight.py:765`, `orchestrator/axis_b5_search/preflight.py:786`)。

   影響: production が実際に分類した結果では、1 件でも三つの失敗値なら走行開始不可になる。

   是正: production 修正は不要。`非収録` の変異 test は必要。

## seal の漏れ

1. **[real] seal 対象の `repo_root` と、実際に load 済みの Python module の所在が束縛されていない。**

   根拠: `preflight.py` は import 時に現在の Python path から `catalog` を load する (`orchestrator/axis_b5_search/preflight.py:23`)。`runner.py` も同様に `parsers` と `preflight` を load する (`orchestrator/axis_b5_search/runner.py:19`, `orchestrator/axis_b5_search/runner.py:28`)。一方、`verify_registration` は呼び手が指定した任意の `repo_root` の tree と bytes だけを seal し、各 module の `__file__` がその root 内の対応 path かを確認しない (`orchestrator/axis_b5_search/preflight.py:274`, `orchestrator/axis_b5_search/preflight.py:290`, `orchestrator/axis_b5_search/preflight.py:335`)。実行器のない fake root が通る test がこの食い違いを実証している (`orchestrator/tests/test_axis_b5_search_executor.py:185`, `orchestrator/tests/test_axis_b5_search_executor.py:299`)。

   影響: seal の `files` が示す bytes と異なる場所の parser、preflight、runner が実際の判定と走行開始可否を決められる。

   最小是正: B5 の必須 module path を literal で要求し、`catalog.__file__`、`parsers.__file__`、`preflight.__file__`、`runner.__file__` が `repo_root` 下の対応 path と一致することを seal 成功条件にする。

2. **[refuted] 既知の `__pycache__` 問題を除けば、対象 directory の走査は再帰的である。seal record の自己参照もない。**

   根拠: worktree は `os.walk` で再帰する (`orchestrator/axis_b5_search/preflight.py:206`, `orchestrator/axis_b5_search/preflight.py:211`)。commit tree は `git ls-tree -r` を使う (`orchestrator/axis_b5_search/preflight.py:169`, `orchestrator/axis_b5_search/preflight.py:172`)。seal は file entry を作った後に構築され、自己 digest field を持たない (`orchestrator/axis_b5_search/preflight.py:335`, `orchestrator/axis_b5_search/preflight.py:373`)。

   影響: 対象 root 内の通常の nested file は extra または missing として検出され、seal record 自身による循環は起きない。

   是正: この点の追加修正は不要。

## 凍結値の転記

1. **[real] `B5-CTL-AND2023@openalex` の期待 AST が 2026 cutoff になる。**

   根拠: 凍結文はこの control の値を `to_publication_date:2023-12-31` と固定する (`docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:316`, `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:318`)。しかし `resolve_leaf` は全 leaf に catalog top-level の共通 cutoff を入れる (`orchestrator/axis_b5_search/runner.py:341`, `orchestrator/axis_b5_search/runner.py:352`)。期待 AST builder は無条件にその `leaf.cutoff` を使う (`orchestrator/axis_b5_search/runner.py:656`, `orchestrator/axis_b5_search/runner.py:658`)。control にも条件 1 が適用される (`orchestrator/axis_b5_search/runner.py:680`, `orchestrator/axis_b5_search/runner.py:688`)。

   影響: 正しい 2023 echo が `未完走` になり、逆に誤った 2026 echo が条件 1 を通り得る。

   最小是正: catalog は変更せず、当該 control の期待 cutoff を凍結 literal `"2023-12-31"` として runner 側で選ぶ。独立 literal AST test を追加する。

2. **[refuted] 他の投影済み凍結 literal に転記差は見つからない。**

   根拠: page size、position parameter、pagination kind、retry 列、endpoint host/path は登録どおりである (`orchestrator/axis_b5_search/runner.py:39`, `orchestrator/axis_b5_search/runner.py:46`, `orchestrator/axis_b5_search/runner.py:48`)。lookup URL 三形は凍結文と一致する (`orchestrator/axis_b5_search/preflight.py:513`, `orchestrator/axis_b5_search/preflight.py:523`, `orchestrator/axis_b5_search/preflight.py:527`)。`get_rows` は文字列 `"200"` だけを受理する (`orchestrator/axis_b5_search/runner.py:625`)。exact 30 member と G2-08 の DOI/arXiv key も明示検査される (`orchestrator/axis_b5_search/preflight.py:462`, `orchestrator/axis_b5_search/preflight.py:480`, `orchestrator/axis_b5_search/preflight.py:483`)。

   影響: これらの定数による受理集合や request bytes の差はない。

   是正: 不要。

## 登録に無い gate

1. **[refuted] W-ID drift、`capacity_echo`、control の「発火」は拒否 gate に加えられていない。**

   根拠: observed W-ID は evidence fieldへ記録されるだけである (`orchestrator/axis_b5_search/preflight.py:709`, `orchestrator/axis_b5_search/preflight.py:712`)。live preflight の pass 判定は classification だけを見る (`orchestrator/axis_b5_search/preflight.py:764`)。`capacity_echo` は条件 3 に参照されない (`orchestrator/axis_b5_search/runner.py:720`)。leaf record が持つのは request completion と六条件であり、control firing field はない (`orchestrator/axis_b5_search/runner.py:200`, `orchestrator/axis_b5_search/runner.py:227`)。

   影響: 登録されていない三つの条件によって走行開始や leaf 完走が狭められることはない。

   是正: 不要。

2. **[refuted] lookup の判定順序と media type 比較は裁定どおりである。**

   根拠: OpenAlex は 404 を content type より先に `非収録` とする (`orchestrator/axis_b5_search/preflight.py:616`, `orchestrator/axis_b5_search/preflight.py:619`)。DBLP は 200 でも `application/json` 以外を `不達` とする (`orchestrator/axis_b5_search/preflight.py:661`, `orchestrator/axis_b5_search/preflight.py:664`)。media type は `;` より後の parameter を除いて比較する (`orchestrator/axis_b5_search/preflight.py:537`, `orchestrator/axis_b5_search/preflight.py:545`)。

   影響: 保存済み実測の OpenAlex 404 HTML、DBLP 200 HTML、arXiv Atom charset 付き応答は裁定どおり分類される。

   是正: 不要。

## 総括

production の実欠陥は四つある。

- arXiv の hybrid delimiter を受理する条件 1 の拡大
- live preflight record 注入 seam と record 内部整合の不足
- seal 対象 root と実際に load された module bytes の不一致
- OpenAlex 2023 control を 2026 AST と照合する転記誤り

main-run HTTP request を実際に発行できる公開 bypass は見つからず、現状は必ず `UnregisteredRunPolicyError` で止まる。一方、その保証を production 入口から検査する test、OpenAlex cursor 終端、live `非収録`、凍結 literal AST の変異 test が欠けている。

read-only の静的検査のみを行い、file 変更、git 操作、pytest、外部 request は実施していない。