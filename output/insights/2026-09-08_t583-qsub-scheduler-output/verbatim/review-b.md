## 判定

m1〜m5 はすべて赤になる。検査の穴はない。

ただし、事前登録された帰属は不正確である。m1/m2 は assert ではなく `list.index()` の `ValueError` で2本とも落ち、m3/m5 も負例だけでなく正例も落ちる。以下は静的に到達順まで追った結果である。

表中の nodeid は次の略号を使う。

- P: `orchestrator/tests/test_pegasus_calibration_workload.py::test_submit_dry_run_passes_scheduler_file_paths_to_qsub`
- N: `orchestrator/tests/test_pegasus_calibration_workload.py::test_submit_dry_run_keeps_scheduler_output_outside_the_repository`

## 変異帰属表

| 変異 | 赤になる nodeid 完全集合 | 実際に最初に赤になる箇所 | 単一理由性 |
|---|---|---|---|
| m1: `-o` 削除 | P、N | P: assert なし。`test_pegasus_calibration_workload.py:237` の `qsub_argv.index("-o")` が `ValueError`。Nも同様に `:262` | 否。意味上の原因は `-o` 欠落1件だが、2テストの抽出処理が別々に例外を出す。前段の script gate はない |
| m2: `-e` 削除 | P、N | P: assert なし。`:238` の `qsub_argv.index("-e")` が `ValueError`。Nは `:263` | 否。m1と同じく2テストの抽出例外で重複。前段の script gate はない |
| m3: stdout を `"$REPO_ROOT/scheduler.stdout"` に変更 | P、N | P: `:244` の stdout basename assert。N: `:266` の repo containment assert | 否。m3は配置だけでなく basename も同時に壊す。Pの`:249`も偽だが`:244`が先に停止する |
| m4: `-o` に directory root を渡す | Pのみ | P: `:244` の stdout basename assert | assert 層では否。`:247`の root 非一致と`:249`の親一致も偽だが、basename assert が先に発火する。Nは緑 |
| m5: `dirname` を2段から1段へ変更 | P、N | P: `:249` の期待親 directory 一致。N: `:266` の repo containment | 否。正例の exact-root gate と負例の containment gate が独立に同じ変異を捕捉する |

## 所見 1: m1/m2 は意図した assert failure ではなく抽出例外である

根拠 (`orchestrator/tests/test_pegasus_calibration_workload.py:237,238,262,263`)

`qsub_argv.index("-o")` と `.index("-e")` は、option がない場合に assert へ到達せず `ValueError` を投げる。pytest 上は赤になるが、「argv に option が存在する」という契約を明示的な assert で検査した結果ではない。また正例と負例の両方が同じ抽出に依存するため、事前登録の「正例だけ」という帰属も成立しない。

影響

成果物への影響: mutation report を事前登録どおり「正例の契約 assert が m1/m2 を KILL」と記録すると、実際には harness 例外であるため検出根拠が虚偽になる。

推奨 (must-fix): 実測結果にはPとNの両方、および `ValueError` であることを記録する。テストを直す場合は、値を抽出する前に `"-o" in qsub_argv` と `"-e" in qsub_argv` を明示的に assert する。

## 所見 2: m3/m5 の「負例だけ・単一理由」という事前帰属は成立しない

根拠 (`orchestrator/tests/test_pegasus_calibration_workload.py:244,249,266`、`tools/pegasus/submit_certify.sh:89,179`)

m3 は stdout の配置だけでなく名前を `scheduler.stdout` に変えるため、正例の basename assert が負例より先に赤になる。m5 では実装だけが1段導出へ変わり、テスト側の `expected_root` は2段導出のままなので、正例`:249`と負例`:266`がともに赤になる。

影響

成果物への影響: m3/m5 を「負例が独自に KILL し、理由は一つ」と報告すると、変異帰属表と実際の failure matrix が一致しない。

推奨 (must-fix): 親の実測結果では、m3とm5の赤 nodeid をP・Nの両方として記録し、単一理由性なしと明記する。正例を弱めて負例だけへ帰属させてはならない。

## 所見 3: m5 は期待値追随で緑にはならない

根拠 (`tools/pegasus/submit_certify.sh:88-90`、`orchestrator/tests/test_pegasus_calibration_workload.py:210-228,249,266`)

テストは script の式や出力 root を読み取って期待値を作っていない。独立した `git rev-parse` 結果へ、Python側で常に `parent.parent` を適用する。

通常 fixture では common dir が `<tmp>/repo/.git` なので、

- 正常実装の2段導出: `<tmp>/izanagi-job-evidence/...`
- m5の1段導出: `<tmp>/repo/izanagi-job-evidence/...`
- テスト期待値: `<tmp>/izanagi-job-evidence/...`

となる。したがってPの`:249`とNの`:266`が赤になる。テストと実装が同じ概念式を重複保持する保守上の相関はあるが、今回の実装だけを変えるm5で期待値が追随する経路はない。仮に将来双方を1段へ同時変更しても、Nの containment assert は赤になる。

