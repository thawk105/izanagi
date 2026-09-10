静的レビューでは must-fix 5 件、裁定へ戻すべき誤記 1 件、nit 1 件を確認した。pytest は実行していない。`1644 passed / 5 skipped` は親の実測であり、このレビュー自身の緑判定ではない。

## 1. 公開 `--job-run` は job script 束縛を自己申告で迂回できる

- **所見**: 3 引数形では呼び出し側が任意 request の hash を自分で渡せるため、`sha256-job-script/v1` は job script 由来の証拠にならず、二重 bnode gate も 1 層になる。

- **なぜ real か**: `tools/pegasus/dispatch_compute.py:3691-3699` は任意の第 3 引数を `_job_run` へ渡し、同 `:844-858` は hash の形式と request bytes との一致しか検査しない。`request_binding`、`dispatch.sh`、`PBS_JOBID` はこの分岐で要求されず、`PBS_JOBID` 不在は同 `:830` で単に `"unknown"` になる。子起動前の残る gate は同 `:880-907` の hostname だけである。これは裁定 `s4-adjudication.md:132-137` と runbook `:574-575` の二重 gate 契約に反する。

- **壊れ方**: `bnode114` 上で `PBS_JOBID` を持たない process が、`task=generic`、`args=["/bin/sh","-c","任意コマンド"]` の request を作り、その bytes の SHA-256 を第 3 引数にして `--job-run` を呼ぶと、job script を一度も経ずに任意 argv が起動する。

- **重大度**: 正しさ防壁

- **成果物影響**: `result.request_sha256` が「job script に埋め込まれた hash」ではなく「呼び出し側が選んだ hash」でも成立するため、request 束縛の参照値と `sha256-job-script/v1` の意味が偽になる。

- **提案**: 公開 3 引数形を削除し、新規 request は `request_binding == _REQUEST_BINDING`、実在する bound `dispatch.sh` envelope、正規の `PBS_JOBID` を同時に要求する。直接 bnode 起動も仕様として許すなら、「二重 gate」「job-script 束縛」を裁定し直す必要がある。なお通常の `pegasus0N` login は hostname gate で拒否され、login 直実行までは破れなかった。

## 2. argv policy は Pytest の短 option cluster と `@argfile` で迂回できる

- **所見**: 両側 validator は同じ実装を通るが、Pytest が後段で展開する別表記を正規化していないため、二層とも同じ入力を許可する。

- **なぜ real か**: `tools/pegasus/dispatch_compute.py:761-778` は各 token の先頭だけを見る。`tools/run_tests.py:562-572` は user argv を末尾へそのまま渡す。現環境の Pytest parser は `_pytest/config/argparsing.py:390-397` で `fromfile_prefix_chars="@"` を有効化しており、Python parser は `/usr/lib/python3.10/argparse.py:1964-2006` で `-qkselected` のような短 option cluster を分解する。

- **壊れ方**: mutation runner argv に `-rf -qkselected` を渡すと、validator は `-qkselected` が `-k` で始まらないため許可するが、Pytest は `-q -k selected` と解釈する。また `@/tmp/options` の内容を `-k selected` や `-p foreign_plugin` にすれば、validator が一度も禁止 token を見ずに選択集合や plugin を変えられる。`-k=x`、`--ignore-glob`、先頭の `-pno:...` 自体は現実装で拒否できているが、cluster 内は漏れる。

- **重大度**: 正しさ防壁

- **成果物影響**: collection、baseline、mutation が裁定した test file 集合ではなく部分集合や外部 plugin 付きで走り、期待 node、KILLED/SURVIVED、ledger 集計値が変わる。

- **提案**: Pytest と同じ字句規則で検査するか、より小さい閉じた runner argv grammar を定義する。少なくとも `@argfile`、`-qk...`、`-qm...`、`-qp...`、代替 config/addopts 注入を拒否し、それぞれを親側と forged `_job_run` 側の両方で負例にする。

