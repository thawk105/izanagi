結論として、hole 実装の単一 materialization seam は `orchestrator/campaign/p3_s4_loop.py:192-243` の `quarantine()` で確定できる。ただし提案する denylist は「有限で閉じた規則集合」であり、任意の C++ が起こす host 効果を意味論的に閉じるものではない。この限界は実装・テスト・docstring に明記する。

以下の行番号は編集前の現行スナップショットを基準とする。

## 1. W-1: coder 効果 gate

### 1.1 単一 seam の確定

- 編集ファイル: `orchestrator/campaign/p3_s4_loop.py`
- file:line: `169-189`, `192-243`, `890-915`
- 変更内容:
  - coder の `implementation` は `render_hole()` を経て `quarantine()` 内でのみ source へ materialize される。
  - `quarantine()` は template 読み込み、hole render、structural quarantine、`res.passed` 後の書き込みを一か所で実施している。
  - 効果 gate を structural quarantine 成功後、`write_text()` の前へ組み込む。
- 理由:
  - `render_hole()` の production 呼び出しは `p3_s4_loop.py:236` の一か所だけであり、ここで拒否すれば coder hole bytes が source/build へ届かない。
  - dry/build の双方が `p3_s4_loop.py:894,902` から同じ seam を通る。
- リスク:
  - 将来 `render_hole()` や template への直接書き込みが追加されると seam が破れる。呼び出し元一意性を静的テストで固定する。

確認した周辺経路:

| 経路 | file:line | 判断 |
|---|---:|---|
| sort campaign | `p3_s4_loop_sort.py:141-168`, `248-259` | `L.quarantine()` 成功後だけ build。seam 内へ gate を置けば迂回不能 |
| trigger gating | `p3_s4_loop_trigger_gating.py:395-445` | coder は `114-127`, `685-717` の 5-bit wire。trusted emitter の出力も同じ seam を通る |
| autonomous preview | `p3_autonomous_workload_trial.py:335-356`, `652-673`, `1773-1817` | raw implementation を受けず、emitted predicate を `L.quarantine()` へ渡す |
| sort sweep | `s6_sort_sweep.py:316-389` | baseline/evaluation とも `326-327`, `347-348` で seam を通り、その後 build |
| trigger sweep | `s8a_trigger_sweep.py:418-490` | baseline/evaluation とも `429-430`, `451-452` で seam を通る |
| permutation coverage | `s5_permutation_coverage.py:138-188` | trusted な固定 broken patch を直接作る non-admissible materializer。coder hole 入力を消費しないため W-1 の迂回ではない |
| direct comparison | `s1_direct_comparison.py:530-570` | sort/trigger の materialization は `565-567` で seam を通る。backoff は trusted static patch |
| calibration | `s1_verify_extime_calibration.py:336-360` | canonical trigger predicate を `342-345` で seam に通す |

### 1.2 有限 deny policy と C++ lexer

- 編集ファイル: `orchestrator/campaign/coder_effect_gate.py`（新規）
- file:line: `new:1-310`
- 変更内容:
  - `new:1-28`: 「有限 lexical deny policy であり、host-security boundary ではない」という契約を書く。
  - `new:30-85`: 固定 rule ID、category、reject finding の型と deny table を定義する。
  - `new:87-205`: C++ の identifier、punctuator、数値、通常・prefix・raw string/char、comment、空白を区別する tokenizer を実装する。
  - `new:207-275`: exact-token 効果検出と明示的な無条件 loop header 検出を実装する。
  - `new:277-310`: `scan_host_effects(implementation)` を公開する。返却値に元 token/string を含めない。
- 理由:
  - `std :: system` の空白差を正規化でき、`ecosystem` や文字列中の `"system"` は拒否しない。
  - 全 identifier 出現を調べるため、呼び出しだけでなく `auto f = &std::system` も拒否できる。
  - lexer が解釈できない token/string は固定 subtype で fail-closed にする。
- リスク:
  - exact identifier でもローカル変数名 `open` などは偽陽性になり得る。既存の正常 candidate 全件を正例として固定する。
  - これは C++ の型・マクロ展開・間接呼び出しを解決する semantic analyzer ではない。

閉じた規則集合は次のカテゴリとする。表の識別子は exact token のみを拒否する。

- process/shell:
  `system`, `popen`, `pclose`, `fork`, `vfork`, `clone`, `clone3`,
  `execl`, `execle`, `execlp`, `execv`, `execve`, `execvp`, `execvpe`,
  `fexecve`, `posix_spawn`, `posix_spawnp`, `wordexp`
