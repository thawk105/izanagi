## 変更した file と行範囲

- [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2406-author/tools/pegasus/p3_s4_loop_pegasus.sh:323): 323–420、463–500
- [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2406-author/orchestrator/tests/test_p3_s4_loop_job_contract.py:208): 208–322、372–414、442–455、498–505、584–658、711–764

変更ファイルはこの 2 本だけです。`git diff --check` も通過しました。

## job body の差分の要点

- plan の shell 本文が `claim_root` 検査直後に逐語一致で入ったことを機械照合しました。
- gflags/glog の argv、`-D`、timeout、`-j 48`、dirty 検査を維持しています。
- 8 個の失敗を同文の `refuse` に移しました。
- provenance file と出力 redirect は追加していません。
- exact な `CMAKE_PREFIX_PATH` export を install 後から driver まで保持します。
- prebuild へ install root 2 本を argv で渡し、semicolon 区切りの `dependency_prefix` を指定しました。
- receipt の `record` block は変更前と完全一致しています。canonical JSON と `os.fsync` は各 2 回のままです。

## 契約テストの差分の要点

- required fragment、stage order、8 refusal、fragment mutant を追加しました。
- `TMPDIR`、PATH、install root、policy、compiler、dependency prefix を固定しました。
- whitelist と位置検査を `_shell_executable_surface` 上へ移しました。
- exact export 1 回だけを受理し、sanitize unset 1 回、prebuild と driver 2 分岐への先行を固定しました。
- 部分 prefix、別変数、2 回目、install 前、export 後 unset を拒否します。
- shim、`--no-build`、include、launcher の既存拒否は維持しています。

## 直接呼出しによる検査結果

- 指定された主要テストを含む 10 関数: 全通過
- fragment mutant: 24 ケース全通過
- shim mutant: 8 ケース全通過
- CMake 禁止 mutant: 9 ケース全通過
- full source を stdin で `bash -n`: `rc=0`
- plan 本文との逐語照合、receipt block、count、provenance 不在: 全通過
- 期待どおりの赤化:
  - partial export mutant: `forbidden-cmake-environment-injection`
  - 禁止 helper を一時的に無効化: `DID NOT RAISE`
- 初回 parametrize harness は単一文字列の展開ミスで `TypeError` になりましたが、修正後に全ケースを再実行して通過しました。
- `bash -n tools/pegasus/p3_s4_loop_pegasus.sh` の file-argument 形は dispatch-required hook に遮断されました。ガードを回避した実行はせず、同じ全ファイル内容を stdin で構文検査しました。
- pytest は指示どおり未実行です。

## 波及の静的列挙

- `orchestrator/tests/test_hooks.py`: admission registry 不変のため鏡像期待値への変更なし。
- `tools/check_docs.py`: README と registry を変更していないため、本変更による期待値変更なし。
- `tools/pegasus_admission_registry.py`: registry entry 不変のため loader への波及なし。
- prebuild receipt consumer: schema と key 集合は不変。`configure_argv` に dependency prefix が残るだけです。

## 総括

plan v2 に沿う 2 ファイルの実装と直接検査は完了しました。計算ノード上の job body と pytest は未実走です。