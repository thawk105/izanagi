## 所見

静的検査のみであり、pytest は実行していない。

### A-1 — token 0 が「測定不能」ではなく 0 USD になる

**対象:** `s2-plan-2.md:164-167,181-188,206`、`tools/codex_reasoning_ab.py:7349-7354,7390-7395,8246-8256,10244-10253`、`orchestrator/tests/test_codex_reasoning_ab.py:11192-11207,11455-11469`

**失敗シナリオ:** 凍結 price version の sol run で token collector が欠測し、4 token field がすべて 0 になったとする。既存コードは ledger record 不在時や prelaunch/pair-invalidated 行へ 0 を書く。プランの helper は「exact int で `0 <= ...`」なら受理するため、`normalized_cost.status = "partial"`、`accounted_amount = "0.00000000"` を生成し、axis の `attempt_count` にも含める。

既存テストは、非空 prompt/output に対する全 0 usage を `RC_RECEIPT` として拒否している。それでも post-treatment は最終 report の `experiment_complete` を妨げない既存設計であり、retry 前の欠測 attempt もプランは resource 集計へ残す。したがって、valid report 内に「測定不能だった試行の 0 USD」が入り、arm cost を過小化できる。

**重大度:** CRITICAL

**根拠:** プランは「`0 <= reasoning_output_tokens <= output_tokens` を要求」とし、`s2-plan-2.md:206` では欠落だけを unavailable としている。一方、原典テストは「`token usage is all zero for non-empty prompt/output`」を明示的な異常としている。

必要なのは exact int 検査に加え、少なくとも `measurement_status = observed | unavailable | not-incurred` の三値化である。prelaunch の「費用非発生」と collector 欠測の 0 を同じ token 値で表現してはならない。

### A-2 — 検証済み snapshot と cost に使う snapshot が同じ bytes に束縛されない

**対象:** `s2-plan-2.md:98`、`tools/codex_reasoning_ab.py:8613-8653,8656-8707`、`tools/t189_price_snapshot.py:627-646,650-762`

**失敗シナリオ:** cost loader が最初に `_validate_frozen_price_snapshot_record()` を呼んだ時点では正規 bytes を読む。その直後、同じ path が、構造上 valid で同じ `price_table_version` を持つが、sol input price を `"4"` から `"1"` に変えた通常ファイルへ atomic replacement される。プランどおり loader が「その後に凍結 bytes を読み」直すと、二度目の validator は価格が正の canonical decimal であるため受理する。

sol の `input_tokens=1_000_000`、cached/output/reasoning が 0 の入力は、凍結価格なら `"4.00000000"` であるべきところ、同じ凍結 `price_version` を表示したまま `"1.00000000"` になる。

`_read_frozen_repo_file` は一回の read 中の inode/mtime 変化は検出するが、二つの read の間の差し替えは検出しない。

**重大度:** CRITICAL

**根拠:** プランは `s2-plan-2.md:98` で「prerequisite として呼び、その後に凍結 bytes を読み」と二度読みを明記している。既存 `_validate_frozen_price_snapshot_record` は validated tree ではなく `FROZEN_PRICE_VERSION` だけを返す。

検証した同一 bytes から作った fresh tree をそのまま返すべきである。再読するなら、二度目の bytes にも固定 SHA-256 を適用してから、その同じ bytes を parse する必要がある。

### A-3 — task manifest が CLI 呼び出し間で凍結されず、同名 task/finding を再解釈できる

**対象:** `s2-plan-2.md:53-70,74-91,217-221`、`tools/codex_reasoning_ab.py:2551-2626,9867-9890,10532-10550,10727-10743,10932-10939,11065-11080`

**失敗シナリオ:** packet 作成、verdict append、freeze を既定 `TASK_MANIFEST` で行う。その後、外部 manifest を渡して reveal/verify する。外部 manifest は同じ task ID `POS`、同じ `legacy_case`、同じ snapshot/provenance を持つが、`oracle_kind` を `positive` から `negative` に変える。既存 validator と downstream のどちらも `positive`、`negative` を受理する。

packet state、verdict freeze、revealed map のどれにも task manifest digest が無い。最終 report の `manifest_sha256` は experiment manifest の digest であり、task manifest のものではない。このため同じ run と verdict が、外部 manifest により positive primary から negative false-finding へ再分類される。

finding ID も同様である。既定と外部の双方に `A-1` があれば、どの manifest の `A-1` だったかを artifact から復元できない。

**重大度:** CRITICAL