## 3. `check_docs.py` の subtree alias 検査は comprehension を通す

- **所見**: 「RHS subtree に `TASKS` load を含む alias 束縛を拒否する」という裁定は、`ListComp`、`SetComp`、`DictComp`、`GeneratorExp` では成立しない。

- **なぜ real か**: `tools/check_docs.py:3343-3398` の `preserves_tasks_alias` は comprehension node を扱わず `False` に落とす。assignment の拒否は同 `:3414-3418` でこの戻り値に依存する。追加テスト `orchestrator/tests/test_check_docs.py:2566-2591` は tuple、dict/subscript、function default だけである。

- **壊れ方**: 次は静的検査を通るが、runtime では `TASKS` 本体へ `extra` を追加する。

  ```python
  alias = [value for value in (TASKS,)][0]
  alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))
  ```

- **重大度**: 実効性

- **成果物影響**: runbook の exact task 表は旧集合のまま、runtime の dispatcher 受理集合だけが増えるため、inventory 同期結果が偽陰性になる。

- **提案**: comprehension と generator の element、iterator、条件式をたどる taint 判定を追加し、上記 4 node 種を負例で固定する。

## 4. 裁定済み DW-M07 条件が正本へ反映されていない

- **所見**: runner 実行経路を含む変異では bundled 経路を使わないという条件が、指定された `DW-M07` 正本に追加されていない。

- **なぜ real か**: 裁定は `s4-adjudication.md:93-101` で DW-M07 への追記を明示するが、`docs/dev-wave/mutation.md:43-54` は HEAD と不変で、新条件がない。runbook `docs/pegasus-runbook.md:579-582` だけが条件を述べながら DW-M07 を参照している。

- **壊れ方**: DW-M07 だけを読んだ後続 wave が `tools/run_tests.py` または `dispatch_compute.py` を変異対象にした bundled local 走行を選び、収集段を自壊させて `rc=16` にする。

- **重大度**: 正しさ防壁

- **成果物影響**: infrastructure failure を mutation 判定として扱う危険が生じ、ledger の KILLED/SURVIVED と queue 削減値が正規経路の参照値でなくなる。

- **提案**: 裁定の逐語条件を `DW-M07` に追加し、runbook から同じ正本を参照させる。

## 5. 裁定修正 A-1 の「受理集合は同じ」は end-to-end では誤り

- **所見**: hook 単体の判定集合は同じだが、gateway 全体の実効受理集合は `generic` 追加によって明確に広がる。

- **なぜ real か**: hook は sanctioned path を内側 task と無関係に許可する `hooks/guard_bash.py:1212-1230`。一方、HEAD の task 集合は `HEAD:tools/pegasus/dispatch_compute.py:110-135` の `{tests, provenance}` だけで、working tree は `tools/pegasus/dispatch_compute.py:112-158` に `generic` を追加し、CLI choices は同 `:3726-3737` からその集合を受理する。A-1 の主張は `s4-adjudication-amendment.md:18-27` にある。

- **壊れ方**: `dispatch_compute.py --task generic -- pytest -q` は wave 前には hook を通った後 argparse で拒否され、wave 後には qsub される。同一入力の最終結果が「拒否」から「compute 実行」へ変わる。

- **重大度**: 受理集合

- **成果物影響**: D103/D895 の acceptance reference に、新たに実行可能になった `generic` gateway が記録されず、「受理集合不変」という decision 値が事実と食い違う。

- **提案**: A-1 を「hook 単体の受理集合は不変だが、end-to-end は D895 により意図的に拡張された」と修正する。hook の exact task 境界化は引き続き裁定待ちとして分離する。

## 6. legacy v1 正例テストが凍結集合自身を fixture にしている

- **所見**: v1 の全 4 キーを守るはずの正例が実装中の集合から入力を生成するため、2 キーを削っても赤にならない。

