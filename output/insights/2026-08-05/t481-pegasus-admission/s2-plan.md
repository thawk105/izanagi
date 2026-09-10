# 段 2 実装プラン

結論として、実装方針は成立しますが、P1 をそのまま採用するには実装前の資源実測が不足しています。特に親 brief の「`collect_receipt.py` は構造的にメモリ有界」という前提は静的読解と一致しません。

[collect_receipt.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:46) の SHA-256 は 1 MiB streaming ですが、JSON 全読込、stderr 全読込、`rglob` の全件 materialize が [同:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:33)、`:67-79`、`:147-151` にあります。`collect_t126_qualification.py` の downstream も scheduler log 等を全読込します。したがって両 collector は「構造的有界」ではなく「要実測」です。

また、`make_acquisition_receipt.py` は [certify_calibration.sh:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/certify_calibration.sh:633) から呼ばれる compute-side helper なので、login-ok にはしません。

## 1. 分類表

コードへ書く target class は次のとおりです。`要実測` の行は、§7.0 の実測が規範値未満であることを確認してから `login-ok` として land します。失敗・未測定なら `compute-only` に倒します。

| `tools/pegasus/` entry | target class | 根拠・事前条件 |
|---|---|---|
| `certify_calibration.sh` | `compute-only` | PBS job body。build・calibration を行い、PBS 環境を必須化。 |
| `collect_receipt.py` | `login-ok`（要実測） | README §3 の login collector。ただし全読込と全件 manifest があり構造的有界ではない。 |
| `collect_t126_qualification.py` | `login-ok`（要実測） | login-side collector。downstream が scheduler log、JSON/JSONL、closure を全読込するため要実測。 |
| `dispatch_compute.py` | `login-ok`（要実測または既存裁定の grandfather） | D103/D105 の既存 sanctioned control plane。log file は 64 KiB cap だが、`subprocess.run(capture_output=True)` の scheduler 出力には hard cap がない。 |
| `exec_calibrate.py` | `compute-only` | [exec_calibrate.py:32-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/exec_calibrate.py:32) の任意 `os.execv` trampoline。D103 決定 5 の拒否対象。 |
| `fetch_third_party.py` | `login-ok` | §7.0 で全 subcommand の certified peak が 140–222 MiB と実測済み。pin 変更時は再分類。 |
| `floor_campaign.sh` | `compute-only` | PBS floor job body。 |
| `floor_scoping.sh` | `compute-only` | PBS scoping job body。brief の P3 列挙漏れだが先頭から compute 専用。 |
| `make_acquisition_receipt.py` | `compute-only` | certification job 内 helper。入力 JSON は全読込であり構造的有界でもない。 |
| `run_probe.py` | `compute-only` | compute allocation の attestation を採る helper。軽量でも login 実行では観測対象が違う。 |
| `silo_ladder_rung1.sh` | `compute-only` | PBS build/measurement job body。 |
| `smoke_probe.sh` | `compute-only` | PBS exploration job body。 |
| `submit_certify.sh` | `login-ok`（要実測または grandfather） | 既存 sanctioned login submitter。資源測定記録は指定資料にない。 |
| `submit_floor.sh` | `login-ok`（要実測または grandfather） | 既存 sanctioned login submitter。資源測定記録は指定資料にない。 |
| `submit_silo_ladder_rung1.sh` | `login-ok`（要実測または grandfather） | login submitter だが、runbook:400 が外部 3 repo clone により明示的に `unknown` としている。 |
| `submit_t126_qualification.sh` | `login-ok`（要実測） | 先頭コメントどおり login submitter。ただし git archive、repo 検査、embedded Python の全読込があり、役割だけでは P1 を満たさない。 |
| `t126_qualification.sh` | `compute-only` | PBS qualification job body。 |
| `t141_region_profile.sh` | `compute-only` | PBS build/perf job body。 |

`README.md` と `policy.json` はデータであり実行体表から除外します。`.py` は executable bit がないものも `python3 path` で実行できるため、meta-test では拡張子 `.py` / `.sh` または executable bit のいずれかを実行体条件にします。

### 実測 gate

実装前に、要実測 entry を §7.0 の専用 cgroup scope で測ります。

- `--help` のような早期終了形は代表値にしない。
- collector は documented collect/verify argv と現実的な完了 attempt fixtureを使う。
- submitter は scheduler 非投入の隔離 fixtureを使う場合も、実際に通る preflight を省かない。
- commit、正確な argv、入力 bytes/件数、`memory.max`、反復最大、certified peak を記録する。
- 測定結果が保証するのはその argv・入力だけであり、path 全体の任意 argv/env を保証しないと明記する。

