実装は行わず、射影された 4 ファイルの静的確認と bytes 分割の短い実測だけを行った。pytest は未実走。

## 1. 6 箇所の変更

| # | file:line | 変更前 | 変更後 | 型 | 受理集合への差 |
|---|---|---|---|---|---|
| 1 | `orchestrator/codex_roles/events.py:316` | `text.splitlines()` | `text.split("\n")` | `str` | 正常な LF JSONL は差なし。JSON string 内の未 escape `U+2028` / `U+2029`、および `U+0085` を行境界と誤認しなくなり、正当な object を受理する。一方、VT、FF、FS、GS、RS、NEL を JSONL 区切りに使う不正入力は行分割されなくなる。 |
| 2 | `tools/codex_worker_launch.py:1273` | `complete.splitlines()` | `complete.split(b"\n")` | `bytes` | 正常な LF JSONL と UTF-8 の `U+2028` / `U+2029` は差なし。CR / CRLF で CR を消さなくなるため、非空 event 行は `parse_jsonl` により invalid になる。 |
| 3 | `tools/codex_worker_launch.py:1406` | `complete.splitlines()` | `complete.split(b"\n")` | `bytes` | 正常な LF JSONL と対象 2 文字は差なし。CR / CRLF rollout 行は CR を保持し、`strict_json_loads` が拒否して `rollout.invalid` になる。 |
| 4 | `tools/codex_worker_launch.py:2335` | `raw.splitlines()` | `raw.split(b"\n")` | `bytes` | 正常な LF JSONL と対象 2 文字は差なし。CR / CRLF の記録済み rollout 行は parse 失敗として summary から除外される。 |
| 5 | `tools/codex_worker_launch.py:4097` | `closed.splitlines()` | `closed.split(b"\n")` | `bytes` | 正常な LF JSONL と対象 2 文字は差なし。CR / CRLF stdout 行は CR を保持し、再計算時の `stdout_invalid` を立てる。 |
| 6 | `tools/codex_worker_launch.py:4119` | `raw.splitlines()` | `raw.split(b"\n")` | `bytes` | 正常な LF JSONL と対象 2 文字は差なし。CR / CRLF rollout 行は CR を保持し、再計算時の `rollout.invalid` を立てる。 |

`tools/codex_worker_launch.py:327` の `completed.stdout.splitlines()` は変更しない。これは `str` の git 出力で、`split("\n")` にすると通常の末尾 LF が余分な空要素を作り、行数検査を壊す。

変更は上記 6 式だけとする。以下はそのまま維持する。

- 全体 byte 上限: `events.py:314,170-197`
- 1 行 byte 上限: `events.py:319-324`
- `strict_json_loads`: `events.py:273-307`
- 空行 skip: `events.py:317-318`、worker 側 `1274-1275,1407-1408,2336-2337,4098-4099,4120-4121`
- worker 側の行上限: `1277-1280,1410-1414,2339-2342,4101-4105,4123-4127`

## 2. 各箇所の負例テスト設計

新規 `orchestrator/tests/test_codex_jsonl_line_split.py` に、次の予定行帯で 6 関数を置く。各 bytes テストは、対象文字の受理確認と CRLF 拒否確認を同じ関数内に持たせる。

