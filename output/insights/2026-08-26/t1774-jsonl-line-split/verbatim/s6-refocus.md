| 所見 (出典と 1 行要約) | 親の裁定 | 現状 | 根拠 (file:line) |
|---|---|---|---|
| R1-1: U+0085 の新規受理、非 LF 区切りの新規拒否、行番号と上限の意味変化 | 事実は real。新規受理は 3 文字。scanner 案は却下し、テスト固定と段 7 台帳記録を採用 | partial | 3 文字は両経路で固定済み (`test_codex_jsonl_line_split.py:105-114,145-169`)。production は LF 専用のまま (`events.py:314-327`)。受理差表の台帳記録は段 7 の予定として残る (`ruling-s6.md:44-47`) |
| R1-2: CR だけの空行が byte 側 5 site で blank skip される | real だが変更前後で不変、scope 外 | not-applicable | blank skip は現在も分割直後に存在する (`codex_worker_launch.py:1273-1278,1406-1411,2335-2340,4097-4102,4119-4124`)。親の scope 外判断と一致する (`ruling-s6.md:49-72`) |
| R2-1: 直接実行時、repo import 前に停止する | real・must-fix・採用 | closed | `_ROOT` の挿入は repo import より前 (`test_codex_jsonl_line_split.py:12-20`)。親提示の直接実行結果は 12 passed |
| R2-2: collection・skip などの横断メタ契約監査が未閉 | real・採用、親が実施 | closed | 親指定の 2 meta-test を含む 8-file 焦点走は提示結果で rc=0。新規 file は skip を持たず、書込み先は `tmp_path` 派生だけ (`test_codex_jsonl_line_split.py:43-49,171-292`) |
| R2-3: 変異 #1 の `[u2028/u2029]` は実在 nodeid ではない | nit・採用。U+0085 追加後の 6 nodeid へ展開 | closed | 3 個の明示 id が 2 箇所に存在し、6 nodeid を構成する (`test_codex_jsonl_line_split.py:105-110,145-152`) |
| R2-4: recorded summary と rollout recompute の fixture が複数 event を同時に CRLF 化 | nit・採用。単一理由へ変更 | closed | 両 fixture とも `session_meta` は LF、`turn_context` だけ CRLF (`test_codex_jsonl_line_split.py:211-230,257-292`) |

### 追加検証

1. production の 6 式

現在の実物は次の 6 式で、R1/R2 が確認した fix 前の位置と一致する。

- `events.py:316` — `text.split("\n")`
- `codex_worker_launch.py:1273` — `complete.split(b"\n")`
- `codex_worker_launch.py:1406` — `complete.split(b"\n")`
- `codex_worker_launch.py:2335` — `raw.split(b"\n")`
- `codex_worker_launch.py:4097` — `closed.split(b"\n")`
- `codex_worker_launch.py:4119` — `raw.split(b"\n")`

`codex_worker_launch.py:327` は引き続き `completed.stdout.splitlines()` で無傷。fix による production 変更は認めない。

2. Unicode 表記と import 順

静的な codepoint 数は U+0085、U+2028、U+2029 ともリテラル 0 件。各 escape は 2 件で、該当箇所は `test_codex_jsonl_line_split.py:107,147`。

`sys.path` bootstrap は `test_codex_jsonl_line_split.py:12-14`、最初の repo import は `:16`。`pytest` は外部 package であり、repo 由来 import の先行はない。

3. 単一理由 fixture

- recorded summary は `session_meta` の LF 行だけが cwd を供給し、CRLF の `turn_context` だけが拒否される。production の期待値は `(None, None, 0, CWD)`、変異 #4 では turn context が復活して赤になる (`test_codex_jsonl_line_split.py:211-230`, `codex_worker_launch.py:2335-2367`)。
- rollout recompute も `session_meta` は LF、`turn_context` だけ CRLF。production では `rollout.invalid`、変異 #6 では両行が解析されて `complete` となるため赤になる (`test_codex_jsonl_line_split.py:257-292`, `codex_worker_launch.py:4119-4148`)。

従って失敗理由は各 1 event に限定され、killer は従来どおり #4 と #6。recorded summary の literal tuple は fixture の焦点化に合わせて cwd だけ保持する形へ狭められている。

4. U+0085 追加による既存期待値

既存の `u2028`、`u2029` id と assertion body は残っている。追加は各 parametrize の `u0085` 1 nodeだけで、旧 10 nodeから 2 node増えた 12 nodeとなる。反転、緩和、skip 化、既存 test function の削除は認めない (`test_codex_jsonl_line_split.py:105-169,171-292`)。

5. killer nodeid

実物上、fix 子の集合と一致する。実在しない nodeid、静的に確認できる抜けはない。

| 変異 | killer nodeid |
|---|---|
| #1 | `orchestrator/tests/test_codex_jsonl_line_split.py::test_parse_jsonl_accepts_unicode_line_separators[u0085]`<br>`orchestrator/tests/test_codex_jsonl_line_split.py::test_parse_jsonl_accepts_unicode_line_separators[u2028]`<br>`orchestrator/tests/test_codex_jsonl_line_split.py::test_parse_jsonl_accepts_unicode_line_separators[u2029]`<br>`orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_accepts_unicode_line_separators[u0085]`<br>`orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_accepts_unicode_line_separators[u2028]`<br>`orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_accepts_unicode_line_separators[u2029]` |
| #2 | `orchestrator/tests/test_codex_jsonl_line_split.py::test_drain_stdout_rejects_crlf_terminated_event` |
| #3 | `orchestrator/tests/test_codex_jsonl_line_split.py::test_tail_rollout_rejects_crlf_terminated_event` |
| #4 | `orchestrator/tests/test_codex_jsonl_line_split.py::test_recorded_summary_skips_crlf_terminated_event` |
| #5 | `orchestrator/tests/test_codex_jsonl_line_split.py::test_recompute_metering_stdout_rejects_crlf_terminated_event` |
| #6 | `orchestrator/tests/test_codex_jsonl_line_split.py::test_recompute_metering_rollout_rejects_crlf_terminated_event` |

新規所見ゼロ。

pytest と変異実走は再実行していない。実走結果は親から提示された結果として扱い、それ以外は静的に確認した。

## 総括

closed でない行は 2 件: `partial` 1 件、`not-applicable` 1 件。  
fix 対象の bootstrap、U+0085 pin、2 fixture の焦点化は閉じている。  
production 6 式と `:327` に回帰はない。  
親は上記 killer nodeid 集合をそのまま変異 spec へ登録してよい。  
次は段 7 で 3 文字の新規受理と 8 種の非 LF 区切り拒否を台帳へ記録する。  
scope 外の CR 空行 skip は、親裁定どおり failure 記録へ回す。