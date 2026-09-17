## 所見 (real / refuted、must-fix / nit / backlog、成果物影響、再現入力と実測)

**D1891 の再帰実装は GO。must-fix は検出しませんでした。ただし、変異の単一理由性と M8 の分類には注意が必要です。**

以下、A＝ALLOW、D＝DENY。特記しない site は `PEGASUS_LOGIN`、repo_root は指定 worktree です。指定差分から変更前ソースをメモリ上で復元し、blob `3b5f6b65018b130702060b9aabc780ff06f1bc89` と一致確認して比較しました。コマンド自体は実行せず、`decide()` を直呼びしました。pytest は未実行です。

**1. refuted / nit — 指定された綴り差で再帰が届かない疑い**

次の入力はすべて **変更前 A → 現物 D** でした。

| 確認対象 | 再現 command |
|---|---|
| 密着形 | `python3 -mcProfile -mpytest -q` |
| `-qm` | `python3 -qm cProfile -m pytest -q` |
| module 等号形 | `python3 -m trace --trace --module=pytest -q` |
| 密着出力値 | `python3 -m cProfile -o/tmp/x -m pytest -q` |
| `--` 後の script | `python3 -m cProfile -- pytest -q` |
| coverage 値付き option | `python3 -m coverage run --source=orchestrator --rcfile /tmp/rc --data-file /tmp/cov -m pytest -q` |
| trace 長 option | `python3 -m trace --module pytest -q` |
| trace 短 option | `python3 -m trace -m pytest -q` |
| runpy positional | `python3 -m runpy pytest -q` |
| 二重 wrapper | `python3 -m cProfile -m cProfile -m pytest -q` |
| 三重 wrapper | `python3 -m cProfile -m profile -m pdb -m pytest -q` |
| 外側 wrapper 列 | `env FOO=1 nice -n 0 command exec python3 -m cProfile -m pytest -q` |
| shell 内側 | `bash -lc 'python3 -m cProfile -m pytest -q'` |
| 絶対 interpreter・版・値付き prefix | `/usr/bin/python3.10 -W ignore -X dev -m cProfile -m pytest -q` |

`trace -m` は `--module` と同じ解釈ではありません。抽出結果は実測で `('script', 'pytest', ['-q'])`。既存 option 表どおりの区別です。

`python3 -qmcProfile -m pytest` は **D→D**。これを新規検出力から外した子 B の扱いは正当です。

**2. real / backlog — 内側の非実行判定に既存の境界問題が残る**

| 再現 command | 変更前→現物 |
|---|---|
| `python3 -m cProfile -m pytest --collect-only` | A→A |
| `python3 -m cProfile -m pytest --help` | A→A |
| `python3 -m cProfile -m pytest --version` | A→A |
| `python3 -m cProfile -m pytest -h` | A→D |
| `python3 -m cProfile -m pytest --co` | A→D |
| `python3 -m cProfile -m pytest -- --help` | A→A |

短い非実行 option は拒否され、`--` 後の位置引数 `--help` も非実行フラグとして扱われます。後者は、その名前のテスト対象が存在する場合の実行を区別できません。

ただし直接形も、変更前から `python3 -m pytest -h`／`--co` は D、`python3 -m pytest -- --help` は A でした。原因は既存 `_pytest_nonexecuting`。同じ判定を再帰適用する今回の仕様には適合し、変更禁止面でもあるため backlog です。

`python3 -m cProfile -- -m pytest` の **A→D** も再確認しました。親・子が報告済みの既存 residual 判定の波及であり、新規所見ではありません。

**3. real / nit — 変異の「専属 killer」候補は、そのままでは単一にならない**

直呼びで M1 は新規3関数、M2 は2関数、M4 は2関数が AssertionError になりました。特に M4 は異なる二理由です。

- `python3 -m cProfile -m pytest --collect-only`：現物 A → M4 D。
- `python3 -m cProfile -m cProfile -m pytest -q`：現物 D → M4 A。

実装の問題ではありません。親の matrix では、選択した killer と他の赤を区別し、「専属1関数を確認済み」と記録しないことが必要です。詳細は次節です。

**4. real / nit — M8 は非等価だが、新規6関数では検出されない**

再現入力：

`python3 -m cProfile tools/run_tests.py -m pytest -q`

実測は **変更前 A／現物 D／M8 A**。再帰を sanctioned 早期許可の後へ移すと、外側が `tools/run_tests.py` を理由に許可されます。

一方、`python3 -m cProfile -m pytest tools/run_tests.py` は **現物 D／M8 D** で、位置の検出には使えません。