**根拠:** プランが保証するのは一つの process 内で「その同一 manifest を……渡す」ことだけである。CLI は make-packets、append、freeze、reveal、verify という別 process の列であり、永続 artifact への digest 束縛は変更閉包に無い。

canonical validated task manifest の SHA-256 を schedule、launch/private mapping、freeze、revealed map、experiment manifest、最終 report に束縛し、各段で完全一致を要求すべきである。

なお、指定された `_LEGACY_KNOWN_FINDINGS`、`EXPECTED_SCHEDULE`、`KNOWN_FINDINGS` についてはプランの consumer 調査を支持する。現物では `_LEGACY_KNOWN_FINDINGS` は既定 manifest の構築時にだけ使われ、後二者に live consumer は無い。問題は module 定数の直接混入ではなく、永続 manifest identity が無いことによる段間の再束縛である。

### A-4 — partial cost が resource gate の値として使えるままになっている

**対象:** `brief.md:58-63,94-95`、`s2-plan-2.md:127-162,196-206`、`price-snapshot-v1.json:1`

**失敗シナリオ:** sol arm に 1,000,000 cache-write tokens、luna arm に 0 が発生したが、正規 receipt には数量が残らないとする。両 arm の観測可能な input/output が同じなら、`accounted_amount` は同額になる。しかし凍結単価では sol の欠落分は 5 USD、luna は 0 USD であり、完全な比較結果は異なる。

プランは `status = "partial"` と `unaccounted_token_categories = ["cache_write"]` を出す点では正しい。しかし親 brief は、この値により「resource-overall gate が値を持てる」としている。全 run が必ず partial なのに、gate を強制的に inconclusive にする規定が無い。

**重大度:** HIGH

**根拠:** プラン自身が「総額を完全な請求額とは表現しない」とし、axis 行も `coverage_status = "partial"` とする。一方、brief は「費用が算出されず、resource-overall gate が値を持てない」と記し、実装後に gate が値を持つことを成果物影響としている。

`unaccounted_token_categories` が空でない限り、total-cost gate と overall を機械的に `inconclusive` にする必要がある。`accounted_amount` を記述統計として残すこととは分けるべきである。

### A-5 — cost field が certification の閉世界へ追加されない

**対象:** `s2-plan-2.md:95-103,227-229`、`tools/codex_reasoning_ab.py:10532-10550`、`orchestrator/tests/test_codex_reasoning_ab.py:8088-8153`

**失敗シナリオ:** `verify` が `valid=true` と `normalized_cost_axis_ledger` を返し、論文生成側が同じ material report 内の cost を certified evidence として読む。しかし既存の `certification_scope` は `certified_report_fields = ["valid"]`、`closed_world = true` のままである。したがって cost 数値は report に見えても、装置の certification 契約上は certified field ではない。

**重大度:** HIGH

**根拠:** 原典は certification の対象を exact に `["valid"]` と固定し、テストも全 return path でその exact object を要求している。プランの変更閉包に `_certification_scope` とこのテストの更新が無い。

cost ledger を証拠とするなら、certification 契約とテストを同時に改訂する必要がある。そうしないなら cost は明示的に exploratory/unverified と表示すべきである。

### A-6 — 外部 manifest loader は宣言した UTF-8/一意 JSON 契約を実装しない

**対象:** `s2-plan-2.md:43-61`、`tools/codex_reasoning_ab.py:2551-2626`

**失敗シナリオ:** UTF-16 で符号化した manifest bytes を渡す。`json.loads(bytes)` は UTF-16/UTF-32 を自動判別できるため、プランが宣言する「UTF-8 JSON だけ」という拒否は発火しない。

別の入力として、JSON object 内に `tasks` key を二度書き、前半で `POS=positive`、後半で `POS=negative` とする。標準 `json.loads` は後勝ちで受理し、出力は同じ `POS` 表示のまま後半の意味で計算される。また `_validate_task_manifest` は `schema_version != 3` しか見ないため、`3.0` も 3 と等しい値として受理する。

**重大度:** HIGH

**根拠:** プランの処理順は `path.read_bytes()` の直後に `json.loads()` とある。既存 validator の原文は `if manifest.get("schema_version") != TASK_MANIFEST_SCHEMA_VERSION` であり exact int 検査ではない。

UTF-8 strict decode、duplicate-key 拒否、NaN/Infinity 拒否、exact `type(schema_version) is int`、closed top-level/task field set が必要である。

### A-7 — cost helper の拒否条件に到達不能なものがある

**対象:** `s2-plan-2.md:117-125,181-193`、`tools/t189_price_snapshot.py:617-646,650-762`

