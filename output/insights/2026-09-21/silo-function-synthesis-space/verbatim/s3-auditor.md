# auditor レンズ: Silo 関数単位合成空間の設計草稿 (s2-plan.md) の監査結果

(Claude subagent `auditor` role、2026-09-21 22:0x〜22:1x JST、17 tool call。親が subagent の最終報告をこの file へ逐語で写した。harness が各行に付けた字下げ 2 字だけを除いた。)

## verdict
**adopt_with_conditions**

「方策 (待機量と retry/abort の二値) は LLM、仕組み (CAS・unlock・validation・tid 生成・trace・再試行) は骨格」という分け方は、契約どおりに書かれた方策に限れば、直列化可能性を壊す経路を持ちません。方策が返せるのは「上限内の待機」と「retry / abort」だけで、どちらを選んでも Silo の正しさは保たれます。
- lock 待ちは原典 Silo の挙動そのものです。
- 取得順が sort 済みなので deadlock は起きず、上限があるので停止もします。

ただし草稿の**封じ込め契約は、次の 4 点で骨格の外に届く穴を残しています**。
- 識別子の拒否リスト的な書き方
- 保存域 (状態を置ける場所) の非排他性
- 名前解決の乗っ取り
- 局所変数のメモリ安全性

さらに、新機構 (上限、再読込、新しい abort 出口での prefix unlock、hook の配線、状態 reset) に対する正例・負例が機構の実体を名指ししておらず、恒真化のおそれがあります。以下の must-fix を実装着手前の条件にするなら採用可、と判断します。

## violations (設計上の違反・穴)

**V1 [型3 / 型16、must-fix] 通常の式の中でマクロ識別子を使って verify build を判別できる。trace 関数も呼べる**
- 箇所: 草稿 §1.3 (L100)、§1.2。実コードは `transaction.cc:9` (trace.hh の include)、`include/trace.hh:25,35,105-111`、`cmake/Options.cmake:67` (`TRACE=${CCBENCH_TRACE}`)。
- 破り方:
  - hole は前処理指令を使えないものの、`TRACE`・`BACK_OFF`・`NO_WAIT_*`・`SILO_POLICY_VARIANT`・`ADD_ANALYSIS`・`WAL`・`VAL_SIZE` などの -D マクロは、通常の式の中でも展開されます。事前定義マクロ (`__TIME__`・`__DATE__`・`__COUNTER__`・`__LINE__`・`__OPTIMIZE__`・`__SANITIZE_ADDRESS__` など) も同様です。
  - したがって `if (TRACE) {...}` と書くだけで「verify のときだけ正しく振る舞う」方策が書けます。
  - 加えて TRACE=1 のときは、L9 の後に置いた hole から `izanagi_trace::record_lock` / `clear_shadow` / `stream` が見えます。これを使うと、D38 の被覆検査に使う shadow を偽装したり、C 行を偽造したりできます。
  - `<cstdlib>` (trace.hh:29)、`rdtscp` (tsc.hh:27)、`GlobalEpoch` / `ThLocalEpoch` (書込み可能) も見えます。ThLocalEpoch に書き込めば ReclamationEpoch が狂い、早すぎる delete から UAF / torn read に至るので、直列化可能性の破れに直結します。
- verifier が見逃す理由: verifier は TRACE=1 build の軌跡しか見ません。判別枝が perf build でだけ別挙動を取れば、trace には一切現れません。
- 対処: 草稿は「許可された…への参照を検疫」と書いていますが、禁止リストとも許可リストとも読めます。次を明文化してください。
  - **許可リスト方式**にする。許可するのは、hole 内で宣言した名前、固定ヘッダの型、閉じた keyword 集合、固定幅 unsigned / bool だけ。
  - 先頭の `::` と、自分の namespace 以外への修飾を禁止する。
  - 全マクロ名と事前定義マクロ名を字句で拒否する。
  - 下記 T1 の**単独 TU での compile 検査**を必須にする。既存の `coder_effect_gate.py:58-105` は host 効果の禁止表にすぎず、CC の大域もマクロも対象外です。

