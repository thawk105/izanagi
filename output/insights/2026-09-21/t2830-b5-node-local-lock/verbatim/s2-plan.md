## 1. node-local lock の挿入位置と適用範囲

**P1 を採用する。** 行番号はすべて現行ファイル基準。

`tools/pegasus/p3_s4_loop_pegasus.sh:660–662` の次の位置に、1 行だけ追加する。

```bash
  b5_rc=0
  export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"
  "$PY" -B -m orchestrator.campaign.b5_generator_contrast "${b5_argv[@]}" || b5_rc=$?
  exit "$b5_rc"
```

前アンカーは `  b5_rc=0`、後アンカーは B-5 driver の起動行。`:648` の B-5 分岐内に収め、非 B-5 の `candidate_rc=0` 以下を変更しない。

根拠は以下。

- `:256–263` で job 固有の `/scr/...` を作成し、`TMPDIR` を export 済み。
- B-5 の `series` 全 arm と `block-stock` は、共通の `:661` を通る。
- 親の静的実測では bench lock の取得は driver 内部に限られ、`:576–644` の prebuild は取得しない。したがって、この export は B-5 起動後の取得を覆う。
- `orchestrator/campaign/lock.py:24–34` は取得時に環境変数を参照する。performance verify pass と bench を囲む構造は変更不要。
- 先例は `b10_backoff_grid.sh:280`、`a5_second_boot_backoff_sweep.sh:259` の同一 literal。

job 全体への適用は、非 B-5 の K2 手動 loop も home 共有 lock から分離できる点では利点がある。しかし、今回の対象外である既存 3 経路の環境・挙動まで変えるため採用しない。提示された取得箇所からは、B-5 のために prebuild より前へ移す必要は認められない。

なお、この path は厳密には **node-local な job 固有 path**。同一ノードの別 job と共通の lock になるわけではなく、既存の専有条件を代替しない。

## 2. job ごとの submit-tree を受ける launcher 設計

**P2・P3 を採用する。** 親が準備した 4 本を受け取り、launcher は生成しない。

CLI は固定 4 arm に対応する次の必須引数とする。

```text
--repo-root-random PATH
--repo-root-sweep-matched PATH
--repo-root-llm PATH
--repo-root-stock PATH
--expected-head FULL_OID
```

単一の `--repo-root` による共有への fallback は設けない。反復 `--submit-tree ARM=PATH` より、arm 名の独自 parser や重複・欠落処理を増やさずに済む。共通の third-party source root と既存の予算・workload 制約は維持する。

変更箇所は `tools/pegasus/b5_contrast_launch.py` の以下。

| 箇所 | 実装方針 |
|---|---|
| `SubmitTree:29–33` | 変更不要。検証済み 1 checkout を表す。 |
| `validate_submit_tree:78–108` | keyword-only の `previous_trees=()` を追加。既存検査後、正規化済み `repo` の重複と `common_repo` の不一致を、それまでの結果と比較する。 |
| `pilot_jobs:150–162` | 変更不要。job の実験条件と tree の配置を分離する。 |
| `build_job_environment:173–201` | 変更不要。各 job に対応する `SubmitTree` を渡す。 |
| `qsub_argv:204–205` | 変更不要。単一 job と単一 tree の関数を維持する。 |
| `_qsub_argv:208–214` | 変更不要。環境変数の順序、walltime、相対 `JOB_BODY` を維持する。 |
| `launch:217–241` | 単一 tree 引数を arm→path の mapping に変更。共通 `expected_head` と `thirdparty_source_root` を keyword 引数で受け、最初に全 4 本を既存 validator で順番に検証する。 |
| `main:244–268` | `:246` を 4 必須引数へ置換。`:260–265` の単一 tree 検証を、mapping を組んで `launch` に渡す形へ変更する。 |

`launch` 内では、既存 `validate_pilot_cap(jobs)` の後に `PILOT_ARMS` 順で次を行う。

1. 同じ `expected_head` で `validate_submit_tree(path, expected_head, previous_trees=...)` を反復する。
2. 返された tree に既存の `replace(..., thirdparty_source_root=...)` を適用する。
3. 全 tree の検証完了後、`(job, tree, env, argv)` を組み立てる。
4. 全 job の環境と既存の出力先 freshness を検査してから、副作用へ進む。

**現行 validator を無変更で 4 回呼ぶだけでは、path 重複・common repo 不一致は検出できない。** 上記はその関係比較を既存 validator 内に収める設計であり、独立 gate・検査コマンド・台帳は作らない。同じ HEAD は既存 `:90–91` に共通 OID を渡すことで検査する。

`:238` の呼び出しは、各 command に保持した tree を使う。