**失敗シナリオ:** validated snapshot の mapping operation を未対応値へ変えて cost helper の専用拒否理由を検査しようとしても、`validate_price_snapshot` が先に `receipt token accounting mismatch` で拒否する。cost helper の「未対応 operation」拒否には到達しない。

同様に、mapping へ `reasoning_output_tokens` を加える入力は exact mapping validator で先に落ちる。非 decimal、非 finite、0 以下の price も `_validate_prices` で先に落ちる。プランが求める validated snapshot だけを helper に渡す限り、次の cost-layer 条件は恒偽である。

- mapping operation/field list が未対応
- mapping が reasoning token を component に含める
- validated price が非 decimal、非 finite、0 以下

常時発火する条件は無い。現在の凍結 snapshot が全正例を通る。

**重大度:** MEDIUM

**根拠:** `_validate_receipt_mapping` は `if item != expected` と exact equality を要求し、`_validate_prices` は canonical positive Decimal だけを返す。一方、プランはこれらを cost helper の独立拒否条件として列挙している。

プランの二つの明示表では、各行に「通る正例」は書かれており、表内で正例欄が欠けた行は無い。ただし次の必要境界自体が表に無いため、対応する正例も無い。

- measured zero、unavailable、not-incurred の区別
- price 検証 bytes と cost 計算 bytes の同一性
- CLI 段間の task manifest digest 一致
- strict UTF-8、duplicate-key 拒否
- partial cost が gate を inconclusive にすること
- cost field の certification

### A-8 — P1 は根拠不成立であり、事前登録本文を直接更新してはならない

**対象:** `brief.md:69-75,87`、`s2-plan-2.md:273,277-280`、`prereg-s10.md:79-80,90-98`

**失敗シナリオ:** 実装完了後、同じ事前登録文書の §5.2/§10 を「未実装」から「実装済み」に直接変更する。実験開始前の契約だった文書 bytes が実装結果を見て改訂され、旧状態との区別や generation 境界が残らない。

**重大度:** HIGH

**根拠:** P1 の根拠は「到達度表を実測へ張り替えた前例」であり、変更管理上の許可ではない。射影された原典は「§13 の登録世代 lock 手続きは D674 により power simulation の段で停止」とし、価格変更については「事前登録 version を更新する」「新しい登録世代を作り、旧世代と混ぜない」と書く。

一方、§13 本文そのものと D674 の原文は今回の必読射影に含まれておらず、brief にあるのは D674 の要約だけである。したがって、原典の carve-out を引用して「到達度更新は改訂ではない」と立証できない。文書本文を変更する以上、例外が明示されない限り事前登録の改訂として扱うべきである。

代替は、実装 commit、静的検査、未実行テストを worklog と decisions spool fragment に記録し、事前登録本文は変更しないこと。本文更新が必要なら裁定パッケージを出し、許可された change log または新しい登録世代として行うこと。

### A-9 — 親 brief の実測前提には誤記と一般化過剰がある

**対象:** `brief.md:29-54`、`tools/codex_reasoning_ab.py:7181-7196,8656-8745,9280-9286,9752-9790`、`orchestrator/tests/test_codex_reasoning_ab.py:112-124`

**失敗シナリオ:** 実装担当が brief を変更閉包として信頼すると、`supervise_pair` の引数追加を省く、price binding を二つの helper だけで完結したと誤認する、raw token event に存在する cache-write field を調べず永久に欠測扱いする、または resource 生成位置を誤る。

**重大度:** MEDIUM

**根拠:** brief は「実測した前提」として断定しているが、現物との照合結果は次のとおりである。