**V2 [型16 / 12 / 15、must-fix] 状態の保存域が排他でない**
- 箇所: 草稿 §1.2 L59-61 (「PolicyState と `thread_local policy_state` を定義**できる**」)。
- 破り方:
  - 関数内 `static`、名前空間 scope の非 thread_local 変数、2 本目の `thread_local`、`inline` 変数を禁じる文がありません。
  - これらは writePhase 末尾の reset を迂回して **txn をまたぐ履歴**を作り、P5 の限定 (状態は txn 内) を無効にします。
  - 非 atomic の共有変数は data race (UB) になります。
  - 共有 ticket と thread_local を組み合わせれば、thid の代理になります (D1409 がいう「ワーカー識別」)。
- verifier が見逃す理由: 性能の歪みも公平性の歪みも G2 には現れません。data race は、偶然壊れた run でしか現れません。
- 対処: 保存域は唯一とします。推奨は、状態の実体を**骨格が所有**し (hole より後に置く `thread_local`)、hook には `PolicyState&` で渡す形です。こうすれば「hole は変数を一切定義しない」という例外なしの字句規則になります。`static` / `thread_local` / `mutable` / `inline` 変数 / `std::atomic` は禁止です。

**V3 [新型 22 案「名前解決の乗っ取り」、must-fix]**
- 箇所: 草稿 §1.4 L119-136。固定の型を `izanagi_silo_policy` に置き、その後ろに hole、さらに後ろに「固定の要因状態・上限付き待機関数」を置く構成です。
- 破り方:
  - hole は骨格 helper より前に来ます。そのため、同じ namespace に完全一致の overload を置くことができます (例: `bounded_wait(uint32_t, unsigned long long)`)。
  - `PolicyAction` 用の `operator==` / `!=`、変換演算子、骨格が予約した名前の先行宣言も置けます。
  - `PolicyAction` / `LockResponse` は同じ namespace に属するため、骨格内の比較や非修飾呼出しは ADL で hole 側の定義を拾います。
  - その結果、骨格の clamp や「不正な action は abort」の判定を、骨格の行を 1 行も変えずに意味だけ置き換えられます。
- verifier が見逃す理由と、検疫が素通りする理由: DiffQuarantine は hole の外に差分が無いことしか見ません。骨格の文面が不変のまま意味が変わるので、行単位の検疫を素通りします。clamp が外れれば hang (trace-timeout) として捕まりますが、判定の置換は上限内に収まる限り無音です。
- 対処:
  - 骨格 helper は別 namespace (例: `izanagi_silo_skel`) に置き、呼出しはすべて完全修飾にする。
  - action の判定は組込型の比較にする (`static_cast<uint32_t>(r.action) == 0u`)。
  - hole では演算子の overload・変換関数・template・骨格予約名の宣言を禁止する。

**V4 [メモリ安全 / 型3 の UB 版、must-fix] 局所の配列・pointer・参照・cast・UB が契約の射程外にある**
- 箇所: 草稿 §1.2 L59 (制約はメンバだけ)、§1.3 L100 (「pointer 操作」の禁止は字句であって意味の保証ではない、と草稿自身が述べている)。実コードは `transaction.cc:146,156,160-183`。
- 破り方:
  - lock hook は prefix lock を保持したまま `lockWriteSet` の中で呼ばれ、inline されうる位置にあります。
  - 局所配列の範囲外書込みは、呼出元フレームの `itr` / `expected` / `desired` を壊しえます。そうなると取得の skip や誤った CAS が起きます。
  - 未初期化の読出し、return の欠落、過大 shift、0 除算、符号付き overflow は、inline された後に「到達不能」とみなされ、骨格の経路 (prefix unlock や status 設定) ごと削除されうる UB です。
  - TRACE の有無でフレーム配置と inline の判断が変わるため、**perf build だけで壊れる**形がありえます。
