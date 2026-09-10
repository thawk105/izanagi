## 移植の忠実さ

configure/build/install の配列、全 `-D`、`-j 48`、gflags 60 秒、glog 120 秒、HEAD/dirty 検査、最終 export は移植元と一致する。許可された `refuse` 化、policy path、provenance/redirect 除去、explicit `dependency_prefix` 以外の実行面差はない。

- `[nit]` 列挙外の literal 差は出典コメントだけである。
  - 元: `# 出典: floor_campaign.sh:703-878。pinned gflags/glog build prologue を同手順で踏襲。`
  - 先: `# 出典: floor_scoping.sh:205-283。pinned gflags/glog build prologue を同手順で踏襲。`
  - 放置時: 実行結果は変わらないが、「列挙した差以外は literal に同じ」という監査上の説明だけが不正確になる。

## bnode での実効性

静的には成立する。

- policy Python の失敗は standalone assignment `policy_output=$(...)` の終了 status になり、`set -e` から `finish` trap へ伝播する。ただし `refuse` には変換されず生の Python rc になる。
- 空出力への `readarray -t policy_values <<<"$policy_output"` は here-string の改行により空文字 1 要素となり、4 field 検査で rc=2 refusal に入る。
- scratch root は事前に非存在を検査して create-only で作られるため、その直下の `mkdir "$GFLAGS_BUILD_DIR"` と `mkdir "$GLOG_BUILD_DIR"` は fresh job では成立する。
- prebuild heredoc は shell 側の引数が13個、Python 側の unpack も13変数で一致する。追加された末尾2個は gflags/glog install dir である。
- `CMAKE_PREFIX_PATH` は親 shell で export され、その後に unset、subshell、`env -u` はない。prebuild Python と両 driver 分岐へ残る。
- `$PY` は事前解決済み、`TMPDIR` と sanitized PATH は prologue より前に export 済み、`GIT_*` は一度除去後に `GIT_OPTIONAL_LOCKS=0` だけ再設定される。`umask 077` とも矛盾しない。
- B1の `command -v` 生 rcと配列内先頭 `realpath` 失敗の隠蔽、B3の timeout/`-j 48` 実績不足は移植元どおり残るが、裁定済みの既知リスクであり新規欠陥ではない。

## 契約テストとの相互作用

- `[must-fix]` heredoc 内の required fragment を raw source の部分文字列だけで検査するため、行をコメントアウトしても契約が通る見逃しがある。例えば次のどちらも required fragment を残したまま有効処理を無効化できる。
  - `    # "gflags_source_path",`
  - `    # dependency_prefix=";".join([gflags_install_dir, glog_install_dir]),`
  - 放置時: policy が3 fieldになって実機だけ refusal になる、または explicit prefix が消えて receipt の `configure_argv` 束縛を失う回帰を、静的契約が受理できる。

forbidden/order 側を `_shell_executable_surface` に移したこと自体は正しい。heredoc と全行コメントが除外され、glog の `-DCMAKE_PREFIX_PATH=` は負の lookbehindにより shell代入と誤認されない。B4/B5 の marker、unset、export、prebuild、両 driver の位置検査にも現行本文上の誤検出はない。

`_shell_submitter_violations` は heredoc を `<<< ''` に置換してから `bash -n` と shlex を使う。新本文に qsub commandはなく、配列、command substitution、heredoc追加で走査状態が壊れる要素も見当たらない。

## README の整合

新しい2 bulletは job bodyと一致する。wrapper/launcherは追加されず、exact prefix export、prebuildへの explicit prefix、provenance file非作成も実装どおりである。qsub fenceは admission markerが先頭で、stdout/stderrの双方を evidenceへ送る。[T-2407] の `cd "$REPO_ROOT"` と submodule PIN checkout以外では、次の不整合が残る。

- `[should]` [README §7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/README.md:370) は依然として「本 job body は main 着地後にしか投入できない」「計算ノードでの動作は測っていない」とする。これは job `981655.nqsv` の到達実績と、固定 SHA の専用 checkoutから投入するP7手順に反する。
  - 放置時: 既に実測された preflight と、今回まだ未実測の新 prologue以後の範囲を読者が区別できない。

- `[should]` 段4裁定B2で追加するとした「`driver_rc` は driverだけでなく job body全体の終了 rc」という説明が§7にない。
  - 放置時: policy parse、Git、CMake、timeoutなど prologue失敗の生 rcを driver本走の終了 rcと誤解する。

## 段 3 所見との一貫性

B4は `export TMPDIR=$scratch` と sanitized PATHのmarker追加で採用済み。B5も初期unsetの唯一性、export後unset拒否、両install→export→prebuild→両driverの順序で採用済みである。

B1とB3を移植元どおり残す判断は差分と裁定文で一致する。B2も実装を変えない点は一致するが、裁定したREADME補足だけが欠落している。B7/B8は指定どおり[T-2407]への持ち越しである。B9は見出しのみ更新され、末尾F660文面の更新が未完了である。

## 総括

`must-fix` 1件、`should` 2件、`nit` 1件。現行 job bodyの実行経路には、許可された移植差以外の機能欠陥を認めない。一方、heredoc required fragmentのコメントアウトを契約テストが見逃すため、統合差分は現状のままでは受理不可と判定する。

pytestその他の試験は実行していない。親報告の `539 passed / 1 skipped` を独立には検証していない。