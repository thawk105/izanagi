結論は **land 不可** です。57 綴りの `mismatch: 0` は、その57件に限れば整合していますが、検査外で実行を伴う **DENY→ALLOW** と正当操作の **ALLOW→DENY** を確認しました。pytest・変異は実行しておらず、以下はコード経路と read-only の `decide()` 差分照合による判定です。baseline は [OLD_HEAD.txt:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/OLD_HEAD.txt:1) の `94db52e...` です。

## 所見ごとの対応表

| 一次所見 | 判定 | 根拠 |
|---|---|---|
| A1: `--rcfile` / `--init-file` fail-open | **partial** | 対話 shell の元再現は `_shell_startup_targets()` と全 target 判定で閉じた。[guard_bash.py:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:778)、[guard_bash.py:852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:852)、[test_hooks.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:851)。一方、非対話 `-c` でも無条件に startup target 扱いして新規過剰拒否し、`BASH_ENV` は未検出。元所見は [s6-revA.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revA.md:36)。 |
| A2: executor 閉集合・bundle fail-open | **partial** | 指定された `pydoc` / `doctest` / `unittest` / `trace --module` と複数 path は追加済み。[guard_bash.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:345)、[test_hooks.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:757)。ただし `unittest discover -s`、dotted test name、dotted `pydoc` は実行対象を捕捉しない。元所見は [s6-revA.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revA.md:49)。 |
| A3: 裁定外 DENY→ALLOW | **regressed** | F3 の列挙4件は残余検査で DENY に戻った。[guard_bash.py:983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:983)、[test_hooks.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:831)。しかし、target 後の `--help` / `--report` と `cProfile -o <Pegasus path>` に新しい DENY→ALLOW がある。[guard_bash.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:725)、[guard_bash.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:742)。元所見は [s6-revA.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revA.md:71)。 |
| A4: 正当な非実行操作の過剰拒否 | **regressed** | 元の4例は ALLOW に復帰した。[test_hooks.py:786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:786)。一方、`python -c` の argv、`bash -c` の `$0`、非対話 `--rcfile`、`pydoc -n` を新たに拒否する。元所見は [s6-revA.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revA.md:84)。 |
| B1: M5 の対象 path 不定 | **closed** | M5 は `collect_t126_qualification.py` の exact anchor と、schema・inventory の2 nodeへ固定された。[mutation-spec.json:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/mutation-spec.json:80)。元所見は [s6-revB.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revB.md:59)。 |
| B2: `.pbs` inventory 漏れ | **partial** | 指摘された2本は registry、`.pbs`、shebang、`stat` mode の全てで捕捉・DENY pin 済み。[test_hooks.py:1073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1073)、[test_hooks.py:1146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1146)、[test_hooks.py:1172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1172)。ただし「再帰 execution inventory」は任意 suffix の interpreter/source 入力を取りこぼす。元所見は [s6-revB.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revB.md:66)。 |
| B3: 未列挙 executor の DENY→ALLOW | **partial** | 元再現は修正済みだが、上記 A2 と同じ CLI grammar の閉鎖漏れが残る。[guard_bash.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:705)、[guard_bash.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:742)。元所見は [s6-revB.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revB.md:74)。 |
| B4: 再現不能な「19関数 PASS」 | **closed** | fix 報告は pytest 実走0 node、緑・closed を申告しない、と限定した。19 PASS 主張は残っていない。[s6-fix2.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-fix2.md:49)。元所見は [s6-revB.md:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revB.md:82)。 |

## 新規・残存 real 所見

### R1 — [real] `--help` / `--report` の位置を無視して execution target を消す

- **(a) 根拠:** args のどこかに help があれば即 `()`、`trace` もどこかに `--report` があれば即 `()` を返す。[guard_bash.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:725)。しかし `cProfile` は最初の program 以後を program argv とし、実際に file を compile する。[cProfile.py:139](/usr/lib/python3.10/cProfile.py:139)、[cProfile.py:161](/usr/lib/python3.10/cProfile.py:161)。`trace` も `progname` 後を `REMAINDER` とする。[trace.py:656](/usr/lib/python3.10/trace.py:656)、[trace.py:716](/usr/lib/python3.10/trace.py:716)。
- **(b) 再現:** `python3 -BmcProfile -- tools/pegasus/exec_calibrate.py --help`、`python3 -Bmtrace --trace -- tools/pegasus/exec_calibrate.py --report`。ともに baseline **DENY**、現在 **ALLOW** で、Pegasus target は実行される。
- **(c) 修正:** help/report は module option parsing 中、かつ `--` または最初の program より前に現れた場合だけ非実行 mode とする。target 決定後の token は target argv として扱う。
- **(d) 未修正時:** LOGIN 受理集合へ dispatch-required 実行綴りが2族以上追加され、57件の `mismatch: 0` は維持されたまま site proof のない実行を許す。

