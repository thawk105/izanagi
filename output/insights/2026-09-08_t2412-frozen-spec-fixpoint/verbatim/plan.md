## 現物確認

指定された 4 ファイルを確認した。

- [brief.md](/home/SFC/tanab/.claude/jobs/8901c450/tmp/t2412/brief.md:1)
  - 実 git で、spec の HEAD blob 一致と `source_commit == HEAD` が同時成立しないという実測を確認した。
- [floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1152)
  - `1190-1192`: working-tree spec と `git show HEAD:<relpath>` の byte 一致を要求する。brief の `1190-1191` は拒否行 `1192` を省略しているが、指摘内容は正しい。
  - `1235-1239`: `_git_head()` の結果と `provenance.source_commit` の同値を要求する。
  - `2175-2183`: 実行時に `runtime_head == loaded_head == source_commit` を要求する。
  - `2643-2651`: finalizer の期待 header が `runtime_head = source_commit` を再構成する。
  - top-level exact key は `1194-1201` の `schema, provenance, environment, artifacts, cells, pairs, windows, randomization, statistics, failure_policy, outputs`。
  - `provenance` exact key は `621-633` の `calibration, source_commit`。
- [test_floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:25)
  - `26-27` で `SOURCE_COMMIT = HEAD`。
  - `_install_git` の定義開始は brief の `306` ではなく `305`。本体 `313-331` は `rev-parse HEAD` を定数に、`show HEAD:*` を working-tree bytes に固定している。
  - `996-1010` と `2003-2015` が現在の二重・三重同値を直接 pin する。
- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_ccbench_spawn_sites.py:113)
  - `115-117` が `_git_head`, `_git_show_head`, `_run_probe` を各 1 site として登録し、`2600-2607` が inventory の完全一致を要求する。

## 設計の選択

P1 の中核を採る。ただし「第一親」ではなく、`source_commit` が `loaded_head` の**唯一の親**であることを要求する。さらに親→`loaded_head` の tree 差分 path を、凍結 spec の relpath ただ 1 件に限定する。merge freeze commit は受理しない。

- 守る保証: spec は tracked HEAD blob と byte 一致し、測定対象は `loaded_head` という特定 commit に束縛され、実行時 HEAD もそこから動かせない。
- 得る保証: `source_commit` の code tree と実行 commit の tree は spec path を除いて同一であり、作成可能な一段の spec-only freeze commit になる。
- 失う保証: `source_commit` 自体が実行 commit の OID と等しい、という文字どおりの三者同値は失う。代わりに「唯一の親＋spec-only tree 差分」で code-state 同一性を保証する。
- P1 からの意図的な絞り込み: merge commit を許さないため受理集合は広がらず、freeze commit の履歴形が一意になる。

案 X は `source_commit` による事前の code-state 宣言を失い、schema key 集合まで変えるため却下する。案 Y は任意の祖先からの介在 code 変更を許してしまい、不変条件 2・3 に反するため却下する。

`SPEC_SCHEMA` は `floor-pair-spec/v3` のままとする。この変更は現実には空だった受理条件の修正であり、version bump は schema と spec SHA を HMAC rank に入れている `1298-1337` の測定順まで変えてしまうためである。top-level exact key 集合も `provenance` の exact key 集合も変更しない。

## 変更プラン

1. [floor_pair_driver.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:22) および [同:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:86)
   - 「同一 revision 内」という proof-limit 文言を、「source commit と spec-only child の自己整合」に更新する。
   - なぜ: `source_commit` と実行 revision が異なる設計になり、現行説明が不正確になるため。

2. [floor_pair_driver.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:538)-[578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:578) の git helper 群
   - `_git_parents(root, loaded_head)` を追加し、固定 argv の `git show -s --format=%P <loaded_head>` から、検証済み 40 桁 lowercase OID の tuple を返す。
   - `_git_changed_paths(root, source_commit, loaded_head)` を追加し、`git diff-tree --no-commit-id --name-only -r -z --no-renames <source> <loaded>` の raw NUL 区切り path を返す。path は decode せず `os.fsencode(spec_relpath)` と比較できる形にする。
   - 両 helper とも既存 helper 同様、timeout、起動失敗、非ゼロ rc、不正出力を `FloorPairBindingError` に正規化する。
   - なぜ: 唯一の親関係と、rename を含めた全 tree 差分 path の閉包を別々に exact 検証するため。

3. [floor_pair_driver.py:1152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1152)-[1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1256)
   - docstring に `source_commit` が spec-only freeze commit の親を表すことを明記する。
   - `1235-1239` の `source_commit == loaded_head` を次の二条件へ置換する。
     - `_git_parents(root, loaded_head) == (provenance.source_commit,)`
     - `_git_changed_paths(root, provenance.source_commit, loaded_head) == (os.fsencode(relpath),)`
   - `1190-1192` の spec HEAD blob byte 一致と expected SHA-256 検査は一切緩めない。
   - なぜ: 不動点だけを除去し、spec 以外の code・binary・receipt・calibration 変更を freeze commit に混入させないため。

