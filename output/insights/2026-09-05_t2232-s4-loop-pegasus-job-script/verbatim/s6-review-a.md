## 所見

1. 対象 file:line: `tools/pegasus/p3_s4_loop_pegasus.sh:174,204,333`、`orchestrator/tests/test_p3_s4_loop_job_contract.py:178-194,219-223,356-412`。3 個の clean gate は `[[ -n "$(git status ...)" ]]` だけを評価しており、条件文脈では `set -e` が `git status` の非 0 を捕捉しない。実際に同型の `false` は後続へ進むため、stderr のみ出して失敗した status を clean として受理する。M3 も成功して空文字を返す `printf ''` への置換しか扱わず、この経路を殺さない。成果物への影響: dirty または検査不能な superproject、CCBench、hydrate source から campaign 成果物や prebuild receipt が HEAD commit と clean を満たしたものとして生成され得る。重大度: must-fix。

2. 対象 file:line: `tools/pegasus/p3_s4_loop_pegasus.sh:41-45,174,204,333`。全 `GIT_*` を unset した後に `GIT_OPTIONAL_LOCKS=0` を再設定していないため、観測用 `git status` が optional index refresh を行い、特に durable な hydrate source の `.git/index` を更新し得る。「scratch へ複製するまで hydrate root を書き換えない」が成り立たない。成果物への影響: job 実行自体が hydrate cache の index 状態を変え、後続 run の clean 判定と source reference の初期状態を変え得る。重大度: must-fix。

3. 対象 file:line: `orchestrator/tests/test_p3_s4_loop_job_contract.py:491-498,562-586`、`s5-author.md:25`。M7 の負例は shim を削除せず、runtime closure も snippet から除いた上で `SANITIZED_PATH="$PATH"` に変える試験である。したがって「shim を作らない」という登録済み M7 と同一ではなく、M7 の単一理由性は証明されていない。実際に closure を含めて shim 一式を削れば、static fragment 欠落と snippet 抽出失敗など複数理由になり得る。成果物への影響: production 成果物は変わらないが、変異被覆報告の受理根拠が実際より強く見える。重大度: nit。

## 裁定との差分

- C4: tracked-clean 判定が `git status` の失敗を拒否せず、hydrate root の Git 観測も非変異化されていない。
- C16: superproject と CCBench の clean 検査が fail-closed ではない。

それ以外の C0〜C3、C5〜C17 は、指定された静的範囲では差分なし。C7 の指定 mutant を実際の位置へ加えると shim entry 数が 2 になり runtime で rc=2 となる。argv は parser 上、`--allow-coder-derived-build --isolate-worktree` と二択の入力だけで、`--no-build`、trace macro、verifier 緩和はない。

## 判定

NO-GO。

最小編集集合は次の 2 file。

- `tools/pegasus/p3_s4_loop_pegasus.sh`: sanitize 後に `GIT_OPTIONAL_LOCKS=0` を固定し、3 個の `git status` を「出力 capture の成否を明示的に検査してから空文字判定」に分ける。
- `orchestrator/tests/test_p3_s4_loop_job_contract.py`: optional-lock 固定と、superproject・CCBench・各 hydrate source の status 非 0が必ず rc=2 になる負例を追加する。

M1〜M16 の exact な現行 mutant は少なくとも指定テストを赤にする。複数の独立理由が確定しているのは報告どおり M13 と M14で、加えて M7 は登録文と試験 mutant が一致せず単一理由性を確認できない。

実装子の「実走」は contract file の直接実行を指し、compute job の実走ではない。報告自身も `run_tests.py`、`check_docs.py`、compute 実走を未実施と明記しており、compute を緑へ読み替えてはいない。本レビューでも pytest は実走していない。

## 総括

最大の欠陥は、3 個の clean gate が `git status` の非 0を clean として通すことである。
親は fix 前に、status が stderr のみを出して失敗する mutant が3対象すべてで rc=2になることを確かめるべきである。
併せて `GIT_OPTIONAL_LOCKS=0` を sanitize 後に固定し、hydrate source の index を観測で変更しない契約を追加する。
以上を直すまでは job body を計算ノードへ投入すべきでない。