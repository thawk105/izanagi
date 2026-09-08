# [T-2406] 段 4 裁定 — plan v2 と変異事前登録

裁定者: 親 (Claude)。入力: `s1-brief.md`、`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、D1773 / D1737 / F813、`buildcache.py` と `p3_s4_loop.py` の現物。
裁定 inbox の再走査: worklog 末尾 (1348) と D1773 以後の decisions に T-2406 の更新無し (2026-09-08 07:30 JST)。

## 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | lens A | `printf -v` / `read` / 名前分割 `eval` / shell が実行する heredoc 内の代入は whitelist 述語を素通りする | real だが**本 wave 以前から同じ盲点** (現行 regex も同一)。exact 1 行の受理追加はこれらを広げない | 不採用 (scope 外の gate 拡張、D1773 の範囲外・G05)。裁定パッケージ候補として記録 |
| A2 | lens A | `export TMPDIR=$scratch`・`GFLAGS_INSTALL_DIR`・`GLOG_INSTALL_DIR` の値束縛が契約に無い | real | **採用**: required fragment 3 本 + install dir の mutant |
| A3 | lens A | 禁止 helper の位置検査がコメント行を実行面に数える | should | **採用**: whitelist / 位置検査は `_shell_executable_surface` 上で行う |
| A4 | lens A | prebuild receipt に ambient prefix が残らない (F813 型)。既存 `dependency_prefix` 引数で `configure_argv` に露出できる | real | **採用**: job body の prebuild heredoc へ `dependency_prefix=";".join([gflags_install, glog_install])` を渡す (argv で 2 root を渡す)。consumer は `configure_argv` を list[str] としか検査しない (`p3_s4_loop.py:306`) ので schema 不変で通る。env export は (d) どおり維持 |
| A5 | lens A | 一部 fragment の mutant は複数 gate に赤が出る (policy-path、glog-install-timeout) | real | 変異 matrix ではこれらを登録せず、単独帰属の mutant だけ登録 |
| A6 | lens A | D1773(c) の「registry を更新する」と「変更不要」の逐語不整合 | nit | registry entry は分類・reason・gate・evidence に変えるものが無いことを再確認し不変。(c) は「変える場合は同 commit」と読む。record に明記し、ユーザー報告に載せる |
| B1 | lens B | `command -v` / `realpath` 失敗が rc=2 でなく生 rc、配列内 `$(realpath)` の rc 隠蔽 | nit | 不採用 (そのまま移植。失敗は configure で露出する)。record に書く |
| B2 | lens B | timeout 124 等は `driver_rc` として compute-result に入る | 既存挙動 (981655 も prebuild 失敗を driver_rc=1 で記録) | 不採用。README 文言で「driver_rc は job body の終了 rc」と補う |
| B3 | lens B | `-j 48` / 60 秒の bnode 実績が射影資料に無い | 条件付き | 不採用 (D1773 「そのまま移植」)。P7 の実走で観測 |
| B4 | lens B | order marker に `export TMPDIR=$scratch` と `export PATH="$SANITIZED_PATH"` が無い | must-fix | **採用** |
| B5 | lens B | export 後の `unset CMAKE_PREFIX_PATH` を検出しない → (d) を破れる | must-fix | **採用**: 実行面で `CMAKE_PREFIX_PATH` を含む `unset` は sanitize の 1 行だけ・export より前、export は prebuild 呼出しと driver 2 分岐より前、を禁止 helper で固定。負例 mutant を登録 |
| B6 | lens B | 新 8 message の試験は明示 refuse だけを覆う | 表現 | P1 を「明示 fail 8 個の写し」に限定して記録 |
| B7 | lens B | README §7 fence が qsub 前に `cd "$REPO_ROOT"` しない | real | **本 wave では不採用** — [T-2407] (D1777、§7 の投入手順修正) と同じ節なので同 wave へ持ち越す。record と報告に書く |
| B8 | lens B | README §7 に submodule PIN checkout 手順が無い | real | [T-2407] そのもの。持ち越し |
| B9 | lens B | §7 見出しの「計算ノードでは未実測」が stale | should | **採用** (docs、親): 見出しを 981655 の事実へ更新 |
| B10 | lens B | P7 の compute smoke 無しでは実効性を主張できない | real | **採用**: 統合 commit 後に固定 SHA の detached checkout から 1 本投入 (下記)。land 条件にはしない |

## (P1)〜(P7) の確定

- P1 確定 (明示 `fail 2` 8 個を同文 `refuse` へ)。P2 確定。P3 確定 (lens B: 同じ sanitized PATH で `compilers_for_current_site()` も gcc/g++ を解くので相対一致)。P4 確定。
- P5 修正: receipt schema は不変のまま、prebuild 呼出しに explicit `dependency_prefix` (semicolon) を渡して `configure_argv` に prefix を残す (A4)。ambient export は driver まで保持。
- P6 確定 + B4 の marker 追加。P7 採用 (B10)。

## plan v2 (= s2-plan + 次の差分)

1. job body: s2-plan の挿入本文どおり (`refuse` 化、`$repo/tools/pegasus/policy.json`、provenance 出力と `cmake-prefix-path.json` を落とす、redirect 無し)。加えて prebuild heredoc の argv に `"$GFLAGS_INSTALL_DIR" "$GLOG_INSTALL_DIR"` を足し、`prepare_masstree_fetchcontent(..., dependency_prefix=";".join([gflags_install_dir, glog_install_dir]))` とする。record (receipt) の key 集合は変えない。
2. 契約テスト: s2-plan の required / marker / refusal / mutant / whitelist / 正例負例に加え、(A2) `export TMPDIR=$scratch`、`GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"`、`GLOG_INSTALL_DIR="$TMPDIR/glog-install"`、prebuild の `dependency_prefix=";".join(` を required fragment に、(A3) whitelist と位置検査は `_shell_executable_surface(source)` 上で、(B4) marker に `export TMPDIR=$scratch` と `export PATH="$SANITIZED_PATH"` を `claim_root` より前に、(B5) `unset` の位置・回数と export の後段 (prebuild・driver 2 分岐) 先行を helper で固定し負例を足す。
3. registry: 不変 (再確認済み)。README §7: 親が bullet 2 本と見出しを直す。