| 予定位置 | test 関数 | 入力と期待結果 | KILL 点検 |
|---|---|---|---|
| `:65-82` | `test_parse_jsonl_accepts_unicode_line_separators` | `separator` を `"\u2028"` / `"\u2029"` で parameterize。`json.dumps(..., ensure_ascii=False)` で separator を JSON string 値に含む 1 event を作り、前後に空 LF 行を加えて `parse_jsonl` へ `str` で渡す。object が 1 件返り、値が完全一致することを確認する。`max_bytes` と `max_line_bytes` は実 byte 数ちょうどでも通し、1 byte 小さい上限では失敗させる。 | `events.py:316` だけを `splitlines()` に戻すと JSON string の途中で 2 行に割れ、両 parameter が parse error になる。KILL 可能。 |
| `:85-112` | `test_drain_stdout_keeps_unicode_separators_and_rejects_crlf` | 対象文字を extra field に含む `thread.started` の LF 行を `AttemptState.stdout_path` に置き、`_drain_stdout` 後に `stdout_invalid is False`、session ID 取得、pending 空を確認する。別 state には対象文字を含まない ASCII JSON の CRLF 行を置き、invalid かつ session 未取得を確認する。 | `:1273` だけを戻すと CR が消されて ASCII event が受理されるため失敗する。対象文字だけの確認では KILL 不能だが、CRLF 観測との組み合わせなら KILL 可能。 |
| `:115-140` | `test_tail_rollout_keeps_unicode_separators_and_rejects_crlf` | extra field に対象文字を含む LF `turn_context` を `_tail_rollout` に読ませ、`invalid is False`、`context_count == 1`、model / effort 一致を確認する。別 rollout の ASCII CRLF 行は `invalid is True`、count 0 とする。 | `:1406` を戻すと CRLF 行から CR が消え、context が受理されるため失敗する。KILL 可能。 |
| `:143-170` | `test_recorded_summary_keeps_unicode_separators_and_rejects_crlf` | 対象文字を extra field に含む LF の `session_meta` と `turn_context` を記録済み rollout として渡し、`_recorded_summary` が model、effort、count 1、cwd を返すことを確認する。ASCII CRLF 版は `(None, None, 0, None)` を期待する。 | `:2335` を戻すと CRLF 版も集計され、期待 tuple と異なる。KILL 可能。 |
| `:173-207` | `test_recompute_metering_stdout_keeps_unicode_separators_and_rejects_crlf` | stdout は対象文字を extra field に含む LF `thread.started`、rollout は LF の正常な `session_meta` と `turn_context` とし、`_recompute_attempt_metering` の evidence が `complete` になることを確認する。次に stdout だけを対象文字なしの ASCII CRLF に替え、evidence `invalid` を期待する。 | `:4097` を戻すと stdout の CR が除去され、正常 rollout と合わせて evidence が `complete` になるため失敗する。`4119` は LF fixture なので変異が独立している。 |
| `:210-244` | `test_recompute_metering_rollout_keeps_unicode_separators_and_rejects_crlf` | stdout は LF の正常な `thread.started`。rollout に対象文字を含む LF の `session_meta` と `turn_context` を置き evidence `complete` と recorded cwd を確認する。次に rollout だけを対象文字なしの ASCII CRLF に替え、evidence `invalid` を期待する。 | `:4119` を戻すと CRLF rollout が正常に読まれ、evidence が `complete` になるため失敗する。`4097` は LF fixture なので変異が独立している。 |

恒真性の点検結果:

- `str` テストは対象 2 文字そのものが変異を KILL する。
- bytes の `splitlines()` は対象 2 文字で分割しない。その受理確認だけを 5 本置く P3 案は、5 変異すべてに対して恒真となる。
- bytes テストの CRLF branch は各変更箇所を直接通り、旧式だけが CR を消して event を受理するため KILL できる。
- CRLF branch を ASCII JSON にすることで、`events.py:316` の変異に依存せず、各 bytes 変異を単独でも全変異同時でも KILL できる。
- CRLF は正常な JSONL ではないため、この拒否強化は正常入力不変の条件に抵触しない。

## 3. bytes 分割の実際の差とテストへの導出

2026-08-26 の Python で、全 256 種の単一 byte と代表列を副作用なしで実測した。単一 byte で結果が異なった値は `10` (`LF`) と `13` (`CR`) だけだった。pytest は使っていない。

| 入力 | `bytes.splitlines()` | `bytes.split(b"\n")` | 実コードでの意味 |
|---|---|---|---|
| `b"x\n"` | `[b"x"]` | `[b"x", b""]` | 後者の末尾空要素は既存の `if not raw_line.strip(): continue` が捨てるため差なし。 |
| `b"x\r"` | `[b"x"]` | `[b"x\r"]` | CR が非空行に残り、既存 strict parser が拒否する。 |
| `b"x\r\n"` | `[b"x"]` | `[b"x\r", b""]` | CRLF を LF だけで切るため CR が残り、既存 strict parser が拒否する。 |
| `b"x\v"`、`b"x\f"`、`b"x\x1c"`、`b"x\x1d"`、`b"x\x1e"`、`b"x\x85"` | 分割なし | 分割なし | bytes 側では差なし。 |
| `b"x\xe2\x80\xa8"`、`b"x\xe2\x80\xa9"` | 分割なし | 分割なし | UTF-8 の `U+2028` / `U+2029` でも差なし。親 brief `:14-17` と一致。 |

従って bytes 5 箇所の有効な変異テスト入力は、非空 ASCII JSON event の CRLF 終端である。期待結果は呼び手ごとに次の通り。

- `:1273`: `stdout_invalid=True`
- `:1406`: `rollout.invalid=True`
- `:2335`: event が summary に入らない
- `:4097`: 再計算 evidence が `invalid`
- `:4119`: 再計算 evidence が `invalid`

