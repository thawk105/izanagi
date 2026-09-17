単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md`
  — 親の段 4 裁定 (plan v2 = 実装の正本、採否、scope、変異事前登録)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s2-plan-out.md`
  — 段 2 plan (擬似 diff と test A〜H の設計)。裁定と食い違う箇所は裁定が勝つ
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s1-brief.md`
  — 親 brief (不変条件・前提実測)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/verbatim-rulings.md`
  — 既裁定と親の前提実測の逐語
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py`
  — 編集対象 (`_cpp_normalize` :1646-1676、`_BUILTIN_MACRO_CACHE` :404)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py`
  — 編集対象 (新 test は :11832 付近、既存 builtin 回帰 `test_source_digest_builtin_ifdef_not_aliased_to_stock` の後。fixture `_FAKE_BACKOFF_HH` :11470、`_FAKE_OPTIONS_CMAKE` / `_FAKE_SILO_CMAKE` :11510 付近、`_fake_ccbench_repo` :11541、`_any_cxx` :11193)

上記以外に repo 内を読んでよい (`orchestrator/tests/test_ccbench_spawn_sites.py`、`orchestrator/tests/test_skip_classification.py`、
`tools/check_trace0_preprocess_identity.py`、`docs/decisions.md` の D34 は一次資料)。

## 所有と権限

- 編集してよい file は次の 2 つだけ: `orchestrator/campaign/source_digest.py`、`orchestrator/tests/test_campaign.py`。
- docs・登録簿 (`test_ccbench_spawn_sites.py`、`test_skip_classification.py`、`acceptance_duration_ledger.json`)・他の test file・
  `external/ccbench` (実共有 submodule) には書かない。commit・push・stash をしない。親が commit する。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。既存 test が赤なら実装側の誤りとして直す。
  期待値が誤りだと判断したら実装を変えず、報告して止める。
- 指示外の受理集合変更をしない。scope 前の現行挙動: `_cpp_normalize` は `-E -P` 出力をそのまま返し、`#define` / `#undef` は
  出力に現れない (F1016)。scope 後: 有効枝の source 指令が出力に残り、環境 prefix (predefined + command-line) は剥がされる。

## この段の仕事

裁定の plan v2 のとおり実装する。

1. **`source_digest.py`**: `_cpp_normalize` に `-dD` を足し、同じ argv の空入力出力 (環境 prefix) を per `(cxx, sorted defines)` の
   module cache (`_CPP_ENV_PREFIX_CACHE`、`_BUILTIN_MACRO_CACHE` :404 の隣) から取って `removeprefix` する。prefix は
   `_cpp_normalize("", defines, cxx, _environment_only=True)` の再帰呼出しで取り、`subprocess.run` の call site は関数内の
   **1 箇所のまま** (spawn site 登録簿 `_cpp_normalize: 1` を変えない)。`startswith(prefix)` 不成立は RuntimeError
   (fails-closed)。cache は key の存在で判定 (空文字も値)。失敗結果は cache に入れない。
   docstring を更新する: D34 案 A (builtin を定義済みのまま評価) は維持、`-dD` で有効枝の `#define` / `#undef` を pre-image に
   乗せる理由 (F1016: file 間へ漏れる指令が別プログラムを stock と同一視した)、実測で predefined と command-line 定義も
   出力されるため空入力 prefix を剥がすこと (剥がさないと template の追加供給 `BACKOFF_FIXED` / `BACKOFF_NOINLINE` だけで
   inert template が非 stock になる)、skipped 枝の指令は出ないこと、prefix 不一致は RuntimeError。残る限界を 1 行併記する:
   include 行を除去するため「指令と include の相対位置」は識別せず、`#pragma push_macro` / `pop_macro` の復元値も出力に
   現れない (裁定 D2104 項 2 の scope 外、段 3 レンズ A の A-1 / A-2)。
   `_trace_pair_diff` 側は変更しない (比較式は不変。`#if TRACE` 内の未使用指令が差分に出るようになる = 狭まる向き、A-3)。
2. **`test_campaign.py`**: plan の A〜H の 8 node を、plan の node 名・docstring・assert 文言で追加する。
   fixture は既存 `_fake_ccbench_repo` を使い、実 compiler は `_any_cxx()`。**G は monkeypatch を使わず、`_cpp_normalize` の
   正規注入 seam である `cxx` 引数に偽 compiler (tmp dir に置く実行可能な shell script。stdin が空なら `#define ENV 1` を、
   非空なら `#define DIFFERENT 1` と `int x;` を出力し rc=0) を渡して prefix 不一致を作る** (DW-O14: 検査対象機構の内側の
   呼出し `subprocess.run` を差し替えない)。偽 compiler の path は一意 (`t2731-fake-cxx-<pid>` 等) にして cache key の衝突を
   避け、tmp は必ず片付ける。D は working-tree の `cmake/Options.cmake` (allowlist 内) にだけ
   未参照の universal 供給を足して `resolve` が `STOCK` を返すことを主張する。E は protocol CMake (allowlist 外) を変えるので
   `compute` / `baseline` 直呼び。F は `BACK_OFF` 枝 (既存供給) を使い、未知条件マクロ拒否で別理由の赤を作らない。
   期待値へ揮発 payload (working tree hash 等) を焼き込まない。
3. 実走: `python3 -m pytest orchestrator/tests/test_campaign.py -k "source_digest or trace_diff" -q -rf -p no:cacheprovider`
   と、新 8 node を nodeid 指定で走らせ、緑には実走 nodeid・範囲を併記する。sandbox で走らせられない node (submodule の
   index lock 等、DW-O06) は「実装済み・未実走」と書き、`closed` と申告しない。実走の赤は内訳 (nodeid・理由) を報告する。
   `orchestrator/tests/test_ccbench_spawn_sites.py` と `orchestrator/tests/test_skip_classification.py` も走らせ、登録簿を
   触らずに緑であることを確認する (赤なら実装形を見直す。登録簿は編集しない)。
4. 完了報告に、所有外 caller (`tools/check_trace0_preprocess_identity.py`、`_trace_pair_diff`、`_normalize_contexts`)・
   共有 fixture・consumer test への波及可能性を静的に列挙する。テスト新設の制約 meta-test (test file の allowlist・
   行番号 pin・spawn site 登録簿) を自ら洗い出して走らせる。

## 禁止

- fixture へ現行 hash を差し込む等、テストを甘くして緑にしない。機構の正例・負例は実体 (`resolve` / `compute` / `baseline`)
  を名指しし、依存先を stub しない (G を除く)。
- `-dD` の代わりに別の方式 (`-P` 除去、環境マクロ名の行 filter、`-dM` 注入) にしない。gate・検査・台帳・helper の新設をしない
  (cache dict 1 つと keyword-only flag 1 つは裁定内)。
- 規律 2 を緩めない (RuntimeError を warning に格下げしない)。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。

## 変更した file と差分の要約
## 実走した nodeid と結果 (緑 / 赤 / 未実走)
## 所有外への波及 (静的列挙)
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
