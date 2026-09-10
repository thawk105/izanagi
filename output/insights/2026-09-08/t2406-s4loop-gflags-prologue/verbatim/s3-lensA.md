## 受理集合の所見

- **must-fix — 間接代入が拒否されない。** 提案 regex は `CMAKE_PREFIX_PATH=` または `+=` の連続表記しか検出しない。exact export の後に `printf -v CMAKE_PREFIX_PATH ...`、`read CMAKE_PREFIX_PATH ...`、変数名を組み立てる `eval "$name=..."`、または shell が実行する heredoc を置いても、shim、stage-order、required fragment のどれも拒否しない。放置すると任意 prefix を使う job body が受理され、prebuild と compute-result の依存実体が変わる。

| 別形 | 提案述語 | 他の検査 |
|---|---|---|
| 先頭空白、空白数変更、末尾コメント | 拒否。行全体が `allowed` と不一致 | 不要 |
| 引用符変更 | 拒否 | 不要 |
| `export` なし | 拒否 | 不要 |
| `declare -x CMAKE_PREFIX_PATH=...` | 拒否 | 不要 |
| `env CMAKE_PREFIX_PATH=... cmd` | 拒否 | 不要 |
| `CMAKE_PREFIX_PATH=... "$PY"` | 拒否 | 不要 |
| 関数内の直接代入 | 拒否 | 不要 |
| heredoc 外の `printf -v` | **拒否されない** | shim、stage-order、fragment とも捕捉しない |
| literal を含む単純な `eval 'CMAKE_PREFIX_PATH=...'` | 拒否 | 不要 |
| 名前を分割・変数化した `eval` | **拒否されない** | 他の検査も捕捉しない |
| shell が source/eval する heredoc 内の代入 | **拒否されない** | heredoc 除去により全検査から消える |

- **must-fix — `$TMPDIR` 束縛が契約化されていない。** 提案 required には `export TMPDIR=$scratch`、`GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"`、`GLOG_INSTALL_DIR="$TMPDIR/glog-install"` がない。exact export を残したまま両変数を任意 path に変える mutant は受理される。放置すると job-private でない依存を使えてしまい、job body の受理集合と driver identity の prefix roots が変わる。

- **位置束縛は全 suite では成立するが、禁止 helper 単独では不完全。** stage-order は `_shell_executable_surface` を使い、両 install、exact export、prebuild 呼出しを一意かつ順番どおり検査する。コメント行と heredoc 本文は除去されるため、この検査は同文字列に誤誘導されない。

- **should — 禁止 helper の位置検査はコメントを実行面として数える。** `_assert_forbidden_job_constructs` は heredoc は除くがコメントを除かず `body.count/index` する。無害な同文コメントで偽拒否でき、実 install をコメント化した形を helper 単独では見逃せる。全 suite では stage-order が後者を拒否するが、helper の受理集合と帰属説明は一致しない。

## 判定材料の出所の所見

- **must-fix — F813 の型に該当する。** `prepare_masstree_fetchcontent` は `dependency_prefix` 未指定なら prefix を argv に追加せず、`_run` が ambient env を継承する。したがって CMake が環境から解決した prefix は、既存 receipt の `configure_argv`、`build_argv`、`toolchain_manifest` のいずれにも残らない。放置すると環境依存で生成された `config.h` を持つ receipt が、依存 prefix の記録なしに受理される。

- driver 側は `build_v2` が ambient 値を `os.pathsep` で正準化して identity に入れるため、少なくとも prefix path 列は束縛される。ただしこれは prebuild receipt の欠落を補わない。

- **現在 scope 内の最小手**は、prebuild 呼出しにも既存 `dependency_prefix` 引数を与えること。環境値は colon 区切り、同 API は semicolon-list を期待するため、raw な `os.environ["CMAKE_PREFIX_PATH"]` をそのまま渡してはいけない。exact な二 root から semicolon 形式を作れば、既存 `configure_argv` に `-DCMAKE_PREFIX_PATH=...` が保存される。環境 export は D1773(d) のため引き続き driver 本走まで保持する。新 file、buildcache 変更、receipt schema 変更は不要。

- 既存 receipt に gflags/glog の source HEAD、install realpath、build argv を追加すれば material provenance はさらに強くなるが、これは最小手ではなく、現プランが宣言する schema 不変と consumer 閉包を越える。

## 変異の帰属の所見

提案 required fragment と mutant の帰属は次のとおり。「単独」は既存の別 gate だけでは同 mutant が赤にならないものを指す。

