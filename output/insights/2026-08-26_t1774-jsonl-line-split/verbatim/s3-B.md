pytest と変異走は未実施。静的 AST 検査に加え、import と `git rev-parse` の読取 probe だけを行った。

## 受理集合の単調増加という brief の不変条件は成立しない

**区分**: 正しさ境界

**根拠**: `brief.md:30-33` は受理集合が壊れていた入力側へだけ広がるとしている。一方、`s2-plan.md:8-12,49-63` は bytes 5 箇所について、従来受理された非空 CR / CRLF event が変更後は拒否されると正しく記述している。`events.py:193-194` と `events.py:291-292` は CR を拒否するため、旧 `bytes.splitlines()` が消していた CR を `split(b"\n")` が残せば受理集合は縮む。

**これが real なら何が壊れるか**: 実装自体よりも brief の証明主張が壊れる。CRLF branch は単なる変異用入力ではなく、新しい拒否挙動を固定する仕様テストになる。

**提案**:

1. 六箇所変更を維持し、不変条件を「正常な LF JSONL は不変。正当な Unicode 入力は受理へ広がり、不正な CR / CRLF の過受理は縮む」と再裁定する。これを推す。裁定済み六箇所と既存の LF-only 規律を両立できる。
2. 単調増加を絶対条件として維持するなら、実修理の `events.py:316` だけに狭める。ただし確定済み六箇所裁定と衝突する。
3. CR を除去して互換維持する択は LF-only 規律を再び弱めるため推さない。

## 新規 test file は計画どおりだと F42 で必ず赤になる

**区分**: 整合・実効性

**根拠**: `s2-plan.md:67-79` は import bootstrap を自走性と誤認しており、予定構成に `_run()` も `__main__` もない。参照元 `test_codex_role_runtime.py:17-19` は import bootstrapしか持たず、実際には `orchestrator/tests/README.md:129-135` の allowlist に載ることで成立している。契約本体は `README.md:107-120`。機械検査は `test_plain_runner_coverage.py:35-41,60-74` である。

**これが real なら何が壊れるか**: 新規 file 単体と既存三 file の焦点走は緑になり得るが、受入全走は次で赤になる。

`orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`

**提案**:

1. `if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))` を新規 file に置く。parametrize をそのまま実行でき、README 編集も増やさないためこれを推す。
2. 真の `_run()` を実装する。ただし parametrize 展開まで自前で扱う必要があり重い。
3. README allowlist に追加する。成立はするが変更 file が一枚増える。
4. 焦点走へ上記メタ node を必ず追加する。allowlist 案なら `test_allowlist_has_no_stale_or_self_runnable_entries` も加える。

## 「JSONL の行分割は六箇所で閉じる」は repo-wide では偽

**区分**: 整合・実効性

**根拠**: grep の穴を次で補った。

- production Python 全体を AST で走査し、import alias を正規化した上で `splitlines`、LF `split`、`rpartition`、`readlines`、`iter_lines` と JSON parser が同一関数にある候補を列挙した。
- `getattr`、動的 import、対象名の文字列参照も別検索した。対象 parser / splitter の動的解決は見つからなかった。
- method-call 検査が落とす binary file iterator も手で追い、`codex_reasoning_ab.py:384-425` の二経路を確認した。
- 任意の実行時文字列合成一般までは静的完全証明できない。

同一関数候補だけで 33 関数あり、六箇所ではない。より直接には、`check_codex_hooks.py:420-431` が Codex JSON event の `str` stdout を `splitlines()` して `json.loads` へ渡す。`run_probe()` が `text=True` の stdout をそこへ渡す実経路も `check_codex_hooks.py:448-476` にある。JSON string 内の実 `\u2028` / `\u2029` で同型に割れる。

一方、対象二 file に狭めれば数は正確である。worker の JSONL `splitlines()` は `:1273,1406,2335,4097,4119` の五つで、`events.py:316` と合わせて六つ。ただし live reader の行フレーミングには既に `worker:1268,1401` の LF `rpartition` もあり、「全行分割箇所」ではなく「置換対象の `splitlines()` 六式」と呼ぶ必要がある。

`events.strict_json_loads` の production 呼出しは九つ。行を渡す四つは `events.py:322` と worker `:1410,2339,4123`、残る五つは `events.py:410,419`、`probe.py:589,722`、`run_codex_role.py:71` で、親の「その他は文書全体」という狭い主張自体は正しい。そこから repo-wide 閉包は導けない。

