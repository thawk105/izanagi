## 受理集合の所見

- **must-fix — A3/B5 は未完了。放置すると export 後の任意代入や unset を契約テストが受理し、driver の依存 prefix が変わる。** `_shell_body_without_heredocs` はコメントを除く前に `<<` を探すため、export 後の次の literal は shell では代入を実行する一方、検査面からは全て消える。

```bash
# <<true
CMAKE_PREFIX_PATH=/tmp/deps
true
```

  根拠は [test_p3_s4_loop_job_contract.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_p3_s4_loop_job_contract.py:45) と [test_p3_s4_loop_job_contract.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_p3_s4_loop_job_contract.py:65)。真正 heredoc 本文と全行コメントは除外できるが、コメント中の偽 opener は誤認する。また `true # timeout 60 "${gflags_install_argv[@]}"` は marker を満たすのに install を実行しない。

- **must-fix — D1773(d) の「driver 本走まで保持」が unset 以外では束縛されない。放置すると prebuild だけ成功し、両 driver は prefix 無しで動ける。** 次はいずれも [prefix 検査:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_p3_s4_loop_job_contract.py:376) を通過する。

```bash
unset CMAKE_PREFIX_PAT\H
export -n CMAKE_PREFIX_PATH
env -u CMAKE_PREFIX_PATH "$PY" -B -m orchestrator.campaign.p3_s4_loop ...
```

  1 行目は bash が `CMAKE_PREFIX_PATH` として解釈するが unset regex に一致しない。2 行目は export 属性を外し、3 行目は driver だけから環境値を除く。

- **must-fix — prebuild → driver 2 分岐の位置束縛が literal には無い。放置すると prebuild 前の driver と、driver を呼ばない分岐を契約が受理できる。** singleton は install 2 本 → export → prebuild を検査する一方、driver は export より後かだけを検査している [test_p3_s4_loop_job_contract.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_p3_s4_loop_job_contract.py:392)。stage-order も `if` の位置だけで、driver との所属関係を持たない [test_p3_s4_loop_job_contract.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_p3_s4_loop_job_contract.py:431)。

- 指定された通常形、すなわち部分値、別変数、2 回目、`export` 無し、`declare -x`、前置代入、`+=` は regex が行中の literal を拾い、行全体が allowed と一致しないため拒否される。

- **nit — 受理集合は逆方向にも狭い。放置しても実行結果は変わらないが、無害な shell 文を偽拒否する。** `printf '%s\n' 'CMAKE_PREFIX_PATH=/tmp/deps'`、`true # CMAKE_PREFIX_PATH=/tmp/deps`、`echo unset CMAKE_PREFIX_PATH` も拒否される。

- `body.index(sanitize)` の ValueError 経路は無い。通常呼出しでは required fragment が先に失敗し、helper 単独でも `prefix_unsets != [sanitize]` が先に AssertionError を送出する。allowed も同様に先行 guard がある。

## fragment / mutant の帰属

- 新規登録 11 件は、required 辞書の包含関係だけを見る限り、各置換で欠ける label は指定された 1 件だけである。`prebuild-dependency-prefix` も長い置換対象が短い required prefix を消すため単独欠落になる。

- **should — `dependency-policy-path` と `glog-install-timeout` の登録は段 4 の採否表に反する。放置すると mutant の単独帰属を過大表示する。** 前者は required の後なら stage-order も失敗し、後者は singleton-order と stage-order も失敗する。それでも [test_p3_s4_loop_job_contract.py:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/tests/test_p3_s4_loop_job_contract.py:666) は required 検査の最初の例外だけを見るため成功する。段 4 はこの 2 件を登録外と明記していた。

- A2 の `TMPDIR`、gflags/glog install root は required に入り、両 install root の mutant も追加済み。B4 の `TMPDIR` と sanitized PATH の marker 順も追加済み。

- 追加された拒否メッセージ 8 件は、job body では全て `refuse` 呼出しに属する。既存 refusal の期待値は削除・変更されていない。

## prebuild prefix の所見

この項目には追加所見なし。A4 は現在の job bodyでは閉じている。

- [job body:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/p3_s4_loop_pegasus.sh:463) で両 install dir を Python に渡し、[job body:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/p3_s4_loop_pegasus.sh:499) で semicolon-list を構成している。
- explicit 値は `;` で分割され、各要素が `abspath` と `realpath` で正準化される [buildcache.py:1845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/campaign/buildcache.py:1845)。
- env の colon-list と explicit の semicolon-list は各 API の区切り規則に沿い、root の順序はともに gflags → glog。CMake configure には `-DCMAKE_PREFIX_PATH=<realpath gflags>;<realpath glog>` が入る [buildcache.py:2041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/campaign/buildcache.py:2041)。
- receipt の `record` は従来の 10 key のままで、`configure_argv` の内容だけが増える [job body:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/p3_s4_loop_pegasus.sh:510)。

## 規律 2 の確認

既存の shim、`--no-build`、CMake include、compiler launcher の拒否述語は削除・緩和されていない。入力を `_shell_executable_surface` に変えたことで真正 heredoc本文と全行コメントだけが対象外になり、通常の実行行に対する既存拒否は維持される。

既存テストの期待値にも変更はなく、新しい required、refusal、mutant が追記されただけである。ただし上記の偽 heredoc、行末コメント、prefix 保持、driver 順序の穴により、A3/B5 を含む新しい保証全体はまだ規律 2 の要求を満たさない。

## A1 の射程

A1 の盲点自体は広がっていない。旧 helper も heredoc 除去後の literal な直接代入しか扱わず、`printf -v`、`read`、分割名 `eval`、shell が実行する heredoc 内代入を受理していた。新 regex は通常の直接形については旧 regex より広く検出し、意図した exact export だけを追加受理している。

偽 heredoc opener による隠蔽も `_shell_body_without_heredocs` の既存挙動なので、A1 の「本 wave 以前からの盲点」という裁定は維持できる。一方、`export -n`、`env -u`、prebuild より前の driver はA1ではなく、本差分が新設した保持・位置契約の欠陥である。

## 総括

must-fix は3件ある。

- コメント中の偽 heredoc openerと行末コメントにより、A3/B5 の実行面検査を回避できる。
- unset 以外の方法で driver から prefix を除去でき、D1773(d) が未束縛である。
- driver 2 本が prebuild より後という位置関係を検査していない。

should は、段 4 で登録外とされた policy-path と glog-install-timeout mutant の誤登録。A2、A4、B4 の production literal は反映済みだが、A3/B5 は受理集合として閉じていない。

pytest と job 実走は行っていない。539 passed / 1 skipped は親から提示された焦点走の記録であり、本レビューでは再検証していない。