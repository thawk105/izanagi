## 模擬への転落

1. **[refuted] `backoff_sweep` は模擬へ転落していない。**

   - 根拠: plan は `run_workload()` を直接呼ぶが、CLI の `main()` が省くのは引数解析と workload 選択だけである。`run_workload()` 自体が single-tenant、site/runtime、calibration、genome、toolchain、build policy を確定し、source/stock root、patch、FetchContent、gate の順に実行する（`orchestrator/campaign/backoff_sweep.py:322-392`）。`main()` は `run_workload()` に値を転送するだけである（同 `:435-455`）。
   - 成果物への影響: `write-heavy` の最小 screening については、実際の production root 束縛と gate 呼び出しを測ったと言える。

2. **[real] `backoff_repro` は root 束縛 seam を本物の入力で通すが、production 入口から gate への到達性は測らない。**

   - 根拠: production の `run_workload()` は gate 前に `_config()`、build context、admission/environment binding、`PerfConfig`、log、compiler 解決を実行する（`orchestrator/campaign/backoff_repro.py:148-166`）。plan は `_assert_single_tenant()`、`ORIG`、`_genomes_reversed()`、compiler 解決だけを再現し、直接 `_conditioned_backoff_patch()` に入る（`s2-plan.md:48-70`）。
   - 静的データフロー上、飛ばした `cfg`、build context、environment binding、`PerfConfig` の戻り値は `_conditioned_backoff_patch()` の `points`、`cxx`、source root、stock root、configure args には渡らない。root は context 内で `buildcache._ccbench_dir()` により改めて束縛され、stock は historical pin の checkout、configure args は空である（`backoff_repro.py:63-83`）。
   - したがって「seam に到達した後の gate 入力が模擬」という攻撃は refuted だが、「CLI/run_workload が実際に gate まで到達することを実測した」という主張は real な過大主張になる。
   - 成果物への影響: 結果は「production `_conditioned_backoff_patch()` の liveness」と記載し、「production entry-to-gate liveness」とは記載できない。

3. **[real] `s1_direct_comparison` は production 入口を迂回し、実際の schedule 状態が選ぶ cell と異なる cell を直接 gate に入れる。**

   - 根拠: production の `run_role()` は authorization、campaign/WAL、既存 session ledger、terminal 状態、single-tenant、budget を確認し、`next_index` から schedule を順番に進める（`orchestrator/campaign/s1_direct_comparison.py:988-1140`）。対象 cell はそのループ内で初めて `prepare_cell()` に渡る（同 `:1142-1151`）。
   - plan は verified freeze の floor schedule から最初の `BACKOFF_FIXED=-1` cell を探索し、その cell を直接 `prepare_cell()` に渡す（`s2-plan.md:72-99`）。実 ledger の `next_index`、先行 cell の verifier/oracle failure、budget refusal により、その cell が production 実行で選ばれない、または到達不能になる経路を丸ごと省いている。
   - 一度その exact cell を選んだ後の `cell`、pin、compiler、`condition_use_class="certified-selection"` は production と一致する。問題は root 束縛の模造ではなく、production 制御フローからの到達性を仮定している点である。
   - 成果物への影響: green は「選んだ一 cell の `prepare_cell()` gate が通る」だけを支持し、s1 driver の production entry-to-gate liveness を支持しない。

4. **[refuted] node-local clone への移設自体は root 束縛の monkeypatch ではない。**

   - 根拠: plan は clone 内の production module を importし、`buildcache._ccbench_dir()` や `ROOT/external/ccbench` を置換しない（`s2-plan.md:103-111`）。s1 は常にその module の `ROOT/external/ccbench` を base に checkout する（`s1_direct_comparison.py:815-819`）。sweep/repro も production 関数内で `buildcache._ccbench_dir()` を呼ぶ。
   - 成果物への影響: exact HEAD、pin、source bytes の preflight が実装どおりなら、絶対パスが `/scr` に変わることだけで模擬測定にはならない。