**これが real なら何が壊れるか**: brief の閉包証明が過大。今回の修理後も hook probe の Codex JSON event parserには同型不具合が残る。

**提案**:

1. 現 wave は「指定二 file の六つの `splitlines()` 置換」と明記して閉じ、`check_codex_hooks.py:423` を別裁定パッケージにする。確定 scope を乱さないためこれを推す。
2. repo-wide の Codex JSON event parser 修理を要求するなら、hook checker と対応テストを今回へ追加する。この場合は「それ以外は変えない」を再裁定する。

## 変異は全て KILL できるが、帰属は一意ではない

**区分**: 整合・実効性

**根拠**: `s2-plan.md:30-35,39-42` の CRLF branch を実装する限り、worker 五変異に SURVIVED はない。各 site は対応する CRLF test だけで KILL される。

ただし `events.py:316` を戻すと、次の三 test が同時に赤になる。

- `test_parse_jsonl_accepts_unicode_line_separators`
- `test_drain_stdout_keeps_unicode_separators_and_rejects_crlf`
- `test_recompute_metering_stdout_keeps_unicode_separators_and_rejects_crlf`

後二つも `worker:1277` と `worker:4101` から `parse_jsonl` を通り、stdout fixture に実 Unicode separator を含むためである。

逆に `brief.md:58-60` の「対象文字の受理だけ」を文字どおり実装すると、bytes の `:1273,1406,2335,4097,4119` を一つずつ戻す五変異は全て SURVIVED になる。`bytes.splitlines()` は対象 UTF-8 列を分割しない。

**これが real なら何が壊れるか**: 「一変異につき赤一件」という意味での一意帰属は成立しない。親 P3 の Unicode-only 解釈なら五変異の検出力が消滅する。

**提案**:

1. CRLF branch を維持し、各変異に「指定 killer node」を事前登録する。追加 fanout は許容すると明記する。これを推す。
2. 赤集合の一意性まで要求するなら、Unicode 受理 test と site 別 CRLF killer test を分離する。ただし `events.py:316` の stdout 経由 fanout自体は避けられない。
3. CRLF 拒否を段 4 で採らない場合、bytes 五変異の KILL 主張も撤回する。

## 直接呼出し設計は import 可能だが recompute fixture 契約が不足している

**区分**: 整合・実効性

**根拠**: `PYTHONDONTWRITEBYTECODE=1` の import probe は成功した。pytest は走らせていない。実シグネチャは次のとおり。

- `_drain_stdout(state)` は `worker:1260`。`AttemptState` は `:379-393` のうち `attempt_index`、`started_ns`、stdout / stderr / output の三 Path が必須。
- `_tail_rollout(rollout, *, model, reasoning, cwd)` は `:1390-1392`。`RolloutState` の必須値は `:358-360` の session ID と path。
- `_recorded_summary(attempts)` は `:2326-2367`。各 attempt に `rollouts`、各 rollout に `path` と `bytes` が必要。
- `_recompute_attempt_metering(attempt, *, model, reasoning, cwd)` は `:4076-4089` で attempt の index と三 path、`:4110-4117` で rollout の session ID / path / bytes、`:4140` で `session_ids` を要求する。返値は object ではなく四要素 tuple。
- evidence `complete` には `:1467-1484` により stdout session、対応 rollout、exact 一件の `session_meta`、一件以上の `turn_context` が必要。session ID / cwd / model / effort の一致条件は `:1321-1355`。

fixture 構築は小さく、subprocess や実 Codex は不要。ただし `s2-plan.md:78` の「最小 attempt fixture」だけでは上記相関契約が書かれていない。

**これが real なら何が壊れるか**: session ID、`bytes`、cwd のどれかを省くと KeyError または evidence `missing` / `invalid` になり、行分割ではなく fixture 不備を検査するテストになる。

**提案**:

1. plan に exact helper 契約を追記する。共通 session ID、三 path、`rollouts=[{session_id,path,bytes}]`、`session_ids=[id]`、一致する session_meta / turn_context を固定する。これを推す。
2. 直接関数を避けて end-to-end launcher を使う択もあるが、fixture コストと失敗原因が増えるため推さない。

## 既存テストに CRLF 仕様を固定するものは見当たらない

**区分**: 整合・実効性