影響

m5 に検出穴はなく、修正案を提示する条件には該当しない。

推奨 (不採用): m5対策の追加修正は不要。

## 所見 4: 負例テストには独自の変異検出力がない

根拠 (`orchestrator/tests/test_pegasus_calibration_workload.py:223-228,249-250,253-268`)

この fixture では `git_common_repo == fixture_repo` であり、`expected_root` はその sibling である。正例が `output_path.parent == expected_root` を満たせば、その output は必ず fixture repo と git common repo の外になる。そのため負例の全 containment assert は正例から論理的に導ける。

m1/m2では負例も抽出例外を重複して出す。m3/m5では負例も赤になるが正例も既に赤で、m4は正例だけが赤になる。したがって、m1〜m5のうち負例だけが独自に検出する変異はゼロであり、検出力だけなら正例で足りる。

影響

総合的な検出力は落ちていないが、「負例が m3/m5 を独自に守る」という説明は成立しない。負例の価値は repo 外という性質を直接表現する可読性に限られる。

推奨 (nit): 裁定が2本を要求しているためテストは維持し、独自検出力を主張しない。

## 所見 5: 一部の assert は先行条件により恒真または完全重複である

根拠 (`orchestrator/tests/test_pegasus_calibration_workload.py:242-250,265-268`)

正例の`:247-248`は、直前の basename regex が成功した後には恒真である。`expected_root.name` は `calibration-certify` であり、regexを通った path名は `<32hex>.scheduler.stdout` または `.stderr` なので、path全体が root directory と等しくなることはない。m4では`:247`も偽になるが、その前の`:244`で停止するため独自検出にはならない。

負例の`:267-268`は、通常の `git init` fixtureでは `git_common_dir.parent == fixture_repo` なので`:265-266`と完全に同じ判定である。

影響

赤を増やす assert に見えるが、実際の mutation attributionには寄与しない。検出穴ではない。

推奨 (nit): mutation report ではこれらを独立した検出理由に数えない。

## 所見 6: `Path.parents` は字句的 containment であり、一般的な物理 containment ではない

根拠 (`orchestrator/tests/test_pegasus_calibration_workload.py:264-268`)

`Path.parents` は `resolve()` を行わない。そのため相対 path、`..`、symlink を含む入力では誤判定できる。例えば repo 外へ正規化される `repo/../outside/file` を repo 内と判定し得る一方、repo 外に見える symlink が repo 内を指す場合は受理し得る。

ただし今回の fixtureでは、script が `pwd -P` 済み repoから絶対 common dirを取得し、固定 suffixを連結しており、相対 pathや`..`は生成されない。新規 fixtureにも symlink はない。したがってm1〜m5の帰属には影響しない。

影響

このテストが証明するのは現在の fixtureに対する字句的 repo 外配置であり、任意の filesystem topologyに対する物理的 containmentではない。

推奨 (不採用): ruling §1と§3が symlink・realpath containment の追加を明示的に不採用としているため、今回の成果物では拡張しない。

## 所見 7: nonce一致 assert は恒真ではないが、submission nonceへの結合までは証明しない

根拠 (`tools/pegasus/submit_certify.sh:93-97,178-181`、`orchestrator/tests/test_pegasus_calibration_workload.py:242-246`)

`:246`が守るのは、stdoutとstderrが同じ32桁識別子を持ち、同一投入の対として扱えることだ。一方だけ別 nonceへ変えれば赤になるため恒真ではない。これが壊れると、stdoutとstderrの対応付けが不確実になり、別投入の evidence と誤認する危険が生じる。

ただし両 pathを同じ別 nonceへ変えた場合は緑であり、`-v` の `IZANAGI_SUBMISSION_NONCE` や receipt nonceとの一致までは検査していない。

影響

指定された「両 pathの nonce一致」は守るが、scheduler fileと submission receiptの完全な結合証明ではない。

推奨 (nit): 現裁定の要求には適合している。将来 receiptとの結合まで主張する場合だけ、`-v` 内の nonceとの一致を追加する。

## 所見 8: 既存テストの弱体化はない

根拠 (`git diff`、`orchestrator/tests/test_pegasus_calibration_workload.py:3-268`)

差分は2ファイルだけで、test fileは import 3行と新規 helper・2テストの112行追加のみである。既存 assertの反転・緩和・削除、skip追加、既存テスト名の変更はない。script側も新規 root導出3行と qsub blockの所定変更だけである。

影響

既存テストを弱めて新規テストの緑を作った形跡はない。

推奨 (不採用): 対応不要。

## 総括

- m1〜m5は全件赤で、m5を含め検出穴はない。
- 最重所見は、m1/m2が assertでなくP・N双方の`ValueError`になる点。
- 次に、m3/m5はP・N双方が赤となり「負例だけ・単一理由」という事前帰属が成立しない。
- 負例に独自検出力はなく、恒真・重複assertもあるが、総合的な correctness gateは弱まっていない。