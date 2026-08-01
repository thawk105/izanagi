# 段 2 実装プラン

## provisional 裁定の評価

| 裁定 | 判断 | 理由 |
|---|---|---|
| P1 | 採用 | 現ノードで再現しなくても、`tools/pegasus/dispatch_compute.py:491-492` は検証済み実体ではなく親 directory しか束縛していない。親 brief `:34-36` の構造的欠陥は成立する。 |
| P2 | 採用 | `_job_script` の bash 本体 `:356-410` は裸の `python3` を起動せず、`:392` と `:409` で `$resolved` / `$selected` を直接実行する。shim は `_job_run` の子環境だけに必要。 |
| P3 | **一部棄却** | submission dir 配下は採るが、canonical binary への symlink は採らない。引数を追加しない透明 wrapper のほうが `sys.executable` と venv の `sys.prefix` を選定時と同じに保てる。 |
| P4 | 採用 | fail-closed 追加で受理集合が変わるため、軽量版にしない。 |
| P5 | 採用・具体化を修正 | fake `python3.10` は symlink でなく実 interpreter のコピーにする。symlinkでは現行の `.resolve().parent` が実 interpreter dir に戻り、現行コードでも誤って通り得る。 |

## 1. shim の名前と consumer 実測

tracked・非 test・非 docs/output を対象に grep した結果は次のとおり。

- shell の実コマンド位置: 裸の `python3` が **46 箇所**。うち `tools/pegasus/*.sh` が45箇所、`.devcontainer/post-create.sh` が1箇所。
- Python の実 argv consumer: **3 箇所**。`tools/task_run_check.py:16,18,20` の `subprocess.call()` 入力で、実消費は同 `:52-64`。
- `#!/usr/bin/env python3` の実行候補: 非 test Python に **50 ファイル**。
- 同じ検索条件で裸の `python` と `python3.10` の shell command / shebang はともに **0箇所**。
- `tools/pegasus/dispatch_compute.py:122-126` の `python3.10` と `orchestrator/qualification/submission.py:107` の各名前は選定候補であり、孫プロセスの command consumer ではない。

したがって `python3` だけを張る。`python` を張ると Python 2 等を意図した将来の呼出しまで変更し、`python3.10` を張ると版付き明示を不必要に上書きする。いずれも現 consumer の根拠がない。

## 2. 実装位置と PATH 配線

### 定数・helper

- `tools/pegasus/dispatch_compute.py:10-22`
  - 実 PATH 解決確認用に `shutil` を追加する。
- 同 `:38-41`
  - `_INTERPRETER_SHIM_DIR_NAME = "interpreter-shim"`
  - `_INTERPRETER_SHIM_NAME = "python3"`
  を追加する。
- 同 `:445-452`、`_import_probe_modules()` と `_job_run()` の間
  - `_create_interpreter_shim(submission_dir, selected)` を追加する。
  - `_verify_interpreter_shim(shim_dir, selected, environ)` を追加する。

`_create_interpreter_shim()` は次を行う。

1. `sys.executable` の絶対パスを、symlink を潰さない選定時パスとして保持する。
2. `resolve(strict=True)` した canonical path は同一実体検査専用にする。
3. `<submission_dir>/interpreter-shim` を `mode=0700`、`exist_ok=False` で作る。
4. `_write_text_x(..., mode=0500)` により `python3` だけを create-only で作る。
5. wrapper 本文を次の2行に固定し、追加 flag や環境操作を入れない。

```sh
#!/bin/sh
exec '<選定時の sys.executable>' "$@"
```

6. `shlex.quote()` で target を引用し、shim dir と submission dir を `_fsync_dir()` する。

### `_job_run()` への配置

`tools/pegasus/dispatch_compute.py:452-519` を次の順序にする。

1. 現行の `_job_run` 版数 gate `:462-463` を維持する。
2. request/task/import gate `:465-471`、入力検査 `:473-481`、hostname gate `:482-484` も先に完了させる。
3. 現行どおり `child_env` を構築し task-run 環境を除去する `:485-490`。
4. `stage = "interpreter-shim"` を設定する。
5. shim を作成し、PATH を次の順にする。

```text
<submission>/interpreter-shim
:<Path(sys.executable).resolve().parent>
:<従来の PATH>
```

既存の interpreter directory は shim の直後に残し、Python 以外の tool 解決を変えない。

6. `shutil.which("python3", path=child_env["PATH"])` が shim leaf そのものを返すことを検査する。
7. shim 経由で内部 identity probeを `python3 -I -S -B -c ...` として起動し、その `sys.executable` の canonical path が現在の検証済み interpreter と一致することを検査する。不一致・非ゼロ・timeout・非構造出力は `DispatchError`。
8. identity の一致が、既存の版数 gate を通過した同一実体への束縛を証明する。ここに新しい代替版数 gateは置かず、既存二層の意味を変えない。
9. 全検査後だけ現行 `:493` の `stage = "child"` に進み、`:494-498` の子を起動する。