| 項目 | 評価 | 原典との照合 |
|---|---|---|
| 1 | 支持 | cost/USD 系文字列は現行 `codex_reasoning_ab.py` に 0 件。 |
| 2 | 支持 | parser に option は無く、`main()` も manifest を渡さない。 |
| 3 | 一般化過剰 | `_validated_slots_price_version` は `{FROZEN_PRICE_VERSION}` という文字列集合だけで version を返し、snapshot bytes は検証しない。完全な binding は `_schedule_expected_price_version` と `_validate_frozen_price_snapshot_record` を含む経路全体で成立する。 |
| 4 | 条件付き支持 | artifact path のリテラルは指定の4箇所。しかし SHA 定数、validator consumer、テスト consumer も pin の一部であり、「4箇所だけ」から hook の非発火まで一般化はできない。 |
| 5 | 未立証 | `tools/check_docs.py` と事前登録全文は射影されていないため、whole-file pin が無いという全体主張は今回の原典から確認不能。 |
| 6 | 部分支持 | model、4価格、decimal、単位は snapshot と一致。ただし cache-write 単価は sol `5`、luna `0.25` と既知であり、不明なのは主に数量である。 |
| 7 | 一般化過剰 | 正規 receipt は4 fieldだが、原典テストの raw token event には `cache_write_input_tokens` が実在し、コードも `tools/codex_reasoning_ab.py:7789` で読む。必須でも一様でもないため現状は partial が妥当だが、「対応 field が存在しない」は raw source 全体には一般化できない。reasoning subset も現行 cost 層では未検査。 |
| 8 | 一部誤り | `_AXIS_FIELDS` の5項目は正しい。resource 行を作るのは `_replay_manifest` ではなく `_aggregate_verified:9752-9790`。段2プラン自身は `s2-plan-2.md:102` でこの誤りを訂正している。 |

加えて、`brief.md:9-12` は `supervise_pair` が既に `task_manifest` 引数を持つと書くが、現行署名 `tools/codex_reasoning_ab.py:7181-7196` には無い。段2プランの `s2-plan-2.md:3` はこれを正しく訂正している。

## 親 brief の P1〜P4 への評価

| 裁定 | 評価 | 理由 |
|---|---|---|
| P1 | **反対** | 到達度変更も事前登録本文の改訂である。§13/D674 原文による例外許可が射影されておらず、過去の編集実績は権限根拠にならない。worklog/spool に記録し、本文変更は裁定または新登録世代へ回すべき。 |
| P2 | **条件付き支持** | `--task-manifest PATH` と、未指定時の既定 manifest は妥当。`main()` 冒頭の先行解決も、プラン `:74-80` の順序を守れば閉じる。例えば `collect-run --task-manifest ext.json --case POS ...` では外部 manifest の `POS -> alpha` だけが解決される。ただし strict loader と段間 digest binding が必須。 |
| P3 | **条件付き支持** | price binding と cost 計算を別関数にする判断、per-run と axis の双方へ出す判断は支持する。A-1、A-2、A-4、A-5を閉じるまでは証拠用 cost として受理できない。 |
| P4 | **条件付き支持** | USD、Decimal、JSON decimal string、reasoning 非加算、cached-input 負値拒否は支持する。`accounted_amount` は partial のまま total cost や resource gate に使わないこと、axis 集計でも float へ戻さないことが条件。 |

補足すると、プランは次の境界を正しく閉じている。

- `reasoning_output_tokens` を output component に加えず、`reasoning <= output` を要求する。
- `cached_input_tokens > input_tokens` を拒否する。
- missing/None token を拒否する。ただし 0 の扱いは A-1 のとおり未閉包。
- cost 計算に float を使わず Decimal を使う。
- all-null price、v2 compatibility、schedule descriptor 無しでは cost key を出さない。

## scope 外だが real な所見

- `prereg-s5.md:108` のとおり served model attest が無い。今回の cost は requested SKU による正規化値であり、実際に served された model や請求額の証拠ではない。provider-side routing の認証は別裁定へ回すべきである。

- raw event には `cache_write_input_tokens` が現れる場合があるが、現在の frozen receipt mapping はこれを必須 field として束縛していない。完全 cost を求めるなら、field の意味、一様な存在、累積規則を調査し、receipt schema と price snapshot の新しい登録世代を作る必要がある。現 wave で frozen artifact を黙って変更してはならない。

- `prereg-s10.md:84-86` が明記するように、原表そのものの真正性は認証されていない。算出できるのは review 済みローカル snapshot に対する正規化 cost までである。

- task-specific oracle ledger と acceptance binding は未完成である。`prereg-s5.md:86-100` の規定どおり、これが無い stage の fix gate と overall は inconclusive のままにすべきであり、cost 実装だけで GO/NO-GO を確定してはならない。

- P1 の文書変更は実装子へ渡さず、§13/D674 原文を含む裁定パッケージへ回すべきである。

## 総括

現プランのままでは NO-GO である。特に、全 token 0 の数値化、snapshot の検証後再読、task manifest digest の段間欠落は、誤った cost や task 解釈が valid report に残る CRITICAL 経路である。

実装前に、token availability の三値化、検証済み同一 bytes からの price tree 返却、task manifest digest の全 artifact 束縛、partial cost gate の強制 inconclusive、certification scope 更新、strict JSON loader を変更閉包へ追加する必要がある。P1 は撤回し、事前登録本文は裁定なしに編集すべきでない。