P1 を厳密適用して測定を省く場合、現在 ALLOW の `dispatch_compute.py`、`submit_certify.sh`、`submit_floor.sh`、`submit_silo_ladder_rung1.sh` まで DENY に反転します。これは本 wave の狙いと既存受理集合維持に反するため、測定または grandfather の裁定なしに実装へ進めません。

## 2. `guard_bash.py` のデータ構造

[guard_bash.py:165-213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:165) を次の形へ再編します。

1. 二つの値定数を置く。

   ```python
   _PEGASUS_LOGIN_OK = "login-ok"
   _PEGASUS_COMPUTE_ONLY = "compute-only"
   ```

2. 上記18 entryを exact repo-relative path で持つ `_PEGASUS_EXECUTION_CLASSES` を追加する。値はこの二値だけにする。

3. `_SANCTIONED_PATHS` は独立した二重表にしない。

   - `tools/run_tests.py`
   - `tools/check_ai_provenance.py`

   だけを `_NON_PEGASUS_SANCTIONED_PATHS` として手書きし、そこへ分類表中の `login-ok` path を機械的に union して `_SANCTIONED_PATHS` を作る。既存テストが参照する `_SANCTIONED_PATHS` 名は維持する。

4. `_SANCTIONED_HEADS` の `qsub/qdel/qstat` は現状維持する。

これにより Pegasus path を `_SANCTIONED_PATHS` と分類表へ重複記載せず、D103 決定 5 の exact-path 契約を維持できます。

[guard_bash.py:411-420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:411) の直後に `_pegasus_execution_class(path)` を置きます。

- exact key なら二値 class を返す。
- 正規化済み path の component が `tools/pegasus/...` だが表にない場合は private sentinel `_PEGASUS_UNCLASSIFIED` を返す。
- Pegasus 外なら `None`。
- allow 判定に glob/prefix は使わない。未分類・nested entry の認識は deny にだけ使う。

## 3. 判定経路の書き換え

### `_script_target`

[guard_bash.py:479-493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:479) を次の順序にします。

1. `_python_module_invocation()` を一度だけ呼ぶ。
2. Python `-m` invocation がある場合、候補は Python head と解決できた module target だけにする。
3. `-m` invocation がない Python/shell invocation に限り、位置引数の script file を候補へ加える。
4. candidate は `_SANCTIONED_PATHS` または `_pegasus_execution_class(candidate) is not None` なら返す。
5. 現行の `path.startswith("tools/pegasus/")` は削除する。

これで `-m X` の後続位置引数は module X のデータになり、実行体候補にはなりません。

### `_heavy_segment_violation`

[guard_bash.py:592-623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:592) の順序は次を維持します。

1. `_provenance_violation`
2. sanctioned exact entry
3. Pegasus class
4. pytest/build/perf 等の既存重量判定

`:610-612` は以下の意味へ置換します。

- `compute-only` → DENY
- `_PEGASUS_UNCLASSIFIED` → DENY
- `login-ok` → `_SANCTIONED_PATHS` 由来の早期 ALLOW
- Pegasus 外 → 後続判定

拒否文は `compute-only` と `未分類` を区別してもよいですが、受理 bit と無関係なので既存文言維持でも構いません。

### OTHER / COMPUTE の 1-bit 不変

構造上の保証点は [guard_bash.py:947-958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:947) です。

- `_heavy_command_violation()` は `_refuses_heavy_work(site)` が真の場合だけ呼ばれる。
- `site=None`、`OTHER`、`PEGASUS_COMPUTE` は偽。
- `_SANCTIONED_PATHS`、`_script_target`、Pegasus 分類表は heavy 経路以外から参照されていない。

したがって変更をこの閉包内に限定すれば OTHER/COMPUTE の後段防護 tree 判定も含め受理集合は変わりません。テスト側では既存 `test_bash_other_keeps_legacy_acceptance_bits` に加え、18 entry の代表 invocationを OTHER/COMPUTE へ通す table-wide 正例を追加します。

## 4. `-m <module>` の単一意味規則

修正箇所は `_script_target` の候補生成側だけで十分です。`_provenance_script_borrow` を族全体へ拡大すると module target 自身が sanctioned な場合まで誤って落とすため採りません。

[guard_bash.py:560-575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:560) の `_provenance_script_borrow` と `:606-608` の既存保護は、既存テストの期待値を変えないため残します。一般則の権威は `_script_target` に移り、この helper は provenance の互換安全網になります。

三つの不整合は次の一規則で閉じます。

- `python3 -mpytest tools/run_tests.py`  
  実行体は `pytest`。`tools/run_tests.py` を sanctioned として借用せず、pytest 分岐で DENY。
- `python3 -m pytest tools/run_tests.py`  
  従来どおり pytest 分岐で DENY。
- `python3 -mpy_compile tools/pegasus/collect_receipt.py`  
  実行体は `py_compile`。file はデータなので ALLOW。分離形と一致。