## 3. wrapper を採る理由

symlink と透明 wrapper はどちらも通常の argv を渡せるが、Python の実行意味論は同一ではない。

- symlink 経由では `sys.executable` が shim path になる。Python 3.10 の `site` は `sys.executable` 周辺の `pyvenv.cfg` から `sys.prefix` を決めるため、venv 外の submission dir に置いた symlink は、probeを通した venv interpreter の prefix/site-packages を失わせ得る。
- wrapper は選定時の `sys.executable` を `exec` するため、raw `sys.executable`、canonical executable、`sys.prefix`、`sys.base_prefix` を直接起動時と同じに保つ。
- wrapper 自身は `-I`、`-S`、`-B`、`-E` を追加しない。`"$@"` で呼出し側の順序をそのまま渡す。
- 呼出し側の `-I` は従来どおり `-E` 相当を含み `PYTHONHOME` を無視し、`-S` は従来どおり `site` 初期化を止める。`-B` は bytecode 書込みだけを抑える。
- `-E` がない呼出しでは `PYTHONHOME` を従来どおり interpreter に渡す。wrapper が unset したり暗黙に `-E` を足したりしない。
- 内部 identity probe の `-I -S -B` は site 出力や環境依存を排した同一実体確認専用であり、実 consumer の argv には混入しない。

wrapper は `/bin/sh` と共有 FS の execute 可否に依存するが、identity probeで子起動前に実行可能性まで fail-closed に検査できる。

## 4. shim dir の配置

| 観点 | submission dir 配下 | node-local tmp |
|---|---|---|
| 共有 FS | job script が marker を書ける既証明の場所で、親から監査可能 | login側から見えず、`$TMPDIR` の存在・mount条件も別契約 |
| 権限 | submission dir は `tools/pegasus/dispatch_compute.py:1000-1001` で `0700`。専用dirも `0700`、leafは create-only `0500` にできる | owner/mode/symlink/noexecを別途検証する必要がある |
| 後始末 | submission artifact として残すため cleanup 不要。数十byteの固定成果物 | 正常時 cleanup と crash残骸の扱いが必要で、証拠も消える |
| 再入 | 既存 shim dir を検出して rc=16。別ノードで古い target を再利用しない | 新しい tmp dir が再入を隠し、同じ submission の二重実行を検出しにくい |

submission dir 配下を採用する。同じ submission dir の再入は、既存の `result.json` create-only `:515-518` と同様に未対応として明示的に拒否し、既存 wrapper の再利用・上書きはしない。

## 5. 失敗時の契約

- bash候補全滅は現行どおり `tools/pegasus/dispatch_compute.py:397-399` の `stage="interpreter"`、rc=16。
- Python側の shim dir作成、wrapper作成、PATH解決、identity probe の各失敗は `stage="interpreter-shim"`、`child_rc=16`。
- `stage` は新処理の直前に設定し、現行例外処理 `:499-502` で `"child-launch"` に変換されない位置に置く。
- `result.json` は現行 payload `:506-516` に `"interpreter-shim"` と具体的 error を記録する。submission dir 自体が書込不能なら結果も書けないため、`:517-519` の rc=16と親の成果物欠落検査へ委ねる。
- 親は現行 `:1322-1331` で `stage != "child"` を bootstrap failure とし、`:1361-1406` から rc=16を返す。schema bumpや特別な成功扱いは追加しない。
- 作成・検査失敗時に従来の executable-dir PATHへ fallbackしてはならない。

配置は bash probe → `_job_run` 版数 gate → task import gate → shim作成・同一実体検査 → child起動となり、既存の二層版数 gateを置換しない。

## 6. `_job_script` の変更要否

変更しない。

`tools/pegasus/dispatch_compute.py:356-410` に対する `python` / `python3` grep は該当0件だった。候補名は `:355` で埋め込まれるが、bashは `:392` で `"$resolved"`、`:409` で `"$selected"` を直接実行する。現行の `export PATH="$(dirname "$selected"):$PATH"` `:407` も維持し、Python側でその前へ shim dirを追加する。

したがって `orchestrator/tests/test_pegasus_dispatch_compute.py:790-812` の逐語 assert、特に `:808` は変更せず残す。

## 7. テスト変更

追加先は `orchestrator/tests/test_pegasus_dispatch_compute.py:875-928` の interpreter 群を中心とする。

