## 直した内容

1. [AST 検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/orchestrator/tests/test_plot_a2_certification.py:544)
   - 2 定数への module-level 代入が各 1 回だけであることを検査。
   - `Assign`、`AnnAssign`、`AugAssign`、`NamedExpr` を走査。
   - subscript 代入と `.update()` などの変更呼び出しを禁止。
   - current 定数を含む全集合が直接の `frozenset` literal であることも固定。

2. [実 t2364 成果物テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/orchestrator/tests/test_plot_a2_certification.py:686)
   - 恒真だった 3 assert を削除。
   - 各 cell の `median_tps` を凍結 `certification.json` と照合。
   - 算出された 2 効果値を凍結 `effects` と照合。
   - `external_inputs` の path 集合を凍結 `raw-manifest.json` の `files` key 集合と照合。
   - 数値 literal は追加していない。

3. [歴史 policy の直接負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/orchestrator/tests/test_plot_a2_certification.py:832)
   - exact historical pair を登録後、`_load_current_policy` を直接呼び出す負例を追加。
   - 234 行目の文言を全文一致で固定。
   - 既存 end-to-end 負例は[そのまま維持](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/orchestrator/tests/test_plot_a2_certification.py:854)。

4. [current tracked_destination 負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/orchestrator/tests/test_plot_a2_certification.py:806)
   - current の完全な configure key 集合を維持したまま、`tracked_destination` だけを `"../outside"` に変更。
   - historical registry 非該当を明示確認し、共有 gate の完全な例外文を固定。

## 新しい nodeid

変更:

- `orchestrator/tests/test_plot_a2_certification.py::test_policy_generation_key_sets_are_independent_exact_literals`
- `orchestrator/tests/test_plot_a2_certification.py::test_t2364_canonical_current_full_measurements_load_without_override`

追加:

- `orchestrator/tests/test_plot_a2_certification.py::test_current_rejects_unbounded_tracked_destination`
- `orchestrator/tests/test_plot_a2_certification.py::test_historical_current_policy_directly_rejects_nonbound_source_binding_status`

## 単一理由性の確認

(3):

1. 埋め込み policy の base64 と SHA-256 は整合する。
2. 変更後 certification SHA-256 と policy SHA-256 の exact pair を歴史世代表へ再登録する。
3. producer の歴史 loader が六つの configure key を受理する。
4. `"token-mismatch"` は既知の status なので certification-cell 構文検査を通過する。
5. protocol、study、cell identity も不変。
6. [先頭 gate](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/tools/plotting/plot_a2_certification.py:233)だけで拒否される。`_load_current_policy` の直接呼び出しなので[二つ目の gate](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/tools/plotting/plot_a2_certification.py:432)には到達しない。

(4):

1. current の七つの configure key が完全であることを fixture 上で確認する。
2. `tracked_destination` 以外は変えず、変更後 policy hash を certification へ再束縛する。
3. exact pair が歴史 registry に無いことを確認し、current loader を選択させる。
4. base64、SHA-256、top-level schema、historical reference、durable path の各検査を通過する。
5. [tracked destination gate](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/orchestrator/campaign/paper_story_a2_certification.py:437)が `"../outside"` の `..` だけを理由に拒否する。
6. scheduler、configure grammar、manifest、raw cell の後段検査には到達しない。

## 実走結果

対象 pytest は実装済み・未実走です。

- 指定形式の直接 pytest: Pegasus 防護により起動前に拒否。
- `tools/run_tests.py` 経由: `qstat -Q` preflight が `rc=1`、dispatcher は `rc=16`、`child_started=false`。テスト実行数は 0。
- 対象 nodeid: 緑 0、赤 0、未実走 4。
- 制約 meta-test `test_plain_runner_coverage.py` の self-run harness: 3 緑、0 赤、0 skip。
- Python 構文検査、`git diff --check`、test 関数名の重複検査は成功。67 test 関数中、重複 0。
- dispatch 試行で生成された一時ファイルは除去済みで、新規 file は残っていない。

## 所有外への波及可能性

- production の `_load_current_policy` の唯一の production caller は [`load_measurements`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-fix1/tools/plotting/plot_a2_certification.py:515)。実装や呼び出し契約は変更していない。
- `_current_fixture`、historical fixture helpers は多数の同一ファイル内テストで共有されるが、helper 自体は変更していない。追加負例による状態変更は `tmp_path` と `monkeypatch` に閉じる。
- t2364 consumer test は、凍結 certification の median/effects または raw manifest の path 集合と consumer 出力が乖離した場合、新たに赤になる。
- AST 検査により、producer 定数を再代入、subscript 更新、変更メソッド呼び出しへ改造する将来の refactor は意図的に赤になる。
- production 2 file と docs は未編集。既存の適用済み production 差分も変更していない。`git add`、commit は行っていない。

## 総括

4 所見すべてを許可されたテストファイルだけで修正しました。  
新規負例は current と historical の到達世代を明示し、狙った gate の全文を固定しています。  
制約 meta-test と静的検査は緑です。  
対象 pytest は実行基盤の `qstat -Q` 障害により、実装済み・未実走です。