## 緑の意味

1. **[real] `stock_comparison` は evaluator の分岐スイッチではなく、inert 分類に対する整合性表明である。**

   - 根拠: request validation は `stock_comparison=True` なのに requested/default が inert でない場合だけ拒否する（`orchestrator/campaign/condition_meaning_gate.py:904-936`）。実際の stock 比較分岐は `request.stock_comparison` ではなく `_is_inert_value(spec, requested, default)` で決まる（同 `:962-970`, `:1812-1817`, `:2501-2518`）。
   - `BACKOFF_FIXED=-1` は spec 自身の inert value なので、flag が false でも evaluator は stock 経路を選ぶ。s1 はさらに `default_value=-1` も持つ。
   - 成果物への影響: 「`stock_comparison=True` が stock 経路を発火させた」ではなく、「実 request は同 flag を持ち、requested value の inert 分類により stock 経路が実行された」と記録すべきである。

2. **[real] supply 腕は本物の requested/stock owner-TU preprocessing を比較する。**

   - 根拠: requested root は patched source、control root は別 stock root、control define は無指定となり（`condition_meaning_gate.py:1811-1817`）、両方を別 CMake configure に通す（同 `:1839-1848`）。owner TU の compile command、macro value、patch edit surface と dependency closure の交差を検査する（同 `:2160-2272`）。inert green は bytes 完全一致か、closure に束縛された root-location-only 差だけである（同 `:2613-2655`）。
   - 成果物への影響: supply green は単なる request 生成確認ではなく、exact source/stock/compiler/configure 条件での実比較を支持する。

3. **[real] meaning 腕は production owner-TU の実行や stock tree との比較ではない。**

   - 根拠: `BACKOFF_FIXED=-1` では patched source の `include/backoff.hh` 等を captureし（`condition_meaning_gate.py:3371-3376`）、materialized conditional を抽出して一時単独 TU として `-DBACKOFF_FIXED=-1` で preprocessする（同 `:2697-2750`）。選択 branch と stock branch の文面を確認するが、stock root、CMake configure args、実 owner-TU compile commandは使わない（同 `:2760-2811`）。
   - 成果物への影響: meaning green は「materialized source の `-1` branch が exact adaptive statementを選ぶ」証拠であり、runtime reachabilityや workload 実行時の adaptive 動作の証明ではない。

4. **[real] `unestablished` は use class に関係なく admission を通る。**

   - 根拠: raw と promotion use class は名前の受理にしか使われない（`condition_meaning_gate.py:3427-3430`, `:4019-4022`）。admission は supply がすべて green、meaning が green または `unestablished` なら `admitted=True` になる（同 `:4048-4058`）。`certified-selection` でも規則は同じである。
   - 成果物への影響: family の `admitted=True` を「全 macro の意味が確立済み」と解釈してはならず、`unestablished_meaning_macros` を必ず成果物に残す必要がある。

5. **[refuted] 対象の `BACKOFF_FIXED=-1` request 自体が `unestablished` のまま admission を通る経路は、3 driver の現行呼び出しにはない。**

   - 根拠: sweep/repro 共通 helper は `-1` request に `STOCK_ADAPTIVE_BRANCH` の `MeaningWitnessDeclaration` を明示する（`backoff_sweep.py:117-150`）。s1 も registry declaration がない場合に `_condition_meaning_declaration()` を使い、`-1` の同 declaration を作る（`s1_direct_comparison.py:229-246`, `:280-287`）。evaluator は matching case が一つなら実 branch witnessを走らせ、成功は green、失敗は redであり、`unestablished` にはしない（`condition_meaning_gate.py:3359-3424`）。
   - 成果物への影響: probe が target request digest の meaning recordまで照合する限り、「admittedだが target inert meaning は何も検査していない」という形は成立しない。他 macro の unestablished は別問題である。

## 恒真な保証