LF 終端の正常入力と、対象 2 文字を含む LF event は従来どおり受理されることも同じ関数で確認する。

## 4. 新規 test file の自走 harness

射影された参照 `orchestrator/tests/test_codex_role_runtime.py:1-31` と同じ形にする。参照 file には `pytest.main` や `if __name__ == "__main__"` はなく、自走性は任意 cwd から repo module を import できる bootstrap で確保されている。

予定構成:

- `test_codex_jsonl_line_split.py:1-3`: UTF-8 coding cookie、docstring、`from __future__ import annotations`
- `:5-9`: `json`、`sys`、`Path`、`pytest`
- `:11-13`: `_REPO = Path(__file__).resolve().parents[2]` と `sys.path` 先頭への追加
- `:15-19`: `EventValidationError`、`parse_jsonl`、`from tools import codex_worker_launch as W`
- `:22-31`: session ID、model、effort、cwd の固定値と `separator` parameter
- `:34-62`: `json.dumps(ensure_ascii=False, separators=(",", ":"))` を使う JSON line encoder、rollout fixture、最小 attempt fixture
- `:65-244`: 上記 6 test 関数

対象文字の source 表記は Python escape の `"\u2028"` と `"\u2029"` のみとする。raw stringや二重 backslashにはせず、実行時には対象文字へ展開させる。生成 JSON は `ensure_ascii=False` とし、実際の UTF-8 byte 列を被験コードへ渡す。

実装後の静的検査として、新規 file に literal `U+2028` / `U+2029` と `U+0300` から `U+036F` が存在しないことを byte 対応の検索で確認する。文字を直接含む検索式や fixture は source に貼らない。

## 5. 落ちうる既存テスト

正しい変更なら、射影内の既存テストに意図的な failure はない。特に次は正常 LF JSONL または既存 strict 規律の回帰点なので確認対象とする。

- `orchestrator/tests/test_codex_role_runtime.py::test_event_stream_requires_real_thread_and_two_stage_json_schema` (`:73`)
- `orchestrator/tests/test_codex_role_runtime.py::test_jsonl_exposed_tool_or_unknown_item_is_rejected` (`:89`)
- `orchestrator/tests/test_codex_role_runtime.py::test_event_stream_never_accepts_success_text_or_malformed_evidence` (`:102`)
- `orchestrator/tests/test_codex_role_runtime.py::test_jsonl_duplicate_key_and_size_limits_are_fail_closed` (`:139`)
- `orchestrator/tests/test_codex_role_runtime.py::test_probe_thread_evidence_requires_canonical_uuid` (`:169`)

落ちうる条件は以下。

- `split("\n")` の末尾空要素を skip し忘れると、正常な末尾 LF fixture が落ちる。ただし今回 skip 分岐は変更しない。
- line length の算出対象や `raw_line + b"\n"` を変えると byte 上限テストが落ちうるため、それらは触らない。
- CRLF を正常入力として期待する worker launcher の既存テストがあれば、新仕様では落ちる。これは以前の CR 除去による過受理を固定していたテストであり、実装を戻す理由にはしない。
- `orchestrator/tests/test_codex_worker_launch.py` は射影外かつ別 wave の編集面なので、node id は確認していない。編集せず file 全体を回帰対象にする。

## 6. 焦点走の pytest 対象 file

親が repo 指定の test runner 経由で、次の順に実走する。

1. `orchestrator/tests/test_codex_jsonl_line_split.py`
2. `orchestrator/tests/test_codex_role_runtime.py`
3. `orchestrator/tests/test_codex_worker_launch.py`

加えて、6 箇所を 1 箇所ずつ `splitlines()` に戻す変異を適用し、新規 file の対応 test がそれぞれ赤になることを確認する。現段では pytest も変異走も実行していない。

## 総括

- 実装変更は `events.py:316` と worker launcher の `:1273,1406,2335,4097,4119` の 6 式だけ。
- 対象文字の実不具合を直すのは `str` の 1 箇所で、bytes 5 箇所では対象文字に対する挙動差はない。
- 最大のリスクは、bytes 側を対象文字の受理だけで検査して 5 本の変異を一切 KILL できないこと。
- 親の択一は「P3 の対象文字だけの 5 テスト」か「対象文字の受理と CRLF 拒否を組み合わせる 5 テスト」か。
- 後者を推奨する。正常 LF JSONLを変えず、各 site の変異を独立に KILL できる。