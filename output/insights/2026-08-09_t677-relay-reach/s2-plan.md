## 結論

(P1) は維持できる。dispatcher は変更せず、`orchestrator/tests/conftest.py` の controller 側 `pytest_unconfigure` を outer wrapper にし、pytest 自身の summary 出力がすべて終わった後に最大 48 KiB のダイジェストを stdout 最末尾へ置く。

ただし、`pytest_terminal_summary` 採用案は退ける。pytest 9.1.1 はその後に無上限の `short test summary info` と late warnings を出すため、到達保証にならない。

調査は current HEAD `bcda1c02` に対する静的確認のみで、ファイル変更・pytest 実走はしていない。

## 一次資料から確定した出力順

[pytest 9.1.1 terminal.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/terminal.py:957) では次の順序になる。

1. `pytest_sessionfinish` の TerminalReporter wrapper が通常の failures/errors/warnings を出す。
2. `pytest_terminal_summary` の他 plugin hook を呼ぶ (`:972-974`)。
3. wrapper の `finally` で `short_test_summary()` と late `summary_warnings()` を出す (`:996-1009`)。
4. `summary_stats()` を出す (`:993`)。
5. その後に `pytest_unconfigure` (`_pytest/main.py:359-373`)。

`short_test_summary()` は `stats["failed"]` / `stats["error"]` を全件ループする (`terminal.py:1289-1395`)。件数上限はなく、CI または高 verbosity では crash message も無切詰めになる (`:1542-1575`)。

実測済み 110 failures artifact では、relay 接頭辞を除いた byte 数は以下だった。

- failure 110 行: 11,501 bytes
- 見出し・最終 summary_stats を含む後続全体: 11,663 bytes
- summary_stats 単独: 81 bytes
- 1 failure 平均: 104.55 bytes
- 同じ平均で 7,505 failures なら約 784,682 bytes

48 KiB ダイジェストを `pytest_terminal_summary` で出すと残余は `65,536 - 49,152 = 16,384` bytes しかないため、平均 157 failures で開始マーカが押し出される。110 failures でも余裕は 4,721 bytesだけで、late warnings は [実装上無上限](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/terminal.py:1088) である。

したがって、次を採用する。

- hook: `pytest_unconfigure(config: pytest.Config) -> Generator[None, object, None]`
- decorator: `@pytest.hookimpl(wrapper=True, tryfirst=True)`
- `yield` 後の `finally` で出力する
- Pluggy 1.6.0 は tryfirst wrapper を外側に置き、その post-yield を最後に実行する (`pluggy/_hooks.py:402-408`, `_callers.py:90-135`)
- pytest の short summary、warnings、summary_stats はすべてこの hook より前なので、通常失敗経路でのそれらの後続 stdout は 0 bytes
- `tools/run_tests.py:1865-1868` は pytest subprocess 後に stdout を足さず、task-run 記録も「never emit output」契約 (`:814-842`)
- compute child も pytest 後は receipt をファイルへ書くだけ (`dispatch_compute.py:588-613`)

`Config._ensure_unconfigure()` 後には cleanup stack が残るため、任意の将来 plugin/atexit まで理論上 0 bytesとは断言しない。そのドリフトは後述 E2E の「END マーカが stdout 最終行」「開始以降 < 64 KiB」で赤にする。

## 変更ファイルと挿入位置

### 1. `orchestrator/tests/conftest.py`

[現行 imports](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:30) に `hashlib`、`json`、`dataclass`、必要な typing と次を追加する。

`from tools.pegasus.dispatch_compute import DEFAULT_FAILURE_RELAY_LIMIT_BYTES`

定数と内部型は現行 fixture 群の前、`conftest.py:37` 付近へ置く。

- `_FAILURE_DIGEST_START`
- `_FAILURE_DIGEST_END`
- `_FAILURE_DIGEST_MAX_BYTES = DEFAULT_FAILURE_RELAY_LIMIT_BYTES * 3 // 4`
- `_FAILURE_EXCERPT_MAX_BYTES = 4 * 1024`
- `_FAILURE_ENTRY_MAX_BYTES = 5 * 1024`
- `_FAILURE_NODEID_DISPLAY_MAX_BYTES = 256`
- `_FailureDigestItem` dataclass