4. [floor_pair_driver.py:2175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:2175)-[2183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:2183)
   - 実行時条件を `runtime_head == spec.loaded_head` のみにする。出力確保前に拒否する順序と既存 status は維持し、message を二者一致に合わせる。
   - なぜ: loader が親関係と tree 差分を確定済みであり、実行時に固定すべき commit は spec を含む `loaded_head` だから。

5. [floor_pair_driver.py:2643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:2643)-[2651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:2651)
   - finalizer の期待 `runtime_head` を `spec.provenance.source_commit` から `spec.loaded_head` に変更する。
   - なぜ: `run_window` が実際に記録する runtime commit と再検証値を同じ意味に揃えるため。

6. [test_ccbench_spawn_sites.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_ccbench_spawn_sites.py:113)-[117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_ccbench_spawn_sites.py:117)
   - `_git_parents` と `_git_changed_paths` をそれぞれ non-CCBench process site、count `1` として登録し、read-only Git lineage/tree query である旨をコメントする。
   - なぜ: `_git_head` / `_git_show_head` 以外に `subprocess.run` site を 2 件増やすため、`2600-2607` の exact inventory 更新が必須だから。

## テストプラン

実 git 正例は [test_floor_pair_driver.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:365) 付近の fixture 群の後に追加する。

骨格は次のとおり。

1. `tmp_path` で `git init` と test-local user 設定を行う。
2. `_write_inputs()` が作る calibration、receipt、binary を commit し、その OID を `source_commit` とする。
3. `_valid_document()` の `provenance.source_commit` にその OIDを設定して `spec.json` を生成する。
4. `spec.json` だけを add/commit し、新 HEAD が親と異なることを確認する。
5. calibration verifier だけを monkeypatch し、Git subprocess は monkeypatch しない。
6. `load_frozen_spec()` が成功し、`spec.provenance.source_commit == parent`、`spec.loaded_head == child`、両者が異なることを assert する。

既存模擬 fixture は [test_floor_pair_driver.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:25)-[331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:331) で次のように更新する。

- `PARENT = "a" * 40`, `HEAD = "b" * 40`, `SOURCE_COMMIT = PARENT` として OID を分離する。
- `_install_git` に親 tuple と changed-path tuple の override を持たせ、新 helper の exact argv/output を模擬する。
- 通常値は親 `(PARENT,)`、差分 `("spec.json",)`。
- 模擬 fixture は schema/type/mutation の高速な単独検査に残し、「実 git 上で作成可能」の証拠には使わない。

追加・変更する負例は以下。

- `996-1010`: `source_commit` が唯一の親でない場合の拒否へ改名・更新する。
- 新規: `source_commit` が第一親でも、親が複数ある merge HEAD を拒否する。
- 新規: 親→HEAD に spec 以外の path が 1 件でもあれば拒否する。
- `737-749`: 新 helper の起動失敗・非ゼロ終了も `FloorPairBindingError` になるケースを追加する。
- `2003-2015`: `runtime_head == loaded_head` を要求する名称へ変更する。通常 fixture の `source_commit != loaded_head` で既存の正例群が走ること自体が、不要な三者同値を復活させない回帰証拠になる。
- `2272-2310`: header の `runtime_head` 改変拒否は維持し、distinct parent/HEAD fixture により finalizer が `loaded_head` を期待していることを確認する。

同期しなければ壊れる既存 test は、`_install_git` を使う全 loader test、`test_mutation_19_source_commit_must_equal_loaded_head`、`test_runtime_head_must_complete_source_commit_three_way_binding`、proof-limit 文言を exact pin する `459-479`、および process inventory の `2600-2607`。schema 値を維持するため schema pin と HMAC golden order は変更しない。

## 残る限界

- freeze receipt は追加しないため、spec が結果観測前に作られたことは引き続き証明しない。
- Git の working-tree clean 状態や、実行中 Python module bytes が HEAD と一致することは新たに証明しない。今回閉じるのは既存の commit/spec binding の不動点だけである。
- HEAD に後続 commit を積めば、code tree が同じでも再 freeze なしには走れない。これは特定 commit への束縛を維持する意図的な制約である。
- T-2423 の成果物名 protocol は一切変更しない。`p3_b4_floor_artifact_issuer.py` も対象外のままとする。

## 総括

`source_commit` を唯一の親、`loaded_head` を spec を含む実行 commit と定義する。  
親→HEAD の差分を spec 1 path に限定し、tracked blob の byte 一致も維持する。  
実行時と成果物再検証は `loaded_head` に統一する。  
実 git の spec-only child commit 正例により、不動点が実際に閉じたことを証明する。