結論は、plan v1 のまま案 A を実装してはならず、現実的な候補は案 B+C の格納方式変更だけです。ただし「14/21 を止める」は過大で、現物から支持できる上限は 12/21 です。既存台帳の収量は 0 件のままです。

## 1. 案 A の共通 supersequence 述語は「著作なし」を保証しない

- **主張:** plan v1 の4条件を全部満たしながら、merge が実際には行を追加できる。D721以前に述語自体が不健全である。
- **再現・反例:** 両親を `P1=P2=[a,b]`、結果を `R=[a,a,b,b]` とする。同一regular mode、全結果行は親由来、`a` と `b` の結果出現数2は親合計2以下、両親とも結果のsubsequenceなので全4条件を通る。しかし結果には `a` と `b` が1回ずつ追加されている。関数呼出し行なら動作も変わる。また plan の正例は、競合後に人が順序を決めた union を明示的に免除するもので、[D721](/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/D721.md:3) が拒否した操作そのものである。
- **成果物影響:** 4 SHAの撤去だけでなく、将来この反例に合う merge の `missing-codex-author` も消え、受理集合が拡大する。該当台帳を外せば checker は rc=0になり、現在なら要求される exact SHA 登録を迂回する。案 A の安全な撤去件数は0件と扱うべきである。

## 2. 「案 A の収量4件」は実装予定述語で測られていない

- **主張:** `measure_subseq.py` の測定とplan v1の述語は同値ではないため、4件という値は実装結果の裏付けになっていない。
- **再現・反例:** script は `bytes.splitlines()`、行集合による `novel==0`、subsequenceだけを測り、mode、regular blob、NUL、出現数上限、末尾空要素を測っていない。例えば親 `b"a\n"` と結果 `b"a"` は `splitlines()`では同一だが、planの `split(b"\n")` では親だけ末尾空要素を持ち、判定が変わる。`measure_union.py` も集合なので重複行を失う。
- **成果物影響:** 4件を先に台帳から外すと、実装とのずれにより新規findingまたはstaleが発生し、checker rc=1/2となる。staleは[checker:2143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:2143)から例外、[main:3059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:3059)でrc=2となる。D721記載のland契約では `RC_PROVENANCE=29` で拒否される。

## 3. `<sha>.json` は現行53件を1件1fileで表現できない

- **主張:** SHAだけをfile keyにする案 B の例は、現行データと衝突する。
- **再現・反例:** SHA `649fe5a060...` には `malformed-ai-agent` と `missing-codex-author` の2エントリが実在する。[checker:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:827) と同834行目で確認できる。1つの `<sha>.json` に配列を入れれば「1 violation 1 file」ではなくなり、別finding追加時に同じfileを編集する。別fileにするなら少なくとも `<sha>--<kind>.json` が必要である。
- **成果物影響:** SHA fileを上書きすれば一方の免除が失われてrc=1、配列なら競合面が残る。安定keyは `(full SHA, finding kind)` とし、将来同kindで複数値を許すかも明文化しなければならない。

## 4. 既存台帳検証は保存可能だが、案 B の仕様には保存方法がない

- **主張:** 現行の検証はすべてデータfile経由でも保存できる。ただしloaderがspec tupleを作り、現行の[_known_violation_registry()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:901)へ渡す設計が必要である。保存不能な検証はない。
- **再現・反例:** 現行は、tuple container、entry型、SHA型、40桁full SHA、kind型、3種の許可集合、非空ruling、note型、note改行禁止、finding value型、malformedでのvalue必須、他kindでのvalue禁止、malformedでのnote必須、note禁止文字、descriptive文字、value禁止文字、重複を検査する。なお実装上の重複keyは `(SHA, kind, expected value)` であり、単純な`(SHA, kind)`禁止ではない。一方、逐語テストは `(SHA, kind)` の一意性もassertしている。[tests:2279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2279)
- **成果物影響:** loaderで既存関数を迂回すると、不正データが免除集合へ入るか、例外がrc=2へ畳まれなくなる。さらにJSON側では、unknown/missing field、重複JSON key、非regular fileまたはsymlink、filenameと内容の不一致、UTF-8、予期しないdirectory entryもfail-closedにする必要がある。

## 5. loaderをimport時に動かすと `--message-file` 契約を壊す