[既存 `pytest_sessionfinish`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:274) の後、現行 EOF `:282` へ以下を追加する。

- `_collect_failure_digest_items(stats: Mapping[str, Sequence[object]]) -> list[_FailureDigestItem]`
- `_render_failure_excerpt(item: _FailureDigestItem, *, rank: int) -> str`
- `_build_failure_digest(stats: Mapping[str, Sequence[object]]) -> str | None`
- `_write_failure_digest(config: pytest.Config) -> None`
- `pytest_unconfigure(config: pytest.Config) -> Generator[None, object, None]`

収集対象は `terminalreporter.stats["error"]` と `["failed"]` だけとし、`report.nodeid`、`report.when`、`report.longreprtext` を使う。captured stdout/stderr の `report.sections` はダイジェストへ混ぜない。

### 2. 新規 `orchestrator/tests/test_pytest_failure_digest.py`

新規ファイル `:1` から、純関数テスト、fake reporter/config、xdist subprocess E2E を置く。既存の `test_real_repo_serialization.py:86-93` と同様に `conftest.py` を `importlib.util.spec_from_file_location` で隔離ロードする。

変更しないファイル:

- [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:741)
- [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pegasus_dispatch_compute.py:266)
- [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_codex_worker_launch.py:38)
- [run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/run_tests.py:367)
- [pytest.ini](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/pytest.ini:1)

## 出力書式

全出力は terminal encoding に左右されない ASCII とする。非 ASCII 診断は `\xNN` / `\uNNNN` へ escape し、各 excerpt 行を `| ` で始める。

開始・終了マーカ:

```text
=== IZANAGI FAILURE DIGEST v1 BEGIN ===
=== IZANAGI FAILURE DIGEST v1 END ===
```

各 failure:

```text
IZANAGI_FAILURE rank=1 category=failed when=call nodeid="..." nodeid_bytes=N nodeid_omitted_bytes=N nodeid_sha256=<64hex> source_bytes=N retained_bytes=N omitted_bytes=N rendered_excerpt_bytes=N sha256=<64hex>
--- IZANAGI FAILURE EXCERPT rank=1 BEGIN ---
| <longreprtext の bounded tail>
--- IZANAGI FAILURE EXCERPT rank=1 END ---
```

会計行:

```text
IZANAGI_FAILURE_DIGEST_ACCOUNT failures=N failed=N errors=N selected=N omitted_failures=N source_bytes=N retained_bytes=N omitted_bytes=N budget_bytes=49152 rendered_bytes=N omitted_manifest_sha256=<64hex-or-dash>
```

生成エラー時はダイジェストの代わりに一行だけ出す。例外 message 自体は出さない。

```text
=== IZANAGI FAILURE DIGEST v1 ERROR exception="RuntimeError" ===
```

`rendered_bytes` は開始マーカから終了マーカ後の改行までの実 ASCII bytes。会計行自身の桁数を含むよう、値が安定するまで再構成してから上限判定する。

## 予算設計

- failure relay: 65,536 bytes
- digest 総量上限: 49,152 bytes = relay の 75%
- 後続出力余白: 16,384 bytes = 25%
- failure excerpt: 最大 4,096 rendered bytes
- failure block 全体: 最大 5,120 bytes
- 固定 frame/account 予約: 1,024 bytes

`(49,152 - 1,024) // 5,120 = 9` なので、すべて最大長でも最低 9 failure を完全な構造ブロックとして残せる。短い failure は exact byte-fit でさらに入れる。

4 KiB は `test_codex_worker_launch.py:42` の `_TRUTH_SUMMARY_MAX_BYTES = 4096` に合わせる。node id は別 field なので、excerpt は `longreprtext` の UTF-8 tail を優先し、message 末尾へ再掲される `truth_summary` と pytest の crash location を残す。

選択順は xdist 到着順に依存させない。

1. `error` の各 source file から最大診断 1 件
2. 残る `error`
3. `failed` の各 source file から最大診断 1 件
4. 残る `failed`
5. 各 tier 内は `source_bytes` 降順、`nodeid`、`when`、sha256 で安定ソート

予算超過時はこの順序の末尾から落とす。これにより、同じ cascading file の failure だけで枠を使い切らず、setup/collection error と異なる failure file を先に残す。

会計方法:

- `source_bytes`: `longreprtext.encode("utf-8", errors="backslashreplace")` の全長
- `retained_bytes`: excerpt に採用した元 UTF-8 bytes
- `omitted_bytes = source_bytes - retained_bytes`
- 各選択 failure の `sha256`: 全 `source_bytes` に対する SHA-256
- 完全に落とした failure は、`nodeid/when/source_bytes/full-sha256` の sort済み canonical JSON Linesを再度 SHA-256 し、`omitted_manifest_sha256` とする
- 全 failure の global `omitted_bytes` は、選択 failure の中間省略と、非選択 failure の全 bytes の合計

## xdist 下の保証

conftest hook 自体は controller と worker の両方へロードされる。worker では xdist が `config.workerinput` を設定する (`xdist/remote.py:420-426`) ため、hook の post-yield 冒頭で `hasattr(config, "workerinput")` を判定し、worker は無出力にする。

controller 集約は一次資料上成立する。

- worker は全 `TestReport` を serialize して送る: `xdist/remote.py:280-289`
- controller は deserialize する: `xdist/workermanage.py:424-431`
- `DSession.worker_testreport` が controller の `pytest_runtest_logreport` を呼ぶ: `xdist/dsession.py:326-330`
- controller の TerminalReporter が category ごとに `stats` へ追加する: `_pytest/terminal.py:625-637`
- exception repr は serialize/deserialize される: `_pytest/reports.py:573-605,660-692`
- `longreprtext` は復元 report から全文を再描画できる: `_pytest/reports.py:103-115`

したがって controller の `terminalreporter.stats` には全 worker の failed/error report が集まり、controller 一回だけで全体ダイジェストを作れる。

## import と中継予算の結合

`tools/` と `tools/pegasus/` に `__init__.py` はないが、repo root から PEP 420 namespace package として import できる。既存テストも `test_pegasus_dispatch_compute.py:20-24` で repo root を `sys.path` へ入れ、`from tools.pegasus import dispatch_compute as DC` を使っている。実際の import も `tools.pegasus`、値 65,536 と確認済み。

producer に 65,536 のリテラルは複製しない。`DEFAULT_FAILURE_RELAY_LIMIT_BYTES` を直接 import する。

既存 `test_relay_limits_are_literal_four_and_sixty_four_kib` (`:357-359`) は削除・弱化せず、relay limit の 65,536 pin を担わせる。新規 (e) は以下を同時に pin する。

- imported relay limit との同値
- digest が relay の `3/4`
- digest の現行値が 49,152

したがって relay limit だけを縮めれば既存 literal test と新規 derived-value test が赤になる。意図的に両契約を更新した場合は E2E が新しい実予算で再検証する。

## 新規テスト一覧

| 対応 | nodeid 候補 | fixture | 赤にする欠陥 |
|---|---|---|---|
| (a) | `test_pytest_failure_digest.py::test_failure_digest_contains_nodeid_and_diagnostic_tail` | なし。`SimpleNamespace` report | node id/longrepr が無い、head-only 化で末尾 `truth_summary` が消える、開始/終了マーカ欠落 |
| (b) | `...::test_failure_digest_is_silent_for_green_and_worker` | `monkeypatch`、fake config/reporter | green でも marker を出して 4 KiB success relay を圧迫する、worker が重複出力する |
| (c) | `...::test_failure_digest_budget_and_omission_accounting_are_exact` | なし | 49,152 bytes 超過、1件 4,096 bytes 超過、単一 file 独占、omitted bytes/hash の誤会計 |
| (d) | `...::test_xdist_failure_digest_remains_in_dispatch_relay_tail` | `tmp_path` | 現状の本件そのもの。marker 不在、controller 未集約、pytest 後続出力による押出し |
| (e) | `...::test_failure_digest_budget_is_bound_to_dispatch_limit` | なし | local 64 KiB literal の二重化、3/4 関係の drift、dispatcher limit の無審査縮小 |
| (f) | `...::test_failure_digest_exception_is_fail_open` | `monkeypatch`、fake reporter/config | builder の `RuntimeError` が `pytest_unconfigure` から escape して pytest process の rc を上書きする |