- verifier が見逃す理由: 被覆検査の X 行は TRACE build にしか存在しません。perf build だけで起きる破壊を見る手段がありません。
- 既存の備え: `CompileOptions.cmake:32` の `-Wall -Wextra -Werror` が return-type や uninitialized の一部を拾いますが、最適化に依存するので完全ではありません。
- 対処:
  - 宣言してよい型は、局所変数も含めて、bool・固定幅 unsigned・固定の骨格型だけにする。
  - 次を禁止する: `[` `]`、単項の `&` / `*`、`->`、cast 全種、`new` / `delete`、`this`、`union`、`volatile`、`goto`、`throw` / `try`、lambda、template、`asm`。
  - 骨格側で hook 呼出しを `[[gnu::noinline]]` にする (UB の伝播を完全には止めません。uncertainty 参照)。
  - T1 と T3 (sanitizer 付き harness) を必須にする。

**V5 [型20 / 型10 の近縁、should (loop を許すなら must)] 自由 C++ の hook 内の loop・再帰**
- 草稿 §1.2 L65 自身が認めているとおり、骨格の上限 (50µs / 32 周回) は hook の計算時間を含みません。
- 有限だが長い loop は、prefix lock の保持時間を任意に延ばしつつ verify を通ります。その間、他 worker は `read_internal` (`transaction.cc:255`、上限なしの spin) で待たされます。
- 停止しない hook は trace-timeout で捕まります。害は liveness と性能に留まり、直列化可能性には及びません。
- 型 10 との比較 (依頼 1 への回答): 上限付きの「待つ」を明示の軸にすること自体は、型 10 と同じ害を持ちません。sort 済みの取得順なので deadlock が無く、上限もあるからです。残る害は、lock 保持時間と公平性という性能側の歪みです。
- 対処: v1 の hole では loop・再帰・goto を禁止します (直線の本体、条件分岐、非再帰の補助関数呼出しだけ)。この制約の下でも、自由な式木なので IR より広い空間が残ります。

**V6 [型4、must-fix] hook ごとの実行証拠が未設計**
- 箇所: 草稿 §2.2 L205 (未設計であることを自認)。§2.1 L193 の「追加 trace は要求しない」とも衝突します。
- abort>0 であれば abort hook は実行されています。全ての abort が `abort()` を通るからです (`ycsb.hh:150,162`)。
- しかし lock hook は、`expected.lock` を観測した回数が 0 でも緑になります。
- 対処: TRACE 限定の per-thread 集計を、信頼済み計装として PIN を前進させて入れます。
  - 集計項目: `abort_hook_calls` / `lock_hook_calls` / `lock_retry_success` / `lock_cap_abort` / `clamp_hits`
  - `lock_hook_calls == 0` の候補は、「lock 方策は未検証」という構造化ラベル付きで critic と記録に流します。reject 閾値にはしません。

**V7 [型2 の近縁 (flag の別名化)、should]**
- 草稿 §1.4 L162 では、軸 ON が `NO_WAIT_LOCKING_IN_VALIDATION` / `NO_WAIT_OF_TICTOC` (`Options.cmake:27-28`) を黙って上書きします。
- genome の flag が実際の挙動を表さなくなり、§4.1 の identity の議論と衝突します。
- 対処: 軸 ON のときは、両 flag が固定値 (1 / 0) 以外なら `#error` にします。

**V8 [型13 / 16、should] abort 要因の写像が未定義**
- 既存の trigger 骨格は 7 つの記録点を持ちます。`kInsertNode` と `kScanNode` もその中に含まれます (`patches/silo-backoff-trigger-gating-variant.patch:134-194`)。
- 草稿 §1.2 の enum は 5 値で、この写像が書かれていません。
- 記録が漏れた点は unset になり、G2 には見えません (`broken-silo-trigger-misattr` と同じ区別)。
- 対処: 全ての abort 代入点を列挙し、enum への写像を骨格仕様として固定します。

