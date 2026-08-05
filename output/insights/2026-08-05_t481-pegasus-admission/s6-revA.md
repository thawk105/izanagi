結論は **land 不可**。静的読解のみで real 4 件、疑わしい nit 1 件を確認した。pytest・hook subprocess は実行しておらず、緑は主張しない。

## 受理集合の照合

直接 entry の三値分類は裁定どおりだった。

- `unknown`: `collect_receipt.py`、`collect_t126_qualification.py`、`submit_t126_qualification.sh` はそれぞれ [guard_bash.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:190)、[guard_bash.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:196)、[guard_bash.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:298) で正しい。
- `local-ok` は既存 5 本だけ: `dispatch_compute.py`、`fetch_third_party.py`、`submit_certify.sh`、`submit_floor.sh`、`submit_silo_ladder_rung1.sh`。
- 残る直接 entry は `unknown` または `dispatch-required` で、LOGIN/SUSPECT では拒否される。
- 未登録 nested も sentinel 経由で拒否される [guard_bash.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:577)。

裁定に一致する意図的な ALLOW→DENY は次の族だった。

- `python3 -m pytest.__main__ ...`
- `python3 -m _pytest.main ...`
- `python3 -m cProfile|profile|pdb|trace|runpy <対象>`
- `python3 -W ignore <対象>`、`python3 -X faulthandler <対象>`
- `bash -O extglob <対象>`、`bash -o errexit <対象>`
- `python3 -mpytest tools/run_tests.py` および sanctioned Pegasus path 借用

一方、裁定外の変化がある。

| 綴り | baseline → 差分後 | 判定 |
|---|---:|---|
| `python3 -mpy_compile tools/pegasus/collect_receipt.py` | DENY → ALLOW | 裁定外。baseline は [probe_attached_m.json:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_attached_m.json:45)、新テストが ALLOW を固定 [test_hooks.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:757) |
| `python3 -c 'print(1)' -m pytest` | DENY → ALLOW | 裁定外。baseline は [probe_lens_claims.json:141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_lens_claims.json:141)、新テストが ALLOW を固定 [test_hooks.py:785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:785) |
| `python3 --help tools/pegasus/collect_receipt.py` | DENY → ALLOW | 未報告。新 parser が long option で解析を終了する [guard_bash.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:604) |
| `python3 -Z tools/pegasus/collect_receipt.py` | DENY → ALLOW | 未報告。未知 short option を `invalid` として後続 path を捨てる [guard_bash.py:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:640) |
| `bash -s tools/pegasus/certify_calibration.sh` | DENY → ALLOW | 未報告。`-s` 後を argv として捨てる [guard_bash.py:762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:762) |
| `python3 tools/pegasus` | ALLOW → DENY | 未列挙の縮小。registry lookup が directory 自体も未登録扱いする [guard_bash.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:583)。実行不能 directory なので後述の nit |

なお、実装報告 [s5-impl.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.md:41) の `python -c <code> <Pegasus path>` まで DENY→ALLOWだったという記述は静的には不正確。旧実装は第1非 option の `<code>` を target としていたため、単なる後続 path 形は既に ALLOW。実測 baseline が支える反転は後続 `-m pytest` 形である。

## 所見

### 1. [real] `--rcfile` / `--init-file` を data として捨て、新しい実コード実行経路を開けている

- 根拠: 両 option が通常の値 option に含まれる [guard_bash.py:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:734)。値を2 tokenまとめて消費し [guard_bash.py:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:750)、`_script_target` は startup file を候補に戻さない [guard_bash.py:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:788)。Bash の `--rcfile FILE` / `--init-file FILE` は interactive shell で FILE のコマンドを読み、実行する。
- 再現綴り:
  - `bash --rcfile tools/pegasus/certify_calibration.sh -i`
  - `bash --init-file=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/certify_calibration.sh -i`
  - `bash -lc 'bash --rcfile /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/certify_calibration.sh -i'`
  - `qstat; bash --rcfile ./tools/pegasus/certify_calibration.sh -i`
  
  旧実装は FILE を第1非 option として DENY、新実装は全て ALLOW へ落ちる。既存テストは安全な `/tmp/bashrc` の後ろに別 script を置く形しか扱っていない [test_hooks.py:779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:779)。
- 修正案: startup-file option を一般の value option から外し、値自身を execution target として登録する。後続 script と startup file の両方を検査するため、target は単数返却ではなく集合にする。relative・absolute・wrapper・shell-string の回帰テストを追加する。
- 成果物影響: `dispatch-required` job body を実行する LOGIN 受理綴りが増え、「local-ok 以外は全拒否」というレポート・台帳の受理集合参照が偽になり、その経路由来 run は certified 選択の site proof を失う。