(d) の subprocess E2E は `tmp_path/failure-digest-e2e/test_many_failures.py` を作り、96 parameter cases を置く。各 case は captured stdout 4,096 bytesと failure message 4,096 bytesを生成する。captured 部だけでも `96 × 4,096 = 393,216 bytes` で relay 枠の 6 倍になる。

inner command は repo root から次の形にする。

- `sys.executable -m pytest`
- `-q -n 2 --dist loadgroup`
- `-p orchestrator.tests.conftest`
- `-p no:cacheprovider`
- `--basetemp=<tmp_path 内>`
- 一時 test file の絶対パス

環境から `PYTEST_ADDOPTS` と外側の `PYTEST_XDIST_*` を除き、stdout/stderr は bytes で capture する。検査値は次のとおり。

- inner rc は 1
- digest開始前の stdout が 65,536 bytes超
-開始・終了マーカが各1個
- account の `failures=96`
- `short test summary info` と summary_stats が開始マーカより前
- stdout が終了マーカ＋改行で終わる
- 開始マーカから EOF まで `<=49,152` かつ `<65,536`
- `stdout[-DEFAULT_FAILURE_RELAY_LIMIT_BYTES:]` に完全な開始・終了マーカが残る

目標 wall は 5 秒以内、hard timeout は 15 秒。性能 gate にはせず、timeout のみ hang 防止に使う。失敗メッセージへ全 stdout を埋めず、総 bytes、sha256、末尾 2 KiB だけを出す。

## 不変条件の固定

- rc: `pytest_unconfigure` は session/exitstatus を受け取らず変更しない。builder/write の通常例外を内部で飲み、一行 fallback の write 失敗も再度飲む。(f) が catch 削除を検出する。
- green: `stats["failed"]` と `stats["error"]` がともに空なら、builder も writer も呼ばない。(b) が固定する。
- xdist: `config.workerinput` guard と (d) の marker 1個・failures 96件で controller-only 集約を固定する。
- relay: 既存 4/64 KiB tests は無編集。(d)+(e) を純増する。
- argv: `run_tests.py`、`pytest.ini`、環境注入は変更しない。conftest の既存自動 discovery だけを使う。
- launcher: 16 KiB message、4 KiB truth summary、production launcher は変更しない。
- transport: dispatcher の収集 2 MiB、末尾 64 KiB、中継 frame は変更しない。

## 変異事前登録

| 位置 | 1行変異 | 期待する新規赤 node |
|---|---|---|
| `conftest.py:新規 _FAILURE_DIGEST_MAX_BYTES` | `* 3 // 4` を relay 全量へ変更 | (c), (e) |
| `conftest.py:新規 tail 抜粋 helper` | tail slice を head slice へ変更 | (a) |
| `conftest.py:新規 source-file representative tier` | representative tier を空にする | (c) |
| `conftest.py:新規 account line` | `omitted_bytes` を常に `0` にする | (c) |
| `conftest.py:新規 pytest_unconfigure` | controller guard を反転して controller を return | (d) |
| `conftest.py:新規 _write_failure_digest` | `except Exception` を `except OSError` に狭める | (f) |

これらは受理集合を変える mutation kill ではなく、`DW-M08` の diagnostic sensitivity pin として記録する。変更前 HEAD の既存テストはこのダイジェスト名・marker・会計・hook 順を一件も検査しておらず、変異は green session の rc も変えないため、旧テスト集合では緑のままになる想定である。ただし未実走なので、段 6 で「新テストあり」と「変更前 HEAD 版テスト」の両方へ同一変異を適用し、`-rf` の実 node 記録で確定する。

## 親が行う実走

実装後は必ず `tools/run_tests.py` 経由で、新規 test file、既存 relay test file、受入全走の順に走らせる。併せて `tools/check_codex_agents.py`、`tools/check_docs.py`、commit 後 provenance 監査を行う。ここでは緑を主張しない。

## 総括

- dispatcher は無編集とし、controller の outer `pytest_unconfigure` post-yield で最末尾へ出す。
- ダイジェストは最大 49,152 bytes、1 failure 最大 4,096 bytes、16,384 bytesを後続余白に残す。
- xdist 全 worker の report は controller `terminalreporter.stats` から集約し、worker 出力は禁止する。
- 大量失敗 subprocess の実 stdout を測り、完全なダイジェストが末尾 64 KiB に残ることを固定する。