```python
result = runner(argv, cwd=tree.repo)
```

最後に検証した tree や先頭 tree を使い回さない。相対 `JOB_BODY` と `IZANAGI_S4_REPO_ROOT` が同じ checkout を指すことを test で固定する。

選択の根拠：

- `p3_s4_loop.py:3428–3444` は、隔離時にも cache を submit-tree の `external/ccbench/build-variants` に置く。
- `patchharness.py:362–364` の一時 worktree は source を隔離するが、この cache root は分離しない。
- `buildcache.py:2222–2231` は既存 claim に対して待機・retry を行わず失敗する。`:2800–2813` には claim 後の公開競合でも失敗する経路がある。
- 共有 tree の事前検査が成功しても、後から発生する同時 claim を防げない。試走で落ちなかった事実も一般保証ではない。

4 本へ分ければ、この **job 間の共有 cache に由来する競合**を構造的に除ける。親が確認した配置では CCBench の git dir も worktree ごとに独立している。ただし、既存 cache の stale claim など、別の失敗原因まで解消するとはしない。`p3_s4_loop.py`、`patchharness.py`、`buildcache.py` は編集しない。

## 3. 既存 3 経路の driver argv bytes 固定

対象は `orchestrator/tests/test_p3_s4_loop_job_contract.py`。

既に以下で全 argv の順序付き比較があるため、同じケースの新規 test は増やさない。

- `test_default_job_invokes_driver_once:1894`：proposal 単独・fixture、stock 未設定／`0`。
- `test_pair_job_invokes_one_driver_with_both_modes:1915`：proposal＋pair。
- `test_complete_k2_environment_reaches_actual_job_driver_argv:1416`：空白を含む manifest を含めた K2 argv。

不足する bytes 固定だけを、前二者へ追加する。`:1298–1300` の fake driver で、既存 JSON history に加えて `args` を次の形式で別ファイルへ記録する。

```python
b"\0".join(os.fsencode(arg) for arg in args) + b"\0"
```

既存の「起動回数 1」アサートを維持し、実測 bytes を独立した期待値と比較する。共通 literal は次のとおり。

```python
b"-B\0-m\0orchestrator.campaign.p3_s4_loop\0"
b"--allow-coder-derived-build\0--isolate-worktree\0"
b"--fetchcontent-prebuild-receipt\0"
```

続けて receipt path の bytes と NUL、必要な K2 引数、最後に以下を連結する。

| 経路 | 末尾 literal |
|---|---|
| proposal 単独 | `b"--run-iteration\0/absolute/proposal.json\0"` |
| proposal＋pair | `b"--stock-control\0--run-iteration\0/absolute/proposal.json\0"` |
| fixture | `b"--value\0" b"20\0"` |

期待値は記録された history から生成せず、既存の固定期待値から作る。fake interpreter 自体の可変 path は対象外とし、既存 harness と同じ `-B` 以降を固定する。

## 4. driver が観測する lock 環境の test

`_run_actual_job_body_through_driver:1219` は拡張可能。戻り値 3 要素は維持する。

- `:1302–1305` の fake driver evidence に、`TMPDIR`、`IZANAGI_BENCH_LOCK` の存在有無と値を追加する。
- `:1391–1397` の辞書全体比較は、既存 3 field の比較に変更する。追加 field は呼び出し側 test が検査する。
- `:1354–1366` の harness 環境初期化で `IZANAGI_BENCH_LOCK` を除去し、その後の入力環境で明示的に注入できるようにする。これは test の汚染防止であり、job body に `unset` は追加しない。

既存 test の拡張内容：

| test | 追加するアサート |
|---|---|
| `test_b5_actual_shell_one_driver_and_trap_rc:2016` | 全 4 arm・rc `0/7` で lock が存在し、`str(tmp_path / "scratch-base/0_945411.nqsv/bench.lock")` と一致する。`TMPDIR` もその親 path と一致する。 |
| `test_default_job_invokes_driver_once:1894` | proposal／fixture／K2、stock 未設定／`0` で lock が環境に存在しない。 |
| `test_pair_job_invokes_one_driver_with_both_modes:1915` | pair でも lock が環境に存在しない。 |

さらに、入力に `/inherited/bench.lock` を与える小さい parameterized test `test_job_preserves_or_overrides_inherited_bench_lock` を追加する。B-5 は scratch path へ上書きし、非 B-5 は入力値を保持する。

「非 B-5 では設定されない」は、**未設定入力を job が新たに設定しない**という意味に固定する。既存挙動を守るため、継承された値を消す契約にはしない。

この harness が検査するのは shell→fake driver の環境伝播まで。実際の flock 取得や性能改善は、この test の確認範囲に含めない。