1. **[real] fresh worktree直後の pinned-clean 検査は入力意味の保証にならない。**

   - 根拠: `patchharness.checkout()` は指定 pin で新規 detached worktree を作り、直後に `assert_pinned_clean()` を呼ぶ。実装コメント自身が「worktree は必ず真」としている（`orchestrator/campaign/patchharness.py:345-372`）。
   - 成果物への影響: この green は checkout 機構の健全性確認にはなるが、inert source/stock 同値性の証拠として数えてはならない。

2. **[real] s1 の「選択 cell が `BACKOFF_FIXED=-1`」確認は選択式から恒真である。**

   - 根拠: plan は同じ条件を満たす最初の row を `next()` で選ぶ（`s2-plan.md:74-84`）。選択後にその flag を記録しても、production schedule がその cell に到達したことは証明しない。
   - 成果物への影響: request 値の記録は必要だが、driver reachability の独立検査とは扱えない。

3. **[real] admission が観測 record ID を参照することは、同じ producer が返した admission の自己整合性である。**

   - 根拠: `require_condition_gate_family()` は渡された records からそのまま `record_ids` を構築する（`condition_meaning_gate.py:4059-4073`）。plan の「両 record ID を参照する admission」検査（`s2-plan.md:144-150`）は、record の source/stock 意味を独立に再検査しない。
   - 成果物への影響: association の取り違え防止には有効だが、arm の green 判定そのものとは別の保証として数えるべきである。

4. **[refuted] supply/meaning の green 自体は恒真ではない。**

   - 根拠: configure、owner entry、define、dependency closure、preprocess bytes、branch bodyの各不一致は具体的な red reasonへ落ちる（`condition_meaning_gate.py:2488-2655`, `:2697-2811`）。
   - 成果物への影響: fresh checkout等の恒真検査を除けば、中心となる両 arm は実入力に依存した検査である。

## アンカーの誤り

1. **[real] brief の s1 stock-root 条件は誤り。plan の補正が正しい。**

   - 根拠: brief は「flags が既定値に一致する場合だけ」とする（`brief.md:36`）。実際は condition macro のいずれか一つについて、`BACKOFF_FIXED=-1` またはその macro の既定値との一致があれば stock checkout を作る（`s1_direct_comparison.py:821-828`）。flags 全体一致ではない。
   - 成果物への影響: s1 の被覆分類は cell 全体の default/non-default ではなく、各 condition macro の存在と値で行う必要がある。

2. **[real] repro の「resolve なし」は gate が実際に保持する root については誤り。**

   - 根拠: driver は `buildcache._ccbench_dir()` の文字列をそのまま渡す（`backoff_repro.py:66-74`）が、`capture_define_inputs()` は source/stock の両方を `resolve(strict=True)` して canonical pathを保存する（`condition_meaning_gate.py:792-831`）。
   - 成果物への影響: 表は「driver 呼び出し時は未 resolve、captured source root は resolve 済み」と訂正すべきである。

3. **[real] brief の関門呼び出し行範囲は三箇所ともずれている。**

   - 根拠:
     - sweep の helper call は `backoff_sweep.py:378-392`。brief の `:371-386` は FetchContent 準備から始まり、`cxx`、use class、configure args の末尾を落とす。
     - repro の context 関数は `backoff_repro.py:63-84`、helper call 自体は `:72-83`。brief の `:66-88` は後続 `_genomes_reversed()` まで含む。
     - s1 の helper call は `s1_direct_comparison.py:916-921`。brief の `:915-921` の line 915 は patch contextへの enterである。
   - 成果物への影響: review anchor は上記の exact 範囲へ直す必要がある。

4. **[refuted] configure 引数と use class の主要記述には実質的な誤りはない。**

   - 根拠: sweep だけが `-DFETCHCONTENT_BASE_DIR=...` を gate に渡す（`backoff_sweep.py:366-391`）。repro/s1 は configure args を渡さない（`backoff_repro.py:72-83`, `s1_direct_comparison.py:275-277`）。s1 production role は develop が `raw`、それ以外が `certified-selection` であり、plan の floor 指定は一致する（`s1_direct_comparison.py:1005`, `:1147-1151`）。
   - 成果物への影響: この三項目については plan の値をそのまま evidence metadata に使える。