- **主張:** 台帳はhistory監査時だけ読む必要がある。module import時のデータ読込は不適切である。
- **再現・反例:** [test_broken_short_sha_registry_is_rc2_but_message_file_is_unchanged](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2470) は、壊れた台帳でhistoryがrc=2でも、`--message-file`はrc=0のままという契約を固定している。現行message-file分岐は[_message_file_paths()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:1640)を使い、registryを読まない。
- **成果物影響:** import時loaderではcommit前検査までrc=2となる。正しいlazy loadなら、将来のdocs JSON登録は実装面でなく、message-fileのCodex author要求も増えない。一方、historyで不正データやstaleを検出した場合は従来どおりrc=2、land不可を保てる。

## 6. 案 C は「説明文だけのpin」ではない

- **主張:** 逐語ミラーはruling/noteだけでなく、53件全部のSHA、finding kind、expected value、順序と一意性、許可集合も独立にpinしている。単純削除はgateの弱化である。
- **再現・反例:** [test_known_violation_ledger_matches_literal_entries](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1861) は5 field全てを`observed == expected`で照合する。対して実commit照合は[31 SHAだけ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2290)で、最新22件を含まない。同じデータfileをloaderとテストが二度読むだけなら恒真である。
- **成果物影響:** Cだけを畳むと、単一docs fileの編集だけで免除集合とstdoutのnoteを変えられる。B+Cを採るなら、全53エントリを実commit findingと突き合わせる検査、loader変異テスト、公開stdoutの逐語テストを同じwaveに入れ、独立literal pinを廃止すること自体はユーザー裁定にする必要がある。

## 7. 1件1fileでも競合ゼロにはならない

- **主張:** indexをなくせば異なるentry同士の競合は減るが、同じentryの並行登録は同じfileを触る。
- **再現・反例:** `e86d363a...` の現行noteは、2 waveが同じ`09ce607b...`を独立登録して競合したと明記する。[checker:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:323) 同じSHA/kindを異なるruling/noteで登録すればadd/add conflictとなる。ランダムな別filenameに逃がすと、merge後にregistry重複でrc=2となり、結局手解決が要る。静的manifest、生成index、全件parametrize一覧、hash snapshotを追加しても共通編集面が復活する。
- **成果物影響:** B+Cは自己増殖を大幅に減らせるが、完全停止とは言えない。実装scopeではindexなしの`sorted` directory列挙を固定し、同じsemantic keyの衝突は意図的にfail-closedとするべきである。

## 8. 14/21 は過大で、支持できる上限は12/21

- **主張:** 最新追補の「G5 11件とmanager直接3件をBで防ぐ」という一般化は、親自身の`prevented.py`と矛盾する。
- **再現・反例:** `prevented.py`のprevented listは12件、すなわちledger-only merge 10件と`94815c...`、`3a5e5f...`である。`311d463...`は`s8b_oracle_driver.py`が現行[_commit_paths()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:1587)に残るためB後もfindingが残る。`25614f...`は`tools/check_docs.py`をmanagerが直接変更した元の違反で、台帳格納が原因ではない。さらに`prevented.py`はSHAをfinding kind確認前に`seen`へ入れるため、`649fe...`の2番目の`missing-codex-author`を実測集合から黙って落とす。
- **成果物影響:** B+Cの既存台帳収量は0件、直近21件への反実仮想抑止は最大12件である。残る9件は `311d463`、`25614f`、`649fe`の2finding、trailer欠落5件である。受理集合は変えず、将来増加率の見積りだけを14/21から最大12/21へ訂正する必要がある。

## 9. merge原因分析と全数分類は独立検証になっていない

- **主張:** 「11/11が台帳競合」「G5は全て台帳原因」という表現は、測定コードが証明できる範囲を超えている。
- **再現・反例:** `measure_mergefile.py`は最初から現在の`_commit_paths()`に残ったpathだけを調べる。過去の競合を片親と完全一致する形で解決したpathは親差分の積集合から消え、観測されない。また`git merge-file`はdefault 3-wayの再計算であり、当時の実際の解決主体やmerge driverまでは示さない。`classify.py`も、`missing-codex-author`かつmergeならpathを確認せず無条件にG5とし、`STRONG_OK` 4件をhard-codeしている。
- **成果物影響:** 53件という全数とfinding内訳は使えるが、G5/G6を独立した原因分類として受理してはならない。Bの収量は`prevented.py`のpath基準で上限評価し、残りの生成器タスクをこの分類だけから設計しないこと。