| fragment | mutant | 帰属 |
|---|---|---|
| `dependency-policy-path` | `/tmp/policy.json` | **不成立**。stage-order も赤 |
| `dependency-policy-fields` | なし | 未証明 |
| `dependency-compilers` | CXX を gcc | 単独 |
| `gflags-head-exact` | expected 比較を空文字比較 | 単独 |
| `gflags-dirty-all` | `all` を `no` | 単独 |
| `gflags-configure-root` | なし | 未証明 |
| `gflags-configure-definitions` | なし | 未証明 |
| `gflags-build-argv` | `-j 47` | 単独 |
| `gflags-install-timeout` | なし | stage-order と冗長、未証明 |
| `glog-head-exact` | なし | 未証明 |
| `glog-dirty-all` | なし | 未証明 |
| `glog-configure-definitions` | `WITH_UNWIND=ON` | 単独 |
| `glog-build-argv` | なし | 未証明 |
| `glog-install-timeout` | `timeout 60` | **不成立**。stage-order と禁止 helper も赤 |

- partial prefix、別変数 prefix、二本目の exact prefix は prefix whitelist だけに帰属する。

- before-install mutant はその test node 内では位置述語に帰属するが、全体では stage-order も拒否するため単独帰属ではない。

- **nit — `test_registered_fragment_mutants_have_one_static_failure` は helper が最初に返す文言を一つに固定するだけで、suite 全体で failure node が一つとは証明しない。** 放置しても job body の受理集合は変わらないが、変異 matrix の帰属表示が過大になる。

- `$TMPDIR` と両 install-dir 定義には fragment も mutant もなく、今回もっとも重要な値束縛が未検査である。

## 裁定との整合

- D1773(a): 整合。policy 四 key への依存を追加している。
- D1773(b): 整合。新 provenance file を作らず、六 command の出力は既存 job stdout/stderr に流す。
- D1773(d): 整合。exact export を prebuild 前に置き、両 driver 分岐まで unset しない。
- 「そのまま移植」: `fail 2` から job 固有の `refuse`、`$TOOLS` から `$repo/...`、既存 TMPDIR/Python の再利用、provenance redirect の除去は、移植先との接続または D1773(b) に必要な適応であり裁量内。
- prebuild へ explicit dependency prefix も、同じ実効値を既存 receipt に露出させる接続上の適応であり、prologue 自体を変えないため裁量内と判断する。
- **nit — D1773(c) とは逐語上不整合。** 裁定は admission registry を同 commit で「更新する」と明記するが、親 brief は条件付きへ弱め、段 2 は変更不要と断定した。分類内容を変える根拠はなく成果物の job acceptance も変わらないが、registry 不変を選ぶなら再裁定が要る。

## (P1)〜(P7) の判定

| 判断 | 判定 | 根拠と成果物への影響 |
|---|---|---|
| P1 | refuted | rc=2 と拒否 payload を保ち、既存 job の prefix を付ける適応は妥当。受理結果は変わらない |
| P2 | refuted | `--untracked-files=all` は移植元を忠実に保ち、未追跡物を依存 build へ混ぜない |
| P3 | 条件付き、should | `/usr/bin/gcc` と gcc-11 realpath は実測 host の値で、compute node と `compilers_for_current_site()` への一般化は未証明。不一致なら異なる compiler で依存を作り、compute-result または ABI identity の説明が崩れる |
| P4 | refuted | qsub の既存 stdout/stderr routing が出力を保持し、新 provenance file を作らない裁定とも整合 |
| P5 | **real、must-fix** | driver identity だけでは ambient prefix を使った prebuild receipt を束縛できない。configure argv への explicit prefix 露出が必要 |
| P6 | refuted | TMPDIR、shim、repository 検査後かつ prebuild 前で、実行順として妥当。ただし値定義 fragment は別途必要 |
| P7 | 条件付き、should | queue が利用可能なら compute 実走なしでは D1737 の「最後まで通る保証なし」が残る。利用不能なら未実測を明記した land は可能だが、成功した compute-result は主張できない |

- 親の source HEAD・clean 実測は時点値だが、job body が毎回再検査するため恒久前提には一般化されていない。一方、compiler realpath と buildcache compiler の一致は runtime gate がなく、時点値の一般化になっている。
- policy whole-file pin、CLI に別 prefix 経路がないこと、registry consumer 閉包は、指定射影だけでは再検証できないため、本レビューでは親の記載以上の確証を与えない。

## 裁定パッケージ候補 (scope 外)

- prefix path だけでなく依存 material identity まで求める場合、既存 receipt に gflags/glog の source HEAD、install realpath、compiler/build argv を追加する案。新 file は作らないので D1773(b) の字面には反しないが、v1 schema と未射影 consumer の監査が必要で、現プラン外。
- job ID を含む prefix path により build identity が毎回変わる問題を解く content-based identity。buildcache の一般化を伴うため本 wave 外。
- registry を実質変更せず据え置くことを D1773(c) の例外として明示する再裁定。

## 総括

must-fix は三点ある。間接代入・実行 heredocによる whitelist bypass、`TMPDIR` と二つの install-dir の未束縛、prebuild receipt に ambient prefix が残らない F813 型の欠落である。最小修正は既存禁止述語をこれらの代入形へ閉じ、三つの値定義を required fragment と mutant で固定し、prebuild の既存 explicit-prefix 引数を semicolon 形式で使って `configure_argv` に実効 prefix を残すこと。

pytest および job 実走は行っておらず、緑とは判定していない。