静的に期待値を維持できる既存 node は次です。

- `test_bash_login_blocks_attached_and_bundled_python_modules`
- `test_bash_login_python_module_option_boundaries_allowed`
- `test_bash_login_blocks_nonsanctioned_provenance_entrypoints`
- `test_bash_login_allows_nonexecuting_provenance_flags`
- `test_bash_compute_allows_provenance_forms`
- `test_bash_login_allows_static_module_reads_of_provenance_script`
- `test_provenance_script_borrow_does_not_lend_sanctioned_status`
- `test_bash_login_provenance_branch_does_not_capture_readers`
- `test_bash_login_sanctioned_entries_are_exact`

特に `test_bash_login_allows_static_module_reads_of_provenance_script` の `py_compile/json.tool/compileall` は、後続 file を target 候補にしなくなるためすべて ALLOW のままです。

## 5. テスト設計

[orchestrator/tests/test_hooks.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:893) 付近へ Pegasus 分類テスト群をまとめます。

### 分類の正例・拒否例

- `test_bash_login_allows_classified_login_entries`
  - 新規三 entry と既存 login-ok を固定 spelling で検査。
  - LOGIN と SUSPECT の両方。
- `test_bash_login_blocks_classified_compute_entries`
  - PBS job body 全本、`exec_calibrate.py`、`make_acquisition_receipt.py`、`run_probe.py`。
- `test_bash_other_and_compute_preserve_all_pegasus_entry_bits`
  - 全18 entryを OTHER/COMPUTE へ渡し、既存 ALLOW bitを固定。
- `test_bash_login_rejects_unclassified_pegasus_entry`
  - 実在不要の `python3 tools/pegasus/future_entry.py` を DENY。未登録 fail-closed を runtime でも固定。

### `-m` 回帰

[同:983-1059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:983) 付近へ追加します。

- `test_bash_login_module_target_cannot_borrow_sanctioned_path`
  - `-mpytest tools/run_tests.py`
  - `-mpytest` と現在 sanctioned な Pegasus 5 path
  - `-qmpytest` / `-Bmpytest` 等の attached bundle
- `test_bash_login_attached_static_modules_treat_paths_as_data`
  - `-mpy_compile tools/pegasus/exec_calibrate.py`
  - `-mpy_compile tools/pegasus/collect_receipt.py`
  - `-mjson.tool tools/pegasus/policy.json`
  - 各々の分離形との bit 一致

### 悉皆 meta-test

[同:1360-1385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1360) の `os.listdir` 型 meta-test に合わせ、`test_bash_all_pegasus_execution_entries_are_classified` を追加します。

検査内容は三つです。

1. `tools/pegasus/` 直下の `.py` / `.sh` または executable regular file の集合と、`_PEGASUS_EXECUTION_CLASSES` の key 集合が完全一致。
2. value 集合が `{login-ok, compute-only}` の部分集合で、空でない。
3. 分類表の `login-ok` key 集合と、`_SANCTIONED_PATHS` 中の Pegasus path 集合が完全一致。

これにより、新しい実行体を追加しただけなら集合差で赤、分類 row を追加すればこの meta-test は緑になります。未知 entry の runtime DENY は別テストが担うため、meta-test 自身を挙動 oracle にしません。

## 6. 受理集合の変化

以下は要実測 entry が target `login-ok` になった場合です。

### 現在 DENY → 実装後 ALLOW

新しい direct execution class は次の三つです。

- `python3 tools/pegasus/collect_receipt.py ...`
- `python3 tools/pegasus/collect_t126_qualification.py ...`
- `tools/pegasus/submit_t126_qualification.sh --dry-run`

`./path`、repo 内絶対 path、対応 interpreter、解決可能な Python module spellingも同じ path 正規化 classとして反転します。

`-m` 修正による完全な変化 family は、

> attached/bundled `-mM` で、現在は最初の位置引数が非-sanctioned `tools/pegasus/...` であるためだけに拒否され、module M 自体には重量拒否がない invocation

です。代表綴りは次です。

- `python3 -mpy_compile tools/pegasus/collect_receipt.py`
- `python3 -mpy_compile tools/pegasus/exec_calibrate.py`
- `python3 -mjson.tool tools/pegasus/policy.json`
- 同じ module の `-qmpy_compile` 等の bundle

分離形は現在も ALLOW なので変化しません。

### 現在 ALLOW → 実装後 DENY

意図した縮小は、attached pytest が sanctioned file を実行体として借りている familyだけです。

- `python3 -mpytest tools/run_tests.py`
- `python3 -mpytest tools/pegasus/dispatch_compute.py`
- `python3 -mpytest tools/pegasus/fetch_third_party.py`
- `python3 -mpytest tools/pegasus/submit_certify.sh`
- `python3 -mpytest tools/pegasus/submit_floor.sh`
- `python3 -mpytest tools/pegasus/submit_silo_ladder_rung1.sh`