**根拠**: 関連する `test_codex_worker_launch.py`、budget test、role runtime、codex hooks を `\r`、CRLF、separator、`splitlines` 依存で検索した。worker launcher 側には物理 CR / CRLF fixture がない。`test_codex_role_runtime.py:121-136` の `result-cr` は nested `result_json` 内の CRで、外側 JSONL では escape されるため今回の物理行境界変更とは別物である。

plan の五件以外で変更経路を通る代表 node は次である。

- `test_codex_worker_launch.py::test_positive_p1_normal_job_is_accepted` (`:3143`)
- `test_codex_worker_launch.py::test_delayed_thread_and_rollout_are_read_from_byte_zero` (`:6704`)
- `test_codex_worker_launch.py::test_final_drain_actuals_are_rechecked_before_acceptance` (`:6802`)
- `test_codex_worker_launch.py::test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts` (`:6342`)
- `test_codex_worker_launch.py::test_docs_authority_alone_rejects_consistent_effort_mutation` (`:6098`)

これらは LF 正常系の `_drain_stdout`、`_tail_rollout`、`_recorded_summary`、recompute を通るため、誤編集なら落ちる。ただし正確な六式置換で意図的に落ちる既存 node は静的には見つからない。`s2-plan.md:106-108` の file 全体焦点走はこれらを包含する。

**これが real なら何が壊れるか**: 既存 suite は CRLF 過受理の変更を検出せず、新規 test が唯一の固定点になる。新規 file の F42 違反が残ると、その固定点を追加した結果として受入全走だけが赤になる。

**提案**:

1. 計画どおり worker test file 全体を回し、新規 test と plain-runner meta node を加える。これを推す。
2. hook parser を今回へ含める裁定なら `test_codex_hooks.py` に separator test も必要。

## 六アンカーと維持行は正確で、327 除外も live 経路では正しい

**区分**: 整合・実効性

**根拠**: 現物との一件ずつの照合結果は次のとおり。

| 対象 | 照合結果 |
|---|---|
| `events.py:316` | exact: `text.splitlines()` |
| `worker:1273` | exact: `complete.splitlines()` |
| `worker:1406` | exact: `complete.splitlines()` |
| `worker:2335` | exact: `raw.splitlines()` |
| `worker:4097` | exact: `closed.splitlines()` |
| `worker:4119` | exact: `raw.splitlines()` |
| 全体 byte 上限 | `events.py:314` から `:170-197` へ到達。実比較は `:183-188` |
| 一行 byte 上限 | `events.py:319-324` exact |
| `strict_json_loads` | `events.py:273-307` exact |
| 空行 skip | `events.py:317-318` と worker `:1274-1275,1407-1408,2336-2337,4098-4099,4120-4121` は全て exact |
| worker 行上限 | `:1277-1280,1410-1414,2339-2342,4101-4105,4123-4127` は全て exact |

ずれたアンカーはない。

`worker:327` は `git rev-parse --show-toplevel` の str stdoutで、判定は `:328-337`。現 checkout の読取 probeでは stdout 末尾が byte `0a` で、`split("\n")` は path と空文字の二要素になった。従って正常な live git 成功時も `len != 1` で launch 前に失敗する。コード一般としては末尾 LF のない mock なら通るため「無条件に常時」ではなく「正常な live git 出力では常時」が正確である。

**これが real なら何が壊れるか**: `:327` まで機械置換すると全 attempt が hook 検証前に launcher error になる。T-1731 の「worker 六箇所」は syntactic `splitlines()` 数としては正しいが、JSONL 六箇所という意味では一件過大である。

**提案**:

1. `:327` は変更しない。これを推す。
2. brief と plan では「worker の JSONL 五式、events の一式」と表記し、単なる `splitlines` 出現数と区別する。

## 総括

- 最重所見 1: 六箇所変更は CR / CRLF の受理集合を縮め、brief の単調増加不変条件と矛盾する。
- 最重所見 2: 新規 test は harness でも allowlist 対象でもなく、F42 meta node が確実に赤になる。
- 最重所見 3: repo-wide 閉包は偽で、`check_codex_hooks.py:423` に同型の str JSON event splitter が残る。
- 段 4 はまず、CRLF 拒否強化を六箇所裁定の一部として正式に採るか、events 一箇所へ狭めるかを裁定すべき。
- 六箇所を維持するなら、CRLF branch と指定 killer node を採り、追加 mutation fanout は許容する。
- 新規 test は `pytest.main([__file__])` の実 `__main__` を持たせ、plain-runner meta node を焦点走へ加える。
- hook parser は現 scope 外の real 所見として別裁定パッケージ化するのを推す。