新規6関数は M8 でも全部通りました。§5 は corpus に依存する SURVIVED 対照を許しているため must-fix とはしませんが、**全入力で等価とは分類できません**。上の入力を追加すれば、この gate を検出できます。

## 変異 M1〜M8 の単一理由性判定

関数名は `test_bash_login_executor_recursion_` を省略しています。結果は選択関数の直接呼び出しであり、pytest matrix の結果ではありません。

| 変異 | anchor | AssertionError になった関数 | 判定 |
|---|---|---|---|
| M1 | 再帰入口の条件 | `module_denied`、`coverage_denied`、`script_denied` | 位置は一意。専属1関数ではない |
| M2 | module 名検証条件を module 全拒否へ | `module_denied`、`coverage_denied` | 位置は一意。専属1関数ではない |
| M3 | program 抽出内の coverage 経路 | `coverage_denied` | 選択範囲では単一 |
| M4 | module 合成から `*rest` を除去 | `module_denied`、`nonexecuting_and_light_allowed` | 位置は一意。過剰拒否と素通しの二理由 |
| M5 | script 抽出の返却 | `script_denied` | 選択範囲では単一 |
| M6 | module 名検証を恒偽化 | 新規正例関数＋既存非実行 mode 関数 | **既存 gate と冗長。新規検出力に数えない** |
| M7 | multi-target 除外を恒偽化 | 既存 pydoc mode 関数 | **非等価。既存 gate の検出力** |
| M8 | 再帰 block を早期許可後へ移動 | 選択した既存・新規関数では赤なし | **非等価だが未検出**。上記入力で識別可能 |

M6 の既存 killer は `test_bash_login_executor_nonexecuting_modes_restore_baseline_allow`。入力 `python3 -m runpy tools/pegasus/exec_calibrate.py` が **現物 A→M6 D** です。

M7 の既存 killer は `test_bash_login_pydoc_server_and_write_modes_do_not_execute_positionals`。入力 `python3 -m pydoc -w tools/pegasus/exec_calibrate.py` が **現物 A→M7 D**。したがって、M7 と M8 は等価変異でも、互いに同じ作用の変異でもありません。

追加6関数は実物の `GB.decide()` を呼び、fixture の stub はありません。負例18入力を個別比較し、**全18件が変更前 A→現物 D**。新規6関数の直呼びも、変更前は負例3関数のみ赤、現物は全6関数が通りました。既存拒否の再掲と M6 の正例再掲は、新規検出力とは分けて扱えます。

## 反転検査 corpus に無い綴りの追加提案 (command と期待判定)

**現物で D428 の D→A を起こす入力は発見していません。** 再帰追加は拒否理由を返すだけで、既存拒否を打ち消す経路はありません。共通化された既存 target 抽出にも意味変更は見当たりません。

親の追加61形の全文は射影資料にないため、以下が corpus 全体に未収録かは確定できません。重複確認して追加する候補です。すべて直呼び済みです。

| command | LOGIN・SUSPECT の変更前→現物／期待 |
|---|---|
| `python3 -m cProfile tools/run_tests.py -m pytest -q` | A→D／D。M8 検出用 |
| `python3 -W ignore -X dev -m coverage.__main__ run --source=orchestrator --rcfile /tmp/rc --data-file=/tmp/cov --module=pytest -q` | A→D／D |
| `env -S "python3.10 -m cProfile -o/tmp/p -m profile -m pytest -q"` | A→D／D |
| `python3 -m cProfile -o tools/pegasus/exec_calibrate.py -m pytest --collect-only` | D→D／D。出力先拒否の維持 |
| `python3 -m runpy -- tools/pegasus/exec_calibrate.py` | D→D／D。baseline 拒否の維持 |
| `python3 -m trace --report --file=/tmp/counts --module=pytest` | A→A／A |

OTHER・PEGASUS_COMPUTE は全行 A→A でした。D428 の維持検査として特に重要なのは、既存 DENY の第4・第5行です。

## 判定 (GO / NO-GO と理由)

**GO — D1891 の実装設計について。**

指定された射程で再帰欠落や既存拒否の緩和は見つかりませんでした。新規負例18入力にも実際の差分検出力があります。

変異評価では、M1・M2・M4 の複数 killer、M6・M7 の既存 gate との重複、M8 の非等価性を明記してください。この GO は、未実施の親の変異 matrix・受入全走まで合格とする判定ではありません。

## 総括

現物の再帰実装は裁定に適合しています。主なレビュー結果は、**M4 の二理由、M6・M7 の冗長性、M8 を識別する具体例**です。ファイル変更・pytest 実行は行っていません。