- file/stdio:
  `ifstream`, `ofstream`, `fstream`, `filebuf`, `basic_ifstream`,
  `basic_ofstream`, `basic_fstream`, `basic_filebuf`, `fopen`, `freopen`,
  `fdopen`, `tmpfile`, `open`, `openat`, `creat`, `read`, `write`,
  `pread`, `pwrite`, `readv`, `writev`, `fread`, `fwrite`, `remove`,
  `rename`, `unlink`, `unlinkat`, `mkdir`, `mkdirat`, `rmdir`,
  `truncate`, `ftruncate`, `mmap`, `shm_open`, `filesystem`
- network:
  `socket`, `socketpair`, `connect`, `bind`, `listen`, `accept`,
  `accept4`, `send`, `sendto`, `sendmsg`, `recv`, `recvfrom`, `recvmsg`,
  `shutdown`, `getaddrinfo`, `getnameinfo`, `curl_easy_init`,
  `curl_easy_perform`
- sleep/block/thread:
  `sleep`, `usleep`, `nanosleep`, `clock_nanosleep`, `sleep_for`,
  `sleep_until`, `pause`, `sigsuspend`, `select`, `pselect`, `poll`,
  `ppoll`, `epoll_wait`, `pthread_create`, `thrd_create`, `async`,
  `thread`, `jthread`
- escape hatches:
  `syscall`, `dlopen`, `dlsym`, `dlvsym`, `asm`, `__asm`, `__asm__`

回避への扱い:

- `std :: system`: token 列が `std`, `::`, `system` になるため拒否。
- `#define RUN system`: candidate-local directive 自体を既存の `diff_quarantine.py:48-57,463-468` が拒否し、さらに `system` token も拒否。
- `auto run = std::system; run(...)`: alias 定義時の `system` token で拒否。
- `"sys" "tem"`: string contents は opaque。単独では効果でないため拒否しない。`dlsym` 等で名前解決する経路は resolver token 側で拒否。
- macro token-pasting、trusted header 内の既存 alias、既存 wrapper、事前取得済み function pointer、operator/constructor の副作用、deny table 外の compiler extension は残余となる。

### 1.3 無限ループ判定

- 編集ファイル: `orchestrator/campaign/coder_effect_gate.py`
- file:line: `new:207-275`
- 変更内容:
  - 次の明示的に無条件な header だけを拒否する。
    - `while (true)` と `while (1)` 相当の単一非ゼロ整数 literal
    - `for (;;)`, `for (; true ;)`, `for (; 1 ;)`
    - `do { ... } while (true)` は末尾の同じ `while` 判定で拒否
  - 任意式の constant-fold、到達可能な `break` の解析、再帰停止性の判定は行わない。
  - 初期化・条件・更新を持つ通常の `for`、range-for、データ依存 `while` は拒否しない。
- 理由:
  - 実測された `while(true){}` を確実に拒否しつつ、通常の comparator/backoff 内の有限 loop を一般論で拒否しない。
- リスク:
  - `while(true) { break; }` も保守的に拒否する。
  - `while(flag)`、相互再帰、整数 overflow 由来の非停止は検出しない。したがって「無限ループを閉じて検出する」とは記述しない。

### 1.4 seam への統合と bytes 非反射

- 編集ファイル: `orchestrator/campaign/p3_s4_loop.py`
- file:line: `192-243`, `779-803`
- 変更内容:
  - trigger の canonical membership 検査、render、既存 structural validation の順は維持する。
  - structural pass の場合だけ `scan_host_effects(coder.implementation)` を必ず実行する。
  - finding があれば `DiffRejectSubtype.HOST_EFFECT` の失敗結果へ変換し、`239-242` の書き込みへ到達させない。
  - `assert_value_literal_consistent()` の `793-803` にある候補値・`coder.implementation!r` を含む例外を固定文言へ変更する。
- 理由:
  - structural reject の優先順位と既存期待値を維持しながら、全軸の単一 seam で効果 gate を強制できる。
  - auditor verdict に依存せず、source 書き込み前に拒否できる。
- リスク:
  - reject evidence に token text を入れると攻撃文字列や path が WAL/critic に漏れるため、固定 category/rule ID と位置情報だけに限定する。

出力してよいもの:

- 固定 subtype `host-effect`
- 固定 rule ID/category
- token ordinal、行番号、byte length
- SHA-256 の短縮値
- finding 件数

出力しないもの:

- 元 identifier、string/char literal、statement
- command、path、hostname、URL
- `implementation` 全体
- diff hunk の候補由来行

これは `auditor_gate._reject_schema:43-49` と同じ非反射規律にする。