## 5. 既存 pin と更新方法

| 対象 | 更新方法 |
|---|---|
| `_assert_static_job_stage_order:581–618` | `b5_argv=("run-$b5_mode")` と B-5 driver の間に `export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を追加。実行面で出現回数 1・順序を検査する。 |
| `B5_PINS:79–102` | `"b5-node-local-lock"` と上記 export literal を追加。`:1969` の変異 test が削除を既存形式で検出する。 |
| harness のアンカー `:1330–1335` | bootstrap PATH、SANITIZED_PATH、scratch_base は変更不要。置換回数 1 の検査を維持する。 |
| B-5 分岐アンカー `:2145` | `if [[ -n "$b5_mode" ]]; then\n  b5_argv=` を維持する。export を driver 直前に置けば更新不要。 |
| fake driver evidence `:1303–1304`／`:1393–1397` | §4 の観測 field 追加に対応。既存 root/cwd のアサートは残す。 |
| `test_four_qsub_argv_and_explicit_environment_are_exact:132` | `_pilot:95` を arm 別 tree に対応させ、`_expected_environment:106` の repo root を `submit-tree-<arm>` に変更。残りの literal と `-v` の順序は維持する。 |
| `test_main_dry_run_validates_tree_and_prints_four_jobs:243` | 4 CLI 引数を渡す。validator spy は arm 順の 4 呼び出し、共通 HEAD、previous trees を確認。出力 4 件の環境・argv も比較する。 |
| `test_submit_only_mkdir_then_argv_runner:220` | fake runner が `(argv, cwd)` を記録し、arm ごとの tree と照合。rc 非零で後続を呼ばない既存検査を維持する。 |
| dry-run／freshness 関連 test | `launch` の新しい引数に追従。dry-run では validator の read-only git 呼び出しと scheduler runner を区別する。 |

validator の test は既存単一-tree fixture を維持し、関係比較用に同じ superproject の 4 worktree fixture を追加する。各 CCBench は独立 checkout にし、同一 HEAD・別 path・共通 repo の成功例、重複 path・異なる HEAD・異なる common repo の負例を検査する。4 本目の検証失敗が mkdir／runner より前であることも固定する。

`STOCK_PINS` と D2205 の pair 1 起動・rc 伝播・結合検査は維持する。親の調査では job body／launcher の SHA に repo 内 literal pin はない。過去の `reservation.json` は書き換えず、将来の job 内自己照合が新しい job body の SHA を記録する構造を維持する。

## 6. 変異負例候補

以下は **実行前の候補と期待する失敗先**。この段では KILLED と判定しない。

| 変異する行・操作 | 落ちるべき test |
|---|---|
| 追加した export 行を削除 | `test_b5_fragment_mutants_have_one_static_failure[b5-node-local-lock]`、B-5 環境観測 |
| 値を `"$HOME/.izanagi/bench.lock"` に変更 | `test_b5_actual_shell_one_driver_and_trap_rc` の exact path |
| export 行を B-5 分岐の外へ移動 | default／pair test の「lock 不在」 |
| `export` を削り shell 変数の代入だけにする | B-5 fake driver の環境観測 |
| 値を `"$TMPDIR/other.lock"` に変更 | B-5 exact path |
| `tree = trees[job.arm]` を `tree = trees["random"]` に変更 | dry-run の全 4 件環境・argv 比較、runner の cwd 比較 |
| `runner(..., cwd=tree.repo)` を先頭 tree の cwd に変更 | `test_submit_only_mkdir_then_argv_runner` |
| validator の重複 repo 拒否条件を無効化 | `test_validate_submit_tree_rejects_reused_repo` |
| validator の common repo 比較を無効化 | `test_validate_submit_tree_rejects_different_common_repo` |
| `pair_argv=(--stock-control)` を空配列に変更 | `test_pair_job_invokes_one_driver_with_both_modes` の argv bytes |
| fixture default の `20` を `21` に変更 | `test_default_job_invokes_driver_once` の fixture bytes |

変異適用前に対象 literal の出現回数を検査し、環境観測系では `source_override` を使って実際の shell 分岐を通す。静的 marker の失敗だけで、環境伝播や tree 対応の負例を代用しない。

## 総括

- P1 採用：B-5 driver 直前だけで lock path を export する。
- P2・P3 採用：親が用意する 4 tree を既存 validator の反復で扱い、job ごとの cwd を保持する。
- 既存 3 経路の argv test を拡張し、bytes と lock 環境の不足分を固定する。
- campaign 実装・認可条件・試走記録は変更せず、本走の対象範囲や予算も広げない。
- 静的読解のみ実施。ファイル変更、テスト実走、変異判定、計測、投入は未実施。