5. **[real] brief の「3 driver とも inert request は作られる」は driver-wide には広すぎる。**

   - 根拠: sweep/repro の production genome列には必ず `-1` がある（`backoff_sweep.py:193-202`, `backoff_repro.py:87-94`）。一方 s1 は cell flags に含まれる condition macro だけを request化し、`BACKOFF_FIXED=-1` の cell に限って stock requestを作る（`s1_direct_comparison.py:184-210`）。
   - 成果物への影響: s1 については「選択した inert cell では request が作られる」と限定すべきである。

## 被覆の表

| driver / 分岐 | 実際の root・request 束縛 | plan の被覆 | 判定 |
|---|---|---|---|
| `backoff_sweep` screening | 共有 sourceを current pin でpatch、別 stock checkout、prepared FetchContent、`(-1, selected fixed)`（`backoff_sweep.py:329-392`） | `write-heavy`, fixed=2 の exact 分岐を被覆 | exact inert arm は被覆 |
| `backoff_sweep` 通常 full sweep | root/compiler/configure は同じだが request family は `-1,2,5,10,25,50,100`（同 `:193-202`, `:378-392`） | fixed=5以降を省略 | full family admission は未被覆 |
| `backoff_sweep` 3 workload | workload は config/perfへ流れ、gate rootや inert request値へ直接流れない（同 `:322-392`） | write-heavyのみ | 同 pin/site/compiler の inert armへの workload一般化は概ね成立。ただし実行時外部状態は一回分 |
| `backoff_repro` write-heavy | patched shared root、historical `dff0f1e` stock、値順 `10,5,-1`（`backoff_repro.py:46-48`, `:63-94`） | 被覆 | seam の exact inert armを被覆 |
| `backoff_repro` balanced | 同じ値集合で順序だけ `5,10,-1`、root/configureも同じ | 未実走 | 静的な inert recordは同型だが、二回目への到達性と時間依存は未被覆 |
| s1 共通 checkout | sourceは常に一時 checkout。該当 condition macro のいずれかが inert/defaultなら別 stock checkout（`s1_direct_comparison.py:818-828`） | 選択した一 cell のみ | 他 cell の stock-root 有無は未被覆 |
| s1 `system_gate` / `ident_all` | trigger templateをapplyし、cell固有 predicateを quarantine/materialize（同 `:833-845`, `:863-873`） | 選択 cell が該当する場合だけ | 他 predicate/configurationは未被覆 |
| s1 `sort_best` | sort template、cell固有 comparator、SWO oracleを gate 前に実行（同 `:846-852`, `:863-912`） | 選択 cell が該当する場合だけ | 他 comparatorとoracle経路は未被覆 |
| s1 `backoff_fixed_best` | backoff templateのみapply。値は非負で flags と一致必須（同 `:853-861`, `:913-915`） | `-1` 選択条件上、この構成自体は対象にならない | non-inert patch分岐 |
| s1 `p2_2_flag_opt` / `stock_common` | この関数内では configuration固有patchを追加しない | 選択 cell が該当する場合だけ | 他 cellのsource bytesは未被覆 |
| s1 role 分岐 | develop=`raw`、floor/block=`certified-selection`（同 `:1005`） | floor相当のみ | developと他 scheduleへの一般化は未被覆 |

1. **[real] sweep の green を通常 driver 全体の admission greenへ一般化できない。**

   - 根拠: admission は一 requestだけでなく、その呼び出しに含まれる全 records の conjunctionである（`condition_meaning_gate.py:4040-4054`）。screening は通常 sweep の request familyを縮小する。
   - 成果物への影響: 「sweep inert arm green」は言えるが、「通常 full sweep の family admission green」は言えない。