## 2. reject/WAL/critic への相乗り

### 2.1 subtype の追加

- 編集ファイル: `orchestrator/campaign/diff_quarantine.py`
- file:line: `40-51`
- 変更内容:
  - `DiffRejectSubtype.HOST_EFFECT = "host-effect"` を加える。
  - structural validator 自体の既存判定順は変更しない。
- 理由:
  - `record_diff_reject()`、既存 WAL schema、loader、renderer をそのまま利用できる。
- リスク:
  - subtype の追加を structural validator の新条件として混在させると既存 priority が変わる。効果判定は `p3_s4_loop.quarantine()` の後段 adapter に限定する。

### 2.2 WAL と critic digest

- 編集ファイル: `orchestrator/critic/digest.py`
- file:line: `163-190`, `341-375`, `678-709`
- 変更内容:
  - `load_diff_rejections()` は subtype を文字列として透過するため変更しない。
  - `render_rejections()` の `691-708` に `host-effect` 用の固定 remediation 文を一枝追加する。
  - evidence や implementation を展開しない。
- 理由:
  - `DiffQuarantineRejection.subtype` は enum exhaustive ではなく `str` なので loader/schema の追加は不要。
  - `record_diff_reject()` の WAL reason は既存の `diff-quarantine` のままでよい。
- リスク:
  - generic frame/hole 文言へ落とすと remediation が誤るため、renderer のみ明示分岐が必要。

WAL golden への影響はない。`p3_s4_loop.py:256-278` の payload key、BUILD_START/ABORT 構造、reason は変更せず、新 subtype は新たに拒否されたケースでのみ出現する。したがって `test_p3_s4_loop.py:372-435` の既存 exact-byte golden は変更しない。

## 3. W-2: auditor を mandatory deny-only veto に固定

### 3.1 合成関数による非拡大保証

- 編集ファイル: `orchestrator/campaign/auditor_gate.py`
- file:line: `148-200` の後
- 変更内容:
  - 次の責務を持つ `apply_mandatory_deny_only_veto(...) -> DiffQuarantineResult` を追加する。
    1. machine/coder gate が失敗なら、その同じ失敗結果を返す。
    2. machine gate が成功した場合は auditor の `diff_digest` を必ず照合する。
    3. auditor が `reject` / `uncertain` なら既存 `auditor_reject_result()` を返す。
    4. auditor が `pass` なら新しい capability/receipt を作らず、元の machine-pass 結果そのものを返す。
- 理由:
  - 合成結果を `machine_accept ∩ auditor_not_veto` として型・返却形で固定できる。
  - `pass` branch が受理結果を新規生成しないため、auditor が coder gate の reject を pass に反転できない。
- リスク:
  - 完全な実行順序の可換性は目標にしない。既存どおり machine reject では auditor digest を評価しないため、診断順序は非可換である。一方、受理集合は順序にかかわらず非拡大という不変条件で固定する。

### 3.2 sort driver

- 編集ファイル: `orchestrator/campaign/p3_s4_loop_sort.py`
- file:line: `141-168`, `216-271`
- 変更内容:
  - `_quarantine_and_audit()` の直接的な `verdict == "pass"` admission branch を削除する。
  - `L.quarantine()` の結果と auditor verdict を上記合成関数へ渡す。
  - 合成結果が false の場合だけ既存 `L.record_diff_reject()`、true の場合だけ後続 dry/build へ進む。
- 理由:
  - W-1 gate は auditor の前後関係ではなく、合成入力として必須になる。
  - auditor pass は machine pass を再利用するだけで、build capability を発行しない。
- リスク:
  - `default_cfg.spec_content` は campaign identity に影響するため変更せず、コード docstring/comment だけを更新する。

### 3.3 trigger driver