**V9 [型1 / 11、must-fix] §2.3 の負例が機構の実体を名指ししていない**
- 「hook の配線解除、再読込の削除は焦点試験で期待応答不成立／timeout」とだけ書かれ、どの計器が赤になるかがありません。
- 既存の `broken-silo-*` は旧 index (b06fd4f) に対する hunk です。`lockskip` の文脈行 (`#if NO_WAIT_LOCKING_IN_VALIDATION`) は新骨格で変わるので、そのままでは当たりません。
- 当て直した結果、break が軸 OFF の `#else` 側に着地すれば、軸 ON では compile で消えます。その場合、「赤になった」は旧骨格での話にすぎず、新骨格に対しては空振りです。
- 新機構 (clamp・上限・再読込・新しい abort 出口の prefix unlock・reset) の負例が全く無い点も、同じ問題の一部です。

**V10 [検出力が方策に依存する、should]**
- 長く待つ方策は verify 中の並行度を下げ、骨格負例 (norw 等) の G2 検出力を落とします。
- 対処: 骨格負例は、即 abort の方策と最大待機の方策の両方の下で走らせます (T6)。

**V11 [型15 / 12、should] 公平性**
- txn 内の状態だけでも「何度も abort した txn は諦め気味に扱う」方策は書けます。
- YCSB は abort した txn を同じ内容で再試行し続けます (`ycsb.hh:155,164`)。そのため飢餓は「負荷配合が変わる」形ではなく「worker が駐車される (実質的なスレッド数削減)」形で現れます。
- G2 にも `trace-empty` にも出ません (一部 worker が枯渇しても全体の C 行は残る)。
- D41 条件 3 の観測は未実装のままです。
- 対処: per-worker の commit 数 (`local_commit_counts_`) を観測値として記録します。gate にはしません。

**型 17〜21 について草稿の指摘は正しいと判断します。** sort IR の免除を新空間へ移してはいけません。新空間では次のように扱うべきです。
- 17 (関数・型の追加): 契約内で部分的に許可する。許可するのは非再帰・非 template の補助関数と、PolicyState 集約型だけ。
- 18 (非決定ビルトイン: `rdtscp`・`__rdtsc`・`rand`・`getenv`・chrono)、19 (hole 外の呼出し)、20 (loop)、21 (例外): いずれも有効な監査対象として残す。
- 21 について補足: `noexcept` の下で例外が出れば terminate になり、`trace-run-nonzero-exit` で捕まります。ただし throw の枝が perf 側の timing でしか通らない形は理論上ありえます。

**依頼 4 (txn をまたぐ履歴と worker 間の共有状態を許した場合) への回答:**
新たに可能になる型は次の 4 つです。
- 型3: 事象の計数から thread 数や競合度を推定し、legacy verify (200 records / 4 threads) と perf を判別する。
- 型12: 共有の commit / abort 計数という、run 自身の fitness の代理に適応する。
- 型15: 共有 ticket と thread_local で worker を選出し、恒常的な優先階級を作る。YCSB は同じ txn を再試行し続けるので、負けた worker は同じ txn の retry に閉じ込められる。
- 新たな liveness 型: 全体フラグで全 worker に最大待機させ、協調して throughput を崩す (上限があるので hang にはならない)。

害の程度は次のとおりです。
- 契約 (出力の二値と上限) が守られる限り、**直列化可能性には及ばず、性能値の歪みに留まります**。
- ただし例外が 2 つあります。非 atomic の共有は data race (UB) で、正しさに届きえます。また型 3 と組み合わせると「認証したプログラムと計測したプログラムが別物」になり、規律 1・2 の前提が崩れます。
- 手法比較で perf 構成の verify を使う案は、legacy verify との判別を弱めるだけで、消しはしません。