## 10. 投影内にも未計上consumerがあり、投影外pinは未検証である

- **主張:** 「参照codeはrepoの2 fileだけ」はproduction repoについての主張にすぎず、今回の再現成果物まで含む閉包ではない。
- **再現・反例:** `measure_union.py`、`measure_mergefile.py`、`measure_subseq.py`、`prevented.py`、`classify.py`は定数を直接importし、`growth.py`は`KnownViolationSpec(`の文字数を数える。定数を除去すれば前5本が壊れ、格納移行後はgrowthが台帳を0件と数える。
- **成果物影響:** gateの受理集合には直接影響しないが、分類と増加実測の再現性が失われる。移行後の測定器はデータdirectoryを履歴時点ごとに数える別版へ切り出すか、既存scriptを「移行前commit専用」と凍結表示する必要がある。

### 推測・投影制限

- **主張:** `check_docs.py`、`test_check_docs.py`、`test_hooks.py`、`test_dev_wave_land.py`などのopaque pinは、このdispatchで読むことを許可された資料に含まれないため未検証である。「壊れない」という親の閉包主張は現時点では成立しない。
- **再現・反例:** whole-file SHA-256、byte budget、行数、逐語断片は`KNOWN_PROVENANCE_VIOLATIONS`を参照しないため、定数名grepでは発見できない。投影されたテスト内ではchecker/test file全体のhash・byte数pinは見つからなかったが、投影外consumerには一般化できない。
- **成果物影響:** その種のpinが実在すればB+C実装はdocs/test/hookで失敗し、land不可になる。B+Cの実装waveでは、これらconsumerの明示的なread-only閉包確認を必須scopeに含めるべきである。

## 11. plan v1 の file:line は正しいが、最新案の実装プランではない

- **主張:** 指された既存symbolと行番号に不存在は見つからなかった。一方、plan v1は案 A だけを具体化しており、最新追補の中心であるB+Cを計画していない。
- **再現・反例:** `_combined_diff_paths` 1539、`_commit_paths` 1587、`_message_file_paths` 1640、stale 2143、main例外3059、mergeテスト1481、invalid UTF-8 1548、octopus 1595、literal test 1861、real-commit test 2290、次def 2363はいずれも実在する。4 SHAのentry、mirror、孤児定数も指定位置にあり、`REAL_REPO_SERIAL_NODES`は実在しないというplanの記述も正しい。
- **成果物影響:** file:line誤りによる直接の実装脱線はない。ただし案 A を実装すれば受理集合を広げるため、正しい行番号でもland対象にしてはならない。B+C用にloader、53 data file、テストseam、stdout、stale、message-file、consumer閉包を明記したplan v2が必要である。

補足すると、plan v1のbinary契約にも入力不足がある。現行`_combined_diff_paths()`はpatch内容を捨ててpath listだけを返すため、「Gitがbinaryとして出した」を後段で知るには追加queryか戻り値変更が必要である。NUL検査だけへ縮退すると、NULなしでもGit側でbinary指定されたpathへ行述語を適用し得る。これはquery上限とfail-closed挙動の双方に反映すべきである。

テストは実行していない。指定どおり、投影資料だけを用いた静的検査である。

## 総括

案 A: **不採用** — D721に反し、重複行の具体的反例でも「著作なし」を保証できないため、撤去収量は0件と扱う。

案 B: **条件付き採用** — Cと同一waveで、複合file key、indexなし列挙、全現行検証、lazy load、consumer閉包を備える場合に限る。抑止見積りは最大12/21。

案 C: **条件付き採用** — 単純削除は不可。全53件の実commit照合と公開形式・schema変異検査を置き、独立literal pin廃止を明示裁定する場合だけBと併用する。

案 D: **予備終端として採用** — B+Cの裁定またはconsumer閉包が得られない場合は、コード・台帳を変更せず監査と先送りpackageだけを残す。

このwaveに収めるべきscope: **案B+Cの意味不変な格納移行、53件全移行、必要consumer閉包と回帰検査まで**。案Aと、残る9/21向けのtrailer作成防壁・manager直接commit防壁・merge解決証跡は別タスクへ切り出す。