### 2. [real] script executor の閉集合が閉じておらず、bundle 形で新しい fail-open を作る

- 根拠: 閉集合は [guard_bash.py:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:333) の6標準 moduleと `coverage` だけ。少なくとも次が欠ける。
  - `pydoc`: `.py` path を `importfile()` へ渡す [/usr/lib/python3.10/pydoc.py:2803](/usr/lib/python3.10/pydoc.py:2803)。loader は module を実際に load/execute する [/usr/lib/python3.10/pydoc.py:400](/usr/lib/python3.10/pydoc.py:400)。
  - `doctest`: 全 `.py` 引数を import して doctest を走らせる [/usr/lib/python3.10/doctest.py:2791](/usr/lib/python3.10/doctest.py:2791)。
  - `unittest`: `python -m unittest` は runner を起動する [/usr/lib/python3.10/unittest/__main__.py:18](/usr/lib/python3.10/unittest/__main__.py:18) うえ、file path を module 名へ変換して import する [/usr/lib/python3.10/unittest/main.py:29](/usr/lib/python3.10/unittest/main.py:29)。
  - 既に集合内の `trace` も `--module` を boolean flag として扱えていない。標準実装は後続 module を `runpy` で実行する [/usr/lib/python3.10/trace.py:656](/usr/lib/python3.10/trace.py:656)、[/usr/lib/python3.10/trace.py:703](/usr/lib/python3.10/trace.py:703)。
- 再現綴り:
  - `python3.10 -Bmpydoc -- ./tools/pegasus/collect_receipt.py`
  - `python3.10 -Bmdoctest tools/pegasus/collect_receipt.py`
  - `python3.10 -Bmunittest tools/pegasus/collect_receipt.py`
  - `python3.10 -Bmtrace --trace --module tools.pegasus.exec_calibrate`
  
  最初の3つは旧 parser が後続 Pegasus path を捕らえて DENY、新 parser は非登録 module の後続を全て data として ALLOWする。最後は旧来穴を閉じられていない。
- wrapper・segment の複合形も通る:
  ```text
  qstat; sudo -u tanab env FOO=1 nice -n 0 taskset -c 0 timeout 5 numactl -C 0 python3.10 -Bmpydoc -- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py
  ```
  wrapper は [guard_bash.py:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:547) で全て剥がれ、module args は target 候補にならない [guard_bash.py:776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:776)。`./` と repo 内絶対 path の双方で成立する。`~` は lexical repo root 外へ展開される場合、既存の cwd/symlink scope 外穴のままであり、新差分の証拠には数えていない。
- 修正案: per-module の実 CLI grammar を持ち、全 execution target を列挙して返す。`pydoc`/`doctest`/`unittest` は複数 file を受けるため「最初の1本」では不十分。`trace --module` は次 token を module pathへ変換する。少なくとも dense/bundle・`--`・版付き head・全 wrapper・複数 target のテストを追加する。
- 成果物影響: LOGIN 受理集合に unknown/dispatch-required module import・test 実行綴りが残り、レポートと台帳の「全 entry deny」参照が偽になる。そこで生成・更新された run は certified 選択に使える site attestation を持たない。

### 3. [real] 裁定禁止の DENY→ALLOW を実装・テストが意図的に固定している

- 根拠: 裁定は「本 wave で ALLOW へ反転する entry は無い」と明記 [s4-ruling.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s4-ruling.md:85)。しかし実装報告自身が反転を認める [s5-impl.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.md:38)。
- 具体例:
  - `python3 -mpy_compile tools/pegasus/collect_receipt.py`: baseline DENY、新テストは ALLOW。
  - `python3 -Bmpy_compile -- tools/pegasus/certify_calibration.sh`: 同じ dense/bundle family。
  - `python3 -mjson.tool tools/pegasus/policy.json`: dense 形は DENY→ALLOW。
  - `python3 -mcompileall tools/pegasus/collect_receipt.py`: dense 形は DENY→ALLOW。
  - `python3 -c 'print(1)' -m pytest`: baseline DENY、新テストは ALLOW。
  - `python3 --help tools/pegasus/collect_receipt.py`、`python3 -Z tools/pegasus/collect_receipt.py`、`bash -s tools/pegasus/certify_calibration.sh`: 未報告の DENY→ALLOW。
- 修正案: 現裁定を正本とするなら、新設した ALLOW assertions [test_hooks.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:757)、[test_hooks.py:785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:785) を反転し、baseline-denied の dense/bundle/`-c`/interpreter-exit 形を互換 deny として保持する。意味的 false positive を解消したいなら、実装側で勝手に広げず新しい親裁定が必要。
- 成果物影響: 段7で記録される受理集合 delta が裁定の「縮小のみ」から外れ、レポートと試行台帳に少なくとも2件の実測済み DENY→ALLOW と追加の未実測 ALLOW family が混入する。