| nodeid | 検査内容・殺す欠陥 |
|---|---|
| `test_job_run_binds_bare_python3_to_selected_interpreter_with_conflicting_sibling` | `fake-bin/python3.10` に `sys.executable` の実体をコピーし、同じdirの `python3` は `{version:[3,9], executable:"old-python3"}` を書くfakeにする。選定コピーで `_job_run` を起動し、孫の裸 `python3` が書いたJSONを `assert observed == {"executable": str(selected.resolve()), "version": list(sys.version_info[:2])}` で固定する。現行は古い sibling を選ぶためこの assert が不合格、修正後の合格条件は選定実体との完全一致。 |
| `test_interpreter_shim_wrapper_preserves_direct_python_semantics[...]` | 一時venvの直接起動とshim起動を `-I -B`、`-I -S -B`、`-E -B`、および無効 `PYTHONHOME` + `-B` で比較する。`sys.executable`、`sys.prefix`、`sys.base_prefix`、`sys.flags`、rcを一致させ、symlink化、flag注入/脱落、`PYTHONHOME`の強制unsetを殺す。 |
| `test_job_run_interpreter_shim_creation_failure_is_fail_closed` | wrapper書込みへ `PermissionError` を注入し、rc=16、子未起動、`result.stage=="interpreter-shim"`、error保持を検査する。fallbackや例外握り潰しを殺す。 |
| `test_job_run_interpreter_shim_resolution_mismatch_is_fail_closed` | identity probeに別 executableを返させ、rc=16、子未起動、同 stageを検査する。`which`だけで済ませる変異や不一致無視を殺す。 |
| `test_interpreter_shim_reentry_is_create_only` | 同じ submission dirへ2回作成し、2回目が既存 bytesを変更せず拒否されることを検査する。`exist_ok=True`、再利用、上書きを殺す。 |
| `test_interpreter_shim_stage_failure_is_preserved_by_parent` | `_Scheduler(stage="interpreter-shim", child_rc=16)` を親収集へ渡し、receiptにstageが残り outcomeがinfraになることを固定する。 |

### 既存テストの更新・維持

- `test_job_script_binds_interpreter_path_repo_and_no_network_bootstrap` `:790-812`
  - **更新不要**。`:808` の `export PATH=...` assertを維持する。
- `_job_run_with_mocked_child` `:1379-1394`
  - 新helperをmockして既知のshim dirを返し、task選択だけを検査する既存責務を維持する。
  - 子へ渡す `PATH.split(os.pathsep)[0]` がそのshim dirであるassertを追加する。
- このhelperを使う次のnodeidは期待値を更新する。
  - `test_job_run_accepts_v1_request_as_tests_task`
  - `test_job_run_launches_task_specific_child_script[tests-run_tests.py]`
  - `test_job_run_launches_task_specific_child_script[provenance-check_ai_provenance.py]`
- `test_m5_dual_layer_interpreter_rejection_changes_acceptance_only_together` `:875-915` は変更しない。shim identity検査を代替の版数 gateにせず、既存二層を同時に外した変異が引き続きこのnodeで検出されるようにする。
- `test_interpreter_stage_failure_is_fail_closed_and_preserved_in_receipt` `:917-927` と `test_provenance_probe_omits_pytest_and_xdist_imports` `:1475-1488` も維持する。

## 8. 変異事前登録候補

| 変異内容 | 期待赤 nodeid | 受理集合・fail-closedへの影響 |
|---|---|---|
| child PATHからshim dir先頭を削り、現行 executable dir先頭へ戻す | `test_job_run_binds_bare_python3_to_selected_interpreter_with_conflicting_sibling` | 古い sibling `python3` を再び受理し、未検証 interpreterで孫を動かす。 |
| 透明wrapperを canonical binaryへのsymlinkへ置換する | `test_interpreter_shim_wrapper_preserves_direct_python_semantics[isolated]` | venvのraw `sys.executable` / `sys.prefix`意味論を変え、従来受理できた環境を別環境として起動する。 |
| 作成例外を捕捉して従来PATHへfallbackする | `test_job_run_interpreter_shim_creation_failure_is_fail_closed` | 「shim作成不能なら拒否」の集合を再び受理へ広げる。 |
| identity probeの不一致判定を削除または警告化する | `test_job_run_interpreter_shim_resolution_mismatch_is_fail_closed` | PATH上の名前だけで誤実体を受理し、束縛が恒真化する。 |
| `mkdir(exist_ok=True)` と既存wrapper再利用を許す | `test_interpreter_shim_reentry_is_create_only` | 別entry・別ノードが残したstale targetを受理し、作成不能時のfail-closedを失う。 |

実走はしていない。実装後は対象nodeを `tools/run_tests.py` 経由でPegasus計算ノードへ投入し、その後に関連スイート、`check_codex_agents.py`、`check_docs.py`、親の受入全走を行う。

## 総括

- submission dir配下に、`python3`だけを提供するcreate-onlyの透明wrapper shimを置く。
- wrapperは選定時の`sys.executable`をflag追加なしで`exec`し、symlink由来のprefix変化を避ける。
- `_job_run`の既存版数/import gate後、child起動前にPATH解決と同一実体を検査する。
- 作成不能・不一致・再入は`stage="interpreter-shim"`、rc=16でfail-closedにする。