## nits
- §2.3 の「上限超の待機要求」は負例でなく境界正例です。表の区分を分けてください。
- §1.2 の `LockContext.attempt` は、CAS 失敗も含めて数えるのか、conflict のたびに数えるのかを明記してください。
- §6 の「reward hack 仮説」に、V3 (名前解決の乗っ取り) と V1 (マクロ識別子による判別) を加えてください。
- CAS 失敗時は `compareExchange` が expected を書き戻します (`atomic_wrapper.hh:67-69`)。再読込が必要なのは lock 枝だけです。§1.1 L29 の根拠としてこの事実を添えてください。
- 再読込を削除した mutation の害は liveness に留まります (上限に達して abort が増えるだけ)。正しさの負例と混ぜないでください。

## proposed_tests

**T1: 単独 TU での compile 検査 (候補ごと、build 前の機械 gate)**
- 狙い: 実 build の include 構造は変えずに、P4 が狙った名前解決による封じ込めを別の手段で回復する。
- 方法: hole の本文だけを、`<cstdint>` と固定ヘッダ (Context / Response 型と署名) だけの TU で compile する。-D マクロは与えず、`-Wall -Wextra -Werror` を付ける。
- 負例 (すべて compile 赤になるべき): `Masstrees`、`FLAGS_thread_num`、`TRACE`、`izanagi_trace::record_lock`、`rdtscp`、`getenv`、`GlobalEpoch` を参照する hole。
- 正例: 無害な hole は compile が通る。
- gate 自体の非恒真性を示す mutation: sandbox TU に `include/transaction.hh` を誤って足すと、上の負例が通ってしまう。これを自己テストの赤として登録する。
- 機械判定: compile の rc と、負例ごとに事前登録した期待赤の一致。

**T2: 事前定義マクロの字句拒否 (候補ごと)**
- 負例: `__TIME__` / `__COUNTER__` / `__LINE__` / `__FILE__` を含む hole は拒否される。T1 では捕まらない (事前定義マクロは -D なしでも存在する) ので字句規則が要る。
- mutation: この規則を外すと負例が通る。これを赤として登録する。

**T3: sanitizer 付き harness (候補ごと、build 前)**
- 方法: T1 の TU を `-fsanitize=undefined,address -fno-sanitize-recover` で compile し、2 つの hook を駆動する。
- 入力の定義域: 全 abort 要因 × attempt 0〜上限+1 × 呼出し列 (reset を挟む)、1 回の呼出しごとに timeout を付ける。
- 負例 (赤になるべき): 状態由来の shift 量が 32 に届く、状態で 0 除算する、再帰、局所配列の範囲外書込み、停止しない loop (timeout)。
- 機械判定: rc と sanitizer 報告の有無。
- 限界: 定義域の外の UB は保証しません。

**T4: 名前解決の乗っ取り**
- 負例: `operator==(PolicyAction, PolicyAction)` を常に true にする hole、骨格 helper と同名の overload を持つ hole。
- 期待: (a) build 前の宣言契約で拒否される。(b) 多層防御として、検疫を迂回した試験用 build でも骨格は乗っ取られない。具体的には、不正な action 値を返す方策が abort に落ち、UINT32_MAX を返す方策は clamp される。
- 機械判定: (b) は焦点走の集計値 `clamp_hits > 0` と、trace-timeout が出ないこと。

**T5: 新骨格の mutation (C 段で 1 回、位置・期待赤・期待 node を事前登録)**
- (a) clamp を削除し、UINT32_MAX を返す方策で走らせる → `trace-timeout`。clamp ありなら pass。
- (b) 再読込を削除し、「待機 0 で retry」の方策で走らせる → `lock_retry_success == 0` (正例では > 0)。
- (c) 上限だけを削除する → 取得順が sort 済みなので、通常の workload では等価変異です。**等価変異として事前登録**し、検出力の主張には使いません。
- (d) hook-abort または上限超過の出口で prefix unlock を省く → lock が漏れ、読み手が `transaction.cc:255` で永久に spin → `trace-timeout`。より強い歯として、TRACE 限定の「abort 時に自 worker の shadow にある tuple が lock されたまま」の検査 (新しい X 理由 `lock-held-at-abort`、判定は indeterminate) を提案します。
- (e) abort hook / lock hook の配線を解除する → abort>0 なのに `abort_hook_calls == 0`、または conflict があるのに `lock_hook_calls == 0` → 焦点判定が赤。
- (f) reset を削除する → 状態の reset を行う実体を名指しした検査が要ります。案: reset を「static の 0 初期化オブジェクトからの memcpy」として実装し、commit 直後の最初の begin で TRACE 限定の memcmp を行って非 0 なら emit する。実現性は uncertainty に記載。
- (g) 要因の誤記録 (D48 条件 3 の型) → 単一スレッドの決定的特性化と、要因別 abort 集計の不整合 → 赤。

