結論は **NO-GO** です。指定4ファイルはすべて読めました。`pegasus02` 上では静的検査だけを行い、pytest・変異実走・実データ走査はしていません。13 passed は親の報告としてのみ扱っています。

### 主所見

1. M8・M10・M12 は既定テキスト出力に限定すれば生存します。

ほぼ全テストが `--json` を使う [_run_json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/tests/test_claude_session_ledger.py:101) 経由です。既定の [_render](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:429) を値付きで検査するのは compaction の一部だけです。

そのため、以下は全テストを通過できます。

- M8: テキストだけ root/sidechain を合算した1区画にする。
- M10: テキストの「読めなかった file」を削除または常に `0` にする。
- M12: テキストの projects root・project/cwd filter を削除または偽値にする。

JSON 内部だけを正本と限定すれば全12変異を kill できますが、裁定にその限定はなく、CLI の既定出力はテキストです。この逃げ道は認められません。

放置時: 既定CLIが誤った母集団・合算値を表示しても、テストは緑のままです。

2. read-only テスト自身が source tree への bytecode write を見逃しています。

実装の入力 open は `"rb"` で、出力先引数・tempfile・file log はなく、明示的な出力は stdout/stderr だけです。この狭い直接CLI経路は read-only です。

しかしテストは ledger を [`exec_module()` で import](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/tests/test_claude_session_ledger.py:18) します。loader が自身の `.pyc` を作る判定は、module 本文が [`sys.dont_write_bytecode=True`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:14) を実行するより前です。

実際に次の ignored file が存在します。

`tools/__pycache__/claude_session_ledger.cpython-310.pyc`

source の更新時刻は 13:39:56、pyc の生成時刻は 13:41:58 でした。一方、テストが検査するのはコピー先の `copied_tools/__pycache__` だけです（[L607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/tests/test_claude_session_ledger.py:607)）。

さらに transcript の bytes と mtime しか snapshot しないため、新規 sidecar/log、別名ファイル、書いて元へ戻す操作、相対パスへの書込みも生存します。48 xdist worker は同じ source pycache を共有します。

放置時: read-only を名乗るテスト実行または将来の回帰が、source tree や transcript 周辺へファイルを残します。

3. `--max-files` はファイル数しか制限せず、login-safe な資源上限ではありません。

既定値は **25** です（[L28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:28)）。100本超の全ファイルを既定で parse はせず、26本目を発見した時点で止まります。

ただし安全性は証明できません。

- 25本それぞれの byte 数、1行長、record 数には上限がありません。
- `json.loads(line)` は巨大な1行全体を構築します。
- 全 request、全 valid usage、tool ID、compaction meta、issue detail を走査終了まで保持します。
- `--max-files` に上限値はなく、任意に巨大化できます。
- symlink file、FIFO、regular file 以外を拒否しません。
- hostname/site gate もありません。

したがって runbook §7.0 の定義では未計測かつ入力依存の `unknown`、すなわち `dispatch-required` です。

また、既定値のテストは

```python
assert report["population"]["max_files"] == LEDGER.DEFAULT_MAX_FILES
```

という実装定数との自己比較です。`DEFAULT_MAX_FILES = 1_000_000` にしても、明示上限テストは `--max-files 2` なので全テストが通ります。

放置時: 壊れた巨大JSONL一つで16 GiB共有cgroupをOOMさせ、無関係な session/process が殺されます。

4. discovery error は黙って母集団から消えます。