各 path の `./`、repo 内絶対 path、および `-qmpytest` / `-Bmpytest` 等「`m` に `pytest` が密着する bundle」も同一 familyです。

`tools/check_ai_provenance.py` は既存 `_provenance_script_borrow` がすでに拒否しているため変化しません。新規 login-ok 三 entry は現在も Pegasus deny により拒否されているので、pytest 形は DENY→DENYです。

測定をせず P1 strict で進む場合は、これ以外に既存四 entryの ALLOW→DENYが発生します。これは推奨しません。

## 7. docs

[docs/pegasus-runbook.md:348-360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/docs/pegasus-runbook.md:348) に次を追記します。

- 測定結果は記録した argv/env/input にだけ有効。
- path-level hook admission が任意 argv の 512 MiB 未満を保証するものではない。
- argv/env admission は本 wave では実装しない。
- input/pin が変われば再測定する。

`:393-418` の `unknown` / `local-ok` 表は、実測値が得られた entryだけ実値で更新します。値を推測で書きません。`:432-435` には、分類判断の正本が `guard_bash.py`、未分類は fail-closed、meta-test が direct entry の悉皆だけを保証することを記します。

[hooks/README.md:78-82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/README.md:78) は既に「exact path と判定は guard が正本」としているため変更しません。全18 entryを転記しません。

## 8. 変異事前登録候補

いずれも DW-M01 の前後層を静的確認済みです。

1. `_script_target` の「module invocation があるとき位置引数を script 候補にしない」条件を1行削除する。  
   期待赤: `test_bash_login_module_target_cannot_borrow_sanctioned_path[tools-run-tests]`。  
   入力 `python3 -mpytest tools/run_tests.py` は前段 provenance に該当せず、正規実装では後段 pytest だけが拒否する。ほかの拒否層はない。

2. 同じ条件を壊し、`python3 -mpy_compile tools/pegasus/exec_calibrate.py` で位置引数を再び target にする。  
   期待赤: `test_bash_login_attached_static_modules_treat_paths_as_data[pycompile-exec-calibrate]`。  
   正規実装には拒否層がなく、変異時だけ Pegasus compute-only 分岐が拒否する。

3. 分類表の `collect_receipt.py: login-ok` 1行を `compute-only` に変える。  
   期待赤: `test_bash_login_allows_classified_login_entries[collect-receipt]`。  
   provenance/pytest/build のどれにも該当せず、変異後の分類分岐だけが拒否理由になる。

4. `_pegasus_execution_class()` の未登録 fallback を sentinel から `None` に変える。  
   期待赤: `test_bash_login_rejects_unclassified_pegasus_entry`。  
   `future_entry.py` は provenance・sanctioned・pytest等に該当せず、この fallbackだけが拒否する。

5. `floor_scoping.sh` の分類 rowを1行削除する。  
   期待赤: `test_bash_all_pegasus_execution_entries_are_classified`。  
   runtime では未分類 fallbackが同じ入力を引き続き拒否するため、挙動テストは赤にならず、悉皆 meta-testだけが「実体と表の差」という単一理由で赤になる。

pytest は実行しておらず、緑は主張しません。worktree は変更なし・cleanです。

## 総括

- 変更ファイルと行:
  - `hooks/guard_bash.py:165-213` — 二値分類表、derived `_SANCTIONED_PATHS`
  - `hooks/guard_bash.py:411-420` 直後 — class lookup と未分類 sentinel
  - `hooks/guard_bash.py:479-499` — module を実行体へ固定した target 解決
  - `hooks/guard_bash.py:592-623` — table-based allow/deny
  - `orchestrator/tests/test_hooks.py:686-723, 893-930, 955-1059` — 分類・`-m`・不変集合テスト
  - `orchestrator/tests/test_hooks.py:1360-1385` 同型 — 悉皆 meta-test
  - `docs/pegasus-runbook.md:348-435` — argv限定の測定根拠、再分類条件、保証限界
  - `hooks/README.md`、`docs/decisions.md` は変更しない
- 未解決の設計択一:
  - 要実測7 entryを測ってから `login-ok` にするか、既存4 entryだけD103/D105で grandfather するか
  - path-level admission が argv別測定より粗いことを受理するか、将来CLI cap/site gateを別 waveに起票するか
- 親が段4で裁定すべき点:
  - `collect_receipt.py` の「構造的有界」前提を撤回し、実測必須へ直すこと
  - `make_acquisition_receipt.py` を compute-only helper とすること
  - 未測定のまま既存 sanctioned を縮小しないこと
  - attached pytest sanctioned-borrow familyの ALLOW→DENYを意図した受理集合縮小として承認すること