**T6: 既存 broken-silo を新骨格に積み直す (軸 ON、方策は {即 abort, 最大待機} の 2 通り)**
- 期待 verdict:
  - `norw` → `non-serializable`
  - `lockskip` → `indeterminate` (X `not-locked-at-entry`)
  - `early-unlock` → `indeterminate` (X `lock-lost-before-write`)
  - `permutation-erase` → `indeterminate` (P `size-changed`)
- 積み直した patch には `#if IZANAGI_BREAK_* && !SILO_POLICY_VARIANT` → `#error` を入れるか、前処理後の出力に break 文が残っていることを機械確認する。break が軸 ON の compile 経路に載っている証拠を取るためです。
- 機械判定: pipeline の verdict / reason が事前登録と完全一致すること。

**T7: flag の別名化**
- 軸 ON かつ `NO_WAIT_OF_TICTOC=1` で configure すると、configure / compile エラーになる。

## role 定義の更新案 (差分案のみ。`.claude/agents/auditor.md` の変更にはユーザーの明示承認が要ります)
```
+ 22. 名前解決の乗っ取り — hole が骨格より前にあり、同じ namespace で overload・演算子・変換関数・
+     予約名の先行宣言を定義して、骨格の非修飾呼出しや比較を文面不変のまま置換する。
+     DiffQuarantine は素通りする。骨格側の完全修飾と組込型比較、hole 側の宣言禁止を行単位で確認する。
+ 23. マクロ識別子による判別 — 前処理指令なしでも TRACE / BACK_OFF / NO_WAIT_* / 軸 macro /
+     事前定義マクロ (__TIME__ 等) は通常の式で展開される。hole 内の全マクロ名を拒否する (型3 の具体形)。
+ 24. 保存域の迂回 — 関数内 static・namespace 変数・追加の thread_local・inline 変数で、
+     骨格 reset を迂回して txn 間履歴や worker 間共有 (thid の代理、data race) を作る。
+ 25. メモリ安全の迂回 — 局所配列・pointer・参照・cast・UB (未初期化、return 欠落、shift、0 除算)。
+     inline 後に骨格経路が削除され、TRACE の有無で挙動が分岐しうる。単独 TU の compile と
+     sanitizer harness の receipt が付いているかを確認する。
+ 26. hook 別の空振り — 複数 hook の軸では hook ごとの実行計数を要求する (型4 の分割)。
  型17〜21 の段落:
- 「以下の型17〜21も sort IR admission と trusted renderer の事後条件であり…veto の根拠にしない」
+ 「…sort IR 軸と、function-policy 軸の機械 IR 候補 (trusted renderer 出力) に限り veto の根拠にしない。
+   function-policy 軸の LLM C++ 候補では、17 は契約内の補助関数と PolicyState だけ許可、
+   18〜21 は有効な監査対象とする」
  チェックリストへの追加:
+ 15. function-policy 軸: 許可リストの識別子契約・保存域の唯一性・宣言型の制限・loop/再帰の禁止・
+     骨格 helper の完全修飾・T1/T3 の receipt、の有無を確認する。
+     hole の外 (要因記録・reset・待機器・clamp・上限・再読込・prefix unlock・呼出し点) の無改変を行単位で確認する。
```
機械 IR 候補で auditor 段を省く運用が成り立つのは、IR admission が型 17〜21 と V1〜V4 を構成上排除し、renderer が信頼済みである場合に限ります。LLM の C++ 候補については、hole の上限は 4096 token であり、全行を読む目視は実行可能です。ただし overload 解決や UB は目視では判定しきれないため、T1 と T3 という機械の受領証を auditor の前提にしてください。