[`os.walk()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py:163) に `onerror` がなく、directory の `scandir` failure は既定動作で無視されます。テストが作るのは、発見済み regular file の `Path.open` failureだけです。

また file symlink は `followlinks=False` の対象外で、root 外へ解決された `.jsonl` も読みます。これにより報告した projects root と実際の入力母集団が一致しません。

放置時: unreadable subtree や root 外の入力が、`files_unreadable=0` のまま集計へ混入・脱落します。

5. 「final usage」の検査は M2 を kill するが、final semantics 自体は固定していません。

M2 fixture は先行 `output_tokens=1`、最終 `247` なので「最初を採る」変異は確実に落ちます。一方、最終値が全 field で prior maximum 以上なので、「各 field の最大値を採る」変異も同じ251を返して通ります。

実装にある `usage_final_below_prior_max` 分岐も未発火です。`STRICT_ISSUES` 9分類のうち、strict failure が直接確認されるのは実質 `malformed_usage` と `missing_request_key` だけです。malformed JSON・unreadable file の fixture は非 strict です。

放置時: `--strict` が破損・欠落・usage rollback を検出しなくなっても、受入は緑のまま過小／過大集計を承認します。

### 独立性・既存資産

テストデータはすべて `tmp_path`、固定 timestamp/mtime、明示 `--projects-root` です。実データ、今日の日付、消費量、hash への依存はありません。xdist の主要な相互干渉は前述の source pycache です。

`git status` 上の変更は新規2ファイルだけで、既存テスト期待値の変更はありません。新規テストは `pytest.main` harness を持つため plain-runner allowlist の追記も不要です。

`codex_worker_ledger.py` との比較では、`model_calls` は双方とも観測源を docstring で限定しており、tool call と混同していません。ただし JSON の `input_tokens` は意味が異なります。

- Claude: cache read/creation と加算する「通常入力」部分
- Codex: cached input を内包する総 input

共通 consumer が同名 field として扱えば誤集計します。現 scope に共通 consumer はないため backlog としますが、横断集計を追加する前に semantic metadata または canonical total 名を揃える必要があります。

`tools/README.md` は 2,949/3,000 bytes、dev-wave 4文書は 25,187/25,200 bytesでした。本実装や self-run harness自体は docs 追記を要求しません。ただし login-local-ok を主張するなら実測・分類が必要で、固定scopeを再裁定せず docs へ追加してはいけません。

## 総括

**(a) 判定: NO-GO。** 9/12 は集計・JSON経路で kill されますが、既定テキスト面で M8・M10・M12 が生存し、read-only と login-safe の保証にも実在する穴があります。

**(b) must-fix**

1. 既定テキスト出力について、root/sidechain、unreadable count、root/filter、時間根拠、主要 token 値を exact に検査する。  
   放置時: JSONだけ正しく、利用者が通常見るCLI出力が偽値でも緑になります。

2. テスト import の bytecode write を抑止し、transcript単体でなく隔離tree全体の増減と書込先引数不在を検査する。  
   放置時: read-only test自身または回帰が共有worktree・session treeへ書き込みます。

3. total bytes・1行長・record/issue保持量を hard bound するか、Pegasus login nodeでfail-closedに拒否する。既定25と既定rootも独立literalで固定する。  
   放置時: 巨大・特殊JSONLが共有cgroupをOOMまたは永久blockさせます。

4. `os.walk(onerror=...)`、regular-file確認、resolve後のroot containmentを導入してテストする。  
   放置時: unreadable subtreeを黙って落とすか、宣言root外を母集団へ混入させます。

5. descending final usage と `STRICT_ISSUES` 全分類の fail-closed matrixを追加する。  
   放置時: final/max semanticsやstrict failureが退化しても、破損入力を正常集計として受理します。

**(c) M1〜M12 判定表**

下表の行番号は [test_claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/tests/test_claude_session_ledger.py:109) です。JSONと既定テキストの双方を公開面として判定しています。

| 変異 | 判定 | kill node / assert と理由 |
|---|---|---|
| M1 record単位 | **kill** | `test_request_dedupe_uses_final_usage_and_all_three_input_fields` L157。`model_calls` が2ではなく3。rawも66→126。 |
| M2 最初のusage | **kill** | 同 node L163。先行output 1、最終247なので、期待251に対し mutant は5。 |
| M3 cache read除外 | **kill** | 同 node L162。raw期待66に対し55。field自体を落とせばL159も失敗。 |
| M4 cache creation除外 | **kill** | 同 node L162。raw期待66に対し44。field自体を落とせばL160も失敗。 |
| M5 input除外 | **kill** | 同 node L162。raw期待66に対し33。field自体を落とせばL161も失敗。 |
| M6 synthetic計上 | **kill** | `test_synthetic_zero_usage_is_excluded_and_reported` L197/L199。model_callsが1→2、またはexcludedが1→0。synthetic fixtureは実在。 |
| M7 sidechain未走査 | **kill** | `test_recursive_sidechains_are_separate_and_only_explicitly_combined` L239–241。sidechain期待 `1 calls / 2 tools / raw 60` が全ゼロ。 |
| M8 親へ合算 | **生存** | JSON集計を変えれば同 node L237–249で落ちる。しかし `_render` だけを単一合算区画にする mutant を検査するassertがない。root 6、sidechain 60という異値fixture自体は良い。 |
| M9 mtimeだけ | **kill** | `test_window_uses_each_event_timestamp_then_reports_mtime_fallback` L317–327。対象file mtimeはuntilちょうどなので、mtime-onlyでは `model_calls 2→1`, raw `24→18`, output `12→8`。basisも完全一致比較。 |
| M10 unreadableを0 | **生存** | JSON counterを0にすれば `test_unreadable_file_is_counted_without_crashing` L466が落ちる。しかし既定textだけを0/省略する mutant は無検査。fixture中のunreadable fileは実在。 |
| M11 上限無視 | **kill** | `test_population_filters_corruption_and_file_limit_are_visible` L414–420。上限2に対し対象project内に3ファイルあり、scan 2→3、root calls 1→2、raw 3→27。 |
| M12 root/filter省略 | **生存** | JSONから落とせば同 node L411–413がKeyError/不一致。しかし既定textのroot・project/cwd filterだけを削除・偽装する mutant は無検査。 |