### R2 — [real] shell startup 判定が false-positive と false-negative を同時に持つ

- **(a) 根拠:** `_shell_startup_targets()` は shell が対話か否かを見ず `--rcfile` / `--init-file` を常に target 化する。[guard_bash.py:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:778)。反対に、先頭の環境代入は捨てられるため `BASH_ENV` を見ない。[guard_bash.py:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:561)。
- **(b) 再現:** `bash --rcfile tools/pegasus/certify_calibration.sh -c 'true'` は rcfile を読まない非対話形だが baseline ALLOW→現在 DENY。`BASH_ENV=tools/pegasus/certify_calibration.sh bash -c 'true'` は逆に file を実行するが baseline・現在とも ALLOW。
- **(c) 修正:** 明示 `-c` 形では `-i` がある場合だけ CLI startup file を target 化する。先頭代入および `env BASH_ENV=...` は、非対話 bash の execution target として抽出する。
- **(d) 未修正時:** 正当操作1族が受理集合から消えたままになり、別の startup-file 実行族は受理集合に残る。

### R3 — [real] 残余 argv の「全 path は実行体」近似が正当な argv を拒否する

- **(a) 根拠:** module/script 以外では、残余の全非 option token を admission path と照合する。[guard_bash.py:983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:983)。新テスト自身がこの拡大を固定している。[test_hooks.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:831)。レビュー A も単純な `python -c <code> <path>` の baseline は ALLOW と確認している。[s6-revA.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s6-revA.md:32)。
- **(b) 再現:** `python3 -c 'print(1)' tools/pegasus/exec_calibrate.py`、`bash -c 'true' tools/pegasus/certify_calibration.sh`。後者の path は実行体ではなく `$0`。ともに baseline ALLOW→現在 DENY。
- **(c) 修正:** `-c ... -m pytest` のような実際の重量構文だけを再構成し、単なる `sys.argv` / `$0` は実行対象にしない。現行の一律拒否を維持するなら、baseline 不変との矛盾について親の再裁定が必要。
- **(d) 未修正時:** LOGIN 受理集合が少なくとも2族縮小し、fix 報告の「baseline bitへ復帰」という参照が不正確になる。run 値自体は変わらない。

### R4 — [real] executor の実 CLI grammar がなお不完全

- **(a) 根拠:** `unittest` の `-s` は単なる値 optionとして読み捨てられ、dotted name は full name が実在 pathへ写像できた場合しか捕捉しない。[guard_bash.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:356)、[guard_bash.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:742)。実際の unittest は `-s` から discovery して import し、dotted name は最長の import 可能 prefix を順に import する。[unittest/main.py:219](/usr/lib/python3.10/unittest/main.py:219)、[unittest/loader.py:147](/usr/lib/python3.10/unittest/loader.py:147)。pydoc も dotted module/object を受ける。[pydoc.py:2819](/usr/lib/python3.10/pydoc.py:2819)。
- **(b) 再現:** `python3 -Bmunittest discover -s tools/pegasus -p 'collect_receipt.py'`、`python3 -Bmunittest tools.pegasus.exec_calibrate.NoSuchTest`、`python3 -Bmpydoc tools.pegasus.exec_calibrate.main` は現在 ALLOW。
- **(c) 修正:** `unittest discover` の start directory を execution root として分類し、dotted name は既存 module の最長 prefix を repo pathへ写像する。pydoc も同様の prefix resolution を行う。
- **(d) 未修正時:** LOGIN 受理集合に Pegasus module の import/test 実行経路が残り、A2/B3を closed と記録できない。

### R5 — [real] path-valued output option が新しい DENY→ALLOW を作る