2. **[refuted] repro の workload差が inert gate入力を変えるという静的反例はない。**

   - 根拠: `ORIG` の二 workload は `best_us` が5/10で入れ替わるだけで、`_genomes_reversed()` が作る値集合は両方 `{5,10,-1}` である（`backoff_repro.py:51-56`, `:87-94`）。gateへ workload dictやtagは渡らない。
   - 成果物への影響: exact source/pin/compilerが同じなら、一方の inert arm結果を他方へ構造上一般化できる。ただし production main の二回目到達性は別に未測定である。

3. **[real] s1 の一 cell greenを driver-wide に一般化できない。**

   - 根拠: configurationごとに patch、quarantine、oracleが異なり、その処理後の `sub` が gate の source rootになる（`s1_direct_comparison.py:829-921`）。さらに request digestの driver IDは configurationを検証するだけで、返却値は全 configuration共通である（同 `:188-191`）。
   - 成果物への影響: s1 evidenceには必ず cell ID、configuration、flags、source hash、freeze pinを付け、「s1 driver全体」ではなくその exact materializationへ主張を限定する必要がある。

## 裁定へ返す候補

以下はすべて scope 外であり、**実装せず裁定へ返す候補**である。

1. **[real] 主張を seam-liveness に狭めるか、production entry-to-gate liveness を実走するか。**

   - 推奨: 本 wave は安全な前者へ狭め、repro は `_conditioned_backoff_patch()`、s1 は exact `prepare_cell()` の liveness と明記する。
   - 成果物への影響: 見出しと総括から「production 入口から到達」を除けば、現 plan の測定との不一致を解消できる。

2. **[real] s1 を一 cellで代表させるか、distinct materializationごとに測るか。**

   - 推奨: 少なくとも `system_gate/ident_all`、`sort_best`、patchなし群について、`BACKOFF_FIXED=-1` を持つ実在 cellがあるなら別々に測る。追加測定を認めない場合は exact cellだけの結論に限定する。
   - 成果物への影響: driver-wide greenの誤一般化を防ぐ。

3. **[real] sweep の family admission を主張に含めるなら full request familyを測る必要がある。**

   - 推奨: この wave では inert arm greenだけを主張し、full admissionは未測定とする。full run追加は一般化・追加計測として裁定対象にする。
   - 成果物への影響: 2点 screening admissionを通常7値 admissionの代用にしなくなる。

4. **[real] promotion use classで `unestablished` を許す現 policyを維持するか。**

   - 推奨: 今回の target inert requestは establishedなので結果を止める必要はない。ただし `certified-selection` 等で他 macroの unestablishedを許す設計判断は別裁定にする。
   - 成果物への影響: admissionを「全意味確立」と誤読する将来リスクを分離できる。

## 総括

静的検査の結論は、**三つの exact gate 呼び出しが模擬物であるという致命傷は見つからないが、wave の driver-wide liveness 主張はそのままでは成立しない**、である。

- sweep は production `run_workload()` を通る。ただし測る admission は縮小 screening familyであり、通常 full sweep の admissionではない。
- repro は production root-binding seamと同じ入力を使うが、production entryからの到達性は測らない。
- s1 はさらに、production ledger/scheduleを迂回して一 cellを直接選ぶため、結論はその exact cellとconfigurationにしか及ばない。
- admissionは一般には meaning `unestablished` を通す。ただし三 driverの対象 `BACKOFF_FIXED=-1` requestは明示 witnessを持つため、target inert meaningが空のまま admittedになる懸念は refuted である。
- greenの意味は「stockとの owner-TU preprocess同値性」と「materialized `-1` branchの静的選択」であり、runtime workloadでadaptive branchが動的に実行された証明ではない。

したがって成果物の安全な表現は、「exact pin/root/compiler/configure条件において、列挙した production seam の inert gate両腕と対応 admissionを観測した」である。「3 driver の production入口から inert経路が通る」または「s1 driver全体が通る」まで広げてはならない。

ファイル編集、commit、push、pytest、計算ノード実測は行っていない。