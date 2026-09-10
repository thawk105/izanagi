## 所見

### B-1: 新規 Git fixture が親プロセスの Git 環境に依存する

- 所見: 新規 helper の Git 呼び出しは `env` を指定しない raw `subprocess.run` であり、テスト用の隔離された環境を使っていない。
- 根拠: [orchestrator/tests/test_codex_reasoning_ab.py:2012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/orchestrator/tests/test_codex_reasoning_ab.py:2012)、同 2016、2017、2037、2039、2048、2050、2062、2077、2085。production helper の `_run` は [tools/codex_reasoning_ab.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/tools/codex_reasoning_ab.py:255) で `HOME=/nonexistent` と Git 環境除去を行う。
- 成立条件: 親環境に `GIT_DIR`、`GIT_WORK_TREE`、`GIT_CONFIG_*` がある、または global `commit.gpgSign=true`、`core.hooksPath`、不正な `init.templateDir` などが設定されている場合。
- 成果物への影響: production oracle への直接影響はない。しかし新規 6 node が `verify_snapshot` 到達前に偽赤となり、段 6 の変異・受入証拠を環境依存にする。外部 hook の内容次第では fixture 外への副作用も許す。
- 判定: nit。受理集合や production 成果物を壊さないため must-fix ではないが、`TOOL._run` 相当の隔離へ揃えることを推奨する。`user.name/email` と `protocol.file.allow` は個別指定済みだが、他の設定は遮断していない。
- 確信度: 高。

並列 path 衝突は見つからない。全パスは function-scope の `tmp_path` 配下で、`source-{index}` もテストごとに分離される。

## 受理集合の判定

受理集合が広がった箇所はない。

新規処理は [tools/codex_reasoning_ab.py:1693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/tools/codex_reasoning_ab.py:1693) で既存 `submodule_manifest` の全行を走査し、未初期化行について既存 `reasons` へ追加するだけである。既存 reason の削除、握り潰し、早期 return、条件反転はない。`enforce_closure` 分岐の外なので、closure の真偽や caller spec で迂回できない。

したがって新受理集合は、旧受理集合のうち manifest 全行が `initialized` の入力だけである。空 manifest と全初期化済み manifest は従来どおり受理される。

oracle dict は [tools/codex_reasoning_ab.py:1706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/tools/codex_reasoning_ab.py:1706) 以下を含め変更されていない。差分も production は 3 行追加、削除 0 行である。継続して受理される入力では、key 集合、各値、`manifest_sha256` の canonical bytes は変更前と同一であり、schedule 突合と replay bytes 比較は維持される。従来受理された未初期化 snapshot は oracle を返さなくなるため、その snapshot の既存 schedule/replay は拒否されるが、これは裁定済みの受理集合縮小である。

## 壊れる既存契約

意図しない既存 node の破壊は無し。pytest は実走しておらず、以下は静的判定である。

- `test_uninitialized_nested_submodule_is_manifested_and_accepted`: [test_codex_reasoning_ab.py:2252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/orchestrator/tests/test_codex_reasoning_ab.py:2252) は `_git_closure_reasons` を直接検査する。新 gate は `verify_snapshot` 内だけなので、この lower-layer 契約は変わらない。
- `test_uninitialized_nested_submodule_gitlink_pin_rejects_change`: `_assert_submodule_manifest_sha256` の直接検査であり、新 gate を通らない。
- `test_pos_neg_submodule_initialization_state_mismatch_is_rejected`: schedule の hash 不一致検査であり、期待値は未変更。
- `test_m1_snapshot_head_pin_is_independent`: 全初期化済みの `benchmark_snapshots` に対する HEAD mismatch は従来どおり積まれる。
- `benchmark_snapshots` 系: canonical source が再帰的に初期化済みなら `_init_submodules_from_local_source` が全階層を snapshot へ伝播するため、新 reason は発生しない。既存テストの反転、緩和、skip、削除はなく、差分は追加 251 行、削除 0 行だった。

production の伝播規則は次のとおり。

- top-level が未初期化: [tools/codex_reasoning_ab.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/tools/codex_reasoning_ab.py:736) の `initialized` リストへ入らず、snapshot の gitlink だけが残り、新 gate が拒否する。
- 親は初期化済み、nested が未初期化: 親を update 後に再帰するが、nested は同じ規則で skip され、nested path を理由に拒否する。
- 未初期化 ancestor の下: inventory は ancestor より下へ再帰せず、まず ancestor 自体を拒否する。
- 全階層が初期化済みかつ HEAD が gitlink と一致: 各階層が update され再帰されるため従来どおり通る。

受入 preflight 自体が recursive status の `-` と `U` を拒否するため、受入可能な正当運用状態を新たに拒否する経路は確認できない。

新規 node は `benchmark_snapshots` その他の共有 fixtureを使わず、実 repo、履歴、成果物 corpus に依存しない。このため `growth_test_holds.py`、`REAL_REPO_SERIAL_NODES`、`test_hold_inventory.py` への登録追加は不要であり、一覧メタテストとの不整合もない。

## 総括

must-fix の退行は検出しなかった。  
受理集合は未初期化 submodule を除く方向にだけ縮小し、fail-open はない。  
継続受理される snapshot の oracle bytes と既存期待値は不変である。  
正当な再帰初期化済み production snapshot と既存 benchmark 系は静的には維持される。  
新規 Git fixture の親環境依存を nit 1 件として報告する。  
pytest は実走していないため、緑とは判定していない。