- **(a) 根拠:** executor parser は一般の value option とその値を検査せず読み飛ばす。[guard_bash.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:742)。`cProfile -o` はその path を出力先にし、profile 結果を書き込む。[cProfile.py:140](/usr/lib/python3.10/cProfile.py:140)、[cProfile.py:158](/usr/lib/python3.10/cProfile.py:158)、[cProfile.py:179](/usr/lib/python3.10/cProfile.py:179)。
- **(b) 再現:** `python3 -BmcProfile -o tools/pegasus/exec_calibrate.py /tmp/safe.py` は baseline DENY→現在 ALLOW。安全な script 実行後、登録済み Python 実行体を profile binary で上書きできる。
- **(c) 修正:** option を「入力・実行対象」「出力先」「純 selector」に分け、登録 path を出力先にする option は拒否する。少なくとも `cProfile/profile -o|--outfile` の dense/bundle 回帰を追加する。
- **(d) 未修正時:** 57件外の DENY→ALLOW が残り、dispatch-required 実行体の内容を hook が許可したコマンドで変更できる。

### R6 — [real] inventory 保証より広い改悪が赤にならない

- **(a) 根拠:** inventory は `.py/.sh/.pbs`、実行 bit、shebang の和だけである。[test_hooks.py:1158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1158)。runtime target 抽出も Python と `bash/sh/zsh` の script 形だけで、`source` / `.` を扱わない。[guard_bash.py:852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:852)。
- **(b) 赤にならない改悪例:** mode 0644、shebangなしの `tools/pegasus/probes/future_probe.bash` を追加し、registryへ登録しない。inventory test は拾わず、`source tools/pegasus/probes/future_probe.bash` と `bash -lc 'source tools/pegasus/probes/future_probe.bash'` も現在 ALLOW。
- **(c) 修正:** `source` / `.` の operand を execution target 化する。inventory は全 regular fileを載せる、独立 manifest/annotationを設ける、または保証名を「suffix/mode/shebang heuristic」に狭める。
- **(d) 未修正時:** 将来の executable body 追加で meta-test は赤にならず、registry参照も増えないまま LOGIN 受理集合に実行綴りが追加される。

### R7 — [real] 変異仕様が現コードに対して4件無効

- **(a) 根拠:** harness は失敗 node 集合の完全一致だけを `KILLED` とする。[mutation_harness.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/mutation_harness.py:1191)。M1/M3 は新テストによる追加赤を登録せず、M4/M6 は変異が別層にマスクされる。
- **(b) 再現:** M4 は `W/X` を invalid にしても残余検査が同じ DENYを返す。M6 は `_SANCTIONED_PATHS` から local-ok を外しても admission loopが local-okを拒否せず、その後の既定 `None` で ALLOWする。[guard_bash.py:1032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:1032)、[guard_bash.py:1098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:1098)。
- **(c) 修正:** 次節の anchor/node 差し替えを行う。
- **(d) 未修正時:** M1/M3/M6 は `MISMATCH`、M4 は `SURVIVED` と予測され、事前登録の `KILLED` 値・期待 node 参照が成立しない。

なお、次は **疑わしい** です。`python3 -W tools/pegasus/exec_calibrate.py /tmp/safe.py` と `bash -O tools/pegasus/certify_calibration.sh /tmp/safe.sh` は baseline DENY→現在 ALLOWですが、Pegasus path は option 値であり実行対象ではありません。[guard_bash.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:634)、[guard_bash.py:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:824)。コード修正より先に probeへ加えて明示裁定すべきです。未対応なら受理集合には2つの未記録 DENY→ALLOW 族が残りますが、登録 path の実行を許す証拠にはなりません。

## 57 綴りの十分性

**十分ではありません。** [probe_fix_result.json:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_fix_result.json:2) の `mismatches: 0` は列挙した入力に対する事実です。特に、非実行 mode は flag が target より前の例だけです。[probe_fix_result.json:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_fix_result.json:131)

read-only で baseline/current の `decide()` を同一入力へ適用した未検査差分は次のとおりです。

| 未検査綴り | baseline → 現在 | 根拠 |
|---|---:|---|
| `python3 -BmcProfile -- tools/pegasus/exec_calibrate.py --help` | DENY → **ALLOW** | global help 判定 [guard_bash.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:725) |
| `python3 -Bmtrace --trace -- tools/pegasus/exec_calibrate.py --report` | DENY → **ALLOW** | global report 判定 [guard_bash.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:727) |
| `python3 -BmcProfile -o tools/pegasus/exec_calibrate.py /tmp/safe.py` | DENY → **ALLOW** | value option読み飛ばし [guard_bash.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:742) |
| `bash --rcfile tools/pegasus/certify_calibration.sh -c 'true'` | ALLOW → **DENY** | startup targetの無条件追加 [guard_bash.py:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:778) |
| `python3 -c 'print(1)' tools/pegasus/exec_calibrate.py` | ALLOW → **DENY** | 残余全path検査 [guard_bash.py:998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:998) |
| `bash -c 'true' tools/pegasus/certify_calibration.sh` | ALLOW → **DENY** | 同上 |
| `python3 -Bmpydoc -n localhost tools/pegasus/exec_calibrate.py` | ALLOW → **DENY** | pydocの early server modeを未分類。[pydoc.py:2793](/usr/lib/python3.10/pydoc.py:2793) |