### 4. [real] module parser が実挙動を過大近似し、正当な非実行操作を新たに拒否する

- 根拠:
  - `timeit` は file runner ではなく、全位置引数を改行連結した Python statement として扱う [/usr/lib/python3.10/timeit.py:271](/usr/lib/python3.10/timeit.py:271)。`tools/pegasus/x.py` を渡してもその file は実行しない。
  - `runpy` CLI は後続を module 名としてだけ実行する [/usr/lib/python3.10/runpy.py:315](/usr/lib/python3.10/runpy.py:315)。slash を含む `.py` path は実行対象ではない。
  - `trace --report` は counts file から report を作って直ちに戻り、位置引数を実行しない [/usr/lib/python3.10/trace.py:679](/usr/lib/python3.10/trace.py:679)。
  - executor parser は未知 flag を読み飛ばして次の token を無条件に target とする [guard_bash.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:725)。
- 再現綴り:
  - `python3 -m timeit tools/pegasus/exec_calibrate.py`
  - `python3 -m runpy tools/pegasus/exec_calibrate.py`
  - `python3 -m trace --report -f /tmp/counts tools/pegasus/exec_calibrate.py`
  - `python3 -m cProfile --help tools/pegasus/exec_calibrate.py`
  
  いずれも分離 `-m` の baseline は ALLOW、差分後は DENY。最初の2件は新テストが誤った「script executor target」として固定している [test_hooks.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:749)。
- 修正案: `timeit` を path-based executor 集合から外す。重い inline statement 自体を止めるなら別の明示裁定・別分類にする。`runpy` は module-name regex に合う場合だけ path へ写像する。`trace --report` と各 module の `-h/--help` を非実行 mode として先に終了させる。
- 成果物影響: LOGIN の受理集合が baseline より不必要に縮み、レポートの正当操作一覧と台帳の拒否理由が誤る。これらの形自体は run を生成しないため、certified 選択値への直接変更はない。

### 5. [疑わしい / nit] registry root 自体の新規拒否

`_pegasus_admission_entry()` が `path == "tools/pegasus"` も未登録扱いするため、`python3 tools/pegasus` は新たに拒否される [guard_bash.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:583)。裁定の実行体 inventory には directory 自体を含めていないが、この綴りは Python が実行できず成果物影響も書けないため nit とする。

## 過剰拒否・scope・site 不変の確認

明示正例は、上記 executor-mode の例外を除き維持される。

- `python3 -m py_compile <file>`: ALLOW。
- pytest `--collect-only` / `--help` / `--version`: `_pytest_nonexecuting()` により ALLOW [guard_bash.py:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:806)。
- `--message-file` preflight: exempt flag に残る [guard_bash.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:366)。
- `qsub` / `qstat` / `qdel`: sanctioned head のまま [guard_bash.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:328)。

裁定で scope 外とされた6面への直接変更はない。

- cwd/relative/symlink 解決: `_invocation_path()` は差分外。
- `env -S` GNU grammar: `_expand_env_split_strings()` は差分外。
- shell `-c` 深さ: `depth < 2` は維持 [guard_bash.py:959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:959)。
- `systemd-run`: wrapper 集合へ追加されていない [guard_bash.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:119)。
- `collect_receipt.py` 入力 cap: 対象ファイルに差分なし。
- `pytest -h` / `--co`: `_pytest_nonexecuting()` に追加されず、既存 DENY のまま。

OTHER / PEGASUS_COMPUTE の1 bit不変はコード閉包で成立する。新 registry/parser は `decide()` の `_refuses_heavy_work(site)` 分岐内からしか呼ばれず [guard_bash.py:1260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:1260)、site policy は OTHER/COMPUTE に false を返す [site_policy.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/campaign/site_policy.py:74)。分岐後の既存防護ツリー判定には今回の変更関数への経路がない。

## 総括

- real 所見: **4 件**
- 最重要3件:
  1. `bash --rcfile/--init-file` による新規 fail-open
  2. `pydoc` / `doctest` / `unittest` と `trace --module` を欠く不完全な executor 閉集合
  3. `-mpy_compile` と `-c ... -m pytest` を含む、裁定禁止の DENY→ALLOW
- 直接 registry の3指定 entry は正しく `unknown` で、OTHER/COMPUTE bit と明示 scope 外6面は不変。
- land 判定: **不可**。少なくとも real 4件を修正し、baseline差分を「裁定列挙の ALLOW→DENY だけ」に戻したうえで、親環境の計算ノード上で受入を再走する必要がある。