- 編集ファイル: `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- file:line: `395-445`
- 変更内容:
  - wire parse、trusted emitter、syntax/binding validation、`L.quarantine()` は維持する。
  - `428-445` の digest/verdict 分岐を同じ deny-only 合成関数へ置き換える。
- 理由:
  - sort と trigger で admission semantics を一つにできる。
  - trigger の閉じた wire schemaを緩めない。
- リスク:
  - raw-code injection test を trigger へ無理に追加すると現行 schema の責任境界を壊す。trigger は全 canonical wire の正例と raw-key schema reject を回帰させる。

## 4. docstring の是正

- 編集ファイル: `orchestrator/campaign/auditor_gate.py`
- file:line: `1-16`, `110-124`, `135-146`, `153-164`, `203-211`
- 変更内容:
  - schema validity・digest attribution と semantic admission を明確に分離する。
  - 文言を必ず「mandatory deny-only veto; affirmative security credit なし」とする。
  - `verdict="pass"` は machine/coder gate の結果を拡張しない、と明記する。
- 理由:
  - R1 の指定と現行実装契約を一致させる。
- リスク:
  - 「advisory」は使用しない。

- 編集ファイル: `orchestrator/campaign/diff_quarantine.py`
- file:line: `3-29`
- 変更内容:
  - `20-22` の auditor を advisory とする記述を削除する。
  - structural quarantine、coder effect gate、mandatory deny-only auditor veto の責任分界を書く。
- 理由:
  - D127 (6) の historical wording は R1 の新契約と衝突する。
- リスク:
  - structural quarantine 単体が semantic security を提供するようには書かない。

- 編集ファイル: `orchestrator/campaign/p3_s4_loop_sort.py`, `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- file:line: `p3_s4_loop_sort.py:18-26,141-168`; `p3_s4_loop_trigger_gating.py:13-17,395-445`
- 変更内容:
  - driver docstring も同じ固定文言へ合わせる。
- 理由:
  - 呼び出し側だけ旧 admission model が残るのを防ぐ。
- リスク:
  - campaign spec/prompt の永続文字列は変更しない。

## 5. テスト計画

### 5.1 deny policy の単体テスト

- 編集ファイル: `orchestrator/tests/test_coder_effect_gate.py`（新規）
- file:line: `new:1-220`
- 変更内容:
  - 4 種の攻撃を scanner が拒否する:
    - `std::system`
    - `execl`
    - `std::ofstream`
    - `while(true){}`
  - `std :: system`、関数 pointer alias、文字列連結を含む呼び出しを拒否する。
  - `ecosystem`、`"system"`、comment 中の識別子は拒否しない。
  - candidate-local directive は structural gate の責任であることを分離して固定する。
  - `for (int i = 0; i < n; ++i)`、range-for、通常の comparator/backoff 式を通す。
  - malformed token/string は fail-closed になり、reject object に元 bytes が含まれないことを確認する。
- 理由:
  - lexical policy の境界と残余を実行可能な仕様にする。
- リスク:
  - table 全件の安定した rule ID と重複なしも meta-test で固定する。

### 5.2 2 raw-code 軸 × 4 注入

- 編集ファイル: `orchestrator/tests/test_p3_s4_loop.py`
- file:line: `146-180` の後、`326-435`, `495-531`, `684-705`
- 変更内容:
  - backoff と sort の各軸について、親 probe と同じ valid wrapper に4種を挿入し、計8ケースを `L.quarantine(write=False)` で拒否する。
  - `write=True` でも source が変化しないことを確認する。
  - subtype は `host-effect`、digest/evidence に command/path/implementation bytes がないことを確認する。
  - `record_diff_reject()` → `load_diff_rejections()` → `render_rejections()` の既存経路で往復させる。
  - `assert_value_literal_consistent()` の例外に implementation bytes が反射しないことを加える。
- 理由:
  - 4種注入を raw implementation を持つ各対象軸で固定する。
- リスク:
  - trigger は raw implementation 軸ではないため、この直積へ含めない。

### 5.3 auditor pass + 実 diff digest echo

- 編集ファイル: `orchestrator/tests/test_p3_s4_loop_sort.py`
- file:line: `116-204`
- 変更内容:
  - 各4注入について実際に生成した `working_diff` の digest を計算する。
  - その digest を echo した valid-schema `AuditorVerdict(verdict="pass")` を渡す。
  - `_quarantine_and_audit()` が `host-effect` reject を記録し、後続 build/dry-pass に進まないことを確認する。
  - 現行の正常 comparator `116-129` は引き続き通す。
- 理由:
  - 単なる schema 不正や digest mismatch ではなく、親実測と同じ valid pass injection を再現する。
- リスク:
  - digest mismatch テスト `149-161` や reject/uncertain テスト `164-204` の期待値は変更しない。

### 5.4 受理集合の非拡大 meta-test

- 編集ファイル: `orchestrator/tests/test_auditor_gate.py`
- file:line: `24-75` の後
- 変更内容:
  - machine result `{pass, reject}` × auditor verdict `{pass, reject, uncertain}` の組合せを列挙する。
  - 全組合せで `combined.passed => machine_result.passed` を検証する。
  - machine reject は auditor pass でも同じ reject object のまま。
  - machine pass + auditor pass は同じ machine result object のまま。
  - machine pass + reject/uncertain のみ false へ狭まる。
- 理由:
  - branch 順序への依存ではなく、受理集合の部分集合関係を直接固定する。