57件は F1 を `-i` 形だけ [probe_fix_result.json:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_fix_result.json:5)、F3 を `-c ... -m pytest` だけ [probe_fix_result.json:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_fix_result.json:110)、help/report を target 前だけ [probe_fix_result.json:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_fix_result.json:131) 検査しています。

## M1〜M6 の再検証

old anchor は全6件とも現在のコードに1回存在します。ただし **anchor・意味・期待赤集合まで有効なのは M2 と M5だけ**です。以下は静的予測で、変異実走結果ではありません。

| ID | 判定 | 必要な修正 |
|---|---|---|
| M1 | **無効（期待 node 不足）** | anchor [guard_bash.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:862) は維持。既存期待に `test_bash_login_closes_additional_executor_module_spellings` を追加する。[test_hooks.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:757) |
| M2 | **有効** | anchor [guard_bash.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:889)、期待 `test_bash_login_module_identity_and_borrow_matrix` は成立。[test_hooks.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:727) |
| M3 | **無効（期待 node 不足）** | anchor [guard_bash.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:208) は維持。期待9 nodeに `test_bash_login_closes_additional_executor_module_spellings` を追加する。trace caseは [test_hooks.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:769)。 |
| M4 | **無効（SURVIVED予測）** | 現 anchor [guard_bash.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:634) を、[guard_bash.py:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:650) の `-W/-X` 継続 blockへ差し替える。変異後はその blockを `return "script", value, remaining` とする。期待 nodeは現行の prefix-value testでよい。 |
| M5 | **有効** | exact anchor・schema/inventory 2 nodeとも成立。[mutation-spec.json:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/mutation-spec.json:80) |
| M6 | **無効（MISMATCH予測）** | 現 anchor [guard_bash.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:336) を admission gate [guard_bash.py:1037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:1037) へ差し替え、`if admission is not None and ...` を `if admission is not None:` にする。期待 nodeは registry bit、fetch spellings、sanctioned exactの3本へ変更する。[test_hooks.py:1123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1123)、[test_hooks.py:1194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1194)、[test_hooks.py:1248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1248) |

## 保証と既存テスト

inventory test は production registry から期待集合を生成していないため、狭義には恒真ではありません。`.pbs`、shebang、`stat` mode の修正も実在2本に対して有効です。ただし [test_hooks.py:1147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1147) の「再帰 execution inventory」という保証名は、R6 の `.bash` / `source` 例より広すぎます。

tracked テストの弱体化はありません。

- 現在の `orchestrator/tests/test_hooks.py` は `git show HEAD:...` と byte-identical。
- wave 導入点 `e1c48e20^..e1c48e20` の差分は **+293 / -0**。
- 追加行は新テスト・独立 expected registry・`stat` importで、既存期待値の反転、緩和、skip、削除はありません。
- ただし、新設テストが誤った広い oracleを固定している例はあります。具体的には残余 argv の一律 DENY [test_hooks.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:831) と、順序を検査しない help/report 正例 [test_hooks.py:786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:786) です。

親の「90 passed / 1 skipped」はその実走範囲の事実ですが、上記の未列挙綴りや、変異 harness の期待 node 完全一致を保証しません。本レビューでは pytest を実行しておらず、緑は主張しません。

## 総括

- 8所見の内訳: **closed 2 / partial 4 / regressed 2**
- post-fixで新たに確認した real 所見: **7件**（新規回帰4、閉鎖漏れ2、変異証拠1）
- 疑わしい所見: **1件**（`-W` / `-O` の option-value-only 差分）
- land 判定: **不可**

少なくとも R1 の実行可能な fail-open、R5 の登録実行体上書き、M1/M3/M4/M6 の仕様不成立を修正し、57 probeへ順序・出力 option・非対話 startup・command argv族を追加したうえで、計算ノード上の焦点テストと変異 matrixを再実測する必要があります。