## 変異事前登録 (DW-M01、実装後に node を probe で採る)

対象 test: `orchestrator/tests/test_p3_s4_loop_job_contract.py`。全て job body または test への 1 置換。

| id | category | 置換 | 期待 |
|---|---|---|---|
| m01-gflags-head-empty | negative | `"$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD"` → `"$GFLAGS_SOURCE_HEAD" != ""` | KILLED |
| m02-gflags-untracked-no | negative | gflags status `--untracked-files=all` → `no` | KILLED |
| m03-gflags-j47 | negative | `gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)` → `-j 47` | KILLED |
| m04-glog-unwind-on | negative | `-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"` → `ON` | KILLED |
| m05-prefix-partial | negative | export 行を `export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR"` へ | KILLED |
| m06-glog-install-tmp | negative | `GLOG_INSTALL_DIR="$TMPDIR/glog-install"` → `/tmp/glog-install` | KILLED |
| m07-unset-after-export | negative | export 行の直後に `unset CMAKE_PREFIX_PATH` を挿入 | KILLED |
| m08-export-before-glog | negative | export 行を glog install の前へ移す | KILLED |
| m09-cxx-gcc | negative | `CXX_PATH=$(command -v g++)` → `gcc` | KILLED |
| m10-policy-key | negative | heredoc 内 `"glog_expected_head",` → `"glog_head",` | KILLED |
| m11-prebuild-prefix-dropped | negative | prebuild heredoc の `dependency_prefix=";".join(` 行を削る | KILLED |
| m12-comment-equivalent | positive | prologue の `# 出典:` コメント文言を変える | SURVIVED |
| m13-test-whitelist-two | negative (test 側) | whitelist の `!= [allowed]` を「allowed が 1〜2 回」へ緩める | KILLED (second-exact-prefix 負例が赤) |

登録外 (帰属不成立): policy path 置換、glog install timeout 置換 (A5)。

## P7 生死確認の段取り (段 6 と並列、land 条件外)

固定 SHA (統合 commit) の detached checkout を `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2406-s4loop-gflags/submit-tree` に作り、CCBench submodule を `p3_s4_loop.PIN` へ checkout、`THIRDPARTY_SOURCE_ROOT` は T-2232 の hydrate 出力を再利用、`EVIDENCE_ROOT` は job dir 配下の新規 attempt dir、qsub 前に `cd "$REPO_ROOT"`、fixture 経路 (`IZANAGI_S4_PROPOSAL_PATH` 無し)。結果は insight へ写す。