- リスク:
  - `parse_auditor_dict()` が valid `pass` schema を受け付ける既存テスト `70-75` は維持する。schema 受理と build admission は別責任である。

### 5.5 正常実装の正例

既存期待値を変更せず、次を gate の正例として利用する。

- `test_p3_s4_loop.py:146-152`: 正常 backoff 実装
- `test_p3_s4_loop_sort.py:116-129`: 正常 sort comparator
- `test_s6_sort_sweep.py:211-216`: 現行 deterministic sort candidate 全件
- `test_s8a_trigger_sweep.py:196-201`: canonical trigger candidate 全件
- `test_p3_s4_loop.py:206-313`: canonical trigger membership

特に `test_s6_sort_sweep.py:211-216` を全 candidate の受理集合回帰として残し、単一 fixture だけに依存しない。

## 6. 指定された既存テストへの影響

| テスト | 現行 file:line | 計画 |
|---|---:|---|
| `test_diff_quarantine.py` | `183-202`, `263-370`, `555-577` | 既存期待値変更なし。正常 pass、directive reject、payload 非反射、substring/raw-string 境界を回帰 |
| `test_auditor_gate.py` | `24-75` | deny-only 合成と非拡大 meta-test を追加。既存 schema/digest テストは維持 |
| `test_p3_s4_loop_sort.py` | `116-224` | 4注入 + pass/digest echo を追加。既存正常、machine-first reject、mismatch、reject/uncertain、critic hint は維持 |
| `test_p3_s4_loop.py` | `146-180`, `206-435`, `495-531`, `684-705` | 2軸×4注入、write 防止、WAL/render、bytes 非反射を追加。既存 WAL golden は変更しない |
| `test_p3_s4_loop_trigger_gating.py` | `1326-1352`, `1567-1615`, `1671-1687` | 期待値変更なし。全32 wire、正常 pass、digest mismatch/auditor reject、raw implementation schema reject を回帰 |
| `test_autonomous_trial_completeness.py` | `992-1032`, `1206-1221` | 編集なし。preview `passed=False` が pre-audit reject になる既存契約を回帰 |
| `test_p3_autonomous_workload_trial.py` | `236-244`, `530-556`, `615-644` | 編集なし。raw implementation key の拒否、canonical emitter、preview schema を回帰 |

本 worker は read-only であり、pytest の実測や緑を主張しない。親が実装後に repository wrapper 経由で対象テストを実測する。

## 総括

### (a) プランの要点

- coder hole の単一 seam は `p3_s4_loop.quarantine():192-243` であり、source 書き込み前に有限 lexical effect gate を置く。
- 4種注入を backoff/sort の両 raw-code 軸で拒否し、正常 comparator/backoff と既存 sweep 全件を正例として維持する。
- auditor は合成関数で mandatory deny-only veto にし、`pass` が machine result や build capability を生成しない形にする。
- reject は既存 `record_diff_reject` / `load_diff_rejections` / `render_rejections` を使い、候補 bytes を一切反射しない。
- 既存テストの期待値と WAL golden は変更せず、追加テストだけで非拡大を固定する。

### (b) 親 brief への疑義・反論

P1 の「閉じた効果 denylist」は表現を狭める必要がある。提案できるのは閉じた有限 rule vocabulary であり、任意の C++ の host 効果に対する閉じた意味論的境界ではない。trusted header の既存 macro/wrapper、間接呼び出し、deny table 外の extension などが残るためである。

N1 は限定的には正しい。sort に denylist を追加すること自体は R1 が退けた「値 IR を sort に一般化する」案ではない。一方、これを build host-security boundary の代替または完全な第三案として扱うなら R1 の境界認識と衝突する。今回の実装は measured attack を塞ぐ defense-in-depth と acceptance narrowing であり、完全な containment とは主張しない。

また、実行順序そのものを完全に可換にするのは現実的でない。machine reject 時に auditor digest を評価しない既存挙動を保つため診断順序は変わり得る。保証対象は `effective_accept ⊆ machine_accept` という受理集合の不変条件にする。

### (c) 本 wave の scope 外

- bwrap/unshare 等の sandbox と完全な build host containment
- `[T-184]` stage matrix
- 独立 oracle（R2-b）
- field mapping（R3-3）
- build 出力 copy-out 厳格化（R3-6）
- backoff の value IR producer/consumer 移行
- autonomous preview の `forbidden_identifiers` hardcode（N4）
- `s5_permutation_coverage.py` の non-admissible materializer 再設計
- docs/decisions・phase docs の編集、commit、テスト実測