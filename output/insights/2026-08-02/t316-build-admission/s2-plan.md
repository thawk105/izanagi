# T-316 設計プラン

結論は、最終形として **(c)「軸別の閉じた表現 + credentialless / network-less sandbox」**を推奨する。ただし親の (P2) とは荷重の置き方が異なる。(b) はホスト保護には load-bearing だが、「何を certified 候補として受理するか」の意味境界には (a) 側が load-bearing である。

本回答は全指定ファイルを読んだ静的検査結果である。書き込み、pytest、ビルド、実バイナリ実行は行っておらず、テストの緑は主張しない。

## 現行の受理境界

### DiffQuarantine が拒否するもの

`DiffQuarantine` 自身も「構造ゲート + byte 二次検査」であり、C++ 意味検査ではないと明記している（`orchestrator/campaign/diff_quarantine.py:9-20`）。

現在は次を拒否する。

| 条件 | 実装箇所 |
|---|---|
| unified diff の構文不正 | `orchestrator/campaign/diff_quarantine.py:176-253`, `:395-401` |
| 対象外ファイルの hunk | `orchestrator/campaign/diff_quarantine.py:416-424` |
| HEAD/base と一致しない context・削除 anchor。ただし `head_text` 未指定時は検査を省略 | `orchestrator/campaign/diff_quarantine.py:426-433` |
| hole 外の削除 | `orchestrator/campaign/diff_quarantine.py:435-446` |
| `if_line < anchor <= else_line` を外れる挿入 | `orchestrator/campaign/diff_quarantine.py:447-458` |
| hole 内の行頭 `#`、`%:`、`??=` による directive | `orchestrator/campaign/diff_quarantine.py:46-50`, `:461-467` |
| EVOLVE-BLOCK marker 文字列 | `orchestrator/campaign/diff_quarantine.py:51-55`, `:468-473` |
| `//`、`/*`、行末 `\` | `orchestrator/campaign/diff_quarantine.py:474-493` |
| template の marker 不成立、hole が既存 block comment/splice に埋まった状態 | `orchestrator/campaign/diff_quarantine.py:329-364`, `:537-630` |

`head_text` 省略時に anchor 確認が縮退する API は、現在の production `quarantine()` では `base_text` を渡しているため発火しない（`orchestrator/campaign/p3_s4_loop.py:207-213`）。ただし新しい呼び手が弱いモードを選べるため、将来は `head_text` を必須化すべきである。

### hole 内で現在書けるもの

上記 byte を含まず、構造上 hole 内なら、C++ の意味にかかわらず受理される。違反が一件もなければ無条件で `passed=True` になる（`orchestrator/campaign/diff_quarantine.py:495-496`）。

したがって次は、適正な hunk 内なら静的分岐上すべて通る。

- 関数呼び出し、代入、複数 statement
- `std::system(...)`、`execl(...)`、`std::getenv(...)`、ファイル I/O
- `while (true) {}`、`for`、`goto`、`throw`
- `asm`、新しい scope・lambda・ローカル型
- 複数行 implementation
- 任意に長い implementation
- `*/`。挿入行検査は `/*` だけを拒否しており、閉じ delimiter は検査していない

`render_hole()` は `implementation.split('\n')` の全行をそのままインデントして挿入し、行数・総 byte 数・AST 深さの上限を持たない（`orchestrator/campaign/p3_s4_loop.py:154-164`）。複数行を合法として固定する既存テストもある（`orchestrator/tests/test_diff_quarantine.py:190-196`）。

逆に `http://` を含む文字列は `//` の byte に偶然当たり拒否される。これは URL の意味を検査した結果ではない（`orchestrator/campaign/diff_quarantine.py:474-480`）。

### 親の実測 1〜3 の再検証

親が挙げた `std::system("id > /tmp/o")`、`execl(...)`、`std::ofstream(...)`、`while (true) {}`、`std::getenv(...)` は、いずれも上記五つの hole 内 byte 分岐には該当しない。このため、コンパイル成否とは独立に quarantine は通す。これは実行による再現ではなく、`validate()` 分岐の静的再追跡である。

追加 include を拒否しても十分ではない。backoff の対象ヘッダは `util.hh` を既に include し（`external/ccbench/include/backoff.hh:3-12`）、そこから `<stdio.h>`、`<stdlib.h>`、`<unistd.h>` が入る（`external/ccbench/include/util.hh:3-10`）。したがって POSIX 原始関数へ到達できないという防御根拠にはならない。ただし個々の payload が全軸・全 toolchain で必ずコンパイルできるとは、静的検査からは主張しない。

### 見落としやすい入力面

1. **production の coder transport は対象ファイル一個に限られる。**  
   `make_working_diff()` は post-template の `base_text` と hole 置換後の `edited_text` から対象ファイル一個の synthetic diff を作る（`orchestrator/campaign/p3_s4_loop.py:167-174`）。したがって coder JSON から任意の別ファイルを直接変更する経路は見つからない。対象外ファイル拒否は、raw diff API や将来の呼び手に対する防壁である。

2. **構造検疫前に一度ファイルへ書いている。**  
   現在は `write=True` のとき `edited_text` を書いた後で `validate()` を呼ぶ（`orchestrator/campaign/p3_s4_loop.py:207-213`）。通常の直列 caller は reject 後に build しないが、検疫前の bytes を shared-tree の別 reader が観測できる。検査後にだけ書く順へ反転すべきである。

3. **template patch は検疫の baseline に取り込まれている。**  
   patch を適用した後のファイルを `base_text` とするため、template patch 自体の変更は coder diff に現れない（`orchestrator/campaign/p3_s4_loop.py:177-213`）。実 patch は `cmake/Options.cmake` と実行対象ソースを変更する（`patches/silo-backoff-fixed.patch:1-74`、`patches/silo-sort-variant.patch:1-66`、`patches/silo-backoff-trigger-gating-variant.patch:1-196`）。

   `applied()` は HEAD と tracked-clean を確認するが、patch bytes の期待 digest は照合しない（`orchestrator/campaign/patchharness.py:234-251`）。これは現状 coder が直接変更する面ではないものの、build 入力として別個の trusted-input seam である。

4. **untracked 入力は clean/identity 判定から外れる。**  
   patch harness は untracked を無視する（`orchestrator/campaign/patchharness.py:125-140`）。source digest の worktree 検査も untracked を無視する（`orchestrator/campaign/source_digest.py:662-698`）。実際に CMake がどの untracked file を読むかは build graph 次第だが、コード上「読めない」とは保証されない。

5. **backoff の `value` も hole 外の coder-controlled 入力である。**  
   loader は `value` を `float` 化し（`orchestrator/campaign/p3_s4_loop.py:701-733`）、実 genome は `int(coder.value)` を使う（`orchestrator/campaign/p3_s4_loop.py:629-634`）。現行整合検査は正規表現で literal を探すだけである（`orchestrator/campaign/p3_s4_loop.py:542-570`）。manifest の integer 1〜1000 契約（`orchestrator/codex_roles/manifest.json:627-675`）をこの loader 自身は完全には執行していない。

6. **source digest は安全性でなく identity を束縛する。**  
   preprocess と digest の計算箇所は `orchestrator/campaign/source_digest.py:221-253`, `:541-574` である。任意 C++ を正確に別 source token として記録できても、その C++ を安全と判定したことにはならない。

## build/run 注入 seam

実在する経路は次の通りである。

```text
coder JSON
  → load_proposal_file
  → render_hole / synthetic diff
  → 対象ソースへ書き込み
  → DiffQuarantine
  → （sort/trigger は auditor gate）
  → run_campaign
  → pipeline.evaluate
  → source_digest の g++ preprocess
  → CMake configure / build
  → trace binary
  → perf 下の benchmark binary
```

各 driver の pre-build 境界は次にある。

- backoff: `orchestrator/campaign/p3_s4_loop.py:607-671`
- sort: `orchestrator/campaign/p3_s4_loop_sort.py:133-160`, `:205-249`
- trigger-gating: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:302-339`, `:385-420`

`pipeline.evaluate()` は identity 確定後に trace/perf の二つを build する（`orchestrator/campaign/pipeline.py:520-598`）。

| process | 現行の起動と権限 |
|---|---|
| `g++` preprocess | `subprocess.run`。環境分離なし（`orchestrator/campaign/source_digest.py:221-253`, `:287`） |
| CMake configure/build | legacy 経路は `cmake`、`gcc-13`、`g++-13` を名前で解決（`orchestrator/campaign/buildcache.py:594-649`）。共通 `_run()` は env/cwd を指定しないため親を継承（`:779-794`） |
| v2 CMake build | toolchain の realpath は固定できるが、namespace・credential 分離ではない（`orchestrator/campaign/buildcache.py:347-365`） |
| trace binary | `numactl` と binary を実行。親の全環境へ `IZANAGI_TRACE_DIR` を追加し、cwd は trace 一時ディレクトリ（`orchestrator/campaign/pipeline.py:204-224`） |
| perf binary | `perf stat -- <binary>`。`extra_env` があれば `dict(os.environ, ...)`、なければ暗黙継承。cwd は一時ディレクトリ（`orchestrator/calibrator/runner.py:325-373`） |
| `nm` | untrusted build artifact を sandbox なしで読む（`orchestrator/campaign/buildcache.py:753-776`） |

この経路には UID/GID、supplementary groups、capability、mount/network/PID namespace、seccomp の変更がない。したがって子 process は原則として orchestrator と同じ OS identity・filesystem 権限で動く。

ただし、次はコードからは決まらない（環境依存）ため推測しない。

- 実 UID/GID、capability、書き込み可能パス
- SSH・cloud・Git 等の credential が実際に存在するか
- `PATH` の具体値と解決先
- 外部 network や loopback への実到達性
- site 側 firewall、container、batch scheduler による追加隔離

コード自身は環境変数を scrub せず、home や credential path を mount から外さず、network を無効化していない。cwd を一時ディレクトリにすることは filesystem sandbox ではない。

trace/perf には 120 秒 timeout がある（`orchestrator/campaign/pipeline.py:187-224`、`orchestrator/calibrator/runner.py:346-373`）一方、legacy build は timeout を渡していない（`orchestrator/campaign/buildcache.py:643-649`）。また直接 child の timeout は process-group/cgroup 全体の確実な回収を意味しない。

## 親の前提実測 4〜7

- auditor gate は期待 digest と返却 digest の一致を確認するだけで、同じ digest と `verdict="pass"` を返せば通る（`orchestrator/campaign/auditor_gate.py:64-75`）。schema 整合も非信頼 verdict の真偽を独立に証明しない（`:105-157`）。P3 に同意し、auditor 強化を本件の security boundary には数えない。
- `test_diff_quarantine.py` の `test_` 定義は静的に 38 本で、意味注入 rejection はない。現行は構造・byte 防壁のテストである（`orchestrator/tests/test_diff_quarantine.py:1-603`）。
- `FROZEN_MANIFEST` は 23 件で、role source、diff quarantine、auditor gate を含まない（`orchestrator/tests/test_frozen_artifacts.py:38-85`, `:141-153`）。
- brief 記載の sort/backoff campaign ディレクトリは存在した。ただし内容の正当性や、現在提案する gate を満たすことは実走・再認証していない。

## 案 (a): 閉じた AST/DSL

親が示した「boolean-expression AST/DSL」を文字どおり全軸へ適用することはできない。trigger-gating には適合するが、backoff はスカラー、sort は comparator である。全軸を閉じるには、軸別 typed IR へ一般化した (a′) が必要である。

### 実装位置

新設する。

- `orchestrator/campaign/coder_semantic_gate.py`（新設、現行 line なし）
  - `BackoffSpec`
  - `SortComparatorSpec`
  - `TriggerPredicate`
  - size/token/depth 上限
  - parse、semantic validation、canonical renderer
  - untrusted 文字列と rendered C++ を別型にする

既存変更点は以下。

1. `orchestrator/campaign/projection_guard.py:26-35`, `:273-315`  
   キー集合だけでなく、軸・型・範囲・最大長を執行する。

2. `orchestrator/campaign/p3_s4_loop.py:607-671`  
   `applied()` より前に backoff spec を確定する。`implementation` を直接使わず、検証済み `value` から  
   `double now_backoff = static_cast<double>(BACKOFF_FIXED);`  
   を trusted renderer が生成する。

3. `orchestrator/campaign/p3_s4_loop_sort.py:205-249`  
   raw comparator を直接 `quarantine()` へ渡さない。typed comparator IR が無い compatibility 期間は fail-closed にする。

4. `orchestrator/campaign/p3_s4_loop_trigger_gating.py:104-131`, `:302-339`  
   現行 forbidden-identifier grep は二次防壁として残し、一次防壁を grammar parser に替える。

5. `orchestrator/campaign/p3_s4_loop.py:154-164`, `:207-213`  
   `render_hole()` は gate が発行した `RenderedHole` だけを受け取る。structural quarantine に通った後でのみ write する。

6. `orchestrator/campaign/p3_s4_loop.py:218-240`  
   semantic rejection を build/fitness なしの pre-build rejection として記録し、gate version、入力 digest、正規化 IR digest、renderer version を残す。

### 軸ごとの表現

| 軸 | 適合性と表現 |
|---|---|
| backoff | boolean DSL は不適合。JSON integer 1〜1000 のみを受け、`bool`、float、NaN/Infinity、指数表記、範囲外を拒否する。C++ は trusted renderer が固定生成する |
| sort | boolean DSL は不適合。最終形は `{keys:[{field:"storage"|"key", order:"asc"|"desc"}]}` のような重複なし・長さ上限付き comparator IR。未知 field、任意式、call は表現不能にする |
| trigger-gating | 最も適合。識別子は `izanagi_abort_reason_`、enum は patch の有限集合（`patches/silo-backoff-trigger-gating-variant.patch:56-67`）、演算子は `== != && || ! ()` と boolean literal のみ。全 enum 値を評価し、`kUnset => true` を強制する |

sort renderer は辞書式比較だけを生成する。これにより任意 statement は排除できるが、生成 C++ と既存 field 演算子の組み合わせまで text 検査で完全証明したとは主張しない。D41 の非 SWO/UB と fairness 死角（`docs/decisions.md:1256-1266`）は別途扱う。

### 閉じる vector

- `system`、`execl`、`getenv`、file I/O、network call
- loop、例外、inline asm、任意 lambda/body
- 複数 statement・複数行・無制限入力
- trigger の forbidden state 読み出しと `kUnset` fail-open
- sort の任意 comparator side effect
- backoff の `value` と実コード literal の帰属ずれ

### 残余 vector

- trusted parser/renderer の実装バグ
- template patch、CMake、toolchain、依存 source の改変
- compiler/kernel の脆弱性
- sort の合法 IR 内での fairness reward hack
- sandbox がなければ、trusted 入力面が破れた場合のホスト影響

### テストと positive control

新設 `orchestrator/tests/test_coder_semantic_gate.py` で以下を固定する。

- 危険 payload を各一件ずつ拒否し、build spy の呼び出しがゼロであること
- 同じ test case に安全な spec を置き、canonical renderer と build spy が一回呼ばれること。全拒否実装で緑になるのを防ぐ
- backoff の 1/1000 を受理し、0/1001/float/bool/NaN/Infinity を拒否
- trigger は全 enum 値の truth table を評価し、特に `kUnset` が true
- sort は duplicate/unknown key を拒否し、安全 IR から生成した比較器を C++ harness でも検査する
- D41 が要求する comparator mutant を ASan/UBSan で赤にする positive control（`docs/decisions.md:1268-1273`）
- gate を一箇所ずつ外した mutant で対応 test が赤になることを変異台帳へ残す

これらは計画であり、今回は実走していない。

## 案 (b): credentialless・network 無し sandbox

### 実装位置

新設する。

- `orchestrator/campaign/native_sandbox.py`（新設、現行 line なし）
  - `SandboxPolicy`
  - capability probe
  - `run_untrusted()`
  - policy/namespace/mount/toolchain receipt
  - cgroup/process-group 全体の停止処理

統合点は、上位一箇所だけでなく coder-derived source/binary を扱う全 subprocess である。

- preprocess: `orchestrator/campaign/source_digest.py:221-253`, `:287`
- configure/build: `orchestrator/campaign/buildcache.py:594-649`, `:779-794`
- `nm`: `orchestrator/campaign/buildcache.py:753-776`
- trace run: `orchestrator/campaign/pipeline.py:204-224`
- perf run: `orchestrator/calibrator/runner.py:325-373`
- `pipeline.evaluate()` の legacy/v2 分岐: `orchestrator/campaign/pipeline.py:557-598`

必要な policy は次である。

- network namespace を分離し外部・loopback network を到達不能にする
- user/PID/IPC/UTS namespace、`no_new_privs`、capability drop
- host home、repo、credential path を mount しない
- source/toolchain/system library は read-only
- candidate ごとの build/scratch/trace dir だけ writable
- env は clear し、固定 `PATH`、locale、必要最小限の変数だけ許可
- executable は絶対 path と digest で指定
- CPU、memory、PID、出力 byte、wall-time 上限
- timeout 時は namespace/cgroup 全体を kill
- backend unavailable 時は build を skip せず、campaign を fail-closed で停止
- cache hit binary も毎回 sandbox 内で実行する

`perf`、hardware counter、NUMA affinity を保ちながら上記 namespace を利用できるかはサイト能力に依存する。コードからは決まらないため、実装前の capability probe が必要である。

### 閉じる vector

- host credential/env/home の読み取り
- host filesystem への任意書き込み
- network exfiltration
- fork/子 process の sandbox 外残留
- CMake custom command を含む build-time の外部影響
- compiler・binary の無制限 resource 消費

### 閉じない残余 vector

- sandbox 内の任意計算
- stdout、trace、workload 経路を利用した measurement/reward hack
- 許可した writable mount の破壊
- kernel、sandbox backend、compiler の脆弱性
- `perf` や NUMA を許可するために広げた syscall/device 面
- arbitrary C++ を「正しい候補」として certified 集合へ入れる問題

最後の点が、(b) 単独を意味 gate と数えられない理由である。

### テストと positive control

新設 `orchestrator/tests/test_native_sandbox.py` で以下を行う。

- 外側では sentinel env/file が読めるが、同じ helper を sandbox 内で動かすと読めない
- 外側では local listener に接続できるが、sandbox 内では失敗する
- sandbox 内でも許可 scratch への marker 書き込みと正常終了は成功する
- host path 書き込み、fork 残留、無限 loop、過大出力を拒否・回収する
- malicious CMake configure/build も隔離される
- cache hit binary も隔離される
- backend 非対応環境では「安全テストを skip」せず、production build が fail-closed になる
- stock binary が trace/perf の必要出力を作れることを positive control にする

role schema は変わらないため role pin、`manifest.json`、adapter への波及はない。

## 案 (c): 両方

推奨する最終経路は次である。

```text
untrusted role JSON
  → 軸別 bounded parser
  → typed IR
  → trusted canonical renderer
  → structural DiffQuarantine
  → sandboxed preprocess/configure/build
  → sandboxed trace/perf execution
  → verifier / certification
```

(a′) が certified 候補の表現を狭め、(b) が parser/renderer・template・compiler の残余失敗をホスト境界内へ封じるため、二層の故障条件は概ね独立している。

加えて template patch の SHA-256 を `applied()` 前に照合する引数を `orchestrator/campaign/patchharness.py:234-251` へ追加し、各 driver の `TEMPLATE_PATCH` 定義（backoff は `orchestrator/campaign/p3_s4_loop.py:82`、sort は `orchestrator/campaign/p3_s4_loop_sort.py:94`）と束縛する。sandbox 用 source materialization には untracked file を含めない。

残る主なリスクは trusted renderer、toolchain、kernel、合法 IR 内の fairness/measurement hack である。

## role pin と生成物への波及

現在の三 coder manifest はいずれも `implementation: string` を持つ。

- backoff: `orchestrator/codex_roles/manifest.json:627-675`
- sort: `orchestrator/codex_roles/manifest.json:776-818`
- trigger-gating: `orchestrator/codex_roles/manifest.json:919-961`

四台帳は次である。

- source bytes: `orchestrator/codex_roles/review_ledger.py:15-29`
- role manifest entry: `orchestrator/codex_roles/review_ledger.py:31-48`
- description: `orchestrator/codex_roles/review_ledger.py:55-69`
- input/output schema: `orchestrator/codex_roles/review_ledger.py:71-102`

これらは `orchestrator/codex_roles/spec.py:499-593`, `:654-676` で照合され、adapter は `:802-872` から生成される。

| 変更 | pin 影響 |
|---|---|
| 現行 string を driver 内で閉じた grammar として解析する compatibility gate | role source、manifest、四台帳、adapter すべて変更不要 |
| 最終 typed IR schema へ移行 | 該当 role source、`ROLE_MANIFEST_SHA256`、output `SCHEMA_SHA256`、manifest、adapter を更新。description bytes を変えた場合だけ `DESCRIPTION_SHA256` も更新 |
| sandbox 単独 | role 関係は変更不要 |
| 案 (c) | typed IR 部分だけ (a) と同じ波及 |
| template patch digest pin | role 関係は変更不要 |

したがって親実測 6 は、「四台帳すべてが review closure に参加する」という意味では正しいが、schema 変更だけで四つの hash 値が必ず全部変わるわけではない。

`.codex/role-adapters/coder-v4-autonomous*.json` は現在 `implementation` schema と pin を埋め込んでいる（各 adapter の `:118-164` 前後）。現状 adapter は runtime blocked/dormant（`orchestrator/codex_roles/spec.py:94-99`）だが、将来契約のため生成物を同期する必要がある。

`FROZEN_MANIFEST` 23 件への直接波及はない。既存 frozen bytes を書き換える理由にもならない。

## 推奨裁定

親の provisional 裁定に対する結論は次の通り。

- **P1: 反対。** test-only では build/run 経路が一切狭まらない。この wave の実装最小集合には、少なくとも schema 互換の semantic admission と pre-build fail-close を含めるべきである。
- **P2: 「直交する二層」には同意、「(b) が load-bearing、(a) は defense-in-depth」には反対。** (b) はホスト containment には load-bearing だが、sandbox 内で arbitrary C++ が stdout・trace・workload を偽装する余地を残す。意味受理集合には (a′) が load-bearing であり、最終裁定は (c) とする。
- **P3: 同意。** auditor は digest と自己申告 verdict を返す非信頼出力であり、`orchestrator/campaign/auditor_gate.py:64-75` は意味の真偽を独立検証しない。deterministic gate 後の advisory review としては残せるが、解には数えない。
- **P4: 同意。** D33 は C++ 翻訳フェーズを text 検査で完全再現できないと確定している（`docs/decisions.md:754-763`）。本案は C++ text の意味を判定するのではなく、別の小さい言語を parse して trusted C++ を生成する。

sort については D43 自身が backoff のスカラー整合検査を転用できないと記録している（`docs/decisions.md:1402-1425`）。したがって「bool DSL が comparator にもそのまま適合する」という設計は採れない。

## この wave の最小実装集合

role hash を更新しないという brief の不変条件を守りつつ、次を最小集合として推す。

1. `orchestrator/campaign/coder_semantic_gate.py` を新設する。

2. backoff は既存 `value` と legacy `implementation` を小さい専用 grammar で読み、integer 1〜1000 と literal 一致を確認した後、実 C++ は `BACKOFF_FIXED` を用いる固定 renderer から生成する。

3. trigger-gating は既存一行 string の外枠 `izanagi_gate_pass = <expr>;` だけを受け、内部を有限 boolean grammar で parse・正規化する。

4. sort は typed schema を導入できる次 wave まで、trusted renderer が持つ有限個の exact canonical comparator だけを受理する。該当しない raw comparator は fail-closed。有限 allowlist も用意できないなら sort の `do_build=True` を停止する。

5. 各 driver の直接 `run_one_iteration()` 呼び出しでも bypass できないよう、`applied()` より前に gate を再実行する（backoff `orchestrator/campaign/p3_s4_loop.py:607-659`、sort `orchestrator/campaign/p3_s4_loop_sort.py:205-228`、trigger `orchestrator/campaign/p3_s4_loop_trigger_gating.py:385-420`）。

6. `quarantine()` は structural validation 後にのみ file write するよう `orchestrator/campaign/p3_s4_loop.py:207-213` の順序を反転する。

7. semantic reject を `orchestrator/campaign/p3_s4_loop.py:218-240` の pre-build WAL 経路へ統合し、fitness や verify payload を作らない。

8. 新規 gate test、三 driver の「reject 時 build 未到達 / safe control は到達」integration test、auditor が pass を返しても semantic reject を上書きできない test を追加する。

純粋な test-only P1 は採らない。危険 payload に対して通常テストで `assert quarantine.passed` だけを書くと、脆弱な層構成を期待値として固定する。DiffQuarantine が構造ゲートであることを示す必要がある場合も、同じ integration test 内で必ず「semantic gate は reject」「build call はゼロ」まで確認する。

もし gate 実装を一切入れられないなら、許容できる代替は test-only ではなく、coder-derived build を止める明示的 fail-closed switch と、未解決なら失敗する security test の組み合わせである。`xfail` や「現在は通ること」を正常系として緑にする案は採らない。

## 成果物影響（DW-G05）

| 提案項目 | 実装しない場合の影響 |
|---|---|
| schema 互換 semantic gate | certified 選択の受理集合が任意 C++ のまま残り、median_tps と変異台帳の数値を「意図した軸の結果」と帰属できず、材料レポートの candidate 参照も非信頼になる |
| typed IR への最終移行 | 数値そのものは compatibility gate と同じでも、role transport が raw string のまま残り、材料レポートは「AST を role が出した」とは記述できず、正規化 IR/renderer digest だけを参照する必要がある |
| sandbox | semantic 受理集合は変わらないが、certified run に host credential/network/filesystem 影響の不存在を主張できず、材料レポートと変異台帳へ `unsandboxed` の注記が必要になる |
| sandbox policy receipt の campaign/WAL 束縛 | sandboxed/unsandboxed run が同じ参照集合に混在し、どの containment 条件で得た median_tps か判別できなくなる |
| template patch digest pin | coder 受理集合は変わらないが、CMake・frame 由来の値を期待 template に帰属できず、選択・材料レポートの skeleton 参照が曖昧になる |
| positive control / mutation-red | 直近の数値は変わらないが、拒否集合の回帰検出力が 0 のままになり、変異台帳に T-316 防壁が実際に歯を持つ証拠を残せない |
| 既存 artifact の legacy 扱いと再実走 | 既存 bytes・数値は変えない一方、新 gate/sandbox 準拠として遡及認証できない。certified 選択から除外するか、legacy-unquarantined と明記して再実走する必要がある |

## 総括

推奨案は (c)。意味受理には軸別 typed IR、ホスト保護には credentialless・network-less sandbox を使い、どちらか一方を他方の代替とは数えない。

この wave の最小集合は、role schema を変えない compatibility semantic gate、全 driver の pre-build 配線、検査後 write、reject/positive-control test である。純粋な test-only P1 は採らない。

最大の未解決点は、Pegasus 上で `perf`・NUMA・hardware counter を維持しながら rootless network/filesystem sandbox を成立させられるかである。これはコードから決まらず、実装前の capability probe と計算ノード実測が必要になる。