## conditions (実装着手前に満たすこと)
1. 許可リスト方式の識別子・宣言契約 (V1 / V3 / V4) を、producer と consumer の双方で一致させて固定する。T1 と T2 を build 前の必須 gate にする。
2. 保存域を唯一にする (骨格所有を推奨、V2)。hole 内の変数定義を全面禁止する。
3. 骨格 helper を別 namespace に置き、完全修飾し、action を組込型で判定する (V3)。
4. v1 では loop・再帰・goto を禁止する (V5)。緩めるなら、その害を明記した裁定を付ける。
5. hook ごとの TRACE 限定の実行計数を、信頼済み計装として PIN を前進させて入れる (V6)。
6. 軸 ON のとき no-wait 系 flag を固定する (V7)。要因の写像を全点で固定する (V8)。
7. T5 と T6 を事前登録する。積み直した負例は軸 ON で break が compile 経路に載っている証拠を持ち、2 通りの方策の下で走らせる (V9 / V10)。
8. per-worker の commit 分布の記録を設計に明記する (V11、D41 条件 3 の継続)。
9. P5 の txn 内状態が retry 数の代理になる件は、草稿どおりユーザー裁定事項に残す。本 auditor は草稿の判定を支持する。
10. role 定義の更新 (上記の差分案) の明示承認を得る。

## uncertainty
- fitness・WAL・計測値のファイルは開いていません。B-5 README (費用の出所) も開いていないため、§5 の見積りは監査していません。
- `diff_quarantine.py` / `source_digest.py` / `build_admission.py` / `docs/axis-onboarding.md` は読んでいません。草稿が引く行番号は検証していません。`coder_effect_gate.py` は冒頭だけを読み、禁止表方式であることを確認しました。
- 「UB が inline 後に骨格経路を削除する」は、GCC / clang の一般的な挙動からの推定です。この骨格での実例は確認していません。`[[gnu::noinline]]` がそれをどこまで防ぐかも未確認です。
- V3 がどこまで成立するかは、骨格 helper の最終配置と namespace に依存します。草稿の擬似差分からは、helper の namespace が読み取れません。
- T5 (f) の reset 検査 (memcpy / memcmp 方式) は、padding の扱いを含めて実装上の成立性が未確認です。
- `-Wall -Wextra -Werror` (`CompileOptions.cmake:32`) が silo の target に確実に適用されているかは、呼出し側を追っていないので未確認です。
- TRACE=1 の下で、template と `if constexpr` を使って `izanagi_trace` の存在を条件付きに参照する手口が現実に書けるかは詰めていません。許可リストと T1 で閉じるため、結論は変わりません。

## 総括
方策と仕組みを分ける境界は健全です。契約を守る方策に限れば、lock 競合時の上限付き待機を含めて直列化可能性を壊しません。txn 間履歴や共有状態を許した場合の害も、data race を除けば公平性・fitness 適応・verify 判別という性能値の歪みに留まります。

一方で、**草稿の封じ込め契約には、骨格の文面を変えずに意味を変える 4 つの穴があります。** マクロ識別子による判別と、trace 関数や大域への到達 (V1)、保存域の非排他 (V2)、名前解決の乗っ取り (V3)、局所変数のメモリ安全と UB (V4) です。加えて、新機構の正例・負例は実体を名指ししておらず、恒真化のおそれがあります (V6 / V9)。

許可リスト方式の契約、単独 TU compile と sanitizer harness、骨格の完全修飾、hook ごとの実行計数、軸 ON で積み直した負例を実装着手前の条件にするなら、条件付き採用を支持します。