- **なぜ real か**: `orchestrator/tests/test_pegasus_dispatch_compute.py:4052-4056` は `DC._LEGACY_V1_ENV_ALLOWLIST` をそのまま列挙する。別の v1 テスト `:4699-4714` が literal に固定するのは `PYTEST_ADDOPTS` と `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS` だけである。拒否は `tools/pegasus/dispatch_compute.py:869-879` で凍結集合に依存する。

- **壊れ方**: `_LEGACY_V1_ENV_ALLOWLIST` から `IZANAGI_TEST_NPROC` または `IZANAGI_TEST_TRIGGER` を削除すると、動的 payload から同じキーも消えるため追加テストは緑のままになるが、そのキーを持つ歴史的 v1 request は `rc=16` になる。

- **重大度**: 実効性

- **成果物影響**: v1 の歴史的受理集合が 4 キーから 3 キー以下へ縮んでも検出できず、互換性台帳の frozen acceptance 値が変わる。

- **提案**: `_LEGACY_V1_ENV_ALLOWLIST == frozenset({...4 literal keys...})` を直接固定し、4 キーすべてを literal payload に入れた unbound v1 envelope テストを追加する。

## 7. hook 回帰テストが揮発する日本語診断を固定している

- **所見**: 拒否という契約に加えて人向け診断文まで固定しており、等価な文言変更で無関係に赤になる。

- **なぜ real か**: `orchestrator/tests/test_hooks.py:4007-4013` は `not ok` に加え `"interpreter argv の python3 -m pytest"` の包含を要求する。

- **壊れ方**: hook が同じ command を同じ理由で拒否したまま診断文だけ整理すると、このテストだけ失敗する。

- **重大度**: nit

- **成果物影響**: DW-G05 上の台帳、受理集合、参照値への影響は書けないため nit/backlog。

- **提案**: `not ok` だけを pin するか、機械安定な reason code を導入してそれを検査する。

## 総括

### (a) must-fix

- 公開 `--job-run` の自己申告 hash と job-script gate 迂回。
- Pytest の短 option cluster、`@argfile` などによる argv policy 迂回。
- comprehension 経由で通る `TASKS` alias。
- DW-M07 正本への裁定条件の未反映。
- legacy v1 4 キーを literal に固定しない恒真寄りテスト。

### (b) 裁定へ返すべきもの

- A-1 の「受理集合不変」は hook 単体にだけ限定し、end-to-end の D895 拡張を明記するべき。
- bnode 上の公開直 `--job-run` を許す意図があるなら、二重 gate と job-script 束縛の契約そのものを再裁定する必要がある。

### (c) 攻撃したが破れなかった箇所

- 正規の親経路は `tools/pegasus/dispatch_compute.py:2681-2685` で同じ task allowlist から request env を作るため、現行 tests/provenance request に全キー強制による過剰拒否は見つからなかった。
- Git 履歴上、v1 request 生成元は `a34266d2` の `dispatch_compute.py` だけで、`fee55899` の v2 化まで内容差分はなく、歴史的 v1 overlay は 4 キーで覆えている。
- 正規の queued request は job script 埋め込み hashと子側照合で task/argv 差し替えを拒否し、pre-binding tests/provenance envelope には互換分岐がある。通常経路の一方向 bump は見つからなかった。
- 非 bnode hostname、hostname 取得失敗、通常の Pegasus login では `_job_run` が子起動前に止まり、login で generic argv を直接起動する経路は見つからなかった。
- 親側と `_job_run` 側は実際に同じ argv validator を呼ぶ。欠陥は層の欠落ではなく、両層共通の字句集合不足である。
- snapshot から削除された 11 hook node はすべて本 wave で追加された未実装 hook 境界の期待値であり、hook 変更と無関係な既存 node の削除はなかった。現行の無境界挙動を pin する代替テストも残っている。
- mutation harness/worktree の login、suspect local 拒否と、OTHER、compute の既存受理はコードと境界テストが対応しており、この部分は静的には破れなかった。